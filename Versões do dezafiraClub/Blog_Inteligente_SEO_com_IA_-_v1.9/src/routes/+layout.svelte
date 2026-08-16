<script lang="ts">
  import "../app.css";
  import Header from '$lib/components/Header.svelte';
  import Footer from '$lib/components/Footer.svelte';
  import CookieConsent from '$lib/components/CookieConsent.svelte';
  import Toast from '$lib/components/Toast.svelte';
  import StoriesBar from '$lib/components/StoriesBar.svelte';
  import { page } from '$app/stores';
  import { htmlLang } from '$lib/i18n';

  let { data, children } = $props();
  const siteTitle = $derived(data?.settings?.site_title || "Blog");
  const siteLogo = $derived(data?.settings?.site_logo || "/favicon.svg");
  const siteFavicon = $derived(data?.settings?.site_favicon || data?.settings?.site_logo || "/favicon.svg");
  const language = $derived(data?.language || 'pt');

  const isAdmin = $derived($page.url.pathname.startsWith('/admin'));
  // Landing pages (/p/*) render full-bleed without blog chrome (header/footer)
  const isLandingPage = $derived($page.url.pathname.startsWith('/p/'));

  $effect(() => {
    if (typeof document === 'undefined') return;
    document.documentElement.lang = htmlLang(language);
  });

  const whatsappEnable = $derived(data?.settings?.whatsapp_enable === '1');
  const whatsappNumber = $derived(data?.settings?.whatsapp_number || "");
  const whatsappMessage = $derived(data?.settings?.whatsapp_message || "");

  const whatsappUrl = $derived(
    whatsappNumber
      ? `https://wa.me/${whatsappNumber.replace(/\D/g, '')}${whatsappMessage ? `?text=${encodeURIComponent(whatsappMessage)}` : ''}`
      : ''
  );

  // Load Google Fonts asynchronously via DOM injection to avoid Rollup TS cast issues.
  // This prevents render-blocking while keeping the font loaded.
  $effect(() => {
    const FONT_URL = 'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap';
    // Avoid duplicate injection
    if (document.querySelector(`link[href="${FONT_URL}"]`)) return;
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = FONT_URL;
    link.media = 'print';
    link.onload = () => { link.media = 'all'; };
    document.head.appendChild(link);
  });

  // Inicialização do Microsoft Clarity no lado do cliente
  $effect(() => {
    const clarityProjectId = data?.settings?.microsoft_clarity_project_id;
    if (clarityProjectId && typeof window !== 'undefined') {
      import('@microsoft/clarity').then(({ default: Clarity }) => {
        Clarity.init(clarityProjectId);
        
        let userIdStr = '';
        let friendlyName = '';
        let userRole = 'anonymous';

        if (data?.user) {
          userIdStr = String(data.user.id);
          friendlyName = data.user.name || data.user.username || '';
          userRole = data.user.role || 'member';
        }

        if (userIdStr) {
          Clarity.identify(userIdStr, undefined, undefined, friendlyName);
        }
        Clarity.setTag('user_role', userRole);
      }).catch(err => {
        console.error('Failed to load Clarity:', err);
      });
    }
  });
</script>

