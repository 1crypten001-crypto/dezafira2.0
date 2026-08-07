<script lang="ts">
  import type { PageData } from './$types';
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import { t, formatMoney } from '$lib/i18n';

  let { data }: { data: PageData } = $props();
  const lang = $derived(data.settings?.site_language || $page.data.language || 'pt');
  const paymentGateway = $derived(data.paymentGateway || $page.data.paymentGateway || 'asaas');
  const displayCurrency = $derived(($page.data.displayCurrency as string) || 'BRL');

  function formatPrice(cents: number) {
    return formatMoney(lang, cents, displayCurrency);
  }

  const faq1a = $derived(
    paymentGateway === 'stripe' ? t(lang, 'premium_page.faq_1_a_stripe') : t(lang, 'premium_page.faq_1_a_asaas')
  );
  const faq3a = $derived(
    paymentGateway === 'stripe' ? t(lang, 'premium_page.faq_3_a_stripe') : t(lang, 'premium_page.faq_3_a_asaas')
  );

  onMount(() => {
    const params = new URLSearchParams(window.location.search);
    const planId = params.get('plan_id');
    const auto = params.get('auto') === '1';
    
    if (planId && auto) {
      const form = document.querySelector(`form[data-plan-id="${planId}"]`) as HTMLFormElement;
      if (form) {
        form.submit();
      }
    }
  });
</script>

<svelte:head>
  <title>{data.settings?.site_title || "Blog"} | {t(lang, "premium_page.badge")}</title>
  <meta name="description" content={t(lang, "premium_page.meta_desc")} />
</svelte:head>

