<script lang="ts">
  import type { Snippet } from 'svelte';

  interface Tab {
    id: string;
    label: string;
    disabled?: boolean;
  }

  let {
    tabs = [],
    activeTab = '',
    variant = 'underline',
    size = 'md',
    fullWidth = false,
    onChange = () => {},
    children
  }: {
    tabs?: Tab[];
    activeTab?: string;
    variant?: 'underline' | 'pills' | 'bordered';
    size?: 'sm' | 'md' | 'lg';
    fullWidth?: boolean;
    onChange?: (tabId: string) => void;
    children?: Snippet<[string]>;
  } = $props();

  function selectTab(tabId: string) {
    if (!tabs.find(t => t.id === tabId)?.disabled) {
      activeTab = tabId;
      onChange(tabId);
    }
  }

  $effect(() => {
    if (!activeTab && tabs.length > 0) {
      activeTab = tabs[0].id;
    }
  });
</script>

<div class="tabs variant-{variant} size-{size}" class:full-width={fullWidth}>
  <div class="tabs-list" role="tablist">
    {#each tabs as tab}
      <button
        role="tab"
        class="tab-btn"
        class:active={activeTab === tab.id}
        class:disabled={tab.disabled}
        disabled={tab.disabled}
        aria-selected={activeTab === tab.id}
        aria-controls={`panel-${tab.id}`}
        id={`tab-${tab.id}`}
        onclick={() => selectTab(tab.id)}
      >
        {#if tab.id === 'overview'}
          <svg viewBox="0 0 20 20" fill="currentColor" width="16" height="16">
            <path d="M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4zM3 10a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H4a1 1 0 01-1-1v-6zM14 9a1 1 0 00-1 1v6a1 1 0 001 1h2a1 1 0 001-1v-6a1 1 0 00-1-1h-2z"/>
          </svg>
        {/if}
        <span>{tab.label}</span>

        {#if tab.disabled}
          <svg class="lock-icon" viewBox="0 0 20 20" fill="currentColor" width="14" height="14">
            <path fill-rule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clip-rule="evenodd"/>
          </svg>
        {/if}
      </button>
    {/each}
  </div>

  <div class="tabs-panels">
    {#if children}
      {@render children(activeTab)}
    {/if}
  </div>
</div>

<style>
  .tabs {
    width: 100%;
  }

  .tabs-list {
    display: flex;
    gap: 0;
    overflow-x: auto;
    scrollbar-width: none;
  }

  .tabs-list::-webkit-scrollbar {
    display: none;
  }

  .full-width .tabs-list {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
  }

  .tab-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    padding: 10px 20px;
    background: none;
    border: none;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    white-space: nowrap;
    transition: all 0.2s;
    color: #6b7280;
    position: relative;
  }

  .tab-btn:disabled {
    cursor: not-allowed;
    opacity: 0.5;
  }

  .tab-btn:not(:disabled):hover {
    color: #374151;
  }

  .tab-btn.active {
    color: #4a90d9;
  }

  .lock-icon {
    opacity: 0.5;
  }

  .variant-underline .tab-btn::after {
    content: '';
    position: absolute;
    bottom: -1px;
    left: 0;
    right: 0;
    height: 2px;
    background: #4a90d9;
    transform: scaleX(0);
    transition: transform 0.2s;
  }

  .variant-underline .tab-btn.active::after {
    transform: scaleX(1);
  }

  .variant-pills .tab-btn {
    border-radius: 8px;
    margin: 0 4px;
  }

  .variant-pills .tab-btn.active {
    background: #eff6ff;
    color: #4a90d9;
  }

  .variant-bordered .tabs-list {
    border-bottom: 1px solid #e5e7eb;
  }

  .variant-bordered .tab-btn {
    border-bottom: 2px solid transparent;
    margin-bottom: -1px;
  }

  .variant-bordered .tab-btn.active {
    border-bottom-color: #4a90d9;
  }

  .size-sm .tab-btn {
    padding: 6px 12px;
    font-size: 12px;
  }

  .size-lg .tab-btn {
    padding: 14px 28px;
    font-size: 16px;
  }

  .tabs-panels {
    padding-top: 20px;
  }

  @keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
  }

  @media (max-width: 640px) {
    .tabs-list {
      padding: 0 4px;
    }

    .tab-btn {
      padding: 8px 12px;
      font-size: 13px;
    }
  }
</style>
