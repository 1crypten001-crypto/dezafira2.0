<script lang="ts">
  import { onMount } from 'svelte';
  import { page } from "$app/stores";
  import { enhance } from "$app/forms";
  import { optimizeImageUrl } from "$lib/image-optimizer";
  import { t, formatMoney } from "$lib/i18n";
  import type { Product } from "$lib/types";

  let {
    data,
    form
  }: {
    data: {
      product: Product;
      hasPurchased: boolean;
      purchaseStatus: string | null;
      hasReviewed: boolean;
      reviews: any[];
      reviewSummary: { averageRating: number; totalCount: number };
      settings?: Record<string, string>;
      user?: any;
      relatedProducts: Product[];
    };
    form: any;
  } = $props();

  const lang = $derived(data.settings?.site_language || $page.data.language || 'pt');
  const paymentGateway = $derived($page.data.paymentGateway || 'asaas');
  const displayCurrency = $derived(($page.data.displayCurrency as string) || 'BRL');
  const securePaymentLabel = $derived(
    paymentGateway === 'stripe'
      ? t(lang, 'product.secure_payment_stripe')
      : t(lang, 'product.secure_payment_asaas')
  );

  let isDescExpanded = $state(false);
  let videoExpanded = $state(false);
  // Para produtos com entrega manual: captura o Gmail/GitHub do comprador
  let buyerAccessId = $state('');
  const isManual = $derived(data.product.resource_type === 'manual');

  // Serviço Extra / Order Bump
  let includeExtraService = $state(false);
  const currentTotalPriceCents = $derived(
    data.product.price_cents + (includeExtraService && data.product.has_extra_service === 1 ? (data.product.extra_service_price_cents || 0) : 0)
  );
  const extraQuery = $derived(includeExtraService ? '&extra=1' : '');
  const accessLabel = $derived(data.product.access_label || t(lang, 'product.access_email_label'));
  const buyerIdValid = $derived(buyerAccessId.trim().length >= 3);

  // Estado de carregamento do download (UX Premium)
  let isDownloading = $state(false);

  function handleDownloadClick(e: MouseEvent) {
    if (isDownloading) {
      e.preventDefault();
      return;
    }
    isDownloading = true;
    
    console.log("=== INICIANDO DOWNLOAD SEGURO ===");
    console.log("Produto ID:", data.product.id);
    console.log("Iniciando requisição do arquivo...");

    // Libera o botão novamente após 5 segundos
    setTimeout(() => {
      isDownloading = false;
    }, 5000);
  }

  // Estados reativos para o formulário de avaliação por estrelas
  let userRating = $state(0);
  let hoveredRating = $state(0);
  let reviewComment = $state('');
  let isSubmittingReview = $state(false);
  let ratingErrorMessage = $state('');

  function getYouTubeId(url: string): string | null {
    if (!url) return null;
    const regExp = /^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|\&v=|shorts\/)([^#\&\?]*).*/;
    const match = url.match(regExp);
    return (match && match[2].length === 11) ? match[2] : null;
  }

  const videoId = $derived(getYouTubeId(data.product.youtube_video_url || ''));

  onMount(() => {
    if (videoId) {
      setTimeout(() => {
        videoExpanded = true;
      }, 2000);
    }
  });

  function formatPrice(cents: number) {
    if (cents === 0) return t(lang, 'product.free');
    return formatMoney(lang, cents, displayCurrency);
  }

  function getPlaceholderBackground(id: any) {
    const gradients = [
      'linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%)', // Blue
      'linear-gradient(135deg, #10b981 0%, #047857 100%)', // Emerald
      'linear-gradient(135deg, #f59e0b 0%, #b45309 100%)', // Amber
      'linear-gradient(135deg, #ec4899 0%, #be185d 100%)', // Pink
      'linear-gradient(135deg, #8b5cf6 0%, #6d28d9 100%)', // Purple
      'linear-gradient(135deg, #f97316 0%, #c2410c 100%)', // Orange
      'linear-gradient(135deg, #14b8a6 0%, #0f766e 100%)', // Teal
      'linear-gradient(135deg, #f43f5e 0%, #be123c 100%)', // Rose
      'linear-gradient(135deg, #6366f1 0%, #4338ca 100%)'  // Indigo
    ];
    const hash = String(id).charCodeAt(0) || 0;
    const index = hash % gradients.length;
    return gradients[index];
  }

  const siteTitle = $derived(data.settings?.site_title || "Blog");
</script>

<svelte:head>
  <title>{data.product.name} | {siteTitle}</title>
  <meta name="description" content={data.product.description || `Adquira já o produto digital ${data.product.name}`} />
  
  <!-- Open Graph -->
  <meta property="og:title" content={`${data.product.name} | ${siteTitle}`} />
  <meta property="og:description" content={data.product.description || `Adquira já o produto digital ${data.product.name}`} />
  <meta property="og:type" content="product" />
  <meta property="og:url" content={$page.url.href} />
  {#if data.product.image_url}
    <meta property="og:image" content={data.product.image_url} />
  {/if}

  <!-- Twitter Card -->
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content={`${data.product.name} | ${siteTitle}`} />
  <meta name="twitter:description" content={data.product.description || `Adquira já o produto digital ${data.product.name}`} />
</svelte:head>

<div class="product-page-container">
  <div class="back-nav">
    <a href="/" class="btn-back">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
        <line x1="19" y1="12" x2="5" y2="12"/><polyline points="12 19 5 12 12 5"/>
      </svg>
      <span>{t(lang, "product.back_to_blog")}</span>
    </a>
  </div>

  <div class="product-main-card">
    <div class="product-grid">
      <!-- Coluna Esquerda: Imagem -->
      <div class="product-media-column">
        {#if data.product.image_url}
          <img src={optimizeImageUrl(data.product.image_url, 600, 600)} alt={data.product.name} class="product-main-image" />
        {:else}
          <div class="product-placeholder-gradient" style="background: {getPlaceholderBackground(data.product.id)}">
            <div class="placeholder-icon-wrapper">
              {#if data.product.file_url}
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>
                </svg>
              {:else}
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/>
                </svg>
              {/if}
            </div>
          </div>
        {/if}
      </div>

      <!-- Coluna Direita: Informações e Compra -->
      <div class="product-details-column">
        <div class="product-badge">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/>
          </svg>
          <span>{t(lang, 'product.digital_resource')}</span>
        </div>

        <h1 class="product-title">{data.product.name}</h1>

        {#if data.reviewSummary}
          <div class="product-rating-summary-compact">
            {#if data.reviewSummary.totalCount > 0}
              <div class="stars-gold-compact">
                {#each Array(5) as _, i}
                  <svg width="15" height="15" viewBox="0 0 24 24" fill={i < Math.round(data.reviewSummary.averageRating) ? "#fbbf24" : "none"} stroke="#fbbf24" stroke-width="2">
                    <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
                  </svg>
                {/each}
              </div>
              <span class="rating-value">{data.reviewSummary.averageRating}</span>
              <span class="rating-count">({data.reviewSummary.totalCount} {data.reviewSummary.totalCount === 1 ? t(lang, 'reviews.count_badge_singular') : t(lang, 'reviews.count_badge_plural')})</span>
            {:else}
              <span class="no-ratings-yet">★ {t(lang, 'reviews.no_ratings')}</span>
            {/if}
          </div>
        {/if}

        {#if data.product.is_premium_included && data.product.is_premium_included >= 1 && !data.hasPurchased}
          <div class="premium-badge-banner">
            <span class="sparkle-icon">⭐</span>
            <div class="banner-content">
              <h4>{t(lang, 'product.included_in_premium')}</h4>
              <p>{t(lang, 'product.premium_promo_desc')}</p>
            </div>
            <a href="/premium" class="btn-premium-link">{t(lang, 'product.subscribe_premium_btn')}</a>
          </div>
        {/if}

        <div class="price-section">
          <span class="price-label">{t(lang, 'product.value')}:</span>
          <span class="price-tag" class:free-price={data.product.price_cents <= 0}>
            {formatPrice(currentTotalPriceCents)}
          </span>
        </div>

        <div class="action-card">
          {#if data.product.price_cents > 0 && !data.hasPurchased}
            <!-- Oferta de Serviço Extra (Order Bump) no Checkout -->
            {#if data.product.has_extra_service === 1 && data.product.extra_service_title && data.user}
              <div class="order-bump-box" class:bump-active={includeExtraService} style="background: #f0f9ff; border: 2px dashed #0284c7; border-radius: 12px; padding: 1.1rem; margin-bottom: 1.25rem; transition: all 0.2s ease;">
                <label style="display: flex; align-items: flex-start; gap: 0.85rem; cursor: pointer; user-select: none; margin: 0;">
                  <input type="checkbox" bind:checked={includeExtraService} style="width: 20px; height: 20px; accent-color: #0284c7; margin-top: 2px; cursor: pointer; flex-shrink: 0;" />
                  <div style="display: flex; flex-direction: column; width: 100%;">
                    <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 0.35rem;">
                      <span style="background: #0284c7; color: #fff; font-size: 0.65rem; font-weight: 800; padding: 2px 6px; border-radius: 4px; letter-spacing: 0.05em; text-transform: uppercase;">
                        ⚡ SERVIÇO EXTRA OPIONAL
                      </span>
                      <span style="font-size: 0.95rem; font-weight: 800; color: #0284c7; margin-left: auto;">
                        + {formatPrice(data.product.extra_service_price_cents || 0)}
                      </span>
                    </div>
                    <span style="font-size: 0.95rem; font-weight: 700; color: #0369a1; line-height: 1.3;">
                      Adicionar {data.product.extra_service_title}
                    </span>
                    {#if data.product.extra_service_description}
                      <p style="font-size: 0.825rem; color: #334155; line-height: 1.45; margin: 0.4rem 0 0 0;">
                        {data.product.extra_service_description}
                      </p>
                    {/if}
                  </div>
                </label>
              </div>
            {/if}

            <!-- Produto Pago Não Adquirido -->
            {#if data.settings?.enable_member_login !== '1'}
              <button class="btn btn-full btn-disabled" disabled>
                {t(lang, "product.sales_suspended")}
              </button>
            {:else if !data.user}
              <a href="/members/login?redirectTo={encodeURIComponent($page.url.pathname)}" class="btn btn-full btn-primary btn-cta">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                  <path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"/><line x1="3" y1="6" x2="21" y2="6"/><path d="M16 10a4 4 0 0 1-8 0"/>
                </svg>
                <span>{t(lang, "product.login_to_buy")}</span>
              </a>
              <p class="login-hint">{t(lang, "product.account_required")}</p>
            {:else}
              {#if isManual}
                <!-- Produto com entrega manual (Drive, GitHub, etc.) -->
                <!-- Comprador precisa informar Gmail/usuário antes de pagar -->
                <div class="manual-access-form">
                  <label for="buyer-access-id" class="manual-label">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>
                    </svg>
                    {accessLabel} <span class="required-mark">*</span>
                  </label>
                  <input
                    id="buyer-access-id"
                    type="text"
                    class="manual-input"
                    bind:value={buyerAccessId}
                    placeholder={t(lang, "product.access_email_ph")}
                  />
                  <p class="manual-hint">{t(lang, "product.manual_delivery_hint")}</p>

                  {#if buyerIdValid}
                    <div class="payment-buttons-group">
                      {#if $page.data.paymentGateway === 'stripe'}
                        <a href="/purchase/{data.product.id}?buyer_id={encodeURIComponent(buyerAccessId.trim())}{extraQuery}" class="btn btn-full btn-primary btn-cta" data-sveltekit-reload target="_blank" rel="noopener noreferrer">
                          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                            <rect x="1" y="4" width="22" height="16" rx="2" ry="2"/><line x1="1" y1="10" x2="23" y2="10"/>
                          </svg>
                          <span>{t(lang, 'product.checkout_stripe')}</span>
                        </a>
                      {:else}
                        <a href="/purchase/{data.product.id}?method=pix&buyer_id={encodeURIComponent(buyerAccessId.trim())}{extraQuery}" class="btn btn-full btn-primary btn-cta btn-pix" data-sveltekit-reload target="_blank" rel="noopener noreferrer">
                          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M12 2L2 12l10 10 10-10L12 2z"/>
                            <path d="M12 7l-5 5 5 5 5-5-5-5z"/>
                          </svg>
                          <span>{t(lang, 'product.pix_payment')}</span>
                        </a>
                        <a href="/purchase/{data.product.id}?method=credit_card&buyer_id={encodeURIComponent(buyerAccessId.trim())}{extraQuery}" class="btn btn-full btn-secondary btn-cta" data-sveltekit-reload target="_blank" rel="noopener noreferrer">
                          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                            <rect x="1" y="4" width="22" height="16" rx="2" ry="2"/><line x1="1" y1="10" x2="23" y2="10"/>
                          </svg>
                          <span>{t(lang, 'product.card_payment')}</span>
                        </a>
                      {/if}
                    </div>
                  {:else}
                    <button class="btn btn-full btn-disabled" disabled>
                      {t(lang, "product.fill_email")}
                    </button>
                  {/if}
                </div>
              {:else}
                <!-- Produto com arquivo/link padrão -->
                <div class="payment-buttons-group">
                  {#if $page.data.paymentGateway === 'stripe'}
                    <a href="/purchase/{data.product.id}?{extraQuery.replace('&', '')}" class="btn btn-full btn-primary btn-cta" data-sveltekit-reload target="_blank" rel="noopener noreferrer">
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                        <rect x="1" y="4" width="22" height="16" rx="2" ry="2"/><line x1="1" y1="10" x2="23" y2="10"/>
                      </svg>
                      <span>{t(lang, 'product.checkout_stripe')}</span>
                    </a>
                  {:else}
                    <a href="/purchase/{data.product.id}?method=pix{extraQuery}" class="btn btn-full btn-primary btn-cta btn-pix" data-sveltekit-reload target="_blank" rel="noopener noreferrer">
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M12 2L2 12l10 10 10-10L12 2z"/>
                        <path d="M12 7l-5 5 5 5 5-5-5-5z"/>
                      </svg>
                      <span>{t(lang, 'product.pix_payment')}</span>
                    </a>
                    <a href="/purchase/{data.product.id}?method=credit_card{extraQuery}" class="btn btn-full btn-secondary btn-cta" data-sveltekit-reload target="_blank" rel="noopener noreferrer">
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                        <rect x="1" y="4" width="22" height="16" rx="2" ry="2"/><line x1="1" y1="10" x2="23" y2="10"/>
                      </svg>
                      <span>{t(lang, 'product.card_payment')}</span>
                    </a>
                  {/if}
                </div>
              {/if}
              <p class="login-hint">{t(lang, 'product.login_hint')}</p>
            {/if}
          {:else}
            <!-- Produto Gratuito ou Já Adquirido -->
            <div class="download-container">
              {#if isManual && data.purchaseStatus === 'pending_delivery'}
                <!-- Entrega manual aguardando compartilhamento pelo admin -->
                <div class="pending-delivery-badge">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" stroke-width="2.5">
                    <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
                  </svg>
                  <span>{t(lang, 'product.waiting_share')}</span>
                </div>
                <p class="pending-delivery-msg">
                  {t(lang, 'product.waiting_share_msg')}
                  {#if data.product.delivery_deadline}
                    <strong>{t(lang, 'product.delivery_deadline')} {data.product.delivery_deadline}.</strong>
                  {/if}
                </p>
                {#if data.product.drive_instructions}
                  <p class="delivery-instructions">{data.product.drive_instructions}</p>
                {/if}
              {:else if isManual && data.purchaseStatus === 'completed'}
                <!-- Entrega manual concluída -->
                <div class="success-purchase-badge">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#22c55e" stroke-width="2.5">
                    <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>
                  </svg>
                  <span>{t(lang, 'product.access_released')}</span>
                </div>
                {#if data.product.drive_instructions}
                  <p class="delivery-instructions delivered">{data.product.drive_instructions}</p>
                {/if}
              {:else}
                <!-- Produto de arquivo/link adquirido -->
                <div class="success-purchase-badge">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#22c55e" stroke-width="2.5">
                    <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>
                  </svg>
                  <span>{t(lang, 'product.access_released')}</span>
                </div>
                <!-- Botão de download aponta para endpoint seguro (/api/download/[id])  -->
                <!-- O servidor valida o acesso e serve SEMPRE o arquivo atual do produto -->
                <!-- Se o admin trocar o ZIP, todos os compradores recebem a versão nova  -->
                <a
                  href="/api/download/{data.product.id}"
                  rel="external"
                  class="btn btn-full btn-cta"
                  class:btn-primary={!isDownloading}
                  class:btn-disabled={isDownloading}
                  onclick={handleDownloadClick}
                >
                  {#if isDownloading}
                    <!-- Ícone Spinner giratório -->
                    <svg class="animate-spin" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                      <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" style="opacity: 0.25;"/>
                      <path d="M4 12a8 8 0 0 1 8-8V0C5.373 0 0 5.373 0 12h4z" fill="currentColor"/>
                    </svg>
                    <span>{lang === 'pt' ? 'Preparando Download...' : lang === 'es' ? 'Preparando Descarga...' : 'Preparing Download...'}</span>
                  {:else}
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>
                    </svg>
                    <span>{data.product.file_url ? t(lang, 'product.download_file') : t(lang, 'product.access_resource')}</span>
                  {/if}
                </a>
                {#if data.isPremiumAccess}
                  <div style="font-size: 0.8rem; color: #4f46e5; text-align: center; margin-top: 0.75rem; font-weight: 600; display: flex; align-items: center; justify-content: center; gap: 0.25rem;">
                    <span>🌟</span> {t(lang, 'product.premium_granted_msg')}
                  </div>
                {/if}
              {/if}
            </div>
          {/if}
        </div>

        <!-- Trust Badges -->
        <div class="trust-badges">
          <div class="badge-item">
            <span class="badge-icon">🔒</span>
            <span class="badge-text">{securePaymentLabel}</span>
          </div>
          <div class="badge-item">
            <span class="badge-icon">⚡</span>
            <span class="badge-text">{t(lang, 'product.instant_download')}</span>
          </div>
          <div class="badge-item">
            {#if data.hasPurchased && data.isPremiumAccess}
              <span class="badge-icon">🌟</span>
              <span class="badge-text">{t(lang, 'product.premium_access')}</span>
            {:else}
              <span class="badge-icon">♾️</span>
              <span class="badge-text">{t(lang, 'product.lifetime_access')}</span>
            {/if}
          </div>
        </div>
      </div>
    </div>
  </div>

  {#if videoId}
    <div class="product-video-card-container" class:expanded={videoExpanded}>
      <div class="product-video-card">
        <div class="video-header">
          <span class="video-badge">
            <span class="pulse-dot"></span>
            {t(lang, 'product.demo_video')}
          </span>
          <h3>{t(lang, 'product.demo_video_subtitle')}</h3>
        </div>
        <div class="video-wrapper">
          {#if videoExpanded}
            <iframe
              src="https://www.youtube.com/embed/{videoId}?autoplay=1&mute=1&enablejsapi=1"
              title="Demonstração do Produto"
              frameborder="0"
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
              allowfullscreen
            ></iframe>
          {:else}
            <div class="video-thumbnail-placeholder">
              <img src="https://img.youtube.com/vi/{videoId}/maxresdefault.jpg" alt="Miniatura do vídeo" />
              <div class="play-button-placeholder">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                  <polygon points="5 3 19 12 5 21 5 3"/>
                </svg>
              </div>
            </div>
          {/if}
        </div>
      </div>
    </div>
  {/if}

  {#if data.product.description}
    <div class="product-description-section">
      <h2>{t(lang, 'product.description')}</h2>
      <div class="description-container">
        <div class="description-content" class:expanded={isDescExpanded}>
          {data.product.description}
        </div>
        {#if data.product.description.length > 300}
          <button 
            type="button" 
            class="toggle-desc-btn" 
            onclick={() => isDescExpanded = !isDescExpanded}
          >
            {isDescExpanded ? t(lang, "common.less") : t(lang, "common.more")}
          </button>
        {/if}
      </div>
    </div>
  {/if}

  <!-- Seção de Avaliações (Reviews) -->
  <div class="product-reviews-section">
    <div class="reviews-header">
      <h2>{t(lang, 'reviews.title')}</h2>
      {#if data.reviewSummary && data.reviewSummary.totalCount > 0}
        <span class="reviews-count-badge">{data.reviewSummary.totalCount} {data.reviewSummary.totalCount === 1 ? t(lang, 'reviews.count_badge_singular') : t(lang, 'reviews.count_badge_plural')}</span>
      {/if}
    </div>

    <div class="reviews-grid">
      <!-- Painel de Resumo de Notas -->
      <div class="reviews-summary-panel">
        <div class="rating-huge-box">
          <span class="rating-huge-val">{data.reviewSummary?.averageRating || "0.0"}</span>
          <div class="stars-gold-huge">
            {#each Array(5) as _, i}
              <svg width="24" height="24" viewBox="0 0 24 24" fill={i < Math.round(data.reviewSummary?.averageRating || 0) ? "#fbbf24" : "none"} stroke="#fbbf24" stroke-width="2">
                <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
              </svg>
            {/each}
          </div>
          <span class="rating-subtitle">{t(lang, 'reviews.general_average')}</span>
        </div>
      </div>

      <!-- Formulário para Deixar Avaliação (Se Elegível e Logado) -->
      <div class="reviews-form-panel">
        {#if !data.user}
          <div class="review-auth-prompt">
            <p>{t(lang, 'reviews.login_prompt')}</p>
            <a href="/members/login?redirectTo={encodeURIComponent($page.url.pathname)}" class="btn btn-secondary btn-sm">{t(lang, "product.login_review")}</a>
          </div>
        {:else if !data.hasPurchased}
          <div class="review-auth-prompt">
            <p>{t(lang, "product.only_buyers")}</p>
          </div>
        {:else if data.hasReviewed}
          <div class="review-success-panel">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#22c55e" stroke-width="2.5">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>
            </svg>
            <p>{t(lang, 'reviews.success_message')}</p>
          </div>
        {:else}
          <!-- Formulário Interativo com Estrelas Douradas -->
          <form method="POST" action="?/addReview" class="add-review-form" use:enhance={({ formData }) => {
            ratingErrorMessage = "";
            if (userRating === 0) {
              ratingErrorMessage = t(lang, "product.select_rating");
              return;
            }
            formData.set("rating", String(userRating));
            isSubmittingReview = true;
            return async ({ result, update }) => {
              isSubmittingReview = false;
              if (result.type === "success") {
                userRating = 0;
                reviewComment = "";
              }
              update();
            };
          }}>
            <h3 class="form-title">{t(lang, 'reviews.leave_review')}</h3>

            <div class="form-group-rating">
              <span class="rating-label">{t(lang, 'reviews.your_rating')}</span>
              <div class="stars-selector">
                {#each [1, 2, 3, 4, 5] as star}
                  <button
                    type="button"
                    class="star-btn"
                    onclick={() => userRating = star}
                    onmouseenter={() => hoveredRating = star}
                    onmouseleave={() => hoveredRating = 0}
                    title={t(lang, "product.star_titles", { n: star })}
                  >
                    <svg
                      width="32"
                      height="32"
                      viewBox="0 0 24 24"
                      fill={(hoveredRating >= star || (!hoveredRating && userRating >= star)) ? "#fbbf24" : "none"}
                      stroke="#fbbf24"
                      stroke-width="2"
                      class="interactive-star"
                    >
                      <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
                    </svg>
                  </button>
                {/each}
              </div>
              {#if ratingErrorMessage}
                <span class="error-msg-inline">{ratingErrorMessage}</span>
              {/if}
            </div>

            <div class="form-group">
              <label for="review-comment">{t(lang, "product.your_comment")}</label>
              <textarea
                id="review-comment"
                name="comment"
                rows="3"
                bind:value={reviewComment}
                placeholder={t(lang, 'reviews.comment_placeholder')}
              ></textarea>
            </div>

            {#if form?.message}
              <div class="alert {form.success ? 'success' : 'error'}">{form.message}</div>
            {/if}

            <button type="submit" class="btn btn-primary btn-submit-review" disabled={isSubmittingReview}>
              {isSubmittingReview ? t(lang, 'reviews.submitting') : t(lang, 'reviews.submit')}
            </button>
          </form>
        {/if}
      </div>
    </div>

    <!-- Lista de Comentários / Avaliações -->
    <div class="reviews-list-container">
      <h3>{t(lang, 'reviews.buyer_opinion')}</h3>

      {#if data.reviews && data.reviews.length > 0}
        <div class="reviews-list">
          {#each data.reviews as review}
            <div class="review-card">
              <div class="review-card-header">
                <div class="reviewer-info">
                  <div class="reviewer-avatar">
                    {(review.user_name || review.username).substring(0, 2).toUpperCase()}
                  </div>
                  <div class="reviewer-meta">
                    <span class="reviewer-name">{review.user_name || review.username}</span>
                    <span class="review-date">{formatDate(review.created_at)}</span>
                  </div>
                </div>
                <div class="stars-gold-compact">
                  {#each Array(5) as _, i}
                    <svg width="14" height="14" viewBox="0 0 24 24" fill={i < review.rating ? "#fbbf24" : "none"} stroke="#fbbf24" stroke-width="2">
                      <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
                    </svg>
                  {/each}
                </div>
              </div>
              {#if review.comment}
                <p class="review-comment-text">{review.comment}</p>
              {:else}
                <p class="review-comment-text no-text">
                  {t(lang, "product.star_titles", { n: review.rating })}
                </p>
              {/if}
            </div>
          {/each}
        </div>
      {:else}
        <div class="reviews-empty">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
          </svg>
          <p>{t(lang, 'reviews.no_reviews')}</p>
        </div>
      {/if}
    </div>
  </div>

  {#if data.relatedProducts && data.relatedProducts.length > 0}
    <div class="related-products-section">
      <h2>{t(lang, 'product.recommended')}</h2>
      <div class="related-products-grid">
        {#each data.relatedProducts as prod}
          <a href="/product/{prod.slug}" class="related-product-card">
            {#if prod.image_url}
              <img src={optimizeImageUrl(prod.image_url, 300, 300)} alt={prod.name} class="related-product-image" />
            {:else}
              <div class="related-product-placeholder" style="background: {getPlaceholderBackground(prod.id)}">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
                </svg>
              </div>
            {/if}
            <div class="related-product-info">
              {#if prod.category}
                <span class="related-product-category">{prod.category}</span>
              {/if}
              <h3 class="related-product-title">{prod.name}</h3>
              <span class="related-product-price">{formatPrice(prod.price_cents)}</span>
            </div>
          </a>
        {/each}
      </div>
    </div>
  {/if}
</div>

<style>
  .product-page-container {
    max-width: 900px;
    margin: 2rem auto;
    padding: 0 1rem;
  }

  .back-nav {
    margin-bottom: 1.5rem;
  }

  .btn-back {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    color: var(--text-muted);
    font-weight: 500;
    font-size: 0.95rem;
    text-decoration: none;
    transition: color var(--transition-fast), transform var(--transition-fast);
  }

  .btn-back:hover {
    color: var(--text-primary);
    transform: translateX(-4px);
  }

  .product-main-card {
    background: var(--bg-primary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-md);
    overflow: hidden;
    margin-bottom: 2rem;
  }

  .product-grid {
    display: grid;
    grid-template-columns: 1fr;
    gap: 2rem;
    padding: 2rem;
  }

  @media (min-width: 768px) {
    .product-grid {
      grid-template-columns: 1fr 1.1fr;
    }
  }

  /* Coluna da mídia */
  .product-media-column {
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--bg-secondary);
    border-radius: var(--radius-md);
    overflow: hidden;
    aspect-ratio: 1;
    border: 1px solid var(--border-light);
  }

  .product-main-image {
    width: 100%;
    height: 100%;
    object-fit: cover;
    transition: transform var(--transition-normal);
  }

  .product-main-image:hover {
    transform: scale(1.02);
  }

  .product-placeholder-gradient {
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: rgba(255, 255, 255, 0.95);
  }

  .placeholder-icon-wrapper {
    background: rgba(255, 255, 255, 0.15);
    padding: 1.5rem;
    border-radius: 50%;
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.25);
    box-shadow: var(--shadow-md);
  }

  /* Coluna de detalhes */
  .product-details-column {
    display: flex;
    flex-direction: column;
    justify-content: center;
  }

  .product-badge {
    align-self: flex-start;
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    background: var(--bg-tertiary);
    color: var(--text-secondary);
    font-size: 0.75rem;
    text-transform: uppercase;
    font-weight: 700;
    letter-spacing: 0.05em;
    padding: 0.35rem 0.75rem;
    border-radius: 100px;
    border: 1px solid var(--border-color);
    margin-bottom: 1rem;
  }

  .product-title {
    font-family: var(--font-sans);
    font-size: 1.75rem;
    font-weight: 800;
    line-height: 1.25;
    color: var(--text-primary);
    margin: 0 0 1rem 0;
  }

  .price-section {
    display: flex;
    align-items: baseline;
    gap: 0.5rem;
    margin-bottom: 1.5rem;
  }

  .price-label {
    color: var(--text-muted);
    font-size: 0.95rem;
    font-weight: 500;
  }

  .price-tag {
    font-family: var(--font-sans);
    font-size: 2rem;
    font-weight: 800;
    color: #22c55e;
  }

  .price-tag.free-price {
    color: #3b82f6;
  }

  /* Ações */
  .action-card {
    background: var(--bg-secondary);
    border: 1px solid var(--border-light);
    border-radius: var(--radius-md);
    padding: 1.25rem;
    margin-bottom: 1.5rem;
  }

  .payment-buttons-group {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
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

  .btn-cta {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    font-weight: 600;
    padding: 0.85rem 1.5rem;
    font-size: 1rem;
    box-shadow: var(--shadow-sm);
    transition: transform var(--transition-fast), box-shadow var(--transition-fast);
  }

  .btn-cta:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: var(--shadow-md);
  }

  .btn-disabled {
    background: var(--bg-tertiary);
    color: var(--text-muted);
    border: 1px solid var(--border-color);
    cursor: not-allowed;
    opacity: 0.7;
  }

  .login-hint {
    font-size: 0.8rem;
    color: var(--text-muted);
    text-align: center;
    margin: 0.75rem 0 0 0;
  }

  .success-purchase-badge {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    font-weight: 700;
    color: #22c55e;
    margin-bottom: 1rem;
    background: rgba(34, 197, 94, 0.08);
    border: 1px solid rgba(34, 197, 94, 0.18);
    padding: 0.5rem;
    border-radius: var(--radius-sm);
  }

  /* Entrega Manual — formulário de captura do identificador do comprador */
  .manual-access-form {
    display: flex;
    flex-direction: column;
    gap: 0.6rem;
    margin-bottom: 0.75rem;
  }

  .manual-label {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    font-weight: 600;
    font-size: 0.9rem;
    color: var(--text-primary);
  }

  .required-mark {
    color: #ef4444;
    font-weight: 700;
  }

  .manual-input {
    width: 100%;
    padding: 0.6rem 0.85rem;
    border: 1.5px solid var(--border-color);
    border-radius: var(--radius-sm);
    background: var(--bg-input, var(--bg-secondary));
    color: var(--text-primary);
    font-size: 0.95rem;
    transition: border-color 0.2s;
  }

  .manual-input:focus {
    outline: none;
    border-color: var(--color-primary, #6366f1);
    box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
  }

  .manual-hint {
    font-size: 0.78rem;
    color: var(--text-muted);
    margin: 0;
    line-height: 1.4;
  }

  /* Badge de entrega pendente (aguardando compartilhamento pelo admin) */
  .pending-delivery-badge {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    font-weight: 700;
    color: #f59e0b;
    margin-bottom: 0.75rem;
    background: rgba(245, 158, 11, 0.08);
    border: 1px solid rgba(245, 158, 11, 0.25);
    padding: 0.6rem;
    border-radius: var(--radius-sm);
  }

  .pending-delivery-msg {
    font-size: 0.88rem;
    color: var(--text-secondary);
    text-align: center;
    margin: 0 0 0.5rem;
    line-height: 1.5;
  }

  .delivery-instructions {
    font-size: 0.85rem;
    color: var(--text-muted);
    background: var(--bg-secondary);
    border-left: 3px solid #f59e0b;
    padding: 0.6rem 0.85rem;
    border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
    margin: 0.25rem 0 0;
    line-height: 1.5;
  }

  .delivery-instructions.delivered {
    border-left-color: #22c55e;
  }

  /* Trust Badges */
  .trust-badges {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 0.5rem;
    border-top: 1px solid var(--border-color);
    padding-top: 1.25rem;
  }

  .badge-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    gap: 0.25rem;
  }

  .badge-icon {
    font-size: 1.2rem;
  }

  .badge-text {
    font-size: 0.7rem;
    font-weight: 600;
    color: var(--text-muted);
  }

  /* Descrição */
  .product-description-section {
    background: var(--bg-primary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-sm);
    padding: 2rem;
  }

  .product-description-section h2 {
    font-family: var(--font-sans);
    font-size: 1.2rem;
    font-weight: 700;
    color: var(--text-primary);
    margin: 0 0 1rem 0;
  }

  .description-container {
    display: flex;
    flex-direction: column;
  }

  .description-content {
    font-size: 0.95rem;
    line-height: 1.6;
    color: var(--text-secondary);
    white-space: pre-wrap;
    display: -webkit-box;
    -webkit-line-clamp: 6;
    -webkit-box-orient: vertical;
    overflow: hidden;
    transition: all 0.3s ease;
  }

  .description-content.expanded {
    display: block;
    -webkit-line-clamp: unset;
    overflow: visible;
  }

  .toggle-desc-btn {
    background: transparent;
    border: none;
    color: var(--accent-color, #3b82f6);
    font-size: 0.9rem;
    font-weight: 600;
    cursor: pointer;
    padding: 0;
    margin-top: 1rem;
    align-self: flex-start;
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
  }

  .toggle-desc-btn:hover {
    text-decoration: underline;
  }

  /* Recomendados */
  .related-products-section {
    margin-top: 3rem;
  }

  .related-products-section h2 {
    font-size: 1.25rem;
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 1.5rem;
  }

  .related-products-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
    gap: 1.5rem;
  }

  .related-product-card {
    background: var(--bg-primary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-lg);
    overflow: hidden;
    text-decoration: none;
    display: flex;
    flex-direction: column;
    box-shadow: var(--shadow-sm);
    transition: transform 0.2s, box-shadow 0.2s;
  }

  .related-product-card:hover {
    transform: translateY(-4px);
    box-shadow: var(--shadow-md);
    border-color: var(--accent-color, #3b82f6);
  }

  .related-product-image {
    width: 100%;
    height: 180px;
    object-fit: cover;
  }

  .related-product-placeholder {
    width: 100%;
    height: 180px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: rgba(255, 255, 255, 0.9);
  }

  .related-product-info {
    padding: 1.25rem;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    flex-grow: 1;
  }

  .related-product-category {
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    color: var(--accent-color, #3b82f6);
    letter-spacing: 0.05em;
  }

  .related-product-title {
    font-size: 1rem;
    font-weight: 600;
    color: var(--text-primary);
    margin: 0;
    line-height: 1.4;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  .related-product-price {
    font-size: 0.95rem;
    font-weight: 700;
    color: var(--text-primary);
    margin-top: auto;
  }

  /* Estilos do Vídeo do YouTube com Animação Premium */
  .product-video-card-container {
    max-height: 0;
    opacity: 0;
    overflow: hidden;
    transform: scale(0.95);
    transition: max-height 0.8s cubic-bezier(0.16, 1, 0.3, 1), 
                opacity 0.8s cubic-bezier(0.16, 1, 0.3, 1), 
                transform 0.8s cubic-bezier(0.16, 1, 0.3, 1), 
                margin 0.8s cubic-bezier(0.16, 1, 0.3, 1);
    margin-bottom: 0;
  }

  .product-video-card-container.expanded {
    max-height: 800px;
    opacity: 1;
    transform: scale(1);
    margin-bottom: 2rem;
  }

  .product-video-card {
    background: var(--bg-primary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-md);
    padding: 1.5rem;
    display: flex;
    flex-direction: column;
    gap: 1.25rem;
  }

  .video-header {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .video-badge {
    align-self: flex-start;
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    background: rgba(239, 68, 68, 0.1);
    color: #ef4444;
    padding: 0.25rem 0.75rem;
    border-radius: var(--radius-full);
    font-size: 0.8rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .pulse-dot {
    width: 8px;
    height: 8px;
    background-color: #ef4444;
    border-radius: 50%;
    display: inline-block;
    box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7);
    animation: pulse 1.5s infinite;
  }

  @keyframes pulse {
    0% {
      transform: scale(0.95);
      box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7);
    }
    70% {
      transform: scale(1);
      box-shadow: 0 0 0 8px rgba(239, 68, 68, 0);
    }
    100% {
      transform: scale(0.95);
      box-shadow: 0 0 0 0 rgba(239, 68, 68, 0);
    }
  }

  .video-header h3 {
    margin: 0;
    font-size: 1.15rem;
    font-weight: 700;
    color: var(--text-primary);
  }

  .video-wrapper {
    position: relative;
    width: 100%;
    padding-bottom: 56.25%; /* Aspect ratio 16:9 */
    height: 0;
    border-radius: var(--radius-md);
    overflow: hidden;
    border: 1px solid var(--border-light);
    background: #000;
  }

  .video-wrapper iframe {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
  }

  .video-thumbnail-placeholder {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
  }

  .video-thumbnail-placeholder img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    opacity: 0.6;
  }

  .play-button-placeholder {
    position: absolute;
    width: 68px;
    height: 68px;
    background: rgba(239, 68, 68, 0.9);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #fff;
    box-shadow: 0 4px 20px rgba(239, 68, 68, 0.4);
    transition: transform 0.3s ease, background 0.3s ease;
  }

  .play-button-placeholder svg {
    margin-left: 3px;
  }

  /* --- AVALIAÇÕES COM ESTRELAS (CSS) --- */
  
  /* Topo do Produto (Média Compacta) */
  .product-rating-summary-compact {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin: 0.5rem 0 1rem;
    font-size: 0.85rem;
  }
  .stars-gold-compact {
    display: inline-flex;
    align-items: center;
    gap: 2px;
  }
  .rating-value {
    font-weight: 700;
    color: var(--text-primary);
  }
  .rating-count {
    color: var(--text-muted);
  }
  .no-ratings-yet {
    color: var(--text-muted);
    font-weight: 500;
  }

  /* Seção Principal */
  .product-reviews-section {
    margin-top: 3.5rem;
    border-top: 1px solid var(--border-color);
    padding-top: 2.5rem;
  }

  .reviews-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 2rem;
  }

  .reviews-header h2 {
    font-size: 1.4rem;
    font-weight: 700;
    color: var(--text-primary);
    margin: 0;
  }

  .reviews-count-badge {
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    color: var(--text-secondary);
    padding: 0.35rem 0.75rem;
    font-size: 0.8rem;
    font-weight: 600;
    border-radius: var(--radius-full);
  }

  /* Grid Principal (Resumo à esquerda, Form à direita) */
  .reviews-grid {
    display: grid;
    grid-template-columns: 1fr;
    gap: 2rem;
    margin-bottom: 3rem;
  }

  @media (min-width: 768px) {
    .reviews-grid {
      grid-template-columns: 240px 1fr;
    }
  }

  /* Painel de Resumo (Nota Grande) */
  .reviews-summary-panel {
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-lg);
    padding: 2rem 1.5rem;
    display: flex;
    align-items: center;
    justify-content: center;
    text-align: center;
  }

  .rating-huge-box {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.5rem;
  }

  .rating-huge-val {
    font-size: 3.5rem;
    font-weight: 800;
    line-height: 1;
    color: var(--text-primary);
    letter-spacing: -0.02em;
  }

  .stars-gold-huge {
    display: flex;
    gap: 4px;
    color: #fbbf24;
  }

  .rating-subtitle {
    font-size: 0.8rem;
    color: var(--text-muted);
    font-weight: 500;
    margin-top: 0.25rem;
  }

  /* Painel de Formulário */
  .reviews-form-panel {
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-lg);
    padding: 2rem;
  }

  .review-auth-prompt {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    height: 100%;
    gap: 1rem;
    color: var(--text-secondary);
  }

  .review-auth-prompt p {
    font-size: 0.95rem;
    margin: 0;
  }

  .review-success-panel {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    gap: 0.75rem;
    color: var(--text-secondary);
    padding: 1rem 0;
  }

  .review-success-panel p {
    font-size: 0.95rem;
    font-weight: 500;
    margin: 0;
  }

  .add-review-form {
    display: flex;
    flex-direction: column;
    gap: 1.25rem;
  }

  .add-review-form .form-title {
    font-size: 1.15rem;
    font-weight: 700;
    margin: 0;
    color: var(--text-primary);
  }

  /* Seleção de Estrelas (Interativa) */
  .form-group-rating {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .rating-label {
    font-size: 0.9rem;
    font-weight: 600;
    color: var(--text-primary);
  }

  .stars-selector {
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .star-btn {
    background: none;
    border: none;
    cursor: pointer;
    padding: 4px;
    margin: 0;
    transition: transform 0.1s ease;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  /* Grupo de formulário e Textarea Premium */
  .add-review-form .form-group {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    width: 100%;
  }

  .add-review-form .form-group label {
    font-size: 0.9rem;
    font-weight: 600;
    color: var(--text-primary);
  }

  .add-review-form textarea {
    width: 100%;
    min-height: 100px;
    padding: 0.75rem 1rem;
    border: 1.5px solid var(--border-color);
    border-radius: var(--radius-md, 8px);
    background: var(--bg-primary, #1e1e1e);
    color: var(--text-primary);
    font-size: 0.95rem;
    font-family: inherit;
    line-height: 1.5;
    resize: vertical;
    outline: none;
    box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.05);
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
  }

  .add-review-form textarea:focus {
    border-color: var(--color-primary, #6366f1);
    box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15), inset 0 1px 2px rgba(0, 0, 0, 0.05);
  }

  .add-review-form textarea::placeholder {
    color: var(--text-muted);
    opacity: 0.75;
  }

  .star-btn:hover {
    transform: scale(1.15);
  }

  .interactive-star {
    transition: fill 0.15s ease, transform 0.15s ease;
  }

  .error-msg-inline {
    font-size: 0.8rem;
    color: #ef4444;
    font-weight: 500;
  }

  .btn-submit-review {
    align-self: flex-start;
    padding: 0.6rem 1.5rem;
    font-size: 0.9rem;
    font-weight: 600;
  }

  /* Lista de Comentários */
  .reviews-list-container {
    margin-top: 3rem;
  }

  .reviews-list-container h3 {
    font-size: 1.15rem;
    font-weight: 700;
    color: var(--text-primary);
    margin: 0 0 1.5rem;
  }

  .reviews-list {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .review-card {
    background: var(--bg-primary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-lg);
    padding: 1.5rem;
    display: flex;
    flex-direction: column;
    gap: 0.85rem;
    box-shadow: var(--shadow-sm);
  }

  .review-card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
  }

  .reviewer-info {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }

  .reviewer-avatar {
    width: 38px;
    height: 38px;
    background: linear-gradient(135deg, var(--color-primary, #6366f1), #4f46e5);
    color: #ffffff;
    font-weight: 700;
    font-size: 0.85rem;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    letter-spacing: 0.05em;
  }

  .reviewer-meta {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .reviewer-name {
    font-size: 0.92rem;
    font-weight: 600;
    color: var(--text-primary);
  }

  .review-date {
    font-size: 0.78rem;
    color: var(--text-muted);
  }

  .review-comment-text {
    font-size: 0.95rem;
    color: var(--text-secondary);
    line-height: 1.5;
    margin: 0;
  }

  .review-comment-text.no-text {
    color: var(--text-muted);
    font-style: italic;
  }

  .reviews-empty {
    background: var(--bg-secondary);
    border: 1px dashed var(--border-color);
    border-radius: var(--radius-lg);
    padding: 3rem 1.5rem;
    text-align: center;
    color: var(--text-muted);
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.75rem;
  }

  .reviews-empty p {
    font-size: 0.9rem;
    margin: 0;
  }

  .premium-badge-banner {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    background: linear-gradient(135deg, #1e1b4b 0%, #312e81 100%);
    border: 1px solid #4338ca;
    border-radius: 12px;
    padding: 1.25rem;
    margin-bottom: 1.5rem;
    color: #e0e7ff;
    position: relative;
    overflow: hidden;
  }
  .premium-badge-banner::before {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle, rgba(99, 102, 241, 0.15) 0%, transparent 70%);
    pointer-events: none;
  }
  .premium-badge-banner .sparkle-icon {
    font-size: 1.5rem;
  }
  .premium-badge-banner h4 {
    margin: 0;
    font-size: 1rem;
    font-weight: 700;
    color: #fff;
    letter-spacing: 0.025em;
  }
  .premium-badge-banner p {
    margin: 0.25rem 0 0 0;
    font-size: 0.8rem;
    line-height: 1.4;
    color: #c7d2fe;
  }
  .btn-premium-link {
    display: inline-block;
    text-align: center;
    background: #4f46e5;
    color: #fff !important;
    text-decoration: none !important;
    padding: 0.6rem 1rem;
    border-radius: 8px;
    font-size: 0.85rem;
    font-weight: 600;
    transition: all 0.2s ease;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  }
  .btn-premium-link:hover {
    background: #6366f1;
    transform: translateY(-1px);
    box-shadow: 0 10px 15px -3px rgba(79, 70, 229, 0.3);
  }

  /* Estado de Download Carregando (UX Premium) */
  @keyframes spin {
    to { transform: rotate(360deg); }
  }
  .animate-spin {
    animation: spin 1s linear infinite;
    flex-shrink: 0;
  }
  .btn-cta.btn-disabled {
    background: #374151 !important;
    color: #9ca3af !important;
    border-color: #374151 !important;
    cursor: not-allowed;
    opacity: 0.85;
    pointer-events: none;
  }
</style>
