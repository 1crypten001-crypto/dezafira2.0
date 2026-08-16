<script lang="ts">
  export type HeaderLink = { id?: string; label: string; href?: string };

  let {
    logo = '',
    links = [] as HeaderLink[],
    ctaText = '',
    ctaHref = '#',
    showCta = true,
    maxWidth = '1200px',
    sticky = false
  }: {
    logo?: string;
    links?: HeaderLink[];
    ctaText?: string;
    ctaHref?: string;
    showCta?: boolean;
    maxWidth?: string;
    sticky?: boolean;
  } = $props();

  const visibleLinks = $derived((links || []).filter((l) => (l?.label || '').trim()));
</script>

<header class="lp-page-header" class:sticky>
  <div class="lp-page-header-inner" style:max-width={maxWidth}>
    {#if logo}
      <div class="lp-logo">
        <span class="lp-logo-dot" aria-hidden="true">●</span>
        <span class="lp-logo-text">{logo}</span>
      </div>
    {:else}
      <div class="lp-logo placeholder"></div>
    {/if}

    <nav class="lp-nav" aria-label="Landing navigation">
      {#each visibleLinks as link (link.id || link.label)}
        <a href={link.href || '#'} class="lp-nav-link">{link.label}</a>
      {/each}
      {#if showCta && ctaText}
        <a href={ctaHref || '#'} class="lp-nav-cta">{ctaText}</a>
      {/if}
    </nav>
  </div>
</header>

<style>
  .lp-page-header {
    width: 100%;
    border-bottom: 1px solid #f1f5f9;
    background: #ffffff;
    box-sizing: border-box;
  }

  .lp-page-header.sticky {
    position: sticky;
    top: 0;
    z-index: 40;
  }

  .lp-page-header-inner {
    margin: 0 auto;
    min-height: 60px;
    padding: 0 1.25rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 1rem;
    width: 100%;
    box-sizing: border-box;
  }

  .lp-logo {
    font-weight: 800;
    color: #0f172a;
    display: flex;
    align-items: center;
    gap: 0.375rem;
    font-size: 0.95rem;
    min-width: 0;
  }

  .lp-logo.placeholder {
    min-width: 1rem;
  }

  .lp-logo-dot {
    color: #111827;
    font-size: 1.25rem;
    line-height: 1;
  }

  .lp-logo-text {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .lp-nav {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    justify-content: flex-end;
    gap: 0.75rem 1.25rem;
    color: #475569;
    font-weight: 500;
    font-size: 0.875rem;
  }

  .lp-nav-link {
    color: inherit;
    text-decoration: none;
    white-space: nowrap;
  }

  .lp-nav-link:hover {
    color: #0f172a;
  }

  .lp-nav-cta {
    background: #111827;
    color: #ffffff;
    padding: 0.5rem 1rem;
    border-radius: 9999px;
    font-weight: 600;
    text-decoration: none;
    white-space: nowrap;
  }

  .lp-nav-cta:hover {
    filter: brightness(1.08);
  }

  @media (max-width: 640px) {
    .lp-page-header-inner {
      flex-direction: column;
      align-items: flex-start;
      padding-top: 0.75rem;
      padding-bottom: 0.75rem;
    }

    .lp-nav {
      width: 100%;
      justify-content: flex-start;
    }
  }
</style>
