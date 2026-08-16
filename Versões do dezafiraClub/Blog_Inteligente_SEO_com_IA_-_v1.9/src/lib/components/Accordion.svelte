<script lang="ts">
  interface AccordionItem {
    id: string;
    title: string;
    content: any;
    disabled?: boolean;
    open?: boolean;
  }

  let { 
    items = [] as AccordionItem[],
    allowMultiple = true,
    variant = 'default' as 'default' | 'bordered' | 'separated',
    animationDuration = 300
  } = $props();

  let openItems = $state<Set<string>>(new Set());
  
  $effect(() => {
    openItems = new Set(items.filter(i => i.open).map(i => i.id));
  });

  function isOpen(id: string): boolean {
    return openItems.has(id);
  }

  function toggle(id: string) {
    if (openItems.has(id)) {
      openItems.delete(id);
    } else {
      if (!allowMultiple) {
        openItems.clear();
      }
      openItems.add(id);
    }
    openItems = new Set(openItems); // trigger reactivity
  }

  function getItemHeight(node: HTMLElement): number {
    return node.scrollHeight;
  }
</script>

<div class="accordion variant-{variant}">
  {#each items as item, index}
    <div 
      class="accordion-item"
      class:open={isOpen(item.id)}
      class:disabled={item.disabled}
    >
      <button
        type="button"
        class="accordion-header"
        onclick={() => !item.disabled && toggle(item.id)}
        disabled={item.disabled}
        aria-expanded={isOpen(item.id)}
        aria-controls={`accordion-content-${item.id}`}
        id={`accordion-header-${item.id}`}
      >
        <span class="accordion-title">{item.title}</span>
        
        <svg 
          class="accordion-icon" 
          viewBox="0 0 20 20" 
          fill="currentColor"
          style="--duration: {animationDuration}ms"
        >
          <path 
            fill-rule="evenodd" 
            d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" 
            clip-rule="evenodd"
          />
        </svg>
      </button>

      <div
        id={`accordion-content-${item.id}`}
        role="region"
        aria-labelledby={`accordion-header-${item.id}`}
        class="accordion-content"
        hidden={!isOpen(item.id)}
      >
        <div class="accordion-body">
          {@html item.content}
        </div>
      </div>
    </div>
  {/each}
</div>

<style>
  .accordion {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .accordion-item {
    border-radius: 8px;
    overflow: hidden;
    transition: box-shadow 0.2s;
  }

  .accordion-item.open {
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  }

  .accordion-item.disabled {
    opacity: 0.6;
  }

  /* Variants */
  .variant-default {
    background: white;
    border: 1px solid #e5e7eb;
  }

  .variant-bordered .accordion-item {
    border: 1px solid #e5e7eb;
    background: white;
  }

  .variant-separated .accordion-item {
    background: white;
  }

  .variant-separated .accordion-item.open {
    border-color: #4a90d9;
  }

  /* Header */
  .accordion-header {
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px 20px;
    background: none;
    border: none;
    cursor: pointer;
    font-size: 15px;
    font-weight: 500;
    color: #374151;
    text-align: left;
    transition: background 0.2s, color 0.2s;
  }

  .accordion-header:not(:disabled):hover {
    background: #f9fafb;
  }

  .accordion-header:disabled {
    cursor: not-allowed;
    color: #9ca3af;
  }

  .accordion-item.open .accordion-header {
    color: #4a90d9;
  }

  .accordion-title {
    flex: 1;
    padding-right: 16px;
  }

  .accordion-icon {
    width: 20px;
    height: 20px;
    flex-shrink: 0;
    color: #9ca3af;
    transition: transform var(--duration, 300ms) ease;
  }

  .accordion-item.open .accordion-icon {
    transform: rotate(180deg);
    color: #4a90d9;
  }

  /* Content */
  .accordion-content {
    overflow: hidden;
    animation: slideDown 0.3s ease;
  }

  @keyframes slideDown {
    from {
      opacity: 0;
      transform: translateY(-8px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  .accordion-body {
    padding: 0 20px 20px;
    font-size: 14px;
    line-height: 1.6;
    color: #6b7280;
  }

  /* Responsive */
  @media (max-width: 640px) {
    .accordion-header {
      padding: 14px 16px;
    }

    .accordion-body {
      padding: 0 16px 16px;
    }
  }
</style>