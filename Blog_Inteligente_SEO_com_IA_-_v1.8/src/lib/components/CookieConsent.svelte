<script lang="ts">
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import { t } from '$lib/i18n';

  let {
    position = 'bottom',
    title = '',
    message = '',
    acceptText = '',
    declineText = '',
    policyText = '',
    policyUrl = '/privacy',
    autoShow = true,
    delay = 2000
  } = $props();

  const lang = $derived($page.data.language || 'pt');
  const i18nTitle = $derived(title || t(lang, 'cookie.title'));
  const i18nMessage = $derived(message || t(lang, 'cookie.message'));
  const i18nAccept = $derived(acceptText || t(lang, 'cookie.accept'));
  const i18nDecline = $derived(declineText || t(lang, 'cookie.decline'));
  const i18nPolicy = $derived(policyText || t(lang, 'cookie.policy'));

  let visible = $state(false);
  let showDetails = $state(false);

  const COOKIE_KEY = 'cookie_consent';

  onMount(() => {
    const consent = localStorage.getItem(COOKIE_KEY);
    if (!consent && autoShow) {
      setTimeout(() => {
        visible = true;
      }, delay);
    }
  });

  function accept() {
    saveConsent('accepted');
    visible = false;
  }

  function decline() {
    saveConsent('declined');
    visible = false;
  }

  function saveConsent(value: string) {
    localStorage.setItem(COOKIE_KEY, value);
    window.dispatchEvent(
      new CustomEvent('cookie-consent', {
        detail: { consent: value }
      })
    );
  }
</script>

{#if visible}
  <div class="cookie-consent position-{position}" role="dialog" aria-label={i18nTitle}>
    <div class="cookie-content">
      <div class="cookie-header">
        <svg class="cookie-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10" />
          <path d="M9.09 9a3 3 0 015.83 1c0 2-3 3-3 3" />
          <line x1="12" y1="17" x2="12.01" y2="17" />
        </svg>
        <h3 class="cookie-title">{i18nTitle}</h3>
      </div>

      <p class="cookie-message">{i18nMessage}</p>

      {#if showDetails}
        <div class="cookie-details">
          <p>{t(lang, 'cookie.details_intro')}</p>
          <ul>
            <li>{t(lang, 'cookie.detail_1')}</li>
            <li>{t(lang, 'cookie.detail_2')}</li>
            <li>{t(lang, 'cookie.detail_3')}</li>
          </ul>
        </div>
      {/if}

      <div class="cookie-actions">
        <button class="cookie-btn decline" onclick={decline}>{i18nDecline}</button>

        <div class="cookie-secondary">
          <button class="cookie-link" onclick={() => (showDetails = !showDetails)}>
            {showDetails ? t(lang, 'cookie.hide_details') : t(lang, 'cookie.more_details')}
          </button>
          <a href={policyUrl} class="cookie-link">{i18nPolicy}</a>
        </div>

        <button class="cookie-btn accept" onclick={accept}>{i18nAccept}</button>
      </div>
    </div>

    <button class="cookie-close" onclick={decline} aria-label={t(lang, 'cookie.close')}>
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <line x1="18" y1="6" x2="6" y2="18" />
        <line x1="6" y1="6" x2="18" y2="18" />
      </svg>
    </button>
  </div>
{/if}

<style>
  .cookie-consent {
    position: fixed;
    left: 16px;
    right: 16px;
    z-index: 9999;
    background: white;
    border-radius: 12px;
    box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.15);
    animation: slideUp 0.3s ease;
    max-width: 600px;
    margin: 0 auto;
  }
  .position-bottom {
    bottom: 16px;
  }
  .position-top {
    top: 16px;
  }
  @keyframes slideUp {
    from {
      opacity: 0;
      transform: translateY(20px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
  .cookie-content {
    padding: 20px 24px;
  }
  .cookie-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 12px;
  }
  .cookie-icon {
    width: 24px;
    height: 24px;
    color: #f59e0b;
    flex-shrink: 0;
  }
  .cookie-title {
    font-size: 16px;
    font-weight: 600;
    color: #1f2937;
    margin: 0;
  }
  .cookie-message {
    font-size: 14px;
    color: #6b7280;
    margin: 0 0 16px 0;
    line-height: 1.6;
  }
  .cookie-details {
    background: #f9fafb;
    padding: 12px 16px;
    border-radius: 8px;
    margin-bottom: 16px;
    font-size: 13px;
    color: #6b7280;
  }
  .cookie-details p {
    margin: 0 0 8px 0;
    font-weight: 500;
    color: #374151;
  }
  .cookie-details ul {
    margin: 0;
    padding-left: 20px;
  }
  .cookie-details li {
    margin-bottom: 4px;
  }
  .cookie-actions {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 12px;
  }
  .cookie-btn {
    padding: 10px 20px;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
    border: none;
  }
  .cookie-btn.accept {
    background: #4a90d9;
    color: white;
  }
  .cookie-btn.accept:hover {
    background: #3a7bc8;
  }
  .cookie-btn.decline {
    background: white;
    border: 1px solid #d1d5db;
    color: #6b7280;
  }
  .cookie-btn.decline:hover {
    background: #f3f4f6;
  }
  .cookie-secondary {
    display: flex;
    gap: 16px;
    flex: 1;
  }
  .cookie-link {
    font-size: 13px;
    color: #6b7280;
    text-decoration: underline;
    background: none;
    border: none;
    cursor: pointer;
  }
  .cookie-link:hover {
    color: #374151;
  }
  .cookie-close {
    position: absolute;
    top: 12px;
    right: 12px;
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: none;
    border: none;
    border-radius: 50%;
    cursor: pointer;
    color: #9ca3af;
  }
  .cookie-close:hover {
    background: #f3f4f6;
    color: #6b7280;
  }
  .cookie-close svg {
    width: 18px;
    height: 18px;
  }
  @media (max-width: 480px) {
    .cookie-actions {
      flex-direction: column;
      align-items: stretch;
    }
    .cookie-btn {
      width: 100%;
    }
    .cookie-secondary {
      order: -1;
      justify-content: center;
      margin-bottom: 8px;
    }
  }
</style>
