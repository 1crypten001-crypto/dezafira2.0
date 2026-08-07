<script lang="ts">
  import { enhance } from "$app/forms";
  import { page } from "$app/stores";
  import { t, memberErrorMessage } from "$lib/i18n";
  
  let { form } = $props();
  let loading = $state(false);
  const lang = $derived($page.data.language || 'pt');
  const errorMsg = $derived(memberErrorMessage(lang, form?.error));
</script>

<svelte:head>
  <title>{t(lang, "members.register_title")} | {t(lang, "members.area_title")}</title>
</svelte:head>

<div class="register-container">
  <div class="register-card">
    <div class="card-header">
      <h1>{t(lang, "members.register_title")}</h1>
      <p class="subtitle">{t(lang, "members.register_subtitle")}</p>
    </div>

    {#if form?.error}
      <div class="alert error">
        {errorMsg}
      </div>
    {/if}

    <form 
      method="POST" 
      use:enhance={() => {
        loading = true;
        return async ({ update }) => {
          loading = false;
          await update();
        };
      }}
      class="register-form"
    >
      <div class="form-group">
        <label for="email">{t(lang, "common.email")}</label>
        <input 
          type="email" 
          id="email" 
          name="email" 
          placeholder="exemplo@email.com" 
          required 
          disabled={loading} 
        />
      </div>

      <div class="form-group">
        <label for="password">{t(lang, "common.password")}</label>
        <input 
          type="password" 
          id="password" 
          name="password" 
          placeholder="Mínimo 6 caracteres" 
          required 
          disabled={loading} 
        />
      </div>

      <div class="form-group">
        <label for="confirmPassword">{t(lang, "members.confirm_password")}</label>
        <input 
          type="password" 
          id="confirmPassword" 
          name="confirmPassword" 
          placeholder="Repita sua senha" 
          required 
          disabled={loading} 
        />
      </div>

      <button 
        type="submit" 
        class="btn btn-primary btn-full" 
        disabled={loading}
      >
        {#if loading}
          {t(lang, "members.creating")}
        {:else}
          {t(lang, "members.sign_up_btn")}
        {/if}
      </button>
    </form>

    <div class="card-footer">
      <span>{t(lang, "members.has_account")}</span>
      <a href="/members/login" class="link">{t(lang, "common.login")}</a>
    </div>
  </div>
</div>

<style>
  .register-container {
    max-width: 480px;
    margin: 4rem auto;
    padding: 0 1rem;
  }

  .register-card {
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

  .register-form {
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
