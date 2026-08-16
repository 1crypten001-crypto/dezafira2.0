<script lang="ts">
  import { optimizeImageUrl } from "$lib/image-optimizer";
  import { goto } from "$app/navigation";
  import { page } from "$app/stores";
  import type { PageData } from "./$types";
  import AdRenderer from "$lib/components/AdRenderer.svelte";
  import NewsletterSignup from "$lib/components/NewsletterSignup.svelte";
  import { ageState, confirmAgeGlobal } from "$lib/stores/age.svelte";
  import Search from "$lib/components/Search.svelte";
  import Pagination from "$lib/components/Pagination.svelte";
  import Skeleton from "$lib/components/Skeleton.svelte";
  import Alert from "$lib/components/Alert.svelte";
  import { t, formatDate as fmtDate, formatMoney } from "$lib/i18n";

  let { data }: { data: PageData } = $props();
  const lang = $derived(data.language || $page.data.language || 'pt');
  const displayCurrency = $derived(($page.data.displayCurrency as string) || (data as any).displayCurrency || 'BRL');

  let searchInput = $state(data.searchQuery || '');

  let currentProductIndex = $state(0);
  function nextProduct(total: number) {
    if (total === 0) return;
    currentProductIndex = (currentProductIndex + 1) % total;
  }
  function prevProduct(total: number) {
    if (total === 0) return;
    currentProductIndex = (currentProductIndex - 1 + total) % total;
  }

  $effect(() => {
    if (data.searchQuery) {
      searchInput = data.searchQuery;
    }
  });
  let feedLoadingMode = $derived(
    data.settings?.feed_loading_mode === "infinite" ? "infinite" : "pagination"
  );

  // Initialize synchronously from SSR data to prevent CLS.
  // The $effect below handles navigation/reactive updates.
  function getInitialPosts() {
    return data.currentPage === 1 && !data.searchQuery
      ? data.posts.slice(1)
      : data.posts;
  }

  let displayedPosts = $state<any[]>(getInitialPosts());
  let infinitePage = $state(data.currentPage ?? 1);
  let infiniteTotalPages = $state(data.totalPages ?? 1);
  let loadingMore = $state(false);
  let loadError = $state<string | null>(null);

  function formatDate(dateString: string) {
    return fmtDate(lang, dateString, {
      day: "numeric",
      month: "short",
      year: "numeric",
    }).replace(".", "");
  }

  function handleSearch(query: string) {
    goto(`/?q=${encodeURIComponent(query)}`);
  }

  function getPostImage(post: any) {
    if (post.cover_image) return post.cover_image;
    const match = post.content?.match(/<img[^>]+src="([^">]+)"/);
    if (match) return match[1];
    return `https://picsum.photos/seed/${post.id}/800/600`;
  }

  function hasNoImage(post: any) {
    if (post.cover_image && post.cover_image.trim().length > 0) return false;
    if (post.content && post.content.includes('<img')) {
      const match = post.content.match(/<img[^>]+src="([^">]+)"/);
      if (match && match[1]) return false;
    }
    return true;
  }

  function getPlaceholderBackground(post: any) {
    const gradients = [
      'linear-gradient(135deg, #e0f2fe 0%, #bae6fd 100%)', // Blue
      'linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%)', // Emerald
      'linear-gradient(135deg, #fef9c3 0%, #fef08a 100%)', // Yellow
      'linear-gradient(135deg, #fce7f3 0%, #fbcfe8 100%)', // Pink
      'linear-gradient(135deg, #f3e8ff 0%, #e9d5ff 100%)', // Purple
      'linear-gradient(135deg, #ffedd5 0%, #fed7aa 100%)', // Orange
      'linear-gradient(135deg, #ccfbf1 0%, #99f6e4 100%)', // Teal
      'linear-gradient(135deg, #ffe4e6 0%, #fecdd3 100%)', // Rose
      'linear-gradient(135deg, #e0e7ff 0%, #c7d2fe 100%)', // Indigo
      'linear-gradient(135deg, #fef3c7 0%, #fde68a 100%)'  // Amber
    ];
    const idStr = String(post.id || post.slug || '0');
    let hash = 0;
    for (let i = 0; i < idStr.length; i++) {
      hash = idStr.charCodeAt(i) + ((hash << 5) - hash);
    }
    const index = Math.abs(hash) % gradients.length;
    return gradients[index];
  }

  $effect(() => {
    // Runs on client after navigation to sync state with new page data
    infinitePage = data.currentPage;
    infiniteTotalPages = data.totalPages;
    loadError = null;
    searchInput = data.searchQuery || '';

    displayedPosts =
      data.currentPage === 1 && !data.searchQuery ? data.posts.slice(1) : data.posts;
  });

  async function loadMore() {
    if (feedLoadingMode !== "infinite") return;
    if (loadingMore) return;
    if (infinitePage >= infiniteTotalPages) return;

    loadingMore = true;
    loadError = null;
    const nextPage = infinitePage + 1;

    try {
      const params = new URLSearchParams();
      params.set("page", String(nextPage));
      if (data.searchQuery) params.set("q", data.searchQuery);

      const res = await fetch(`/api/posts?${params.toString()}`);
      if (!res.ok) throw new Error(String(res.status));

      const payload = await res.json();
      const newPosts = Array.isArray(payload?.posts) ? payload.posts : [];

      // Hard dedupe by id (safety net if ranking ever drifts between SSR and API)
      const seen = new Set(displayedPosts.map((p) => p.id));
      const uniqueNew = newPosts.filter((p: any) => p?.id != null && !seen.has(p.id));
      displayedPosts = [...displayedPosts, ...uniqueNew];
      infinitePage = typeof payload?.currentPage === "number" ? payload.currentPage : nextPage;
      infiniteTotalPages =
        typeof payload?.totalPages === "number" ? payload.totalPages : infiniteTotalPages;
    } catch {
      loadError = "Erro ao carregar mais posts";
    } finally {
      loadingMore = false;
    }
  }

  function infiniteScroll(node: HTMLElement) {
    if (feedLoadingMode !== "infinite") return;

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((e) => e.isIntersecting)) loadMore();
      },
      { rootMargin: "800px 0px" }
    );

    observer.observe(node);

    return {
      destroy() {
        observer.disconnect();
      },
    };
  }
