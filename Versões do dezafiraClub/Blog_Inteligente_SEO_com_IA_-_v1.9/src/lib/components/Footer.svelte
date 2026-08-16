<script lang="ts">
  import { page } from '$app/stores';
  import { t } from '$lib/i18n';

  let {
    logo = '',
    siteName = 'Blog',
    description = '',
    copyright = '',
    adminEmail = '',
    location = '',
    showSocial = true,
    showContact = true,
    showNewsletter = false,
    language = ''
  } = $props();

  const lang = $derived(language || $page.data.language || 'pt');
  const currentYear = new Date().getFullYear();
  const email = $derived(
    adminEmail ||
      `contato@${siteName.split(/[|\-]/)[0].trim().toLowerCase().replace(/[^a-z0-9]/g, '')}.com`
  );
  const displayLocation = $derived(location || t(lang, 'footer.default_location'));

  const links = $derived({
    explore: [
      { label: t(lang, 'nav.home'), href: '/' },
      { label: t(lang, 'nav.categories'), href: '/categories' },
      { label: t(lang, 'nav.products'), href: '/products' },
      { label: 'Comunidade VIP', href: '/members/area' },
      { label: t(lang, 'nav.premium'), href: '/premium' },
      { label: t(lang, 'footer.rss'), href: '/rss.xml' },
      { label: t(lang, 'footer.sitemap'), href: '/sitemap.xml' }
    ],
    legal: [
      { label: t(lang, 'footer.privacy'), href: '/privacy' },
      { label: t(lang, 'footer.terms'), href: '/terms' },
      { label: t(lang, 'footer.cookies'), href: '/cookies' }
    ],
    social: [
      { name: 'Twitter', href: '', icon: 'twitter' },
      { name: 'Facebook', href: '', icon: 'facebook' },
      { name: 'Instagram', href: '', icon: 'instagram' },
      { name: 'YouTube', href: '', icon: 'youtube' }
    ]
  });

  const socialIcons: Record<string, string> = {
    twitter:
      'M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z',
    facebook:
      'M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z',
    instagram:
      'M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z',
    youtube:
      'M23.495 6.205a3.007 3.007 0 00-2.088-2.088c-1.87-.501-9.396-.501-9.396-.501s-7.507-.01-9.396.501A3.007 3.007 0 00.527 6.205a31.247 31.247 0 00-.522 5.805 31.247 31.247 0 00.522 5.783 3.007 3.007 0 002.088 2.088c1.868.502 9.396.502 9.396.502s7.506 0 9.396-.502a3.007 3.007 0 002.088-2.088 31.247 31.247 0 00.5-5.783 31.247 31.247 0 00-.5-5.805zM9.609 15.601V8.408l6.264 3.602z'
  };
</script>

