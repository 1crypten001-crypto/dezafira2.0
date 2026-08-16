<script lang="ts">
  import { page } from '$app/stores';
  import { t } from '$lib/i18n';
  import LandingBlockTree from '$lib/components/LandingBlockTree.svelte';
  import LandingPageHeader from '$lib/components/LandingPageHeader.svelte';

  let { data } = $props();
  const lang = $derived($page.data.language || 'pt');

  const blocks = $derived.by(() => {
    try {
      return data.landingPage.content ? JSON.parse(data.landingPage.content) : [];
    } catch {
      return [];
    }
  });

  const settings = $derived.by(() => {
    try {
      return data.landingPage.settings ? JSON.parse(data.landingPage.settings) : {};
    } catch {
      return {};
    }
  });

  const seoTitle = $derived(settings.seoTitle || data.landingPage.title);
  const seoDesc = $derived(settings.seoDesc || data.landingPage.title);
  const socialImage = $derived(settings.socialImage || '');
  const containerWidth = $derived(settings.containerWidth || '1200px');
  const backgroundColor = $derived(settings.backgroundColor || '#ffffff');
  const textColor = $derived(settings.textColor || '#111827');
  const isDraft = $derived(data.landingPage.status === 'draft');

  const showHeader = $derived(settings.showHeader === true || settings.showHeader === 1);
  const headerLogo = $derived(settings.headerLogo || '');
  const headerLinks = $derived(Array.isArray(settings.headerLinks) ? settings.headerLinks : []);
  const headerCtaEnabled = $derived(settings.headerCtaEnabled !== false && settings.headerCtaEnabled !== 0);
  const headerCtaText = $derived(settings.headerCtaText || '');
  const headerCtaHref = $derived(settings.headerCtaHref || '#');

  const absoluteOgImage = $derived.by(() => {
    if (!socialImage) return '';
    if (socialImage.startsWith('http')) return socialImage;
    const origin = $page.url.origin;
    return `${origin}${socialImage.startsWith('/') ? '' : '/'}${socialImage}`;
  });
</script>

<svelte:head>
  <title>{seoTitle}</title>
  <meta name="description" content={seoDesc} />
  {#if isDraft}
    <meta name="robots" content="noindex, nofollow" />
  {/if}

  <meta property="og:title" content={seoTitle} />
  <meta property="og:description" content={seoDesc} />
  <meta property="og:type" content="website" />
  <meta property="og:url" content={$page.url.href} />
  {#if absoluteOgImage}
    <meta property="og:image" content={absoluteOgImage} />
    <meta name="twitter:image" content={absoluteOgImage} />
  {/if}

  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content={seoTitle} />
  <meta name="twitter:description" content={seoDesc} />
</svelte:head>

{#if isDraft}
  <div class="draft-banner" role="status">
    <span>{t(lang, 'admin.landing_pages.builder.draft_preview')}</span>
    <span class="dot">·</span>
    <span>{t(lang, 'admin.landing_pages.builder.draft_admin_only')}</span>
  </div>
{/if}

<div
  class="landing-page-public-root"
  style:background-color={backgroundColor}
  style:color={textColor}
>
  {#if showHeader && (headerLogo || headerLinks.length || (headerCtaEnabled && headerCtaText))}
    <LandingPageHeader
      logo={headerLogo}
      links={headerLinks}
      ctaText={headerCtaText}
      ctaHref={headerCtaHref}
      showCta={headerCtaEnabled}
      maxWidth={containerWidth}
      sticky={true}
    />
  {/if}
  <LandingBlockTree {blocks} {containerWidth} {lang} />
</div>

<style>
  :global(body) {
    margin: 0;
    padding: 0;
  }

  .landing-page-public-root {
    min-height: 100dvh;
    font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    line-height: 1.5;
    -webkit-font-smoothing: antialiased;
  }

  .draft-banner {
    position: sticky;
    top: 0;
    z-index: 50;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    background: linear-gradient(90deg, #f59e0b, #d97706);
    color: #111;
    font-size: 0.8rem;
    font-weight: 700;
    letter-spacing: 0.02em;
    text-transform: uppercase;
  }

  .draft-banner .dot {
    opacity: 0.6;
  }
</style>
