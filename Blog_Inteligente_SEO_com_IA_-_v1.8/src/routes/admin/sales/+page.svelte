<script lang="ts">
  import { page } from "$app/stores";
  import { t, formatDate as fmtDate, formatMoney } from "$lib/i18n";
  import { enhance } from '$app/forms';

  let { data, form } = $props();
  const lang = $derived($page.data.language || 'pt');
let activeTab = $state('overview'); // overview, history, holdings
  let historySearchQuery = $state('');
  let holdingsSearchQuery = $state('');

  function formatCurrency(value: number) {
    return new Intl.NumberFormat(lang === 'en' ? 'en-US' : lang === 'es' ? 'es-ES' : 'pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(value);
  }

  function formatDate(dateString: string) {
    const date = new Date(dateString);
    return date.toLocaleDateString(lang === "en" ? "en-US" : lang === "es" ? "es-ES" : "pt-BR", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit"
    });
  }

  function getItemTypeLabel(type: string) {
    switch (type) {
      case 'product': return t(lang, 'admin.sales.product');
      case 'course': return t(lang, 'admin.sales.course');
      case 'subscription': return t(lang, 'admin.sales.subscription');
      default: return type;
    }
  }

  function getStatusLabel(status: string) {
    switch (status) {
      case 'completed': return t(lang, 'admin.sales.completed');
      case 'approved': return t(lang, 'admin.sales.approved');
      case 'active': return t(lang, 'admin.sales.active');
      case 'pending': return t(lang, 'admin.sales.pending');
      case 'pending_delivery': return t(lang, 'admin.sales.pending_delivery');
      case 'cancelled': return t(lang, 'admin.sales.cancelled');
      default: return status;
    }
  }

  // Filter history based on search query
  let filteredHistory = $derived.by(() => {
    const list = data.history || [];
    if (!historySearchQuery.trim()) return list;
    const query = historySearchQuery.toLowerCase();
    return list.filter((item: any) => 
      item.username.toLowerCase().includes(query) ||
      (item.user_name && item.user_name.toLowerCase().includes(query)) ||
      item.item_name.toLowerCase().includes(query)
    );
  });

  // Filter holdings based on search query
  let filteredHoldings = $derived.by(() => {
    const list = data.holdings || [];
    if (!holdingsSearchQuery.trim()) return list;
    const query = holdingsSearchQuery.toLowerCase();
    return list.filter((user: any) => 
      user.username.toLowerCase().includes(query) ||
      (user.name && user.name.toLowerCase().includes(query))
    );
  });
</script>

<svelte:head>
  <title>{t(lang, "admin.sales.title")}</title>
</svelte:head>