<footer class="footer">
  <div class="footer-container">
    <div class="footer-main">
      <div class="footer-brand">
        <a href="/" class="footer-logo">
          {#if logo}
            <img src={logo} alt={siteName} class="logo-img" />
          {:else}
            <svg class="logo-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 19l7-7 3 3-7 7-3-3z" />
              <path d="M18 13l-1.5-7.5L2 2l3.5 14.5L13 18l5-5z" />
              <path d="M2 2l7.586 7.586" />
              <circle cx="11" cy="11" r="2" />
            </svg>
          {/if}
          <span>{siteName}</span>
        </a>

        {#if description}
          <p class="footer-description">{description}</p>
        {/if}

        {#if showSocial && links.social.some((s) => Boolean(s.href))}
          <div class="footer-social">
            {#each links.social.filter((s) => Boolean(s.href)) as social}
              <a href={social.href} class="social-link" aria-label={social.name} title={social.name}>
                <svg viewBox="0 0 24 24" fill="currentColor">
                  <path d={socialIcons[social.icon] || ''} />
                </svg>
              </a>
            {/each}
          </div>
        {/if}
      </div>

      <div class="footer-links">
        <div class="footer-col">
          <h4 class="footer-heading">{t(lang, 'footer.explore')}</h4>
          <ul class="footer-list">
            {#each links.explore as link}
              <li>
                <a href={link.href} class="footer-link">{link.label}</a>
              </li>
            {/each}
          </ul>
        </div>

        <div class="footer-col">
          <h4 class="footer-heading">{t(lang, 'footer.legal')}</h4>
          <ul class="footer-list">
            {#each links.legal as link}
              <li>
                <a href={link.href} class="footer-link">{link.label}</a>
              </li>
            {/each}
          </ul>
        </div>

        {#if showContact}
          <div class="footer-col">
            <h4 class="footer-heading">{t(lang, 'footer.contact')}</h4>
            <ul class="footer-list contact-list">
              <li>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" />
                  <polyline points="22,6 12,13 2,6" />
                </svg>
                <a class="footer-link" href={`mailto:${email}`}>{email}</a>
              </li>
              <li>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z" />
                  <circle cx="12" cy="10" r="3" />
                </svg>
                <span>{displayLocation}</span>
              </li>
            </ul>
          </div>
        {/if}
      </div>
    </div>

    <div class="footer-bottom">
      <p class="copyright">
        &copy; {currentYear} {siteName}. {copyright || t(lang, 'common.all_rights')}
      </p>

      <div class="footer-badges">
        <span class="badge">{t(lang, 'common.made_with_svelte')}</span>
      </div>
    </div>
  </div>
</footer>

<style>
  .footer {
    background: #1f2937;
    color: #d1d5db;
    margin-top: auto;
  }

  .footer-container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 20px;
  }

  .footer-main {
    display: grid;
    grid-template-columns: 1fr 2fr;
    gap: 60px;
    padding: 60px 0 40px;
  }

  .footer-brand {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .footer-logo {
    display: flex;
    align-items: center;
    gap: 10px;
    text-decoration: none;
    color: white;
    font-weight: 700;
    font-size: 1.25rem;
  }

  .logo-img {
    height: 32px;
    width: auto;
  }

  .logo-icon {
    width: 28px;
    height: 28px;
  }

  .footer-description {
    font-size: 0.9rem;
    line-height: 1.6;
    color: #9ca3af;
    margin: 0;
  }

  .footer-social {
    display: flex;
    gap: 12px;
  }

  .social-link {
    width: 36px;
    height: 36px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 8px;
    background: rgba(255, 255, 255, 0.08);
    color: #d1d5db;
    transition: background 0.2s, color 0.2s;
  }

  .social-link:hover {
    background: rgba(255, 255, 255, 0.15);
    color: white;
  }

  .social-link svg {
    width: 18px;
    height: 18px;
  }

  .footer-links {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 32px;
  }

  .footer-heading {
    color: white;
    font-size: 0.85rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin: 0 0 16px;
  }

  .footer-list {
    list-style: none;
    padding: 0;
    margin: 0;
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .footer-link {
    color: #9ca3af;
    text-decoration: none;
    font-size: 0.9rem;
    transition: color 0.2s;
  }

  .footer-link:hover {
    color: white;
  }

  .contact-list li {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    font-size: 0.9rem;
    color: #9ca3af;
  }

  .contact-list svg {
    width: 16px;
    height: 16px;
    flex-shrink: 0;
    margin-top: 2px;
  }

  .footer-bottom {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px 0;
    border-top: 1px solid rgba(255, 255, 255, 0.08);
    gap: 16px;
    flex-wrap: wrap;
  }

  .copyright {
    margin: 0;
    font-size: 0.85rem;
    color: #6b7280;
  }

  .badge {
    font-size: 0.75rem;
    color: #9ca3af;
    background: rgba(255, 255, 255, 0.06);
    padding: 4px 10px;
    border-radius: 999px;
  }

  @media (max-width: 768px) {
    .footer-main {
      grid-template-columns: 1fr;
      gap: 40px;
      padding: 40px 0 24px;
    }

    .footer-links {
      grid-template-columns: 1fr 1fr;
    }
  }

  @media (max-width: 480px) {
    .footer-links {
      grid-template-columns: 1fr;
    }
  }
</style>
