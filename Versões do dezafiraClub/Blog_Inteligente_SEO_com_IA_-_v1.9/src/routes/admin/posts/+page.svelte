<script lang="ts">
  import { page } from "$app/stores";
  import { t, formatDate as fmtDate, formatMoney } from "$lib/i18n";

let { data } = $props();
  const lang = $derived($page.data.language || 'pt');
function formatDate(dateString: string) {
    const date = new Date(dateString);
    return date.toLocaleDateString(lang === 'en' ? 'en-US' : lang === 'es' ? 'es-ES' : 'pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    });
  }

  function handleDelete(event: Event) {
    if (!confirm(t(lang, 'admin.ui.confirm_delete'))) {
      event.preventDefault();
    }
  }
</script>

<svelte:head>
  <title>{t(lang, "admin.posts.title")}</title>
</svelte:head>

<div class="admin-header">
  <h1 class="admin-title">{t(lang, "admin.posts.heading")}</h1>
  <a href="/admin/posts/new" class="btn btn-primary">{t(lang, "admin.posts.new")}</a>
</div>

{#if data.posts.length === 0}
  <div class="empty-state">
    <p>{t(lang, "admin.posts.empty")}</p>
    <a href="/admin/posts/new" class="btn btn-primary">{t(lang, "admin.posts.create_first")}</a>
  </div>
{:else}
  <div class="admin-table-container">
    <table class="table">
      <thead>
        <tr>
          <th>{t(lang, "admin.ui.title")}</th>
          <th>{t(lang, "admin.ui.slug")}</th>
          <th>{t(lang, "admin.ui.date")}</th>
          <th>{t(lang, "admin.ui.status")}</th>
          <th>{t(lang, "admin.ui.actions")}</th>
        </tr>
      </thead>
      <tbody>
        {#each data.posts as post}
          <tr>
            <td>
              <a href="/admin/posts/{post.id}">{post.title}</a>
            </td>
            <td style="font-family: monospace; font-size: 0.875rem;">{post.slug}</td>
            <td>{formatDate(post.created_at)}</td>
            <td>
              <span class="status status-{post.published ? 'published' : 'draft'}">
                {post.published ? t(lang, 'admin.ui.published') : t(lang, 'admin.ui.draft')}
              </span>
            </td>
            <td>
              <div class="actions">
                <a href="/admin/posts/{post.id}" class="btn btn-small">{t(lang, "admin.ui.edit")}</a>
                <form action="/admin/posts/{post.id}/delete" method="POST" style="display: inline;">
                  <button type="submit" class="btn btn-small btn-danger" onclick={handleDelete}>{t(lang, "admin.ui.delete")}</button>
                </form>
              </div>
            </td>
          </tr>
        {/each}
      </tbody>
    </table>
  </div>
{/if}

<style>
  .admin-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 2rem;
  }

  .admin-title {
    font-family: var(--font-sans);
    font-size: 1.5rem;
    font-weight: 700;
    margin: 0;
  }

  .admin-table-container {
    background: var(--bg-primary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-lg);
    overflow-x: auto;
    width: 100%;
  }

  /* Status and actions remain the same */
  .status {
    display: inline-block;
    padding: 0.25rem 0.5rem;
    font-family: var(--font-sans);
    font-size: 0.625rem;
    text-transform: uppercase;
    letter-spacing: 1px;
    border-radius: var(--radius-sm);
  }

  .status-published {
    background: #efe;
    color: #060;
  }

  .status-draft {
    background: #fee;
    color: #c00;
  }

  .actions {
    display: flex;
    gap: 0.5rem;
  }

  .btn-danger {
    border-color: #c00;
    color: #c00;
  }

  .btn-danger:hover {
    background: #c00;
    color: white;
  }

  @media (max-width: 640px) {
    .admin-header {
      flex-direction: column;
      align-items: flex-start;
      gap: 1rem;
    }

    .admin-title {
      font-size: 1.75rem;
    }
  }
</style>
