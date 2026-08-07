<script lang="ts">
  import { page } from '$app/stores';
  import { t } from '$lib/i18n';

  let {
    variant = 'page',
    showPhone = true,
    showSubject = true
  } = $props();

  const lang = $derived($page.data.language || 'pt');

  let name = $state('');
  let email = $state('');
  let phone = $state('');
  let subject = $state('');
  let message = $state('');

  let submitting = $state(false);
  let submitted = $state(false);
  let error = $state<string | null>(null);

  const subjects = $derived([
    t(lang, 'contact.subject_general'),
    t(lang, 'contact.subject_support'),
    t(lang, 'contact.subject_partners'),
    t(lang, 'contact.subject_suggestions'),
    t(lang, 'contact.subject_bug'),
    t(lang, 'contact.subject_other')
  ]);

  async function handleSubmit(e: Event) {
    e.preventDefault();
    submitting = true;
    error = null;

    try {
      const response = await fetch('/api/contact', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, email, phone, subject, message })
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || t(lang, 'contact.error_send'));
      }

      submitted = true;
      name = '';
      email = '';
      phone = '';
      subject = '';
      message = '';
    } catch (e: any) {
      error = e.message || t(lang, 'contact.error_unknown');
    } finally {
      submitting = false;
    }
  }
</script>

<div class="contact-form variant-{variant}">
  {#if submitted}
    <div class="contact-success">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M22 11.08V12a10 10 0 11-5.93-9.14"/>
        <polyline points="22,4 12,14.01 9,11.01"/>
      </svg>
      <h3>{t(lang, 'contact.success_title')}</h3>
      <p>{t(lang, 'contact.success_body')}</p>
      <button onclick={() => submitted = false} class="btn-reset">
        {t(lang, 'contact.send_another')}
      </button>
    </div>
  {:else}
    {#if error}
      <div class="contact-error">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/>
          <line x1="12" y1="8" x2="12" y2="12"/>
          <line x1="12" y1="16" x2="12.01" y2="16"/>
        </svg>
        {error}
      </div>
    {/if}

    <form onsubmit={handleSubmit}>
      <div class="form-row">
        <div class="form-group">
          <label for="name" class="form-label">{t(lang, 'contact.label_name')}</label>
          <input type="text" id="name" bind:value={name} required class="form-input" placeholder={t(lang, 'contact.ph_name')} />
        </div>
        <div class="form-group">
          <label for="email" class="form-label">{t(lang, 'contact.label_email')}</label>
          <input type="email" id="email" bind:value={email} required class="form-input" placeholder={t(lang, 'contact.ph_email')} />
        </div>
      </div>

      {#if showPhone}
        <div class="form-group">
          <label for="phone" class="form-label">{t(lang, 'contact.label_phone')}</label>
          <input type="tel" id="phone" bind:value={phone} class="form-input" placeholder={t(lang, 'contact.ph_phone')} />
        </div>
      {/if}

      {#if showSubject}
        <div class="form-group">
          <label for="subject" class="form-label">{t(lang, 'contact.label_subject')}</label>
          <select id="subject" bind:value={subject} required class="form-select">
            <option value="">{t(lang, 'contact.ph_subject')}</option>
            {#each subjects as s}
              <option value={s}>{s}</option>
            {/each}
          </select>
        </div>
      {/if}

      <div class="form-group">
        <label for="message" class="form-label">{t(lang, 'contact.label_message')}</label>
        <textarea id="message" bind:value={message} required class="form-textarea" rows="5" placeholder={t(lang, 'contact.ph_message')}></textarea>
      </div>

      <button type="submit" class="form-submit" disabled={submitting}>
        {#if submitting}
          <svg class="spinner" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10" stroke-dasharray="60" stroke-dashoffset="60"/>
          </svg>
          {t(lang, 'contact.sending')}
        {:else}
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="22" y1="2" x2="11" y2="13"/>
            <polygon points="22,2 15,22 11,13 2,9"/>
          </svg>
          {t(lang, 'contact.submit')}
        {/if}
      </button>
    </form>
  {/if}
</div>

<style>
  .contact-form {
    width: 100%;
  }

  .contact-success {
    text-align: center;
    padding: 40px 20px;
    color: #10b981;
  }

  .contact-success svg {
    margin-bottom: 16px;
  }

  .contact-success h3 {
    font-size: 24px;
    margin: 0 0 8px 0;
    color: #1f2937;
  }

  .contact-success p {
    color: #6b7280;
    margin: 0 0 24px 0;
  }

  .btn-reset {
    background: none;
    border: 1px solid #d1d5db;
    padding: 8px 16px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 14px;
    color: #6b7280;
  }

  .btn-reset:hover {
    background: #f3f4f6;
  }

  .contact-error {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 12px 16px;
    background: #fef2f2;
    border: 1px solid #fecaca;
    border-radius: 8px;
    color: #dc2626;
    margin-bottom: 20px;
    font-size: 14px;
  }

  .form-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
  }

  @media (max-width: 640px) {
    .form-row {
      grid-template-columns: 1fr;
    }
  }

  .form-group {
    margin-bottom: 16px;
  }

  .form-label {
    display: block;
    font-size: 14px;
    font-weight: 500;
    color: #374151;
    margin-bottom: 6px;
  }

  .form-input,
  .form-select,
  .form-textarea {
    width: 100%;
    padding: 10px 14px;
    border: 1px solid #d1d5db;
    border-radius: 8px;
    font-size: 16px;
    transition: border-color 0.2s, box-shadow 0.2s;
    background: white;
  }

  .form-input:focus,
  .form-select:focus,
  .form-textarea:focus {
    outline: none;
    border-color: #4a90d9;
    box-shadow: 0 0 0 3px rgba(74, 144, 217, 0.1);
  }

  .form-textarea {
    resize: vertical;
    min-height: 120px;
  }

  .form-submit {
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    padding: 14px 24px;
    background: #4a90d9;
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 16px;
    font-weight: 500;
    cursor: pointer;
    transition: background 0.2s;
  }

  .form-submit:hover:not(:disabled) {
    background: #3a7bc8;
  }

  .form-submit:disabled {
    opacity: 0.7;
    cursor: not-allowed;
  }

  .spinner {
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }

  /* Variants */
  .variant-widget .form-row {
    grid-template-columns: 1fr;
  }

  .variant-widget .form-submit {
    padding: 12px 20px;
    font-size: 14px;
  }

  .variant-inline {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 16px;
  }

  .variant-inline .form-row {
    grid-column: 1 / -1;
  }
</style>