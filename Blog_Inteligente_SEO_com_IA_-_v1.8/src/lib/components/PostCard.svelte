<script lang="ts">
  import { page } from '$app/stores';
  import { t, formatDate as fmtDate } from '$lib/i18n';

  let {
    variant = 'default',
    title = '',
    excerpt = '',
    image = '',
    category = '',
    date = '',
    href = '#',
    loading = false,
    isPremium = false
  } = $props();

  const lang = $derived($page.data.language || 'pt');

  function formatDate(dateStr: string) {
    if (!dateStr) return '';
    return fmtDate(lang, dateStr, { day: 'numeric', month: 'short', year: 'numeric' }).replace('.', '');
  }
</script>

{#if loading}
  <article class="post-card {variant} loading">
    {#if variant !== 'compact'}
      <div class="post-image skeleton-card-image"></div>
    {/if}
    <div class="post-content">
      <div class="skeleton-title"></div>
      <div class="skeleton-excerpt">
        <div class="skeleton-line"></div>
        <div class="skeleton-line short"></div>
      </div>
      <div class="skeleton-meta"></div>
    </div>
  </article>
{:else}
  <article class="post-card {variant}">
    {#if variant !== 'compact' && image}
      <a href={href} class="post-image-wrapper">
        <img src={image} alt={title} class="post-image" loading="lazy" />
        {#if isPremium}
          <span class="premium-badge">⭐ {t(lang, 'common.premium')}</span>
        {/if}
      </a>
    {/if}

    <div class="post-content">
      {#if category}
        <span class="post-category">{category}</span>
      {/if}

      <h3 class="post-title">
        <a href={href}>{title}</a>
      </h3>

      {#if excerpt && variant !== 'compact'}
        <p class="post-excerpt">{excerpt}</p>
      {/if}

      <div class="post-meta">
        {#if date}
          <span class="post-date">{formatDate(date)}</span>
        {/if}
        <a href={href} class="read-more">
          {t(lang, 'common.read_more')}
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M5 12h14M12 5l7 7-7 7"/>
          </svg>
        </a>
      </div>
    </div>
  </article>
{/if}

<style>
  .post-card {
    display: flex;
    flex-direction: column;
    background: white;
    border-radius: 12px;
    overflow: hidden;
    transition: transform 0.2s, box-shadow 0.2s;
  }

  .post-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 24px rgba(0, 0, 0, 0.1);
  }

  /* Variants */
  .post-card.featured {
    flex-direction: row;
  }

  .post-card.compact {
    flex-direction: row;
    gap: 12px;
    padding: 12px;
    background: transparent;
    border: 1px solid #e5e7eb;
  }

  .post-card.horizontal {
    flex-direction: row;
  }

  /* Image */
  .post-image-wrapper {
    position: relative;
    display: block;
    overflow: hidden;
  }

  .post-image {
    width: 100%;
    height: 200px;
    object-fit: cover;
    transition: transform 0.3s;
  }

  .post-card:hover .post-image {
    transform: scale(1.05);
  }

  .post-card.featured .post-image {
    height: 100%;
    min-height: 300px;
  }

  .premium-badge {
    position: absolute;
    top: 12px;
    right: 12px;
    background: linear-gradient(135deg, #fbbf24, #f59e0b);
    color: #1f2937;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
  }

  /* Content */
  .post-content {
    padding: 20px;
    display: flex;
    flex-direction: column;
    flex: 1;
  }

  .post-card.compact .post-content {
    padding: 0;
  }

  .post-category {
    font-size: 12px;
    font-weight: 600;
    text-transform: uppercase;
    color: #4a90d9;
    letter-spacing: 0.5px;
    margin-bottom: 8px;
  }

  .post-title {
    font-size: 20px;
    font-weight: 700;
    margin: 0 0 8px 0;
    line-height: 1.3;
  }

  .post-card.compact .post-title {
    font-size: 16px;
    margin-bottom: 4px;
  }

  .post-title a {
    color: #1f2937;
    text-decoration: none;
    transition: color 0.2s;
  }

  .post-title a:hover {
    color: #4a90d9;
  }

  .post-excerpt {
    color: #6b7280;
    font-size: 14px;
    line-height: 1.6;
    margin: 0 0 16px 0;
    flex: 1;
  }

  .post-card.compact .post-excerpt {
    display: none;
  }

  .post-meta {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: auto;
  }

  .post-date {
    font-size: 12px;
    color: #9ca3af;
  }

  .read-more {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-size: 14px;
    font-weight: 500;
    color: #4a90d9;
    text-decoration: none;
    transition: gap 0.2s;
  }

  .read-more:hover {
    gap: 8px;
  }

  .read-more svg {
    transition: transform 0.2s;
  }

  .read-more:hover svg {
    transform: translateX(4px);
  }

  /* Skeleton Loading */
  .post-card.loading {
    pointer-events: none;
  }

  .skeleton-card-image {
    height: 200px;
    background: linear-gradient(90deg, #f0f0f0 25%, #e8e8e8 50%, #f0f0f0 75%);
    background-size: 200% 100%;
    animation: shimmer 1.5s infinite;
  }

  .skeleton-title {
    height: 28px;
    width: 80%;
    background: linear-gradient(90deg, #f0f0f0 25%, #e8e8e8 50%, #f0f0f0 75%);
    background-size: 200% 100%;
    animation: shimmer 1.5s infinite;
    border-radius: 4px;
    margin-bottom: 8px;
  }

  .skeleton-excerpt {
    display: flex;
    flex-direction: column;
    gap: 8px;
    margin-bottom: 16px;
  }

  .skeleton-line {
    height: 16px;
    background: linear-gradient(90deg, #f0f0f0 25%, #e8e8e8 50%, #f0f0f0 75%);
    background-size: 200% 100%;
    animation: shimmer 1.5s infinite;
    border-radius: 4px;
  }

  .skeleton-line.short {
    width: 60%;
  }

  .skeleton-meta {
    height: 20px;
    width: 40%;
    background: linear-gradient(90deg, #f0f0f0 25%, #e8e8e8 50%, #f0f0f0 75%);
    background-size: 200% 100%;
    animation: shimmer 1.5s infinite;
    border-radius: 4px;
  }

  @keyframes shimmer {
    0% { background-position: 200% 0; }
    100% { background-position: -200% 0; }
  }

  /* Responsive */
  @media (max-width: 768px) {
    .post-card.featured {
      flex-direction: column;
    }

    .post-card.featured .post-image {
      min-height: 200px;
    }
  }
</style>