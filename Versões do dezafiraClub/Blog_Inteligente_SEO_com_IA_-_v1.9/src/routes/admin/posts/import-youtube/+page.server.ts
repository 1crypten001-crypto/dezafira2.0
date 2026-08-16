import { fail } from '@sveltejs/kit';
import type { Actions } from './$types';
import { env } from '$env/dynamic/private';
import { getSettings } from '$lib/server/database';

// Tempo máximo (ms) para cada etapa
const TIMEOUT_OEMBED      = 8_000;   //  8s – busca de metadados oEmbed
const TIMEOUT_TRANSCRIPT  = 12_000;  // 12s – scraping de transcrição YouTube
const TIMEOUT_CAPTIONS    = 8_000;   //  8s – download do arquivo de legendas
const TIMEOUT_GEMINI      = 55_000;  // 55s – chamada à API Gemini

/** Cria um signal de AbortController com timeout automático */
function makeSignal(ms: number): AbortSignal {
    const controller = new AbortController();
    setTimeout(() => controller.abort(), ms);
    return controller.signal;
}

function extractYoutubeId(url: string): string | null {
    const patterns = [
        /(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^\&\s?]+)/,
        /youtube\.com\/shorts\/([^\&\s?]+)/,
    ];
    for (const pattern of patterns) {
        const match = url.match(pattern);
        if (match) return match[1];
    }
    return null;
}

