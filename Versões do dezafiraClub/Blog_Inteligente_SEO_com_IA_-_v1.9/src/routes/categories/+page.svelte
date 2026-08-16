<script lang="ts">
  import { CategoryBadge, Skeleton, Breadcrumb } from '$lib/components';
  import { page } from '$app/stores';
  import { t, formatDate } from '$lib/i18n';
  
  let { data } = $props();
  const lang = $derived($page.data.language || 'pt');
  
  let categories = $derived(data.categories || []);
  
  // Estatísticas
  let totalPosts = $derived(categories.reduce((acc: number, cat: any) => acc + (cat.post_count || 0), 0));
  
  // Cores para categorias sem cor definida
  const categoryColors = [
    '#4a90d9', '#10b981', '#f59e0b', '#ef4444',
    '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16'
  ];
  
  function getCategoryColor(name: string): string {
    let hash = 0;
    for (let i = 0; i < name.length; i++) {
      hash = name.charCodeAt(i) + ((hash << 5) - hash);
    }
    return categoryColors[Math.abs(hash) % categoryColors.length];
  }
</script>

<svelte:head>
  <title>{data.settings?.site_title || "Blog"} | {t(lang, 'categories.title')}</title>
  <meta name="description" content={t(lang, 'categories.explore', { count: categories.length, posts: totalPosts })} />
</svelte:head>

