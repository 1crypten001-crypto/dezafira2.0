<script lang="ts">
  import { page } from "$app/stores";
  import { t, adminErrorMessage } from "$lib/i18n";
  import { enhance } from "$app/forms";
  import Pagination from "$lib/components/Pagination.svelte";

  let { data, form } = $props();
  const lang = $derived($page.data.language || 'pt');

  const formError = $derived.by(() => {
    if (!form?.message) return '';
    if (form.message === 'SL_SLUG_IN_USE') {
      return t(lang, 'admin.shortlinks.errors.slug_in_use', { slug: form.slug || '' });
    }
    return adminErrorMessage(lang, form.message);
  });

  const formSuccessMsg = $derived.by(() => {
    if (!form?.success) return '';
    if (form.action === 'create') return t(lang, 'admin.shortlinks.created_success');
    if (form.action === 'delete') return t(lang, 'admin.shortlinks.deleted_success');
    return t(lang, 'admin.shortlinks.updated_success');
  });

  let newSlug = $state("");
  let newDestinationUrl = $state("");
  let newUseAdInterstitial = $state(false);
  let newAdDurationSeconds = $state(5);
  let newFixedAdId = $state("");
  let newIsIndexed = $state(false);
  let newMetaTitle = $state("");
  let newMetaDescription = $state("");

  let editingId = $state<number | null>(null);
  let editingSlug = $state("");
  let editingDestinationUrl = $state("");
  let editingUseAdInterstitial = $state(false);
  let editingAdDurationSeconds = $state(5);
  let editingFixedAdId = $state("");
  let editingIsIndexed = $state(false);
  let editingMetaTitle = $state("");
  let editingMetaDescription = $state("");

  let searchQuery = $state(data.q || "");

  function startEdit(link: any) {
    editingId = link.id;
    editingSlug = link.slug;
    editingDestinationUrl = link.destination_url;
    editingUseAdInterstitial = link.use_ad_interstitial === 1;
    editingAdDurationSeconds = link.ad_duration_seconds;
    editingFixedAdId = link.fixed_ad_id ? String(link.fixed_ad_id) : "";
    editingIsIndexed = link.is_indexed === 1;
    editingMetaTitle = link.meta_title || "";
    editingMetaDescription = link.meta_description || "";
  }

  function cancelEdit() {
    editingId = null;
  }

  function confirmDelete(event: Event) {
    if (!confirm(t(lang, "admin.shortlinks.confirm_delete"))) {
      event.preventDefault();
    }
  }

  $effect(() => {
    if (form?.success && form?.action === 'create') {
      newSlug = "";
      newDestinationUrl = "";
      newUseAdInterstitial = false;
      newAdDurationSeconds = 5;
      newFixedAdId = "";
      newIsIndexed = false;
      newMetaTitle = "";
      newMetaDescription = "";
    }
  });

  let copiedSlug = $state<string | null>(null);

  async function copyToClipboard(url: string, slug: string) {
    try {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(url);
      } else {
        const textarea = document.createElement('textarea');
        textarea.value = url;
        textarea.style.position = 'fixed';
        textarea.style.opacity = '0';
        document.body.appendChild(textarea);
        textarea.select();
        const successful = document.execCommand('copy');
        document.body.removeChild(textarea);
        if (!successful) throw new Error('Fallback copy failed');
      }
      copiedSlug = slug;
      setTimeout(() => {
        if (copiedSlug === slug) copiedSlug = null;
      }, 2000);
    } catch (err) {
      console.error('Failed to copy text: ', err);
      alert(t(lang, 'admin.shortlinks.copy_manual', { url }));
    }
  }
</script>

<svelte:head>
    <title>{t(lang, "admin.shortlinks.title")}</title>
</svelte:head>

