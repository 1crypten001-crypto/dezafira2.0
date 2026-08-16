import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import crypto from 'crypto';
import { env } from '$env/dynamic/private';
import { getActiveNewsletterEmails } from '$lib/server/database';
import { sendNewsletterCampaignEmail } from '$lib/server/resend';
import { getSettings } from '$lib/server/database';

function safeEqual(a: string, b: string): boolean {
  const ba = Buffer.from(a);
  const bb = Buffer.from(b);
  if (ba.length !== bb.length) return false;
  return crypto.timingSafeEqual(ba, bb);
}

/**
 * POST /api/import/nurture
 *
 * Ponte DezafiraAdm → DezafiraClube (funil): dispara UM e-mail da sequência
 * de nurturing (fase 5 do MarketingPipeline) para todos os assinantes ativos
 * da newsletter, via Resend. O Adm chama 4x (E-mail 1..4) com os conteúdos
 * gerados por IA.
 *
 * Autenticação: header `x-import-key` == IMPORT_API_KEY (mesma chave da ponte
 * de produtos). Fail-closed: 503 se a chave não estiver configurada.
 */
export const POST: RequestHandler = async ({ request }) => {
  const importKey = env.IMPORT_API_KEY || '';
  const providedKey = request.headers.get('x-import-key') || '';

  if (!importKey) {
    return json({ success: false, error: 'IMPORT_API_KEY não configurado neste serviço.' }, { status: 503 });
  }
  if (!safeEqual(providedKey, importKey)) {
    return json({ success: false, error: 'Chave de importação inválida.' }, { status: 401 });
  }

  let body: any;
  try {
    body = await request.json();
  } catch (e) {
    return json({ success: false, error: 'JSON inválido.' }, { status: 400 });
  }

  const subject = String(body.subject || '').trim();
  const content = String(body.content || '').trim();
  const emailIndex = parseInt(body.email_index) || 0;
  const youtubeVideoUrl = body.youtube_video_url ? String(body.youtube_video_url).trim() : null;

  if (!subject || !content) {
    return json({ success: false, error: 'subject e content são obrigatórios.' }, { status: 400 });
  }
  if (emailIndex < 1 || emailIndex > 4) {
    return json({ success: false, error: 'email_index deve ser 1..4.' }, { status: 400 });
  }

  try {
    const emails = await getActiveNewsletterEmails();
    if (emails.length === 0) {
      return json({ success: true, sent: 0, email_index: emailIndex, message: 'Nenhum assinante ativo.' });
    }

    const settings = await getSettings();
    const siteName = settings.site_name || env.RESEND_FROM_NAME || 'Dezafira Club';
    const siteUrl = settings.site_url || env.SITE_URL || 'https://www.dezafira.com.br';

    const ok = await sendNewsletterCampaignEmail(
      emails,
      subject,
      content,
      youtubeVideoUrl,
      siteName,
      siteUrl
    );

    return json({
      success: ok,
      sent: ok ? emails.length : 0,
      email_index: emailIndex,
      recipients: emails.length,
      message: ok ? 'Sequência de nurturing enviada.' : 'Falha ao enviar (verifique RESEND_API_KEY).'
    });
  } catch (e) {
    console.error('[IMPORT NURTURE] Erro ao enviar nurturing:', e);
    return json({ success: false, error: 'Erro ao disparar nurturing.' }, { status: 500 });
  }
};
