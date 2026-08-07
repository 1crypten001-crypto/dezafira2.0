<script lang="ts">
  import { optimizeImageUrl } from "$lib/image-optimizer";
  import { goto } from "$app/navigation";
  import { page } from "$app/stores";
  import { ageState } from "$lib/stores/age.svelte";
  import type { Post, Category } from "$lib/types";
  import AdRenderer from "$lib/components/AdRenderer.svelte";
  import NewsletterSignup from "$lib/components/NewsletterSignup.svelte";
  import AgeVerification from "$lib/components/AgeVerification.svelte";
  import { t, formatDate as fmtDate, formatMoney } from "$lib/i18n";

  let {
    data,
  }: {
    data: {
      post: Post;
      settings?: Record<string, string>;
      categories: Category[];
      popularPosts: Post[];
      sidebarAds: any[];
      postInlineAds: any[];
      relatedPosts?: Post[];
      products?: any[];
    };
  } = $props();

  const lang = $derived($page.data.language || data.settings?.site_language || 'pt');
  const displayCurrency = $derived(($page.data.displayCurrency as string) || 'BRL');

  let searchInput = $state("");
  let showScrollTop = $state(false);
  let isCoverExpanded = $state(false);
  let expandedProducts = $state<Record<number, boolean>>({});

  let videoExpanded = $state(false);

  function getYouTubeId(url: string | null | undefined): string | null {
    if (!url) return null;
    const regExp = /^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|\&v=|shorts\/)([^#\&\?]*).*/;
    const match = url.match(regExp);
    return (match && match[2].length === 11) ? match[2] : null;
  }

  const videoId = $derived(getYouTubeId(data.post.youtube_video_url));

  $effect(() => {
    if (videoId) {
      const timer = setTimeout(() => {
        videoExpanded = true;
      }, 2000);
      return () => clearTimeout(timer);
    }
  });

  function formatDate(dateString: string) {
    return fmtDate(lang, dateString, {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  }

  function handleSearch(e: Event) {
    e.preventDefault();
    goto(`/?q=${encodeURIComponent(searchInput)}`);
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

  // Calculate reading time (average 200 words per minute)
  const readingTime = $derived(() => {
    const text = data.post.content
      .replace(/<[^>]*>/g, "") // Remove HTML tags
      .replace(/&nbsp;/g, " ")
      .trim();
    const wordCount = text.split(/\s+/).length;
    const minutes = Math.ceil(wordCount / 200);
    return minutes;
  });

  // Generate JSON-LD structured data
  const jsonLd = $derived(() => {
    const siteTitle = data.settings?.site_title || "Blog";
    const baseUrl = $page.url.origin;
    const schema = {
      "@context": "https://schema.org",
      "@type": "Article",
      headline: data.post.title,
      description: data.post.excerpt || data.post.title,
      image: data.post.cover_image ? [data.post.cover_image] : [],
      datePublished: data.post.created_at,
      dateModified: data.post.updated_at || data.post.created_at,
      author: {
        "@type": "Person",
        name: "Admin",
      },
      publisher: {
        "@type": "Organization",
        name: siteTitle,
        logo: {
          "@type": "ImageObject",
          url: data.settings?.seo_image || `${baseUrl}/logo.png`,
        },
      },
      mainEntityOfPage: {
        "@type": "WebPage",
        "@id": `${baseUrl}/post/${data.post.slug}`,
      },
    };

    if (data.post.categories) {
      const categoryList = data.post.categories.split(",");
      (schema as any).articleSection = categoryList[0].trim();
    }

    return JSON.stringify(schema);
  });

// Breadcrumb JSON-LD
  const breadcrumbJsonLd = $derived(() => {
    const baseUrl = $page.url.origin;
    const category = data.post.categories ? data.post.categories.split(",")[0].trim() : null;
    const categorySlug = category ? category.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '') : null;
    
    const itemList = {
      "@context": "https://schema.org",
      "@type": "BreadcrumbList",
      itemListElement: [
        {
          "@type": "ListItem",
          position: 1,
          name: "Home",
          item: baseUrl,
        },
      ],
    };

    if (category && categorySlug) {
      itemList.itemListElement.push({
        "@type": "ListItem",
        position: 2,
        name: category,
        item: `${baseUrl}/category/${categorySlug}`,
      });
    }

    itemList.itemListElement.push({
      "@type": "ListItem",
      position: category ? 3 : 2,
      name: data.post.title,
      item: `${baseUrl}/post/${data.post.slug}`,
    });

    return JSON.stringify(itemList);
  });

  // NewsArticle JSON-LD for Google News
  const newsSchemaLd = $derived(() => {
    return JSON.stringify({
      "@context": "https://schema.org",
      "@type": "NewsArticle",
      "headline": data.post.title,
      "description": data.post.excerpt || data.post.title,
      "image": data.post.cover_image ? [data.post.cover_image] : [],
      "datePublished": data.post.created_at,
      "dateModified": data.post.updated_at || data.post.created_at,
      "author": { "@type": "Person", "name": "Admin" },
      "publisher": {
        "@type": "Organization",
        "name": siteTitle,
        "logo": { "@type": "ImageObject", "url": data.settings?.seo_image || `${$page.url.origin}/logo.png` }
      },
      "mainEntityOfPage": { "@type": "WebPage", "@id": currentUrl },
      "articleSection": data.post.categories ? data.post.categories.split(",")[0].trim() : "Artigo",
      "keywords": data.post.categories || "noticia, artigo",
      "inLanguage": lang === "en" ? "en" : lang === "es" ? "es" : "pt-BR",
      "isAccessibleForFree": true
    });
  });

  // FAQPage JSON-LD (AEO - Answer Engine Optimization)
  const faqSchemaLd = $derived(() => {
    if (!data.post.content) return null;
    
    // Parse h2/h3 questions and the following paragraph as answers
    const faqs = [];
    const regex = /<h[23][^>]*>(.*?)\?<\/h[23]>\s*<p[^>]*>(.*?)<\/p>/gi;
    let match;
    
    while ((match = regex.exec(data.post.content)) !== null) {
      faqs.push({
        "@type": "Question",
        "name": match[1].replace(/<[^>]*>/g, '').trim() + '?',
        "acceptedAnswer": {
          "@type": "Answer",
          "text": match[2].replace(/<[^>]*>/g, '').trim()
        }
      });
    }

    if (faqs.length === 0) return null;

    return JSON.stringify({
      "@context": "https://schema.org",
      "@type": "FAQPage",
      "mainEntity": faqs
    });
  });

  const siteTitle = $derived(data.settings?.site_title || "Blog");
  const siteUrl = $derived($page.url.origin);
  const twitterHandle = $derived(data.settings?.twitter_handle || "");
  const currentUrl = $derived(`${siteUrl}/post/${data.post.slug}`);
  const shareText = $derived(`Confira este artigo: ${data.post.title}`);

  // Image dimension validation for Google News (min 1600px wide recommended)
  const imageForNews = $derived(() => {
    const img = data.post.cover_image;
    if (!img) return null;
    return {
      url: img,
      width: 1600,
      height: 900
    };
  });

  function scrollToTop() {
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  // Track scroll position for scroll-to-top button
  if (typeof window !== "undefined") {
    window.addEventListener("scroll", () => {
      showScrollTop = window.scrollY > 500;
    });
  }

  async function trackEvent(event: string) {
    if (data.settings?.enable_recommendations === '0') return;
    try {
      await fetch('/api/recommendations/track', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ event, postId: data.post.id })
      });
    } catch (e) {
      console.error('Failed to track recommendation event:', e);
    }
  }

  $effect(() => {
    if (typeof window === "undefined" || !data.post?.id) return;

    // 1. Visualizou o artigo (+1 pt)
    trackEvent('view');

    // 2. Passou mais de 3 minutos (+3 pts)
    const readTimer = setTimeout(() => {
      trackEvent('time_3m');
    }, 180000);

    // 3. Rastreamento de Scroll (50% e 100%)
    let tracked50 = false;
    let tracked100 = false;

    const handleScroll = () => {
      const scrollHeight = document.documentElement.scrollHeight - window.innerHeight;
      if (scrollHeight <= 0) return;
      const scrollPct = (window.scrollY / scrollHeight) * 100;

      if (scrollPct >= 50 && !tracked50) {
        tracked50 = true;
        trackEvent('scroll_50'); // (+3 pts)
      }
      if (scrollPct >= 90 && !tracked100) {
        tracked100 = true;
        trackEvent('scroll_100'); // (+5 pts)
        tracked50 = true;
      }
    };

    window.addEventListener('scroll', handleScroll);

    return () => {
      clearTimeout(readTimer);
      window.removeEventListener('scroll', handleScroll);
    };
  });

  function shareOnFacebook() {
    trackEvent('share'); // (+10 pts)
    window.open(
      `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(currentUrl)}`,
      "_blank",
      "width=600,height=400",
    );
  }

  function shareOnTwitter() {
    trackEvent('share'); // (+10 pts)
    const twitterText = encodeURIComponent(shareText);
    const url = encodeURIComponent(currentUrl);
    const handle = twitterHandle.replace("@", "");
    window.open(
      `https://twitter.com/intent/tweet?text=${twitterText}&url=${url}&via=${handle}`,
      "_blank",
      "width=600,height=400",
    );
  }

  function copyLink() {
    trackEvent('share'); // (+10 pts)
    navigator.clipboard.writeText(currentUrl).then(() => {
      alert("Link copiado!");
    });
  }


  function getAbsoluteImageUrl(url: string | null) {
    if (!url) return null;
    if (url.startsWith("http")) return url;
    // Remove double slashes if any
    const cleanUrl = url.startsWith("/") ? url : `/${url}`;
    return `${siteUrl}${cleanUrl}`;
  }

  const absoluteCoverImage = $derived(getAbsoluteImageUrl(data.post.cover_image));
  const absoluteSeoImage = $derived(getAbsoluteImageUrl(data.settings?.seo_image || null));
</script>

<svelte:head>
  <title>{siteTitle} | {data.post.title}</title>
  <meta name="description" content={data.post.excerpt || data.post.title} />

  {#if data.post.categories}
    {@const firstCategory = data.post.categories.split(",")[0].trim()}
    <meta property="article:section" content={firstCategory} />
  {/if}

  <!-- JSON-LD Structured Data - Article -->
  {@html `<script type="application/ld+json">${jsonLd()}</script>`}

  <!-- JSON-LD Structured Data - NewsArticle (Google News) -->
  {@html `<script type="application/ld+json">${newsSchemaLd()}</script>`}

  <!-- Breadcrumb JSON-LD -->
  {@html `<script type="application/ld+json">${breadcrumbJsonLd()}</script>`}

  {#if faqSchemaLd()}
    <!-- FAQPage JSON-LD for AEO / GEO -->
    {@html `<script type="application/ld+json">${faqSchemaLd()}</script>`}
  {/if}

  <!-- Open Graph / Facebook -->
  <meta property="og:type" content="article" />
  <meta property="og:url" content={currentUrl} />
  <meta property="og:title" content={data.post.title} />
  <meta
    property="og:description"
    content={data.post.excerpt || data.post.title}
  />
  {#if absoluteCoverImage}
    <meta property="og:image" content={absoluteCoverImage} />
  {:else if absoluteSeoImage}
    <meta property="og:image" content={absoluteSeoImage} />
  {/if}
  <meta property="og:site_name" content={siteTitle} />
  <meta property="article:published_time" content={data.post.created_at} />
  {#if data.post.updated_at}
    <meta property="article:modified_time" content={data.post.updated_at} />
  {/if}

  <!-- Twitter -->
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content={data.post.title} />
  <meta
    name="twitter:description"
    content={data.post.excerpt || data.post.title}
  />
  {#if absoluteCoverImage}
    <meta name="twitter:image" content={absoluteCoverImage} />
  {:else if absoluteSeoImage}
    <meta name="twitter:image" content={absoluteSeoImage} />
  {/if}
  {#if twitterHandle}
    <meta name="twitter:site" content={twitterHandle} />
  {/if}

  <!-- Canonical URL -->
  <link rel="canonical" href={currentUrl} />
</svelte:head>

<AgeVerification is18Plus={data.post.is_18_plus === 1} />

<div class="post-layout-wrapper container">
  <div class="main-layout">
    <div class="content-area">
      <article class="article">
        {#if data.post.cover_image}
          <div class="article-cover" 
               role="button" 
               tabindex="0"
               onclick={() => isCoverExpanded = true}
               onkeydown={(e) => e.key === 'Enter' && (isCoverExpanded = true)}
               aria-label={t(lang, "post.expand_cover")}
          >
            <img 
              src={optimizeImageUrl(data.post.cover_image, 1200)} 
              alt={data.post.title}
              loading="eager"
              fetchpriority="high"
              width="1200"
              height="630"
            />
            <button 
              class="pinterest-save-btn" 
              onclick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                window.open(`https://pinterest.com/pin/create/button/?url=${encodeURIComponent(currentUrl)}&media=${encodeURIComponent(absoluteCoverImage || data.post.cover_image)}&description=${encodeURIComponent(data.post.title)}`, '_blank', 'width=600,height=400');
              }}
              aria-label={t(lang, "home.save_pinterest")}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M12.017 0C5.396 0 .029 5.367.029 11.987c0 5.079 3.158 9.417 7.618 11.162-.105-.949-.199-2.403.041-3.439.219-.937 1.406-5.957 1.406-5.957s-.359-.72-.359-1.781c0-1.663.967-2.911 2.168-2.911 1.024 0 1.518.769 1.518 1.688 0 1.029-.653 2.567-.992 3.992-.285 1.193.6 2.165 1.775 2.165 2.128 0 3.768-2.245 3.768-5.487 0-2.861-2.063-4.869-5.008-4.869-3.41 0-5.409 2.562-5.409 5.199 0 1.033.394 2.143.889 2.741.099.12.112.225.085.345-.09.375-.293 1.199-.334 1.363-.053.225-.172.271-.401.165-1.495-.69-2.433-2.878-2.433-4.646 0-3.776 2.748-7.252 7.92-7.252 4.158 0 7.392 2.967 7.392 6.923 0 4.135-2.607 7.462-6.233 7.462-1.214 0-2.354-.629-2.758-1.379l-.749 2.848c-.269 1.045-1.004 2.352-1.498 3.146 1.123.345 2.306.535 3.55.535 6.607 0 11.985-5.365 11.985-11.987C23.97 5.366 18.605 0 12.017 0z"/></svg>
              Salvar
            </button>
            <div class="expand-hint">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="11" cy="11" r="8"></circle>
                <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                <line x1="11" y1="8" x2="11" y2="14"></line>
                <line x1="8" y1="11" x2="14" y2="11"></line>
              </svg>
            </div>
          </div>
        {/if}

        <header class="article-header">
          <div class="article-meta-top">
            <span class="article-category">
              {data.post.categories ? data.post.categories.split(",")[0] : "Post"}
            </span>
            <span class="article-date">{formatDate(data.post.created_at)}</span>
          </div>
          <h1 class="article-title">{data.post.title}</h1>
          {#if data.post.excerpt}
            <section class="ai-summary" aria-label="Resumo do Artigo" role="doc-abstract">
              <strong>💡 {t(lang, "post.quick_summary")}</strong> {data.post.excerpt}
            </section>
          {/if}
          <div class="article-meta">
            <span class="meta-item">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10" />
                <polyline points="12 6 12 12 16 14" />
              </svg>
              {readingTime()} {t(lang, "post.min_read")}
            </span>
          </div>
        </header>

        {#if videoId}
          <div class="post-video-card-container" class:expanded={videoExpanded}>
            <div class="post-video-card">
              <div class="video-header">
                <span class="video-pulse-container">
                  <span class="pulse-dot"></span>
                </span>
              </div>
              <div class="video-wrapper">
                {#if videoExpanded}
                  <iframe
                    src="https://www.youtube.com/embed/{videoId}?autoplay=1&mute=1&enablejsapi=1"
                    title={t(lang, "post.article_video")}
                    frameborder="0"
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                    allowfullscreen
                  ></iframe>
                {:else}
                  <button class="video-thumbnail-placeholder" onclick={() => videoExpanded = true}>
                    <img src="https://img.youtube.com/vi/{videoId}/maxresdefault.jpg" alt={t(lang, "post.video_thumb")} />
                    <div class="play-button-placeholder">
                      <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                        <polygon points="5 3 19 12 5 21 5 3"/>
                      </svg>
                    </div>
                  </button>
                {/if}
              </div>
            </div>
          </div>
        {/if}

        <div class="article-content-wrapper">
          <div class="article-content" class:premium-blur={!data.hasAccess}>
            {#if data.postInlineAds && data.postInlineAds.length > 0 && data.hasAccess}
              {@const paragraphs = data.post.content.split("</p>")}
              {#each paragraphs as p, i}
                {#if p.trim()}
                  {@html p + "</p>"}
                {/if}
                {#if i === Math.floor(paragraphs.length / 2) - 1}
                  <AdRenderer ads={data.postInlineAds} placement="post_inline" />
                {/if}
              {/each}
            {:else}
              {@html data.post.content}
            {/if}

            {#if !data.hasAccess}
              <div class="premium-paywall">
                <div class="paywall-overlay"></div>
                <div class="paywall-card">
                  <div class="paywall-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                      <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                      <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                    </svg>
                  </div>
                  <h2>{t(lang, "post.premium_title")}</h2>
                  {#if !data.user}
                    <p>Este artigo é exclusivo para membros do blog. Cadastre-se ou entre em sua conta para assinar um plano e continuar lendo.</p>
                    <div class="paywall-actions">
                      <a href="/members/login" class="btn btn-primary">{t(lang, "common.login")}</a>
                      <a href="/members/register" class="btn btn-secondary">{t(lang, "common.register")}</a>
                    </div>
                  {:else}
                    <p>Este artigo é exclusivo para membros Premium. Adquira uma assinatura premium para ter acesso imediato a todos os posts exclusivos.</p>
                    <div class="paywall-actions">
                      <a href="/premium" class="btn btn-primary">{t(lang, "post.view_plans")}</a>
                    </div>
                  {/if}
                </div>
              </div>
            {/if}
          </div>
        </div>

        {#if data.products && data.products.length > 0 && data.hasAccess}
          <div class="product-attachments-box">
            <h2>📎 {t(lang, "post.attachments")}</h2>
            <p>Este post contém arquivos digitais para download ou links adicionais:</p>
            <div class="products-attachments-list">
              {#each data.products as product}
                <div class="product-attachment-item">
                  <div class="product-attachment-left">
                    {#if product.image_url}
                      <a href="/product/{product.slug}">
                        <img src={product.image_url} alt={product.name} class="product-attachment-thumb" />
                      </a>
                    {:else}
                      <div class="product-attachment-thumb-placeholder">
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
                    <div class="product-attachment-info">
                      <a href="/product/{product.slug}" class="product-attachment-name-link">
                        <span class="product-attachment-name">{product.name}</span>
                      </a>
                      {#if product.description}
                        <div class="product-attachment-desc-container">
                          <div class="product-attachment-desc-wrapper">
                            <span class="product-attachment-desc">{product.description}</span>
                            {#if product.description.length > 200}
                              <div class="desc-fade-overlay"></div>
                            {/if}
                          </div>
                          {#if product.description.length > 200}
                            <a 
                              href="/product/{product.slug}" 
                              class="toggle-desc-btn"
                            >
                              Ver detalhes do produto
                              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="margin-left: 4px;">
                                <line x1="5" y1="12" x2="19" y2="12"></line>
                                <polyline points="12 5 19 12 12 19"></polyline>
                              </svg>
                            </a>
                          {/if}
                        </div>
                      {/if}
                    </div>
                  </div>
                  <div class="product-attachment-action">
                    {#if product.price_cents > 0}
                      <span class="product-price">{formatMoney(lang, product.price_cents, displayCurrency)}</span>
                    {/if}
                    {#if product.price_cents > 0 && !product.hasPurchased}
                      {#if data.settings?.enable_member_login !== '1'}
                        <button class="btn btn-small btn-secondary" disabled style="opacity: 0.6; cursor: not-allowed;">
                          {t(lang, "post.not_available")}
                        </button>
                      {:else if !data.user}
                        <a href="/members/login?redirectTo={encodeURIComponent($page.url.pathname)}" class="btn btn-small btn-primary buy-btn">
                          {t(lang, "common.buy")}
                        </a>
                      {:else}
                        <a href="/purchase/{product.id}" class="btn btn-small btn-primary buy-btn" data-sveltekit-reload target="_blank" rel="noopener noreferrer">
                          {t(lang, "common.buy")}
                        </a>
                      {/if}
                    {:else}
                      {#if product.file_url}
                        <a href="/api/download/{product.id}" rel="external" class="btn btn-small btn-primary">
                          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>
                          </svg>
                          {t(lang, "post.download_file")}
                        </a>
                      {:else if product.external_link}
                        <a href={product.external_link} target="_blank" class="btn btn-small btn-secondary">
                          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/>
                          </svg>
                          {t(lang, "post.access_link")}
                        </a>
                      {/if}
                    {/if}
                  </div>
                </div>
              {/each}
            </div>
          </div>
        {/if}

        <footer class="article-footer">
          <div class="author-box">
            <div class="author-avatar">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                <circle cx="12" cy="7" r="4" />
              </svg>
            </div>
            <div class="author-info">
              <span class="author-name">Admin</span>
              <span class="author-date">{t(lang, "post.published_on")} {formatDate(data.post.created_at)}</span>
            </div>
          </div>

          <div class="sharing-buttons">
            <button class="share-btn" onclick={shareOnFacebook} aria-label="Compartilhar no Facebook">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
              </svg>
              Facebook
            </button>
            <button class="share-btn" onclick={shareOnTwitter} aria-label="Compartilhar no Twitter">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
              </svg>
              Twitter
            </button>
            <button class="share-btn" onclick={copyLink} aria-label={t(lang, "post.copy_link")}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" />
                <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" />
              </svg>
              {t(lang, "post.copy_link")}
            </button>
          </div>
        </footer>

        {#if data.relatedPosts && data.relatedPosts.length > 0}
          {@const hasCollaborative = data.relatedPosts.some(p => (p as any).isCollaborative)}
          <section class="organic-related">
            <h2 class="related-title">{hasCollaborative ? t(lang, "post.related_title") : t(lang, "post.continue_reading")}</h2>
            <div class="related-feed">
              {#each data.relatedPosts as relatedPost}
                <a href="/post/{relatedPost.slug}" class="related-item">
                  <div class="related-image-wrapper">
                    {#if hasNoImage(relatedPost)}
                      <div class="no-image-placeholder" style="background: {getPlaceholderBackground(relatedPost)}">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="placeholder-icon">
                          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                          <polyline points="14 2 14 8 20 8"></polyline>
                          <line x1="16" y1="13" x2="8" y2="13"></line>
                          <line x1="16" y1="17" x2="8" y2="17"></line>
                          <polyline points="10 9 9 9 8 9"></polyline>
                        </svg>
                        <div class="no-image-placeholder-title">
                          {relatedPost.title}
                        </div>
                      </div>
                    {:else}
                      <img 
                        src={optimizeImageUrl(getPostImage(relatedPost), 400)} 
                        alt={relatedPost.title} 
                        loading="lazy" 
                        class:blurred={relatedPost.is_18_plus && !ageState.confirmed}
                        width="400"
                        height="250"
                      />
                    {/if}
                    <button 
                      class="pinterest-save-btn" 
                      onclick={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        window.open(`https://pinterest.com/pin/create/button/?url=${encodeURIComponent($page.url.origin + '/post/' + relatedPost.slug)}&media=${encodeURIComponent(getPostImage(relatedPost))}&description=${encodeURIComponent(relatedPost.title)}`, '_blank', 'width=600,height=400');
                      }}
                      aria-label={t(lang, "home.save_pinterest")}
                    >
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M12.017 0C5.396 0 .029 5.367.029 11.987c0 5.079 3.158 9.417 7.618 11.162-.105-.949-.199-2.403.041-3.439.219-.937 1.406-5.957 1.406-5.957s-.359-.72-.359-1.781c0-1.663.967-2.911 2.168-2.911 1.024 0 1.518.769 1.518 1.688 0 1.029-.653 2.567-.992 3.992-.285 1.193.6 2.165 1.775 2.165 2.128 0 3.768-2.245 3.768-5.487 0-2.861-2.063-4.869-5.008-4.869-3.41 0-5.409 2.562-5.409 5.199 0 1.033.394 2.143.889 2.741.099.12.112.225.085.345-.09.375-.293 1.199-.334 1.363-.053.225-.172.271-.401.165-1.495-.69-2.433-2.878-2.433-4.646 0-3.776 2.748-7.252 7.92-7.252 4.158 0 7.392 2.967 7.392 6.923 0 4.135-2.607 7.462-6.233 7.462-1.214 0-2.354-.629-2.758-1.379l-.749 2.848c-.269 1.045-1.004 2.352-1.498 3.146 1.123.345 2.306.535 3.55.535 6.607 0 11.985-5.365 11.985-11.987C23.97 5.366 18.605 0 12.017 0z"/></svg>
                      Salvar
                    </button>
                  </div>
                  <div class="related-content">
                    <div class="related-meta-row">
                      <span class="related-category">
                        {relatedPost.categories ? relatedPost.categories.split(",")[0] : "Post"}
                      </span>
                      {#if (relatedPost as any).recommendationReason}
                        <span class="related-rec-badge">{(relatedPost as any).recommendationReason}</span>
                      {/if}
                    </div>
                    <h3 class="related-post-title">{relatedPost.title}</h3>
                    <span class="related-post-date">{formatDate(relatedPost.created_at)}</span>
                  </div>
                </a>
              {/each}
            </div>
          </section>
        {/if}
      </article>
    </div>

    <aside class="sidebar">
      <div class="widget search-widget">
        <form onsubmit={handleSearch} class="search-form">
          <input type="text" bind:value={searchInput} placeholder={t(lang, "home.search_placeholder")} class="search-input" />
          <button type="submit" class="search-btn" aria-label="Buscar posts">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="11" cy="11" r="8" />
              <path d="M21 21l-4.35-4.35" />
            </svg>
          </button>
        </form>
      </div>

      {#if data.sidebarAds && data.sidebarAds.length > 0}
        <div class="widget ad-widget">
          <AdRenderer ads={data.sidebarAds} placement="sidebar" />
        </div>
      {/if}

      <div class="widget categories-widget">
        <h2 class="widget-title">{t(lang, "common.categories")}</h2>
        <ul class="categories-list">
          {#each data.categories as cat}
            <li>
              <a href="/category/{cat.slug}" class="category-link">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z" />
                </svg>
                {cat.name}
              </a>
            </li>
          {/each}
        </ul>
      </div>

      <div class="widget newsletter-widget">
        <NewsletterSignup />
      </div>
    </aside>
  </div>

  {#if showScrollTop}
    <button class="scroll-to-top" onclick={scrollToTop} aria-label={t(lang, "post.back_to_top")}>
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M18 15l-6-6-6 6" />
      </svg>
    </button>
  {/if}

  {#if isCoverExpanded && data.post.cover_image}
    <div class="lightbox-overlay" onclick={() => isCoverExpanded = false} role="button" tabindex="0" onkeydown={(e) => e.key === 'Escape' && (isCoverExpanded = false)}>
      <button class="lightbox-close" aria-label="Fechar" onclick={() => isCoverExpanded = false}>
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M18 6L6 18M6 6l12 12"></path>
        </svg>
      </button>
      <img src={optimizeImageUrl(data.post.cover_image, 1920)} alt={data.post.title} class="lightbox-img" onclick={(e) => e.stopPropagation()} role="presentation" />
    </div>
  {/if}
</div>

<style>
  .post-layout-wrapper {
    padding: 2rem 0 5rem;
  }

  .main-layout {
    display: grid;
    grid-template-columns: 1fr 280px;
    gap: 3rem;
  }

  .content-area {
    min-width: 0;
  }

  .article {
    background: transparent;
    animation: fadeIn 0.5s ease-out;
  }

  .article-cover {
    width: 100%;
    aspect-ratio: 16/9;
    overflow: hidden;
    border-radius: 24px;
    margin-bottom: 3rem;
    box-shadow: var(--shadow-lg);
    background: var(--bg-tertiary);
    border: 1px solid var(--border-light);
    position: relative;
    cursor: zoom-in;
  }

  .article-cover img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    object-position: top;
    transition: transform 0.6s cubic-bezier(0.4, 0, 0.2, 1);
  }

  .article-cover:hover img {
    transform: scale(1.02);
  }

  .article-header {
    margin-bottom: 2.5rem;
    max-width: 800px;
  }

  .article-meta-top {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 1rem;
  }

  .article-category {
    background: var(--bg-tertiary);
    color: var(--text-primary);
    padding: 0.35rem 0.75rem;
    border-radius: 6px;
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .article-date {
    font-size: 0.85rem;
    color: var(--text-tertiary);
  }

  .article-title {
    font-family: var(--font-serif);
    font-size: clamp(2rem, 5vw, 3.25rem);
    font-weight: 600;
    line-height: 1.15;
    letter-spacing: -0.02em;
    margin-bottom: 1rem;
    color: var(--text-primary);
  }

  .ai-summary {
    font-size: 1.15rem;
    line-height: 1.6;
    color: var(--text-secondary);
    margin-bottom: 1.5rem;
    background: var(--bg-tertiary);
    padding: 1.25rem;
    border-radius: 12px;
    border-left: 4px solid var(--text-primary);
  }
  
  .ai-summary strong {
    color: var(--text-primary);
  }

  .article-meta {
    display: flex;
    gap: 1.5rem;
    font-size: 0.9rem;
    color: var(--text-muted);
  }

  .meta-item {
    display: flex;
    align-items: center;
    gap: 0.4rem;
  }

  .article-content-wrapper {
    max-width: 720px;
  }

  .article-content {
    font-family: var(--font-serif);
    font-size: 1.15rem;
    line-height: 1.85;
    color: var(--text-primary);
  }

  :global(.article-content p) {
    margin-bottom: 1.5rem;
  }

  :global(.article-content h2) {
    font-family: var(--font-serif);
    font-size: 1.75rem;
    margin: 2.5rem 0 1rem;
  }

  :global(.article-content img) {
    max-width: 100%;
    height: auto;
    border-radius: 12px;
    margin: 2rem 0;
  }

  :global(.article-content blockquote) {
    border-left: 3px solid var(--text-primary);
    padding-left: 1.5rem;
    margin: 2rem 0;
    font-style: italic;
    color: var(--text-secondary);
  }

  .article-footer {
    margin-top: 3rem;
    padding-top: 2rem;
    border-top: 1px solid var(--border-light);
  }

  .author-box {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 2rem;
  }

  .author-avatar {
    width: 48px;
    height: 48px;
    background: var(--bg-tertiary);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--text-muted);
  }

  .author-info {
    display: flex;
    flex-direction: column;
  }

  .author-name {
    font-weight: 600;
    font-size: 0.95rem;
    color: var(--text-primary);
  }

  .author-date {
    font-size: 0.8rem;
    color: var(--text-muted);
  }

  .sharing-buttons {
    display: flex;
    gap: 0.75rem;
    flex-wrap: wrap;
  }

  .share-btn {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.6rem 1rem;
    border: 1px solid var(--border-color);
    border-radius: 8px;
    background: var(--bg-primary);
    font-family: var(--font-sans);
    font-size: 0.8rem;
    font-weight: 500;
    color: var(--text-primary);
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .share-btn:hover {
    border-color: var(--text-primary);
    background: var(--bg-secondary);
  }

  .organic-related {
    margin-top: 4rem;
    padding-top: 3rem;
    border-top: 1px solid var(--border-light);
  }

  .related-title {
    font-family: var(--font-sans);
    font-size: 1.5rem;
    font-weight: 700;
    margin-bottom: 2rem;
    color: var(--text-primary);
  }

  .related-feed {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
    gap: 1.5rem;
  }

  .related-item {
    break-inside: avoid;
    margin-bottom: 1.5rem;
    display: inline-block;
    width: 100%;
    text-decoration: none;
    color: inherit;
    border-radius: 16px;
    overflow: hidden;
    background: var(--bg-primary);
    border: 1px solid var(--border-light);
    box-shadow: var(--shadow-sm);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }

  .related-item:hover {
    transform: translateY(-4px);
    box-shadow: var(--shadow-md);
    border-color: var(--text-primary);
  }

  .related-image-wrapper {
    position: relative;
    width: 100%;
    overflow: hidden;
  }

  .related-image-wrapper img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    object-position: top;
    transition: transform 0.3s ease;
  }

  .related-item:hover .related-image-wrapper img {
    transform: scale(1.05);
  }

  .related-image-wrapper img.blurred {
    filter: blur(30px) grayscale(0.2);
    transform: scale(1.1);
  }

  .related-content {
    padding: 1.25rem;
  }

  .related-category {
    display: inline-block;
    font-size: 0.65rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: var(--accent-color, #3b82f6);
  }

  .related-meta-row {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 6px;
    margin-bottom: 0.4rem;
  }

  .related-rec-badge {
    background: rgba(99, 102, 241, 0.08);
    color: #4f46e5;
    font-size: 9.5px;
    font-weight: 600;
    padding: 2px 7px;
    border-radius: 9999px;
    display: inline-flex;
    align-items: center;
    border: 1px solid rgba(99, 102, 241, 0.15);
    white-space: nowrap;
  }

  .related-post-title {
    font-family: var(--font-sans);
    font-size: 1rem;
    font-weight: 600;
    line-height: 1.4;
    margin-bottom: 0.4rem;
    color: var(--text-primary);
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
    transition: color 0.2s ease;
  }

  .related-item:hover .related-post-title {
    color: var(--accent-color, #3b82f6);
  }

  .related-post-date {
    font-size: 0.75rem;
    color: var(--text-muted);
  }

  .sidebar {
    position: sticky;
    top: 2rem;
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }

  .widget {
    background: var(--bg-primary);
    border: 1px solid var(--border-light);
    border-radius: 14px;
    padding: 1.25rem;
  }

  .widget-title {
    font-size: 0.8rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 1rem;
    color: var(--text-primary);
  }

  .search-widget {
    padding: 0;
    border: none;
    background: transparent;
  }

  .search-form {
    display: flex;
  }

  .search-input {
    flex: 1;
    background: var(--bg-primary);
    border: 1px solid var(--border-color);
    padding: 0.7rem 1rem;
    border-radius: 10px 0 0 10px;
    font-size: 0.9rem;
    outline: none;
  }

  .search-btn {
    background: var(--text-primary);
    color: var(--bg-primary);
    width: 42px;
    border-radius: 0 10px 10px 0;
    border: none;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .categories-list {
    list-style: none;
    padding: 0;
  }

  .category-link {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.6rem 0.5rem;
    text-decoration: none;
    color: var(--text-secondary);
    font-size: 0.9rem;
    border-radius: 6px;
    transition: all 0.2s ease;
  }

  .category-link:hover {
    background: var(--bg-secondary);
    color: var(--text-primary);
  }

  .scroll-to-top {
    position: fixed;
    bottom: 2rem;
    right: 2rem;
    width: 48px;
    height: 48px;
    background: var(--text-primary);
    color: var(--bg-primary);
    border: none;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    box-shadow: var(--shadow-lg);
    transition: all 0.2s ease;
    z-index: 100;
    animation: fadeIn 0.3s ease-out;
  }

  .scroll-to-top:hover {
    transform: translateY(-4px);
    box-shadow: var(--shadow-xl);
  }

  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
  }

  @media (max-width: 1024px) {
    .main-layout {
      grid-template-columns: 1fr;
    }

    .sidebar {
      display: none;
    }

    .related-feed {
      column-count: 2;
      column-gap: 1rem;
    }
  }

  @media (max-width: 768px) {
    .article-title {
      font-size: 1.75rem;
    }

    .article-cover {
      aspect-ratio: 16/9;
      border-radius: 12px;
    }

    .sharing-buttons {
      flex-direction: column;
    }

    .share-btn {
      width: 100%;
      justify-content: center;
    }

    .related-feed {
      column-count: 2;
      column-gap: 0.75rem;
    }
  }

  /* Lightbox and Pinterest Additions */
  .expand-hint {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%) scale(0.8);
    background: rgba(0, 0, 0, 0.6);
    color: white;
    width: 80px;
    height: 80px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    opacity: 0;
    transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
    pointer-events: none;
    z-index: 2;
  }

  .article-cover:hover .expand-hint {
    opacity: 1;
    transform: translate(-50%, -50%) scale(1);
  }

  .article-cover::after {
    content: '';
    position: absolute;
    inset: 0;
    background: rgba(0,0,0,0.3);
    opacity: 0;
    transition: opacity 0.3s ease;
    pointer-events: none;
    z-index: 1;
  }

  .article-cover:hover::after {
    opacity: 1;
  }

  .pinterest-save-btn {
    position: absolute;
    top: 1.5rem;
    right: 1.5rem;
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
  
  .article-cover:hover .pinterest-save-btn,
  .related-image-wrapper:hover .pinterest-save-btn {
    opacity: 1;
    transform: translateY(0);
  }

  .pinterest-save-btn:hover {
    background: #b3001b;
  }

  .lightbox-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background: rgba(0, 0, 0, 0.9);
    z-index: 99999;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: zoom-out;
    animation: fadeIn 0.3s ease;
  }

  .lightbox-close {
    position: absolute;
    top: 20px;
    right: 20px;
    background: rgba(255, 255, 255, 0.1);
    color: white;
    border: none;
    border-radius: 50%;
    width: 48px;
    height: 48px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: background 0.2s;
  }

  .lightbox-close:hover {
    background: rgba(255, 255, 255, 0.2);
  }

  .lightbox-img {
    max-width: 90vw;
    max-height: 90vh;
    object-fit: contain;
    border-radius: 8px;
    cursor: default;
    box-shadow: 0 20px 50px rgba(0,0,0,0.5);
  }

  /* Premium Paywall Styles */
  .premium-paywall {
    position: relative;
    padding: 3rem 1rem;
    margin-top: 1rem;
    z-index: 10;
  }

  .paywall-overlay {
    position: absolute;
    top: -120px;
    left: 0;
    right: 0;
    height: 120px;
    background: linear-gradient(to bottom, transparent, var(--bg-primary));
    pointer-events: none;
  }

  .paywall-card {
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-lg);
    padding: 3rem 2rem;
    max-width: 500px;
    margin: 0 auto;
    box-shadow: var(--shadow-lg);
    text-align: center;
  }

  .paywall-icon {
    width: 56px;
    height: 56px;
    margin: 0 auto 1.5rem;
    background: #fffbeb;
    color: #d97706;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 1px solid #fef3c7;
  }

  :global([data-theme="dark"]) .paywall-icon {
    background: #2d2006;
    color: #f59e0b;
    border-color: #453008;
  }

  .paywall-icon svg {
    width: 24px;
    height: 24px;
  }

  .paywall-card h3 {
    font-size: 1.35rem;
    font-weight: 700;
    margin-bottom: 0.75rem;
    color: var(--text-primary);
  }

  .paywall-card p {
    color: var(--text-secondary);
    font-size: 0.925rem;
    line-height: 1.6;
    margin-bottom: 2rem;
  }

  .paywall-actions {
    display: flex;
    gap: 1rem;
    justify-content: center;
  }

  .paywall-actions .btn {
    padding: 0.75rem 1.75rem;
    font-size: 0.875rem;
    font-weight: 600;
  }

  /* Product Attachments Styles */
  .product-attachments-box {
    margin-top: 3rem;
    padding: 2rem;
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-lg);
    font-family: var(--font-sans);
  }

  .product-attachments-box h3 {
    font-size: 1.25rem;
    font-weight: 700;
    margin-bottom: 0.5rem;
    color: var(--text-primary);
  }

  .product-attachments-box p {
    font-size: 0.9rem;
    color: var(--text-secondary);
    margin-bottom: 1.5rem;
  }

  .products-attachments-list {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .product-attachment-item {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    padding: 1.25rem;
    background: var(--bg-primary);
    border: 1px solid var(--border-light);
    border-radius: var(--radius-md);
    gap: 1.5rem;
  }

  .product-attachment-left {
    display: flex;
    align-items: flex-start;
    gap: 1rem;
    flex: 1;
  }

  .product-attachment-thumb {
    width: 64px;
    height: 64px;
    object-fit: cover;
    border-radius: var(--radius-sm);
    border: 1px solid var(--border-light);
    background: var(--bg-secondary);
    flex-shrink: 0;
  }

  .product-attachment-thumb-placeholder {
    width: 64px;
    height: 64px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: var(--radius-sm);
    border: 1px dashed var(--border-light);
    background: var(--bg-secondary);
    color: var(--text-muted);
    flex-shrink: 0;
  }

  .product-attachment-info {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    flex: 1;
  }

  .product-attachment-name-link {
    text-decoration: none;
    display: inline-block;
  }

  .product-attachment-name-link:hover .product-attachment-name {
    color: var(--accent-color, #3b82f6);
  }

  .product-attachment-desc-container {
    display: flex;
    flex-direction: column;
    width: 100%;
  }

  .product-attachment-desc-wrapper {
    position: relative;
    max-height: 5.8rem;
    overflow: hidden;
    transition: max-height 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    width: 100%;
  }

  .product-attachment-desc {
    font-size: 0.825rem;
    color: var(--text-muted);
    white-space: pre-wrap;
    line-height: 1.5;
    display: block;
  }

  .desc-fade-overlay {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    height: 40px;
    background: linear-gradient(to bottom, transparent 0%, var(--bg-primary) 100%);
    pointer-events: none;
  }

  .toggle-desc-btn {
    background: transparent;
    border: none;
    color: var(--accent-color, #3b82f6);
    font-size: 0.8rem;
    font-weight: 600;
    cursor: pointer;
    padding: 0;
    margin-top: 0.5rem;
    display: inline-flex;
    align-items: center;
    text-decoration: none;
    width: fit-content;
  }

  .toggle-desc-btn:hover {
    text-decoration: underline;
  }

  .toggle-desc-btn svg {
    transition: transform 0.2s;
  }

  .toggle-desc-btn:hover svg {
    transform: translateX(3px);
  }

  .product-attachment-action {
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  .product-price {
    font-weight: 700;
    color: var(--text-primary);
    font-size: 1rem;
  }

  .product-attachment-action .btn {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    font-size: 0.8rem;
    font-weight: 600;
    white-space: nowrap;
  }

  @media (max-width: 640px) {
    .product-attachment-item {
      flex-direction: column;
      align-items: flex-start;
      gap: 1rem;
    }
    .product-attachment-left {
      width: 100%;
    }
    .product-attachment-action {
      width: 100%;
      justify-content: space-between;
    }
  }

  /* No-image placeholder styling */
  .no-image-placeholder {
    width: 100%;
    aspect-ratio: 16 / 9;
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
    font-weight: 800;
    color: #111827;
    font-size: 1.25rem;
    line-height: 1.4;
    margin: 0;
    display: -webkit-box;
    -webkit-line-clamp: 3;
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

  /* Featured Video Player Styles */
  .post-video-card-container {
    max-height: 0;
    opacity: 0;
    overflow: hidden;
    transform: scale(0.95);
    transition:
      max-height 0.8s cubic-bezier(0.16, 1, 0.3, 1),
      opacity    0.8s cubic-bezier(0.16, 1, 0.3, 1),
      transform  0.8s cubic-bezier(0.16, 1, 0.3, 1),
      margin     0.8s cubic-bezier(0.16, 1, 0.3, 1);
    margin-bottom: 0;
  }
  
  .post-video-card-container.expanded {
    max-height: 800px;
    opacity: 1;
    transform: scale(1);
    margin-bottom: 3rem;
  }

  .post-video-card {
    background: var(--bg-primary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-md);
    padding: 1.25rem;
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .video-header {
    display: flex;
    align-items: center;
  }

  .video-pulse-container {
    display: inline-flex;
    align-items: center;
    justify-content: center;
  }

  .pulse-dot {
    width: 8px;
    height: 8px;
    background-color: #ef4444;
    border-radius: 50%;
    display: inline-block;
    box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7);
    animation: pulse-post 1.5s infinite;
  }

  @keyframes pulse-post {
    0%   { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7); }
    70%  { transform: scale(1);    box-shadow: 0 0 0 8px rgba(239, 68, 68, 0); }
    100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
  }

  .video-wrapper {
    position: relative;
    width: 100%;
    padding-bottom: 56.25%; /* 16:9 aspect ratio */
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
    border: none;
    background: transparent;
    padding: 0;
  }

  .video-thumbnail-placeholder img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    opacity: 0.6;
  }

  .play-button-placeholder {
    position: absolute;
    width: 58px;
    height: 58px;
    background: rgba(239, 68, 68, 0.9);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #fff;
    box-shadow: 0 4px 15px rgba(239, 68, 68, 0.4);
    transition: transform 0.3s ease, background 0.3s ease;
  }

  .play-button-placeholder svg {
    margin-left: 2px;
  }
</style>