</script>

<svelte:head>
  <title>{data.settings?.site_title || "Blog"} | Home</title>
  <meta name="description" content={data.settings?.site_description || "Blog oficial"} />
</svelte:head>

<div class="page-wrapper container">
  {#if data.currentPage === 1 && !data.searchQuery && data.posts.length > 0}
    {@const heroPost = data.posts[0]}
    <section class="hero-section">
      <a href="/post/{heroPost.slug}" class="hero-link">
        <div class="hero-image-wrapper">
          {#if hasNoImage(heroPost)}
            <div class="no-image-placeholder" style="background: {getPlaceholderBackground(heroPost)}">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="placeholder-icon">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                <polyline points="14 2 14 8 20 8"></polyline>
                <line x1="16" y1="13" x2="8" y2="13"></line>
                <line x1="16" y1="17" x2="8" y2="17"></line>
                <polyline points="10 9 9 9 8 9"></polyline>
              </svg>
              <div class="no-image-placeholder-title">
                {heroPost.title}
              </div>
            </div>
          {:else}
            <img
              src={optimizeImageUrl(getPostImage(heroPost), 1200)}
              alt={heroPost.title}
              class="hero-image"
              class:blurred={heroPost.is_18_plus && !ageState.confirmed}
              loading="eager"
              fetchpriority="high"
              width="1200"
              height="630"
            />
          {/if}
          <button 
            class="pinterest-save-btn" 
            onclick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              window.open(`https://pinterest.com/pin/create/button/?url=${encodeURIComponent($page.url.origin + '/post/' + heroPost.slug)}&media=${encodeURIComponent(getPostImage(heroPost))}&description=${encodeURIComponent(heroPost.title)}`, '_blank', 'width=600,height=400');
            }}
            aria-label={t(lang, 'home.save_pinterest')}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M12.017 0C5.396 0 .029 5.367.029 11.987c0 5.079 3.158 9.417 7.618 11.162-.105-.949-.199-2.403.041-3.439.219-.937 1.406-5.957 1.406-5.957s-.359-.72-.359-1.781c0-1.663.967-2.911 2.168-2.911 1.024 0 1.518.769 1.518 1.688 0 1.029-.653 2.567-.992 3.992-.285 1.193.6 2.165 1.775 2.165 2.128 0 3.768-2.245 3.768-5.487 0-2.861-2.063-4.869-5.008-4.869-3.41 0-5.409 2.562-5.409 5.199 0 1.033.394 2.143.889 2.741.099.12.112.225.085.345-.09.375-.293 1.199-.334 1.363-.053.225-.172.271-.401.165-1.495-.69-2.433-2.878-2.433-4.646 0-3.776 2.748-7.252 7.92-7.252 4.158 0 7.392 2.967 7.392 6.923 0 4.135-2.607 7.462-6.233 7.462-1.214 0-2.354-.629-2.758-1.379l-.749 2.848c-.269 1.045-1.004 2.352-1.498 3.146 1.123.345 2.306.535 3.55.535 6.607 0 11.985-5.365 11.985-11.987C23.97 5.366 18.605 0 12.017 0z"/></svg>
            {t(lang, 'home.save')}
          </button>
          <div class="hero-overlay">
            <span class="hero-category">
              {heroPost.categories ? heroPost.categories.split(",")[0] : t(lang, 'common.featured')}
            </span>
          </div>
        </div>
        <div class="hero-text">
          <h1 class="hero-title">{heroPost.title}</h1>
          {#if heroPost.excerpt}
            <p class="hero-excerpt">{heroPost.excerpt}</p>
          {/if}
          <div class="hero-footer">
             <span class="hero-date">{formatDate(heroPost.created_at)}</span>
             <span class="read-more">{t(lang, 'home.read_article')}</span>
          </div>
        </div>
      </a>
    </section>
  {/if}

  {#if data.homeMiddleAds && data.homeMiddleAds.length > 0}
    <div class="home-ad-wrapper">
      <AdRenderer ads={data.homeMiddleAds} placement="home_middle" />
    </div>
  {/if}

  <div class="main-layout">
    <main class="content-area">
      {#if data.searchQuery}
        <div class="section-header">
          <h2 class="section-title">{t(lang, 'home.results_for', { q: data.searchQuery })}</h2>
        </div>
      {/if}

      {#if data.posts.length === 0}
        <div class="empty-card">
          <div class="empty-content">
            <div class="empty-illustration">
              <svg width="80" height="80" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1">
                <circle cx="11" cy="11" r="8" />
                <path d="M21 21l-4.35-4.35" />
                <path d="M11 8v6M8 11h6" opacity="0.5" />
              </svg>
            </div>
            <h3>{t(lang, 'home.empty_title')}</h3>
            <p>{data.searchQuery ? t(lang, 'home.empty_search') : t(lang, 'home.empty_default')}</p>
            <a href="/" class="btn btn-outline">{t(lang, 'common.clear_search')}</a>
          </div>
        </div>
      {:else}
        <div class="organic-feed">
          {#each displayedPosts as post, i}
            <article class="feed-item">
              <a href="/post/{post.slug}" class="feed-card">
                <div class="feed-image-wrapper">
                  {#if hasNoImage(post)}
                    <div class="no-image-placeholder" style="background: {getPlaceholderBackground(post)}">
                      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="placeholder-icon">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                        <polyline points="14 2 14 8 20 8"></polyline>
                        <line x1="16" y1="13" x2="8" y2="13"></line>
                        <line x1="16" y1="17" x2="8" y2="17"></line>
                        <polyline points="10 9 9 9 8 9"></polyline>
                      </svg>
                      <div class="no-image-placeholder-title">
                        {post.title}
                      </div>
                    </div>
                  {:else}
                    <img
                      src={optimizeImageUrl(getPostImage(post), 800)}
                      alt={post.title}
                      class="feed-image"
                      class:blurred={post.is_18_plus && !ageState.confirmed}
                      loading="lazy"
                      width="800"
                      height="450"
                    />
                  {/if}
                  <button 
                    class="pinterest-save-btn" 
                    onclick={(e) => {
                      e.preventDefault();
                      e.stopPropagation();
                      window.open(`https://pinterest.com/pin/create/button/?url=${encodeURIComponent($page.url.origin + '/post/' + post.slug)}&media=${encodeURIComponent(getPostImage(post))}&description=${encodeURIComponent(post.title)}`, '_blank', 'width=600,height=400');
                    }}
                    aria-label={t(lang, 'home.save_pinterest')}
                  >
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M12.017 0C5.396 0 .029 5.367.029 11.987c0 5.079 3.158 9.417 7.618 11.162-.105-.949-.199-2.403.041-3.439.219-.937 1.406-5.957 1.406-5.957s-.359-.72-.359-1.781c0-1.663.967-2.911 2.168-2.911 1.024 0 1.518.769 1.518 1.688 0 1.029-.653 2.567-.992 3.992-.285 1.193.6 2.165 1.775 2.165 2.128 0 3.768-2.245 3.768-5.487 0-2.861-2.063-4.869-5.008-4.869-3.41 0-5.409 2.562-5.409 5.199 0 1.033.394 2.143.889 2.741.099.12.112.225.085.345-.09.375-.293 1.199-.334 1.363-.053.225-.172.271-.401.165-1.495-.69-2.433-2.878-2.433-4.646 0-3.776 2.748-7.252 7.92-7.252 4.158 0 7.392 2.967 7.392 6.923 0 4.135-2.607 7.462-6.233 7.462-1.214 0-2.354-.629-2.758-1.379l-.749 2.848c-.269 1.045-1.004 2.352-1.498 3.146 1.123.345 2.306.535 3.55.535 6.607 0 11.985-5.365 11.985-11.987C23.97 5.366 18.605 0 12.017 0z"/></svg>
                    {t(lang, 'home.save')}
                  </button>
                  <div class="feed-chips">
                    <span class="feed-chip">
                      {post.categories ? post.categories.split(",")[0] : t(lang, 'common.post')}
                    </span>
                    {#if post.is_18_plus}
                      <span class="feed-chip age-restricted">18+</span>
                    {/if}
                  </div>
                <div class="feed-info">
                  {#if post.recommendationReason}
                    <div class="recommendation-badge-wrapper">
                      <span class="recommendation-badge">{post.recommendationReason}</span>
                    </div>
                  {/if}
                  <h2 class="feed-title">{post.title}</h2>
                  <div class="feed-meta">
                    <span class="feed-date">{formatDate(post.created_at)}</span>
                  </div>
                </div>

              </a>
            </article>
          {/each}
        </div>
        
        <!-- Pagination logic remains the same -->
        {#if feedLoadingMode === 'infinite'}
          <div class="infinite-footer">
            <div class="infinite-sentinel" use:infiniteScroll></div>
            {#if loadError}
              <div class="infinite-error">
                <span>{loadError}</span>
                <button type="button" class="btn btn-small" onclick={loadMore}>{t(lang, 'common.try_again')}</button>
              </div>
            {:else if loadingMore}
              <div class="infinite-loading">
                <div class="loading-spinner"></div>
                <span>{t(lang, 'home.loading_more')}</span>
              </div>
            {:else if infinitePage >= infiniteTotalPages && displayedPosts.length > 0}
              <div class="infinite-done">{t(lang, 'home.end_of_page')}</div>
            {/if}
          </div>
        {/if}

        {#if feedLoadingMode === 'pagination'}
          <Pagination
            currentPage={data.currentPage}
            totalPages={data.totalPages}
            baseUrl="/"
          />
        {/if}
      {/if}
    </main>

    <aside class="sidebar">
      <div class="widget search-widget">
        <Search 
          value={searchInput}
          onSearch={handleSearch}
          placeholder={t(lang, 'home.search_placeholder')}
        />
      </div>

      <div class="widget categories-widget">
        <h2 class="widget-title">{t(lang, 'common.categories')}</h2>
        <ul class="categories-list">
          <li>
            <a href="/" class="category-link active">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7" /><rect x="14" y="3" width="7" height="7" /><rect x="3" y="14" width="7" height="7" /><rect x="14" y="14" width="7" height="7" /></svg>
              {t(lang, 'common.all')}
            </a>
          </li>
          {#each data.categories as cat}
            <li>
              <a href="/category/{cat.slug}" class="category-link">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z" /></svg>
                {cat.name}
              </a>
            </li>
          {/each}
        </ul>
      </div>

      {#if data.products && data.products.length > 0}
        {@const displayMode = data.settings?.sidebar_products_display_mode || 'carousel'}
        <div class="widget products-widget">
          <h2 class="widget-title">{t(lang, 'home.digital_products')}</h2>
          
          {#if displayMode === 'carousel'}
            <!-- Carousel Mode -->
            <div class="products-carousel">
              <div class="carousel-inner">
                {#each data.products as product, idx}
                  <div class="carousel-slide" class:active={currentProductIndex === idx}>
                    <div class="product-sidebar-card">
                      {#if product.image_url}
                        <div class="product-sidebar-image-wrapper">
                          <img src={product.image_url} alt={product.name} class="product-sidebar-image" />
                        </div>
                      {:else}
                        <div class="product-sidebar-icon">
                          {#if product.file_url}
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>
                            </svg>
                          {:else}
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                              <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/>
                            </svg>
                          {/if}
                        </div>
                      {/if}
                      <h3 class="product-sidebar-name">{product.name}</h3>
                      {#if product.description}
                        <p class="product-sidebar-desc">{product.description}</p>
                      {/if}
                      <div class="product-sidebar-footer">
                        <span class="product-sidebar-price">
                          {product.price_cents === 0 ? t(lang, 'common.free') : formatMoney(lang, product.price_cents, displayCurrency)}
                        </span>
                        {#if product.price_cents > 0 && !product.hasPurchased}
                          {#if data.settings?.enable_member_login !== '1'}
                            <button class="product-sidebar-btn btn btn-small btn-secondary" disabled style="opacity: 0.6; cursor: not-allowed;">{t(lang, 'common.unavailable')}</button>
                          {:else if !data.user}
                            <a href="/members/login?redirectTo={encodeURIComponent($page.url.pathname)}" class="product-sidebar-btn btn btn-small btn-primary">{t(lang, 'common.buy')}</a>
                          {:else if $page.data.paymentGateway === 'stripe'}
                            <a href="/purchase/{product.id}" class="product-sidebar-btn btn btn-small btn-primary" data-sveltekit-reload target="_blank" rel="noopener noreferrer">{t(lang, 'common.buy')}</a>
                          {:else}
                            <div class="product-sidebar-btn-group">
                              <a href="/purchase/{product.id}?method=pix" class="product-sidebar-btn btn btn-small btn-primary btn-pix-small" data-sveltekit-reload target="_blank" rel="noopener noreferrer">{t(lang, 'common.pix')}</a>
                              <a href="/purchase/{product.id}?method=credit_card" class="product-sidebar-btn btn btn-small btn-secondary btn-card-small" data-sveltekit-reload target="_blank" rel="noopener noreferrer">{t(lang, 'common.card')}</a>
                            </div>
                          {/if}
                        {:else}
                          {#if product.file_url}
                            <a href="/api/download/{product.id}" rel="external" class="product-sidebar-btn btn btn-small btn-primary">{t(lang, 'common.download')}</a>
                          {:else if product.external_link}
                            <a href={product.external_link} target="_blank" class="product-sidebar-btn btn btn-small btn-secondary">{t(lang, 'common.access')}</a>
                          {/if}
                        {/if}
                      </div>
                    </div>
                  </div>
                {/each}
              </div>
              
              {#if data.products.length > 1}
                <div class="carousel-nav">
                  <button type="button" class="carousel-nav-btn prev" onclick={() => prevProduct(data.products.length)} aria-label={t(lang, 'common.previous')}>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M15 18l-6-6 6-6"/>
                    </svg>
                  </button>
                  <span class="carousel-indicator">{currentProductIndex + 1} / {data.products.length}</span>
                  <button type="button" class="carousel-nav-btn next" onclick={() => nextProduct(data.products.length)} aria-label={t(lang, 'common.next')}>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M9 18l6-6-6-6"/>
                    </svg>
                  </button>
                </div>
              {/if}
            </div>
          {:else}
            <!-- List Mode -->
            <div class="products-sidebar-list">
              {#each data.products.slice(0, 5) as product}
                <div class="product-sidebar-list-item">
                  {#if product.image_url}
                    <img src={product.image_url} alt={product.name} class="product-list-item-thumb" />
                  {:else}
                    <div class="product-list-item-icon">
                      {#if product.file_url}
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>
                        </svg>
                      {:else}
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                          <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/>
                        </svg>
                      {/if}
                    </div>
                  {/if}
                  <div class="product-list-item-info">
                    <span class="product-list-item-name" title={product.name}>{product.name}</span>
                    <div class="product-list-item-footer">
                      <span class="product-list-item-price">
                        {product.price_cents === 0 ? t(lang, 'common.free') : formatMoney(lang, product.price_cents, displayCurrency)}
                      </span>
                      {#if product.price_cents > 0 && !product.hasPurchased}
                        {#if data.settings?.enable_member_login !== '1'}
                          <span class="product-list-item-link" style="opacity: 0.5; cursor: not-allowed; text-decoration: none;">{t(lang, 'common.unavailable')}</span>
                        {:else if !data.user}
                          <a href="/members/login?redirectTo={encodeURIComponent($page.url.pathname)}" class="product-list-item-link">{t(lang, 'common.buy')}</a>
                        {:else if $page.data.paymentGateway === 'stripe'}
                          <a href="/purchase/{product.id}" class="product-list-item-link" data-sveltekit-reload target="_blank" rel="noopener noreferrer">{t(lang, 'common.buy')}</a>
                        {:else}
                          <span class="product-list-item-btn-group">
                            <a href="/purchase/{product.id}?method=pix" class="product-list-item-link text-pix" data-sveltekit-reload target="_blank" rel="noopener noreferrer">{t(lang, 'common.pix')}</a>
                            <span class="product-list-item-divider">/</span>
                            <a href="/purchase/{product.id}?method=credit_card" class="product-list-item-link" data-sveltekit-reload target="_blank" rel="noopener noreferrer">{t(lang, 'common.card')}</a>
                          </span>
                        {/if}
                      {:else}
                        {#if product.file_url}
                          <a href="/api/download/{product.id}" rel="external" class="product-list-item-link">{t(lang, 'common.download')}</a>
                        {:else if product.external_link}
                          <a href={product.external_link} target="_blank" class="product-list-item-link">{t(lang, 'common.access')}</a>
                        {/if}
                      {/if}
                    </div>
                  </div>
                </div>
              {/each}
            </div>
          {/if}
        </div>
      {/if}

      <div class="widget newsletter-widget">
        <NewsletterSignup />
      </div>

      {#if data.sidebarAds && data.sidebarAds.length > 0}
        <div class="widget ad-widget">
          <AdRenderer ads={data.sidebarAds} placement="sidebar" />
        </div>
      {/if}
    </aside>
  </div>
</div>

<style>
  .page-wrapper {
    width: 100%;
    margin: 0 auto;
    padding: 0;
  }

  /* Infinite Scroll UI */
  .infinite-footer {
    min-height: 120px;
    padding: 0;
    text-align: center;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
  }

  .infinite-sentinel {
    height: 1px;
    width: 100%;
  }

  .infinite-loading {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.75rem;
    font-size: 0.9rem;
    color: var(--text-muted);
    font-weight: 500;
  }

  .loading-spinner {
    width: 28px;
    height: 28px;
    border: 3px solid var(--border-light);
    border-top-color: var(--accent-primary, #6366f1);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }

  .infinite-done {
    font-size: 0.9rem;
    color: var(--text-muted);
    font-weight: 500;
    padding: 0.75rem 1.5rem;
    border-radius: 50px;
    background: var(--bg-secondary);
    border: 1px solid var(--border-light);
    display: inline-block;
  }

  .infinite-error {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1rem;
    color: #ef4444;
  }



  /* Hero Section Polish */
  .hero-section {
    margin-top: 4px;
    margin-bottom: 2rem;
    max-width: 100%;
    animation: fadeIn 1s ease-out;
  }

  .home-ad-wrapper {
    margin-bottom: 2rem;
    width: 100%;
  }

  .hero-link {
    display: grid;
    grid-template-columns: 1.2fr 0.8fr;
    gap: 3rem;
    text-decoration: none;
    color: inherit;
    align-items: center;
    background: var(--bg-primary);
    padding: 1.5rem;
    border-radius: 24px;
    border: 1px solid var(--border-light);
    box-shadow: var(--shadow-md);
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  }

  .hero-link:hover {
    box-shadow: var(--shadow-xl);
    transform: translateY(-4px);
    border-color: var(--text-primary);
  }

  .hero-image-wrapper {
    position: relative;
    border-radius: 18px;
    overflow: hidden;
    aspect-ratio: 16/9;
  }

  .hero-image {
    width: 100%;
    height: 100%;
    object-fit: cover;
    object-position: top;
    transition: transform 0.8s cubic-bezier(0.165, 0.84, 0.44, 1), filter 0.8s ease;
  }

  .hero-image.blurred {
    filter: blur(40px) grayscale(0.2);
    transform: scale(1.1);
  }

  .hero-link:hover .hero-image {
    transform: scale(1.04);
  }

  .hero-overlay {
    position: absolute;
    top: 1.5rem;
    left: 1.5rem;
  }

  .hero-category {
    background: var(--bg-glass);
    backdrop-filter: blur(8px);
    color: var(--text-primary);
    padding: 0.5rem 1rem;
    border-radius: 10px;
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
    box-shadow: var(--shadow-sm);
  }

  .hero-title {
    font-size: clamp(2rem, 4vw, 3.2rem);
    font-weight: 800;
    line-height: 1.1;
    letter-spacing: -0.04em;
    margin: 0 0 1.25rem 0;
    color: var(--text-primary);
  }

  .hero-excerpt {
    font-size: 1.15rem;
    line-height: 1.6;
    color: var(--text-secondary);
    margin: 0;
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  /* Hero Footer Polish */
  .hero-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 1.5rem;
    padding-top: 1rem;
    border-top: 1px solid var(--border-light);
  }

  .hero-date {
    font-size: 0.85rem;
    font-weight: 600;
    color: var(--text-muted);
  }

  .read-more {
    font-size: 0.85rem;
    font-weight: 700;
    color: var(--text-primary);
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  /* Empty Card State */
  .empty-card {
    background: var(--bg-primary);
    border: 1px solid var(--border-light);
    border-radius: 24px;
    padding: 4rem 2rem;
    text-align: center;
    box-shadow: var(--shadow-sm);
  }

  .empty-content {
    max-width: 400px;
    margin: 0 auto;
  }

  .empty-illustration {
    color: var(--text-muted);
    margin-bottom: 1.5rem;
    opacity: 0.5;
  }

  .empty-card h3 {
    font-size: 1.5rem;
    font-weight: 800;
    margin-bottom: 1rem;
    color: var(--text-primary);
  }

  .empty-card p {
    color: var(--text-secondary);
    line-height: 1.6;
    margin-bottom: 2rem;
  }

  .btn-outline {
    border: 1.5px solid var(--text-primary);
    background: transparent;
    color: var(--text-primary);
  }

  .btn-outline:hover {
    background: var(--text-primary);
    color: var(--bg-primary);
  }

  /* Main Layout */
  .main-layout {
    display: grid;
    grid-template-columns: 1fr 300px;
    gap: 3rem;
    max-width: 100%;
    margin: 0 auto;
    padding: 2rem 0;
  }

  .content-area {
    min-width: 0;
  }

  /* Organic Feed - Masonry Style via CSS Columns */
  .organic-feed {
    column-count: 3;
    column-gap: 1.5rem;
    width: 100%;
  }

  @keyframes fadeIn {
    from {
      opacity: 0;
      transform: translateY(12px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  .feed-item {
    display: inline-block;
    width: 100%;
    margin-bottom: 1.5rem;
    break-inside: avoid;
    box-sizing: border-box;
    background: var(--bg-primary);
    border-radius: 20px;
    overflow: hidden;
    border: 1px solid var(--border-light);
    box-shadow: var(--shadow-sm);
    transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
    animation: fadeIn 0.5s cubic-bezier(0.16, 1, 0.3, 1) forwards;
  }

  .feed-item:hover {
    transform: translateY(-6px) scale(1.01);
    box-shadow: var(--shadow-lg);
    border-color: var(--border-dark);
    z-index: 2;
  }

  .feed-card {
    display: flex;
    flex-direction: column;
    text-decoration: none;
    color: inherit;
  }

  .feed-image-wrapper {
    position: relative;
    overflow: hidden;
  }

  .feed-image {
    width: 100%;
    height: auto;
    display: block;
    transition: transform 0.5s ease, filter 0.5s ease;
  }

  .feed-image.blurred {
    filter: blur(40px) grayscale(0.2);
    transform: scale(1.1);
  }

  .pinterest-save-btn {
    position: absolute;
    top: 1rem;
    right: 1rem;
    background: #e60023;
    color: white;
    border: none;
    border-radius: 24px;
    padding: 0.5rem 1rem;
    font-weight: 700;
    font-size: 0.85rem;
    display: flex;
    align-items: center;
    gap: 0.4rem;
    cursor: pointer;
    opacity: 0;
    transform: translateY(-10px);
    transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
    z-index: 10;
  }
  
  .hero-image-wrapper:hover .pinterest-save-btn,
  .feed-image-wrapper:hover .pinterest-save-btn {
    opacity: 1;
    transform: translateY(0);
  }

  .pinterest-save-btn:hover {
    background: #b3001b;
  }

  .feed-chips {
    position: absolute;
    top: 1rem;
    left: 1rem;
    z-index: 2;
  }

  .feed-chip {
    font-size: 0.6rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--text-primary);
    background: var(--bg-glass);
    backdrop-filter: blur(6px);
    padding: 0.35rem 0.75rem;
    border-radius: 8px;
    box-shadow: var(--shadow-sm);
  }

  .feed-chip.age-restricted {
    background: #ff4757;
    color: white;
  }

  .recommendation-badge-wrapper {
    margin-bottom: 2px;
    display: flex;
  }

  .recommendation-badge {
    background: rgba(99, 102, 241, 0.08); /* light Indigo */
    color: #4f46e5;
    font-size: 11px;
    font-weight: 600;
    padding: 3px 8px;
    border-radius: 9999px;
    display: inline-flex;
    align-items: center;
    border: 1px solid rgba(99, 102, 241, 0.15);
    letter-spacing: 0.2px;
    white-space: nowrap;
    text-overflow: ellipsis;
    overflow: hidden;
    max-width: 100%;
  }

  .feed-info {
    padding: 1.25rem;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .feed-title {
    font-size: 1.15rem;
    font-weight: 700;
    line-height: 1.3;
    margin: 0;
    color: var(--text-primary);
    transition: color 0.2s ease;
  }

  .feed-item:hover .feed-title {
    color: var(--accent-hover);
  }

  .feed-excerpt {
    margin: 0;
    font-size: 0.95rem;
    line-height: 1.5;
    color: var(--text-secondary);
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  .feed-meta {
    margin-top: 0.5rem;
    padding-top: 0.75rem;
    border-top: 1px solid var(--border-light);
  }

  .feed-date {
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--text-muted);
  }

  /* Sidebar */
  .sidebar {
    position: sticky;
    top: 80px;
    display: flex;
    flex-direction: column;
    gap: 2rem;
  }

  .widget {
    background: var(--bg-primary);
    border: 1px solid var(--border-light);
    border-radius: 20px;
    padding: 1.5rem;
    box-shadow: var(--shadow-xs);
  }

  .widget-title {
    font-size: 0.8rem;
    font-weight: 800;
    margin: 0 0 1.25rem 0;
    color: var(--text-primary);
    text-transform: uppercase;
    letter-spacing: 1px;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .widget-title::after {
    content: '';
    flex: 1;
    height: 1px;
    background: var(--border-light);
  }

  .categories-list {
    list-style: none;
    padding: 0;
    margin: 0;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .category-link {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.75rem 1rem;
    border-radius: 12px;
    color: var(--text-secondary);
    font-size: 0.9rem;
    font-weight: 500;
    transition: all 0.2s ease;
  }

  .category-link:hover, .category-link.active {
    background: var(--bg-tertiary);
    color: var(--text-primary);
  }

  /* Media Queries */
  @media (max-width: 1100px) {
    .main-layout {
      grid-template-columns: 1fr;
      gap: 3rem;
    }

    .sidebar {
      position: static;
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 1.5rem;
    }

    .search-widget {
      grid-column: span 2;
    }
  }

  @media (max-width: 768px) {
    .page-wrapper.container {
      padding: 0 16px;
      margin: 0 auto;
      overflow-x: hidden;
    }

    .hero-section {
      margin-top: 4px;
      margin-bottom: 1rem;
    }

    .home-ad-wrapper {
      margin-bottom: 1.5rem;
    }

    .main-layout {
      padding: 1rem 0;
    }

    .hero-link {
      grid-template-columns: 1fr;
      padding: 1rem;
      gap: 1.5rem;
      border-radius: 20px;
    }

    .hero-title {
      font-size: 1.8rem;
    }

    .feed-image-wrapper {
      display: flex;
      flex-direction: column;
      overflow: visible;
    }

    .feed-chips {
      position: static;
      padding: 0.6rem 0.75rem 0 0.75rem;
      display: flex;
      flex-wrap: wrap;
      gap: 0.25rem;
    }

    .feed-chip {
      background: rgba(99, 102, 241, 0.08);
      color: var(--accent-primary, #6366f1);
      border: 1px solid rgba(99, 102, 241, 0.15);
      backdrop-filter: none;
      box-shadow: none;
      font-size: 0.65rem;
      padding: 0.25rem 0.5rem;
      border-radius: 6px;
    }

    .recommendation-badge {
      font-size: 9px;
      padding: 2px 6px;
    }

    .organic-feed {
      column-count: 2;
      column-gap: 0.75rem;
    }

    .feed-item {
      margin-bottom: 0.75rem;
      border-radius: 12px;
    }

    .feed-info {
      padding: 0.75rem;
    }

    .feed-title {
      font-size: 0.95rem;
    }

    .feed-excerpt {
      display: none;
    }

    .sidebar {
      grid-template-columns: 1fr;
      margin-top: 1.5rem;
      gap: 1rem;
      padding-bottom: 2rem;
    }

    .widget {
      width: 100%;
      margin: 0;
      padding: 1.25rem;
    }

    .search-widget {
      grid-column: span 1;
      padding: 0;
    }
  }

  @media (max-width: 480px) {
    .page-wrapper.container {
      padding: 0 12px;
    }

    .organic-feed {
      column-gap: 0.5rem;
    }
  }

  /* Sidebar Products Widget Styles */
  .products-widget {
    background: var(--bg-primary);
    border: 1px solid var(--border-light);
    border-radius: 20px;
    padding: 1.5rem;
    box-shadow: var(--shadow-sm);
  }

  .products-carousel {
    position: relative;
    width: 100%;
    margin-top: 1rem;
    overflow: hidden;
  }

  .carousel-inner {
    display: grid;
    grid-template-columns: 100%;
    width: 100%;
  }

  .carousel-slide {
    grid-area: 1 / 1 / 2 / 2;
    opacity: 0;
    pointer-events: none;
    transition: opacity 0.3s ease-in-out;
  }

  .carousel-slide.active {
    opacity: 1;
    pointer-events: auto;
  }

  .product-sidebar-card {
    background: var(--bg-secondary);
    border: 1px solid var(--border-light);
    border-radius: 12px;
    padding: 1.25rem;
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .product-sidebar-image-wrapper {
    width: 100%;
    height: 120px;
    border-radius: 8px;
    overflow: hidden;
    border: 1px solid var(--border-light);
    background: var(--bg-primary);
  }

  .product-sidebar-image {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }

  .product-list-item-thumb {
    width: 36px;
    height: 36px;
    object-fit: cover;
    border-radius: 6px;
    border: 1px solid var(--border-light);
    background: var(--bg-primary);
    flex-shrink: 0;
  }

  .product-sidebar-icon {
    width: 40px;
    height: 40px;
    background: var(--bg-primary);
    border: 1px solid var(--border-light);
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--text-secondary);
  }

  .product-sidebar-name {
    font-size: 0.95rem;
    font-weight: 600;
    color: var(--text-primary);
    margin: 0;
    line-height: 1.3;
  }

  .product-sidebar-desc {
    font-size: 0.8rem;
    color: var(--text-muted);
    margin: 0;
    line-height: 1.4;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  .product-sidebar-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 0.5rem;
  }

  .product-sidebar-price {
    font-size: 0.9rem;
    font-weight: 700;
    color: var(--text-primary);
  }

  .product-sidebar-btn {
    padding: 0.4rem 0.75rem !important;
    font-size: 0.75rem !important;
    font-weight: 600 !important;
    height: auto !important;
  }

  .carousel-nav {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 1rem;
    padding-top: 0.75rem;
    border-top: 1px solid var(--border-light);
  }

  .carousel-nav-btn {
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    width: 28px;
    height: 28px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--text-secondary);
    cursor: pointer;
    transition: all 0.2s;
  }

  .carousel-nav-btn:hover {
    background: var(--bg-primary);
    color: var(--text-primary);
    border-color: var(--text-primary);
  }

  .carousel-indicator {
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--text-muted);
  }

  /* List Mode Styles */
  .products-sidebar-list {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    margin-top: 1rem;
  }

  .product-sidebar-list-item {
    display: flex;
    align-items: flex-start;
    gap: 0.75rem;
    padding: 0.75rem;
    background: var(--bg-secondary);
    border: 1px solid var(--border-light);
    border-radius: 8px;
  }

  .product-list-item-icon {
    width: 28px;
    height: 28px;
    background: var(--bg-primary);
    border: 1px solid var(--border-light);
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--text-muted);
    flex-shrink: 0;
    margin-top: 0.1rem;
  }

  .product-list-item-info {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    flex: 1;
    min-width: 0;
  }

  .product-list-item-name {
    font-size: 0.85rem;
    font-weight: 600;
    color: var(--text-primary);
    line-height: 1.3;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .product-list-item-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .product-list-item-price {
    font-size: 0.75rem;
    font-weight: 700;
    color: var(--text-secondary);
  }

  .product-list-item-link {
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--text-primary);
    text-decoration: underline;
  }

  .product-list-item-link:hover {
    color: var(--text-secondary);
  }

  /* No-image placeholder styling */
  .no-image-placeholder {
    width: 100%;
    aspect-ratio: 16 / 9;
    max-height: 220px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    padding: 1.5rem;
    box-sizing: border-box;
    text-align: center;
    position: relative;
    overflow: hidden;
    user-select: none;
    border-radius: inherit;
  }

  .no-image-placeholder-title {
    font-family: var(--font-sans), sans-serif;
    font-weight: 700;
    color: #1f2937;
    font-size: 1rem;
    line-height: 1.4;
    padding: 0 1rem;
    margin: 0;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
    text-overflow: ellipsis;
    z-index: 2;
  }

  .placeholder-icon {
    position: absolute;
    top: 1.25rem;
    right: 1.25rem;
    color: rgba(17, 24, 39, 0.12);
    z-index: 1;
  }

  .hero-image-wrapper .no-image-placeholder-title {
    font-size: 1.35rem;
    padding: 0 2rem;
    -webkit-line-clamp: 2;
  }

  .product-sidebar-btn-group {
    display: flex;
    gap: 0.25rem;
  }

  .btn-pix-small {
    background: #32bcad !important;
    border-color: #32bcad !important;
    color: white !important;
  }

  .btn-pix-small:hover {
    background: #2a9f92 !important;
    border-color: #2a9f92 !important;
  }

  .product-list-item-btn-group {
    display: inline-flex;
    align-items: center;
    gap: 0.2rem;
  }

  .product-list-item-divider {
    font-size: 0.7rem;
    color: var(--text-muted);
    user-select: none;
  }

  .text-pix {
    color: #2a9f92 !important;
    text-decoration: underline;
  }

  .text-pix:hover {
    color: #207e74 !important;
  }
</style>
