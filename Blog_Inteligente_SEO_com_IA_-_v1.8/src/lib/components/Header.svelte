<script lang="ts">
  import { page } from '$app/stores';
  import { t } from '$lib/i18n';
  
  let { 
    logo = '',
    siteName = 'Blog',
    showSearch = true,
    showThemeToggle = true,
    user = null,
    enableMemberLogin = false,
    defaultTheme = 'light',
    language = ''
  } = $props();

  let mobileMenuOpen = $state(false);
  let searchOpen = $state(false);
  let searchQuery = $state('');
  let theme = $state<'light' | 'dark'>('light');
  let themeReady = $state(false);

  const lang = $derived(language || $page.data.language || 'pt');
  
  const links = $derived([
    { label: t(lang, 'nav.home'), href: '/' },
    { label: t(lang, 'nav.categories'), href: '/categories' },
    { label: t(lang, 'nav.products'), href: '/products' },
    ...(user ? [
      { label: t(lang, 'nav.courses'), href: '/members/area' },
      { label: t(lang, 'nav.my_account'), href: '/members/dashboard' }
    ] : [
      { label: t(lang, 'nav.premium'), href: '/premium' },
      { label: t(lang, 'nav.login'), href: '/members/login' }
    ])
  ]);
  
  function toggleMobileMenu() {
    mobileMenuOpen = !mobileMenuOpen;
  }
  
  function toggleSearch() {
    searchOpen = !searchOpen;
    if (!searchOpen) searchQuery = '';
  }
  
  function handleSearch(e: Event) {
    e.preventDefault();
    if (searchQuery.trim()) {
      window.location.href = `/?q=${encodeURIComponent(searchQuery)}`;
    }
  }

  function toggleTheme() {
    theme = theme === 'dark' ? 'light' : 'dark';
  }

  $effect(() => {
    if (typeof window === 'undefined') return;
    if (themeReady) return;

    const stored = window.localStorage.getItem('theme');
    theme = stored === 'dark' || stored === 'light' ? stored : (defaultTheme === 'dark' || defaultTheme === 'light' ? defaultTheme : 'light');
    themeReady = true;
  });

  $effect(() => {
    if (typeof document === 'undefined') return;
    document.documentElement.dataset.theme = theme;
    if (typeof window !== 'undefined') window.localStorage.setItem('theme', theme);
  });
</script>

