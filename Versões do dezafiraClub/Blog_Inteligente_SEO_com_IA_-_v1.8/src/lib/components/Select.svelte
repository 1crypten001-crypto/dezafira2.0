<script lang="ts">
  import { onMount } from 'svelte';

  let { 
    items = [],
    groupBy = '',
    searchable = true,
    placeholder = 'Selecionar...',
    searchPlaceholder = 'Buscar...',
    allowClear = true,
    disabled = false
  } = $props();

  let open = $state(false);
  let search = $state('');
  let selectedItem = $state<any>(null);

  let filteredItems = $derived(groupBy
    ? groupItems(items, groupBy)
    : items.filter(item => matchesSearch(item)));

  let flatItems = $derived(groupBy
    ? items
    : filteredItems);

  function matchesSearch(item: any): boolean {
    if (!search) return true;
    const searchLower = search.toLowerCase();
    return item.label?.toLowerCase().includes(searchLower) ||
           item.name?.toLowerCase().includes(searchLower) ||
           item.title?.toLowerCase().includes(searchLower);
  }

  function groupItems(items: any[], key: string): any[] {
    const grouped: Record<string, any[]> = {};
    items.forEach(item => {
      const group = item[key] || 'Outros';
      if (!grouped[group]) grouped[group] = [];
      grouped[group].push(item);
    });
    return Object.entries(grouped).flatMap(([group, items]) => [
      { type: 'group', label: group },
      ...items
    ]);
  }

  function selectItem(item: any) {
    if (item.type === 'group') return;
    selectedItem = item;
    open = false;
    search = '';
    
    // Emit change
    dispatch('change', item);
  }

  function clearSelection() {
    selectedItem = null;
    dispatch('change', null);
  }

  function toggle() {
    if (!disabled) open = !open;
  }

  function handleClickOutside(event: MouseEvent) {
    const target = event.target as HTMLElement;
    if (!target.closest('.select-container')) {
      open = false;
    }
  }

  function dispatch(name: string, detail: any) {
    const event = new CustomEvent(name, { detail });
    // Simple dispatch implementation
  }

  onMount(() => {
    document.addEventListener('click', handleClickOutside);
    return () => document.removeEventListener('click', handleClickOutside);
  });
</script>

<div class="select-container" class:disabled class:open>
  <button type="button" class="select-trigger" onclick={toggle}>
    {#if selectedItem}
      <span class="select-value">
        {#if selectedItem.icon}
          {@html selectedItem.icon}
        {/if}
        {selectedItem.label || selectedItem.name || selectedItem.title}
      </span>
    {:else}
      <span class="select-placeholder">{placeholder}</span>
    {/if}
    
    <svg class="select-arrow" viewBox="0 0 20 20" fill="currentColor">
      <path fill-rule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clip-rule="evenodd"/>
    </svg>
  </button>

  {#if open}
    <div class="select-dropdown">
      {#if searchable}
        <div class="select-search">
          <svg viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clip-rule="evenodd"/>
          </svg>
          <input
            type="text"
            bind:value={search}
            placeholder={searchPlaceholder}
            class="select-search-input"
          />
        </div>
      {/if}

      <div class="select-options">
        {#if allowClear && selectedItem}
          <button
            type="button"
            class="select-option clear-option"
            onclick={clearSelection}
          >
            <svg viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/>
            </svg>
            Limpar seleção
          </button>
        {/if}

        {#each flatItems as item}
          {#if item.type === 'group'}
            <div class="select-group-label">{item.label}</div>
          {:else}
            <button
              type="button"
              class="select-option"
              class:selected={selectedItem?.value === item.value}
              onclick={() => selectItem(item)}
            >
              {#if item.icon}
                <span class="option-icon">{@html item.icon}</span>
              {/if}
              <span class="option-label">{item.label || item.name || item.title}</span>
              {#if item.description}
                <span class="option-desc">{item.description}</span>
              {/if}
              {#if selectedItem?.value === item.value}
                <svg class="check-icon" viewBox="0 0 20 20" fill="currentColor">
                  <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/>
                </svg>
              {/if}
            </button>
          {/if}
        {/each}

        {#if flatItems.length === 0}
          <div class="select-empty">Nenhum resultado encontrado</div>
        {/if}
      </div>
    </div>
  {/if}
</div>

<style>
  .select-container {
    position: relative;
    width: 100%;
  }

  .select-container.disabled {
    opacity: 0.6;
    pointer-events: none;
  }

  .select-trigger {
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 14px;
    background: white;
    border: 1px solid #d1d5db;
    border-radius: 8px;
    cursor: pointer;
    font-size: 14px;
    transition: border-color 0.2s, box-shadow 0.2s;
  }

  .select-trigger:hover {
    border-color: #9ca3af;
  }

  .select-container.open .select-trigger {
    border-color: #4a90d9;
    box-shadow: 0 0 0 3px rgba(74, 144, 217, 0.1);
  }

  .select-value {
    display: flex;
    align-items: center;
    gap: 8px;
    color: #1f2937;
  }

  .select-placeholder {
    color: #9ca3af;
  }

  .select-arrow {
    width: 20px;
    height: 20px;
    color: #9ca3af;
    transition: transform 0.2s;
  }

  .select-container.open .select-arrow {
    transform: rotate(180deg);
  }

  .select-dropdown {
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    z-index: 50;
    margin-top: 4px;
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
    animation: dropdownOpen 0.2s ease;
  }

  @keyframes dropdownOpen {
    from {
      opacity: 0;
      transform: translateY(-8px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  .select-search {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 12px;
    border-bottom: 1px solid #e5e7eb;
  }

  .select-search svg {
    width: 18px;
    height: 18px;
    color: #9ca3af;
    flex-shrink: 0;
  }

  .select-search-input {
    flex: 1;
    border: none;
    outline: none;
    font-size: 14px;
    background: none;
  }

  .select-options {
    max-height: 250px;
    overflow-y: auto;
    padding: 4px;
  }

  .select-option {
    width: 100%;
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 12px;
    border: none;
    background: none;
    text-align: left;
    cursor: pointer;
    border-radius: 6px;
    font-size: 14px;
    color: #374151;
    transition: background 0.15s;
  }

  .select-option:hover {
    background: #f3f4f6;
  }

  .select-option.selected {
    background: #eff6ff;
    color: #4a90d9;
  }

  .select-option.clear-option {
    color: #ef4444;
    border-bottom: 1px solid #e5e7eb;
    margin-bottom: 4px;
  }

  .select-group-label {
    padding: 8px 12px 4px;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    color: #9ca3af;
    letter-spacing: 0.5px;
  }

  .option-icon {
    flex-shrink: 0;
    width: 18px;
    height: 18px;
  }

  .option-label {
    flex: 1;
  }

  .option-desc {
    font-size: 12px;
    color: #9ca3af;
  }

  .check-icon {
    width: 16px;
    height: 16px;
    color: #4a90d9;
  }

  .select-empty {
    padding: 20px;
    text-align: center;
    color: #9ca3af;
    font-size: 14px;
  }
</style>