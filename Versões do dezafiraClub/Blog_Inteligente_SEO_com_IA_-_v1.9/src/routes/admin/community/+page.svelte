<script lang="ts">
  import { page } from '$app/stores';
  import { enhance } from '$app/forms';
  import { t } from '$lib/i18n';

  let { data } = $props();
  const lang = $derived($page.data.language || 'pt');

  function formatDate(dateStr: string) {
    if (!dateStr) return '';
    return new Date(dateStr).toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }
</script>

<svelte:head>
  <title>Gerenciar Comunidade VIP | Painel Admin</title>
</svelte:head>

<div class="admin-page-header">
  <div>
    <h1>💬 Gerenciar Comunidade VIP</h1>
    <p class="subtitle">Modere discussões, fixe comunicados oficiais e gerencie o engajamento dos membros.</p>
  </div>
  <a href="/members/area" target="_blank" class="btn btn-outline">
    👁️ Abrir Comunidade
  </a>
</div>

<!-- Cards de Estatísticas -->
<div class="stats-grid">
  <div class="stat-card">
    <div class="stat-icon">💬</div>
    <div class="stat-info">
      <span class="stat-value">{data.stats.totalTopics}</span>
      <span class="stat-label">Tópicos Criados</span>
    </div>
  </div>

  <div class="stat-card">
    <div class="stat-icon">🗣️</div>
    <div class="stat-info">
      <span class="stat-value">{data.stats.totalComments}</span>
      <span class="stat-label">Respostas / Comentários</span>
    </div>
  </div>

  <div class="stat-card">
    <div class="stat-icon">❤️</div>
    <div class="stat-info">
      <span class="stat-value">{data.stats.totalLikes}</span>
      <span class="stat-label">Curtidas Totais</span>
    </div>
  </div>
</div>

<!-- Tabela de Tópicos -->
<div class="card">
  <div class="table-wrapper">
    <table class="data-table">
      <thead>
        <tr>
          <th>Status</th>
          <th>Tópico / Título</th>
          <th>Autor</th>
          <th>Categoria</th>
          <th>Engajamento</th>
          <th>Data</th>
          <th class="actions-col">Ações</th>
        </tr>
      </thead>
      <tbody>
        {#if data.topics.length === 0}
          <tr>
            <td colspan="7" class="empty-cell">Nenhum tópico publicado na comunidade ainda.</td>
          </tr>
        {:else}
          {#each data.topics as topic}
            <tr class:row-pinned={topic.is_pinned}>
              <td>
                {#if topic.is_pinned}
                  <span class="status-badge status-pinned">📌 Fixado</span>
                {:else}
                  <span class="status-badge status-normal">Normal</span>
                {/if}
              </td>
              <td>
                <a href="/members/area/topic/{topic.id}" target="_blank" class="topic-link-title">
                  {topic.title}
                </a>
              </td>
              <td>
                <div class="author-cell">
                  <span class="author-email">{topic.user_email}</span>
                  {#if topic.user_role === 'admin'}
                    <span class="badge-sm badge-admin">Admin</span>
                  {/if}
                </div>
              </td>
              <td>
                <span class="cat-pill">{topic.category}</span>
              </td>
              <td>
                <span class="engagement">❤️ {topic.likes_count} · 💬 {topic.comments_count}</span>
              </td>
              <td>{formatDate(topic.created_at)}</td>
              <td>
                <div class="action-buttons">
                  <form method="POST" action="?/togglePin" use:enhance>
                    <input type="hidden" name="topic_id" value={topic.id} />
                    <input type="hidden" name="is_pinned" value={topic.is_pinned ? 'true' : 'false'} />
                    <button type="submit" class="btn-sm btn-pin" title={topic.is_pinned ? 'Desfixar Tópico' : 'Fixar no Topo'}>
                      {topic.is_pinned ? '📌 Desfixar' : '📌 Fixar'}
                    </button>
                  </form>

                  <form method="POST" action="?/deleteTopic" use:enhance>
                    <input type="hidden" name="topic_id" value={topic.id} />
                    <button type="submit" class="btn-sm btn-delete" title="Excluir Tópico" onclick={(e) => { if (!confirm('Tem certeza que deseja excluir esta discussão permanentemente?')) e.preventDefault(); }}>
                      🗑️ Excluir
                    </button>
                  </form>
                </div>
              </td>
            </tr>
          {/each}
        {/if}
      </tbody>
    </table>
  </div>
</div>

<style>
  .admin-page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 2rem; flex-wrap: wrap; gap: 1rem; }
  h1 { font-size: 1.8rem; font-weight: 800; margin: 0 0 0.25rem; }
  .subtitle { color: var(--text-secondary); margin: 0; }

  .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1.25rem; margin-bottom: 2rem; }
  .stat-card {
    background: var(--bg-primary); border: 1px solid var(--border-light); border-radius: 16px;
    padding: 1.25rem; display: flex; align-items: center; gap: 1.25rem; box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  }
  .stat-icon { font-size: 2.2rem; }
  .stat-info { display: flex; flex-direction: column; }
  .stat-value { font-size: 1.6rem; font-weight: 900; color: var(--text-primary); }
  .stat-label { font-size: 0.82rem; color: var(--text-secondary); font-weight: 600; }

  .card { background: var(--bg-primary); border: 1px solid var(--border-light); border-radius: 16px; overflow: hidden; }
  .table-wrapper { overflow-x: auto; }
  .data-table { width: 100%; border-collapse: collapse; font-size: 0.9rem; text-align: left; }
  .data-table th, .data-table td { padding: 1rem 1.25rem; border-bottom: 1px solid var(--border-light); }
  .data-table th { background: var(--bg-tertiary); font-weight: 700; color: var(--text-secondary); }

  .row-pinned { background: rgba(245,158,11,0.03); }

  .topic-link-title { font-weight: 700; color: var(--text-primary); text-decoration: none; }
  .topic-link-title:hover { color: #6366f1; text-decoration: underline; }

  .status-badge { font-size: 0.72rem; padding: 0.2rem 0.6rem; border-radius: 12px; font-weight: 800; }
  .status-pinned { background: rgba(245,158,11,0.15); color: #d97706; }
  .status-normal { background: var(--bg-tertiary); color: var(--text-muted); }

  .author-cell { display: flex; align-items: center; gap: 0.4rem; }
  .badge-sm { font-size: 0.65rem; padding: 0.1rem 0.4rem; border-radius: 4px; font-weight: 700; }
  .badge-admin { background: #ef4444; color: white; }

  .cat-pill { background: rgba(99,102,241,0.1); color: #6366f1; padding: 0.2rem 0.5rem; border-radius: 6px; font-weight: 700; font-size: 0.75rem; }
  .engagement { font-weight: 600; font-size: 0.85rem; color: var(--text-secondary); }

  .action-buttons { display: flex; gap: 0.4rem; }
  .btn-sm { padding: 0.35rem 0.65rem; font-size: 0.78rem; font-weight: 700; border-radius: 6px; cursor: pointer; border: 1px solid transparent; }
  .btn-pin { background: var(--bg-tertiary); border-color: var(--border-color); color: var(--text-primary); }
  .btn-pin:hover { background: rgba(245,158,11,0.15); color: #d97706; }
  .btn-delete { background: rgba(239,68,68,0.1); color: #ef4444; }
  .btn-delete:hover { background: #ef4444; color: white; }

  .empty-cell { text-align: center; color: var(--text-muted); padding: 3rem; }
</style>
