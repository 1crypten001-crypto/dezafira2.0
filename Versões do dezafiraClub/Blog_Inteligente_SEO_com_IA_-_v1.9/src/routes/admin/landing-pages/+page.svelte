<script lang="ts">
  import { page } from "$app/stores";
  import { t } from "$lib/i18n";
  import { enhance } from "$app/forms";
  import LandingCliPanel from '$lib/components/LandingCliPanel.svelte';
  import Pagination from '$lib/components/Pagination.svelte';

  // Obter props de dados passados pelo servidor
  let { data, form } = $props();

  const lang = $derived($page.data.language || 'pt');

  // Estados dos Modais
  let createModalOpen = $state(false);
  let editModalOpen = $state(false);
  let deleteModalOpen = $state(false);

  // Valores dos formulários nos modais
  let newTitle = $state('');
  let newSlug = $state('');
  let editingId = $state(0);
  let editingTitle = $state('');
  let editingSlug = $state('');
  let editingStatus = $state('draft');
  let deletingId = $state(0);
  let deletingTitle = $state('');

  // Auto-gerar slug a partir do título do modal de criação
  function onTitleInput() {
    newSlug = newTitle
      .toLowerCase()
      .trim()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .replace(/[^a-z0-9\s-]/g, '')
      .replace(/[\s_]+/g, '-')
      .replace(/-+/g, '-')
      .replace(/^-+|-+$/g, '');
  }

  function openEditModal(item: any) {
    editingId = item.id;
    editingTitle = item.title;
    editingSlug = item.slug;
    editingStatus = item.status;
    editModalOpen = true;
  }

  function openDeleteModal(item: any) {
    deletingId = item.id;
    deletingTitle = item.title;
    deleteModalOpen = true;
  }

  let copiedSlug = $state<string | null>(null);

  async function copyPublicUrl(slug: string) {
    const url = `${window.location.origin}/p/${slug}`;
    try {
      await navigator.clipboard.writeText(url);
      copiedSlug = slug;
      setTimeout(() => {
        if (copiedSlug === slug) copiedSlug = null;
      }, 2000);
    } catch {
      // ignore
    }
  }
</script>

<svelte:head>
  <title>Admin | {t(lang, 'admin.landing_pages.title')}</title>
</svelte:head>