async function getYoutubeTranscript(videoId: string): Promise<string | null> {
    try {
        const watchUrl = `https://www.youtube.com/watch?v=${videoId}`;

        const response = await fetch(watchUrl, {
            signal: makeSignal(TIMEOUT_TRANSCRIPT),
            headers: {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7'
            }
        });
        if (!response.ok) return null;

        const html = await response.text();
        const match = html.match(/ytInitialPlayerResponse\s*=\s*({.+?})\s*;/);
        if (!match) return null;

        const playerResponse = JSON.parse(match[1]);
        const captionTracks = playerResponse?.captions?.playerCaptionsTracklistRenderer?.captionTracks;
        if (!captionTracks || captionTracks.length === 0) return null;

        const track =
            captionTracks.find((t: any) => t.languageCode === 'pt' || t.languageCode === 'pt-BR') ||
            captionTracks.find((t: any) => t.languageCode?.startsWith('pt')) ||
            captionTracks.find((t: any) => t.languageCode === 'en') ||
            captionTracks[0];

        if (!track?.baseUrl) return null;

        const captionResponse = await fetch(track.baseUrl, {
            signal: makeSignal(TIMEOUT_CAPTIONS)
        });
        if (!captionResponse.ok) return null;

        const xmlText = await captionResponse.text();
        const textRegex = /<text[^>]*>([\s\S]*?)<\/text>/g;
        let matchText;
        let transcriptText = '';

        while ((matchText = textRegex.exec(xmlText)) !== null) {
            const line = matchText[1]
                .replace(/&amp;/g, '&')
                .replace(/&lt;/g, '<')
                .replace(/&gt;/g, '>')
                .replace(/&quot;/g, '"')
                .replace(/&#39;/g, "'")
                .replace(/&apos;/g, "'");
            transcriptText += line + ' ';
        }
        return transcriptText.trim() || null;

    } catch (error: any) {
        if (error?.name === 'AbortError') {
            console.warn(`[import-youtube] Transcript fetch timed out for video ${videoId}`);
        } else {
            console.error('[import-youtube] Error fetching YouTube transcript:', error);
        }
        return null;
    }
}

export const actions: Actions = {
    default: async ({ request }) => {
        const data = await request.formData();
        const videoUrl = data.get('videoUrl') as string;

        if (!videoUrl) {
            return fail(400, { error: 'YT_URL_REQUIRED' });
        }

        // ── Carregar chave de API ──────────────────────────────────────────────
        const settings = await getSettings();

        const keyFromDB  = settings.gemini_api_key?.trim()  || '';
        const keyFromEnv = env.GEMINI_API_KEY?.trim()        || '';
        const apiKey     = keyFromDB || keyFromEnv;
        const apiModel   = (settings.gemini_api_model?.trim() || env.GEMINI_API_MODEL?.trim() || 'gemini-2.5-flash');

        // Log diagnóstico (não exibe o valor completo da chave por segurança)
        console.log(`[import-youtube] API key source: ${keyFromDB ? 'database (painel)' : keyFromEnv ? 'env (.env)' : 'NOT FOUND'}`);
        if (apiKey) {
            console.log(`[import-youtube] API key starts with: ${apiKey.substring(0, 8)}...`);
        }

        if (!apiKey) {
            return fail(500, { error: 'YT_NO_API_KEY' });
        }

        // ── Metadados via oEmbed ───────────────────────────────────────────────
        try {
            const oembedUrl = `https://www.youtube.com/oembed?url=${encodeURIComponent(videoUrl)}&format=json`;

            let oembedResponse: Response;
            try {
                oembedResponse = await fetch(oembedUrl, { signal: makeSignal(TIMEOUT_OEMBED) });
            } catch (e: any) {
                const code = e?.name === 'AbortError' ? 'YT_OEMBED_TIMEOUT' : 'YT_OEMBED_FAIL';
                return fail(400, { error: code });
            }

            if (!oembedResponse.ok) {
                return fail(400, { error: 'YT_OEMBED_INVALID' });
            }

            const metadata    = await oembedResponse.json();
            const title       = metadata.title as string;
            const videoId     = extractYoutubeId(videoUrl);
            const thumbnailUrl = videoId
                ? `https://i.ytimg.com/vi/${videoId}/maxresdefault.jpg`
                : (metadata.thumbnail_url as string);

            // ── Transcrição (opcional) ─────────────────────────────────────────
            let transcriptText: string | null = null;
            if (videoId) {
                console.log(`[import-youtube] Trying to fetch transcript for: ${videoId}`);
                transcriptText = await getYoutubeTranscript(videoId);
                console.log(`[import-youtube] Transcript: ${transcriptText ? `found (${transcriptText.length} chars)` : 'not found'}`);
            }

            const canonicalUrl = videoId
                ? `https://www.youtube.com/watch?v=${videoId}`
                : videoUrl;

            // ── Montar requisição para o Gemini ────────────────────────────────
            const geminiUrl = `https://generativelanguage.googleapis.com/v1beta/models/${apiModel}:generateContent?key=${apiKey}`;
            let body: any;

            if (transcriptText) {
                console.log('[import-youtube] Mode: text generation (transcript)');
                const prompt = `Você é um redator profissional de blog. Escreva um artigo de blog completo e profissional em Português (Brasil) baseado inteiramente na seguinte transcrição de um vídeo do YouTube.
O artigo deve ser estruturado APENAS com tags HTML puras (<h2>, <h3>, <p>, <ul>, <li>, <strong>).
Retorne apenas o conteúdo do corpo do artigo em HTML. Não use markdown.

Transcrição do vídeo:
${transcriptText}`;

                body = {
                    contents: [{ parts: [{ text: prompt }] }]
                };
            } else {
                console.log('[import-youtube] Mode: direct video analysis (file_data fallback)');
                const prompt = `Analise o conteúdo deste vídeo do YouTube e escreva um artigo de blog completo e profissional em Português (Brasil).
O artigo deve ser formatado APENAS com tags HTML puras (<h2>, <h3>, <p>, <ul>, <li>, <strong>).
Retorne apenas o conteúdo do corpo do artigo em HTML. Não use markdown.`;

                body = {
                    contents: [{
                        parts: [
                            { file_data: { file_uri: canonicalUrl } },
                            { text: prompt }
                        ]
                    }]
                };
            }

            // ── Chamar a API Gemini ────────────────────────────────────────────
            let geminiResponse: Response;
            try {
                geminiResponse = await fetch(geminiUrl, {
                    method: 'POST',
                    signal: makeSignal(TIMEOUT_GEMINI),
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(body)
                });
            } catch (e: any) {
                if (e?.name === 'AbortError') {
                    return fail(504, { error: 'YT_GEMINI_TIMEOUT' });
                }
                throw e;
            }

            if (!geminiResponse.ok) {
                const errorData = await geminiResponse.json().catch(() => ({}));
                console.error('[import-youtube] Gemini API Error:', JSON.stringify(errorData));
                const apiMsg = (errorData as any)?.error?.message || '';
                if (geminiResponse.status === 400 && apiMsg.toLowerCase().includes('api key')) {
                    return fail(500, { error: 'YT_GEMINI_INVALID_KEY' });
                }
                return fail(500, {
                    error: 'YT_GEMINI_API',
                    status: String(geminiResponse.status),
                    detail: apiMsg || String(geminiResponse.status)
                });
            }

            const result  = await geminiResponse.json();
            const content = result.candidates?.[0]?.content?.parts?.[0]?.text || '';

            if (!content) {
                return fail(500, { error: 'YT_NO_CONTENT' });
            }

            // ── Limpar e montar conteúdo final ─────────────────────────────────
            let cleanedContent = content
                .replace(/```html/g, '')
                .replace(/```/g, '')
                .trim();

            if (videoId) {
                const embedHtml = `<div class="video-container" style="position:relative;padding-bottom:56.25%;height:0;overflow:hidden;max-width:100%;margin-bottom:2rem;border-radius:8px;">
    <iframe
        src="https://www.youtube.com/embed/${videoId}"
        style="position:absolute;top:0;left:0;width:100%;height:100%;border:0;"
        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
        allowfullscreen>
    </iframe>
</div>`;
                cleanedContent = embedHtml + cleanedContent;
            }

            return {
                success: true,
                generatedPost: {
                    title,
                    content: cleanedContent,
                    excerpt: `Artigo baseado no vídeo: ${title}`,
                    cover_image: thumbnailUrl,
                    videoUrl
                }
            };

        } catch (error) {
            console.error('[import-youtube] Unexpected error:', error);
            return fail(500, { error: 'YT_UNEXPECTED' });
        }
    }
};
