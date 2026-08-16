<script lang="ts">
  import { page } from "$app/stores";
  import { optimizeImageUrl } from "$lib/image-optimizer";
  import type { Product } from "$lib/types";
  import { t, formatMoney } from "$lib/i18n";

  let { data } = $props();
  const lang = $derived(data.settings?.site_language || $page.data.language || 'pt');
  const displayCurrency = $derived(($page.data.displayCurrency as string) || 'BRL');

  let searchQuery = $state("");
  /** "all" or product category id as string (stable filter key; avoids legacy category name collision) */
  let selectedCategory = $state("all");
  let expandedDescriptions = $state<Record<number, boolean>>({});

  // Helper to format price
  function formatPrice(cents: number) {
    if (cents === 0) return t(lang, 'products.free');
    return formatMoney(lang, cents, displayCurrency);
  }

  // Predefined/cached gradients for product placeholders
  function getPlaceholderBackground(id: any) {
    const gradients = [
      'linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%)',
      'linear-gradient(135deg, #10b981 0%, #047857 100%)',
      'linear-gradient(135deg, #f59e0b 0%, #b45309 100%)',
      'linear-gradient(135deg, #ec4899 0%, #be185d 100%)',
      'linear-gradient(135deg, #8b5cf6 0%, #6d28d9 100%)'
    ];
    const hash = String(id).charCodeAt(0) || 0;
    return gradients[hash % gradients.length];
  }

  // Categories from product_categories table (admin-managed)
  const categories = $derived(
    (data.categories ?? []).filter((c: { id: number; name: string }) => c?.name)
  );

  // Filter by category_id (not name) so LibSQL legacy column collision can't break the filter
  const filteredProducts = $derived(
    data.products.filter((p: Product & { category_id?: number | null }) => {
      const matchesSearch = p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                            (p.description && p.description.toLowerCase().includes(searchQuery.toLowerCase()));
      const matchesCategory =
        selectedCategory === "all" ||
        String(p.category_id ?? "") === selectedCategory;
      return matchesSearch && matchesCategory;
    })
  );

  const siteTitle = $derived(data.settings?.site_title || "Blog");
  // Helper to format clean summary
  function getProductSummary(description: string) {
    if (!description) return "";
    const cleanText = description.replace(/\s+/g, ' ').trim();
    if (cleanText.length <= 130) return cleanText;
    return cleanText.substring(0, 130) + "...";
  }
</script>

<svelte:head>
  <title>{t(lang, "products.title")} | {siteTitle}</title>
  <meta name="description" content={t(lang, "products.meta_desc")} />
</svelte:head>