<div class="landing-manager-container">
  <!-- Cabeçalho Principal -->
  <div class="header-section">
    <div>
      <h1 class="page-title">{t(lang, 'admin.landing_pages.title')}</h1>
      <p class="page-subtitle">{t(lang, 'admin.landing_pages.subtitle')}</p>
    </div>
    <button class="create-btn" onclick={() => { newTitle = ''; newSlug = ''; createModalOpen = true; }}>
      <svg viewBox="0 0 20 20" fill="currentColor" width="18" height="18" class="btn-icon">
        <path fill-rule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clip-rule="evenodd" />
      </svg>
      {t(lang, 'admin.landing_pages.button')}
    </button>
  </div>

  <!-- Feedback de Erro do Form -->
  {#if form?.error}
    <div class="alert alert-error">
      <svg viewBox="0 0 20 20" fill="currentColor" width="18" height="18">
        <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
      </svg>
      {form.error}
    </div>
  {/if}

  <div class="list-toolbar">
    <form method="GET" class="search-form" role="search">
      <span class="search-icon" aria-hidden="true">⌕</span>
      <input type="search" name="q" value={data.search || ''} placeholder="Buscar por título ou slug..." aria-label="Buscar landing page por título ou slug" />
      {#if data.search}<a class="clear-search" href="/admin/landing-pages">Limpar</a>{/if}
      <button type="submit">Buscar</button>
    </form>
    <div class="list-summary"><strong>{data.pagination.total}</strong><span>{data.pagination.total === 1 ? 'landing encontrada' : 'landings encontradas'}</span></div>
  </div>

  {#if !data.landingPages || data.landingPages.length === 0}
    <div class="empty-state-card">
      <div class="illustration-box">
        <svg viewBox="0 0 24 24" width="72" height="72" fill="none" stroke="currentColor" stroke-width="1.25" stroke-linecap="round" stroke-linejoin="round" class="illustration-svg">
          <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
          <line x1="3" y1="9" x2="21" y2="9" />
          <line x1="9" y1="21" x2="9" y2="9" />
          <line x1="12" y1="13" x2="16" y2="13" />
          <line x1="12" y1="16" x2="16" y2="16" />
        </svg>
      </div>
      
      {#if data.search}
        <h2 class="empty-title">Nenhuma landing encontrada</h2>
        <p class="empty-description">Não encontramos título ou slug correspondente a “{data.search}”. Tente outro termo.</p>
        <a class="create-btn secondary-create" href="/admin/landing-pages">Ver todas as landings</a>
      {:else}
        <h2 class="empty-title">{t(lang, 'admin.landing_pages.empty_title')}</h2>
        <p class="empty-description">{t(lang, 'admin.landing_pages.empty_desc')}</p>
        <button class="create-btn" onclick={() => { newTitle = ''; newSlug = ''; createModalOpen = true; }}>
          <svg viewBox="0 0 20 20" fill="currentColor" width="18" height="18" class="btn-icon">
            <path fill-rule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clip-rule="evenodd" />
          </svg>
          {t(lang, 'admin.landing_pages.create_first')}
        </button>
      {/if}
    </div>
  {:else}
    <div class="table-container">
      <table class="landing-table">
        <thead>
          <tr>
            <th>{t(lang, 'admin.landing_pages.col_title')}</th>
            <th>{t(lang, 'admin.landing_pages.col_slug')}</th>
            <th>{t(lang, 'admin.landing_pages.col_status')}</th>
            <th>{t(lang, 'admin.landing_pages.col_created')}</th>
            <th class="actions-header">{t(lang, 'admin.landing_pages.col_actions')}</th>
          </tr>
        </thead>
        <tbody>
          {#each data.landingPages as item}
            <tr>
              <td>
                <div class="title-cell">
                  <span class="page-name">{item.title}</span>
                </div>
              </td>
              <td>
                <div class="slug-cell">
                  <a href="/p/{item.slug}" target="_blank" rel="noopener noreferrer" class="slug-link" title={t(lang, 'admin.landing_pages.open_public')}>
                    /p/{item.slug}
                    <svg viewBox="0 0 20 20" fill="currentColor" width="14" height="14" class="link-icon">
                      <path d="M11 3a1 1 0 100 2h2.586l-6.293 6.293a1 1 0 101.414 1.414L15 6.414V9a1 1 0 102 0V4a1 1 0 00-1-1h-5z" />
                      <path d="M5 5a2 2 0 00-2 2v8a2 2 0 002 2h8a2 2 0 002-2v-3a1 1 0 10-2 0v3H5V7h3a1 1 0 000-2H5z" />
                    </svg>
                  </a>
                  <button type="button" class="copy-url-btn" onclick={() => copyPublicUrl(item.slug)} title={t(lang, 'admin.landing_pages.copy_url')}>
                    {copiedSlug === item.slug ? '✓' : '⧉'}
                  </button>
                </div>
              </td>
              <td>
                {#if item.status === 'published'}
                  <span class="status-badge published">
                    {t(lang, 'admin.landing_pages.published')}
                  </span>
                {:else}
                  <span class="status-badge draft">
                    {t(lang, 'admin.landing_pages.draft')}
                  </span>
                {/if}
              </td>
              <td>
                <span class="date-txt">
                  {new Date(item.created_at).toLocaleDateString(lang === 'pt' ? 'pt-BR' : lang === 'es' ? 'es-ES' : 'en-US')}
                </span>
              </td>
              <td class="actions-cell">
                <a href="/admin/landing-pages/{item.id}" class="action-btn edit-btn" title={t(lang, 'admin.landing_pages.visual_editor')}>
                  <svg viewBox="0 0 20 20" fill="currentColor" width="16" height="16">
                    <path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z" />
                  </svg>
                  {t(lang, 'admin.landing_pages.visual_editor')}
                </a>

                <form method="POST" action="?/duplicate" class="inline-form">
                  <input type="hidden" name="id" value={item.id} />
                  <button type="submit" class="action-btn details-btn" title={t(lang, 'admin.landing_pages.duplicate')}>
                    <svg viewBox="0 0 20 20" fill="currentColor" width="16" height="16">
                      <path d="M7 9a2 2 0 012-2h6a2 2 0 012 2v6a2 2 0 01-2 2H9a2 2 0 01-2-2V9z" />
                      <path d="M5 3a2 2 0 00-2 2v6a2 2 0 002 2V5h6a2 2 0 00-2-2H5z" />
                    </svg>
                  </button>
                </form>
                
                <button class="action-btn details-btn" onclick={() => openEditModal(item)} title={t(lang, 'admin.landing_pages.edit_details')}>
                  <svg viewBox="0 0 20 20" fill="currentColor" width="16" height="16">
                    <path d="M17.414 2.586a2 2 0 00-2.828 0L7 10.172V13h2.828l7.586-7.586a2 2 0 000-2.828z" />
                    <path fill-rule="evenodd" d="M2 6a2 2 0 012-2h4a1 1 0 010 2H4v10h10v-4a1 1 0 112 0v4a2 2 0 01-2 2H4a2 2 0 01-2-2V6z" clip-rule="evenodd" />
                  </svg>
                </button>

                <button class="action-btn delete-btn" onclick={() => openDeleteModal(item)} title={t(lang, 'admin.landing_pages.delete_page')}>
                  <svg viewBox="0 0 20 20" fill="currentColor" width="16" height="16">
                    <path fill-rule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd" />
                  </svg>
                </button>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
    <div class="pagination-wrapper">
      <Pagination
        currentPage={data.pagination.page}
        totalPages={data.pagination.totalPages}
        baseUrl={`/admin/landing-pages${data.search ? `?q=${encodeURIComponent(data.search)}` : ''}`}
      />
    </div>
  {/if}
</div>

<LandingCliPanel
  tokenConfigured={data.cliTokenConfigured}
  tokenExpiresAt={form?.cliTokenExpiresAt || data.cliTokenExpiresAt}
  {form}
/>

<!-- MODAL: Criar Nova Página -->
{#if createModalOpen}
  <div class="modal-backdrop">
    <div class="modal-card">
      <h3 class="modal-title">{t(lang, 'admin.landing_pages.new_page')}</h3>
      <form method="POST" action="?/create" use:enhance={() => { createModalOpen = false; }}>
        <div class="form-group">
          <label for="title">{t(lang, 'admin.landing_pages.page_title')}</label>
          <input type="text" id="title" name="title" bind:value={newTitle} oninput={onTitleInput} placeholder="Ex: sales-page" required />
        </div>
        <div class="form-group">
          <label for="slug">Slug (URL)</label>
          <div class="slug-input-wrapper">
            <span class="prefix">/p/</span>
            <input type="text" id="slug" name="slug" bind:value={newSlug} placeholder="sales-page" required />
          </div>
        </div>
        <div class="modal-actions">
          <button type="button" class="cancel-btn" onclick={() => createModalOpen = false}>
            {t(lang, 'admin.landing_pages.cancel')}
          </button>
          <button type="submit" class="submit-btn">
            {t(lang, 'admin.landing_pages.create_continue')}
          </button>
        </div>
      </form>
    </div>
  </div>
{/if}

<!-- MODAL: Editar Metadados -->
{#if editModalOpen}
  <div class="modal-backdrop">
    <div class="modal-card">
      <h3 class="modal-title">{t(lang, 'admin.landing_pages.edit_details')}</h3>
      <form method="POST" action="?/update" use:enhance={() => { editModalOpen = false; }}>
        <input type="hidden" name="id" value={editingId} />
        <div class="form-group">
          <label for="edit_title">{t(lang, 'admin.landing_pages.page_title')}</label>
          <input type="text" id="edit_title" name="title" bind:value={editingTitle} required />
        </div>
        <div class="form-group">
          <label for="edit_slug">Slug (URL)</label>
          <div class="slug-input-wrapper">
            <span class="prefix">/p/</span>
            <input type="text" id="edit_slug" name="slug" bind:value={editingSlug} required />
          </div>
        </div>
        <div class="form-group">
          <label for="edit_status">Status</label>
          <select id="edit_status" name="status" bind:value={editingStatus}>
            <option value="draft">{t(lang, 'admin.landing_pages.draft')}</option>
            <option value="published">{t(lang, 'admin.landing_pages.published')}</option>
          </select>
        </div>
        <div class="modal-actions">
          <button type="button" class="cancel-btn" onclick={() => editModalOpen = false}>
            {t(lang, 'admin.landing_pages.cancel')}
          </button>
          <button type="submit" class="submit-btn">
            {t(lang, 'admin.landing_pages.save_changes')}
          </button>
        </div>
      </form>
    </div>
  </div>
{/if}

<!-- MODAL: Excluir Confirmação -->
{#if deleteModalOpen}
  <div class="modal-backdrop">
    <div class="modal-card danger-card">
      <h3 class="modal-title warning-text">
        <svg viewBox="0 0 20 20" fill="currentColor" width="22" height="22" class="modal-warning-icon">
          <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
        </svg>
        {t(lang, 'admin.landing_pages.delete_page')}
      </h3>
      <p class="modal-warning-desc">
        {t(lang, 'admin.landing_pages.delete_confirm', { title: deletingTitle })}
      </p>
      <form method="POST" action="?/delete" use:enhance={() => { deleteModalOpen = false; }}>
        <input type="hidden" name="id" value={deletingId} />
        <div class="modal-actions">
          <button type="button" class="cancel-btn" onclick={() => deleteModalOpen = false}>
            {t(lang, 'admin.landing_pages.cancel')}
          </button>
          <button type="submit" class="submit-btn danger-submit-btn">
            {t(lang, 'admin.landing_pages.delete_permanent')}
          </button>
        </div>
      </form>
    </div>
  </div>
{/if}

<style>
  .landing-manager-container {
    max-width: 1200px;
    margin: 0 auto;
    display: flex;
    flex-direction: column;
    gap: 2rem;
  }

  .header-section {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid var(--border-light, #e5e7eb);
    padding-bottom: 1.25rem;
  }

  .page-title {
    font-size: 1.75rem;
    font-weight: 700;
    color: var(--text-primary, #111827);
    margin: 0 0 0.375rem 0;
  }

  .page-subtitle {
    font-size: 0.875rem;
    color: var(--text-secondary, #6b7280);
    margin: 0;
  }

  .create-btn {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    background: #2563eb;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 0.625rem 1.25rem;
    font-size: 0.875rem;
    font-weight: 600;
    cursor: pointer;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
    transition: background 150ms;
  }

  .slug-cell {
    display: flex;
    align-items: center;
    gap: 0.35rem;
  }

  .copy-url-btn {
    border: 1px solid var(--border-light, #e5e7eb);
    background: var(--bg-secondary, #f9fafb);
    border-radius: 6px;
    width: 28px;
    height: 28px;
    cursor: pointer;
    font-size: 0.85rem;
    color: var(--text-secondary, #6b7280);
  }

  .copy-url-btn:hover {
    background: var(--bg-primary, #fff);
    color: var(--text-primary, #111);
  }

  .inline-form {
    display: inline;
  }

  .create-btn:hover {
    background: #1d4ed8;
  }

  .btn-icon {
    flex-shrink: 0;
  }

  .alert-error {
    background: #fef2f2;
    border: 1px solid #fca5a5;
    color: #b91c1c;
    padding: 0.875rem 1rem;
    border-radius: 8px;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.875rem;
  }

  .list-toolbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    padding: 0.9rem;
    border: 1px solid var(--border-light, #e5e7eb);
    border-radius: 12px;
    background: var(--bg-card, #ffffff);
    box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
  }

  .search-form {
    display: flex;
    align-items: center;
    flex: 1;
    max-width: 620px;
    min-width: 0;
    border: 1px solid #cbd5e1;
    border-radius: 10px;
    background: #ffffff;
    overflow: hidden;
    transition: border-color 150ms, box-shadow 150ms;
  }

  .search-form:focus-within {
    border-color: #2563eb;
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.12);
  }

  .search-icon { padding-left: 0.8rem; color: #64748b; font-size: 1.15rem; }
  .search-form input { min-width: 0; flex: 1; height: 42px; padding: 0 0.7rem; border: 0; outline: 0; background: transparent; color: #0f172a; font-size: 0.85rem; }
  .search-form input::-webkit-search-cancel-button { display: none; }
  .search-form button { align-self: stretch; padding: 0 1rem; border: 0; background: #0f172a; color: #fff; font-size: 0.78rem; font-weight: 700; cursor: pointer; }
  .search-form button:hover { background: #1d4ed8; }
  .clear-search { padding: 0.35rem 0.55rem; border-radius: 6px; color: #64748b; font-size: 0.7rem; font-weight: 650; text-decoration: none; }
  .clear-search:hover { background: #f1f5f9; color: #1d4ed8; }
  .list-summary { display: flex; align-items: baseline; gap: 0.35rem; white-space: nowrap; color: #64748b; font-size: 0.72rem; }
  .list-summary strong { color: #0f172a; font-size: 1rem; }
  .secondary-create { background: #fff; border: 1px solid #bfdbfe; color: #1d4ed8; text-decoration: none; }
  .secondary-create:hover { background: #eff6ff; }
  .pagination-wrapper :global(.pagination) { margin: 1rem 0 0.25rem; }
  .pagination-wrapper :global(.pagination-info) { margin-top: 0; }

  .empty-state-card {
    background: var(--bg-card, #ffffff);
    border: 1px solid var(--border-light, #e5e7eb);
    border-radius: 12px;
    padding: 5rem 2rem;
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  }

  .illustration-box {
    background: #eff6ff;
    color: #3b82f6;
    width: 120px;
    height: 120px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 1.5rem;
    border: 4px solid #f8fafc;
  }

  .empty-title {
    font-size: 1.25rem;
    font-weight: 600;
    color: var(--text-primary, #111827);
    margin: 0 0 0.5rem 0;
  }

  .empty-description {
    font-size: 0.875rem;
    color: var(--text-secondary, #6b7280);
    max-width: 440px;
    line-height: 1.5;
    margin: 0 0 2rem 0;
  }

  /* Tabela de Landing Pages */
  .table-container {
    background: var(--bg-card, #ffffff);
    border: 1px solid var(--border-light, #e5e7eb);
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  }

  .landing-table {
    width: 100%;
    border-collapse: collapse;
    text-align: left;
    font-size: 0.875rem;
  }

  .landing-table th {
    background: #f9fafb;
    color: #4b5563;
    font-weight: 600;
    padding: 0.875rem 1.25rem;
    border-bottom: 1px solid var(--border-light, #e5e7eb);
  }

  .landing-table td {
    padding: 1rem 1.25rem;
    border-bottom: 1px solid var(--border-light, #e5e7eb);
    vertical-align: middle;
  }

  .landing-table tbody tr:last-child td {
    border-bottom: none;
  }

  .title-cell {
    display: flex;
    flex-direction: column;
  }

  .page-name {
    font-weight: 600;
    color: var(--text-primary, #111827);
    font-size: 0.9375rem;
  }

  .slug-link {
    color: #2563eb;
    text-decoration: none;
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
    font-family: monospace;
    font-size: 0.875rem;
  }

  .slug-link:hover {
    text-decoration: underline;
  }

  .link-icon {
    opacity: 0.6;
  }

  .status-badge {
    display: inline-flex;
    font-size: 0.75rem;
    font-weight: 600;
    padding: 0.25rem 0.625rem;
    border-radius: 9999px;
  }

  .status-badge.published {
    background: #ecfdf5;
    color: #047857;
  }

  .status-badge.draft {
    background: #f3f4f6;
    color: #4b5563;
  }

  .date-txt {
    color: var(--text-secondary, #6b7280);
  }

  .actions-header {
    text-align: right;
  }

  .actions-cell {
    display: flex;
    justify-content: flex-end;
    gap: 0.5rem;
  }

  .action-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 0.375rem;
    background: var(--bg-card, #ffffff);
    border: 1px solid var(--border-light, #e5e7eb);
    border-radius: 6px;
    padding: 0.4375rem 0.75rem;
    font-size: 0.8125rem;
    font-weight: 600;
    cursor: pointer;
    color: var(--text-primary, #374151);
    transition: all 150ms;
  }

  .action-btn:hover {
    background: #f9fafb;
    border-color: #d1d5db;
  }

  .edit-btn {
    background: #eff6ff;
    color: #2563eb;
    border-color: #bfdbfe;
    text-decoration: none;
  }

  .edit-btn:hover {
    background: #dbeafe;
    border-color: #93c5fd;
  }

  .details-btn:hover {
    color: #1e3a8a;
    background: #f0fdf4;
    border-color: #bbf7d0;
  }

  .delete-btn {
    color: #dc2626;
  }

  .delete-btn:hover {
    background: #fef2f2;
    border-color: #fca5a5;
  }

  /* Modais */
  .modal-backdrop {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.4);
    backdrop-filter: blur(4px);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
    padding: 1rem;
  }

  .modal-card {
    background: var(--bg-card, #ffffff);
    border: 1px solid var(--border-light, #e5e7eb);
    border-radius: 12px;
    width: 100%;
    max-width: 500px;
    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
    padding: 1.5rem;
    display: flex;
    flex-direction: column;
    gap: 1.25rem;
  }

  .modal-card.danger-card {
    max-width: 450px;
  }

  .modal-title {
    font-size: 1.125rem;
    font-weight: 700;
    color: var(--text-primary, #111827);
    margin: 0;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .modal-title.warning-text {
    color: #dc2626;
  }

  .modal-warning-icon {
    color: #dc2626;
  }

  .modal-warning-desc {
    font-size: 0.875rem;
    color: var(--text-secondary, #4b5563);
    line-height: 1.5;
    margin: 0;
  }

  .form-group {
    display: flex;
    flex-direction: column;
    gap: 0.375rem;
    margin-bottom: 1rem;
  }

  .form-group label {
    font-size: 0.8125rem;
    font-weight: 600;
    color: var(--text-primary, #374151);
  }

  .form-group input, .form-group select {
    border: 1px solid var(--border-light, #d1d5db);
    border-radius: 6px;
    padding: 0.5rem 0.75rem;
    font-size: 0.875rem;
    background: var(--bg-card, #ffffff);
    color: var(--text-primary, #111827);
    outline: none;
  }

  .form-group input:focus, .form-group select:focus {
    border-color: #2563eb;
    box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.1);
  }

  .slug-input-wrapper {
    display: flex;
    align-items: center;
    border: 1px solid var(--border-light, #d1d5db);
    border-radius: 6px;
    overflow: hidden;
  }

  .slug-input-wrapper .prefix {
    background: #f3f4f6;
    color: #6b7280;
    font-family: monospace;
    font-size: 0.875rem;
    padding: 0.5rem 0.75rem;
    border-right: 1px solid var(--border-light, #d1d5db);
  }

  .slug-input-wrapper input {
    border: none !important;
    border-radius: 0 !important;
    flex: 1;
    box-shadow: none !important;
  }

  .modal-actions {
    display: flex;
    justify-content: flex-end;
    gap: 0.75rem;
    margin-top: 0.5rem;
  }

  .cancel-btn {
    background: var(--bg-card, #ffffff);
    border: 1px solid var(--border-light, #d1d5db);
    color: var(--text-primary, #374151);
    border-radius: 6px;
    padding: 0.5rem 1rem;
    font-size: 0.875rem;
    font-weight: 600;
    cursor: pointer;
    transition: background 150ms;
  }

  .cancel-btn:hover {
    background: #f9fafb;
  }

  .submit-btn {
    background: #2563eb;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 0.5rem 1rem;
    font-size: 0.875rem;
    font-weight: 600;
    cursor: pointer;
    transition: background 150ms;
  }

  .submit-btn:hover {
    background: #1d4ed8;
  }

  .submit-btn.danger-submit-btn {
    background: #dc2626;
  }

  .submit-btn.danger-submit-btn:hover {
    background: #b91c1c;
  }

  /* Modo Escuro (Dark Mode) */
  :global(.dark) .empty-state-card, :global(.dark) .table-container, :global(.dark) .modal-card {
    background: #1f2937;
    border-color: #374151;
  }

  :global(.dark) .list-toolbar, :global(.dark) .search-form { background: #1f2937; border-color: #374151; }
  :global(.dark) .search-form input { color: #f3f4f6; }
  :global(.dark) .list-summary strong { color: #f3f4f6; }

  @media (max-width: 720px) {
    .header-section, .list-toolbar { align-items: stretch; flex-direction: column; }
    .header-section .create-btn { justify-content: center; }
    .search-form { max-width: none; width: 100%; }
    .list-summary { justify-content: center; }
    .table-container { overflow-x: auto; }
    .landing-table { min-width: 820px; }
  }

  :global(.dark) .illustration-box {
    background: #1e293b;
    color: #60a5fa;
    border-color: #334155;
  }

  :global(.dark) .page-title, :global(.dark) .empty-title, :global(.dark) .page-name, :global(.dark) .modal-title {
    color: #f3f4f6;
  }

  :global(.dark) .page-subtitle, :global(.dark) .empty-description, :global(.dark) .date-txt, :global(.dark) .modal-warning-desc {
    color: #9ca3af;
  }

  :global(.dark) .landing-table th {
    background: #111827;
    color: #9ca3af;
    border-color: #374151;
  }

  :global(.dark) .landing-table td {
    border-color: #374151;
  }

  :global(.dark) .action-btn {
    background: #1f2937;
    border-color: #374151;
    color: #d1d5db;
  }

  :global(.dark) .action-btn:hover {
    background: #374151;
    border-color: #4b5563;
  }

  :global(.dark) .edit-btn {
    background: #1e3a8a;
    color: #3b82f6;
    border-color: #2563eb;
  }

  :global(.dark) .edit-btn:hover {
    background: #1d4ed8;
    color: #ffffff;
  }

  :global(.dark) .details-btn:hover {
    background: #064e3b;
    color: #34d399;
  }

  :global(.dark) .delete-btn {
    color: #fca5a5;
  }

  :global(.dark) .delete-btn:hover {
    background: #7f1d1d;
    border-color: #dc2626;
  }

  :global(.dark) .status-badge.draft {
    background: #374151;
    color: #d1d5db;
  }

  :global(.dark) .status-badge.published {
    background: #064e3b;
    color: #a7f3d0;
  }

  :global(.dark) .form-group label {
    color: #d1d5db;
  }

  :global(.dark) .form-group input, :global(.dark) .form-group select {
    background: #111827;
    border-color: #374151;
    color: #f3f4f6;
  }

  :global(.dark) .slug-input-wrapper .prefix {
    background: #374151;
    color: #d1d5db;
    border-color: #374151;
  }

  :global(.dark) .cancel-btn {
    background: #1f2937;
    border-color: #374151;
    color: #d1d5db;
  }

  :global(.dark) .cancel-btn:hover {
    background: #374151;
  }
</style>
