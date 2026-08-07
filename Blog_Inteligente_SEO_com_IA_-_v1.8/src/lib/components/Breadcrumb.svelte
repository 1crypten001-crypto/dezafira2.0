<script lang="ts">
  import { page } from '$app/stores';
  import { t } from '$lib/i18n';

  let {
    items = []
  }: {
    items: Array<{
      label: string;
      href?: string;
      icon?: string;
    }>
  } = $props();

  const lang = $derived($page.data.language || 'pt');
</script>

{#if items.length > 0}
  <nav class="breadcrumb" aria-label={t(lang, 'breadcrumb.aria')}>
    <ol class="breadcrumb-list">
      <li class="breadcrumb-item">
        <a href="/" class="breadcrumb-link">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/>
            <polyline points="9,22 9,12 15,12 15,22"/>
          </svg>
          <span class="sr-only">{t(lang, 'breadcrumb.home')}</span>
        </a>
      </li>

      {#each items as item, i}
        <li class="breadcrumb-item">
          <svg class="breadcrumb-separator" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="9,18 15,12 9,6"/>
          </svg>
          
          {#if item.href && i < items.length - 1}
            <a href={item.href} class="breadcrumb-link">
              {#if item.icon}
                <span class="breadcrumb-icon">{@html item.icon}</span>
              {/if}
              {item.label}
            </a>
          {:else}
            <span class="breadcrumb-current">
              {#if item.icon}
                <span class="breadcrumb-icon">{@html item.icon}</span>
              {/if}
              {item.label}
            </span>
          {/if}
        </li>
      {/each}
    </ol>
  </nav>
{/if}

<style>
  .breadcrumb {
    margin: 16px 0;
  }

  .breadcrumb-list {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 4px;
    list-style: none;
    padding: 0;
    margin: 0;
  }

  .breadcrumb-item {
    display: flex;
    align-items: center;
    gap: 4px;
  }

  .breadcrumb-separator {
    color: #9ca3af;
    flex-shrink: 0;
  }

  .breadcrumb-link,
  .breadcrumb-current {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: 14px;
    color: #6b7280;
    text-decoration: none;
    padding: 4px 8px;
    border-radius: 4px;
    transition: background 0.2s, color 0.2s;
  }

  .breadcrumb-link:hover {
    background: #f3f4f6;
    color: #374151;
  }

  .breadcrumb-current {
    color: #374151;
    font-weight: 500;
  }

  .breadcrumb-link svg {
    width: 16px;
    height: 16px;
  }

  .breadcrumb-icon :global(svg) {
    width: 16px;
    height: 16px;
  }

  .sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border: 0;
  }

  @media (max-width: 640px) {
    .breadcrumb-link span:not(.breadcrumb-icon),
    .breadcrumb-current span:not(.breadcrumb-icon) {
      max-width: 120px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
  }
</style>