<div class="vitrine-container">
  <!-- Header -->
  <div class="vitrine-header">
    <h1>{t(lang, "products.title")}</h1>
    <p>{t(lang, "products.subtitle")}</p>
    
    <!-- Search and Filter Bar -->
    <div class="filter-bar">
      <div class="search-wrapper">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
        </svg>
        <input 
          type="text" 
          placeholder={t(lang, "products.search_placeholder")} 
          bind:value={searchQuery}
        />
      </div>
    </div>

    <!-- Category Pills -->
    {#if categories.length > 0}
      <div class="category-pills">
        <button 
          class="pill-btn" 
          class:active={selectedCategory === "all"}
          onclick={() => selectedCategory = "all"}
        >
          {t(lang, "common.all")}
        </button>
        {#each categories as cat}
          <button 
            class="pill-btn" 
            class:active={selectedCategory === String(cat.id)}
            onclick={() => selectedCategory = String(cat.id)}
          >
            {cat.name}
          </button>
        {/each}
      </div>
    {/if}
  </div>

  <!-- Product Grid -->
  {#if filteredProducts.length > 0}
    <div class="products-grid">
      {#each filteredProducts as product}
        <div class="product-card">
          <!-- Thumbnail -->
          <div class="product-thumbnail">
            {#if product.category}
              <span class="category-tag">{product.category}</span>
            {/if}
            {#if product.image_url}
              <img src={optimizeImageUrl(product.image_url, 400, 300)} alt={product.name} />
            {:else}
              <div class="thumbnail-placeholder" style="background: {getPlaceholderBackground(product.id)}">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
                </svg>
              </div>
            {/if}
          </div>

          <!-- Info -->
          <div class="product-info">
            <h3 class="product-title">{product.name}</h3>
            
            {#if product.description}
              <div class="description-wrapper">
                <p class="product-desc">
                  {getProductSummary(product.description)}
                </p>
              </div>
            {/if}

            <div class="product-footer">
              <span class="product-price">{formatPrice(product.price_cents)}</span>
              <a href="/product/{product.slug}" class="btn btn-primary btn-view">
                <span>{t(lang, "products.view_details")}</span>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                  <line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/>
                </svg>
              </a>
            </div>
          </div>
        </div>
      {/each}
    </div>
  {:else}
    <div class="empty-state">
      <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <circle cx="12" cy="12" r="10"/><line x1="8" y1="12" x2="16" y2="12"/>
      </svg>
      <h3>{t(lang, "products.empty_title")}</h3>
      <p>{t(lang, "products.empty_body")}</p>
    </div>
  {/if}
</div>

<style>
  .vitrine-container {
    max-width: 1200px;
    margin: 2rem auto;
    padding: 0 1.5rem;
  }

  .vitrine-header {
    text-align: center;
    margin-bottom: 3rem;
  }

  .vitrine-header h1 {
    font-size: 2.25rem;
    font-weight: 800;
    color: var(--text-primary);
    margin-bottom: 0.5rem;
  }

  .vitrine-header p {
    color: var(--text-muted);
    font-size: 1.1rem;
    margin-bottom: 2rem;
  }

  .filter-bar {
    max-width: 500px;
    margin: 0 auto 1.5rem auto;
  }

  .search-wrapper {
    position: relative;
    display: flex;
    align-items: center;
    background: var(--bg-primary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-lg);
    padding: 0.25rem 0.75rem;
    box-shadow: var(--shadow-sm);
  }

  .search-wrapper svg {
    color: var(--text-muted);
    margin-right: 0.5rem;
  }

  .search-wrapper input {
    width: 100%;
    border: none;
    background: transparent;
    padding: 0.75rem 0;
    font-size: 0.95rem;
    color: var(--text-primary);
  }

  .search-wrapper input:focus {
    outline: none;
  }

  .category-pills {
    display: flex;
    justify-content: center;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-top: 1rem;
  }

  .pill-btn {
    background: var(--bg-primary);
    border: 1px solid var(--border-color);
    color: var(--text-secondary);
    padding: 0.5rem 1.25rem;
    border-radius: 9999px;
    font-size: 0.875rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .pill-btn:hover {
    border-color: var(--accent-color, #3b82f6);
    color: var(--accent-color, #3b82f6);
  }

  .pill-btn.active {
    background: var(--accent-color, #3b82f6);
    border-color: var(--accent-color, #3b82f6);
    color: #ffffff;
  }

  /* Grid */
  .products-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
    gap: 2rem;
  }

  .product-card {
    background: var(--bg-primary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-xl);
    overflow: hidden;
    display: flex;
    flex-direction: column;
    box-shadow: var(--shadow-md);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
  }

  .product-card:hover {
    transform: translateY(-4px);
    box-shadow: var(--shadow-lg);
    border-color: var(--accent-color, #3b82f6);
  }

  .product-thumbnail {
    position: relative;
    width: 100%;
    height: 200px;
    overflow: hidden;
  }

  .product-thumbnail img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }

  .thumbnail-placeholder {
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #ffffff;
  }

  .category-tag {
    position: absolute;
    top: 1rem;
    left: 1rem;
    background: rgba(15, 23, 42, 0.75);
    backdrop-filter: blur(4px);
    color: #ffffff;
    padding: 0.25rem 0.75rem;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    z-index: 2;
  }

  .product-info {
    padding: 1.5rem;
    display: flex;
    flex-direction: column;
    flex-grow: 1;
  }

  .product-title {
    font-size: 1.15rem;
    font-weight: 700;
    color: var(--text-primary);
    margin: 0 0 0.75rem 0;
    line-height: 1.4;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  .description-wrapper {
    display: flex;
    flex-direction: column;
    margin-bottom: 1.5rem;
  }

  .product-desc {
    font-size: 0.875rem;
    color: var(--text-secondary);
    line-height: 1.5;
    margin: 0;
    white-space: normal;
    display: -webkit-box;
    -webkit-line-clamp: 4;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  .product-desc.expanded {
    display: block;
    -webkit-line-clamp: unset;
    overflow: visible;
  }

  .toggle-desc-btn {
    background: transparent;
    border: none;
    color: var(--accent-color, #3b82f6);
    font-size: 0.8rem;
    font-weight: 700;
    cursor: pointer;
    padding: 0;
    margin-top: 0.5rem;
    align-self: flex-start;
  }

  .toggle-desc-btn:hover {
    text-decoration: underline;
  }

  .product-footer {
    margin-top: auto;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding-top: 1.25rem;
    border-top: 1px solid var(--border-color);
  }

  .product-price {
    font-size: 1.2rem;
    font-weight: 800;
    color: var(--text-primary);
  }

  .btn-view {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    font-size: 0.85rem;
    font-weight: 700;
    padding: 0.5rem 1rem;
    border-radius: var(--radius-md);
    background: var(--accent-color, #3b82f6);
    color: #ffffff;
    text-decoration: none;
    transition: all 0.2s ease;
  }

  .btn-view:hover {
    background: var(--accent-hover, #2563eb);
    transform: translateX(2px);
  }

  .empty-state {
    text-align: center;
    padding: 5rem 1.5rem;
    background: var(--bg-primary);
    border: 1px dashed var(--border-color);
    border-radius: var(--radius-xl);
    color: var(--text-muted);
  }

  .empty-state svg {
    margin-bottom: 1rem;
    color: var(--text-muted);
    opacity: 0.5;
  }

  .empty-state h3 {
    font-size: 1.25rem;
    font-weight: 700;
    color: var(--text-primary);
    margin: 0 0 0.5rem 0;
  }

  .empty-state p {
    margin: 0;
    font-size: 0.95rem;
  }
</style>
