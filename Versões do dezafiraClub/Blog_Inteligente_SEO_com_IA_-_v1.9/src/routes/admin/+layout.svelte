<script lang="ts">
  import { page } from "$app/stores";
  import { t } from "$lib/i18n";


  let { children } = $props();
  const lang = $derived($page.data.language || 'pt');
  let sidebarOpen = $state(false);
  let toolsMenuOpen = $state(false);

  // Close sidebar on route change (mobile)
  $effect(() => {
    $page.url.pathname;
    sidebarOpen = false;
  });

  // Auto-open tools submenu if we are currently inside a tools route
  $effect(() => {
    if ($page.url.pathname.startsWith("/admin/shortlinks") || $page.url.pathname.startsWith("/admin/landing-pages") || $page.url.pathname.startsWith("/admin/web-stories")) {
      toolsMenuOpen = true;
    }
  });

  // Lock background scroll when mobile sidebar is open
  $effect(() => {
    if (typeof document === 'undefined') return;
    if (sidebarOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
  });

  // Check if we're on the login page to hide the admin layout
  const isLoginPage = $derived($page.url.pathname === "/admin/login");

  function toggleSidebar() {
    sidebarOpen = !sidebarOpen;
  }

  function closeSidebar() {
    sidebarOpen = false;
  }
const navItems = $derived([
    {
      href: "/admin",
      label: t(lang, 'admin.menu.dashboard'),
      exact: true,
      icon: `<svg viewBox="0 0 20 20" fill="currentColor"><path d="M2 10a8 8 0 1116 0A8 8 0 012 10zm8-3a1 1 0 00-.867.5L7.414 10H6a1 1 0 000 2h2a1 1 0 00.867-.5L10 9.732l1.133 1.768A1 1 0 0012 12h2a1 1 0 000-2h-1.414l-1.719-2.5A1 1 0 0010 7z"/></svg>`,
    },
    {
      href: "/admin/sales",
      label: t(lang, 'admin.menu.sales'),
      exact: false,
      prefix: "/admin/sales",
      icon: `<svg viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-11a1 1 0 10-2 0v.177c-1.383.17-2.5 1.213-2.5 2.573 0 1.36 1.117 2.403 2.5 2.573V14a1 1 0 102 0v-.177c1.383-.17 2.5-1.213 2.5-2.573 0-1.36-1.117-2.403-2.5-2.573V7zm-2.5 3.323c0-.448.337-.823.75-.893v1.786c-.413-.07-.75-.445-.75-.893zm2.5 2.247v-1.786c.413.07.75.445.75.893 0 .448-.337.823-.75.893z" clip-rule="evenodd"/></svg>`,
    },
    {
      href: "/admin/posts/new",
      label: t(lang, 'admin.menu.new_post'),
      exact: false,
      prefix: "/admin/posts/new",
      icon: `<svg viewBox="0 0 20 20" fill="currentColor"><path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zm-2.207 2.207L3 14.172V17h2.828l8.38-8.379-2.83-2.828z"/></svg>`,
    },
    {
      href: "/admin/posts",
      label: t(lang, 'admin.menu.posts'),
      exact: false,
      prefix: "/admin/posts",
      excludePrefixes: ["/admin/posts/new", "/admin/posts/import-youtube"],
      icon: `<svg viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clip-rule="evenodd"/></svg>`,
    },
    {
      href: "/admin/posts/import-youtube",
      label: t(lang, 'admin.menu.youtube_import'),
      exact: false,
      prefix: "/admin/posts/import-youtube",
      icon: `<svg viewBox="0 0 20 20" fill="currentColor"><path d="M10 12a2 2 0 100-4 2 2 0 000 4z"/><path fill-rule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clip-rule="evenodd"/></svg>`,
    },
    {
      href: "/admin/categories",
      label: t(lang, 'admin.menu.categories'),
      exact: false,
      prefix: "/admin/categories",
      icon: `<svg viewBox="0 0 20 20" fill="currentColor"><path d="M5 3a1 1 0 000 2c5.523 0 10 4.477 10 10a1 1 0 102 0C17 8.373 11.627 3 5 3z"/><path d="M4 9a1 1 0 011-1 7 7 0 017 7 1 1 0 11-2 0 5 5 0 00-5-5 1 1 0 01-1-1zM3 15a2 2 0 114 0 2 2 0 01-4 0z"/></svg>`,
    },
    {
      href: "/admin/ads",
      label: t(lang, 'admin.menu.ads'),
      exact: false,
      prefix: "/admin/ads",
      icon: `<svg viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M3 5a2 2 0 012-2h10a2 2 0 012 2v8a2 2 0 01-2 2h-2.22l.123.489.804.804A1 1 0 0113 18H7a1 1 0 01-.707-1.707l.804-.804L7.22 15H5a2 2 0 01-2-2V5zm5.771 7H5V5h10v7H8.771z" clip-rule="evenodd"/></svg>`,
    },
    {
      href: "/admin/premium/plans",
      label: t(lang, 'admin.menu.premium'),
      exact: false,
      prefix: "/admin/premium",
      icon: `<svg viewBox="0 0 20 20" fill="currentColor"><path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"/></svg>`,
    },
    {
      href: "/admin/newsletter",
      label: t(lang, 'admin.menu.newsletter'),
      exact: false,
      prefix: "/admin/newsletter",
      icon: `<svg viewBox="0 0 20 20" fill="currentColor"><path d="M2.003 5.884L10 9.882l7.997-3.998A2 2 0 0016 4H4a2 2 0 00-1.997 1.884z"/><path d="M18 8.118l-8 4-8-4V14a2 2 0 002 2h12a2 2 0 002-2V8.118z"/></svg>`,
    },
    {
      href: "/admin/products",
      label: t(lang, 'admin.menu.products'),
      exact: false,
      prefix: "/admin/products",
      excludePrefixes: ["/admin/products/categories"],
      icon: `<svg viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M10 2a4 4 0 00-4 4v1H5a1 1 0 00-.994.89l-1 9A1 1 0 004 18h12a1 1 0 00.994-1.11l-1-9A1 1 0 0015 7h-1V6a4 4 0 00-4-4zm2 5V6a2 2 0 10-4 0v1h4zm-6 3a1 1 0 112 0 1 1 0 01-2 0zm7-1a1 1 0 100 2 1 1 0 000-2z" clip-rule="evenodd"/></svg>`,
    },
    {
      href: "/admin/products/categories",
      label: t(lang, 'admin.menu.product_categories'),
      exact: false,
      prefix: "/admin/products/categories",
      icon: `<svg viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clip-rule="evenodd"/></svg>`,
    },
    {
      href: "/admin/courses",
      label: t(lang, 'admin.menu.courses'),
      exact: false,
      prefix: "/admin/courses",
      icon: `<svg viewBox="0 0 20 20" fill="currentColor"><path d="M10.394 2.08a1 1 0 00-.788 0l-7 3a1 1 0 000 1.84L5.25 8.051a.999.999 0 01.356-.257l4-1.714a1 1 0 11.788 1.838L7.667 9.088l1.94.831a1 1 0 00.787 0l7-3a1 1 0 000-1.838l-7-3zM3.31 9.397L5 10.12v4.102a8.969 8.969 0 00-1.05-.174 1 1 0 01-.89-.89 11.115 11.115 0 01.25-3.762zM9.3 16.573A9.026 9.026 0 007 14.935v-3.957l1.818.78a3 3 0 002.364 0l5.508-2.361a11.026 11.026 0 01.25 3.762 1 1 0 01-.89.89 8.968 8.968 0 00-5.35 2.524 1 1 0 01-1.4 0zM6 18a1 1 0 001-1v-2.065a8.935 8.935 0 00-2-.712V17a1 1 0 001 1z"/></svg>`,
    },
    {
      href: "/admin/community",
      label: "Comunidade VIP",
      exact: false,
      prefix: "/admin/community",
      icon: `<svg viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9a1 1 0 100 2h6a1 1 0 100-2H7z" clip-rule="evenodd"/></svg>`,
    },
    {
      href: "/admin/users",
      label: t(lang, 'admin.menu.users'),
      exact: false,
      prefix: "/admin/users",
      icon: `<svg viewBox="0 0 20 20" fill="currentColor"><path d="M9 6a3 3 0 11-6 0 3 3 0 016 0zM17 6a3 3 0 11-6 0 3 3 0 016 0zM12.93 17c.046-.327.07-.66.07-1a6.97 6.97 0 00-1.5-4.33A5 5 0 0119 16v1h-6.07zM6 11a5 5 0 015 5v1H1v-1a5 5 0 015-5z"/></svg>`,
    },
    {
      href: "/admin/cli",
      label: t(lang, 'admin.menu.cli_api'),
      exact: false,
      prefix: "/admin/cli",
      icon: `<svg viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M2 5a2 2 0 012-2h12a2 2 0 012 2v10a2 2 0 01-2 2H4a2 2 0 01-2-2V5zm3.293 1.293a1 1 0 011.414 0l3 3a1 1 0 010 1.414l-3 3a1 1 0 01-1.414-1.414L7.586 10 5.293 7.707a1 1 0 010-1.414zM11 12a1 1 0 100 2h3a1 1 0 100-2h-3z" clip-rule="evenodd"/></svg>`,
    },
    {
      href: "/admin/settings",
      label: t(lang, 'admin.menu.settings'),
      exact: false,
      prefix: "/admin/settings",
      icon: `<svg viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z" clip-rule="evenodd"/></svg>`,
    },
  ]);

  function isActive(item: any) {
    const path = $page.url.pathname;
    if (item.exact) return path === item.href;
    if (item.excludePrefixes?.some((ex: string) => path.startsWith(ex))) return false;
    return item.prefix ? path.startsWith(item.prefix) : false;
  }
</script>

<svelte:head>
  <title>Admin</title>
</svelte:head>

{#if isLoginPage}
  {@render children()}
{:else}
  <div class="admin-layout">
    <!-- Mobile topbar -->
    <header class="topbar">
      <button class="menu-toggle" onclick={toggleSidebar} aria-label="Menu">
        <svg viewBox="0 0 20 20" fill="currentColor" width="20" height="20">
          {#if sidebarOpen}
            <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/>
          {:else}
            <path fill-rule="evenodd" d="M3 5a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM3 10a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM3 15a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clip-rule="evenodd"/>
          {/if}
        </svg>
      </button>
      <a href="/admin" class="topbar-brand">Admin</a>
      <a href="/" class="topbar-blog-link" target="_blank" aria-label="Ver blog">
        <svg viewBox="0 0 20 20" fill="currentColor" width="16" height="16">
          <path d="M11 3a1 1 0 100 2h2.586l-6.293 6.293a1 1 0 101.414 1.414L15 6.414V9a1 1 0 102 0V4a1 1 0 00-1-1h-5z"/>
          <path d="M5 5a2 2 0 00-2 2v8a2 2 0 002 2h8a2 2 0 002-2v-3a1 1 0 10-2 0v3H5V7h3a1 1 0 000-2H5z"/>
        </svg>
      </a>
    </header>

    <!-- Overlay -->
    {#if sidebarOpen}
      <button class="overlay" onclick={closeSidebar} aria-label="Fechar menu"></button>
    {/if}

    <!-- Sidebar -->
    <aside class="sidebar" class:open={sidebarOpen}>
      <div class="sidebar-brand">
        <a href="/admin" onclick={closeSidebar}>Admin</a>
      </div>

      <nav class="sidebar-nav">
        <div class="nav-group">
          <span class="nav-group-label">{t(lang, 'admin.group_content')}</span>
          {#each navItems.slice(0, 4) as item}
            <a
              href={item.href}
              class="nav-item"
              class:active={isActive(item)}
              onclick={closeSidebar}
            >
              <span class="nav-icon">{@html item.icon}</span>
              <span class="nav-label">{item.label}</span>
              {#if isActive(item)}
                <span class="nav-dot"></span>
              {/if}
            </a>
          {/each}
        </div>

        <div class="nav-group">
          <span class="nav-group-label">{t(lang, 'admin.group_management')}</span>
          {#each navItems.slice(4, 10) as item}
            <a
              href={item.href}
              class="nav-item"
              class:active={isActive(item)}
              onclick={closeSidebar}
            >
              <span class="nav-icon">{@html item.icon}</span>
              <span class="nav-label">{item.label}</span>
              {#if isActive(item)}
                <span class="nav-dot"></span>
              {/if}
            </a>
          {/each}

          <!-- Dropdown Ferramentas -->
          <details class="tools-dropdown" bind:open={toolsMenuOpen}>
            <summary class="nav-item nav-dropdown-btn" class:active={$page.url.pathname.startsWith("/admin/shortlinks") || $page.url.pathname.startsWith("/admin/landing-pages") || $page.url.pathname.startsWith("/admin/web-stories")}>
              <span class="nav-icon">
                <svg viewBox="0 0 20 20" fill="currentColor">
                  <path fill-rule="evenodd" d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.381z" clip-rule="evenodd"/>
                </svg>
              </span>
              <span class="nav-label">{t(lang, 'admin.group_tools')}</span>
              <span class="nav-arrow">
                <svg viewBox="0 0 20 20" fill="currentColor" width="16" height="16">
                  <path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd"/>
                </svg>
              </span>
            </summary>
            
            <div class="submenu">
              <a
                href="/admin/shortlinks"
                class="nav-item submenu-item"
                class:active={$page.url.pathname.startsWith("/admin/shortlinks")}
                onclick={closeSidebar}
              >
                <span class="nav-icon">
                  <svg viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M12.586 4.586a2 2 0 112.828 2.828l-3 3a2 2 0 01-2.828 0 1 1 0 00-1.414 1.414 4 4 0 005.656 0l3-3a4 4 0 00-5.656-5.656l-1.5 1.5a1 1 0 101.414 1.414l1.5-1.5zm-5 5a2 2 0 012.828 0 1 1 0 101.414-1.414 4 4 0 00-5.656 0l-3 3a4 4 0 105.656 5.656l1.5-1.5a1 1 0 10-1.414-1.414l-1.5 1.5a2 2 0 11-2.828-2.828l3-3z" clip-rule="evenodd"/>
                  </svg>
                </span>
                <span class="nav-label">{t(lang, 'admin.menu.shortlinks')}</span>
              </a>

              <a
                href="/admin/landing-pages"
                class="nav-item submenu-item"
                class:active={$page.url.pathname.startsWith("/admin/landing-pages")}
                onclick={closeSidebar}
              >
                <span class="nav-icon">
                  <svg viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M4 4a2 2 0 012-2h8a2 2 0 012 2v12a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 12h8V4H6v12zm2-8a1 1 0 011-1h4a1 1 0 110 2H9a1 1 0 01-1-1zm0 4a1 1 0 011-1h4a1 1 0 110 2H9a1 1 0 01-1-1z" clip-rule="evenodd"/>
                  </svg>
                </span>
                <span class="nav-label">{t(lang, 'admin.menu.landing_pages')}</span>
                <span class="nav-badge">{t(lang, 'admin.menu.badge_new')}</span>
              </a>

              <a
                href="/admin/web-stories"
                class="nav-item submenu-item"
                class:active={$page.url.pathname.startsWith("/admin/web-stories")}
                onclick={closeSidebar}
              >
                <span class="nav-icon">
                  <svg viewBox="0 0 20 20" fill="currentColor">
                    <path d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h4V3H4zm6 0v14h6a2 2 0 002-2V5a2 2 0 00-2-2h-6z"/>
                  </svg>
                </span>
                <span class="nav-label">{t(lang, 'admin.menu.web_stories')}</span>
                <span class="nav-badge">{t(lang, 'admin.menu.badge_new')}</span>
              </a>
            </div>
          </details>
        </div>

        <div class="nav-group">
          <span class="nav-group-label">{t(lang, 'admin.group_system')}</span>
          {#each navItems.slice(10) as item}
            <a
              href={item.href}
              class="nav-item"
              class:active={isActive(item)}
              onclick={closeSidebar}
            >
              <span class="nav-icon">{@html item.icon}</span>
              <span class="nav-label">{item.label}</span>
              {#if isActive(item)}
                <span class="nav-dot"></span>
              {/if}
            </a>
          {/each}
        </div>
      </nav>

      <div class="sidebar-footer">
        <a href="/" class="footer-link" target="_blank">
          <svg viewBox="0 0 20 20" fill="currentColor" width="16" height="16">
            <path d="M11 3a1 1 0 100 2h2.586l-6.293 6.293a1 1 0 101.414 1.414L15 6.414V9a1 1 0 102 0V4a1 1 0 00-1-1h-5z"/>
            <path d="M5 5a2 2 0 00-2 2v8a2 2 0 002 2h8a2 2 0 002-2v-3a1 1 0 10-2 0v3H5V7h3a1 1 0 000-2H5z"/>
          </svg>
          {t(lang, 'admin.view_blog')}
        </a>
        <form action="/admin/logout" method="POST">
          <button type="submit" class="footer-link footer-logout">
            <svg viewBox="0 0 20 20" fill="currentColor" width="16" height="16">
              <path fill-rule="evenodd" d="M3 3a1 1 0 00-1 1v12a1 1 0 102 0V4a1 1 0 00-1-1zm10.293 9.293a1 1 0 001.414 1.414l3-3a1 1 0 000-1.414l-3-3a1 1 0 10-1.414 1.414L14.586 9H7a1 1 0 100 2h7.586l-1.293 1.293z" clip-rule="evenodd"/>
            </svg>
            {t(lang, 'admin.logout')}
          </button>
        </form>
      </div>
    </aside>

    <!-- Main content -->
    <main class="main-content">
      {@render children()}
    </main>
  </div>
{/if}

<style>
  /* ── Layout shell ─────────────────────────────────────────────── */
  .admin-layout {
    display: flex;
    flex-direction: column;
    min-height: 100dvh;
    background: var(--bg-secondary);
  }

  /* ── Mobile topbar ────────────────────────────────────────────── */
  .topbar {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    z-index: 100;
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0 1rem;
    height: 52px;
    background: var(--bg-primary);
    border-bottom: 1px solid var(--border-light);
  }

  .menu-toggle {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 36px;
    height: 36px;
    border: none;
    border-radius: var(--radius-md);
    background: transparent;
    color: var(--text-secondary);
    cursor: pointer;
    transition: background var(--transition-fast), color var(--transition-fast);
    flex-shrink: 0;
  }

  .menu-toggle:hover {
    background: var(--bg-secondary);
    color: var(--text-primary);
  }

  .topbar-brand {
    font-family: var(--font-sans);
    font-size: 0.9375rem;
    font-weight: 600;
    color: var(--text-primary);
    text-decoration: none;
    flex: 1;
  }

  .topbar-blog-link {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 36px;
    height: 36px;
    border-radius: var(--radius-md);
    color: var(--text-muted);
    transition: background var(--transition-fast), color var(--transition-fast);
  }

  .topbar-blog-link:hover {
    background: var(--bg-secondary);
    color: var(--text-primary);
  }

  /* ── Overlay ──────────────────────────────────────────────────── */
  .overlay {
    position: fixed;
    inset: 0;
    z-index: 200;
    background: rgba(0, 0, 0, 0.4);
    border: none;
    cursor: pointer;
    backdrop-filter: blur(2px);
  }

  /* ── Sidebar ──────────────────────────────────────────────────── */
  .sidebar {
    position: fixed;
    top: 0;
    left: 0;
    bottom: 0;
    z-index: 210;
    width: 260px;
    background: var(--bg-primary);
    border-right: 1px solid var(--border-light);
    display: flex;
    flex-direction: column;
    transform: translateX(-100%);
    transition: transform 0.24s cubic-bezier(0.4, 0, 0.2, 1);
    will-change: transform;
  }

  .sidebar.open {
    transform: translateX(0);
    box-shadow: 0 0 40px rgba(0, 0, 0, 0.12);
  }

  .sidebar-brand {
    padding: 1.25rem 1.25rem 1rem;
    border-bottom: 1px solid var(--border-light);
  }

  .sidebar-brand a {
    font-family: var(--font-sans);
    font-size: 1rem;
    font-weight: 700;
    color: var(--text-primary);
    text-decoration: none;
    letter-spacing: -0.3px;
  }

  /* ── Nav groups ───────────────────────────────────────────────── */
  .sidebar-nav {
    flex: 1;
    overflow-y: auto;
    padding: 0.75rem 0;
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .nav-group {
    padding: 0 0.75rem 0.5rem;
  }

  .nav-group-label {
    display: block;
    padding: 0.5rem 0.5rem 0.375rem;
    font-family: var(--font-sans);
    font-size: 0.6875rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--text-muted);
  }

  /* ── Nav items ────────────────────────────────────────────────── */
  .nav-item {
    display: flex;
    align-items: center;
    gap: 0.625rem;
    padding: 0.5625rem 0.625rem;
    border-radius: var(--radius-md);
    font-family: var(--font-sans);
    font-size: 0.875rem;
    color: var(--text-secondary);
    text-decoration: none;
    transition: background var(--transition-fast), color var(--transition-fast);
    position: relative;
  }

  .nav-item:hover {
    background: var(--bg-secondary);
    color: var(--text-primary);
  }

  .nav-item.active {
    background: var(--bg-tertiary, var(--bg-secondary));
    color: var(--text-primary);
    font-weight: 500;
  }

  .nav-icon {
    width: 18px;
    height: 18px;
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    opacity: 0.7;
  }

  .nav-item.active .nav-icon {
    opacity: 1;
  }

  .nav-icon :global(svg) {
    width: 16px;
    height: 16px;
  }

  .nav-label {
    flex: 1;
    min-width: 0;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .nav-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--text-primary);
    flex-shrink: 0;
  }

  /* ── Sidebar footer ───────────────────────────────────────────── */
  .sidebar-footer {
    padding: 0.75rem;
    border-top: 1px solid var(--border-light);
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .footer-link {
    display: flex;
    align-items: center;
    gap: 0.625rem;
    padding: 0.5625rem 0.625rem;
    border-radius: var(--radius-md);
    font-family: var(--font-sans);
    font-size: 0.875rem;
    color: var(--text-muted);
    text-decoration: none;
    background: none;
    border: none;
    width: 100%;
    text-align: left;
    cursor: pointer;
    transition: background var(--transition-fast), color var(--transition-fast);
  }

  .footer-link:hover {
    background: var(--bg-secondary);
    color: var(--text-primary);
  }

  .footer-logout {
    color: #dc2626;
  }

  .footer-logout:hover {
    background: #fef2f2;
    color: #dc2626;
  }

  /* ── Main content ─────────────────────────────────────────────── */
  .main-content {
    flex: 1;
    padding: 1.25rem 1rem;
    margin-top: 52px;
    min-width: 0;
  }

  /* ── Desktop: persistent sidebar ─────────────────────────────── */
  @media (min-width: 1024px) {
    .admin-layout {
      flex-direction: row;
    }

    .topbar {
      display: none;
    }

    .overlay {
      display: none !important;
    }

    .sidebar {
      position: fixed;
      top: 0;
      left: 0;
      bottom: 0;
      width: 260px;
      height: 100dvh;
      transform: none !important;
      box-shadow: none;
      flex-shrink: 0;
    }

    .main-content {
      margin-left: 260px;
      margin-top: 0;
      width: calc(100% - 260px);
      padding: 2rem;
    }
  }

  @media (min-width: 1280px) {
    .main-content {
      padding: 2rem 2.5rem;
    }
  }

  /* ── Submenus & Dropdowns ─────────────────────────────────────── */
  .nav-dropdown-btn {
    width: 100%;
    text-align: left;
    background: transparent;
    border: none;
    cursor: pointer;
    font-family: inherit;
    font-size: inherit;
  }

  .nav-arrow {
    display: flex;
    align-items: center;
    justify-content: center;
    transition: transform var(--transition-fast);
  }

  .tools-dropdown[open] .nav-arrow {
    transform: rotate(90deg);
  }

  summary.nav-dropdown-btn {
    list-style: none;
    outline: none;
  }

  summary.nav-dropdown-btn::-webkit-details-marker {
    display: none;
  }

  .submenu {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    padding-left: 1.25rem;
    margin-top: 0.25rem;
    border-left: 1px solid var(--border-light);
    margin-left: 0.75rem;
  }

  .submenu-item {
    font-size: 0.8125rem;
    padding: 0.4375rem 0.5rem;
  }

  .nav-badge {
    background: #eff6ff;
    color: #2563eb;
    font-size: 0.6875rem;
    font-weight: 600;
    padding: 0.125rem 0.4375rem;
    border-radius: 9999px;
    margin-left: auto;
    border: 1px solid #bfdbfe;
  }
</style>
