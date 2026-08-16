<script lang="ts">
  import { page } from '$app/stores';
  import { t, formatMoney, formatDate as formatDateI18n, memberErrorMessage } from '$lib/i18n';
  import { enhance } from "$app/forms";
  
  let { data, form } = $props();
  const lang = $derived($page.data.language || 'pt');
  const paymentGateway = $derived(data.paymentGateway || $page.data.paymentGateway || 'asaas');
  const requiresCpf = $derived(data.requiresCpf ?? paymentGateway !== 'stripe');
  const displayCurrency = $derived(($page.data.displayCurrency as string) || 'BRL');
  let loading = $state(false);
  let profileLoading = $state(false);

  let nameValue = $state(data.user?.name || '');
  let cpfValue = $state(data.user?.cpf || '');
  let phoneValue = $state(data.user?.phone || '');

  const hasProfileError = $derived($page.url.searchParams.get('error') === 'update_profile');
  const formError = $derived(memberErrorMessage(lang, form?.error));
  const formSuccess = $derived(memberErrorMessage(lang, form?.success));

  const profileDesc = $derived(
    paymentGateway === 'stripe'
      ? t(lang, 'members.profile_desc_stripe')
      : t(lang, 'members.profile_desc_asaas')
  );
  const profileIncompleteMsg = $derived(
    paymentGateway === 'stripe'
      ? t(lang, 'members.profile_incomplete_payment_stripe')
      : t(lang, 'members.profile_incomplete_payment')
  );

  function formatDate(isoString: string | null) {
    if (!isoString) return t(lang, 'members.na');
    return formatDateI18n(lang, isoString, {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    });
  }

  function formatPrice(cents: number) {
    return formatMoney(lang, cents, displayCurrency);
  }

  function canCancelSubscription(sub: any): boolean {
    if (!sub || sub.status !== 'active') return false;
    if (sub.asaas_subscription_id) return true;
    if (sub.stripe_subscription_id && !String(sub.stripe_subscription_id).startsWith('cs_pending:')) {
      return true;
    }
    return false;
  }

  function getStatusLabel(status: string) {
    switch (status) {
      case 'active': return t(lang, 'members.status_active');
      case 'pending': return t(lang, 'members.status_pending');
      case 'cancelled': return t(lang, 'members.status_cancelled');
      case 'approved':
      case 'confirmed':
      case 'completed':
        return t(lang, 'members.approved');
      default: return status;
    }
  }

  function paymentMethodLabel(method: string | null | undefined) {
    if (!method) return t(lang, 'members.payment_method_card_pix');
    const m = String(method).toLowerCase();
    if (m === 'card_pix' || method === 'Cartão/Pix' || method === 'Card/Pix') {
      return t(lang, 'members.payment_method_card_pix');
    }
    if (m === 'stripe' || m === 'card' || m === 'credit_card') {
      return t(lang, 'members.payment_method_stripe');
    }
    if (m === 'pix') return t(lang, 'common.pix');
    return method;
  }

  function intervalLabel(intervalDays: number | null | undefined) {
    if (!intervalDays || intervalDays === 30) return t(lang, 'members.per_month');
    return t(lang, 'members.per_days', { n: String(intervalDays) });
  }

  // Format CPF on the fly (e.g. 000.000.000-00)
  function formatCPF(val: string) {
    const clean = val.replace(/\D/g, '').substring(0, 11);
    if (clean.length <= 3) return clean;
    if (clean.length <= 6) return `${clean.substring(0, 3)}.${clean.substring(3)}`;
    if (clean.length <= 9) return `${clean.substring(0, 3)}.${clean.substring(3, 6)}.${clean.substring(6)}`;
    return `${clean.substring(0, 3)}.${clean.substring(3, 6)}.${clean.substring(6, 9)}-${clean.substring(9)}`;
  }

  // Format Phone on the fly (e.g. (00) 00000-0000)
  function formatPhone(val: string) {
    const clean = val.replace(/\D/g, '').substring(0, 11);
    if (clean.length <= 2) return clean;
    if (clean.length <= 6) return `(${clean.substring(0, 2)}) ${clean.substring(2)}`;
    if (clean.length <= 10) return `(${clean.substring(0, 2)}) ${clean.substring(2, 6)}-${clean.substring(6)}`;
    return `(${clean.substring(0, 2)}) ${clean.substring(2, 7)}-${clean.substring(7)}`;
  }
