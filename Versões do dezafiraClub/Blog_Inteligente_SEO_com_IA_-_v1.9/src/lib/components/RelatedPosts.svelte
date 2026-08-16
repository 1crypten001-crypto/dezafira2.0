<script lang="ts">
  import { page } from '$app/stores';
  import { t, formatDate as fmtDate } from '$lib/i18n';

  let {
    posts = [],
    title = '',
    maxPosts = 4,
    layout = 'grid'
  } = $props();

  const lang = $derived($page.data.language || 'pt');
  const displayTitle = $derived(title || t(lang, 'post.related_title'));
  let displayPosts = $derived(posts.slice(0, maxPosts));

  function formatDate(dateString: string) {
    return fmtDate(lang, dateString, { day: 'numeric', month: 'short', year: 'numeric' }).replace('.', '');
  }
  
  function getPostImage(post: any) {
    if (post.cover_image) return post.cover_image;
    const match = post.content?.match(/<img[^>]+src="([^">]+)"/);
    if (match) return match[1];
    return `https://picsum.photos/seed/${post.id}/400/300`;
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
</script>

{#if displayPosts.length > 0}
  <section class="related-posts layout-{layout}">
    <h3 class="related-title">{displayTitle}</h3>
    
    <div class="related-grid" class:list-layout={layout === 'list'}>
      {#each displayPosts as post}
        <a href="/post/{post.slug}" class="related-card">
          <div class="related-image">
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
                src={getPostImage(post)} 
                alt={post.title}
                loading="lazy"
              />
            {/if}
          </div>
          
          <div class="related-content">
            <div class="related-meta-row">
              {#if post.category_name}
                <span class="related-category">{post.category_name}</span>
              {/if}
              {#if post.recommendationReason}
                <span class="recommendation-badge">{post.recommendationReason}</span>
              {/if}
            </div>
            
            <h4 class="related-post-title">{post.title}</h4>
            
            <span class="related-date">{formatDate(post.created_at)}</span>
          </div>
        </a>
      {/each}
    </div>
  </section>
{/if}

<style>
  .related-posts {
    margin: 40px 0;
    padding: 32px;
    background: #f9fafb;
    border-radius: 12px;
  }

  .related-title {
    font-size: 20px;
    font-weight: 700;
    color: #1f2937;
    margin: 0 0 24px 0;
    padding-bottom: 12px;
    border-bottom: 2px solid #e5e7eb;
  }

  .related-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 20px;
  }

  .related-grid.list-layout {
    grid-template-columns: 1fr;
  }

  .related-card {
    display: flex;
    flex-direction: column;
    background: white;
    border-radius: 10px;
    overflow: hidden;
    text-decoration: none;
    transition: transform 0.2s, box-shadow 0.2s;
  }

  .related-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
  }

  .related-grid.list-layout .related-card {
    flex-direction: row;
  }

  .related-image {
    width: 100%;
    height: 140px;
    overflow: hidden;
    flex-shrink: 0;
  }

  .related-grid.list-layout .related-image {
    width: 120px;
    height: 80px;
  }

  .related-image img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    transition: transform 0.3s;
  }

  .related-card:hover .related-image img {
    transform: scale(1.05);
  }

  .related-content {
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .related-grid.list-layout .related-content {
    padding: 8px 16px;
  }

  .related-meta-row {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 6px;
  }

  .related-category {
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    color: #4a90d9;
    letter-spacing: 0.5px;
  }

  .recommendation-badge {
    background: rgba(99, 102, 241, 0.08);
    color: #4f46e5;
    font-size: 10px;
    font-weight: 600;
    padding: 2px 7px;
    border-radius: 9999px;
    display: inline-flex;
    align-items: center;
    border: 1px solid rgba(99, 102, 241, 0.15);
    letter-spacing: 0.2px;
    white-space: nowrap;
  }

  .related-post-title {
    font-size: 15px;
    font-weight: 600;
    color: #1f2937;
    margin: 0;
    line-height: 1.4;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  .related-grid.list-layout .related-post-title {
    font-size: 14px;
    -webkit-line-clamp: 1;
  }

  .related-date {
    font-size: 12px;
    color: #9ca3af;
    margin-top: auto;
  }

  /* Responsive */
  @media (max-width: 640px) {
    .related-posts {
      padding: 20px;
    }

    .related-grid {
      grid-template-columns: 1fr 1fr;
    }
  }

  @media (max-width: 480px) {
    .related-grid {
      grid-template-columns: 1fr;
    }

    .related-grid.list-layout .related-card {
      flex-direction: column;
    }

    .related-grid.list-layout .related-image {
      width: 100%;
      height: 120px;
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
</style>