<svelte:head>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link rel="icon" href={siteFavicon} />
  <link rel="apple-touch-icon" href={siteFavicon} />
  {#if !isAdmin && data?.settings?.custom_head_script}
    {@html data.settings.custom_head_script}
  {/if}
</svelte:head>

{#if isAdmin || isLandingPage}
  {@render children()}
{:else}
  <div class="app-layout">
    <Header
      logo={data?.settings?.site_logo || ""}
      siteName={data?.settings?.site_title || "Blog"}
      user={data?.user}
      enableMemberLogin={data?.settings?.enable_member_login === '1'}
      defaultTheme={data?.settings?.default_theme || "light"}
      language={data?.language}
    />

    {#if data?.settings?.enable_web_stories_bar === '1' && data?.webStories?.length > 0}
      <StoriesBar stories={data.webStories} language={language} />
    {/if}

    <main
      class="main-content"
      class:has-stories={data?.settings?.enable_web_stories_bar === '1' && data?.webStories?.length > 0}
    >
      {@render children()}
    </main>

    <Footer
      logo={data?.settings?.site_logo || ""}
      siteName={data?.settings?.site_title || "Blog"}
      description={data?.settings?.site_description || ""}
      copyright={data?.settings?.footer_text || ""}
      adminEmail={data?.settings?.admin_email || ""}
      language={language}
    />

    <!-- Global Components — strings come from i18n via site language -->
    <CookieConsent />

    <Toast />

    {#if whatsappEnable && whatsappUrl}
      <a
        href={whatsappUrl}
        target="_blank"
        rel="noopener noreferrer"
        class="whatsapp-float-btn"
        aria-label="Fale conosco pelo WhatsApp"
      >
        <span class="whatsapp-pulse-ring"></span>
        <svg viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
          <path d="M12.012 2C6.48 2 2 6.48 2 12.012c0 1.764.456 3.48 1.332 5.004L2 22l5.124-1.344c1.476.804 3.144 1.236 4.884 1.236 5.532 0 10.012-4.48 10.012-10.012C22.02 6.48 17.54 2 12.012 2zm6.204 14.352c-.252.708-1.464 1.38-2.004 1.44-.48.06-.96.276-3.084-.552-2.7-1.056-4.428-3.792-4.56-3.972-.132-.18-.996-1.32-.996-2.52 0-1.2.624-1.788.852-2.04.228-.252.492-.312.66-.312.168 0 .336.006.48.012.156.006.366-.06.576.444.216.528.744 1.812.81 1.944.066.132.108.288.018.468-.09.18-.132.288-.264.444-.132.156-.276.348-.396.468-.132.132-.27.276-.114.54.156.264.696 1.152 1.488 1.86 1.02.912 1.872 1.188 2.136 1.32.264.132.42.108.576-.072.156-.18.672-.78.852-1.044.18-.264.36-.216.612-.12.252.096 1.608.756 1.884.888.276.132.456.198.522.312.066.114.066.66-.186 1.368z"/>
        </svg>
      </a>
    {/if}

    {#if data?.settings?.custom_body_script}
      {@html data.settings.custom_body_script}
    {/if}
  </div>
{/if}

<style>
  .app-layout {
    display: flex;
    flex-direction: column;
    min-height: 100vh;
  }

  .main-content {
    flex: 1;
    padding-top: 3rem;
  }

  /* Stories already add vertical space — keep hero tight below bubbles */
  .main-content.has-stories {
    padding-top: 0.75rem;
  }

  .whatsapp-float-btn {
    position: fixed;
    bottom: 24px;
    left: 24px;
    width: 52px;
    height: 52px;
    background: #25d366;
    color: #fff;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 4px 16px rgba(37, 211, 102, 0.35);
    z-index: 9999;
    cursor: pointer;
    text-decoration: none;
    transition: transform 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275), background-color 0.3s, box-shadow 0.3s;
  }

  .whatsapp-float-btn:hover {
    transform: scale(1.1) rotate(8deg);
    background-color: #22c35e;
    box-shadow: 0 6px 20px rgba(37, 211, 102, 0.5);
  }

  .whatsapp-pulse-ring {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    border-radius: 50%;
    border: 2px solid #25d366;
    animation: whatsapp-pulse-anim 2s infinite ease-in-out;
    pointer-events: none;
    z-index: -1;
  }

  @keyframes whatsapp-pulse-anim {
    0% {
      transform: scale(1);
      opacity: 0.8;
    }
    50% {
      opacity: 0.5;
    }
    100% {
      transform: scale(1.4);
      opacity: 0;
    }
  }

  @media (max-width: 640px) {
    .whatsapp-float-btn {
      bottom: 20px;
      left: 20px;
      width: 48px;
      height: 48px;
    }
  }
</style>
