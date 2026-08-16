<script lang="ts">
  import { page } from '$app/stores';
  import { t } from '$lib/i18n';

  let {
    currentPage = 1,
    totalPages = 1,
    maxButtons = 5,
    baseUrl = ''
  } = $props();

  const lang = $derived($page.data.language || 'pt');

  let pages = $derived(generatePages(currentPage, totalPages, maxButtons));

  function generatePages(current: number, total: number, max: number): number[] {
    if (total <= max) {
      return Array.from({ length: total }, (_, i) => i + 1);
    }

    const half = Math.floor(max / 2);
    let start = Math.max(current - half, 1);
    let end = Math.min(start + max - 1, total);

    if (end - start < max - 1) {
      start = Math.max(end - max + 1, 1);
    }

    return Array.from({ length: end - start + 1 }, (_, i) => start + i);
  }

  function getUrl(page: number): string {
    if (!baseUrl) return `?page=${page}`;
    try {
      const url = new URL(baseUrl);
      url.searchParams.set('page', page.toString());
      return url.pathname + url.search;
    } catch {
      try {
        const base = typeof window !== 'undefined' ? window.location.origin : 'http://localhost';
        const url = new URL(baseUrl, base);
        url.searchParams.set('page', page.toString());
        return url.pathname + url.search;
      } catch {
        return `?page=${page}`;
      }
    }
  }
</script>

{#if totalPages > 1}
  <nav class="pagination" aria-label={t(lang, 'pagination.aria')}>
    {#if currentPage > 1}
      <a href={getUrl(currentPage - 1)} class="pagination-btn prev" aria-label={t(lang, 'pagination.prev_page')}>
        <svg viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clip-rule="evenodd"/>
        </svg>
        <span>{t(lang, 'pagination.prev')}</span>
      </a>
    {/if}

    <div class="pagination-pages">
      {#each pages as page}
        {#if page === 1 && !pages.includes(1)}
          <a href={getUrl(1)} class="pagination-page" class:active={page === currentPage}>1</a>
          <span class="pagination-ellipsis">...</span>
        {/if}

        {#if page !== 1 && page !== totalPages}
          <a 
            href={getUrl(page)} 
            class="pagination-page"
            class:active={page === currentPage}
            class:current={page === currentPage}
          >
            {page}
          </a>
        {:else if page === totalPages && !pages.includes(totalPages)}
          <span class="pagination-ellipsis">...</span>
          <a href={getUrl(totalPages)} class="pagination-page" class:active={page === currentPage}>{totalPages}</a>
        {:else}
          <a 
            href={getUrl(page)} 
            class="pagination-page"
            class:active={page === currentPage}
          >
            {page}
          </a>
        {/if}
      {/each}
    </div>

    {#if currentPage < totalPages}
      <a href={getUrl(currentPage + 1)} class="pagination-btn next" aria-label={t(lang, 'pagination.next_page')}>
        <span>{t(lang, 'pagination.next')}</span>
        <svg viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd"/>
        </svg>
      </a>
    {/if}
  </nav>

  <div class="pagination-info">
    {t(lang, 'common.page_of', { current: currentPage, total: totalPages })}
  </div>
{/if}

<style>
  .pagination {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    margin: 3rem 0;
    flex-wrap: wrap;
  }

  .pagination-btn,
  .pagination-page {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 40px;
    height: 40px;
    padding: 0 1rem;
    border-radius: var(--radius-md, 10px);
    font-size: 0.875rem;
    font-weight: 600;
    text-decoration: none;
    transition: all var(--transition-fast, 150ms) ease;
    border: 1px solid var(--border-color);
    background: var(--bg-primary);
    color: var(--text-secondary);
    cursor: pointer;
  }

  .pagination-btn:hover,
  .pagination-page:hover {
    background: var(--bg-secondary);
    border-color: var(--text-primary);
    color: var(--text-primary);
    box-shadow: var(--shadow-xs);
  }

  .pagination-btn svg {
    width: 18px;
    height: 18px;
  }

  .pagination-pages {
    display: flex;
    align-items: center;
    gap: 0.35rem;
  }

  .pagination-page {
    padding: 0;
    width: 40px;
  }

  .pagination-page.active,
  .pagination-page.current {
    background: var(--text-primary);
    color: var(--bg-primary);
    border-color: var(--text-primary);
  }

  .pagination-ellipsis {
    padding: 0 0.5rem;
    color: var(--text-muted);
    font-size: 0.9rem;
    user-select: none;
  }

  .pagination-info {
    text-align: center;
    color: var(--text-muted);
    font-size: 0.85rem;
    margin-top: 0.5rem;
  }

  @media (max-width: 640px) {
    .pagination-btn span {
      display: none;
    }
    .pagination-btn {
      padding: 0 0.75rem;
    }
  }
</style>