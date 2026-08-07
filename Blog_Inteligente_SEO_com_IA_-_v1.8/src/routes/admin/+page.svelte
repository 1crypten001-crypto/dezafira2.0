<script lang="ts">
  import { page } from "$app/stores";
  import { t, formatDate as fmtDate, formatMoney } from "$lib/i18n";

let { data } = $props();
  const lang = $derived($page.data.language || 'pt');
function formatDate(dateString: string) {
    const date = new Date(dateString);
    return date.toLocaleDateString(lang === "en" ? "en-US" : lang === "es" ? "es-ES" : "pt-BR", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
    });
  }

  function getStatusText(published: number) {
    return published ? t(lang, 'admin.ui.published') : t(lang, 'admin.ui.draft');
  }

  function formatChartDate(dateString: string) {
    const parts = dateString.split('-');
    if (parts.length < 3) return dateString;
    return `${parts[2]}/${parts[1]}`;
  }

  // SVG Line Chart calculations
  let chartWidth = 600;
  let chartHeight = 150;
  let paddingX = 30;
  let paddingY = 20;

  let points = $derived.by(() => {
    const list = data.analytics?.viewsByDay || [];
    if (list.length === 0) return [];
    const maxVal = Math.max(...list.map((d: any) => d.count), 5);
    return list.map((d: any, i: number) => {
      const x = paddingX + (i * (chartWidth - paddingX * 2)) / (list.length - 1 || 1);
      const y = chartHeight - paddingY - (d.count * (chartHeight - paddingY * 2)) / maxVal;
      return { x, y, count: d.count, date: d.date };
    });
  });

  let pathD = $derived.by(() => {
    if (points.length === 0) return '';
    return points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ');
  });

  let areaD = $derived.by(() => {
    if (points.length === 0) return '';
    const first = points[0];
    const last = points[points.length - 1];
    return `${pathD} L ${last.x} ${chartHeight - paddingY} L ${first.x} ${chartHeight - paddingY} Z`;
  });
</script>

<svelte:head>
  <title>{t(lang, "admin.dash.title")}</title>
</svelte:head>

