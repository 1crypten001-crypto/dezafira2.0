<script lang="ts">
  let { 
    name = '',
    slug = '',
    href = '',
    size = 'md',
    color = '',
    count
  } = $props();
  
  // Gerar cor baseada no nome se não especificada
  const colors = [
    '#4a90d9', '#10b981', '#f59e0b', '#ef4444', 
    '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16'
  ];
  
  function getColor(name: string): string {
    if (color) return color;
    let hash = 0;
    for (let i = 0; i < name.length; i++) {
      hash = name.charCodeAt(i) + ((hash << 5) - hash);
    }
    return colors[Math.abs(hash) % colors.length];
  }
  
  const badgeColor = $derived(getColor(name || slug));
  const computedHref = $derived(href || `/category/${slug}`);
</script>

<a href={computedHref} class="category-badge size-{size}" style="--badge-color: {badgeColor}">
  <span class="badge-icon">
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z"/>
    </svg>
  </span>
  
  <span class="badge-text">{name || slug}</span>
  
  {#if count !== undefined}
    <span class="badge-count">{count}</span>
  {/if}
</a>

<style>
  .category-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: color-mix(in srgb, var(--badge-color) 10%, transparent);
    color: var(--badge-color);
    border: 1px solid color-mix(in srgb, var(--badge-color) 20%, transparent);
    border-radius: 20px;
    text-decoration: none;
    font-weight: 500;
    transition: all 0.2s;
  }

  .category-badge:hover {
    background: color-mix(in srgb, var(--badge-color) 20%, transparent);
    transform: translateY(-1px);
  }

  /* Sizes */
  .size-sm {
    padding: 2px 10px;
    font-size: 11px;
  }

  .size-md {
    padding: 4px 12px;
    font-size: 12px;
  }

  .size-lg {
    padding: 6px 16px;
    font-size: 14px;
  }

  .badge-icon {
    display: flex;
    align-items: center;
    opacity: 0.7;
  }

  .badge-text {
    line-height: 1;
  }

  .badge-count {
    background: var(--badge-color);
    color: white;
    padding: 0 6px;
    border-radius: 10px;
    font-size: 10px;
    font-weight: 600;
  }

  .size-sm .badge-count {
    padding: 0 4px;
    font-size: 9px;
  }

  .size-lg .badge-count {
    padding: 0 8px;
    font-size: 12px;
  }
</style>
