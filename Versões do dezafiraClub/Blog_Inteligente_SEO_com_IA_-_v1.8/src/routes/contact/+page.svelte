<script lang="ts">
  import { ContactForm, Breadcrumb, SocialShare } from '$lib/components';
  import { page } from '$app/stores';
  import { t } from '$lib/i18n';
  let { data } = $props();
  const lang = $derived($page.data.language || 'pt');

  const contactMethods = $derived([
    {
      icon: 'mail',
      title: t(lang, 'contact.method_email'),
      value: data.settings?.admin_email || 'contato@blog.com',
      description: t(lang, 'contact.method_email_desc')
    },
    {
      icon: 'phone',
      title: t(lang, 'contact.method_phone'),
      value: data.settings?.contact_phone || '',
      description: ''
    },
    {
      icon: 'location',
      title: t(lang, 'contact.method_location'),
      value: data.settings?.contact_location || t(lang, 'footer.default_location'),
      description: ''
    }
  ].filter((m) => m.value));

  const socialLinks = [
    { name: 'Twitter', href: '#', color: '#1da1f2' },
    { name: 'GitHub', href: '#', color: '#333' },
    { name: 'LinkedIn', href: '#', color: '#0a66c2' },
    { name: 'YouTube', href: '#', color: '#ff0000' }
  ];
</script>

<svelte:head>
  <title>{data.settings?.site_title || "Blog"} | {t(lang, 'contact.meta_title')}</title>
  <meta name="description" content={t(lang, 'contact.meta_desc')} />
</svelte:head>

