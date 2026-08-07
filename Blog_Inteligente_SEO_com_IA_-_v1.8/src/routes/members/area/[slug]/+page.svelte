<script lang="ts">
  import { page } from '$app/stores';
  import { t, formatMoney } from '$lib/i18n';
  let { data } = $props();
  const lang = $derived($page.data.language || 'pt');
  const displayCurrency = $derived(($page.data.displayCurrency as string) || 'BRL');

  let activeLesson = $state(data.selectedLesson);
  let videoData = $state<{ videoId: string; videoType: string } | null>(null);
  let videoLoading = $state(false);
  let videoError = $state('');
  let sidebarOpen = $state(false);

  // Group lessons by topic for timeline
  const groupedLessons = $derived(() => {
    const groups: { topic: string | null; lessons: any[] }[] = [];
    for (const lesson of data.lessons) {
      const topic = lesson.topic || null;
      const last = groups[groups.length - 1];
      if (last && last.topic === topic) {
        last.lessons.push(lesson);
      } else {
        groups.push({ topic, lessons: [lesson] });
      }
    }
    return groups;
  });

  // Flat index for prev/next navigation
  const lessonIndex = $derived(data.lessons.findIndex((l: any) => l.id === activeLesson?.id));
  const prevLesson = $derived(lessonIndex > 0 ? data.lessons[lessonIndex - 1] : null);
  const nextLesson = $derived(lessonIndex < data.lessons.length - 1 ? data.lessons[lessonIndex + 1] : null);

  async function selectLesson(lesson: any) {
    if (!data.hasAccess && !lesson.is_preview) {
      videoError = t(lang, 'members.no_lesson_access');
      return;
    }
    const url = new URL($page.url);
    url.searchParams.set('aula', lesson.id);
    history.pushState({}, '', url.toString());

    videoData = null;
    videoError = '';
    activeLesson = { ...lesson };
    sidebarOpen = false;

    if (lesson.has_video) await loadVideo(lesson.id);
  }

  async function loadVideo(lessonId: number) {
    videoLoading = true;
    try {
      const res = await fetch(`/api/members/lesson/${lessonId}/video`);
      if (!res.ok) { videoError = t(lang, "members.no_video_access"); return; }
      videoData = await res.json();
    } catch {
      videoError = t(lang, "members.video_error");
    } finally {
      videoLoading = false;
    }
  }

  $effect(() => {
    if (activeLesson?.has_video && data.hasAccess) {
      loadVideo(activeLesson.id);
    }
  });

  function getVideoEmbedUrl(videoId: string, videoType: string) {
    if (videoType === 'youtube')
      return `https://www.youtube.com/embed/${videoId}?rel=0&modestbranding=1&showinfo=0&controls=1`;
    if (videoType === 'vimeo')
      return `https://player.vimeo.com/video/${videoId}?dnt=1`;
    return '';
  }

  function formatPrice(cents: number) {
    return formatMoney(lang, cents, displayCurrency);
  }

  function completedCount() {
    return 0; // future: track completed lessons
  }
</script>

<svelte:head>
  <title>{data.course.title} | {t(lang, "members.area_title")}</title>
  <meta name="robots" content="noindex" />
</svelte:head>

