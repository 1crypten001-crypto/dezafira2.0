<script lang="ts">
  import { page } from "$app/stores";
  import { t, formatDate as fmtDate, formatMoney } from "$lib/i18n";
  import { enhance } from '$app/forms';

  let { data } = $props();
  const lang = $derived($page.data.language || 'pt');
let deletingId = $state<number | null>(null);

  const accessLabels: Record<string, string> = {
    free: 'Grátis',
    premium: 'Premium',
    paid: 'Pago'
  };
  const accessColors: Record<string, string> = {
    free: '#10b981',
    premium: '#6366f1',
    paid: '#f59e0b'
  };
</script>

<div class="page-header">
  <div>
    <h1>{t(lang, "admin.courses.heading")}</h1>
    <p class="subtitle">Gerencie os cursos da área de membros</p>
  </div>
  <a href="/admin/courses/new" class="btn btn-primary">
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
    Novo Curso
  </a>
</div>

{#if data.courses.length === 0}
  <div class="empty-state">
    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>
    <h3>Nenhum curso criado</h3>
    <p>Crie seu primeiro curso para a área de membros.</p>
    <a href="/admin/courses/new" class="btn btn-primary">Criar Primeiro Curso</a>
  </div>
{:else}
  <div class="courses-grid">
    {#each data.courses as course}
      <div class="course-card">
        {#if course.cover_image}
          <div class="course-cover">
            <img src={course.cover_image} alt={course.title} />
          </div>
        {:else}
          <div class="course-cover course-cover--placeholder">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>
          </div>
        {/if}
        <div class="course-info">
          <div class="course-meta">
            <span class="access-badge" style="background: {accessColors[course.access_type] || '#6366f1'}20; color: {accessColors[course.access_type] || '#6366f1'}">
              {accessLabels[course.access_type] || course.access_type}
              {#if course.access_type === 'paid' && course.price_cents > 0}
                · {(course.price_cents / 100).toLocaleString(lang === 'en' ? 'en-US' : lang === 'es' ? 'es-ES' : 'pt-BR', { style: 'currency', currency: 'BRL' })}
              {/if}
            </span>
            <span class="status-badge" class:published={course.published}>
              {course.published ? t(lang, 'admin.ui.published') : t(lang, 'admin.ui.draft')}
            </span>
          </div>
          <h3 class="course-title">{course.title}</h3>
          <div class="course-stats">
            <span>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"/></svg>
              {t(lang, 'admin.courses.lessons_count', { n: course.lesson_count })}
            </span>
            <span>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
              {t(lang, 'admin.courses.materials_count', { n: course.material_count })}
            </span>
          </div>
          <div class="course-actions">
            <a href="/admin/courses/{course.id}" class="btn btn-sm btn-secondary">{t(lang, "admin.ui.edit")}</a>
            <a href="/members/area/{course.slug}" target="_blank" class="btn btn-sm btn-ghost">Ver</a>
            <form method="POST" action="?/delete" use:enhance={() => {
              deletingId = course.id;
              return async ({ update }) => { deletingId = null; await update(); };
            }}>
              <input type="hidden" name="id" value={course.id} />
              <button type="submit" class="btn btn-sm btn-danger" disabled={deletingId === course.id}>
                {deletingId === course.id ? '...' : t(lang, 'admin.ui.delete')}
              </button>
            </form>
          </div>
        </div>
      </div>
    {/each}
  </div>
{/if}

<style>
  .page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 2rem; gap: 1rem; }
  h1 { font-size: 1.75rem; font-weight: 800; margin: 0 0 0.25rem 0; }
  .subtitle { color: var(--text-secondary); font-size: 0.9rem; margin: 0; }

  .empty-state {
    text-align: center; padding: 4rem 2rem;
    background: var(--bg-primary); border: 1px dashed var(--border-color);
    border-radius: var(--radius-lg); color: var(--text-secondary);
  }
  .empty-state svg { opacity: 0.3; margin-bottom: 1rem; }
  .empty-state h3 { font-size: 1.25rem; font-weight: 700; color: var(--text-primary); margin: 0 0 0.5rem; }
  .empty-state p { margin: 0 0 1.5rem; }

  .courses-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 1.5rem; }

  .course-card {
    background: var(--bg-primary); border: 1px solid var(--border-light);
    border-radius: var(--radius-lg); overflow: hidden;
    box-shadow: var(--shadow-sm); transition: box-shadow 0.2s;
  }
  .course-card:hover { box-shadow: var(--shadow-md); }

  .course-cover { height: 160px; overflow: hidden; }
  .course-cover img { width: 100%; height: 100%; object-fit: cover; }
  .course-cover--placeholder {
    background: var(--bg-tertiary); display: flex;
    align-items: center; justify-content: center; color: var(--text-muted);
  }

  .course-info { padding: 1.25rem; }
  .course-meta { display: flex; gap: 0.5rem; flex-wrap: wrap; margin-bottom: 0.75rem; }

  .access-badge {
    display: inline-block; padding: 0.2rem 0.6rem;
    border-radius: 6px; font-size: 0.75rem; font-weight: 700;
  }
  .status-badge {
    display: inline-block; padding: 0.2rem 0.6rem; border-radius: 6px;
    font-size: 0.75rem; font-weight: 700;
    background: var(--bg-tertiary); color: var(--text-muted);
  }
  .status-badge.published { background: #d1fae520; color: #10b981; }

  .course-title { font-size: 1rem; font-weight: 700; margin: 0 0 0.75rem; color: var(--text-primary); }

  .course-stats { display: flex; gap: 1rem; margin-bottom: 1rem; }
  .course-stats span {
    display: flex; align-items: center; gap: 0.35rem;
    font-size: 0.8rem; color: var(--text-muted);
  }

  .course-actions { display: flex; gap: 0.5rem; flex-wrap: wrap; }

  .btn-sm { padding: 0.35rem 0.75rem; font-size: 0.8rem; border-radius: 8px; }
  .btn-ghost { background: transparent; color: var(--text-secondary); border: 1px solid var(--border-color); text-decoration: none; display: inline-flex; align-items: center; }
  .btn-ghost:hover { background: var(--bg-secondary); }
  .btn-danger { background: #fef2f2; color: #ef4444; border: 1px solid #fee2e2; cursor: pointer; font-family: inherit; }
  .btn-danger:hover:not(:disabled) { background: #fee2e2; }
  .btn-danger:disabled { opacity: 0.5; }
</style>
