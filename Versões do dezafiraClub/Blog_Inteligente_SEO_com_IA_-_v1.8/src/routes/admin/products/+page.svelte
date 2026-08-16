<script lang="ts">
  import { page } from "$app/stores";
  import { t, formatDate as fmtDate, formatMoney } from "$lib/i18n";
  import { enhance } from "$app/forms";
    import type { PageData } from "./$types";

  const lang = $derived($page.data.language || 'pt');

let { data }: { data: PageData } = $props();

    function formatPrice(cents: number) {
        if (cents === 0) return 'Gratuito / Apenas Link';
        return (cents / 100).toLocaleString(lang === 'en' ? 'en-US' : lang === 'es' ? 'es-ES' : 'pt-BR', { style: 'currency', currency: 'BRL' });
    }

    function truncate(str: string | null, len = 60) {
        if (!str) return '';
        return str.length > len ? str.slice(0, len) + '...' : str;
    }

    const notifyFlash = $derived.by(() => {
        const n = $page.url.searchParams.get('notify');
        if (!n) return null;
        const sent = $page.url.searchParams.get('sent') || '0';
        const failed = $page.url.searchParams.get('failed') || '0';
        if (n === 'ok') return { type: 'ok' as const, text: `Produto salvo. E-mail de atualização enviado para ${sent} comprador(es).` };
        if (n === 'no_buyers') return { type: 'warn' as const, text: 'Produto salvo. Nenhum comprador elegível encontrado para notificar.' };
        if (n === 'no_resend') return { type: 'err' as const, text: 'Produto salvo, mas Resend não está configurado (API key). Configure em Configurações → Resend.' };
        if (n === 'fail') return { type: 'err' as const, text: `Produto salvo, mas o envio falhou (enviados: ${sent}, falhas: ${failed}). Verifique domínio From no Resend e os logs do servidor.` };
        if (n === 'error') return { type: 'err' as const, text: 'Produto salvo, mas houve erro ao preparar a notificação. Veja os logs do servidor.' };
        return null;
    });
</script>

