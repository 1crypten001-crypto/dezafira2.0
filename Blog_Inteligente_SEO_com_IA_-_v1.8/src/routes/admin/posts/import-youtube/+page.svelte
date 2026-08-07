<script lang="ts">
  import { page } from "$app/stores";
  import { t, adminErrorMessage } from "$lib/i18n";
  import { enhance } from "$app/forms";
  import { goto } from "$app/navigation";

  const lang = $derived($page.data.language || 'pt');

  let {
    form,
  }: {
    form?: {
      error?: string;
      status?: string;
      detail?: string;
      success?: boolean;
      generatedPost?: {
        title: string;
        content: string;
        excerpt: string;
        cover_image: string;
        videoUrl: string;
      };
    };
  } = $props();

  let loading = $state(false);
  let videoUrlInput = $state("");

  const formError = $derived.by(() => {
    if (!form?.error) return '';
    if (form.error === 'YT_GEMINI_API') {
      return t(lang, 'admin.posts.errors.yt_gemini_api', {
        status: form.status || '',
        detail: form.detail || ''
      });
    }
    return adminErrorMessage(lang, form.error);
  });

  $effect(() => {
    if (form?.success && form.generatedPost) {
      sessionStorage.setItem("importedPost", JSON.stringify(form.generatedPost));
      goto("/admin/posts/new");
    }
  });
</script>

<svelte:head>
  <title>{t(lang, "admin.posts.import_youtube")} - Admin</title>
</svelte:head>