<div class="contact-page">
  <div class="container">
    <!-- Header -->
    <header class="page-header">
      <Breadcrumb items={[
        { label: t(lang, 'contact.meta_title'), icon: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>' }
      ]} />
      
      <h1 class="page-title">{t(lang, 'contact.page_title')}</h1>
      <p class="page-subtitle">
        {t(lang, 'contact.page_subtitle')}
      </p>
    </header>

    <!-- Contact Methods -->
    <div class="contact-methods">
      {#each contactMethods as method}
        <div class="method-card">
          <div class="method-icon">
            {#if method.icon === 'mail'}
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
                <polyline points="22,6 12,13 2,6"/>
              </svg>
            {:else if method.icon === 'phone'}
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M22 16.92v3a2 2 0 01-2.18 2 19.79 19.79 0 01-8.63-3.07 19.5 19.5 0 01-6-6 19.79 19.79 0 01-3.07-8.67A2 2 0 014.11 2h3a2 2 0 012 1.72 12.84 12.84 0 00.7 2.81 2 2 0 01-.45 2.11L8.09 9.91a16 16 0 006 6l1.27-1.27a2 2 0 012.11-.45 12.84 12.84 0 002.81.7A2 2 0 0122 16.92z"/>
              </svg>
            {:else if method.icon === 'location'}
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z"/>
                <circle cx="12" cy="10" r="3"/>
              </svg>
            {/if}
          </div>
          <div class="method-info">
            <h3 class="method-title">{method.title}</h3>
            <span class="method-value">{method.value}</span>
            <span class="method-description">{method.description}</span>
          </div>
        </div>
      {/each}
    </div>

    <!-- Contact Form + Info -->
    <div class="contact-grid">
      <div class="form-section">
        <ContactForm />
      </div>
      
      <div class="info-section">
        <div class="faq-card">
          <h3 class="faq-title">Perguntas Frequentes</h3>
          <div class="faq-list">
            <div class="faq-item">
              <h4>Como posso contribuir com o blog?</h4>
              <p>Envie sua proposta de artigo pelo formulário acima.</p>
            </div>
            <div class="faq-item">
              <h4>Vocês oferecem suporte técnico?</h4>
              <p>Sim, respondemos dúvidas nos comentários dos posts.</p>
            </div>
            <div class="faq-item">
              <h4>Posso fazer guest posts?</h4>
              <p>Aceitamos colaboradores! Entre em contato.</p>
            </div>
          </div>
        </div>

        <div class="social-card">
          <h3 class="social-title">{t(lang, "contact.follow_us")}</h3>
          <div class="social-links">
            {#each socialLinks as social}
              <a 
                href={social.href} 
                class="social-link"
                style="--social-color: {social.color}"
                aria-label={social.name}
              >
                {#if social.name === 'Twitter'}
                  <svg viewBox="0 0 24 24" fill="currentColor">
                    <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
                  </svg>
                {:else if social.name === 'GitHub'}
                  <svg viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
                  </svg>
                {:else if social.name === 'LinkedIn'}
                  <svg viewBox="0 0 24 24" fill="currentColor">
                    <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
                  </svg>
                {:else if social.name === 'YouTube'}
                  <svg viewBox="0 0 24 24" fill="currentColor">
                    <path d="M23.495 6.205a3.007 3.007 0 00-2.088-2.088c-1.87-.501-9.396-.501-9.396-.501s-7.507-.01-9.396.501A3.007 3.007 0 00.527 6.205a31.247 31.247 0 00-.522 5.805 31.247 31.247 0 00.522 5.783 3.007 3.007 0 002.088 2.088c1.868.502 9.396.502 9.396.502s7.506 0 9.396-.502a3.007 3.007 0 002.088-2.088 31.247 31.247 0 00.5-5.783 31.247 31.247 0 00-.5-5.805zM9.609 15.601V8.408l6.264 3.602z"/>
                  </svg>
                {/if}
                <span>{social.name}</span>
              </a>
            {/each}
          </div>
        </div>

        <div class="response-time">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <polyline points="12,6 12,12 16,14"/>
          </svg>
          <span>Tempo médio de resposta: <strong>24 horas</strong></span>
        </div>
      </div>
    </div>
  </div>
</div>

<style>
  .contact-page {
    min-height: 100vh;
    padding: 40px 0 80px;
  }

  .container {
    max-width: 1100px;
    margin: 0 auto;
    padding: 0 20px;
  }

  /* Header */
  .page-header {
    text-align: center;
    margin-bottom: 48px;
  }

  .page-title {
    font-size: 36px;
    font-weight: 800;
    color: #1f2937;
    margin: 16px 0 8px;
  }

  .page-subtitle {
    font-size: 16px;
    color: #6b7280;
    margin: 0;
  }

  /* Contact Methods */
  .contact-methods {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 24px;
    margin-bottom: 60px;
  }

  .method-card {
    display: flex;
    align-items: flex-start;
    gap: 16px;
    padding: 24px;
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    transition: border-color 0.2s, box-shadow 0.2s;
  }

  .method-card:hover {
    border-color: #4a90d9;
    box-shadow: 0 4px 12px rgba(74, 144, 217, 0.1);
  }

  .method-icon {
    width: 48px;
    height: 48px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #eff6ff;
    border-radius: 12px;
    color: #4a90d9;
    flex-shrink: 0;
  }

  .method-icon svg {
    width: 24px;
    height: 24px;
  }

  .method-info {
    display: flex;
    flex-direction: column;
  }

  .method-title {
    font-size: 12px;
    font-weight: 600;
    text-transform: uppercase;
    color: #9ca3af;
    letter-spacing: 0.5px;
    margin: 0 0 4px;
  }

  .method-value {
    font-size: 16px;
    font-weight: 600;
    color: #1f2937;
    margin: 0 0 2px;
  }

  .method-description {
    font-size: 13px;
    color: #9ca3af;
  }

  /* Contact Grid */
  .contact-grid {
    display: grid;
    grid-template-columns: 1fr 400px;
    gap: 40px;
    align-items: start;
  }

  .form-section {
    background: white;
    padding: 32px;
    border-radius: 16px;
    border: 1px solid #e5e7eb;
  }

  .info-section {
    display: flex;
    flex-direction: column;
    gap: 24px;
  }

  /* FAQ Card */
  .faq-card,
  .social-card {
    background: white;
    padding: 24px;
    border-radius: 12px;
    border: 1px solid #e5e7eb;
  }

  .faq-title,
  .social-title {
    font-size: 18px;
    font-weight: 600;
    color: #1f2937;
    margin: 0 0 20px;
  }

  .faq-list {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .faq-item {
    padding-bottom: 16px;
    border-bottom: 1px solid #f3f4f6;
  }

  .faq-item:last-child {
    padding-bottom: 0;
    border-bottom: none;
  }

  .faq-item h4 {
    font-size: 14px;
    font-weight: 600;
    color: #374151;
    margin: 0 0 4px;
  }

  .faq-item p {
    font-size: 13px;
    color: #6b7280;
    margin: 0;
  }

  /* Social Links */
  .social-links {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
  }

  .social-link {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 14px;
    background: #f9fafb;
    border-radius: 8px;
    text-decoration: none;
    color: #374151;
    font-size: 14px;
    font-weight: 500;
    transition: all 0.2s;
  }

  .social-link:hover {
    background: var(--social-color);
    color: white;
  }

  .social-link svg {
    width: 18px;
    height: 18px;
  }

  /* Response Time */
  .response-time {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 16px 20px;
    background: #eff6ff;
    border-radius: 10px;
    color: #4a90d9;
    font-size: 14px;
  }

  .response-time svg {
    width: 20px;
    height: 20px;
    flex-shrink: 0;
  }

  .response-time strong {
    font-weight: 600;
  }

  /* Responsive */
  @media (max-width: 900px) {
    .contact-methods {
      grid-template-columns: 1fr;
    }

    .contact-grid {
      grid-template-columns: 1fr;
    }

    .info-section {
      order: -1;
    }
  }

  @media (max-width: 640px) {
    .method-card {
      padding: 16px;
    }

    .form-section {
      padding: 20px;
    }

    .social-links {
      grid-template-columns: 1fr;
    }

    .page-title {
      font-size: 28px;
    }
  }
</style>