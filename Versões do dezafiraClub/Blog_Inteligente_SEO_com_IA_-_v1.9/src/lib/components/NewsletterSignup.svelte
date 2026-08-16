<script lang="ts">
  import { page } from '$app/stores';
  import { t } from '$lib/i18n';

  let {
    title = '',
    description = '',
    placeholder = '',
    buttonText = ''
  }: {
    title?: string;
    description?: string;
    placeholder?: string;
    buttonText?: string;
  } = $props();

  const lang = $derived($page.data.language || 'pt');
  const i18nTitle = $derived(title || t(lang, 'newsletter.title'));
  const i18nDescription = $derived(description || t(lang, 'newsletter.description'));
  const i18nPlaceholder = $derived(placeholder || t(lang, 'newsletter.placeholder'));
  const i18nButton = $derived(buttonText || t(lang, 'newsletter.button'));

  let email = $state('');
  let submitted = $state(false);
  let error = $state('');
  let loading = $state(false);

  async function handleSubmit(e: Event) {
    e.preventDefault();

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      error = t(lang, 'newsletter.invalid_email');
      return;
    }

    loading = true;
    error = '';

    try {
      const response = await fetch('/api/newsletter', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email })
      });

      const result = await response.json();

      if (result.success) {
        submitted = true;
        email = '';
      } else {
        error = result.error || t(lang, 'newsletter.error');
      }
    } catch {
      error = t(lang, 'newsletter.connection_error');
    } finally {
      loading = false;
    }
  }
</script>

<div class="newsletter-widget">
  {#if !submitted}
    <h3 class="newsletter-title">{i18nTitle}</h3>
    <p class="newsletter-description">{i18nDescription}</p>

    <form onsubmit={handleSubmit} class="newsletter-form">
      <div class="newsletter-input-wrapper">
        <input
          type="email"
          bind:value={email}
          class="newsletter-input"
          placeholder={i18nPlaceholder}
          required
          aria-label={t(lang, 'newsletter.email_aria')}
          disabled={loading}
        />
      </div>

      {#if error}
        <p class="newsletter-error">{error}</p>
      {/if}

      <button type="submit" class="newsletter-btn" disabled={loading}>
        {i18nButton}
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M5 12h14M12 5l7 7-7 7" />
        </svg>
      </button>
    </form>
  {:else}
    <div class="newsletter-success">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M20 6L9 17l-5-5" />
      </svg>
      <h4 class="success-title">{t(lang, 'newsletter.success_title')}</h4>
      <p class="success-message">{t(lang, 'newsletter.success_body')}</p>
    </div>
  {/if}
</div>

<style>
  .newsletter-widget {
    background: linear-gradient(135deg, var(--bg-secondary) 0%, var(--bg-tertiary) 100%);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-lg);
    padding: 1.5rem;
  }
  .newsletter-title {
    font-family: var(--font-sans);
    font-size: 1.125rem;
    font-weight: 700;
    margin-bottom: 0.5rem;
    color: var(--text-primary);
  }
  .newsletter-description {
    font-family: var(--font-sans);
    font-size: 0.875rem;
    color: var(--text-secondary);
    margin-bottom: 1.25rem;
    line-height: 1.5;
  }
  .newsletter-form {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }
  .newsletter-input {
    width: 100%;
    padding: 0.75rem 1rem;
    font-family: var(--font-sans);
    font-size: 0.875rem;
    border: 1px solid var(--border-color);
    border-radius: var(--radius-md);
    background: var(--bg-primary);
    color: var(--text-primary);
    outline: none;
  }
  .newsletter-input:focus {
    border-color: var(--text-primary);
    box-shadow: 0 0 0 3px rgba(42, 42, 42, 0.08);
  }
  .newsletter-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    width: 100%;
    padding: 0.75rem 1rem;
    font-family: var(--font-sans);
    font-size: 0.875rem;
    font-weight: 600;
    background: var(--text-primary);
    color: var(--bg-primary);
    border: none;
    border-radius: var(--radius-md);
    cursor: pointer;
  }
  .newsletter-btn:hover:not(:disabled) {
    filter: brightness(1.05);
  }
  .newsletter-btn:disabled {
    opacity: 0.7;
    cursor: not-allowed;
  }
  .newsletter-error {
    font-size: 0.75rem;
    color: #dc2626;
    margin: 0;
    padding: 0.5rem 0.75rem;
    background: #fef2f2;
    border: 1px solid #fecaca;
    border-radius: var(--radius-sm);
  }
  .newsletter-success {
    text-align: center;
    padding: 1.5rem 1rem;
  }
  .newsletter-success svg {
    color: #16a34a;
    margin-bottom: 1rem;
  }
  .success-title {
    font-size: 1.125rem;
    font-weight: 700;
    margin-bottom: 0.5rem;
    color: var(--text-primary);
  }
  .success-message {
    font-size: 0.875rem;
    color: var(--text-secondary);
    line-height: 1.5;
    margin: 0;
  }
</style>
