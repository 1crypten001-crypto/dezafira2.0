<script lang="ts">
  import { page } from "$app/stores";
  import { t, formatDate as fmtDate, formatMoney } from "$lib/i18n";
  import { enhance } from "$app/forms";

    let { form } = $props();
  const lang = $derived($page.data.language || 'pt');
let adType = $state("native");
    let adPlacement = $state("in_article");

    function getPreviewSize() {
        if (adPlacement === "sidebar") return "300x300px";
        if (adPlacement === "home_middle") return "1200x250px";
        if (adPlacement === "in_article") return "Adaptável";
        return "Sem tamanho fixo";
    }
</script>

<div class="ads-page">
    <div class="page-header">
        <h1>Nova Campanha</h1>
        <p class="subtitle">Crie um novo anúncio ou conteúdo nativo</p>
    </div>

    <form method="POST" enctype="multipart/form-data" use:enhance>
        <div class="form-section">
            <div class="form-group">
                <label for="name">Nome da Campanha</label>
                <input type="text" id="name" name="name" placeholder="Ex: Promoção de Verão 2026" required />
            </div>

            <div class="form-row">
                <div class="form-group">
                    <label for="placement">Posicionamento</label>
                    <select id="placement" name="placement" bind:value={adPlacement}>
                        <option value="in_article">Dentro do Artigo (Nativo)</option>
                        <option value="sidebar">Sidebar (Quadrado)</option>
                        <option value="home_middle">Home (Entre posts)</option>
                        <option value="post_inline">Post (Interno)</option>
                    </select>
                </div>

                <div class="form-group">
                    <label for="weight">Prioridade</label>
                    <div class="weight-input">
                        <input type="range" id="weight" name="weight" min="1" max="10" value="1" />
                        <span class="weight-value">1x</span>
                    </div>
                </div>
            </div>

            <div class="form-group">
                <label for="type">Tipo de Anúncio</label>
                <div class="type-grid">
                    <label class="type-card" class:active={adType === 'native'}>
                        <input type="radio" name="type" value="native" bind:group={adType} />
                        <div class="type-icon">
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M12 2L2 7l10 5 10-5-10-5z"/>
                                <path d="M2 17l10 5 10-5"/>
                                <path d="M2 12l10 5 10-5"/>
                            </svg>
                        </div>
                        <div class="type-info">
                            <span class="type-name">Conteúdo Nativo</span>
                            <span class="type-desc">Integra-se ao design do blog</span>
                        </div>
                    </label>
                    <label class="type-card" class:active={adType === 'image'}>
                        <input type="radio" name="type" value="image" bind:group={adType} />
                        <div class="type-icon">
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <rect x="3" y="3" width="18" height="18" rx="2"/>
                                <circle cx="8.5" cy="8.5" r="1.5"/>
                                <polyline points="21 15 16 10 5 21"/>
                            </svg>
                        </div>
                        <div class="type-info">
                            <span class="type-name">Banner/Imagem</span>
                            <span class="type-desc">Imagem com link clicável</span>
                        </div>
                    </label>
                    <label class="type-card" class:active={adType === 'html'}>
                        <input type="radio" name="type" value="html" bind:group={adType} />
                        <div class="type-icon">
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <polyline points="16 18 22 12 16 6"/>
                                <polyline points="8 6 2 12 8 18"/>
                            </svg>
                        </div>
                        <div class="type-info">
                            <span class="type-name">Script/HTML</span>
                            <span class="type-desc">Google Adsense, etc</span>
                        </div>
                    </label>
                    <label class="type-card" class:active={adType === 'text'}>
                        <input type="radio" name="type" value="text" bind:group={adType} />
                        <div class="type-icon">
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                                <polyline points="14 2 14 8 20 8"/>
                            </svg>
                        </div>
                        <div class="type-info">
                            <span class="type-name">Apenas Texto</span>
                            <span class="type-desc">Texto clicável</span>
                        </div>
                    </label>
                    <label class="type-card" class:active={adType === 'video'}>
                        <input type="radio" name="type" value="video" bind:group={adType} />
                        <div class="type-icon">
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <polygon points="23 7 16 12 23 17 23 7"/>
                                <rect x="1" y="5" width="15" height="14" rx="2" ry="2"/>
                            </svg>
                        </div>
                        <div class="type-info">
                            <span class="type-name">Vídeo YouTube</span>
                            <span class="type-desc">Vídeo com autoplay e expansão</span>
                        </div>
                    </label>
                </div>
            </div>

            {#if adType === 'native'}
                <div class="native-preview">
                    <div class="preview-header">
                        <span>Prévia do Anúncio Nativo</span>
                    </div>
                    <div class="preview-content">
                        <div class="preview-image"></div>
                        <div class="preview-text">
                            <div class="preview-label"></div>
                            <div class="preview-title"></div>
                            <div class="preview-cta"></div>
                        </div>
                    </div>
                </div>
                <div class="form-group">
                    <label for="content">Label (texto acima do título)</label>
                    <input type="text" id="content" name="content" placeholder="Ex: Conteúdo Recomendado" />
                </div>
            {/if}

            {#if adType === 'image'}
                <div class="form-group">
                    <label for="image_file">Banner/Imagem</label>
                    <div class="image-upload-wrapper">
                        <input type="file" id="image_file" name="image_file" accept="image/*" class="file-input" />
                        <div class="url-fallback">
                            <span>Ou use uma URL:</span>
                            <input type="url" id="image_url" name="image_url" placeholder="https://exemplo.com/banner.jpg" />
                        </div>
                    </div>
                    <small>Recomendado: {getPreviewSize()}</small>
                </div>
                <div class="form-group">
                    <label for="link_url">Link de Destino</label>
                    <input type="url" id="link_url" name="link_url" placeholder="https://seusite.com" required />
                </div>
            {:else if adType === 'html'}
                <div class="form-group">
                    <label for="content">Código HTML/Script</label>
                    <textarea id="content" name="content" rows="6" placeholder="Cole aqui seu script (ex: Google Adsense)..."></textarea>
                </div>
            {:else if adType === 'text'}
                <div class="form-group">
                    <label for="content">Texto do Anúncio</label>
                    <input type="text" id="content" name="content" placeholder="Ex: Conheça nossos serviços exclusivos!" required />
                </div>
                <div class="form-group">
                    <label for="link_url">Link de Destino</label>
                    <input type="url" id="link_url" name="link_url" placeholder="https://..." required />
                </div>
            {:else if adType === 'video'}
                <div class="form-group">
                    <label for="youtube_video_url">URL do Vídeo do YouTube</label>
                    <input type="url" id="youtube_video_url" name="youtube_video_url" placeholder="https://www.youtube.com/watch?v=..." required />
                </div>
                <div class="form-group">
                    <label for="link_url">Link de Destino (Opcional)</label>
                    <input type="url" id="link_url" name="link_url" placeholder="https://seusite.com" />
                </div>
            {/if}

        </div>

        <div class="section-divider"></div>

        <div class="form-section">
            <label class="checkbox-label">
                <input type="checkbox" name="is_active" checked />
                <span>Campanha Ativa</span>
            </label>
        </div>

        {#if form?.message}
            <div class="alert error">{form.message}</div>
        {/if}

        <div class="form-actions">
            <a href="/admin/ads" class="btn">{t(lang, "admin.ui.cancel")}</a>
            <button type="submit" class="btn btn-primary">Criar Campanha</button>
        </div>
    </form>
</div>

<style>
    .ads-page { max-width: 800px; margin: 0 auto; }
    .page-header { margin-bottom: 2rem; }
    h1 { font-family: var(--font-sans); font-size: 1.5rem; font-weight: 700; margin-bottom: 0.5rem; }
    .subtitle { color: var(--text-muted); font-family: var(--font-sans); }

    form { background: var(--bg-primary); padding: 2rem; border-radius: var(--radius-lg); border: 1px solid var(--border-color); }
    .form-section { display: flex; flex-direction: column; gap: 1.5rem; }
    .form-group { display: flex; flex-direction: column; gap: 0.5rem; }
    .form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; align-items: start; }

    label { font-weight: 500; color: var(--text-primary); font-size: 0.875rem; }
    input[type="text"], input[type="url"], select, textarea {
        width: 100%; padding: 0.75rem; background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: var(--radius-md); color: var(--text-primary); font-family: var(--font-sans); transition: border-color var(--transition-fast);
    }
    input:focus, select:focus, textarea:focus { outline: none; border-color: var(--text-primary); }

    .weight-input { display: flex; align-items: center; gap: 1rem; }
    .weight-input input[type="range"] { flex: 1; }
    .weight-value { font-weight: 600; min-width: 30px; }

    .type-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 1rem; }
    .type-card {
        display: flex; align-items: center; gap: 1rem; padding: 1rem; background: var(--bg-secondary); border: 2px solid var(--border-light); border-radius: var(--radius-md); cursor: pointer; transition: all 0.2s ease;
    }
    .type-card input { display: none; }
    .type-card:hover { border-color: var(--border-color); }
    .type-card.active { border-color: var(--text-primary); background: var(--bg-primary); }
    .type-icon { color: var(--text-muted); }
    .type-card.active .type-icon { color: var(--text-primary); }
    .type-info { display: flex; flex-direction: column; }
    .type-name { font-weight: 600; font-size: 0.9rem; }
    .type-desc { font-size: 0.75rem; color: var(--text-muted); }

    .native-preview { background: var(--bg-secondary); border: 1px dashed var(--border-color); border-radius: var(--radius-md); padding: 1rem; }
    .preview-header { font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.5px; color: var(--text-muted); margin-bottom: 0.75rem; }
    .preview-content { display: grid; grid-template-columns: 100px 1fr; gap: 1rem; align-items: center; }
    .preview-image { aspect-ratio: 1/1; background: var(--bg-tertiary); border-radius: 6px; }
    .preview-text { display: flex; flex-direction: column; gap: 0.4rem; }
    .preview-label { height: 8px; width: 60%; background: var(--bg-tertiary); border-radius: 4px; }
    .preview-title { height: 12px; width: 90%; background: var(--bg-tertiary); border-radius: 4px; }
    .preview-cta { height: 8px; width: 40%; background: var(--bg-tertiary); border-radius: 4px; }

    .image-upload-wrapper { display: flex; flex-direction: column; gap: 1rem; padding: 1.5rem; background: var(--bg-secondary); border: 1px dashed var(--border-color); border-radius: var(--radius-md); }
    .file-input { font-family: var(--font-sans); font-size: 0.875rem; }
    .url-fallback { display: flex; flex-direction: column; gap: 0.5rem; padding-top: 1rem; border-top: 1px solid var(--border-light); }
    .url-fallback span { font-size: 0.75rem; font-weight: 600; color: var(--text-muted); text-transform: uppercase; }

    .checkbox-label { display: flex; align-items: center; gap: 0.5rem; cursor: pointer; font-weight: 600; }
    input[type="checkbox"] { width: 18px; height: 18px; accent-color: var(--text-primary); }

    .section-divider { height: 1px; background: var(--border-light); margin: 2rem 0; }
    .form-actions { margin-top: 2rem; display: flex; justify-content: flex-end; gap: 1rem; }
    .alert { padding: 1rem; border-radius: var(--radius-md); margin-bottom: 1.5rem; font-family: var(--font-sans); font-size: 0.875rem; }
    .error { background: #fef2f2; color: #dc2626; border: 1px solid #fecaca; }

    small { color: var(--text-muted); font-size: 0.75rem; }

    @media (max-width: 640px) {
        .form-row { grid-template-columns: 1fr; gap: 1rem; }
        .type-grid { grid-template-columns: 1fr; }
        .preview-content { grid-template-columns: 80px 1fr; }
    }
</style>