<div class="shortlinks-page">
    <div class="page-header">
        <h1>{t(lang, "admin.shortlinks.heading_full")}</h1>
        <p class="subtitle">{t(lang, "admin.shortlinks.subtitle")}</p>
    </div>

    {#if form?.success}
        <div class="alert success">{formSuccessMsg}</div>
    {:else if formError}
        <div class="alert error">{formError}</div>
    {/if}

    {#if data.activeAdsCount === 0}
        <div class="alert warning-alert">
            <strong>{t(lang, "admin.shortlinks.monetization_title")}</strong>
            {t(lang, "admin.shortlinks.no_ads_warning")}
            {t(lang, "admin.shortlinks.monetization_body")}
            <a href="/admin/ads" class="alert-link">{t(lang, "admin.shortlinks.ads_link")}</a>.
        </div>
    {/if}

    <div class="card create-card">
        <h2>{t(lang, "admin.shortlinks.create_new")}</h2>
        <form method="POST" action="?/create" use:enhance>
            <div class="form-grid">
                <div class="form-group">
                    <label for="slug">{t(lang, "admin.shortlinks.short_url")}</label>
                    <div class="input-prefix-wrapper">
                        <span class="url-prefix">/l/</span>
                        <input
                            type="text"
                            id="slug"
                            name="slug"
                            bind:value={newSlug}
                            placeholder={t(lang, "admin.shortlinks.slug_placeholder")}
                            required
                            pattern="^[a-zA-Z0-9-_]+$"
                            title={t(lang, "admin.shortlinks.slug_pattern_title")}
                        />
                    </div>
                </div>

                <div class="form-group">
                    <label for="destination_url">{t(lang, "admin.shortlinks.destination")}</label>
                    <input
                        type="url"
                        id="destination_url"
                        name="destination_url"
                        bind:value={newDestinationUrl}
                        placeholder={t(lang, "admin.shortlinks.destination_placeholder")}
                        required
                    />
                </div>
            </div>

            <div class="interstitial-settings">
                <label class="checkbox-label toggle-switch">
                    <input
                        type="checkbox"
                        name="use_ad_interstitial"
                        bind:checked={newUseAdInterstitial}
                    />
                    <span class="slider"></span>
                    <span class="toggle-text">{t(lang, "admin.shortlinks.show_ad")}</span>
                </label>

                {#if newUseAdInterstitial}
                    <div class="duration-settings">
                        <label for="ad_duration_seconds">{t(lang, "admin.shortlinks.ad_duration_label")}</label>
                        <input
                            type="number"
                            id="ad_duration_seconds"
                            name="ad_duration_seconds"
                            bind:value={newAdDurationSeconds}
                            min="3"
                            max="30"
                            required
                        />
                    </div>
                    <div class="ad-select-wrapper">
                        <label for="fixed_ad_id">{t(lang, "admin.shortlinks.ad_displayed")}</label>
                        <select id="fixed_ad_id" name="fixed_ad_id" bind:value={newFixedAdId} class="ad-select">
                            <option value="">{t(lang, "admin.shortlinks.ad_random")}</option>
                            {#each data.ads.filter(a => a.is_active === 1) as ad}
                                <option value={ad.id}>{ad.name} ({ad.type})</option>
                            {/each}
                        </select>
                        <p class="settings-help">{t(lang, "admin.shortlinks.ad_select_help")}</p>
                    </div>
                {/if}
            </div>

            <div class="indexing-settings">
                <label class="checkbox-label toggle-switch">
                    <input
                        type="checkbox"
                        name="is_indexed"
                        bind:checked={newIsIndexed}
                    />
                    <span class="slider"></span>
                    <span class="toggle-text">{t(lang, "admin.shortlinks.allow_index")}</span>
                </label>
                <p class="settings-help">{t(lang, "admin.shortlinks.index_help")}</p>

                {#if newIsIndexed}
                    <div class="seo-fields-wrapper">
                        <div class="form-grid inline-seo-grid">
                            <div class="form-group">
                                <label for="meta_title">{t(lang, "admin.shortlinks.seo_title_optional")}</label>
                                <input
                                    type="text"
                                    id="meta_title"
                                    name="meta_title"
                                    bind:value={newMetaTitle}
                                    placeholder={t(lang, "admin.shortlinks.seo_title_ph")}
                                />
                            </div>

                            <div class="form-group">
                                <label for="meta_description">{t(lang, "admin.shortlinks.seo_desc_optional")}</label>
                                <input
                                    type="text"
                                    id="meta_description"
                                    name="meta_description"
                                    bind:value={newMetaDescription}
                                    placeholder={t(lang, "admin.shortlinks.seo_desc_ph")}
                                />
                            </div>
                        </div>
                    </div>
                {/if}
            </div>

            <div class="form-actions">
                <button type="submit" class="btn btn-primary">{t(lang, "admin.shortlinks.create_btn")}</button>
            </div>
        </form>
    </div>

    <div class="card search-card">
        <form method="GET" action="" class="search-form">
            <div class="search-input-wrapper">
                <input
                    type="text"
                    name="q"
                    placeholder={t(lang, "admin.shortlinks.search_placeholder")}
                    bind:value={searchQuery}
                />
                {#if searchQuery}
                    <a href="?" class="btn-clear-search" title={t(lang, "admin.shortlinks.clear_search")}>✕</a>
                {/if}
                <button type="submit" class="btn btn-primary btn-search">{t(lang, "admin.ui.search")}</button>
            </div>
        </form>
    </div>

    <div class="card">
        <h2>{t(lang, "admin.shortlinks.heading")} — {t(lang, "admin.shortlinks.registered", { n: String(data.totalCount) })}</h2>

        {#if data.shortlinks.length === 0}
            <div class="empty-state">
                <p>{data.q ? t(lang, "admin.shortlinks.empty_search") : t(lang, "admin.shortlinks.empty")}</p>
            </div>
        {:else}
            <div class="table-container">
                <table class="links-table">
                    <thead>
                        <tr>
                            <th>{t(lang, "admin.shortlinks.col_short")}</th>
                            <th>{t(lang, "admin.shortlinks.col_destination")}</th>
                            <th>{t(lang, "admin.shortlinks.col_settings")}</th>
                            <th>{t(lang, "admin.shortlinks.clicks")}</th>
                            <th>{t(lang, "admin.ui.actions")}</th>
                        </tr>
                    </thead>
                    <tbody>
                        {#each data.shortlinks as link}
                            {#if editingId === link.id}
                                <!-- Edit Form Row -->
                                <tr class="edit-row">
                                    <td colspan="5">
                                        <form method="POST" action="?/update" use:enhance class="row-edit-form">
                                            <input type="hidden" name="id" value={link.id} />
                                            
                                            <div class="form-grid">
                                                <div class="form-group">
                                                    <label for="edit_slug_{link.id}">{t(lang, "admin.ui.slug")}</label>
                                                    <div class="input-prefix-wrapper">
                                                        <span class="url-prefix">/l/</span>
                                                        <input
                                                            type="text"
                                                            id="edit_slug_{link.id}"
                                                            name="slug"
                                                            bind:value={editingSlug}
                                                            required
                                                        />
                                                    </div>
                                                </div>

                                                <div class="form-group">
                                                    <label for="edit_dest_{link.id}">{t(lang, "admin.shortlinks.destination")}</label>
                                                    <input
                                                        type="url"
                                                        id="edit_dest_{link.id}"
                                                        name="destination_url"
                                                        bind:value={editingDestinationUrl}
                                                        required
                                                    />
                                                </div>
                                            </div>

                                            <div class="row-edit-options">
                                                <label class="checkbox-label">
                                                    <input
                                                        type="checkbox"
                                                        name="use_ad_interstitial"
                                                        bind:checked={editingUseAdInterstitial}
                                                    />
                                                    <span>{t(lang, "admin.shortlinks.show_ad_interstitial")}</span>
                                                </label>

                                                {#if editingUseAdInterstitial}
                                                    <div class="duration-settings inline-duration">
                                                        <label for="edit_duration_{link.id}">{t(lang, "admin.shortlinks.duration_short")}</label>
                                                        <input
                                                            type="number"
                                                            id="edit_duration_{link.id}"
                                                            name="ad_duration_seconds"
                                                            bind:value={editingAdDurationSeconds}
                                                            min="3"
                                                            max="30"
                                                            required
                                                        />
                                                    </div>
                                                    <div class="ad-select-wrapper">
                                                        <label for="edit_fixed_ad_{link.id}">{t(lang, "admin.shortlinks.ad_displayed")}</label>
                                                        <select id="edit_fixed_ad_{link.id}" name="fixed_ad_id" bind:value={editingFixedAdId} class="ad-select">
                                                            <option value="">{t(lang, "admin.shortlinks.ad_random")}</option>
                                                            {#each data.ads.filter(a => a.is_active === 1) as ad}
                                                                <option value={ad.id}>{ad.name} ({ad.type})</option>
                                                            {/each}
                                                        </select>
                                                    </div>
                                                {/if}

                                                <label class="checkbox-label">
                                                    <input
                                                        type="checkbox"
                                                        name="is_indexed"
                                                        bind:checked={editingIsIndexed}
                                                    />
                                                    <span>{t(lang, "admin.shortlinks.index_google")}</span>
                                                </label>
                                            </div>

                                            {#if editingIsIndexed}
                                                <div class="row-edit-seo">
                                                    <div class="form-grid inline-seo-grid">
                                                        <div class="form-group">
                                                            <label for="edit_meta_title_{link.id}">{t(lang, "admin.shortlinks.seo_title_optional")}</label>
                                                            <input
                                                                type="text"
                                                                id="edit_meta_title_{link.id}"
                                                                name="meta_title"
                                                                bind:value={editingMetaTitle}
                                                                placeholder={t(lang, "admin.shortlinks.seo_title_ph")}
                                                            />
                                                        </div>
                                                        <div class="form-group">
                                                            <label for="edit_meta_desc_{link.id}">{t(lang, "admin.shortlinks.seo_desc_optional")}</label>
                                                            <input
                                                                type="text"
                                                                id="edit_meta_desc_{link.id}"
                                                                name="meta_description"
                                                                bind:value={editingMetaDescription}
                                                                placeholder={t(lang, "admin.shortlinks.seo_desc_ph")}
                                                            />
                                                        </div>
                                                    </div>
                                                </div>
                                            {/if}

                                            <div class="edit-actions">
                                                <button type="submit" class="btn btn-small btn-primary">{t(lang, "admin.ui.save")}</button>
                                                <button type="button" class="btn btn-small" onclick={cancelEdit}>{t(lang, "admin.ui.cancel")}</button>
                                            </div>
                                        </form>
                                    </td>
                                </tr>
                            {:else}
                                <!-- Normal Row -->
                                <tr>
                                    <td>
                                        <div class="link-copy-container">
                                            <a href="/l/{link.slug}" target="_blank" class="shortlink-anchor">
                                                /l/{link.slug}
                                            </a>
                                            <button 
                                                type="button" 
                                                class="btn-copy" 
                                                onclick={() => {
                                                    const base = data.siteUrl || (typeof window !== 'undefined' ? window.location.origin : '');
                                                    copyToClipboard(`${base}/l/${link.slug}`, link.slug);
                                                }}
                                                title={t(lang, "admin.shortlinks.copy_full")}
                                            >
                                                {#if copiedSlug === link.slug}
                                                    <span class="copied-text">✓ {t(lang, "admin.shortlinks.copied")}</span>
                                                {:else}
                                                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
                                                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
                                                    </svg>
                                                {/if}
                                            </button>
                                        </div>
                                    </td>
                                    <td>
                                        <span class="dest-url" title={link.destination_url}>
                                            {link.destination_url}
                                        </span>
                                    </td>
                                    <td>
                                        <div class="config-badges">
                                            {#if link.use_ad_interstitial === 1}
                                                {#if link.fixed_ad_id}
                                                    <span class="badge badge-ad">📌 {t(lang, "admin.shortlinks.badge_fixed_ad", { s: String(link.ad_duration_seconds) })}</span>
                                                {:else}
                                                    <span class="badge badge-ad">📢 {t(lang, "admin.shortlinks.badge_ad", { s: String(link.ad_duration_seconds) })}</span>
                                                {/if}
                                            {:else}
                                                <span class="badge badge-direct">⚡ {t(lang, "admin.shortlinks.badge_direct")}</span>
                                            {/if}

                                            {#if link.is_indexed === 1}
                                                <span class="badge badge-indexed" title={t(lang, "admin.shortlinks.badge_indexed_title")}>🔍 {t(lang, "admin.shortlinks.badge_indexed")}</span>
                                            {:else}
                                                <span class="badge badge-noindex" title={t(lang, "admin.shortlinks.badge_private_title")}>🔒 {t(lang, "admin.shortlinks.badge_private")}</span>
                                            {/if}
                                        </div>
                                    </td>
                                    <td>
                                        <span class="clicks-badge">
                                            {link.clicks_count}
                                        </span>
                                    </td>
                                    <td>
                                        <div class="action-buttons">
                                            <button
                                                type="button"
                                                class="btn btn-small"
                                                onclick={() => startEdit(link)}
                                            >
                                                {t(lang, "admin.ui.edit")}
                                            </button>
                                            <form
                                                method="POST"
                                                action="?/delete"
                                                use:enhance
                                                style="display:inline;"
                                            >
                                                <input type="hidden" name="id" value={link.id} />
                                                <button
                                                    type="submit"
                                                    class="btn btn-small btn-danger"
                                                    onclick={confirmDelete}
                                                >
                                                    {t(lang, "admin.ui.delete")}
                                                </button>
                                            </form>
                                        </div>
                                    </td>
                                </tr>
                            {/if}
                        {/each}
                    </tbody>
                </table>
            </div>

            {#if data.totalPages > 1}
                <div class="pagination-wrapper">
                    <Pagination
                        currentPage={data.currentPage}
                        totalPages={data.totalPages}
                        baseUrl={"/admin/shortlinks?q=" + encodeURIComponent(data.q || '')}
                    />
                </div>
            {/if}
        {/if}
    </div>
</div>

<style>
    .shortlinks-page {
        max-width: 960px;
        margin: 0 auto;
    }

    .page-header {
        margin-bottom: 2rem;
    }

    h1 {
        font-family: var(--font-sans);
        font-size: 1.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        color: var(--text-primary);
    }

    .subtitle {
        color: var(--text-muted);
        font-family: var(--font-sans);
    }

    h2 {
        font-family: var(--font-sans);
        font-size: 0.8125rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: var(--text-secondary);
        margin-bottom: 1.25rem;
    }

    .card {
        background: var(--bg-primary);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-lg);
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02);
    }

    .form-grid {
        display: grid;
        grid-template-columns: 1fr 2fr;
        gap: 1.25rem;
        margin-bottom: 1.25rem;
    }

    .form-group {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
    }

    .form-group label {
        font-family: var(--font-sans);
        font-size: 0.8125rem;
        font-weight: 500;
        color: var(--text-secondary);
    }

    .input-prefix-wrapper {
        display: flex;
        align-items: center;
        background: var(--bg-secondary);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-md);
        overflow: hidden;
        transition: border-color var(--transition-fast);
    }

    .input-prefix-wrapper:focus-within {
        border-color: var(--text-primary);
    }

    .url-prefix {
        padding: 0 0.75rem;
        font-family: var(--font-sans);
        font-size: 0.875rem;
        color: var(--text-muted);
        background: var(--bg-tertiary);
        border-right: 1px solid var(--border-color);
        user-select: none;
        height: 100%;
        display: flex;
        align-items: center;
    }

    .input-prefix-wrapper input {
        border: none !important;
        border-radius: 0 !important;
        background: transparent !important;
        flex: 1;
    }

    input[type="text"],
    input[type="url"],
    input[type="number"] {
        padding: 0.725rem 0.75rem;
        background: var(--bg-secondary);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-md);
        color: var(--text-primary);
        font-family: var(--font-sans);
        font-size: 0.875rem;
        transition: border-color var(--transition-fast);
    }

    input:focus {
        outline: none;
        border-color: var(--text-primary);
    }

    .interstitial-settings {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 1rem 0;
        border-top: 1px dashed var(--border-light);
        border-bottom: 1px dashed var(--border-light);
        margin-bottom: 1.25rem;
        gap: 1.5rem;
    }

    .duration-settings {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        font-family: var(--font-sans);
        font-size: 0.875rem;
        color: var(--text-secondary);
    }

    .duration-settings input {
        width: 70px;
        text-align: center;
        padding: 0.5rem;
    }

    .ad-select-wrapper {
        display: flex;
        flex-direction: column;
        gap: 0.35rem;
        font-size: 0.875rem;
        color: var(--text-secondary);
        font-family: var(--font-sans);
        margin-top: 0.75rem;
    }

    .ad-select-wrapper label {
        font-weight: 500;
        color: var(--text-secondary);
        font-size: 0.875rem;
    }

    .ad-select {
        width: 100%;
        max-width: 480px;
        padding: 0.5rem 0.75rem;
        border: 1px solid var(--border-color);
        border-radius: var(--radius-md, 8px);
        background: var(--bg-primary);
        color: var(--text-primary);
        font-size: 0.875rem;
        font-family: var(--font-sans);
        cursor: pointer;
        transition: border-color 0.2s;
    }

    .ad-select:focus {
        outline: none;
        border-color: var(--accent);
        box-shadow: 0 0 0 3px color-mix(in srgb, var(--accent) 15%, transparent);
    }

    .indexing-settings {
        padding: 0.5rem 0 1.25rem;
        border-bottom: 1px dashed var(--border-light);
        margin-bottom: 1.25rem;
    }

    .settings-help {
        font-family: var(--font-sans);
        font-size: 0.75rem;
        color: var(--text-muted);
        margin-top: 0.35rem;
        padding-left: 50px;
        line-height: 1.4;
    }

    .form-actions {
        display: flex;
        justify-content: flex-end;
    }

    /* ── Search Styling ────────────────────────────────────────────── */
    .search-card {
        padding: 1rem 1.5rem;
    }

    .search-form {
        width: 100%;
    }

    .search-input-wrapper {
        display: flex;
        gap: 0.75rem;
        align-items: center;
    }

    .search-input-wrapper input {
        flex: 1;
        padding: 0.725rem 0.75rem;
        background: var(--bg-secondary);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-md);
        color: var(--text-primary);
        font-family: var(--font-sans);
        font-size: 0.875rem;
    }

    .btn-search {
        padding: 0.725rem 1.5rem;
        font-size: 0.875rem;
        height: 100%;
    }

    .btn-clear-search {
        color: var(--text-muted);
        text-decoration: none;
        font-size: 1.125rem;
        padding: 0.5rem;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        transition: color var(--transition-fast);
    }

    .btn-clear-search:hover {
        color: var(--text-primary);
    }

    /* ── Table Styling ────────────────────────────────────────────── */
    .table-container {
        overflow-x: auto;
    }

    .links-table {
        width: 100%;
        border-collapse: collapse;
        text-align: left;
        font-family: var(--font-sans);
    }

    .links-table th {
        padding: 0.75rem 1rem;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        color: var(--text-muted);
        border-bottom: 1px solid var(--border-color);
    }

    .links-table td {
        padding: 1rem;
        border-bottom: 1px solid var(--border-light);
        vertical-align: middle;
    }

    .links-table tr:last-child td {
        border-bottom: none;
    }

    .shortlink-anchor {
        font-weight: 600;
        color: var(--accent, #3b82f6);
        text-decoration: none;
        background: rgba(59, 130, 246, 0.05);
        padding: 0.25rem 0.5rem;
        border-radius: var(--radius-sm);
        font-family: "Monaco", "Consolas", monospace;
        font-size: 0.8125rem;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        max-width: 160px;
        display: inline-block;
        vertical-align: middle;
    }

    .shortlink-anchor:hover {
        text-decoration: underline;
    }

    .dest-url {
        display: block;
        max-width: 240px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        color: var(--text-secondary);
        font-size: 0.875rem;
    }

    .config-badges {
        display: flex;
        gap: 0.5rem;
        align-items: center;
        flex-wrap: wrap;
    }

    .badge {
        display: inline-flex;
        align-items: center;
        gap: 0.25rem;
        font-size: 0.75rem;
        font-weight: 500;
        padding: 0.25rem 0.625rem;
        border-radius: 9999px;
        white-space: nowrap;
    }

    .badge-direct {
        background: #ecfdf5;
        color: #059669;
        border: 1px solid #a7f3d0;
    }

    .badge-ad {
        background: #fff7ed;
        color: #d97706;
        border: 1px solid #fed7aa;
    }

    .badge-indexed {
        background: #eff6ff;
        color: #2563eb;
        border: 1px solid #bfdbfe;
    }

    .badge-noindex {
        background: #f1f5f9;
        color: #475569;
        border: 1px solid #cbd5e1;
    }

    .clicks-badge {
        font-family: "Monaco", "Consolas", monospace;
        font-size: 0.875rem;
        font-weight: 600;
        color: var(--text-primary);
        background: var(--bg-tertiary);
        padding: 0.2rem 0.6rem;
        border-radius: var(--radius-md);
    }

    .action-buttons {
        display: flex;
        gap: 0.5rem;
    }

    .btn-danger {
        border-color: #dc2626;
        color: #dc2626;
    }

    .btn-danger:hover {
        background: #dc2626;
        color: white;
    }

    /* ── Edit Mode Row ────────────────────────────────────────────── */
    .edit-row {
        background: var(--bg-secondary);
    }

    .row-edit-form {
        padding: 1rem;
        border: 1px solid var(--border-color);
        border-radius: var(--radius-md);
        background: var(--bg-primary);
    }

    .row-edit-options {
        display: flex;
        align-items: center;
        gap: 1.5rem;
        margin-bottom: 1rem;
        padding-top: 0.5rem;
        border-top: 1px dashed var(--border-light);
        flex-wrap: wrap;
    }

    .row-edit-options .checkbox-label {
        font-size: 0.8125rem;
    }

    .inline-duration {
        margin-top: 0;
        margin-bottom: 0;
    }

    /* ── Pagination Wrapper ───────────────────────────────────────── */
    .pagination-wrapper {
        margin-top: 1.5rem;
        border-top: 1px solid var(--border-light);
        padding-top: 1.5rem;
    }

    .pagination-wrapper :global(.pagination) {
        margin: 1.5rem 0 0.5rem 0 !important;
    }

    /* ── Alerts ───────────────────────────────────────────────────── */
    .alert {
        padding: 1rem;
        border-radius: var(--radius-md);
        margin-bottom: 1.5rem;
        font-family: var(--font-sans);
        font-size: 0.875rem;
    }

    .success {
        background: #ecfdf5;
        color: #059669;
        border: 1px solid #a7f3d0;
    }

    .error {
        background: #fef2f2;
        color: #dc2626;
        border: 1px solid #fecaca;
    }

    .warning-alert {
        background: #fffbeb;
        color: #b45309;
        border: 1px solid #fde68a;
    }

    .alert-link {
        color: inherit;
        text-decoration: underline;
        font-weight: 600;
    }

    .empty-state {
        text-align: center;
        padding: 3rem 1rem;
        color: var(--text-muted);
        font-family: var(--font-sans);
    }

    /* ── Checkbox Toggle switch styling ───────────────────────────── */
    .checkbox-label {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        font-family: var(--font-sans);
        font-size: 0.875rem;
        color: var(--text-secondary);
        cursor: pointer;
        user-select: none;
    }

    /* Switch slider container */
    .toggle-switch {
        position: relative;
        padding-left: 50px;
        height: 24px;
    }

    .toggle-switch input {
        opacity: 0;
        width: 0;
        height: 0;
        position: absolute;
    }

    .slider {
        position: absolute;
        cursor: pointer;
        top: 0;
        left: 0;
        width: 42px;
        height: 24px;
        background-color: var(--border-color);
        transition: .3s;
        border-radius: 34px;
    }

    .slider:before {
        position: absolute;
        content: "";
        height: 16px;
        width: 16px;
        left: 4px;
        bottom: 4px;
        background-color: white;
        transition: .3s;
        border-radius: 50%;
    }

    .toggle-switch input:checked + .slider {
        background-color: var(--accent, #3b82f6);
    }

    .toggle-switch input:checked + .slider:before {
        transform: translateX(18px);
    }

    .toggle-text {
        font-weight: 500;
    }

    @media (max-width: 768px) {
        .form-grid {
            grid-template-columns: 1fr;
        }

        .interstitial-settings {
            flex-direction: column;
            align-items: flex-start;
            gap: 1rem;
        }

        .action-buttons {
            flex-direction: column;
            gap: 0.25rem;
        }

        .action-buttons button,
        .action-buttons form,
        .action-buttons form button {
            width: 100%;
        }
    }

    /* ── Clipboard Copy ───────────────────────────────────────────── */
    .link-copy-container {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        flex-wrap: nowrap;
        overflow: hidden;
        max-width: 200px;
    }

    .btn-copy {
        background: transparent;
        border: none;
        color: var(--text-muted);
        cursor: pointer;
        padding: 0.35rem;
        border-radius: var(--radius-sm);
        display: inline-flex;
        align-items: center;
        justify-content: center;
        transition: color var(--transition-fast), background-color var(--transition-fast);
    }

    .btn-copy:hover {
        color: var(--text-primary);
        background: var(--bg-secondary);
    }

    .copied-text {
        font-size: 0.75rem;
        color: #059669;
        font-weight: 600;
        animation: copyFadeIn 0.2s ease-in-out;
    }

    @keyframes copyFadeIn {
        from { opacity: 0; transform: translateY(-2px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .seo-fields-wrapper {
        margin-top: 1.25rem;
        padding: 1.25rem;
        background: var(--bg-secondary);
        border: 1px dashed var(--border-color);
        border-radius: var(--radius-md);
        animation: slideDown 200ms ease-in-out;
    }

    .row-edit-seo {
        margin-top: 1rem;
        padding: 1rem;
        background: var(--bg-secondary);
        border: 1px dashed var(--border-color);
        border-radius: var(--radius-md);
        margin-bottom: 1rem;
        animation: slideDown 200ms ease-in-out;
    }

    .inline-seo-grid {
        grid-template-columns: 1fr 1fr !important;
        margin-bottom: 0 !important;
        gap: 1rem !important;
    }

    @keyframes slideDown {
        from { opacity: 0; transform: translateY(-5px); }
        to { opacity: 1; transform: translateY(0); }
    }

    @media (max-width: 768px) {
        .inline-seo-grid {
            grid-template-columns: 1fr !important;
        }
    }
</style>