<div class="import-page">
  <div class="import-header">
    <h1 class="import-title">{t(lang, "admin.posts.import_page_title")}</h1>
    <p class="subtitle">{t(lang, "admin.posts.import_page_subtitle")}</p>
  </div>

  <div class="import-card">
    {#if formError}
      <div class="message error">
        <span class="icon">⚠️</span>
        <p>{formError}</p>
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
    >
      <div class="form-group">
        <label for="videoUrl">{t(lang, "admin.posts.import_video_label")}</label>
        <div class="input-wrapper">
          <span class="input-icon">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="2" width="20" height="20" rx="2.18" ry="2.18"></rect><line x1="7" y1="2" x2="7" y2="22"></line><line x1="17" y1="2" x2="17" y2="22"></line><line x1="2" y1="12" x2="22" y2="12"></line><line x1="2" y1="7" x2="7" y2="7"></line><line x1="2" y1="17" x2="7" y2="17"></line><line x1="17" y1="17" x2="22" y2="17"></line><line x1="17" y1="7" x2="22" y2="7"></line></svg>
          </span>
          <input
            type="url"
            id="videoUrl"
            name="videoUrl"
            bind:value={videoUrlInput}
            placeholder="https://www.youtube.com/watch?v=..."
            required
            disabled={loading}
          />
        </div>
        <p class="hint">{t(lang, "admin.posts.import_hint")}</p>
      </div>

      <button type="submit" class="generate-btn" disabled={loading}>
        {#if loading}
          <span class="loader"></span>
          {t(lang, "admin.posts.generating_article")}
        {:else}
          {t(lang, "admin.posts.generate_gemini")}
        {/if}
      </button>
    </form>
  </div>

  <div class="info-grid">
    <div class="info-item">
      <span class="info-icon">
        <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color: #4f46e5;"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
      </span>
      <h3>{t(lang, "admin.posts.import_feature_transcript_title")}</h3>
      <p>{t(lang, "admin.posts.import_feature_transcript_desc")}</p>
    </div>
    <div class="info-item">
      <span class="info-icon">
        <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color: #4f46e5;"><path d="M12 20h9"></path><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path></svg>
      </span>
      <h3>{t(lang, "admin.posts.import_feature_seo_title")}</h3>
      <p>{t(lang, "admin.posts.import_feature_seo_desc")}</p>
    </div>
    <div class="info-item">
      <span class="info-icon">
        <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color: #4f46e5;"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg>
      </span>
      <h3>{t(lang, "admin.posts.import_feature_thumb_title")}</h3>
      <p>{t(lang, "admin.posts.import_feature_thumb_desc")}</p>
    </div>
  </div>
</div>

<style>
  .import-page {
    max-width: 800px;
    margin: 0 auto;
    padding-bottom: 3rem;
  }

  .import-header {
    text-align: center;
    margin-bottom: 2.5rem;
  }

  h1.import-title {
    font-family: var(--font-sans);
    font-size: clamp(1.75rem, 5vw, 2rem);
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 0.5rem;
  }

  .subtitle {
    color: var(--text-muted);
    font-family: var(--font-sans);
  }

  .import-card {
    background: var(--bg-primary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-xl);
    padding: 2.5rem;
    box-shadow: var(--shadow-lg);
    margin-bottom: 3rem;
  }

  .form-group {
    margin-bottom: 1.5rem;
  }

  .form-group label {
    display: block;
    margin-bottom: 0.75rem;
    font-weight: 500;
    color: var(--text-primary);
    font-family: var(--font-sans);
  }

  .input-wrapper {
    position: relative;
    display: flex;
    align-items: center;
  }

  .input-icon {
    position: absolute;
    left: 1rem;
    display: inline-flex;
    align-items: center;
    color: var(--text-muted);
  }

  .input-wrapper input {
    width: 100%;
    padding: 1rem 1rem 1rem 3rem;
    border: 1px solid var(--border-color);
    border-radius: var(--radius-md);
    background: var(--bg-secondary);
    color: var(--text-primary);
    font-family: var(--font-sans);
    font-size: 0.95rem;
  }

  .input-wrapper input:focus {
    outline: none;
    border-color: var(--text-primary);
  }

  .input-wrapper input:disabled {
    opacity: 0.7;
  }

  .hint {
    margin-top: 0.5rem;
    font-size: 0.8rem;
    color: var(--text-muted);
    font-family: var(--font-sans);
  }

  .generate-btn {
    width: 100%;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    padding: 0.95rem 1.25rem;
    background: #4f46e5;
    color: #fff;
    border: none;
    border-radius: var(--radius-md);
    font-weight: 700;
    font-family: var(--font-sans);
    cursor: pointer;
    transition: filter 0.15s ease;
  }

  .generate-btn:hover:not(:disabled) {
    filter: brightness(1.05);
  }

  .generate-btn:disabled {
    opacity: 0.75;
    cursor: not-allowed;
  }

  .loader {
    width: 16px;
    height: 16px;
    border: 2px solid rgba(255, 255, 255, 0.35);
    border-top-color: #fff;
    border-radius: 50%;
    animation: spin 0.7s linear infinite;
  }

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }

  .message.error {
    display: flex;
    gap: 0.65rem;
    align-items: flex-start;
    padding: 0.9rem 1rem;
    margin-bottom: 1.25rem;
    background: #fef2f2;
    border: 1px solid #fecaca;
    border-radius: var(--radius-md);
    color: #b91c1c;
    font-size: 0.9rem;
  }

  .message.error p {
    margin: 0;
  }

  .info-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1.25rem;
  }

  .info-item {
    background: var(--bg-primary);
    border: 1px solid var(--border-light);
    border-radius: var(--radius-lg);
    padding: 1.25rem;
    text-align: center;
  }

  .info-icon {
    display: inline-flex;
    margin-bottom: 0.75rem;
  }

  .info-item h3 {
    font-size: 0.95rem;
    font-weight: 700;
    margin: 0 0 0.5rem;
    color: var(--text-primary);
    font-family: var(--font-sans);
  }

  .info-item p {
    margin: 0;
    font-size: 0.85rem;
    color: var(--text-muted);
    line-height: 1.45;
    font-family: var(--font-sans);
  }

  @media (max-width: 768px) {
    .import-card {
      padding: 1.5rem;
    }

    .info-grid {
      grid-template-columns: 1fr;
    }
  }
</style>
