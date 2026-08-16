<script lang="ts">
  import { page } from "$app/stores";
  import { t, formatMoney } from "$lib/i18n";

  let { data } = $props();
  const lang = $derived($page.data.language || 'pt');

  function formatPrice(cents: number) {
    return formatMoney(lang, cents || 0);
  }

  const activeCount = $derived(data.plans.filter((p: any) => p.is_active === 1).length);
  const avgPrice = $derived(
    data.plans.length
      ? data.plans.reduce((sum: number, p: any) => sum + (p.price_cents || 0), 0) / data.plans.length
      : 0
  );
</script>

<svelte:head>
  <title>{t(lang, "admin.premium.title")}</title>
</svelte:head>

<div class="premium-admin">
  <div class="page-header">
    <div class="page-header-title">
      <h1>{t(lang, "admin.premium.heading")}</h1>
      <p class="subtitle">{t(lang, "admin.premium.subtitle")}</p>
    </div>
    <a href="/admin/premium/plans/new" class="btn btn-primary">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
      </svg>
      {t(lang, "admin.premium.new")}
    </a>
  </div>

  <div class="stats-row">
    <div class="stat-card">
      <span class="stat-number">{data.plans.length}</span>
      <span class="stat-label">{t(lang, "admin.premium.plans_stat")}</span>
    </div>
    <div class="stat-card">
      <span class="stat-number">{activeCount}</span>
      <span class="stat-label">{t(lang, "admin.premium.active_stat")}</span>
    </div>
    <div class="stat-card">
      <span class="stat-number">{formatPrice(avgPrice)}</span>
      <span class="stat-label">{t(lang, "admin.premium.avg_price_stat")}</span>
    </div>
  </div>

  <div class="card">
    {#if data.plans.length === 0}
      <div class="empty-state">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
        </svg>
        <p>{t(lang, "admin.premium.empty")}</p>
        <a href="/admin/premium/plans/new" class="btn btn-small btn-primary">{t(lang, "admin.premium.create_first")}</a>
      </div>
    {:else}
      <div class="plans-list">
        {#each data.plans as plan}
          <div class="plan-item" class:inactive={plan.is_active !== 1}>
            <div class="plan-info">
              <h3 class="plan-name">{plan.name}</h3>
              {#if plan.description}
                <p class="plan-desc">{plan.description}</p>
              {/if}
            </div>
            <div class="plan-details">
              <div class="plan-price">
                <span class="price">{formatPrice(plan.price_cents)}</span>
                <span class="interval">{t(lang, "admin.premium.per_days", { n: String(plan.interval_days || 30) })}</span>
              </div>
              <span class="status-badge {plan.is_active === 1 ? 'active' : 'inactive'}">
                {plan.is_active === 1 ? t(lang, "admin.premium.active") : t(lang, "admin.premium.inactive")}
              </span>
            </div>
            <div class="plan-actions">
              <a href="/admin/premium/plans/{plan.id}" class="btn btn-small btn-icon" title={t(lang, "admin.premium.edit")}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                  <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                </svg>
              </a>
            </div>
          </div>
        {/each}
      </div>
    {/if}
  </div>
</div>

<style>
  .premium-admin { max-width: 1000px; margin: 0 auto; }
  .page-header { display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 2rem; }
  h1 { font-family: var(--font-sans); font-size: 1.5rem; font-weight: 700; margin-bottom: 0.5rem; }
  .subtitle { color: var(--text-muted); font-family: var(--font-sans); }
  .btn { display: inline-flex; align-items: center; gap: 0.5rem; }
  .btn-icon { padding: 0.5rem; }

  .stats-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-bottom: 1.5rem; }
  .stat-card { background: var(--bg-primary); border: 1px solid var(--border-light); border-radius: 12px; padding: 1.25rem; text-align: center; }
  .stat-number { display: block; font-size: 1.75rem; font-weight: 700; }
  .stat-label { font-size: 0.8rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px; }

  .card { background: var(--bg-primary); border: 1px solid var(--border-color); border-radius: var(--radius-lg); overflow: hidden; }
  .plans-list { display: flex; flex-direction: column; }
  .plan-item { display: flex; align-items: center; gap: 1rem; padding: 1.5rem; border-bottom: 1px solid var(--border-light); transition: background 0.2s; }
  .plan-item:hover { background: var(--bg-secondary); }
  .plan-item.inactive { opacity: 0.6; }
  .plan-info { flex: 1; }
  .plan-name { font-size: 1rem; font-weight: 600; margin-bottom: 0.25rem; }
  .plan-desc { font-size: 0.85rem; color: var(--text-muted); }
  .plan-details { display: flex; align-items: center; gap: 1rem; }
  .plan-price { text-align: right; }
  .price { font-size: 1.1rem; font-weight: 700; }
  .interval { font-size: 0.8rem; color: var(--text-muted); }
  .status-badge { font-size: 0.75rem; font-weight: 600; padding: 0.25rem 0.75rem; border-radius: 20px; }
  .status-badge.active { background: #ecfdf5; color: #059669; }
  .status-badge.inactive { background: var(--bg-secondary); color: var(--text-muted); }
  .plan-actions { display: flex; gap: 0.5rem; }
  .empty-state { padding: 4rem 2rem; text-align: center; color: var(--text-muted); }

  @media (max-width: 768px) {
    .page-header { flex-direction: column; align-items: flex-start; gap: 1rem; }
    .stats-row { grid-template-columns: 1fr; }
    .plan-item { flex-wrap: wrap; }
  }
</style>
