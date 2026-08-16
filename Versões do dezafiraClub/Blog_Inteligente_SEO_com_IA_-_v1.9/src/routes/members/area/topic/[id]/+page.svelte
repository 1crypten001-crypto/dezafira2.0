<script lang="ts">
  import { page } from '$app/stores';
  import { enhance } from '$app/forms';
  import { t } from '$lib/i18n';

  let { data } = $props();
  const lang = $derived($page.data.language || 'pt');

  let commentContent = $state('');
  let isSubmitting = $state(false);

  function formatDate(dateStr: string) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleDateString(lang === 'pt' ? 'pt-BR' : 'en-US', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }

  function getUserBadge(role: string) {
    if (role === 'admin') return { label: '🛡️ Admin', class: 'badge-admin' };
    return { label: '⭐ Membro VIP', class: 'badge-vip' };
  }
</script>

<svelte:head>
  <title>{data.topic.title} | Comunidade VIP</title>
  <meta name="robots" content="noindex" />
</svelte:head>

<div class="topic-container">
  <div class="top-nav">
    <a href="/members/area" class="back-link">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="15 18 9 12 15 6"/></svg>
      Voltar para Comunidade
    </a>
  </div>

  <article class="topic-card">
    <header class="topic-header">
      <div class="topic-meta">
        <span class="category-badge">{data.topic.category}</span>
        {#if data.topic.is_pinned}
          <span class="pinned-badge">📌 Fixado</span>
        {/if}
      </div>
      <h1 class="topic-title">{data.topic.title}</h1>
      <div class="author-bar">
        <div class="author-avatar">
          {data.topic.user_email[0].toUpperCase()}
        </div>
        <div class="author-info">
          <div class="author-name">
            {data.topic.user_email.split('@')[0]}
            <span class="badge {getUserBadge(data.topic.user_role).class}">
              {getUserBadge(data.topic.user_role).label}
            </span>
          </div>
          <time class="topic-date">{formatDate(data.topic.created_at)}</time>
        </div>
      </div>
    </header>

    <div class="topic-body">
      {data.topic.content}
    </div>

    <footer class="topic-footer">
      <div class="footer-actions">
        <form method="POST" action="?/toggleLike" use:enhance>
          <button type="submit" class="btn-like" class:liked={data.topic.user_has_liked}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill={data.topic.user_has_liked ? "currentColor" : "none"} stroke="currentColor" stroke-width="2"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>
            <span>{data.topic.likes_count} Curtidas</span>
          </button>
        </form>

        <span class="comments-count">
          💬 {data.comments.length} Respostas
        </span>
      </div>

      {#if data.user && (data.user.id === data.topic.user_id || data.user.role === 'admin')}
        <form method="POST" action="?/deleteTopic" use:enhance>
          <input type="hidden" name="topic_id" value={data.topic.id} />
          <button type="submit" class="btn-delete" onclick={(e) => { if (!confirm('Tem certeza que deseja excluir esta discussão?')) e.preventDefault(); }}>
            🗑️ Excluir Tópico
          </button>
        </form>
      {/if}
    </footer>
  </article>

  <!-- Seção de Comentários / Respostas -->
  <section class="comments-section">
    <h2>Respostas ({data.comments.length})</h2>

    <!-- Form de Nova Resposta -->
    <form method="POST" action="?/addComment" class="comment-form" use:enhance={() => {
      isSubmitting = true;
      return async ({ update }) => {
        isSubmitting = false;
        commentContent = '';
        await update();
      };
    }}>
      <div class="form-group">
        <textarea
          name="content"
          rows="3"
          placeholder="Escreva sua resposta para a comunidade..."
          bind:value={commentContent}
          required
        ></textarea>
      </div>
      <button type="submit" class="btn btn-primary" disabled={isSubmitting || !commentContent.trim()}>
        {isSubmitting ? 'Enviando...' : '💬 Responder'}
      </button>
    </form>

    <!-- Lista de Comentários -->
    <div class="comments-list">
      {#if data.comments.length === 0}
        <div class="no-comments">
          <p>Nenhuma resposta ainda. Seja o primeiro a participar da conversa!</p>
        </div>
      {:else}
        {#each data.comments as comment}
          <div class="comment-card">
            <div class="comment-header">
              <div class="comment-author">
                <div class="avatar-small">{comment.user_email[0].toUpperCase()}</div>
                <div>
                  <strong class="comment-name">{comment.user_email.split('@')[0]}</strong>
                  <span class="badge {getUserBadge(comment.user_role).class}">
                    {getUserBadge(comment.user_role).label}
                  </span>
                </div>
              </div>
              <div class="comment-actions">
                <time class="comment-date">{formatDate(comment.created_at)}</time>
                {#if data.user && (data.user.id === comment.user_id || data.user.role === 'admin')}
                  <form method="POST" action="?/deleteComment" use:enhance>
                    <input type="hidden" name="comment_id" value={comment.id} />
                    <input type="hidden" name="topic_id" value={data.topic.id} />
                    <button type="submit" class="btn-icon-delete" title="Excluir resposta" onclick={(e) => { if (!confirm('Excluir esta resposta?')) e.preventDefault(); }}>
                      ✕
                    </button>
                  </form>
                {/if}
              </div>
            </div>
            <div class="comment-content">
              {comment.content}
            </div>
          </div>
        {/each}
      {/if}
    </div>
  </section>
</div>

<style>
  .topic-container { max-width: 900px; margin: 0 auto; padding: 2rem 1.5rem 4rem; }
  .top-nav { margin-bottom: 1.5rem; }
  .back-link { display: inline-flex; align-items: center; gap: 0.4rem; color: var(--text-secondary); text-decoration: none; font-weight: 600; font-size: 0.9rem; }
  .back-link:hover { color: var(--text-primary); }

  .topic-card {
    background: var(--bg-primary); border: 1px solid var(--border-light);
    border-radius: 20px; padding: 2rem; box-shadow: 0 4px 20px rgba(0,0,0,0.06);
    margin-bottom: 2.5rem;
  }

  .topic-meta { display: flex; gap: 0.5rem; margin-bottom: 0.75rem; }
  .category-badge { background: rgba(99,102,241,0.12); color: #6366f1; padding: 0.25rem 0.75rem; border-radius: 6px; font-weight: 700; font-size: 0.75rem; }
  .pinned-badge { background: rgba(245,158,11,0.12); color: #f59e0b; padding: 0.25rem 0.75rem; border-radius: 6px; font-weight: 700; font-size: 0.75rem; }

  .topic-title { font-family: var(--font-serif); font-size: clamp(1.5rem, 3.5vw, 2.2rem); font-weight: 600; margin: 0 0 1.25rem; color: var(--text-primary); line-height: 1.3; }

  .author-bar { display: flex; align-items: center; gap: 0.75rem; padding-bottom: 1.25rem; border-bottom: 1px solid var(--border-light); margin-bottom: 1.5rem; }
  .author-avatar { width: 40px; height: 40px; border-radius: 50%; background: var(--bg-tertiary); border: 1px solid var(--border-color); color: var(--text-primary); display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 1rem; }
  .author-info { display: flex; flex-direction: column; gap: 0.1rem; }
  .author-name { font-weight: 700; font-size: 0.95rem; display: flex; align-items: center; gap: 0.5rem; color: var(--text-primary); }
  .topic-date { font-size: 0.78rem; color: var(--text-muted); }

  .badge { font-size: 0.7rem; padding: 0.15rem 0.5rem; border-radius: 4px; font-weight: 700; }
  .badge-admin { background: rgba(239,68,68,0.12); color: #ef4444; }
  .badge-vip { background: rgba(245,158,11,0.15); color: #d97706; }

  .topic-body { font-size: 1.05rem; line-height: 1.75; color: var(--text-primary); margin-bottom: 2rem; white-space: pre-wrap; word-break: break-word; }

  .topic-footer { display: flex; justify-content: space-between; align-items: center; border-top: 1px solid var(--border-light); padding-top: 1.25rem; flex-wrap: wrap; gap: 1rem; }
  .footer-actions { display: flex; align-items: center; gap: 1.25rem; }

  .btn-like {
    background: var(--bg-primary); border: 1px solid var(--border-color); color: var(--text-primary);
    padding: 0.5rem 1rem; border-radius: 30px; font-weight: 700; font-size: 0.88rem;
    display: inline-flex; align-items: center; gap: 0.4rem; cursor: pointer; transition: all var(--transition-fast);
  }
  .btn-like:hover { background: rgba(239,68,68,0.08); color: #ef4444; border-color: #ef4444; }
  .btn-like.liked { background: rgba(239,68,68,0.12); color: #ef4444; border-color: #ef4444; }

  .comments-count { font-size: 0.9rem; color: var(--text-secondary); font-weight: 600; }
  .btn-delete { background: transparent; border: none; color: #ef4444; font-weight: 600; font-size: 0.85rem; cursor: pointer; }
  .btn-delete:hover { text-decoration: underline; }

  .comments-section h2 { font-family: var(--font-serif); font-size: 1.3rem; font-weight: 600; margin-bottom: 1.25rem; color: var(--text-primary); }
  .comment-form { margin-bottom: 2rem; background: var(--bg-primary); padding: 1.25rem; border-radius: var(--radius-lg); border: 1px solid var(--border-light); }
  .comment-form textarea {
    width: 100%; border: 1px solid var(--border-color); border-radius: var(--radius-md); padding: 0.75rem;
    background: var(--bg-secondary); color: var(--text-primary); font-family: inherit; font-size: 0.95rem; resize: vertical; margin-bottom: 0.75rem;
  }

  .comments-list { display: flex; flex-direction: column; gap: 1rem; }
  .no-comments { text-align: center; padding: 2rem; background: var(--bg-primary); border-radius: var(--radius-md); border: 1px dashed var(--border-color); color: var(--text-secondary); }

  .comment-card { background: var(--bg-primary); border: 1px solid var(--border-light); border-radius: var(--radius-md); padding: 1.25rem; }
  .comment-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem; }
  .comment-author { display: flex; align-items: center; gap: 0.6rem; }
  .avatar-small { width: 30px; height: 30px; border-radius: 50%; background: var(--bg-tertiary); border: 1px solid var(--border-color); display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 0.85rem; color: var(--text-primary); }
  .comment-name { font-size: 0.9rem; color: var(--text-primary); }
  .comment-actions { display: flex; align-items: center; gap: 0.75rem; }
  .comment-date { font-size: 0.75rem; color: var(--text-muted); }
  .btn-icon-delete { background: transparent; border: none; color: var(--text-muted); cursor: pointer; font-size: 0.9rem; padding: 0.2rem; }
  .btn-icon-delete:hover { color: #ef4444; }
  .comment-content { font-size: 0.95rem; line-height: 1.6; color: var(--text-primary); white-space: pre-wrap; word-break: break-word; }
</style>
