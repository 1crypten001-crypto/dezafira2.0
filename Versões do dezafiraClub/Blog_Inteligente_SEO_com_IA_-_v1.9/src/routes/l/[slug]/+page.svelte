<script lang="ts">
    import { onMount } from 'svelte';
    import AdRenderer from '$lib/components/AdRenderer.svelte';
    import { page } from '$app/stores';
    import { t } from '$lib/i18n';

    let { data } = $props();
    const lang = $derived($page.data.language || 'pt');

    const duration = data.link.ad_duration_seconds;
    let secondsLeft = $state(duration);
    let progress = $derived((secondsLeft / duration) * 100);
    let canSkip = $state(false);

    onMount(() => {
        // Habilitar botão de pular após 2 segundos (ou quando acabar)
        const skipTimeout = setTimeout(() => {
            canSkip = true;
        }, 2000);

        const interval = setInterval(() => {
            if (secondsLeft > 0) {
                secondsLeft--;
            } else {
                clearInterval(interval);
                clearTimeout(skipTimeout);
                redirectNow();
            }
        }, 1000);

        return () => {
            clearInterval(interval);
            clearTimeout(skipTimeout);
        };
    });

    function redirectNow() {
        if (typeof window !== 'undefined') {
            window.location.href = data.link.destination_url;
        }
    }
</script>

<svelte:head>
    <title>{data.link.meta_title || `${t(lang, 'shortlink.accessing')} | ${data.siteTitle}`}</title>
    {#if data.link.meta_description}
        <meta name="description" content={data.link.meta_description} />
    {/if}
    {#if data.link.is_indexed === 1}
        <meta name="robots" content="index, follow" />
    {:else}
        <meta name="robots" content="noindex, nofollow" />
    {/if}
</svelte:head>

<div class="interstitial-page">
    <div class="progress-bar-container">
        <div class="progress-bar" style="width: {progress}%"></div>
    </div>

    <header class="header">
        <a href="/" class="brand">
            {#if data.siteLogo}
                <img src={data.siteLogo} alt={data.siteTitle} class="logo" />
            {/if}
            <span class="site-title">{data.siteTitle}</span>
        </a>
    </header>

    <main class="main-content">
        <div class="info-card">
            <div class="status-header">
                <div class="spinner"></div>
                <h2>{t(lang, 'shortlink.redirecting')}</h2>
            </div>
            <p class="description">
                {t(lang, 'shortlink.wait_body')}
            </p>

            <div class="countdown-badge">
                {#if secondsLeft > 0}
                    {t(lang, 'shortlink.redirect_in', { n: secondsLeft })}
                {:else}
                    {t(lang, 'shortlink.redirect_now')}
                {/if}
            </div>

            <div class="actions">
                <button 
                    onclick={redirectNow} 
                    class="btn btn-primary btn-redirect"
                    disabled={!canSkip}
                >
                    {#if secondsLeft > 0 && !canSkip}
                        {t(lang, 'shortlink.wait_n', { n: secondsLeft })}
                    {:else}
                        {t(lang, 'shortlink.go_destination')}
                    {/if}
                </button>
            </div>
        </div>

        <div class="ad-card-wrapper">
            <AdRenderer ads={[data.ad]} placement="interstitial" />
        </div>
    </main>

    <footer class="footer">
        <p>© {new Date().getFullYear()} {data.siteTitle}. {t(lang, "common.all_rights")}</p>
    </footer>
</div>

<style>
    /* ── Reset e Estrutura Geral ─────────────────────────────────────── */
    .interstitial-page {
        min-height: 100dvh;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        background: radial-gradient(circle at top, var(--bg-secondary) 0%, var(--bg-primary) 100%);
        font-family: var(--font-sans, system-ui, sans-serif);
        color: var(--text-primary);
        position: relative;
        padding: 1.5rem;
    }

    /* ── Barra de Progresso no Topo ───────────────────────────────────── */
    .progress-bar-container {
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: var(--border-light, #f1f5f9);
        z-index: 10;
    }

    .progress-bar {
        height: 100%;
        background: var(--accent, #3b82f6);
        transition: width 1s linear;
    }

    /* ── Cabeçalho minimalista ───────────────────────────────────────── */
    .header {
        display: flex;
        justify-content: center;
        padding: 1rem 0;
    }

    .brand {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        text-decoration: none;
        color: var(--text-primary);
    }

    .logo {
        height: 28px;
        width: auto;
    }

    .site-title {
        font-weight: 700;
        font-size: 1.125rem;
        letter-spacing: -0.02em;
    }

    /* ── Conteúdo Central ───────────────────────────────────────────── */
    .main-content {
        flex: 1;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        max-width: 680px;
        width: 100%;
        margin: 0 auto;
        gap: 2rem;
    }

    .info-card {
        background: var(--bg-primary, white);
        border: 1px solid var(--border-color, #e2e8f0);
        border-radius: 16px;
        padding: 2rem;
        width: 100%;
        text-align: center;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05), 0 8px 10px -6px rgba(0, 0, 0, 0.05);
    }

    .status-header {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.75rem;
        margin-bottom: 0.75rem;
    }

    .status-header h2 {
        font-size: 1.25rem;
        font-weight: 700;
        margin: 0;
    }

    .spinner {
        width: 20px;
        height: 20px;
        border: 3px solid var(--border-color);
        border-top-color: var(--accent, #3b82f6);
        border-radius: 50%;
        animation: spin 1s infinite linear;
    }

    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }

    .description {
        color: var(--text-secondary);
        font-size: 0.9375rem;
        line-height: 1.5;
        margin-bottom: 1.5rem;
    }

    .countdown-badge {
        display: inline-flex;
        align-items: center;
        background: var(--bg-secondary, #f8fafc);
        border: 1px solid var(--border-light, #e2e8f0);
        padding: 0.5rem 1rem;
        border-radius: 9999px;
        font-size: 0.875rem;
        font-weight: 500;
        color: var(--text-secondary);
        margin-bottom: 1.5rem;
    }

    .countdown-badge span {
        color: var(--accent, #3b82f6);
        font-weight: 700;
        margin-left: 0.25rem;
        font-family: monospace;
    }

    .btn-redirect {
        width: 100%;
        padding: 0.875rem 1.5rem;
        font-size: 1rem;
        font-weight: 600;
        border-radius: 8px;
        cursor: pointer;
        transition: background-color 0.2s, transform 0.2s;
    }

    .btn-redirect:disabled {
        opacity: 0.65;
        cursor: not-allowed;
    }

    /* ── Renderização do Anúncio ──────────────────────────────────────── */
    .ad-card-wrapper {
        width: 100%;
    }

    .ad-card-wrapper :global(.ad-container) {
        margin: 0 !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
    }

    /* ── Rodapé minimalista ──────────────────────────────────────────── */
    .footer {
        text-align: center;
        padding: 1rem 0;
        font-size: 0.75rem;
        color: var(--text-muted);
    }

    @media (max-width: 640px) {
        .info-card {
            padding: 1.5rem;
        }

        .status-header h2 {
            font-size: 1.125rem;
        }
    }
</style>
