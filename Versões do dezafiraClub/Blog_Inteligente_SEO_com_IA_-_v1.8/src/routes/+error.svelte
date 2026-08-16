<script lang="ts">
  import { page } from '$app/stores';
  import AdRenderer from '$lib/components/AdRenderer.svelte';
  import { optimizeImageUrl } from '$lib/image-optimizer';
  import { t } from '$lib/i18n';

  let { data } = $props();
  const lang = $derived($page.data.language || 'pt');

  function getPostImage(post: any) {
    if (post.cover_image) return post.cover_image;
    const match = post.content?.match(/<img[^>]+src="([^">]+)"/);
    if (match) return match[1];
    return null;
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

<div class="error-page" class:has-recommendations={$page.status === 404}>
  <div class="error-container">
    <div class="error-content">
      <div class="error-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
        </svg>
      </div>
      
      <h1 class="error-code">{$page.status}</h1>
      <h2 class="error-title">
        {#if $page.status === 404}
          {t(lang, 'error.not_found')}
        {:else if $page.status === 500}
          {t(lang, 'error.server')}
        {:else}
          {t(lang, 'error.generic')}
        {/if}
      </h2>
      
      <p class="error-message">
        {#if $page.status === 404}
          {t(lang, 'error.not_found_body')}
        {:else}
          {$page.error?.message || t(lang, 'error.generic_body')}
        {/if}
      </p>
      
      <div class="error-actions">
        <a href="/" class="btn btn-primary">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/>
            <polyline points="9,22 9,12 15,12 15,22"/>
          </svg>
          {t(lang, 'common.back_home')}
        </a>
        
        <button onclick={() => history.back()} class="btn btn-secondary">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="19" y1="12" x2="5" y2="12"/>
            <polyline points="12,19 5,12 12,5"/>
          </svg>
          {t(lang, 'common.back')}
        </button>
      </div>
    </div>

    {#if $page.status === 404}
      <!-- Anúncio em Destaque no 404 (Aproveitando tráfego perdido) -->
      {#if data?.sidebarAds && data.sidebarAds.length > 0}
        <div class="error-ad-wrapper">
          <AdRenderer ads={data.sidebarAds} placement="sidebar" />
        </div>
      {/if}

      <!-- Sugestões de Posts -->
      {#if data?.popularPosts && data.popularPosts.length > 0}
        <div class="suggested-posts-section">
          <h3 class="suggested-title">{t(lang, 'error.recommended')}</h3>
          <div class="posts-grid">
            {#each data.popularPosts.slice(0, 3) as post}
               <a href="/post/{post.slug}" class="post-card">
                {#if !hasNoImage(post)}
                  <div class="post-card-image">
                    <img src={optimizeImageUrl(getPostImage(post), 400)} alt={post.title} loading="lazy" />
                  </div>
                {:else}
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
                {/if}
                <div class="post-card-content">
                  <h4>{post.title}</h4>
                  {#if post.excerpt}
                    <p>{post.excerpt.slice(0, 80)}...</p>
                  {/if}
                </div>
              </a>
            {/each}
          </div>
        </div>
      {/if}
    {/if}
  </div>
</div>

<style>
  .error-page {
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 40px 20px;
    background: linear-gradient(180deg, #f9fafb 0%, white 100%);
    box-sizing: border-box;
  }

  .error-page.has-recommendations {
    align-items: flex-start;
    padding: 80px 20px;
  }

  .error-container {
    width: 100%;
    max-width: 800px;
    display: flex;
    flex-direction: column;
    align-items: center;
  }

  .error-content {
    text-align: center;
    max-width: 500px;
    width: 100%;
  }

  .error-icon {
    margin-bottom: 16px;
  }

  .error-icon svg {
    width: 72px;
    height: 72px;
    color: #d1d5db;
  }

  .error-code {
    font-size: 100px;
    font-weight: 800;
    color: #4a90d9;
    margin: 0;
    line-height: 1;
    text-shadow: 0 4px 20px rgba(74, 144, 217, 0.2);
  }

  .error-title {
    font-size: 24px;
    font-weight: 700;
    color: #1f2937;
    margin: 12px 0;
  }

  .error-message {
    font-size: 15px;
    color: #6b7280;
    margin: 0 0 24px;
    line-height: 1.6;
  }

  .error-actions {
    display: flex;
    justify-content: center;
    gap: 16px;
    margin-bottom: 24px;
  }

  .btn {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 10px 20px;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 500;
    text-decoration: none;
    cursor: pointer;
    border: none;
    transition: all 0.2s;
  }

  .btn svg {
    width: 16px;
    height: 16px;
  }

  .btn-primary {
    background: #4a90d9;
    color: white;
  }

  .btn-primary:hover {
    background: #3a7bc8;
    transform: translateY(-2px);
  }

  .btn-secondary {
    background: white;
    color: #6b7280;
    border: 1px solid #e5e7eb;
  }

  .btn-secondary:hover {
    background: #f9fafb;
  }

  /* Centralized Larger Ad Wrapper */
  .error-ad-wrapper {
    margin: 2rem auto;
    max-width: 460px;
    width: 100%;
    display: flex;
    justify-content: center;
    box-sizing: border-box;
  }

  .error-ad-wrapper :global(.ad-container) {
    width: 100% !important;
    max-width: 100% !important;
    margin: 0 !important;
  }

  /* Suggested Posts */
  .suggested-posts-section {
    width: 100%;
    margin-top: 3rem;
    padding-top: 2.5rem;
    border-top: 1px solid var(--border-light, #e5e7eb);
  }

  .suggested-title {
    font-family: var(--font-sans), sans-serif;
    font-size: 1.25rem;
    font-weight: 700;
    color: var(--text-primary, #1f2937);
    margin-bottom: 1.5rem;
    text-align: center;
  }

  .posts-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1.5rem;
    width: 100%;
  }

  .post-card {
    background: var(--bg-primary, #ffffff);
    border: 1px solid var(--border-color, #e5e7eb);
    border-radius: 12px;
    overflow: hidden;
    text-decoration: none;
    color: inherit;
    display: flex;
    flex-direction: column;
    transition: transform 0.2s, box-shadow 0.2s, border-color 0.2s;
  }

  .post-card:hover {
    transform: translateY(-4px);
    box-shadow: var(--shadow-md, 0 4px 6px -1px rgba(0, 0, 0, 0.1));
    border-color: var(--text-muted, #9ca3af);
  }

  .post-card-image {
    aspect-ratio: 16/9;
    overflow: hidden;
    background: var(--bg-secondary, #f3f4f6);
  }

  .post-card-image img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }

  .placeholder-image {
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 2rem;
  }

  .post-card-content {
    padding: 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    flex-grow: 1;
  }

  .post-card-content h4 {
    margin: 0;
    font-family: var(--font-sans), sans-serif;
    font-size: 0.95rem;
    font-weight: 600;
    line-height: 1.4;
    color: var(--text-primary, #1f2937);
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  .post-card-content p {
    margin: 0;
    font-size: 0.8rem;
    color: var(--text-muted, #6b7280);
    line-height: 1.5;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  @media (max-width: 768px) {
    .posts-grid {
      grid-template-columns: 1fr;
      gap: 1rem;
    }

    .error-page.has-recommendations {
      padding: 40px 20px;
    }

    .error-actions {
      flex-direction: column;
      gap: 10px;
    }

    .btn {
      width: 100%;
      justify-content: center;
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
    font-weight: 700;
    color: #1f2937;
    font-size: 0.9rem;
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
    top: 1rem;
    right: 1rem;
    color: rgba(17, 24, 39, 0.12);
    z-index: 1;
  }
</style>