<div class="course-page">

  <!-- ── Hero Header ───────────────────────────────── -->
  <div class="course-hero" style={data.course.cover_image ? `--hero-bg: url('${data.course.cover_image}')` : ''}>
    <div class="hero-overlay">
      <div class="hero-content">
        <a href="/members/area" class="back-pill">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M19 12H5M12 5l-7 7 7 7"/></svg>
          {t(lang, "members.area_title")}
        </a>
        <h1>{data.course.title}</h1>
        {#if data.course.description}
          <p class="hero-desc">{data.course.description}</p>
        {/if}
        <div class="hero-stats">
          <span class="stat">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"/></svg>
            {t(lang, "members.lessons_n", { n: String(data.lessons.length) })}
          </span>
          {#if data.materials.length > 0}
            <span class="stat">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/></svg>
              {t(lang, "members.materials_n", { n: String(data.materials.length) })}
            </span>
          {/if}
          {#if data.hasAccess}
            <span class="stat access-badge">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
              {t(lang, "members.full_access")}
            </span>
          {/if}
        </div>
      </div>
    </div>
  </div>

  <!-- ── Sem acesso ─────────────────────────────────── -->
  {#if !data.hasAccess}
    <div class="paywall-wrap">
      <div class="paywall-card">
        <div class="paywall-lock">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0110 0v4"/></svg>
        </div>
        <h2>{t(lang, "members.exclusive")}</h2>
        {#if data.course.access_type === 'paid'}
          <p>{@html t(lang, "members.course_paid_desc", { price: formatPrice(data.course.price_cents) })}</p>
          <div class="paywall-actions">
            <a href="/api/members/course/{data.course.id}/purchase" class="btn-buy" target="_blank" rel="noopener noreferrer">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
              {t(lang, "members.buy_for", { price: formatPrice(data.course.price_cents) })}
            </a>
            <a href="/premium" class="btn-premium">{t(lang, "members.view_plans")}</a>
          </div>
        {:else}
          <p>{t(lang, "members.course_premium_only")}</p>
          <a href="/premium" class="btn-buy">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
            {t(lang, "members.view_plans")}
          </a>
        {/if}
      </div>

      <!-- Aulas preview disponíveis -->
      {#if data.lessons.some((l: any) => l.is_preview)}
        <div class="preview-block">
          <h3>{t(lang, "members.free_previews_title")}</h3>
          <div class="preview-list">
            {#each data.lessons.filter((l: any) => l.is_preview) as lesson}
              <button class="preview-lesson-btn" onclick={() => selectLesson(lesson)}>
                <span class="plb-icon">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"/></svg>
                </span>
                <span class="plb-title">{lesson.title}</span>
                <span class="plb-tag">Preview</span>
              </button>
            {/each}
          </div>
        </div>
      {/if}
    </div>

  {:else}
    <!-- ── Layout principal ──────────────────────────── -->
    <div class="main-layout">

      <!-- Toggle mobile -->
      <button class="mobile-toggle" onclick={() => sidebarOpen = !sidebarOpen}>
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>
        {sidebarOpen ? t(lang, 'common.close') : t(lang, "members.course_content")}
      </button>

      <!-- ── SIDEBAR / TIMELINE ──────────────────────── -->
      <aside class="course-sidebar" class:open={sidebarOpen}>
        <div class="sidebar-top">
          <div class="sidebar-title">Conteúdo</div>
          <span class="sidebar-count">{data.lessons.length} aulas</span>
        </div>

        <div class="timeline">
          {#each groupedLessons() as group}
            <!-- Módulo / tópico -->
            {#if group.topic}
              <div class="timeline-module">
                <span class="module-line"></span>
                <span class="module-label">{group.topic}</span>
              </div>
            {/if}

            <!-- Aulas do grupo -->
            {#each group.lessons as lesson, li}
              {@const isActive = activeLesson?.id === lesson.id}
              {@const isLocked = !lesson.is_preview && !data.hasAccess}
              <button
                class="timeline-lesson"
                class:active={isActive}
                class:locked={isLocked}
                onclick={() => selectLesson(lesson)}
              >
                <!-- Bolinha da timeline -->
                <div class="tl-dot-col">
                  <div class="tl-line top" class:invisible={group.topic === null && li === 0 && groupedLessons().indexOf(group) === 0}></div>
                  <div class="tl-dot" class:active={isActive}>
                    {#if isActive}
                      <svg width="10" height="10" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"/></svg>
                    {:else if isLocked}
                      <svg width="9" height="9" viewBox="0 0 24 24" fill="currentColor"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0110 0v4" fill="none" stroke="currentColor" stroke-width="2"/></svg>
                    {:else}
                      <span class="tl-num">{data.lessons.indexOf(lesson) + 1}</span>
                    {/if}
                  </div>
                  <div class="tl-line bottom"></div>
                </div>

                <!-- Info da aula -->
                <div class="tl-info">
                  <span class="tl-title">{lesson.title}</span>
                  <div class="tl-badges">
                    {#if lesson.has_video}
                      <span class="tl-badge video">
                        <svg width="9" height="9" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"/></svg>
                        Vídeo
                      </span>
                    {/if}
                    {#if lesson.is_preview}
                      <span class="tl-badge preview">Free</span>
                    {/if}
                  </div>
                </div>
              </button>
            {/each}
          {/each}
        </div>

        <!-- Materiais -->
        {#if data.materials.length > 0}
          <div class="sidebar-materials">
            <div class="mat-header">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/></svg>
              {t(lang, "members.course_materials")}
            </div>
            {#each data.materials as mat}
              <a href={mat.file_url} target="_blank" rel="noopener" class="mat-link" download>
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                {mat.title}
                {#if mat.file_type}<span class="mat-ext">.{mat.file_type}</span>{/if}
              </a>
            {/each}
          </div>
        {/if}
      </aside>

      <!-- ── CONTEÚDO DA AULA ─────────────────────────── -->
      <main class="lesson-main">
        {#if activeLesson}
          <!-- Player -->
          {#if activeLesson.has_video}
            <div class="video-player">
              {#if videoLoading}
                <div class="player-state">
                  <div class="spinner"></div>
                  <span>{t(lang, "members.loading_video")}</span>
                </div>
              {:else if videoError}
                <div class="player-state error">
                  <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                  <p>{videoError}</p>
                </div>
              {:else if videoData}
                <iframe
                  src={getVideoEmbedUrl(videoData.videoId, videoData.videoType)}
                  title={activeLesson.title}
                  frameborder="0"
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                  allowfullscreen
                ></iframe>
              {/if}
            </div>
          {/if}

          <!-- Título e badges -->
          <div class="lesson-header">
            <div class="lesson-header-top">
              <h2>{activeLesson.title}</h2>
              {#if activeLesson.is_preview && !data.hasAccess}
                <span class="badge-preview-inline">{t(lang, "members.free_preview")}</span>
              {/if}
            </div>
            {#if activeLesson.topic}
              <p class="lesson-topic-label">{activeLesson.topic}</p>
            {/if}
          </div>

          <!-- Conteúdo HTML -->
          {#if activeLesson.content}
            <div class="lesson-body">
              {@html activeLesson.content}
            </div>
          {/if}

          <!-- Navegação anterior / próxima -->
          <div class="lesson-nav">
            {#if prevLesson}
              <button class="nav-btn prev" onclick={() => selectLesson(prevLesson)}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 18l-6-6 6-6"/></svg>
                <div class="nav-text">
                  <span class="nav-label">{t(lang, "common.previous")}</span>
                  <span class="nav-title">{prevLesson.title}</span>
                </div>
              </button>
            {:else}
              <div></div>
            {/if}
            {#if nextLesson}
              <button class="nav-btn next" onclick={() => selectLesson(nextLesson)}>
                <div class="nav-text">
                  <span class="nav-label">{t(lang, "common.next")}</span>
                  <span class="nav-title">{nextLesson.title}</span>
                </div>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 18l6-6-6-6"/></svg>
              </button>
            {:else}
              <div class="course-completed">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
                {t(lang, "members.course_done")}
              </div>
            {/if}
          </div>

        {:else}
          <div class="empty-state">
            <svg width="56" height="56" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="0.8"><polygon points="5 3 19 12 5 21 5 3"/></svg>
            <p>{t(lang, "members.select_lesson")}</p>
          </div>
        {/if}
      </main>
    </div>
  {/if}
</div>

<style>
  /* ── Reset & Base ────────────────────────────────── */
  .course-page { min-height: 80vh; background: var(--bg-secondary, #f8f9fa); }

  /* ── Hero ────────────────────────────────────────── */
  .course-hero {
    background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
    background-image: var(--hero-bg);
    background-size: cover; background-position: center;
    position: relative;
  }
  .hero-overlay {
    background: linear-gradient(135deg, rgba(15,12,41,0.88) 0%, rgba(48,43,99,0.75) 100%);
    padding: 3.5rem 1.5rem 3rem;
  }
  .hero-content { max-width: 960px; margin: 0 auto; }

  .back-pill {
    display: inline-flex; align-items: center; gap: 0.4rem;
    background: rgba(255,255,255,0.12); backdrop-filter: blur(8px);
    color: rgba(255,255,255,0.9); text-decoration: none;
    padding: 0.35rem 0.875rem; border-radius: 999px; font-size: 0.8rem;
    margin-bottom: 1.25rem; transition: background 0.2s;
  }
  .back-pill:hover { background: rgba(255,255,255,0.2); }

  h1 {
    font-size: clamp(1.6rem, 4vw, 2.6rem); font-weight: 900;
    color: white; margin: 0 0 0.5rem; letter-spacing: -0.5px;
    line-height: 1.15;
  }
  .hero-desc { color: rgba(255,255,255,0.75); margin: 0 0 1.25rem; font-size: 1rem; max-width: 560px; }
  .hero-stats { display: flex; gap: 1rem; flex-wrap: wrap; }
  .stat {
    display: inline-flex; align-items: center; gap: 0.35rem;
    color: rgba(255,255,255,0.7); font-size: 0.82rem;
    background: rgba(255,255,255,0.1); padding: 0.25rem 0.75rem;
    border-radius: 999px;
  }
  .access-badge { background: rgba(52,211,153,0.2); color: #6ee7b7; }

  /* ── Paywall ─────────────────────────────────────── */
  .paywall-wrap { max-width: 680px; margin: 3rem auto; padding: 0 1.5rem; }
  .paywall-card {
    background: var(--bg-primary); border-radius: 24px;
    box-shadow: 0 8px 40px rgba(0,0,0,0.1);
    padding: 3rem 2rem; text-align: center;
    border: 1px solid var(--border-light);
  }
  .paywall-lock {
    width: 80px; height: 80px; border-radius: 50%;
    background: linear-gradient(135deg, #667eea, #764ba2);
    display: flex; align-items: center; justify-content: center;
    margin: 0 auto 1.25rem; color: white;
  }
  .paywall-card h2 { font-size: 1.6rem; font-weight: 800; margin: 0 0 0.6rem; }
  .paywall-card p { color: var(--text-secondary); margin: 0 0 1.75rem; }
  .paywall-actions { display: flex; gap: 0.75rem; justify-content: center; flex-wrap: wrap; }
  .btn-buy {
    display: inline-flex; align-items: center; gap: 0.5rem;
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: white; text-decoration: none; font-weight: 700;
    padding: 0.875rem 1.75rem; border-radius: 12px; font-size: 0.95rem;
    transition: transform 0.15s, box-shadow 0.15s;
    border: none; cursor: pointer; font-family: inherit;
  }
  .btn-buy:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(102,126,234,0.4); }
  .btn-premium {
    display: inline-flex; align-items: center; padding: 0.875rem 1.5rem;
    border: 1.5px solid var(--border-color); border-radius: 12px;
    color: var(--text-primary); text-decoration: none; font-weight: 600;
    transition: border-color 0.15s;
  }
  .btn-premium:hover { border-color: var(--text-primary); }

  .preview-block { margin-top: 2.5rem; }
  .preview-block h3 { font-size: 1rem; font-weight: 700; margin: 0 0 1rem; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.5px; font-size: 0.75rem; }
  .preview-list { display: flex; flex-direction: column; gap: 0.4rem; }
  .preview-lesson-btn {
    display: flex; align-items: center; gap: 0.875rem; padding: 1rem 1.25rem;
    background: var(--bg-primary); border: 1px solid var(--border-light);
    border-radius: 12px; cursor: pointer; text-align: left;
    font-family: inherit; font-size: 0.9rem; color: var(--text-primary);
    transition: box-shadow 0.15s, transform 0.15s;
  }
  .preview-lesson-btn:hover { box-shadow: 0 2px 12px rgba(0,0,0,0.08); transform: translateY(-1px); }
  .plb-icon { width: 32px; height: 32px; background: linear-gradient(135deg, #667eea, #764ba2); border-radius: 8px; display: flex; align-items: center; justify-content: center; color: white; flex-shrink: 0; }
  .plb-title { flex: 1; font-weight: 600; }
  .plb-tag { font-size: 0.68rem; font-weight: 800; text-transform: uppercase; background: #d1fae5; color: #065f46; padding: 0.2rem 0.5rem; border-radius: 6px; letter-spacing: 0.3px; }

  /* ── Layout ──────────────────────────────────────── */
  .main-layout {
    display: grid;
    grid-template-columns: 320px 1fr;
    grid-template-rows: auto 1fr;
    min-height: 70vh;
    max-width: 1400px;
    margin: 0 auto;
  }
  .mobile-toggle { display: none; }

  /* ── Sidebar Timeline ────────────────────────────── */
  .course-sidebar {
    background: var(--bg-primary);
    border-right: 1px solid var(--border-light);
    display: flex; flex-direction: column;
    overflow-y: auto; max-height: calc(100vh - 80px);
    position: sticky; top: 0;
  }
  .sidebar-top {
    padding: 1.25rem 1.25rem 0.875rem;
    border-bottom: 1px solid var(--border-light);
    display: flex; justify-content: space-between; align-items: center;
    flex-shrink: 0;
  }
  .sidebar-title { font-size: 0.8rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px; color: var(--text-secondary); }
  .sidebar-count { font-size: 0.75rem; color: var(--text-muted); background: var(--bg-secondary); padding: 0.15rem 0.5rem; border-radius: 999px; }

  /* Timeline */
  .timeline { padding: 1rem 0.75rem; flex: 1; }

  .timeline-module {
    display: flex; align-items: center; gap: 0.5rem;
    padding: 0.75rem 0.5rem 0.25rem;
  }
  .module-line { flex: 0 0 2px; height: 1px; background: var(--border-color); display: none; }
  .module-label {
    font-size: 0.7rem; font-weight: 800; text-transform: uppercase;
    letter-spacing: 0.6px; color: var(--text-muted);
    background: var(--bg-secondary); padding: 0.2rem 0.6rem;
    border-radius: 999px; border: 1px solid var(--border-light);
  }

  .timeline-lesson {
    display: flex; align-items: flex-start; gap: 0;
    width: 100%; background: none; border: none; cursor: pointer;
    text-align: left; font-family: inherit; padding: 0;
    border-radius: 0; transition: none;
  }
  .timeline-lesson.locked { opacity: 0.45; cursor: not-allowed; }

  /* Dot column */
  .tl-dot-col {
    display: flex; flex-direction: column; align-items: center;
    width: 36px; flex-shrink: 0;
  }
  .tl-line {
    width: 2px; flex: 1; min-height: 8px;
    background: var(--border-color);
  }
  .tl-line.invisible { background: transparent; }
  .tl-dot {
    width: 28px; height: 28px; border-radius: 50%;
    border: 2px solid var(--border-color);
    background: var(--bg-primary);
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0; transition: all 0.2s;
    color: var(--text-muted); font-size: 0.75rem;
    position: relative; z-index: 1;
  }
  .tl-dot.active {
    background: linear-gradient(135deg, #667eea, #764ba2);
    border-color: #667eea; color: white;
    box-shadow: 0 0 0 4px rgba(102,126,234,0.15);
  }
  .tl-num { font-size: 0.65rem; font-weight: 700; }
  .timeline-lesson:hover:not(.locked) .tl-dot:not(.active) {
    border-color: #667eea; color: #667eea;
    background: rgba(102,126,234,0.06);
  }

  /* Info column */
  .tl-info {
    padding: 0.15rem 0.5rem 0.75rem 0.5rem;
    flex: 1; min-width: 0;
  }
  .tl-title {
    display: block; font-size: 0.85rem; font-weight: 600;
    color: var(--text-secondary); line-height: 1.35;
    transition: color 0.15s;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  }
  .timeline-lesson.active .tl-title { color: #667eea; font-weight: 700; }
  .timeline-lesson:hover:not(.locked) .tl-title { color: var(--text-primary); }
  .tl-badges { display: flex; gap: 0.3rem; margin-top: 0.25rem; flex-wrap: wrap; }
  .tl-badge {
    display: inline-flex; align-items: center; gap: 0.2rem;
    font-size: 0.6rem; font-weight: 800; text-transform: uppercase;
    padding: 0.1rem 0.4rem; border-radius: 4px; letter-spacing: 0.3px;
  }
  .tl-badge.video { background: #ede9fe; color: #7c3aed; }
  .tl-badge.preview { background: #d1fae5; color: #065f46; }

  /* Sidebar materials */
  .sidebar-materials {
    border-top: 1px solid var(--border-light);
    padding: 1rem 1.25rem; margin-top: auto;
  }
  .mat-header {
    display: flex; align-items: center; gap: 0.4rem;
    font-size: 0.7rem; font-weight: 800; text-transform: uppercase;
    letter-spacing: 0.5px; color: var(--text-muted); margin-bottom: 0.75rem;
  }
  .mat-link {
    display: flex; align-items: center; gap: 0.5rem;
    padding: 0.5rem 0.25rem; text-decoration: none;
    color: var(--text-secondary); font-size: 0.82rem;
    border-bottom: 1px solid var(--border-light);
    transition: color 0.15s;
  }
  .mat-link:hover { color: var(--text-primary); }
  .mat-ext { font-size: 0.65rem; font-weight: 700; color: var(--text-muted); text-transform: uppercase; margin-left: auto; }

  /* ── Lesson Main ─────────────────────────────────── */
  .lesson-main { padding: 2.5rem 2.5rem; overflow-y: auto; min-height: 70vh; }

  /* Video Player */
  .video-player {
    position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden;
    border-radius: 20px; background: #000; margin-bottom: 2.5rem;
    box-shadow: 0 8px 40px rgba(0,0,0,0.25);
  }
  .video-player iframe { position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: none; }
  .player-state {
    position: absolute; inset: 0; display: flex; flex-direction: column;
    align-items: center; justify-content: center; gap: 1rem;
    color: rgba(255,255,255,0.7); font-size: 0.9rem;
  }
  .player-state.error { color: #f87171; }
  .spinner {
    width: 40px; height: 40px; border: 3px solid rgba(255,255,255,0.15);
    border-top-color: white; border-radius: 50%; animation: spin 0.8s linear infinite;
  }
  @keyframes spin { to { transform: rotate(360deg); } }

  /* Lesson header */
  .lesson-header { margin-bottom: 1.75rem; }
  .lesson-header-top { display: flex; align-items: flex-start; gap: 0.75rem; flex-wrap: wrap; }
  h2 { font-size: 1.6rem; font-weight: 800; margin: 0; letter-spacing: -0.3px; color: var(--text-primary); }
  .badge-preview-inline {
    display: inline-block; font-size: 0.72rem; font-weight: 800;
    background: #d1fae5; color: #065f46; padding: 0.25rem 0.65rem;
    border-radius: 8px; text-transform: uppercase; letter-spacing: 0.4px;
    margin-top: 0.3rem;
  }
  .lesson-topic-label { color: var(--text-muted); font-size: 0.82rem; font-weight: 600; margin: 0.4rem 0 0; }

  /* Lesson body */
  .lesson-body {
    font-size: 1rem; line-height: 1.85; color: var(--text-primary);
    max-width: 720px;
  }
  .lesson-body :global(h2), .lesson-body :global(h3) { font-weight: 700; margin-top: 1.75rem; }
  .lesson-body :global(a) { color: #667eea; }
  .lesson-body :global(img) { max-width: 100%; border-radius: 16px; }
  .lesson-body :global(pre) { background: var(--bg-tertiary); border-radius: 12px; padding: 1.25rem; overflow-x: auto; }

  /* Navigation */
  .lesson-nav {
    display: flex; justify-content: space-between; align-items: stretch;
    gap: 1rem; margin-top: 3rem; padding-top: 1.75rem;
    border-top: 1px solid var(--border-light);
  }
  .nav-btn {
    display: flex; align-items: center; gap: 0.75rem; padding: 0.875rem 1.25rem;
    border: 1.5px solid var(--border-color); border-radius: 14px;
    background: var(--bg-primary); cursor: pointer; font-family: inherit;
    transition: all 0.2s; flex: 1; max-width: 280px;
  }
  .nav-btn:hover { border-color: #667eea; box-shadow: 0 2px 12px rgba(102,126,234,0.15); }
  .nav-btn.next { flex-direction: row-reverse; text-align: right; margin-left: auto; }
  .nav-text { display: flex; flex-direction: column; gap: 0.15rem; overflow: hidden; }
  .nav-label { font-size: 0.65rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; color: var(--text-muted); }
  .nav-title { font-size: 0.85rem; font-weight: 600; color: var(--text-primary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .course-completed {
    display: flex; align-items: center; gap: 0.5rem;
    color: #059669; font-size: 0.9rem; font-weight: 700;
    margin-left: auto;
  }

  /* Empty state */
  .empty-state { text-align: center; padding: 6rem 2rem; color: var(--text-muted); }
  .empty-state svg { opacity: 0.15; margin-bottom: 1.25rem; }
  .empty-state p { font-size: 1rem; }

  /* ── Mobile ──────────────────────────────────────── */
  @media (max-width: 800px) {
    .main-layout { grid-template-columns: 1fr; }
    .mobile-toggle {
      display: flex; align-items: center; gap: 0.5rem;
      padding: 0.875rem 1.25rem; border: none;
      border-bottom: 1px solid var(--border-light);
      background: var(--bg-primary); cursor: pointer;
      font-family: inherit; font-size: 0.875rem; font-weight: 700;
      color: var(--text-secondary); width: 100%;
    }
    .course-sidebar {
      max-height: 0; overflow: hidden; position: static;
      transition: max-height 0.35s ease; border-right: none;
      border-bottom: 1px solid var(--border-light);
    }
    .course-sidebar.open { max-height: 600px; overflow-y: auto; }
    .lesson-main { padding: 1.5rem 1.25rem; }
  }
</style>