</script>

<svelte:head>
  <title>{t(lang, "members.dashboard_title")} | {t(lang, "members.area_title")}</title>
</svelte:head>

<div class="dashboard-container">
  <!-- Header -->
  <div class="dashboard-header">
    <div>
      <h1>{t(lang, "members.dashboard_title")}</h1>
      <p class="subtitle">{t(lang, "members.welcome", { user: data.user?.username || '' })}</p>
    </div>
    <form method="POST" action="/members/logout">
      <button type="submit" class="btn btn-secondary btn-logout">
        {t(lang, "members.logout_account")}
      </button>
    </form>
  </div>

  {#if hasProfileError}
    <div class="alert warning">
      {profileIncompleteMsg}
    </div>
  {/if}

  {#if formError}
    <div class="alert error">{formError}</div>
  {/if}

  {#if formSuccess}
    <div class="alert success">{formSuccess}</div>
  {/if}

  <div class="dashboard-grid">
    <div class="dashboard-col">
      <!-- Profile Card -->
      <div class="card profile-card">
        <h2>{t(lang, "members.profile_data")}</h2>
        <p class="card-desc">{profileDesc}</p>
        
        <form 
          method="POST" 
          action="?/updateProfile" 
          use:enhance={() => {
            profileLoading = true;
            return async ({ update }) => {
              profileLoading = false;
              await update();
            };
          }}
          class="profile-form"
        >
          <input type="hidden" name="redirectTo" value={$page.url.searchParams.get('redirectTo') || ''} />
          <div class="form-group">
            <label for="name">{t(lang, "members.full_name")}</label>
            <input 
              type="text" 
              id="name" 
              name="name" 
              bind:value={nameValue} 
              placeholder={t(lang, "members.full_name_placeholder")} 
              required 
              disabled={profileLoading}
            />
          </div>

          <div class="form-group">
            <label for="cpf">{requiresCpf ? t(lang, "members.cpf") : t(lang, "members.cpf_optional")}</label>
            <input 
              type="text" 
              id="cpf" 
              name="cpf" 
              value={formatCPF(cpfValue)}
              oninput={(e) => cpfValue = e.currentTarget.value}
              placeholder={t(lang, "members.cpf_placeholder")} 
              required={requiresCpf}
              disabled={profileLoading}
            />
          </div>

          <div class="form-group">
            <label for="phone">{t(lang, "members.phone_optional")}</label>
            <input 
              type="text" 
              id="phone" 
              name="phone" 
              value={formatPhone(phoneValue)}
              oninput={(e) => phoneValue = e.currentTarget.value}
              placeholder={t(lang, "members.phone_placeholder")} 
              disabled={profileLoading}
            />
          </div>

          <button 
            type="submit" 
            class="btn btn-primary btn-full" 
            disabled={profileLoading}
            style="margin-top: 1rem;"
          >
            {profileLoading ? t(lang, "members.saving") : t(lang, "members.save_profile")}
          </button>
        </form>
      </div>

      <!-- Courses Quick Access -->
      <div class="card courses-card">
        <div class="courses-card-icon">🎓</div>
        <h2>{t(lang, "members.area_title")}</h2>
        <p>{t(lang, "members.welcome_area")}</p>
        <a href="/members/area" class="btn btn-primary courses-btn">{t(lang, "members.access_courses")}</a>
      </div>
    </div>

    <div class="dashboard-col">
      <!-- Subscription Card -->
      <div class="card subscription-card">
        <h2>{t(lang, "members.premium_sub")}</h2>
        
        {#if data.subscription}
          <div class="sub-info">
            <div class="info-row">
              <span class="info-label">{t(lang, "members.plan")}</span>
              <span class="info-value plan-name">{data.subscription.plan_name}</span>
            </div>

            <div class="info-row">
              <span class="info-label">{t(lang, "members.price")}</span>
              <span class="info-value">{formatPrice(data.subscription.price_cents)}{intervalLabel(data.subscription.interval_days)}</span>
            </div>

            <div class="info-row">
              <span class="info-label">{t(lang, "members.status")}</span>
              <span class="status-badge {data.subscription.status}">
                {getStatusLabel(data.subscription.status)}
              </span>
            </div>

            <div class="info-row">
              <span class="info-label">{t(lang, "members.valid_until")}</span>
              <span class="info-value">{formatDate(data.subscription.expires_at)}</span>
            </div>
          </div>

          {#if canCancelSubscription(data.subscription)}
            <form 
              method="POST" 
              action="?/cancel" 
              use:enhance={() => {
                loading = true;
                return async ({ update }) => {
                  loading = false;
                  await update();
                };
              }}
              class="cancel-form"
            >
              <button 
                type="submit" 
                class="btn btn-outline btn-cancel" 
                disabled={loading}
              >
                {loading ? t(lang, "members.cancelling") : t(lang, "members.cancel_sub")}
              </button>
            </form>
          {/if}
        {:else}
          <div class="empty-subscription">
            <p>{t(lang, "members.no_sub")}</p>
            <a href="/premium" class="btn btn-primary">{t(lang, "members.view_plans")}</a>
          </div>
        {/if}
      </div>

      <!-- Purchased Products Card -->
      <div class="card purchased-products-card">
        <h2>{t(lang, "members.my_downloads")}</h2>
        {#if data.purchasedProducts && data.purchasedProducts.length > 0}
          <div class="purchased-products-list">
            {#each data.purchasedProducts as product}
              <div class="purchased-product-item">
                {#if product.image_url}
                  <img src={product.image_url} alt={product.name} class="purchased-product-thumb" />
                {:else}
                  <div class="purchased-product-icon">
                    {#if product.file_url}
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>
                      </svg>
                    {:else}
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/>
                      </svg>
                    {/if}
                  </div>
                {/if}
                <div class="purchased-product-info">
                  <span class="purchased-product-name" title={product.name}>{product.name}</span>
                  {#if product.description}
                    <span class="purchased-product-desc" title={product.description}>{product.description}</span>
                  {/if}
                </div>
                <div class="purchased-product-action">
                  {#if product.file_url || product.external_link}
                    <a href="/api/download/{product.id}" rel="external" class="btn btn-small btn-primary">
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>
                      </svg>
                      {product.file_url ? t(lang, "members.download") : t(lang, "members.access")}
                    </a>
                  {/if}
                  <a href="/product/{product.slug}" class="btn btn-small btn-outline">
                    {t(lang, "members.view_page")}
                  </a>
                </div>
              </div>
            {/each}
          </div>
        {:else}
          <div class="empty-purchased-products">
            <p>{t(lang, "members.no_products")}</p>
          </div>
        {/if}
      </div>

      <!-- Payment History -->
      <div class="card payments-card">
        <h2>{t(lang, "members.payments_history")}</h2>
        {#if data.payments && data.payments.length > 0}
          <div class="table-responsive">
            <table class="payments-table">
              <thead>
                <tr>
                  <th>{t(lang, "members.date")}</th>
                  <th>{t(lang, "members.amount")}</th>
                  <th>{t(lang, "members.payment_method")}</th>
                  <th>{t(lang, "members.status")}</th>
                </tr>
              </thead>
              <tbody>
                {#each data.payments as payment}
                  <tr>
                    <td>{formatDate(payment.created_at)}</td>
                    <td>{formatPrice(payment.amount_cents)}</td>
                    <td>{paymentMethodLabel(payment.payment_method)}</td>
                    <td>
                      <span class="status-badge {payment.status}">
                        {getStatusLabel(payment.status)}
                      </span>
                    </td>
                  </tr>
                {/each}
              </tbody>
            </table>
          </div>
        {:else}
          <p class="empty-payments">{t(lang, "members.no_payments")}</p>
        {/if}
      </div>
    </div>
  </div>
</div>

<style>
  .dashboard-container {
    max-width: 1200px;
    margin: 3rem auto;
    padding: 0 1.5rem;
    /* Previne scroll lateral causado por conteúdo interno */
    overflow-x: hidden;
  }

  .courses-card {
    text-align: center;
    padding: 2.5rem 2rem;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.75rem;
  }
  .courses-card-icon { font-size: 3rem; }
  .courses-card h2 { font-size: 1.25rem; font-weight: 700; margin: 0; }
  .courses-card p { color: var(--text-secondary); font-size: 0.9rem; margin: 0; }
  .courses-btn { margin-top: 0.5rem; }

  .dashboard-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 2.5rem;
    gap: 1.5rem;
  }

  h1 {
    font-size: 2.25rem;
    font-weight: 800;
    letter-spacing: -0.5px;
    margin-bottom: 0.25rem;
  }

  .subtitle {
    font-size: 1rem;
    color: var(--text-secondary);
  }

  .btn-logout {
    padding: 0.6rem 1.2rem;
    font-size: 0.875rem;
    border: 1px solid var(--border-color);
  }

  .btn-logout:hover {
    background: var(--bg-secondary);
    color: var(--text-primary);
  }

  .alert {
    padding: 1rem;
    border-radius: var(--radius-md);
    font-size: 0.9rem;
    margin-bottom: 2rem;
  }

  .error {
    background: #fef2f2;
    color: #dc2626;
    border: 1px solid #fee2e2;
  }

  .success {
    background: #ecfdf5;
    color: #059669;
    border: 1px solid #d1fae5;
  }

  .warning {
    background: #fffbeb;
    color: #92400e;
    border: 1px solid #fde68a;
  }

  .dashboard-grid {
    display: grid;
    grid-template-columns: minmax(0, 1fr) minmax(0, 1.2fr);
    gap: 2rem;
    align-items: start;
    width: 100%;
  }

  @media (max-width: 1000px) {
    .dashboard-grid {
      grid-template-columns: minmax(0, 1fr);
    }
  }

  .dashboard-col {
    display: flex;
    flex-direction: column;
    gap: 2rem;
    min-width: 0;
  }

  .card-desc {
    color: var(--text-secondary);
    font-size: 0.85rem;
    margin-bottom: 1.5rem;
    line-height: 1.5;
  }

  .profile-form {
    display: flex;
    flex-direction: column;
    gap: 1.25rem;
  }

  .profile-form .form-group {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .profile-form label {
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    font-weight: 600;
    color: var(--text-secondary);
  }

  .profile-form input {
    width: 100%;
    padding: 0.75rem;
    border: 1px solid var(--border-color);
    border-radius: var(--radius-md);
    background: var(--bg-secondary);
    color: var(--text-primary);
    font-size: 0.95rem;
    transition: all 0.2s;
  }

  .profile-form input:focus {
    outline: none;
    border-color: var(--text-primary);
    background: var(--bg-primary);
  }

  .card {
    background: var(--bg-primary);
    border: 1px solid var(--border-light);
    border-radius: var(--radius-lg);
    padding: 2rem;
    box-shadow: var(--shadow-sm);
    min-width: 0;
  }

  .card h2 {
    font-size: 1.25rem;
    font-weight: 700;
    margin-bottom: 1.5rem;
    padding-bottom: 0.75rem;
    border-bottom: 1px solid var(--border-light);
  }

  .sub-info {
    display: flex;
    flex-direction: column;
    gap: 1.25rem;
    margin-bottom: 2rem;
  }

  .info-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.95rem;
  }

  .info-label {
    color: var(--text-secondary);
    font-weight: 500;
  }

  .info-value {
    color: var(--text-primary);
    font-weight: 600;
  }

  .plan-name {
    color: var(--accent-color, #4a90d9);
  }

  .status-badge {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: var(--radius-full);
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .status-badge.active,
  .status-badge.approved,
  .status-badge.confirmed {
    background: #d1fae5;
    color: #065f46;
  }

  .status-badge.pending {
    background: #fef3c7;
    color: #92400e;
  }

  .status-badge.cancelled {
    background: #f3f4f6;
    color: #374151;
  }

  .cancel-form {
    margin-top: 1.5rem;
  }

  .btn-cancel {
    width: 100%;
    border-color: #fca5a5;
    color: #ef4444;
  }

  .btn-cancel:hover {
    background: #fef2f2;
    color: #b91c1c;
  }

  .empty-subscription {
    text-align: center;
    padding: 2.5rem 1rem;
  }

  .empty-subscription p {
    color: var(--text-secondary);
    margin-bottom: 1.5rem;
    font-size: 0.95rem;
  }

  .table-responsive {
    overflow-x: auto;
    width: 100%;
  }

  .payments-table {
    width: 100%;
    border-collapse: collapse;
    text-align: left;
    font-size: 0.9rem;
  }

  .payments-table th,
  .payments-table td {
    padding: 1rem;
    border-bottom: 1px solid var(--border-light);
  }

  .payments-table th {
    color: var(--text-secondary);
    font-weight: 600;
    text-transform: uppercase;
    font-size: 0.75rem;
    letter-spacing: 0.5px;
  }

  .payments-table td {
    color: var(--text-primary);
  }

  .empty-payments {
    color: var(--text-secondary);
    text-align: center;
    padding: 3rem 0;
  }

  .purchased-products-list {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    width: 100%;
  }

  .purchased-product-item {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.875rem 1rem;
    background: var(--bg-secondary);
    border: 1px solid var(--border-light);
    border-radius: var(--radius-md);
    min-width: 0;
    width: 100%;
    overflow: hidden;
    box-sizing: border-box;
  }

  .purchased-product-thumb {
    width: 48px;
    height: 48px;
    object-fit: cover;
    border-radius: var(--radius-sm);
    border: 1px solid var(--border-color);
    background: var(--bg-primary);
    flex-shrink: 0;
  }

  .purchased-product-icon {
    width: 48px;
    height: 48px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: var(--radius-sm);
    border: 1px dashed var(--border-color);
    background: var(--bg-primary);
    color: var(--text-muted);
    flex-shrink: 0;
  }

  .purchased-product-info {
    display: flex;
    flex-direction: column;
    gap: 0.15rem;
    flex: 1;
    min-width: 0;
  }

  .purchased-product-name {
    font-weight: 600;
    font-size: 0.9rem;
    color: var(--text-primary);
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
    text-overflow: ellipsis;
    line-height: 1.3;
    word-break: break-word;
  }

  .purchased-product-desc {
    font-size: 0.75rem;
    color: var(--text-muted);
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
    text-overflow: ellipsis;
    line-height: 1.4;
    word-break: break-word;
  }

  .purchased-product-action {
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
    align-items: flex-end;
    flex-shrink: 0;
    margin-left: auto;
  }

  .btn-outline {
    border: 1px solid var(--border-color);
    background: transparent;
    color: var(--text-primary);
  }

  .btn-outline:hover {
    background: var(--bg-secondary);
    border-color: var(--border-dark);
  }

  .purchased-product-action .btn {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    padding: 0.4rem 0.75rem;
    font-size: 0.75rem;
    font-weight: 600;
    height: auto;
  }

  .empty-purchased-products {
    color: var(--text-muted);
    text-align: center;
    padding: 2rem 0;
    font-size: 0.9rem;
  }
</style>
