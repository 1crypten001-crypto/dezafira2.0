<script lang="ts">
  import { enhance } from "$app/forms";
  import { page } from "$app/stores";
  import { t, memberErrorMessage } from "$lib/i18n";
  
  let { data, form } = $props();
  let loading = $state(false);
  let waitSeconds = $derived(form?.waitSeconds || 0);
  let remaining = $derived(form?.remaining ?? undefined);
  const lang = $derived($page.data.language || 'pt');
  const errorMsg = $derived(memberErrorMessage(lang, form?.error));
</script>

<svelte:head>
  <title>{t(lang, "common.login")} | {t(lang, "members.area_title")}</title>
</svelte:head>

<div class="login-container">
  <div class="login-card">
    <div class="card-header">
      <h1>{t(lang, "members.area_title")}</h1>
      <p class="subtitle">
        {#if data.enableOtpLogin}
          {#if form?.otpSent}
            {t(lang, "members.otp_sent")}
          {:else}
            {t(lang, "members.otp_prompt")}
          {/if}
        {:else}
          {t(lang, "members.login_subtitle")}
        {/if}
      </p>
    </div>

    {#if form?.error}
      <div class="alert error" class:warning={waitSeconds > 0}>
        {errorMsg}
        {#if remaining !== undefined && waitSeconds === 0}
          <span class="remaining">{t(lang, "members.remaining", { n: remaining })}</span>
        {/if}
      </div>
    {/if}

    {#if data.enableOtpLogin}
      <!-- OTP-Based Login Flow -->
      {#if !form?.otpSent}
        <form 
          method="POST" 
          action="?/sendOtp"
          use:enhance={() => {
            loading = true;
            return async ({ update }) => {
              loading = false;
              await update();
            };
          }}
          class="login-form"
        >
          <div class="form-group">
            <label for="email">{t(lang, "common.email")}</label>
            <input 
              type="email" 
              id="email" 
              name="email" 
              placeholder="exemplo@email.com" 
              required 
              disabled={loading || waitSeconds > 0} 
            />
          </div>

          <button 
            type="submit" 
            class="btn btn-primary btn-full" 
            disabled={loading || waitSeconds > 0}
          >
            {#if loading}
              {t(lang, "common.submitting")}
            {:else if waitSeconds > 0}
              {t(lang, "members.wait_s", { n: waitSeconds })}
            {:else}
              {t(lang, "members.send_code")}
            {/if}
          </button>
        </form>
      {:else}
        <!-- Step 2: Verify OTP Code -->
        <form 
          method="POST" 
          action="?/verifyOtp"
          use:enhance={() => {
            loading = true;
            return async ({ update }) => {
              loading = false;
              await update();
            };
          }}
          class="login-form"
        >
          <input type="hidden" name="email" value={form.email} />

          <div class="form-group">
            <label for="code">{t(lang, "members.access_code")}</label>
            <input 
              type="text" 
              id="code" 
              name="code" 
              placeholder="123456" 
              inputmode="numeric"
              maxlength="10"
              required 
              disabled={loading || waitSeconds > 0} 
              oninput={(e) => {
                e.currentTarget.value = e.currentTarget.value.replace(/\D/g, '');
              }}
              style="text-align: center; font-size: 1.5rem; letter-spacing: 0.5rem; padding: 0.5rem;"
            />
          </div>

          <button 
            type="submit" 
            class="btn btn-primary btn-full" 
            disabled={loading || waitSeconds > 0}
          >
            {#if loading}
              {t(lang, "members.verifying")}
            {:else}
              {t(lang, "members.confirm_enter")}
            {/if}
          </button>

          <a href="/members/login" class="btn btn-secondary btn-full" style="text-align: center; border: 1px solid var(--border-color); margin-top: 0.5rem;">
            {t(lang, "common.back")}
          </a>
        </form>
      {/if}
    {:else}
      <!-- Traditional Password-Based Login Flow -->
      <form 
        method="POST" 
        action="?/login"
        use:enhance={() => {
          loading = true;
          return async ({ update }) => {
            loading = false;
            await update();
          };
        }}
        class="login-form"
      >
        <div class="form-group">
          <label for="email">{t(lang, "common.email")}</label>
          <input 
            type="email" 
            id="email" 
            name="email" 
            placeholder="exemplo@email.com" 
            required 
            disabled={loading || waitSeconds > 0} 
          />
        </div>

        <div class="form-group">
          <label for="password">{t(lang, "common.password")}</label>
          <input 
            type="password" 
            id="password" 
            name="password" 
            placeholder="••••••••" 
            required 
            disabled={loading || waitSeconds > 0} 
          />
        </div>

        <button 
          type="submit" 
          class="btn btn-primary btn-full" 
          disabled={loading || waitSeconds > 0}
        >
          {#if loading}
            {t(lang, "members.entering")}
          {:else if waitSeconds > 0}
            {t(lang, "members.wait_s", { n: waitSeconds })}
          {:else}
            {t(lang, "common.login")}
          {/if}
        </button>
      </form>
    {/if}

    <div class="card-footer">
      <span>{t(lang, "members.no_account")}</span>
      <a href="/members/register" class="link">{t(lang, "members.sign_up")}</a>
    </div>
  </div>
</div>

<style>
  .login-container {
    max-width: 480px;
    margin: 4rem auto;
    padding: 0 1rem;
  }

  .login-card {
    background: var(--bg-primary);
    border: 1px solid var(--border-light);
    border-radius: var(--radius-lg);
    padding: 2.5rem;
    box-shadow: var(--shadow-lg);
  }

  .card-header {
    text-align: center;
    margin-bottom: 2rem;
  }

  h1 {
    font-size: 1.75rem;
    font-weight: 700;
    margin-bottom: 0.5rem;
    letter-spacing: -0.5px;
  }

  .subtitle {
    font-size: 0.9rem;
    color: var(--text-secondary);
    line-height: 1.5;
  }

  .login-form {
    display: flex;
    flex-direction: column;
    gap: 1.25rem;
  }

  .form-group {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  label {
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    font-weight: 600;
    color: var(--text-secondary);
  }

  input {
    width: 100%;
    padding: 0.875rem;
    border: 1px solid var(--border-color);
    border-radius: var(--radius-md);
    background: var(--bg-secondary);
    color: var(--text-primary);
    font-size: 0.95rem;
    transition: all 0.2s;
  }

  input:focus {
    outline: none;
    border-color: var(--text-primary);
    background: var(--bg-primary);
  }

  .btn-full {
    width: 100%;
    padding: 0.875rem;
    font-size: 0.9rem;
    margin-top: 0.5rem;
  }

  .alert {
    padding: 1rem;
    border-radius: var(--radius-md);
    font-size: 0.875rem;
    margin-bottom: 1.5rem;
  }

  .error {
    background: #fef2f2;
    color: #dc2626;
    border: 1px solid #fee2e2;
  }

  .warning {
    background: #fffbeb;
    color: #d97706;
    border: 1px solid #fef3c7;
  }

  .remaining {
    display: block;
    font-size: 0.75rem;
    opacity: 0.8;
    margin-top: 0.25rem;
  }

  .card-footer {
    margin-top: 1.5rem;
    display: flex;
    justify-content: center;
    gap: 0.5rem;
    font-size: 0.875rem;
    color: var(--text-secondary);
  }

  .link {
    color: var(--text-primary);
    font-weight: 600;
    text-decoration: underline;
  }
</style>