<div class="sales-dashboard">
  <div class="sales-header">
    <div>
      <h1>{t(lang, "admin.sales.heading")}</h1>
      <p class="subtitle">{t(lang, "admin.sales.subtitle")}</p>
    </div>
  </div>

  <!-- Tabs Navigation -->
  <div class="tabs-nav">
    <button 
      class="tab-btn" 
      class:active={activeTab === 'overview'} 
      onclick={() => activeTab = 'overview'}
    >
      {t(lang, "admin.sales.tab_overview")}
    </button>
    <button 
      class="tab-btn" 
      class:active={activeTab === 'history'} 
      onclick={() => activeTab = 'history'}
    >
      {t(lang, "admin.sales.tab_history")}
    </button>
    <button 
      class="tab-btn" 
      class:active={activeTab === 'holdings'} 
      onclick={() => activeTab = 'holdings'}
    >
      {t(lang, "admin.sales.tab_holdings")}
    </button>
  </div>

  {#if activeTab === 'overview'}
    <!-- General Metrics -->
    <div class="metrics-grid">
      <div class="metric-card">
        <div class="metric-icon faturamento">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
          </svg>
        </div>
        <div class="metric-info">
          <span class="metric-value">{formatCurrency(data.summary?.totalRevenue || 0)}</span>
          <span class="metric-label">{t(lang, "admin.sales.total_revenue")}</span>
        </div>
      </div>

      <div class="metric-card">
        <div class="metric-icon produtos">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"/><line x1="3" y1="6" x2="21" y2="6"/><path d="M16 10a4 4 0 0 1-8 0"/>
          </svg>
        </div>
        <div class="metric-info">
          <span class="metric-value">{data.summary?.productSalesCount || 0}</span>
          <span class="metric-label">{t(lang, "admin.sales.products_sold", { amount: formatCurrency(data.summary?.productRevenue || 0) })}</span>
        </div>
      </div>

      <div class="metric-card">
        <div class="metric-icon cursos">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M22 10v6M2 10l10-5 10 5-10 5z"/><path d="M6 12v5c0 2 2 3 6 3s6-1 6-3v-5"/>
          </svg>
        </div>
        <div class="metric-info">
          <span class="metric-value">{data.summary?.courseSalesCount || 0}</span>
          <span class="metric-label">{t(lang, "admin.sales.courses_sold", { amount: formatCurrency(data.summary?.courseRevenue || 0) })}</span>
        </div>
      </div>

      <div class="metric-card">
        <div class="metric-icon assinaturas">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
          </svg>
        </div>
        <div class="metric-info">
          <span class="metric-value">{data.summary?.activeSubscriptionsCount || 0}</span>
          <span class="metric-label">{t(lang, "admin.sales.active_subs", { amount: formatCurrency(data.summary?.subscriptionRevenue || 0) })}</span>
        </div>
      </div>
    </div>

    <!-- Quick Stats & Info -->
    <div class="overview-details">
      <div class="details-card">
        <h2>{t(lang, "admin.sales.revenue_dist")}</h2>
        <div class="distribution-list">
          <div class="distribution-item">
            <span class="dot product-dot"></span>
            <span class="label">{t(lang, "admin.sales.digital_products")}</span>
            <span class="value">{formatCurrency(data.summary?.productRevenue || 0)}</span>
          </div>
          <div class="distribution-item">
            <span class="dot course-dot"></span>
            <span class="label">{t(lang, "admin.sales.courses_videos")}</span>
            <span class="value">{formatCurrency(data.summary?.courseRevenue || 0)}</span>
          </div>
          <div class="distribution-item">
            <span class="dot sub-dot"></span>
            <span class="label">{t(lang, "admin.sales.premium_subs")}</span>
            <span class="value">{formatCurrency(data.summary?.subscriptionRevenue || 0)}</span>
          </div>
        </div>
      </div>

      <div class="details-card">
        <h2>{t(lang, "admin.sales.recent_sales")}</h2>
        {#if data.history && data.history.length > 0}
          <div class="recent-sales-list">
            {#each data.history.slice(0, 5) as sale}
              <div class="recent-sale-item">
                <div class="sale-main">
                  <span class="sale-title">{sale.item_name}</span>
                  <span class="sale-user">{sale.user_name || sale.username}</span>
                </div>
                <div class="sale-meta">
                  <span class="sale-price">{formatCurrency(sale.amount_cents / 100)}</span>
                  <span class="badge badge-{sale.item_type}">{getItemTypeLabel(sale.item_type)}</span>
                </div>
              </div>
            {/each}
          </div>
        {:else}
          <p class="empty-text">{t(lang, "admin.sales.no_sales")}</p>
        {/if}
      </div>
    </div>

  {:else if activeTab === 'history'}
    <!-- Purchase History Tab -->
    <div class="search-bar-container">
      <div class="search-input-wrapper">
        <svg class="search-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
        </svg>
        <input 
          type="text" 
          placeholder={t(lang, "admin.sales.search_history")} 
          bind:value={historySearchQuery} 
        />
      </div>
    </div>

    <div class="table-card">
      <div class="table-responsive">
        <table>
          <thead>
            <tr>
              <th>{t(lang, "admin.sales.col_datetime")}</th>
              <th>{t(lang, "admin.sales.col_customer")}</th>
              <th>{t(lang, "admin.sales.col_item")}</th>
              <th>{t(lang, "admin.ui.type")}</th>
              <th>{t(lang, "admin.sales.col_amount")}</th>
              <th>{t(lang, "admin.ui.status")}</th>
            </tr>
          </thead>
          <tbody>
            {#each filteredHistory as item}
              <tr>
                <td class="date-col">{formatDate(item.created_at)}</td>
                <td>
                  <div class="user-info">
                    <span class="user-name">{item.user_name || t(lang, 'admin.sales.user_fallback')}</span>
                    <span class="user-email">{item.username}</span>
                  </div>
                </td>
                <td class="item-name-col">
                  <div>{item.item_name}</div>
                  {#if item.has_extra_service === 1 && item.extra_service_title_snapshot}
                    <div style="margin-top: 0.35rem; font-size: 0.75rem; background: #f0f9ff; border: 1px solid #bae6fd; color: #0284c7; padding: 3px 8px; border-radius: 6px; display: inline-flex; align-items: center; gap: 0.3rem; font-weight: 600; line-height: 1.2;">
                      ⚡ + Serviço Extra: {item.extra_service_title_snapshot} ({formatCurrency(item.extra_service_price_cents / 100)})
                    </div>
                  {/if}
                </td>
                <td>
                  <span class="badge badge-{item.item_type}">{getItemTypeLabel(item.item_type)}</span>
                </td>
                <td class="amount-col">{formatCurrency(item.amount_cents / 100)}</td>
                <td>
                  {#if item.status === 'pending_delivery'}
                    <!-- Entrega manual aguardando -->
                    <div class="delivery-cell">
                      <span class="status-indicator status-pending_delivery">⏳ {t(lang, "admin.sales.awaiting_delivery")}</span>
                      {#if item.buyer_access_id}
                        <div class="buyer-access-id">
                          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
                          <span title="Identificador do comprador">{item.buyer_access_id}</span>
                          <button class="copy-btn" onclick={() => navigator.clipboard.writeText(item.buyer_access_id)} title={t(lang, "admin.ui.copy")}>
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
                          </button>
                        </div>
                      {/if}
                      <form method="POST" action="?/markDelivered" use:enhance>
                        <input type="hidden" name="purchase_id" value={item.id} />
                        <button type="submit" class="btn-deliver">
                          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
                          Marcar Entregue
                        </button>
                      </form>
                    </div>
                  {:else}
                    <span class="status-indicator status-{item.status}">
                      {getStatusLabel(item.status)}
                    </span>
                    {#if item.buyer_access_id}
                      <div class="buyer-access-id">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
                        <span title="Identificador do comprador">{item.buyer_access_id}</span>
                      </div>
                    {/if}
                  {/if}
                </td>
              </tr>
            {:else}
              <tr>
                <td colspan="6" class="table-empty">{t(lang, "admin.sales.no_history")}</td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    </div>

  {:else if activeTab === 'holdings'}
    <!-- Accesses and Downloads Tab -->
    <div class="search-bar-container">
      <div class="search-input-wrapper">
        <svg class="search-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
        </svg>
        <input 
          type="text" 
          placeholder="Buscar cliente por nome ou email..." 
          bind:value={holdingsSearchQuery} 
        />
      </div>
    </div>

    <div class="holdings-list">
      {#each filteredHoldings as user}
        <div class="user-holdings-card">
          <div class="user-holdings-header">
            <div>
              <h3>{user.name || 'Sem Nome'}</h3>
              <p class="user-email">{user.username}</p>
            </div>
            <span class="joined-date">Membro desde: {new Date(user.createdAt).toLocaleDateString(lang === 'en' ? 'en-US' : lang === 'es' ? 'es-ES' : 'pt-BR')}</span>
          </div>

          <div class="holdings-details">
            <!-- Subscription -->
            <div class="holding-section">
              <h4>Assinatura</h4>
              {#if user.subscription}
                <div class="active-subscription">
                  <span class="plan-name">{user.subscription.plan_name}</span>
                  <span class="plan-status">Ativa</span>
                  {#if user.subscription.expires_at}
                    <span class="plan-expiry">Expira em: {new Date(user.subscription.expires_at).toLocaleDateString(lang === 'en' ? 'en-US' : lang === 'es' ? 'es-ES' : 'pt-BR')}</span>
                  {/if}
                </div>
              {:else}
                <p class="no-holdings">Sem assinatura premium ativa.</p>
              {/if}
            </div>

            <!-- Digital Products & Downloads -->
            <div class="holding-section">
              <h4>Produtos Digitais Adquiridos</h4>
              {#if user.products && user.products.length > 0}
                <ul class="holdings-list-items">
                  {#each user.products as prod}
                    <li>
                      <div class="item-title-row">
                        <span class="item-name">{prod.item_name}</span>
                        <span class="purchase-date">Comprado em: {new Date(prod.created_at).toLocaleDateString(lang === 'en' ? 'en-US' : lang === 'es' ? 'es-ES' : 'pt-BR')}</span>
                      </div>
                      <div class="download-badge-row">
                        {#if prod.download_count > 0}
                          <span class="downloads-count success">
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>
                            </svg>
                            Baixado {prod.download_count} {prod.download_count === 1 ? 'vez' : 'vezes'}
                          </span>
                        {:else}
                          <span class="downloads-count zero">
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                              <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
                            </svg>
                            {t(lang, "admin.ui.no_data")}
                          </span>
                        {/if}
                      </div>
                    </li>
                  {/each}
                </ul>
              {:else}
                <p class="no-holdings">{t(lang, "admin.ui.no_data")}</p>
              {/if}
            </div>

            <!-- Courses -->
            <div class="holding-section">
              <h4>Cursos Adquiridos</h4>
              {#if user.courses && user.courses.length > 0}
                <ul class="holdings-list-items">
                  {#each user.courses as course}
                    <li>
                      <div class="item-title-row">
                        <span class="item-name">{course.item_name}</span>
                        <span class="purchase-date">Comprado em: {new Date(course.created_at).toLocaleDateString(lang === 'en' ? 'en-US' : lang === 'es' ? 'es-ES' : 'pt-BR')}</span>
                      </div>
                    </li>
                  {/each}
                </ul>
              {:else}
                <p class="no-holdings">{t(lang, "admin.ui.no_data")}</p>
              {/if}
            </div>
          </div>
        </div>
      {:else}
        <p class="empty-text">{t(lang, "admin.users.empty")}</p>
      {/each}
    </div>
  {/if}
</div>

<style>
  .sales-dashboard {
    padding: 1.5rem;
    max-width: 1200px;
    margin: 0 auto;
    color: var(--text-primary);
  }

  .sales-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 2rem;
  }

  .sales-header h1 {
    font-size: 1.75rem;
    font-weight: 700;
    margin: 0;
  }

  .subtitle {
    color: var(--text-secondary);
    margin-top: 0.25rem;
    font-size: 0.95rem;
  }

  .tabs-nav {
    display: flex;
    gap: 0.5rem;
    border-bottom: 1px solid var(--border-color);
    margin-bottom: 2rem;
    padding-bottom: 0.5rem;
  }

  .tab-btn {
    background: transparent;
    border: none;
    color: var(--text-secondary);
    padding: 0.75rem 1.25rem;
    font-weight: 500;
    cursor: pointer;
    border-radius: var(--radius-md);
    transition: all 0.2s ease;
  }

  .tab-btn:hover {
    color: var(--text-primary);
    background: var(--bg-secondary);
  }

  .tab-btn.active {
    color: var(--accent-color, #3b82f6);
    background: rgba(59, 130, 246, 0.1);
    font-weight: 600;
  }

  /* Metrics Cards */
  .metrics-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    gap: 1.5rem;
    margin-bottom: 2rem;
  }

  .metric-card {
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-lg);
    padding: 1.5rem;
    display: flex;
    align-items: center;
    gap: 1rem;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  }

  .metric-icon {
    width: 48px;
    height: 48px;
    border-radius: var(--radius-md);
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .metric-icon svg {
    width: 24px;
    height: 24px;
  }

  .metric-icon.faturamento { background: rgba(16, 185, 129, 0.1); color: #10b981; }
  .metric-icon.produtos { background: rgba(59, 130, 246, 0.1); color: #3b82f6; }
  .metric-icon.cursos { background: rgba(245, 158, 11, 0.1); color: #f59e0b; }
  .metric-icon.assinaturas { background: rgba(139, 92, 246, 0.1); color: #8b5cf6; }

  .metric-info {
    display: flex;
    flex-direction: column;
  }

  .metric-value {
    font-size: 1.5rem;
    font-weight: 700;
    line-height: 1.2;
  }

  .metric-label {
    font-size: 0.85rem;
    color: var(--text-secondary);
    margin-top: 0.25rem;
  }

  /* Overview Details */
  .overview-details {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
    gap: 1.5rem;
  }

  .details-card {
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-lg);
    padding: 1.5rem;
  }

  .details-card h2 {
    font-size: 1.2rem;
    font-weight: 600;
    margin-top: 0;
    margin-bottom: 1.25rem;
  }

  .distribution-list {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .distribution-item {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }

  .dot {
    width: 12px;
    height: 12px;
    border-radius: 50%;
  }

  .product-dot { background: #3b82f6; }
  .course-dot { background: #f59e0b; }
  .sub-dot { background: #8b5cf6; }

  .distribution-item .label {
    flex: 1;
    font-size: 0.95rem;
  }

  .distribution-item .value {
    font-weight: 600;
  }

  .recent-sales-list {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .recent-sale-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-bottom: 0.75rem;
    border-bottom: 1px solid var(--border-color);
  }

  .recent-sale-item:last-child {
    border-bottom: none;
    padding-bottom: 0;
  }

  .sale-main {
    display: flex;
    flex-direction: column;
  }

  .sale-title {
    font-weight: 500;
    font-size: 0.95rem;
  }

  .sale-user {
    font-size: 0.8rem;
    color: var(--text-secondary);
  }

  .sale-meta {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 0.25rem;
  }

  .sale-price {
    font-weight: 600;
    font-size: 0.95rem;
  }

  /* Table styles */
  .search-bar-container {
    margin-bottom: 1.25rem;
  }

  .search-input-wrapper {
    position: relative;
    max-width: 400px;
  }

  .search-input-wrapper input {
    width: 100%;
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    color: var(--text-primary);
    padding: 0.75rem 1rem 0.75rem 2.5rem;
    border-radius: var(--radius-md);
    outline: none;
    transition: border-color 0.2s;
  }

  .search-input-wrapper input:focus {
    border-color: var(--accent-color, #3b82f6);
  }

  .search-icon {
    position: absolute;
    left: 0.85rem;
    top: 50%;
    transform: translateY(-50%);
    color: var(--text-secondary);
    pointer-events: none;
  }

  .table-card {
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-lg);
    overflow: hidden;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  }

  .table-responsive {
    overflow-x: auto;
  }

  table {
    width: 100%;
    border-collapse: collapse;
    text-align: left;
    font-size: 0.9rem;
  }

  th {
    background: rgba(0, 0, 0, 0.1);
    padding: 1rem;
    font-weight: 600;
    color: var(--text-secondary);
    border-bottom: 1px solid var(--border-color);
  }

  td {
    padding: 1rem;
    border-bottom: 1px solid var(--border-color);
    vertical-align: middle;
  }

  tr:last-child td {
    border-bottom: none;
  }

  .date-col {
    color: var(--text-secondary);
    font-family: monospace;
    font-size: 0.85rem;
  }

  .user-info {
    display: flex;
    flex-direction: column;
  }

  .user-name {
    font-weight: 500;
  }

  .user-email {
    font-size: 0.8rem;
    color: var(--text-secondary);
  }

  .item-name-col {
    font-weight: 500;
  }

  .amount-col {
    font-weight: 600;
  }

  /* Badges */
  .badge {
    display: inline-block;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .badge-product { background: rgba(59, 130, 246, 0.15); color: #60a5fa; }
  .badge-course { background: rgba(245, 158, 11, 0.15); color: #fbbf24; }
  .badge-subscription { background: rgba(139, 92, 246, 0.15); color: #a78bfa; }

  /* Status Indicators */
  .status-indicator {
    display: inline-block;
    padding: 0.25rem 0.5rem;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 500;
  }

  .status-completed, .status-approved, .status-active {
    background: rgba(16, 185, 129, 0.15);
    color: #34d399;
  }

  .status-pending {
    background: rgba(245, 158, 11, 0.15);
    color: #fbbf24;
  }

  .status-cancelled {
    background: rgba(239, 68, 68, 0.15);
    color: #f87171;
  }

  .status-pending_delivery {
    background: rgba(245, 158, 11, 0.12);
    color: #f59e0b;
    border: 1px solid rgba(245, 158, 11, 0.3);
  }

  /* Célula de entrega manual no painel de vendas */
  .delivery-cell {
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
    align-items: flex-start;
  }

  .buyer-access-id {
    display: flex;
    align-items: center;
    gap: 0.3rem;
    font-size: 0.78rem;
    color: var(--text-secondary);
    background: var(--bg-secondary);
    border-radius: 4px;
    padding: 2px 6px;
    max-width: 180px;
    overflow: hidden;
  }

  .buyer-access-id span {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .copy-btn {
    background: none;
    border: none;
    cursor: pointer;
    padding: 2px;
    color: var(--text-muted);
    flex-shrink: 0;
    display: flex;
    align-items: center;
    transition: color 0.15s;
  }

  .copy-btn:hover {
    color: var(--text-primary);
  }

  .btn-deliver {
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
    background: rgba(34, 197, 94, 0.1);
    border: 1px solid rgba(34, 197, 94, 0.3);
    color: #22c55e;
    font-size: 0.78rem;
    font-weight: 600;
    padding: 4px 10px;
    border-radius: 5px;
    cursor: pointer;
    transition: background 0.15s, border-color 0.15s;
  }

  .btn-deliver:hover {
    background: rgba(34, 197, 94, 0.2);
    border-color: rgba(34, 197, 94, 0.5);
  }

  .table-empty, .empty-text {
    text-align: center;
    padding: 3rem;
    color: var(--text-secondary);
  }

  /* Holdings Card Styling */
  .holdings-list {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }

  .user-holdings-card {
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-lg);
    padding: 1.5rem;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
  }

  .user-holdings-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    border-bottom: 1px solid var(--border-color);
    padding-bottom: 1rem;
    margin-bottom: 1rem;
  }

  .user-holdings-header h3 {
    font-size: 1.15rem;
    font-weight: 600;
    margin: 0;
  }

  .joined-date {
    font-size: 0.8rem;
    color: var(--text-secondary);
  }

  .holdings-details {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 1.5rem;
  }

  .holding-section {
    display: flex;
    flex-direction: column;
  }

  .holding-section h4 {
    font-size: 0.9rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--text-secondary);
    margin-top: 0;
    margin-bottom: 0.75rem;
    border-bottom: 1px dashed var(--border-color);
    padding-bottom: 0.25rem;
  }

  .active-subscription {
    background: rgba(139, 92, 246, 0.08);
    border: 1px solid rgba(139, 92, 246, 0.2);
    border-radius: var(--radius-md);
    padding: 0.75rem;
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .plan-name {
    font-weight: 600;
    color: #a78bfa;
  }

  .plan-status {
    font-size: 0.75rem;
    font-weight: 700;
    background: rgba(16, 185, 129, 0.2);
    color: #34d399;
    padding: 0.1rem 0.4rem;
    border-radius: 4px;
    align-self: flex-start;
  }

  .plan-expiry {
    font-size: 0.75rem;
    color: var(--text-secondary);
    margin-top: 0.25rem;
  }

  .no-holdings {
    font-size: 0.85rem;
    color: var(--text-secondary);
    font-style: italic;
    margin: 0;
  }

  .holdings-list-items {
    list-style: none;
    padding: 0;
    margin: 0;
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .holdings-list-items li {
    background: rgba(0, 0, 0, 0.15);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-md);
    padding: 0.6rem 0.8rem;
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
  }

  .item-title-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .item-name {
    font-weight: 500;
    font-size: 0.9rem;
  }

  .purchase-date {
    font-size: 0.75rem;
    color: var(--text-secondary);
  }

  .download-badge-row {
    display: flex;
    align-items: center;
  }

  .downloads-count {
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
    font-size: 0.75rem;
    font-weight: 500;
    padding: 0.15rem 0.5rem;
    border-radius: 4px;
  }

  .downloads-count.success {
    background: rgba(16, 185, 129, 0.1);
    color: #34d399;
    border: 1px solid rgba(16, 185, 129, 0.2);
  }

  .downloads-count.zero {
    background: rgba(245, 158, 11, 0.1);
    color: #fbbf24;
    border: 1px solid rgba(245, 158, 11, 0.2);
  }

  @media (max-width: 768px) {
    .sales-header {
      flex-direction: column;
      align-items: flex-start;
      gap: 1rem;
    }

    .overview-details {
      grid-template-columns: 1fr;
    }

    .user-holdings-header {
      flex-direction: column;
      gap: 0.5rem;
    }
  }
</style>
