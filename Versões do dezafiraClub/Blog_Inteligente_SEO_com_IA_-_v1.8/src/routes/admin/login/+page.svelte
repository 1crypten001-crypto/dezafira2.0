<script lang="ts">
  import { page } from "$app/stores";
  import { t, formatDate as fmtDate, formatMoney } from "$lib/i18n";
  import { enhance } from "$app/forms";

  const lang = $derived($page.data.language || 'pt');

let { form }: { form?: { error: string; remaining?: number; waitSeconds?: number } } = $props();
  let loading = $state(false);
  let waitSeconds = $derived(form?.waitSeconds || 0);
  let remaining = $derived(form?.remaining ?? undefined);
</script>

<svelte:head>
  <title>{t(lang, "admin.login.title")}</title>
</svelte:head>

<div class="login-page">
  <main class="login-main">
    <div class="login-content">
      <div class="login-intro">
        <h1>{t(lang, "admin.login.heading")}</h1>
        <p>
          {t(lang, "admin.login.subtitle")}
        </p>
      </div>

      <div class="login-form-wrapper">
        <h2 class="form-title">{t(lang, "admin.login.form_title")}</h2>

        {#if form?.error}
          <div class="message" class:message-error={waitSeconds === 0} class:message-warning={waitSeconds > 0}>
            {form.error}
            {#if remaining !== undefined && waitSeconds === 0}
              <span class="remaining">{t(lang, "admin.ui.remaining", { n: remaining })}</span>
            {/if}
          </div>
        {/if}

        <form
          method="POST"
          action="?/login"
          use:enhance
        >
          <div class="form-group">
            <label for="username" class="form-label">{t(lang, "admin.ui.username")}</label>
            <input
              type="text"
              id="username"
              name="username"
              class="form-input login-input"
              required
              autocomplete="username"
              disabled={waitSeconds > 0}
            />
          </div>

          <div class="form-group">
            <label for="password" class="form-label">{t(lang, "admin.ui.password")}</label>
            <input
              type="password"
              id="password"
              name="password"
              class="form-input login-input"
              required
              autocomplete="current-password"
              disabled={waitSeconds > 0}
            />
          </div>

          <button
            type="submit"
            class="btn btn-primary login-btn"
            disabled={loading || waitSeconds > 0}
          >
            {#if loading}
              <span class="spinner"></span>
              {t(lang, "admin.ui.entering")}
            {:else if waitSeconds > 0}
              {t(lang, "admin.ui.wait_s", { n: waitSeconds })}
            {:else}
              {t(lang, "admin.ui.login")}
            {/if}
          </button>
        </form>
      </div>
    </div>
  </main>
</div>

<style>
  .login-page {
    min-height: calc(100vh - 200px);
    display: flex;
    flex-direction: column;
  }

  .login-main {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 4rem 2rem;
  }

  .login-content {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 5rem;
    max-width: 1000px;
    width: 100%;
    align-items: center;
    margin: 0 auto;
  }

  .login-intro {
    animation: slideUp 0.5s ease-out;
  }

  .login-intro h1 {
    font-family: var(--font-sans);
    font-size: 3rem;
    font-weight: 800;
    line-height: 1.15;
    margin-bottom: 1.5rem;
    letter-spacing: -1.5px;
  }

  .login-intro p {
    font-family: var(--font-sans);
    font-size: 1.125rem;
    color: var(--text-secondary);
    line-height: 1.7;
    max-width: 420px;
  }

  .login-form-wrapper {
    background: var(--bg-primary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-lg);
    padding: 2.5rem;
    box-shadow: var(--shadow-lg);
    animation: scaleIn 0.4s ease-out;
    min-width: 380px;
  }

  .form-title {
    font-family: var(--font-sans);
    font-size: 1.5rem;
    font-weight: 600;
    margin-bottom: 2rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid var(--border-light);
  }

  .login-input {
    padding: 1rem 1.25rem;
    font-size: 1.0625rem;
  }

  .login-btn {
    width: 100%;
    margin-top: 1rem;
    padding: 1rem 2rem;
    font-size: 0.875rem;
  }

  .spinner {
    display: inline-block;
    width: 16px;
    height: 16px;
    border: 2px solid rgba(255, 255, 255, 0.3);
    border-radius: 50%;
    border-top-color: white;
    animation: spin 0.8s linear infinite;
    margin-right: 0.5rem;
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

  @keyframes scaleIn {
    from {
      opacity: 0;
      transform: scale(0.95);
    }
    to {
      opacity: 1;
      transform: scale(1);
    }
  }

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }

  .message {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .message-error {
    background: var(--bg-error);
    color: var(--text-error);
    border: 1px solid var(--border-error);
    padding: 0.875rem 1rem;
    border-radius: var(--radius-md);
    font-size: 0.875rem;
  }

  .message-warning {
    background: var(--bg-warning);
    color: var(--text-warning);
    border: 1px solid var(--border-warning);
    padding: 0.875rem 1rem;
    border-radius: var(--radius-md);
    font-size: 0.875rem;
  }

  .remaining {
    font-size: 0.75rem;
    opacity: 0.8;
    margin-top: 0.25rem;
  }

  @media (max-width: 900px) {
    .login-content {
      grid-template-columns: 1fr;
      gap: 2.5rem;
      max-width: 480px;
    }

    .login-intro {
      text-align: center;
    }

    .login-intro h1 {
      font-size: 2.25rem;
    }

    .login-intro p {
      font-size: 1.0625rem;
      max-width: none;
    }

    .login-form-wrapper {
      min-width: auto;
    }
  }

  @media (max-width: 480px) {
    .login-main {
      padding: 2rem 1rem;
    }

    .login-intro h1 {
      font-size: 1.75rem;
    }

    .login-intro p {
      font-size: 1rem;
    }

    .login-form-wrapper {
      padding: 1.5rem;
    }

    .form-title {
      font-size: 1.25rem;
      margin-bottom: 1.5rem;
    }

    .login-input {
      padding: 0.875rem 1rem;
    }

    .login-btn {
      padding: 0.875rem 1.5rem;
    }
  }
</style>