<div class="products-list-page">
    <div class="page-header">
        <div class="header-text">
            <h1>{t(lang, "admin.products.heading")} Digitais</h1>
            <p class="subtitle">{t(lang, "admin.products.heading")}</p>
        </div>
        <div class="header-actions" style="display: flex; gap: 0.75rem; align-items: center;">
            <a href="/admin/products/categories" class="btn btn-secondary">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="vertical-align: middle;">
                    <line x1="4" y1="6" x2="20" y2="6"/><line x1="4" y1="12" x2="20" y2="12"/><line x1="4" y1="18" x2="20" y2="18"/>
                </svg>
                Categorias
            </a>
            <a href="/admin/products/new" class="btn btn-primary">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
                </svg>
                Novo Produto
            </a>
        </div>
    </div>

    {#if notifyFlash}
        <div class="notify-banner" class:ok={notifyFlash.type === 'ok'} class:warn={notifyFlash.type === 'warn'} class:err={notifyFlash.type === 'err'}>
            {notifyFlash.text}
        </div>
    {/if}

    <div class="table-container">
        {#if data.products && data.products.length > 0}
            <table class="data-table">
                <thead>
                    <tr>
                        <th>{t(lang, "admin.ui.name")}</th>
                        <th>{t(lang, "admin.ui.description")}</th>
                        <th>{t(lang, "admin.ui.price")}</th>
                        <th>Tipo de Recurso</th>
                        <th>Link / Arquivo</th>
                        <th class="actions-header">{t(lang, "admin.ui.actions")}</th>
                    </tr>
                </thead>
                <tbody>
                    {#each data.products as product}
                        <tr>
                            <td class="font-semibold" data-label="Nome">
                                <div class="product-name-cell">
                                    {#if product.image_url}
                                        <img src={product.image_url} alt={product.name} class="product-list-thumb" />
                                    {:else}
                                        <div class="product-list-thumb-placeholder">
                                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>
                                            </svg>
                                        </div>
                                    {/if}
                                    <div class="product-info-stack">
                                        <span class="product-name-text">{product.name}</span>
                                        {#if product.slug}
                                            <div class="product-slug-row">
                                                <a href="/product/{product.slug}" target="_blank" class="product-slug-link" title="Visualizar página pública do produto">
                                                    /product/{product.slug}
                                                </a>
                                                <button type="button" class="btn-copy-slug" onclick={() => {
                                                    const fullUrl = window.location.origin + '/product/' + product.slug;
                                                    navigator.clipboard.writeText(fullUrl);
                                                    alert(t(lang, 'admin.products.copy_link'));
                                                }} title="Copiar link completo">
                                                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                                                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
                                                    </svg>
                                                </button>
                                            </div>
                                        {/if}
                                    </div>
                                </div>
                            </td>
                            <td class="text-muted" data-label="Descrição">{truncate(product.description)}</td>
                            <td data-label="Preço">
                                <span class="price-badge" class:free={product.price_cents === 0}>
                                    {formatPrice(product.price_cents)}
                                </span>
                            </td>
                            <td data-label="Tipo">
                                {#if product.file_url}
                                    {#if product.file_url.startsWith('http')}
                                        <span class="type-badge" style="background: #e0f2fe; color: #0369a1; border: 1px solid #bae6fd; padding: 0.25rem 0.5rem; border-radius: 9999px; font-size: 0.75rem; font-weight: 500;">Cloudinary</span>
                                    {:else}
                                        <span class="type-badge file">Arquivo Local</span>
                                    {/if}
                                {:else if product.external_link}
                                    <span class="type-badge link">Link Externo</span>
                                {:else}
                                    <span class="type-badge empty">-</span>
                                {/if}
                            </td>
                            <td class="file-link-cell" data-label="Arquivo/Link">
                                {#if product.file_url}
                                    <a href="/api/download/{product.id}" target="_blank" class="download-link" title="Visualizar arquivo">
                                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>
                                        </svg>
                                        Arquivo
                                    </a>
                                {:else if product.external_link}
                                    <a href={product.external_link} target="_blank" class="external-url" title="Abrir link externo">
                                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                            <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/>
                                        </svg>
                                        Link
                                    </a>
                                {:else}
                                    <span class="text-muted">-</span>
                                {/if}
                            </td>
                            <td class="table-actions" data-label="Ações">
                                <a href="/admin/products/{product.id}" class="btn btn-small btn-secondary" title="Editar">
                                    Editar
                                </a>
                                <form method="POST" action="?/delete" use:enhance={() => {
                                    return async ({ update }) => {
                                        if (confirm(t(lang, 'admin.products.confirm_delete'))) {
                                            update();
                                        }
                                    };
                                }} style="display:inline;">
                                    <input type="hidden" name="id" value={product.id} />
                                    <button type="submit" class="btn btn-small btn-danger" title={t(lang, "admin.ui.delete")}>
                                        {t(lang, "admin.ui.delete")}
                                    </button>
                                </form>
                            </td>
                        </tr>
                    {/each}
                </tbody>
            </table>
        {:else}
            <div class="empty-state">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <rect x="2" y="3" width="20" height="14" rx="2" ry="2"/><line x1="2" y1="10" x2="22" y2="10"/>
                </svg>
                <p>{t(lang, "admin.products.empty")}</p>
                <a href="/admin/products/new" class="btn btn-primary btn-small">Cadastrar Primeiro Produto</a>
            </div>
        {/if}
    </div>
</div>

<style>
    .products-list-page {
        padding: 0.5rem 0;
    }

    .page-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 2rem;
        flex-wrap: wrap;
        gap: 1rem;
    }

    .notify-banner {
        padding: 0.85rem 1rem;
        border-radius: 10px;
        font-size: 0.9rem;
        margin-bottom: 1.25rem;
        border: 1px solid transparent;
        line-height: 1.45;
    }
    .notify-banner.ok {
        background: #ecfdf5;
        color: #065f46;
        border-color: #a7f3d0;
    }
    .notify-banner.warn {
        background: #fffbeb;
        color: #92400e;
        border-color: #fde68a;
    }
    .notify-banner.err {
        background: #fef2f2;
        color: #991b1b;
        border-color: #fecaca;
    }

    h1 {
        font-family: var(--font-sans);
        font-size: 1.5rem;
        font-weight: 700;
        margin-bottom: 0.25rem;
        color: var(--text-primary);
    }

    .subtitle {
        color: var(--text-muted);
        font-size: 0.9rem;
    }

    .table-container {
        background: var(--bg-primary);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-lg);
        overflow-x: auto;
    }

    .data-table {
        width: 100%;
        border-collapse: collapse;
        text-align: left;
        font-size: 0.9rem;
    }

    .data-table th, .data-table td {
        padding: 1rem 1.25rem;
        border-bottom: 1px solid var(--border-light);
    }

    .data-table th {
        font-weight: 600;
        color: var(--text-secondary);
        background: var(--bg-secondary);
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .actions-header {
        text-align: right;
    }

    .font-semibold {
        font-weight: 600;
        color: var(--text-primary);
    }

    .product-name-cell {
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }

    .product-list-thumb {
        width: 40px;
        height: 40px;
        object-fit: cover;
        border-radius: var(--radius-sm);
        border: 1px solid var(--border-color);
        background: var(--bg-secondary);
        flex-shrink: 0;
    }

    .product-list-thumb-placeholder {
        width: 40px;
        height: 40px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: var(--radius-sm);
        border: 1px dashed var(--border-color);
        background: var(--bg-secondary);
        color: var(--text-muted);
        flex-shrink: 0;
    }

    .text-muted {
        color: var(--text-muted);
        font-size: 0.85rem;
    }

    .price-badge {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        background: var(--bg-secondary);
        border-radius: 4px;
        font-weight: 500;
        font-size: 0.8rem;
        color: var(--text-primary);
        border: 1px solid var(--border-color);
    }

    .price-badge.free {
        background: #f0fdf4;
        color: #166534;
        border-color: #bbf7d0;
    }

    .type-badge {
        display: inline-block;
        padding: 0.2rem 0.5rem;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
    }

    .type-badge.file {
        background: #eff6ff;
        color: #1e40af;
    }

    .type-badge.link {
        background: #fdf2f8;
        color: #9d174d;
    }

    .type-badge.empty {
        background: transparent;
        color: var(--text-muted);
    }

    .download-link, .external-url {
        display: inline-flex;
        align-items: center;
        gap: 0.25rem;
        font-size: 0.85rem;
        font-weight: 500;
        color: var(--text-primary);
        text-decoration: underline;
    }

    .download-link:hover, .external-url:hover {
        color: var(--text-secondary);
    }

    .table-actions {
        display: flex;
        gap: 0.5rem;
        justify-content: flex-end;
        align-items: center;
    }

    .empty-state {
        text-align: center;
        padding: 4rem 2rem;
        color: var(--text-muted);
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 1rem;
    }

    .empty-state svg {
        color: var(--text-muted);
    }

    .empty-state p {
        font-size: 0.95rem;
    }

    .product-info-stack {
        display: flex;
        flex-direction: column;
        gap: 0.25rem;
    }

    .product-name-text {
        font-weight: 600;
        color: var(--text-primary);
    }

    .product-slug-row {
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .product-slug-link {
        font-family: var(--font-mono);
        font-size: 0.75rem;
        color: var(--text-muted);
        text-decoration: none;
        transition: color var(--transition-fast);
    }

    .product-slug-link:hover {
        color: #3b82f6;
        text-decoration: underline;
    }

    .btn-copy-slug {
        background: none;
        border: none;
        padding: 2px;
        color: var(--text-muted);
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: var(--radius-sm);
        transition: color var(--transition-fast), background var(--transition-fast);
    }

    .btn-copy-slug:hover {
        color: var(--text-primary);
        background: var(--bg-tertiary);
    }

    @media (max-width: 768px) {
        .page-header {
            flex-direction: column;
            align-items: stretch;
            gap: 1rem;
        }

        .header-actions {
            width: 100%;
            display: grid !important;
            grid-template-columns: 1fr 1fr;
            gap: 0.5rem;
        }

        .header-actions a {
            justify-content: center;
        }

        .table-container {
            border: none;
            background: transparent;
            overflow-x: visible;
        }

        .data-table {
            display: block;
        }

        .data-table thead {
            display: none;
        }

        .data-table tbody {
            display: flex;
            flex-direction: column;
            gap: 1rem;
            width: 100%;
        }

        .data-table tr {
            display: block;
            background: var(--bg-primary);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-lg);
            padding: 1rem;
            box-shadow: var(--shadow-sm);
        }

        .data-table td {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.65rem 0;
            border-bottom: 1px solid var(--border-light);
            text-align: right;
            gap: 1rem;
            font-size: 0.85rem;
        }

        .data-table td:last-child {
            border-bottom: none;
            padding-bottom: 0;
        }

        .data-table td::before {
            content: attr(data-label);
            font-weight: 600;
            color: var(--text-secondary);
            font-size: 0.75rem;
            text-transform: uppercase;
            text-align: left;
            flex-shrink: 0;
        }

        .product-name-cell {
            justify-content: flex-end;
            text-align: right;
            width: 100%;
        }

        .product-info-stack {
            align-items: flex-end;
        }

        .product-slug-row {
            justify-content: flex-end;
        }

        .table-actions {
            width: 100%;
            justify-content: flex-end;
            margin-top: 0.5rem;
        }
    }
</style>
