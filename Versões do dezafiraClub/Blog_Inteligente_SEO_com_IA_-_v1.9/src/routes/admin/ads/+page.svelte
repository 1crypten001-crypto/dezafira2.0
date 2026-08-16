<script lang="ts">
  import { page } from "$app/stores";
  import { t, formatDate as fmtDate, formatMoney } from "$lib/i18n";
  import { enhance } from "$app/forms";

    let { data } = $props();
  const lang = $derived($page.data.language || 'pt');
function getPlacementName(placement: string) {
        const placements: Record<string, string> = {
            sidebar: "Sidebar",
            home_middle: "Home (Meio)",
            post_inline: "Post (Interno)",
            in_article: "Artigo (Nativo)",
        };
        return placements[placement] || placement;
    }

    function getTypeName(type: string) {
        const types: Record<string, string> = {
            html: "Script/HTML",
            image: "Banner/Imagem",
            text: "Texto",
            native: "Conteúdo Nativo",
        };
        return types[type] || type;
    }

    function getTypeIcon(type: string) {
        const icons: Record<string, string> = {
            html: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>',
            image: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>',
            text: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>',
            native: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>',
        };
        return icons[type] || '';
    }
</script>

<div class="ads-page">
    <div class="page-header">
        <div class="page-header-title">
            <h1>{t(lang, "admin.ads.heading")}</h1>
            <p class="subtitle">{t(lang, "admin.ads.heading")}</p>
        </div>
        <a href="/admin/ads/new" class="btn btn-primary">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
            </svg>
            Nova Campanha
        </a>
    </div>

    <div class="stats-row">
        <div class="stat-card">
            <span class="stat-number">{data.ads.length}</span>
            <span class="stat-label">Total</span>
        </div>
        <div class="stat-card">
            <span class="stat-number">{data.ads.filter((a: any) => a.is_active === 1).length}</span>
            <span class="stat-label">Ativas</span>
        </div>
        <div class="stat-card">
            <span class="stat-number">{data.ads.filter((a: any) => a.type === 'native').length}</span>
            <span class="stat-label">Nativos</span>
        </div>
    </div>

    <div class="card">
        {#if data.ads.length === 0}
            <div class="empty-state">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <rect x="3" y="3" width="18" height="18" rx="2"/>
                    <circle cx="8.5" cy="8.5" r="1.5"/>
                    <polyline points="21 15 16 10 5 21"/>
                </svg>
                <p>{t(lang, "admin.ads.empty")}</p>
                <a href="/admin/ads/new" class="btn btn-small btn-primary">Começar agora</a>
            </div>
        {:else}
            <div class="table-container">
                <table class="table">
                    <thead>
                        <tr>
                            <th>Campanha</th>
                            <th>Local</th>
                            <th>{t(lang, "admin.ui.type")}</th>
                            <th>Peso</th>
                            <th>{t(lang, "admin.ui.status")}</th>
                            <th class="text-right">{t(lang, "admin.ui.actions")}</th>
                        </tr>
                    </thead>
                    <tbody>
                        {#each data.ads as ad}
                            <tr class:inactive={ad.is_active !== 1}>
                                <td>
                                    <div class="ad-info">
                                        <span class="ad-name">{ad.name}</span>
                                        {#if ad.link_url}
                                            <span class="ad-link">{ad.link_url}</span>
                                        {/if}
                                    </div>
                                </td>
                                <td>
                                    <span class="badge badge-{ad.placement}">
                                        {getPlacementName(ad.placement)}
                                    </span>
                                </td>
                                <td>
                                    <span class="type-badge type-{ad.type}">
                                        {@html getTypeIcon(ad.type)}
                                        {getTypeName(ad.type)}
                                    </span>
                                </td>
                                <td>
                                    <div class="weight-display">
                                        <span class="weight-bar" style="width: {ad.weight * 10}%"></span>
                                        <span class="weight-text">{ad.weight}x</span>
                                    </div>
                                </td>
                                <td>
                                    <span class="status-badge {ad.is_active ? 'active' : 'inactive'}">
                                        {ad.is_active ? "Ativo" : "Pausado"}
                                    </span>
                                </td>
                                <td class="text-right">
                                    <div class="actions">
                                        <a href="/admin/ads/{ad.id}" class="btn btn-small btn-icon" title="Editar">
                                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                                                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                                            </svg>
                                        </a>
                                        <form action="/admin/ads/{ad.id}/delete" method="POST" use:enhance={() => {
                                            return ({ result }) => {
                                                if (result.type === "success") {
                                                    window.location.reload();
                                                }
                                            };
                                        }} style="display:inline;">
                                            <button type="submit" class="btn btn-small btn-icon btn-danger" title={t(lang, "admin.ui.delete")}
                                                onclick={(e) => { if (!confirm(t(lang, 'admin.ads.confirm_delete'))) e.preventDefault(); }}>
                                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                                    <polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                                                </svg>
                                            </button>
                                        </form>
                                    </div>
                                </td>
                            </tr>
                        {/each}
                    </tbody>
                </table>
            </div>
        {/if}
    </div>
</div>

<style>
    .ads-page { max-width: 1100px; margin: 0 auto; }

    .page-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-end;
        margin-bottom: 2rem;
    }

    h1 { font-family: var(--font-sans); font-size: 1.5rem; font-weight: 700; margin-bottom: 0.5rem; }
    .subtitle { color: var(--text-muted); font-family: var(--font-sans); }

    .btn { display: inline-flex; align-items: center; gap: 0.5rem; }
    .btn-icon { padding: 0.5rem; }

    .stats-row {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 1rem;
        margin-bottom: 1.5rem;
    }

    .stat-card {
        background: var(--bg-primary);
        border: 1px solid var(--border-light);
        border-radius: 12px;
        padding: 1.25rem;
        text-align: center;
    }

    .stat-number { display: block; font-size: 1.75rem; font-weight: 700; color: var(--text-primary); }
    .stat-label { font-size: 0.8rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px; }

    .card { background: var(--bg-primary); border: 1px solid var(--border-color); border-radius: var(--radius-lg); overflow: hidden; }
    .table-container { overflow-x: auto; }
    .table { width: 100%; border-collapse: collapse; font-family: var(--font-sans); }

    th { text-align: left; padding: 1rem; background: var(--bg-secondary); border-bottom: 1px solid var(--border-color); font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.5px; color: var(--text-secondary); font-weight: 600; }
    td { padding: 1rem; border-bottom: 1px solid var(--border-light); font-size: 0.875rem; vertical-align: middle; }
    tr:hover { background: var(--bg-secondary); }
    tr.inactive { opacity: 0.6; }

    .ad-info { display: flex; flex-direction: column; gap: 0.25rem; }
    .ad-name { font-weight: 600; color: var(--text-primary); }
    .ad-link { font-size: 0.75rem; color: var(--text-muted); max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

    .badge { padding: 0.25rem 0.6rem; border-radius: 6px; font-size: 0.75rem; font-weight: 500; display: inline-flex; align-items: center; gap: 0.3rem; }
    .badge-sidebar { background: #fef3c7; color: #92400e; }
    .badge-home_middle { background: #dbeafe; color: #1e40af; }
    .badge-post_inline { background: #d1fae5; color: #065f46; }
    .badge-in_article { background: #ede9fe; color: #5b21b6; }

    .type-badge { display: inline-flex; align-items: center; gap: 0.4rem; font-size: 0.75rem; padding: 0.25rem 0.5rem; border-radius: 4px; background: var(--bg-tertiary); color: var(--text-secondary); }
    .type-badge :global(svg) { opacity: 0.7; }

    .weight-display { position: relative; display: flex; align-items: center; gap: 0.5rem; }
    .weight-bar { height: 6px; background: var(--text-primary); border-radius: 3px; min-width: 6px; max-width: 60px; }
    .weight-text { font-size: 0.8rem; font-weight: 600; min-width: 24px; }

    .status-badge { font-size: 0.75rem; font-weight: 600; padding: 0.25rem 0.75rem; border-radius: 20px; }
    .status-badge.active { background: #ecfdf5; color: #059669; }
    .status-badge.inactive { background: var(--bg-secondary); color: var(--text-muted); }

    .actions { display: flex; gap: 0.5rem; justify-content: flex-end; }
    .btn-danger { color: #dc2626; }
    .btn-danger:hover { background: #fef2f2; }

    .text-right { text-align: right; }
    .empty-state { padding: 4rem 2rem; text-align: center; color: var(--text-muted); }

    @media (max-width: 768px) {
        .page-header { flex-direction: column; align-items: flex-start; gap: 1rem; }
        .stats-row { grid-template-columns: 1fr; }
    }
</style>