<div class="categories-page">
  <div class="container">
    <!-- Header -->
    <header class="page-header">
      <Breadcrumb items={[
        { label: t(lang, 'categories.title'), icon: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z"/></svg>' }
      ]} />
      
      <h1 class="page-title">{t(lang, 'categories.title')}</h1>
      <p class="page-subtitle">
        {t(lang, 'categories.explore', { count: categories.length, posts: totalPosts })}
      </p>
    </header>

    {#if categories.length === 0}
      <!-- Empty State -->
      <div class="empty-state">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z"/>
          <line x1="12" y1="11" x2="12" y2="17"/>
          <line x1="9" y1="14" x2="15" y2="14"/>
        </svg>
        <h3>{t(lang, 'categories.empty_title')}</h3>
        <p>{t(lang, 'categories.empty_body')}</p>
      </div>
    {:else}
      <!-- Grid de Categorias -->
      <div class="categories-grid">
        {#each categories as category}
          <a href="/category/{category.slug}" class="category-card">
            <div 
              class="category-icon"
              style="background: {getCategoryColor(category.name)}15; color: {getCategoryColor(category.name)}"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z"/>
              </svg>
            </div>
            
            <div class="category-content">
              <h3 class="category-name">{category.name}</h3>
              
              {#if category.description}
                <p class="category-description">{category.description}</p>
              {/if}
              
              <div class="category-meta">
                <span class="post-count">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
                    <polyline points="14,2 14,8 20,8"/>
                    <line x1="16" y1="13" x2="8" y2="13"/>
                    <line x1="16" y1="17" x2="8" y2="17"/>
                  </svg>
                  {t(lang, 'categories.posts_count', { n: category.post_count || 0 })}
                </span>
                
                {#if category.updated_at}
                  <span class="last-update">
                    {t(lang, 'categories.updated', { date: formatDate(lang, category.updated_at) })}
                  </span>
                {/if}
              </div>
            </div>
            
            <div class="category-arrow">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="9,18 15,12 9,6"/>
              </svg>
            </div>
          </a>
        {/each}
      </div>

      <!-- Tags Cloud (categorias menores) -->
      {#if categories.length > 8}
        <section class="tags-cloud">
          <h2 class="section-title">Todas as Tags</h2>
          <div class="tags-list">
            {#each categories as category}
              <CategoryBadge 
                name={category.name}
                slug={category.slug}
                count={category.post_count}
                size="md"
              />
            {/each}
          </div>
        </section>
      {/if}
    {/if}
  </div>
</div>
<style>
  .categories-page {
    min-height: 100vh;
    padding: 40px 0 80px;
    background-color: var(--bg-secondary);
  }

  .container {
    max-width: 1000px;
    margin: 0 auto;
    padding: 0 20px;
  }

  /* Header */
  .page-header {
    text-align: center;
    margin-bottom: 48px;
    animation: fadeIn 0.8s ease-out;
  }

  .page-title {
    font-size: clamp(2rem, 5vw, 3rem);
    font-weight: 800;
    color: var(--text-primary);
    margin: 16px 0 8px;
    letter-spacing: -0.02em;
  }

  .page-subtitle {
    font-size: 1.1rem;
    color: var(--text-secondary);
    margin: 0;
    opacity: 0.8;
  }

  /* Empty State */
  .empty-state {
    text-align: center;
    padding: 60px 20px;
    background: var(--bg-primary);
    border: 1px solid var(--border-light);
    border-radius: 24px;
    box-shadow: var(--shadow-sm);
  }

  .empty-state svg {
    width: 64px;
    height: 64px;
    color: var(--text-muted);
    margin-bottom: 16px;
    opacity: 0.5;
  }

  .empty-state h3 {
    font-size: 20px;
    color: var(--text-primary);
    margin: 0 0 8px;
  }

  .empty-state p {
    font-size: 14px;
    color: var(--text-muted);
    margin: 0;
  }

  /* Categories Grid */
  .categories-grid {
    display: grid;
    gap: 1.25rem;
  }

  .category-card {
    display: flex;
    align-items: center;
    gap: 24px;
    padding: 24px;
    background: var(--bg-primary);
    border: 1px solid var(--border-light);
    border-radius: 20px;
    text-decoration: none;
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: var(--shadow-sm);
  }

  .category-card:hover {
    border-color: var(--text-primary);
    box-shadow: var(--shadow-lg);
    transform: translateY(-4px) scale(1.01);
  }

  .category-icon {
    width: 64px;
    height: 64px;
    border-radius: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    transition: transform 0.3s ease;
  }

  .category-card:hover .category-icon {
    transform: rotate(-5deg) scale(1.1);
  }

  .category-icon svg {
    width: 32px;
    height: 32px;
  }

  .category-content {
    flex: 1;
    min-width: 0;
  }

  .category-name {
    font-size: 1.25rem;
    font-weight: 700;
    color: var(--text-primary);
    margin: 0 0 6px;
    transition: color 0.2s ease;
  }

  .category-description {
    font-size: 0.95rem;
    color: var(--text-secondary);
    margin: 0 0 12px;
    line-height: 1.5;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
    opacity: 0.9;
  }

  .category-meta {
    display: flex;
    align-items: center;
    gap: 20px;
    font-size: 0.8rem;
    font-weight: 600;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .post-count {
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .post-count svg {
    width: 14px;
    height: 14px;
  }

  .category-arrow {
    color: var(--text-muted);
    opacity: 0.3;
    transition: all 0.3s ease;
  }

  .category-card:hover .category-arrow {
    color: var(--text-primary);
    opacity: 1;
    transform: translateX(6px);
  }

  .category-arrow svg {
    width: 24px;
    height: 24px;
  }

  /* Tags Cloud */
  .tags-cloud {
    margin-top: 80px;
    padding-top: 48px;
    border-top: 1px solid var(--border-light);
    animation: slideUp 0.8s ease-out backwards;
    animation-delay: 0.4s;
  }

  .section-title {
    font-size: 1.25rem;
    font-weight: 800;
    color: var(--text-primary);
    margin: 0 0 32px;
    text-align: center;
    text-transform: uppercase;
    letter-spacing: 1px;
  }

  .tags-list {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 12px;
  }

  /* Responsive */
  @media (max-width: 768px) {
    .page-header {
      margin-bottom: 32px;
    }

    .category-card {
      padding: 20px;
      gap: 16px;
      border-radius: 16px;
    }

    .category-icon {
      width: 52px;
      height: 52px;
      border-radius: 12px;
    }

    .category-icon svg {
      width: 24px;
      height: 24px;
    }

    .category-name {
      font-size: 1.1rem;
    }

    .category-description {
      -webkit-line-clamp: 1;
      font-size: 0.85rem;
    }

    .category-meta {
      gap: 12px;
      font-size: 0.75rem;
    }

    .category-arrow {
      display: none;
    }
  }
</style>
le>