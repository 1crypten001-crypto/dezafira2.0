<script lang="ts">
  import { page } from '$app/stores';
  import { t } from '$lib/i18n';

  let {
    value = '',
    placeholder = '',
    onSearch = () => {}
  } = $props();

  const lang = $derived($page.data.language || 'pt');
  const i18nPlaceholder = $derived(placeholder || t(lang, 'search.placeholder'));
  let inputValue = $state(value);

  $effect(() => {
    // Sync only when the external 'value' prop changes.
    // Assigning to inputValue here won't trigger an infinite loop 
    // as long as we don't read inputValue inside this effect.
    inputValue = value;
  });

  function handleClear() {
    inputValue = '';
    onSearch('');
  }

  function handleSubmit(event: Event) {
    event.preventDefault();
    onSearch(inputValue);
  }
</script>

<form class="search-container" onsubmit={handleSubmit}>
  <div class="search-input-wrapper">
    <svg class="search-icon" viewBox="0 0 20 20" fill="currentColor">
      <path fill-rule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clip-rule="evenodd"/>
    </svg>

    <input
      type="search"
      bind:value={inputValue}
      placeholder={i18nPlaceholder}
      class="search-input"
      aria-label={t(lang, 'search.aria')}
    />

    {#if inputValue.length > 0}
      <button type="button" class="search-clear" onclick={handleClear} aria-label={t(lang, 'search.clear')}>
        <svg viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/>
        </svg>
      </button>
    {/if}
  </div>

  <button type="submit" class="search-submit">
    {t(lang, 'search.button')}
  </button>
</form>

<style>
  .search-container {
    display: flex;
    gap: 8px;
    width: 100%;
  }

  .search-input-wrapper {
    flex: 1;
    position: relative;
    display: flex;
    align-items: center;
  }

  .search-icon {
    position: absolute;
    left: 12px;
    width: 20px;
    height: 20px;
    color: var(--text-muted, #9ca3af);
    pointer-events: none;
  }

  .search-input {
    width: 100%;
    height: 44px;
    padding: 0 40px;
    border: 1px solid var(--border-color, #e5e7eb);
    border-radius: 12px;
    font-size: 15px;
    background: var(--bg-primary, white);
    color: var(--text-primary, black);
    transition: all 0.2s;
  }

  .search-input:focus {
    outline: none;
    border-color: var(--text-primary, #111);
    box-shadow: 0 0 0 1px var(--text-primary, #111);
  }

  .search-input::placeholder {
    color: var(--text-muted, #9ca3af);
  }

  .search-input::-webkit-search-cancel-button,
  .search-input::-webkit-search-decoration {
    display: none;
  }

  .search-clear {
    position: absolute;
    right: 12px;
    width: 20px;
    height: 20px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--text-muted, #9ca3af);
    background: none;
    border: none;
    padding: 0;
    cursor: pointer;
    transition: color 0.2s;
  }

  .search-clear:hover {
    color: var(--text-primary, #111);
  }

  .search-submit {
    height: 44px;
    padding: 0 20px;
    background: var(--text-primary, #111);
    color: var(--bg-primary, white);
    border: 1px solid var(--text-primary, #111);
    border-radius: 12px;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
    white-space: nowrap;
  }

  .search-submit:hover {
    background: transparent;
    color: var(--text-primary, #111);
  }

  @media (max-width: 640px) {
    .search-container {
      flex-direction: column;
    }

    .search-submit {
      width: 100%;
    }
  }
</style>