<header class="header">
  <div class="header-container">
    <!-- Logo -->
    <a href="/" class="logo">
      <div class="logo-icon-dezafira">
        <span>D</span>
      </div>
      <span class="logo-text">Dezafira Club</span>
    </a>

    <!-- Desktop Nav -->
    <nav class="nav-desktop">
      {#each links as link}
        <a 
          href={link.href} 
          class="nav-link"
          class:active={$page.url.pathname === link.href}
        >
          {link.label}
        </a>
      {/each}
    </nav>

    <!-- Actions -->
    <div class="header-actions">
      {#if showSearch}
        <button class="action-btn" onclick={toggleSearch} aria-label={t(lang, 'nav.search_aria')}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"/>
            <path d="M21 21l-4.35-4.35"/>
          </svg>
        </button>
      {/if}

      {#if showThemeToggle}
        <button
          class="action-btn"
          onclick={toggleTheme}
          aria-label={theme === 'dark' ? t(lang, 'nav.theme_light') : t(lang, 'nav.theme_dark')}
        >
          {#if theme === 'dark'}
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="5"/>
              <line x1="12" y1="1" x2="12" y2="3"/>
              <line x1="12" y1="21" x2="12" y2="23"/>
              <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>
              <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
              <line x1="1" y1="12" x2="3" y2="12"/>
              <line x1="21" y1="12" x2="23" y2="12"/>
              <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/>
              <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
            </svg>
          {:else}
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z"/>
            </svg>
          {/if}
        </button>
      {/if}

      <!-- Mobile menu toggle -->
      <button class="action-btn mobile-menu-btn" onclick={toggleMobileMenu} aria-label={t(lang, 'nav.menu')}>
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          {#if mobileMenuOpen}
            <line x1="18" y1="6" x2="6" y2="18"/>
            <line x1="6" y1="6" x2="18" y2="18"/>
          {:else}
            <line x1="3" y1="12" x2="21" y2="12"/>
            <line x1="3" y1="6" x2="21" y2="6"/>
            <line x1="3" y1="18" x2="21" y2="18"/>
          {/if}
        </svg>
      </button>
    </div>
  </div>

  <!-- Search Bar -->
  {#if searchOpen}
    <div class="search-bar">
      <form onsubmit={handleSearch} class="search-form">
        <input 
          type="search"
          bind:value={searchQuery}
          placeholder={t(lang, 'nav.search_placeholder')}
          class="search-input"
        />
        <button type="submit" class="search-submit" aria-label={t(lang, 'nav.search_aria')}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"/>
            <path d="M21 21l-4.35-4.35"/>
          </svg>
        </button>
        <button type="button" class="search-close" onclick={toggleSearch} aria-label={t(lang, 'nav.search_close')}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"/>
            <line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>
      </form>
    </div>
  {/if}

  <!-- Mobile Nav -->
  {#if mobileMenuOpen}
    <nav class="nav-mobile">
      {#each links as link}
        <a 
          href={link.href} 
          class="nav-link-mobile"
          class:active={$page.url.pathname === link.href}
          onclick={() => mobileMenuOpen = false}
        >
          {link.label}
        </a>
      {/each}
    </nav>
  {/if}
</header>

<style>
  .header {
    background: var(--bg-primary);
    border-bottom: 1px solid var(--border-color);
    position: sticky;
    top: 0;
    z-index: 100;
  }

  .header-container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 20px;
    height: 64px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 24px;
  }

  /* Logo */
  .logo {
    display: flex;
    align-items: center;
    gap: 10px;
    text-decoration: none;
    color: var(--text-primary);
  }

  .logo-icon-dezafira {
    width: 32px;
    height: 32px;
    background: var(--accent);
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--accent-text);
    font-weight: 800;
    font-size: 16px;
  }

  .logo-text {
    font-size: 20px;
    font-weight: 700;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 280px;
  }

  /* Desktop Nav */
  .nav-desktop {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .nav-link {
    padding: 8px 16px;
    border-radius: 6px;
    color: var(--text-secondary);
    text-decoration: none;
    font-size: 15px;
    font-weight: 500;
    transition: all 0.2s;
    white-space: nowrap;
  }

  .nav-link:hover {
    background: var(--bg-tertiary);
    color: var(--text-primary);
  }

  .nav-link.active {
    background: var(--bg-tertiary);
    color: var(--text-primary);
  }

  /* Actions */
  .header-actions {
    display: flex;
    align-items: center;
    gap: 4px;
  }

  .action-btn {
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 8px;
    background: none;
    border: none;
    color: var(--text-secondary);
    cursor: pointer;
    transition: all 0.2s;
  }

  .action-btn:hover {
    background: var(--bg-tertiary);
    color: var(--text-primary);
  }

  .action-btn svg {
    width: 20px;
    height: 20px;
  }

  .mobile-menu-btn {
    display: none;
  }

  /* Search Bar */
  .search-bar {
    border-top: 1px solid var(--border-color);
    padding: 12px 20px;
    background: var(--bg-secondary);
  }

  .search-form {
    max-width: 600px;
    margin: 0 auto;
    display: flex;
    gap: 8px;
  }

  .search-input {
    flex: 1;
    height: 44px;
    padding: 0 16px;
    border: 1px solid var(--border-color);
    border-radius: 8px;
    font-size: 16px;
    background: var(--bg-primary);
    color: var(--text-primary);
  }

  .search-input:focus {
    outline: none;
    border-color: var(--border-dark);
  }

  .search-submit,
  .search-close {
    width: 44px;
    height: 44px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 8px;
    border: none;
    cursor: pointer;
  }

  .search-submit {
    background: var(--text-primary);
    color: var(--bg-primary);
  }

  .search-close {
    background: var(--bg-tertiary);
    color: var(--text-secondary);
  }

  .search-submit svg,
  .search-close svg {
    width: 20px;
    height: 20px;
  }

  /* Mobile Nav */
  .nav-mobile {
    display: none;
    flex-direction: column;
    padding: 8px 20px 16px;
    border-top: 1px solid var(--border-color);
    background: var(--bg-primary);
  }

  .nav-link-mobile {
    padding: 12px 0;
    color: var(--text-secondary);
    text-decoration: none;
    font-size: 16px;
    font-weight: 500;
    border-bottom: 1px solid var(--border-light);
  }

  .nav-link-mobile:hover,
  .nav-link-mobile.active {
    color: var(--text-primary);
  }

  /* Responsive */
  @media (max-width: 992px) {
    .logo {
      min-width: 0;
      max-width: 220px;
    }

    .logo-text {
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      max-width: 180px;
    }

    .nav-desktop {
      display: none;
    }

    .mobile-menu-btn {
      display: flex;
    }

    .nav-mobile {
      display: flex;
    }
  }
</style>
