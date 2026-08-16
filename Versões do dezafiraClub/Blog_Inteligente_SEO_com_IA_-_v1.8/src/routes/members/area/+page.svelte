<script lang="ts">
  import { page } from '$app/stores';
  import { t, formatMoney } from '$lib/i18n';
  let { data } = $props();
  const lang = $derived($page.data.language || 'pt');
  const displayCurrency = $derived(($page.data.displayCurrency as string) || 'BRL');

  const accessLabel = $derived({ free: t(lang, 'members.badge_free'), premium: t(lang, 'members.badge_premium'), paid: t(lang, 'members.badge_paid') });
  const accessColor: Record<string, string> = { free: '#10b981', premium: '#6366f1', paid: '#f59e0b' };

  function formatPrice(cents: number) {
    return formatMoney(lang, cents, displayCurrency);
  }
</script>

<svelte:head>
  <title>{t(lang, "members.area_title")}</title>
  <meta name="robots" content="noindex" />
</svelte:head>

<div class="area-container">
  <div class="area-header">
    <div class="area-header-text">
      <h1>{t(lang, "members.area_title")}</h1>
      <p>{t(lang, 'members.welcome_area')}, <strong>{data.user?.username?.split('@')[0]}</strong>!</p>
    </div>
    <div class="area-header-actions">
      {#if !data.hasPremium}
        <a href="/premium" class="btn btn-accent">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
          {t(lang, "members.subscribe_premium")}
        </a>
      {/if}
      <a href="/members/dashboard" class="btn btn-secondary">{t(lang, "members.my_account")}</a>
    </div>
  </div>

  {#if data.courses.length === 0}
    <div class="empty-state">
      <div class="empty-icon">🎓</div>
      <h2>Nenhum curso disponível ainda</h2>
      <p>Em breve novos conteúdos exclusivos serão publicados aqui.</p>
    </div>
  {:else}
    <div class="courses-grid">
      {#each data.courses as course}
        <div class="course-card" class:locked={!course.hasAccess}>
          <a href={course.hasAccess ? `/members/area/${course.slug}` : '#'} class="course-link" onclick={!course.hasAccess ? (e) => e.preventDefault() : undefined}>
            <div class="course-cover">
              {#if course.cover_image}
                <img src={course.cover_image} alt={course.title} loading="lazy" />
              {:else}
                <div class="cover-placeholder">
                  <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>
                </div>
              {/if}

              {#if !course.hasAccess}
                <div class="lock-overlay">
                  <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
                </div>
              {:else}
                <div class="access-check">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20 6 9 17 4 12"/></svg>
                </div>
              {/if}
            </div>

            <div class="course-body">
              <div class="course-badges">
                <span class="badge-access" style="background:{accessColor[course.access_type]}20; color:{accessColor[course.access_type]}">
                  {accessLabel[course.access_type]}
                  {#if course.access_type === 'paid' && course.price_cents > 0}
                    · {formatPrice(course.price_cents)}
                  {/if}
                </span>
              </div>
              <h3 class="course-title">{course.title}</h3>
              {#if course.description}
                <p class="course-desc">{course.description}</p>
              {/if}
              <div class="course-meta">
                <span>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"/></svg>
                  {t(lang, "members.lessons_n", { n: String(course.lesson_count) })}
                </span>
                {#if course.material_count > 0}
                  <span>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/></svg>
                    {t(lang, "members.materials_n", { n: String(course.material_count) })}
                  </span>
                {/if}
              </div>
            </div>
          </a>

          {#if !course.hasAccess}
            <div class="course-cta">
              {#if course.access_type === 'paid'}
                <a href="/api/members/course/{course.id}/purchase" class="btn btn-primary btn-full" data-sveltekit-reload target="_blank" rel="noopener noreferrer">
                  {t(lang, "members.buy_for", { price: formatPrice(course.price_cents) })}
                </a>
                <span class="cta-or">{t(lang, "common.or")}</span>
                <a href="/premium" class="btn btn-outline btn-full">{t(lang, "members.subscribe_premium")}</a>
              {:else}
                <a href="/premium" class="btn btn-accent btn-full">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
                  {t(lang, "members.subscribe_to_access")}
                </a>
              {/if}
            </div>
          {:else}
            <a href="/members/area/{course.slug}" class="btn btn-primary btn-full course-enter">
              {t(lang, "members.access_course")}
            </a>
          {/if}
        </div>
      {/each}
    </div>
  {/if}
</div>

<style>
  .area-container { max-width: 1100px; margin: 0 auto; padding: 2rem 1.5rem 4rem; }

  .area-header {
    display: flex; justify-content: space-between; align-items: flex-start;
    gap: 1.5rem; margin-bottom: 3rem; flex-wrap: wrap;
  }
  h1 { font-size: 2rem; font-weight: 900; margin: 0 0 0.4rem; letter-spacing: -0.5px; }
  .area-header-text p { color: var(--text-secondary); margin: 0; }
  .area-header-actions { display: flex; gap: 0.75rem; align-items: center; flex-wrap: wrap; }

  .btn-accent {
    background: linear-gradient(135deg, #f59e0b, #f97316);
    color: white; border: none; display: inline-flex; align-items: center; gap: 0.4rem;
    font-weight: 700;
  }
  .btn-accent:hover { opacity: 0.9; }
  .btn-outline { border: 1px solid var(--border-color); background: transparent; color: var(--text-primary); text-decoration: none; display: inline-flex; align-items: center; justify-content: center; }
  .btn-outline:hover { background: var(--bg-secondary); }

  .empty-state {
    text-align: center; padding: 5rem 2rem;
    background: var(--bg-primary); border: 1px dashed var(--border-color);
    border-radius: var(--radius-xl);
  }
  .empty-icon { font-size: 4rem; margin-bottom: 1rem; }
  .empty-state h2 { font-size: 1.5rem; font-weight: 700; margin: 0 0 0.5rem; }
  .empty-state p { color: var(--text-secondary); }

  .courses-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 1.75rem; }

  .course-card {
    background: var(--bg-primary); border: 1px solid var(--border-light);
    border-radius: 20px; overflow: hidden; display: flex; flex-direction: column;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06); transition: transform 0.2s, box-shadow 0.2s;
  }
  .course-card:hover { transform: translateY(-3px); box-shadow: 0 8px 28px rgba(0,0,0,0.1); }
  .course-card.locked { opacity: 0.9; }

  .course-link { text-decoration: none; color: inherit; display: block; }
  .course-cover { position: relative; height: 200px; overflow: hidden; background: var(--bg-tertiary); }
  .course-cover img { width: 100%; height: 100%; object-fit: cover; transition: transform 0.4s; }
  .course-card:hover .course-cover img { transform: scale(1.04); }
  .cover-placeholder { height: 100%; display: flex; align-items: center; justify-content: center; color: var(--text-muted); }

  .lock-overlay {
    position: absolute; inset: 0; background: rgba(0,0,0,0.5);
    display: flex; align-items: center; justify-content: center; color: white;
  }
  .access-check {
    position: absolute; top: 0.75rem; right: 0.75rem;
    background: #10b981; color: white; border-radius: 50%;
    width: 28px; height: 28px; display: flex; align-items: center; justify-content: center;
    box-shadow: 0 2px 8px rgba(16,185,129,0.4);
  }

  .course-body { padding: 1.25rem; flex: 1; }
  .course-badges { margin-bottom: 0.6rem; }
  .badge-access { display: inline-block; padding: 0.2rem 0.6rem; border-radius: 6px; font-size: 0.72rem; font-weight: 700; }
  .course-title { font-size: 1.05rem; font-weight: 700; margin: 0 0 0.5rem; color: var(--text-primary); }
  .course-desc { font-size: 0.85rem; color: var(--text-secondary); margin: 0 0 0.75rem; line-height: 1.5; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
  .course-meta { display: flex; gap: 1rem; }
  .course-meta span { display: flex; align-items: center; gap: 0.35rem; font-size: 0.8rem; color: var(--text-muted); }

  .course-cta, .course-enter {
    padding: 1rem 1.25rem; border-top: 1px solid var(--border-light);
    display: flex; flex-direction: column; gap: 0.5rem;
  }
  .course-enter { text-align: center; font-weight: 700; border-radius: 0; text-decoration: none; justify-content: center; }
  .btn-full { width: 100%; text-align: center; justify-content: center; }
  .cta-or { text-align: center; font-size: 0.75rem; color: var(--text-muted); }

  @media (max-width: 600px) {
    .courses-grid { grid-template-columns: 1fr; }
    h1 { font-size: 1.6rem; }
  }
</style>