<div class="dashboard">
  <div class="dashboard-header">
    <h1>{t(lang, "admin.dash.heading")}</h1>
    <a href="/admin/posts/new" class="btn btn-primary">{t(lang, "admin.dash.new_post")}</a>
  </div>

  <!-- Stats Grid -->
  <div class="stats-grid">
    <div class="stat-card">
      <div class="stat-icon">
        <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
          <path stroke-linecap="round" stroke-linejoin="round" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
        </svg>
      </div>
      <div class="stat-info">
        <span class="stat-number">{data.analytics?.viewsToday ?? 0}</span>
        <span class="stat-label">{t(lang, "admin.dash.views_today")}</span>
      </div>
    </div>

    <div class="stat-card">
      <div class="stat-icon">
        <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
        </svg>
      </div>
      <div class="stat-info">
        <span class="stat-number">{data.analytics?.viewsWeek ?? 0}</span>
        <span class="stat-label">{t(lang, "admin.dash.views_week")}</span>
      </div>
    </div>

    <div class="stat-card">
      <div class="stat-icon">
        <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"/>
        </svg>
      </div>
      <div class="stat-info">
        <span class="stat-number">{data.analytics?.totalViews ?? 0}</span>
        <span class="stat-label">{t(lang, "admin.dash.views_total")}</span>
      </div>
    </div>

    <div class="stat-card">
      <div class="stat-icon">
        <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
        </svg>
      </div>
      <div class="stat-info">
        <span class="stat-number">{data.posts?.length ?? 0}</span>
        <span class="stat-label">{t(lang, "admin.dash.posts")}</span>
      </div>
    </div>

    <div class="stat-card sitemap-card">
      <div class="stat-icon">
        <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9"/>
        </svg>
      </div>
      <div class="stat-info">
        <span class="stat-label">{t(lang, "admin.dash.sitemap")}</span>
        <div class="sitemap-url-wrapper">
          <input type="text" readonly value="/sitemap.xml" class="sitemap-input" id="sitemap-url" />
          <button
            class="btn btn-small btn-copy"
            onclick={() => {
              const input = document.getElementById("sitemap-url") as HTMLInputElement;
              if (input) { navigator.clipboard.writeText(window.location.origin + '/sitemap.xml'); }
            }}
          >{t(lang, "admin.ui.copy")}</button>
        </div>
      </div>
    </div>
  </div>

  <!-- Chart -->
  <div class="chart-section">
    <div class="section-title-row">
      <div>
        <h2 class="section-title">{t(lang, "admin.dash.traffic")}</h2>
        <p class="section-subtitle">{t(lang, "admin.dash.last_7")}</p>
      </div>
    </div>

    <div class="card chart-card">
      {#if !data.analytics || data.analytics.viewsWeek === 0}
        <div class="empty-state">
          <svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
          </svg>
          <p>{t(lang, "admin.dash.no_views")}</p>
          <span class="empty-hint">{t(lang, "admin.dash.no_views_hint")}</span>
        </div>
      {:else}
        <div class="svg-wrapper">
          <svg viewBox="0 0 600 150" class="trend-chart" preserveAspectRatio="none">
            <defs>
              <linearGradient id="chartGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stop-color="#3b82f6" stop-opacity="0.18"/>
                <stop offset="100%" stop-color="#3b82f6" stop-opacity="0"/>
              </linearGradient>
            </defs>

            {#each [0, 0.25, 0.5, 0.75, 1] as ratio}
              <line
                x1={paddingX}
                y1={paddingY + ratio * (chartHeight - paddingY * 2)}
                x2={chartWidth - paddingX}
                y2={paddingY + ratio * (chartHeight - paddingY * 2)}
                stroke="var(--border-light, rgba(0,0,0,0.06))"
                stroke-width="1"
                stroke-dasharray="4,4"
              />
            {/each}

            <path d={areaD} fill="url(#chartGrad)"/>
            <path d={pathD} fill="none" stroke="#3b82f6" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>

            {#each points as pt}
              <g class="chart-point-group">
                <circle cx={pt.x} cy={pt.y} r="4" class="chart-point" fill="#3b82f6" stroke="white" stroke-width="2"/>
                <circle cx={pt.x} cy={pt.y} r="12" fill="transparent" style="cursor:pointer">
                  <title>{formatChartDate(pt.date)}: {pt.count} visitas</title>
                </circle>
              </g>
            {/each}
          </svg>
        </div>

        <div class="chart-labels">
          {#each points as pt}
            <span class="chart-label-item">
              <span class="date">{formatChartDate(pt.date)}</span>
              <span class="val">{pt.count}</span>
            </span>
          {/each}
        </div>
      {/if}
    </div>
  </div>

  <!-- Bottom lists -->
  <div class="lists-grid">
    <!-- Posts Recentes -->
    <div class="card list-card">
      <div class="list-header">
        <h2 class="list-title">{t(lang, "admin.dash.recent_posts")}</h2>
        <a href="/admin/posts" class="list-link">{t(lang, "admin.ui.view_all")}</a>
      </div>

      {#if !data.posts || data.posts.length === 0}
        <div class="empty-state">
          <svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
          </svg>
          <p>{t(lang, "admin.dash.no_posts")}</p>
          <a href="/admin/posts/new" class="btn btn-primary">{t(lang, "admin.dash.create_first")}</a>
        </div>
      {:else}
        <div class="posts-list">
          {#each data.posts.slice(0, 5) as post}
            <a href="/admin/posts/{post.id}" class="post-row">
              <div class="post-info">
                <span class="post-title">{post.title}</span>
                <span class="post-meta">{formatDate(post.created_at)}</span>
              </div>
              <span class="status" class:published={post.published} class:draft={!post.published}>
                {getStatusText(post.published)}
              </span>
            </a>
          {/each}
        </div>
      {/if}
    </div>

    <!-- Posts Mais Lidos -->
    <div class="card list-card">
      <div class="list-header">
        <h2 class="list-title">{t(lang, "admin.dash.top_read")}</h2>
        <span class="list-link-muted">{t(lang, "admin.dash.top5")}</span>
      </div>

      {#if !data.analytics?.topPosts || data.analytics.topPosts.length === 0}
        <div class="empty-state">
          <svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"/>
          </svg>
          <p>{t(lang, "admin.dash.no_read_data")}</p>
          <span class="empty-hint">{t(lang, "admin.dash.no_read_hint")}</span>
        </div>
      {:else}
        <div class="posts-list">
          {#each data.analytics.topPosts as post}
            <a href="/admin/posts/{post.id}" class="post-row">
              <div class="post-info">
                <span class="post-title">{post.title}</span>
                <span class="post-meta">/{post.slug}</span>
              </div>
              <div class="views-badge">
                <span class="views-count">{post.views}</span>
                <span class="views-lbl">views</span>
              </div>
            </a>
          {/each}
        </div>
      {/if}
    </div>
  </div>
</div>

<style>
  .dashboard {
    max-width: 1100px;
    margin: 0 auto;
    display: flex;
    flex-direction: column;
    gap: 1.75rem;
  }

  /* ── Header ──────────────────────────────────────────────────── */
  .dashboard-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 0.75rem;
  }

  .dashboard-header h1 {
    font-family: var(--font-sans);
    font-size: 1.5rem;
    font-weight: 700;
    margin: 0;
    color: var(--text-primary);
  }

  /* ── Stats Grid ───────────────────────────────────────────────── */
  .stats-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 0.75rem;
  }

  @media (min-width: 640px) {
    .stats-grid {
      grid-template-columns: repeat(3, 1fr);
    }
  }

  @media (min-width: 900px) {
    .stats-grid {
      grid-template-columns: repeat(5, 1fr);
    }
  }

  .stat-card {
    background: var(--bg-primary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-lg);
    padding: 1rem;
    display: flex;
    align-items: center;
    gap: 0.875rem;
    transition: box-shadow var(--transition-fast);
  }

  .stat-card:hover {
    box-shadow: var(--shadow-md);
  }

  .stat-icon {
    width: 38px;
    height: 38px;
    border-radius: var(--radius-md);
    background: var(--bg-secondary);
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--text-muted);
    flex-shrink: 0;
  }

  .stat-icon svg {
    width: 18px;
    height: 18px;
  }

  .stat-info {
    display: flex;
    flex-direction: column;
    min-width: 0;
  }

  .stat-number {
    font-family: var(--font-sans);
    font-size: 1.5rem;
    font-weight: 700;
    line-height: 1;
    color: var(--text-primary);
  }

  .stat-label {
    font-size: 0.71rem;
    color: var(--text-muted);
    margin-top: 0.25rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .sitemap-card {
    grid-column: span 2;
  }

  @media (min-width: 640px) {
    .sitemap-card { grid-column: span 1; }
  }

  .sitemap-url-wrapper {
    display: flex;
    gap: 0.375rem;
    margin-top: 0.375rem;
  }

  .sitemap-input {
    background: var(--bg-secondary);
    border: 1px solid var(--border-light);
    border-radius: var(--radius-sm);
    padding: 0.25rem 0.5rem;
    font-size: 0.71rem;
    font-family: monospace;
    width: 90px;
    color: var(--text-secondary);
  }

  .btn-copy { padding: 0.25rem 0.5rem; font-size: 0.71rem; }

  /* ── Section titles ───────────────────────────────────────────── */
  .section-title-row {
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
  }

  .section-title {
    font-family: var(--font-sans);
    font-size: 1rem;
    font-weight: 600;
    margin: 0;
    color: var(--text-primary);
  }

  .section-subtitle {
    font-size: 0.8125rem;
    color: var(--text-muted);
    margin: 0.2rem 0 0;
  }

  /* ── Card base ────────────────────────────────────────────────── */
  .card {
    background: var(--bg-primary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-lg);
    overflow: hidden;
  }

  /* ── Chart ────────────────────────────────────────────────────── */
  .chart-section {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .chart-card {
    padding: 1.25rem;
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .svg-wrapper { width: 100%; }

  .trend-chart {
    width: 100%;
    height: 130px;
    overflow: visible;
  }

  .chart-point { transition: r 0.15s ease; }
  .chart-point-group:hover .chart-point { r: 6px; }

  .chart-labels {
    display: flex;
    justify-content: space-between;
    border-top: 1px solid var(--border-light);
    padding-top: 0.75rem;
  }

  .chart-label-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    font-size: 0.71rem;
    color: var(--text-muted);
    flex: 1;
    text-align: center;
  }

  .chart-label-item .date { font-weight: 600; }

  .chart-label-item .val {
    font-size: 0.6875rem;
    margin-top: 0.125rem;
    background: var(--bg-secondary);
    padding: 0.1rem 0.4rem;
    border-radius: 999px;
    color: var(--text-secondary);
    font-weight: 500;
  }

  /* ── Lists grid ───────────────────────────────────────────────── */
  .lists-grid {
    display: grid;
    grid-template-columns: 1fr;
    gap: 1rem;
  }

  @media (min-width: 768px) {
    .lists-grid { grid-template-columns: 1fr 1fr; }
  }

  .list-card { display: flex; flex-direction: column; }

  .list-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem 1.25rem;
    border-bottom: 1px solid var(--border-light);
  }

  .list-title {
    font-family: var(--font-sans);
    font-size: 0.9375rem;
    font-weight: 600;
    margin: 0;
    color: var(--text-primary);
  }

  .list-link {
    font-size: 0.8125rem;
    color: var(--text-secondary);
    text-decoration: none;
    transition: color var(--transition-fast);
  }

  .list-link:hover { color: var(--text-primary); }

  .list-link-muted {
    font-size: 0.75rem;
    color: var(--text-muted);
  }

  /* ── Post rows ────────────────────────────────────────────────── */
  .posts-list { display: flex; flex-direction: column; }

  .post-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.875rem 1.25rem;
    border-bottom: 1px solid var(--border-light);
    text-decoration: none;
    gap: 0.75rem;
    transition: background var(--transition-fast);
  }

  .post-row:last-child { border-bottom: none; }
  .post-row:hover { background: var(--bg-secondary); }

  .post-info {
    display: flex;
    flex-direction: column;
    gap: 0.2rem;
    min-width: 0;
    flex: 1;
  }

  .post-title {
    font-family: var(--font-sans);
    font-size: 0.875rem;
    font-weight: 500;
    color: var(--text-primary);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .post-meta {
    font-size: 0.71rem;
    color: var(--text-muted);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  /* ── Status badges ────────────────────────────────────────────── */
  .status {
    display: inline-block;
    padding: 0.2rem 0.55rem;
    font-size: 0.65rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    border-radius: 999px;
    flex-shrink: 0;
  }

  .status.published { background: #ecfdf5; color: #059669; }
  .status.draft     { background: #fef3c7; color: #d97706; }

  /* ── Views badge ──────────────────────────────────────────────── */
  .views-badge {
    display: flex;
    flex-direction: column;
    align-items: center;
    background: var(--bg-secondary);
    padding: 0.3rem 0.6rem;
    border-radius: var(--radius-md);
    min-width: 48px;
    flex-shrink: 0;
  }

  .views-count {
    font-size: 0.9375rem;
    font-weight: 700;
    color: #3b82f6;
    line-height: 1;
  }

  .views-lbl {
    font-size: 0.6rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-top: 0.1rem;
  }

  /* ── Empty state ──────────────────────────────────────────────── */
  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    padding: 2rem 1.25rem;
    gap: 0.5rem;
  }

  .empty-icon {
    width: 36px;
    height: 36px;
    color: var(--text-muted);
    opacity: 0.4;
  }

  .empty-state p {
    font-size: 0.9rem;
    color: var(--text-muted);
    margin: 0;
  }

  .empty-hint {
    font-size: 0.78rem;
    color: var(--text-muted);
    opacity: 0.75;
  }
</style>