<div class="premium-page">
  <div class="premium-header">
    <span class="premium-badge">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
      </svg>
      {t(lang, "premium_page.badge")}
    </span>
    <h1>{t(lang, "premium_page.title")}</h1>
    <p class="subtitle">{t(lang, "premium_page.subtitle")}</p>
  </div>

  {#if data.plans.length === 0}
    <div class="empty-state">
      <p>{t(lang, "premium_page.empty")}</p>
    </div>
  {:else}
    <div class="plans-grid">
      {#each data.plans as plan}
        <div class="plan-card" class:featured={plan.features && plan.features.length > 3}>
          {#if plan.features && plan.features.length > 3}
            <span class="featured-badge">{t(lang, "premium_page.most_popular")}</span>
          {/if}
          <div class="plan-header">
            <h2 class="plan-name">{plan.name}</h2>
            {#if plan.description}
              <p class="plan-description">{plan.description}</p>
            {/if}
          </div>
          <div class="plan-price">
            <span class="price-value">{formatPrice(plan.price_cents)}</span>
            <span class="price-period">{plan.interval_days === 30 ? t(lang, "premium_page.per_month") : t(lang, "premium_page.per_days", { n: plan.interval_days })}</span>
          </div>
          {#if plan.features}
            <ul class="plan-features">
              {#each plan.features as feature}
                <li>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
                  {feature}
                </li>
              {/each}
            </ul>
          {/if}
          <div class="premium-subscription-actions" style="display: flex; flex-direction: column; gap: 0.5rem; width: 100%;">
            {#if !data.paymentConfigured}
              <p class="gateway-offline">{t(lang, "premium_page.gateway_offline")}</p>
            {:else if data.paymentGateway === 'stripe'}
              <form method="POST" action="?/subscribe" data-plan-id={plan.id} style="width: 100%;">
                <input type="hidden" name="plan_id" value={plan.id} />
                <button type="submit" class="btn btn-primary btn-full" style="display: flex; justify-content: center; align-items: center; gap: 0.5rem; width: 100%;">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="1" y="4" width="22" height="16" rx="2" ry="2"/><line x1="1" y1="10" x2="23" y2="10"/>
                  </svg>
                  <span>{t(lang, "premium_page.subscribe_stripe")}</span>
                </button>
              </form>
            {:else}
              <!-- Asaas default: PIX + Cartão (produção) -->
              <form method="POST" action="?/subscribe" data-plan-id={plan.id} style="width: 100%;">
                <input type="hidden" name="plan_id" value={plan.id} />
                <input type="hidden" name="method" value="pix" />
                <button type="submit" class="btn btn-primary btn-full btn-pix" style="display: flex; justify-content: center; align-items: center; gap: 0.5rem; width: 100%;">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M12 2L2 12l10 10 10-10L12 2z"/>
                    <path d="M12 7l-5 5 5 5 5-5-5-5z"/>
                  </svg>
                  <span>{t(lang, "premium_page.subscribe_pix")}</span>
                </button>
              </form>

              <form method="POST" action="?/subscribe" data-plan-id={plan.id} style="width: 100%;">
                <input type="hidden" name="plan_id" value={plan.id} />
                <input type="hidden" name="method" value="credit_card" />
                <button type="submit" class="btn btn-secondary btn-full" style="display: flex; justify-content: center; align-items: center; gap: 0.5rem; width: 100%;">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="1" y="4" width="22" height="16" rx="2" ry="2"/><line x1="1" y1="10" x2="23" y2="10"/>
                  </svg>
                  <span>{t(lang, "premium_page.subscribe_card")}</span>
                </button>
              </form>
            {/if}
          </div>
        </div>
      {/each}
    </div>
  {/if}

  <div class="faq-section">
    <h2>{t(lang, "premium_page.faq_title")}</h2>
    <div class="faq-grid">
      <div class="faq-item">
        <h3>{t(lang, "premium_page.faq_1_q")}</h3>
        <p>{faq1a}</p>
      </div>
      <div class="faq-item">
        <h3>{t(lang, "premium_page.faq_2_q")}</h3>
        <p>{t(lang, "premium_page.faq_2_a")}</p>
      </div>
      <div class="faq-item">
        <h3>{t(lang, "premium_page.faq_3_q")}</h3>
        <p>{faq3a}</p>
      </div>
      <div class="faq-item">
        <h3>{t(lang, "premium_page.faq_4_q")}</h3>
        <p>{t(lang, "premium_page.faq_4_a")}</p>
      </div>
    </div>
  </div>
</div>

<style>
  .premium-page {
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem 0;
  }

  .gateway-offline {
    margin: 0;
    padding: 0.75rem;
    font-size: 0.85rem;
    color: #92400e;
    background: #fffbeb;
    border: 1px solid #fde68a;
    border-radius: 8px;
    text-align: center;
  }

  .premium-header {
    text-align: center;
    margin-bottom: 3rem;
  }

  .premium-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
    color: white;
    padding: 0.5rem 1rem;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 1rem;
  }

  h1 {
    font-family: var(--font-serif);
    font-size: clamp(2rem, 5vw, 3rem);
    font-weight: 600;
    margin-bottom: 0.75rem;
  }

  .subtitle {
    font-size: 1.1rem;
    color: var(--text-secondary);
    max-width: 500px;
    margin: 0 auto;
  }

  .plans-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 2rem;
    margin-bottom: 4rem;
  }

  .plan-card {
    position: relative;
    background: var(--bg-primary);
    border: 1px solid var(--border-light);
    border-radius: 20px;
    padding: 2rem;
    display: flex;
    flex-direction: column;
    transition: transform 0.3s ease, box-shadow 0.3s ease;
  }

  .plan-card:hover {
    transform: translateY(-4px);
    box-shadow: var(--shadow-lg);
  }

  .plan-card.featured {
    border-color: var(--accent-color, #f59e0b);
    box-shadow: 0 0 0 1px var(--accent-color, #f59e0b);
  }

  .featured-badge {
    position: absolute;
    top: -12px;
    left: 50%;
    transform: translateX(-50%);
    background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
    color: white;
    padding: 0.35rem 1rem;
    border-radius: 20px;
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .plan-header {
    margin-bottom: 1.5rem;
  }

  .plan-name {
    font-family: var(--font-sans);
    font-size: 1.25rem;
    font-weight: 700;
    margin-bottom: 0.5rem;
  }

  .plan-description {
    font-size: 0.9rem;
    color: var(--text-secondary);
    line-height: 1.5;
  }

  .plan-price {
    display: flex;
    align-items: baseline;
    gap: 0.25rem;
    margin-bottom: 1.5rem;
    padding-bottom: 1.5rem;
    border-bottom: 1px solid var(--border-light);
  }

  .price-value {
    font-size: 2.5rem;
    font-weight: 700;
    color: var(--text-primary);
  }

  .price-period {
    font-size: 0.9rem;
    color: var(--text-muted);
  }

  .plan-features {
    list-style: none;
    padding: 0;
    margin: 0 0 2rem 0;
    flex: 1;
  }

  .plan-features li {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.5rem 0;
    font-size: 0.9rem;
    color: var(--text-secondary);
  }

  .plan-features svg {
    color: #10b981;
    flex-shrink: 0;
  }

  .btn-pix {
    background: #32bcad;
    border-color: #32bcad;
    color: white;
  }

  .btn-pix:hover {
    background: #2a9f92;
    border-color: #2a9f92;
  }

  .btn-full {
    width: 100%;
    padding: 1rem;
  }

  .faq-section {
    background: var(--bg-primary);
    border-radius: 20px;
    padding: 3rem;
    border: 1px solid var(--border-light);
  }

  .faq-section h2 {
    font-family: var(--font-serif);
    font-size: 1.75rem;
    text-align: center;
    margin-bottom: 2rem;
  }

  .faq-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    gap: 2rem;
  }

  .faq-item h3 {
    font-family: var(--font-sans);
    font-size: 1rem;
    font-weight: 600;
    margin-bottom: 0.5rem;
  }

  .faq-item p {
    font-size: 0.9rem;
    color: var(--text-secondary);
    line-height: 1.6;
  }

  .empty-state {
    text-align: center;
    padding: 4rem 2rem;
    background: var(--bg-primary);
    border-radius: 20px;
    border: 1px solid var(--border-light);
  }

  @media (max-width: 768px) {
    .faq-section {
      padding: 2rem 1.5rem;
    }

    .plans-grid {
      grid-template-columns: 1fr;
    }
  }
</style>