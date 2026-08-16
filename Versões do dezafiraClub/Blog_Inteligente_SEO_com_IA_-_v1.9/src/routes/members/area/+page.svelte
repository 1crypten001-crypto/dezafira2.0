<script lang="ts">
  import { page } from '$app/stores';
  import { enhance } from '$app/forms';
  import { t, formatMoney } from '$lib/i18n';

  let { data } = $props();
  const lang = $derived($page.data.language || 'pt');
  const displayCurrency = $derived(($page.data.displayCurrency as string) || 'BRL');

  let activeTab = $state<'community' | 'courses'>('community');
  let selectedCategory = $state<string>('Todos');
  let showNewTopicModal = $state(false);
  let isSubmittingTopic = $state(false);

  // Categorias da Comunidade
  const communityCategories = ['Todos', 'Geral', 'Dúvidas', 'Ideias & Sugestões', 'Anúncios'];

  const accessLabel = $derived({ free: t(lang, 'members.badge_free'), premium: t(lang, 'members.badge_premium'), paid: t(lang, 'members.badge_paid') });
  const accessColor: Record<string, string> = { free: '#10b981', premium: '#6366f1', paid: '#f59e0b' };

  function formatPrice(cents: number) {
    return formatMoney(lang, cents, displayCurrency);
  }

  function formatDate(dateStr: string) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleDateString(lang === 'pt' ? 'pt-BR' : 'en-US', {
      day: '2-digit',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit'
    });
  }

  function getUserBadge(role: string) {
    if (role === 'admin') return { label: '🛡️ Admin', class: 'badge-admin' };
    return { label: '⭐ Membro VIP', class: 'badge-vip' };
  }

  let filteredTopics = $derived(
    selectedCategory === 'Todos'
      ? data.communityTopics
      : data.communityTopics.filter((t: any) => t.category === selectedCategory)
  );
</script>

<svelte:head>
  <title>Comunidade VIP & Área de Membros</title>
  <meta name="robots" content="noindex" />
</svelte:head>

<div class="area-container">
  <!-- Top Header Hero - Minimalist Theme Standard -->
  <header class="area-hero">
    <div class="hero-badge">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
        <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
      </svg>
      {#if data.hasPremium}
        <span>Comunidade VIP · Assinante Ativo</span>
      {:else}
        <span>Área de Membros · Acesso Gratuito</span>
      {/if}
    </div>

    <h1>Comunidade VIP & Área de Membros</h1>
    <p class="subtitle">Conecte-se com outros membros, troque conhecimento em discussões exclusivas e acesse seus cursos.</p>

    <div class="hero-actions">
      {#if !data.hasPremium}
        <a href="/premium" class="btn btn-primary">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
          Assinar Plano VIP
        </a>
      {/if}
      <a href="/members/dashboard" class="btn btn-outline">Minha Conta</a>
    </div>
  </header>

  <!-- Navegação de Abas -->
  <div class="tabs-nav">
    <button
      class="tab-link"
      class:active={activeTab === 'community'}
      onclick={() => activeTab = 'community'}
    >
      💬 Feed & Discussões
      <span class="count-pill">{data.communityTopics.length}</span>
    </button>
    <button
      class="tab-link"
      class:active={activeTab === 'courses'}
      onclick={() => activeTab = 'courses'}
    >
      🎓 Cursos Exclusivos
      <span class="count-pill">{data.courses.length}</span>
    </button>
  </div>

  <!-- CONTEÚDO DA ABA 1: FEED DE DISCUSSÕES -->
  {#if activeTab === 'community'}
    {#if !data.hasPremium}
      <!-- Paywall Card Integrado ao Tema -->
      <div class="paywall-box">
        <div class="paywall-icon-wrap">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>
          </svg>
        </div>
        <h2>A Comunidade VIP é Exclusiva para Assinantes</h2>
        <p>Faça o upgrade da sua conta para publicar tópicos, tirar dúvidas diretamente com os autores e interagir no feed de discussões.</p>

        <div class="paywall-grid">
          <div class="paywall-benefit">
            <span class="benefit-check">✓</span>
            <span>Feed interativo de perguntas e respostas</span>
          </div>
          <div class="paywall-benefit">
            <span class="benefit-check">✓</span>
            <span>Contato direto com administradores e especialistas</span>
          </div>
          <div class="paywall-benefit">
            <span class="benefit-check">✓</span>
            <span>Acesso ilimitado a todos os cursos e materiais</span>
          </div>
        </div>

        <div class="paywall-cta-row">
          <a href="/premium" class="btn btn-primary btn-lg">
            {#if data.cheapestPlan}
              Desbloquear Comunidade VIP por {formatPrice(data.cheapestPlan.price_cents)}
            {:else}
              Assinar Plano VIP
            {/if}
          </a>
        </div>
      </div>
    {:else}
      <!-- Barra de Controle (Filtros de Categoria + Novo Tópico) -->
      <div class="feed-toolbar">
        <div class="filter-pills">
          {#each communityCategories as cat}
            <button
              class="filter-pill"
              class:active={selectedCategory === cat}
              onclick={() => selectedCategory = cat}
            >
              {cat}
            </button>
          {/each}
        </div>

        <button class="btn btn-primary btn-sm" onclick={() => showNewTopicModal = true}>
          ✨ Criar Discussão
        </button>
      </div>

      <!-- Modal de Criar Tópico -->
      {#if showNewTopicModal}
        <div class="modal-overlay" onclick={() => showNewTopicModal = false} role="presentation">
          <div class="modal-card" onclick={(e) => e.stopPropagation()} role="dialog" aria-modal="true">
            <div class="modal-header">
              <h3>Nova Discussão na Comunidade</h3>
              <button class="btn-icon" onclick={() => showNewTopicModal = false}>✕</button>
            </div>
            <form method="POST" action="?/createTopic" use:enhance={() => {
              isSubmittingTopic = true;
              return async ({ update }) => {
                isSubmittingTopic = false;
                showNewTopicModal = false;
                await update();
              };
            }}>
              <div class="form-field">
                <label for="title">Título da Discussão</label>
                <input type="text" id="title" name="title" placeholder="Ex: Qual a melhor estratégia para acelerar os resultados?" required />
              </div>

              <div class="form-field">
                <label for="category">Categoria</label>
                <select id="category" name="category">
                  <option value="Geral">Geral</option>
                  <option value="Dúvidas">Dúvidas</option>
                  <option value="Ideias & Sugestões">Ideias & Sugestões</option>
                  {#if data.user?.role === 'admin'}
                    <option value="Anúncios">Anúncios</option>
                  {/if}
                </select>
              </div>

              <div class="form-field">
                <label for="content">Mensagem / Detalhes</label>
                <textarea id="content" name="content" rows="4" placeholder="Escreva os detalhes da sua mensagem..." required></textarea>
              </div>

              {#if data.user?.role === 'admin'}
                <div class="form-field checkbox-field">
                  <label>
                    <input type="checkbox" name="is_pinned" />
                    Fixar no topo como Comunicado Oficial 📌
                  </label>
                </div>
              {/if}

              <div class="modal-footer">
                <button type="button" class="btn btn-outline btn-sm" onclick={() => showNewTopicModal = false}>Cancelar</button>
                <button type="submit" class="btn btn-primary btn-sm" disabled={isSubmittingTopic}>
                  {isSubmittingTopic ? 'Publicando...' : 'Publicar Tópico'}
                </button>
              </div>
            </form>
          </div>
        </div>
      {/if}

      <!-- Feed de Tópicos da Comunidade -->
      <div class="topics-list">
        {#if filteredTopics.length === 0}
          <div class="empty-box">
            <p>Nenhuma discussão nesta categoria ainda. Seja o primeiro a criar um tópico!</p>
          </div>
        {:else}
          {#each filteredTopics as topic}
            <a href="/members/area/topic/{topic.id}" class="topic-card" class:is-pinned={topic.is_pinned}>
              <div class="topic-card-header">
                <div class="author-block">
                  <div class="avatar">{topic.user_email[0].toUpperCase()}</div>
                  <div class="author-meta">
                    <span class="author-name">{topic.user_email.split('@')[0]}</span>
                    <span class="badge-role {getUserBadge(topic.user_role).class}">
                      {getUserBadge(topic.user_role).label}
                    </span>
                  </div>
                </div>
                <span class="topic-date">{formatDate(topic.created_at)}</span>
              </div>

              <h2 class="topic-card-title">
                {#if topic.is_pinned}
                  <span class="pinned-tag">📌 FIXADO</span>
                {/if}
                {topic.title}
              </h2>

              <p class="topic-snippet">{topic.content.slice(0, 140)}{topic.content.length > 140 ? '...' : ''}</p>

              <div class="topic-card-footer">
                <span class="cat-badge">{topic.category}</span>

                <div class="topic-stats">
                  <span class="stat-item" class:liked={topic.user_has_liked}>
                    ❤️ {topic.likes_count}
                  </span>
                  <span class="stat-item">
                    💬 {topic.comments_count} respostas
                  </span>
                </div>
              </div>
            </a>
          {/each}
        {/if}
      </div>
    {/if}
  {/if}

  <!-- CONTEÚDO DA ABA 2: CURSOS -->
  {#if activeTab === 'courses'}
    {#if data.courses.length === 0}
      <div class="empty-box">
        <h3>Nenhum curso disponível ainda</h3>
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
                    <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>
                  </div>
                {/if}

                {#if !course.hasAccess}
                  <div class="lock-overlay">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
                  </div>
                {:else}
                  <div class="access-check">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20 6 9 17 4 12"/></svg>
                  </div>
                {/if}
              </div>

              <div class="course-body">
                <div class="course-badges">
                  <span class="badge-access" style="background:{accessColor[course.access_type]}15; color:{accessColor[course.access_type]}">
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
                </div>
              </div>
            </a>

            <div class="course-card-footer">
              {#if !course.hasAccess}
                <a href="/premium" class="btn btn-outline btn-full btn-sm">
                  Assinar VIP para Acessar
                </a>
              {:else}
                <a href="/members/area/{course.slug}" class="btn btn-primary btn-full btn-sm">
                  Acessar Curso
                </a>
              {/if}
            </div>
          </div>
        {/each}
      </div>
    {/if}
  {/if}
</div>

<style>
  .area-container {
    max-width: 1050px;
    margin: 0 auto;
    padding: 2.5rem 1.5rem 5rem;
  }

  /* Hero Section (Aesthetic matching blog theme) */
  .area-hero {
    text-align: center;
    margin-bottom: 2.5rem;
  }

  .hero-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    background: linear-gradient(135deg, rgba(245, 158, 11, 0.12), rgba(217, 119, 6, 0.12));
    color: #d97706;
    padding: 0.4rem 0.9rem;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 700;
    margin-bottom: 1rem;
    border: 1px solid rgba(245, 158, 11, 0.2);
  }

  .area-hero h1 {
    font-family: var(--font-serif);
    font-size: clamp(1.8rem, 4vw, 2.6rem);
    font-weight: 600;
    margin: 0 0 0.75rem;
    color: var(--text-primary);
    letter-spacing: -0.5px;
  }

  .subtitle {
    font-size: 1.05rem;
    color: var(--text-secondary);
    max-width: 620px;
    margin: 0 auto 1.5rem;
    line-height: 1.6;
  }

  .hero-actions {
    display: flex;
    justify-content: center;
    gap: 0.75rem;
    flex-wrap: wrap;
  }

  /* Tabs Nav */
  .tabs-nav {
    display: flex;
    justify-content: center;
    gap: 0.5rem;
    border-bottom: 1px solid var(--border-light);
    margin-bottom: 2rem;
  }

  .tab-link {
    background: transparent;
    border: none;
    padding: 0.85rem 1.25rem;
    font-weight: 700;
    font-size: 0.95rem;
    color: var(--text-secondary);
    cursor: pointer;
    border-bottom: 2px solid transparent;
    margin-bottom: -1px;
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    transition: all var(--transition-fast);
  }

  .tab-link:hover {
    color: var(--text-primary);
  }

  .tab-link.active {
    color: var(--text-primary);
    border-bottom-color: var(--accent, #1a1a1a);
  }

  .count-pill {
    background: var(--bg-tertiary);
    color: var(--text-secondary);
    padding: 0.15rem 0.5rem;
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: 700;
  }

  /* Paywall Card (Matching Theme Standards) */
  .paywall-box {
    background: var(--bg-primary);
    border: 1px solid rgba(245, 158, 11, 0.3);
    border-radius: var(--radius-xl);
    padding: 3rem 2rem;
    text-align: center;
    box-shadow: var(--shadow-md);
  }

  .paywall-icon-wrap {
    width: 60px;
    height: 60px;
    border-radius: 50%;
    background: linear-gradient(135deg, rgba(245, 158, 11, 0.15), rgba(217, 119, 6, 0.15));
    color: #d97706;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto 1.25rem;
  }

  .paywall-box h2 {
    font-family: var(--font-serif);
    font-size: 1.5rem;
    font-weight: 600;
    margin: 0 0 0.75rem;
    color: var(--text-primary);
  }

  .paywall-box p {
    color: var(--text-secondary);
    max-width: 580px;
    margin: 0 auto 1.75rem;
    line-height: 1.6;
    font-size: 0.95rem;
  }

  .paywall-grid {
    display: flex;
    justify-content: center;
    gap: 1.5rem;
    margin-bottom: 2rem;
    flex-wrap: wrap;
  }

  .paywall-benefit {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    font-size: 0.88rem;
    font-weight: 600;
    color: var(--text-primary);
  }

  .benefit-check {
    color: #10b981;
    font-weight: 800;
  }

  .paywall-cta-row {
    display: flex;
    justify-content: center;
  }

  /* Toolbar & Filters */
  .feed-toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 1rem;
    margin-bottom: 1.75rem;
    flex-wrap: wrap;
  }

  .filter-pills {
    display: flex;
    gap: 0.4rem;
    flex-wrap: wrap;
  }

  .filter-pill {
    background: var(--bg-primary);
    border: 1px solid var(--border-light);
    color: var(--text-secondary);
    padding: 0.35rem 0.85rem;
    border-radius: 20px;
    font-weight: 600;
    font-size: 0.82rem;
    cursor: pointer;
    transition: all var(--transition-fast);
  }

  .filter-pill:hover {
    background: var(--bg-tertiary);
    color: var(--text-primary);
  }

  .filter-pill.active {
    background: var(--accent, #1a1a1a);
    color: var(--bg-primary);
    border-color: var(--accent, #1a1a1a);
    font-weight: 700;
  }

  /* Topics List */
  .topics-list {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .empty-box {
    text-align: center;
    padding: 3.5rem 2rem;
    background: var(--bg-primary);
    border: 1px dashed var(--border-color);
    border-radius: var(--radius-lg);
    color: var(--text-secondary);
  }

  .topic-card {
    background: var(--bg-primary);
    border: 1px solid var(--border-light);
    border-radius: var(--radius-lg);
    padding: 1.25rem 1.5rem;
    text-decoration: none;
    color: inherit;
    display: block;
    box-shadow: var(--shadow-xs);
    transition: transform var(--transition-fast), box-shadow var(--transition-fast), border-color var(--transition-fast);
  }

  .topic-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-md);
    border-color: var(--border-dark);
  }

  .topic-card.is-pinned {
    border-left: 4px solid #f59e0b;
  }

  .topic-card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.6rem;
  }

  .author-block {
    display: flex;
    align-items: center;
    gap: 0.6rem;
  }

  .avatar {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    background: var(--bg-tertiary);
    border: 1px solid var(--border-color);
    color: var(--text-primary);
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 0.85rem;
  }

  .author-meta {
    display: flex;
    align-items: center;
    gap: 0.4rem;
  }

  .author-name {
    font-weight: 700;
    font-size: 0.88rem;
    color: var(--text-primary);
  }

  .badge-role {
    font-size: 0.68rem;
    padding: 0.15rem 0.45rem;
    border-radius: 4px;
    font-weight: 700;
  }

  .badge-admin {
    background: rgba(239, 68, 68, 0.12);
    color: #ef4444;
  }

  .badge-vip {
    background: rgba(245, 158, 11, 0.15);
    color: #d97706;
  }

  .topic-date {
    font-size: 0.78rem;
    color: var(--text-muted);
  }

  .topic-card-title {
    font-size: 1.1rem;
    font-weight: 700;
    margin: 0 0 0.4rem;
    color: var(--text-primary);
    display: flex;
    align-items: center;
    gap: 0.5rem;
    line-height: 1.35;
  }

  .pinned-tag {
    font-size: 0.65rem;
    background: #f59e0b;
    color: white;
    padding: 0.15rem 0.45rem;
    border-radius: 4px;
    font-weight: 800;
  }

  .topic-snippet {
    font-size: 0.9rem;
    color: var(--text-secondary);
    margin: 0 0 1rem;
    line-height: 1.5;
  }

  .topic-card-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .cat-badge {
    background: var(--bg-tertiary);
    color: var(--text-secondary);
    padding: 0.2rem 0.55rem;
    border-radius: 6px;
    font-weight: 600;
    font-size: 0.72rem;
  }

  .topic-stats {
    display: flex;
    gap: 0.75rem;
  }

  .stat-item {
    font-size: 0.8rem;
    font-weight: 600;
    color: var(--text-muted);
  }

  .stat-item.liked {
    color: #ef4444;
  }

  /* Modal Overlay & Form */
  .modal-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.4);
    backdrop-filter: blur(4px);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
    padding: 1rem;
  }

  .modal-card {
    background: var(--bg-primary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-lg);
    width: 100%;
    max-width: 520px;
    padding: 1.75rem;
    box-shadow: var(--shadow-xl);
  }

  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1.25rem;
  }

  .modal-header h3 {
    font-size: 1.15rem;
    font-weight: 700;
    margin: 0;
    color: var(--text-primary);
  }

  .btn-icon {
    background: transparent;
    border: none;
    font-size: 1.1rem;
    cursor: pointer;
    color: var(--text-muted);
  }

  .form-field {
    margin-bottom: 1rem;
  }

  .form-field label {
    display: block;
    font-weight: 600;
    font-size: 0.85rem;
    margin-bottom: 0.35rem;
    color: var(--text-primary);
  }

  .form-field input, .form-field select, .form-field textarea {
    width: 100%;
    padding: 0.65rem 0.75rem;
    border: 1px solid var(--border-color);
    border-radius: var(--radius-md);
    background: var(--bg-secondary);
    color: var(--text-primary);
    font-family: inherit;
    font-size: 0.9rem;
  }

  .checkbox-field label {
    font-weight: 600;
    font-size: 0.85rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    cursor: pointer;
  }

  .modal-footer {
    display: flex;
    justify-content: flex-end;
    gap: 0.5rem;
    margin-top: 1.5rem;
  }

  /* Courses Grid */
  .courses-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 1.5rem;
  }

  .course-card {
    background: var(--bg-primary);
    border: 1px solid var(--border-light);
    border-radius: var(--radius-lg);
    overflow: hidden;
    display: flex;
    flex-direction: column;
    box-shadow: var(--shadow-xs);
    transition: transform var(--transition-fast), box-shadow var(--transition-fast);
  }

  .course-card:hover {
    transform: translateY(-3px);
    box-shadow: var(--shadow-md);
  }

  .course-card.locked {
    opacity: 0.9;
  }

  .course-link {
    text-decoration: none;
    color: inherit;
    display: block;
  }

  .course-cover {
    position: relative;
    height: 160px;
    overflow: hidden;
    background: var(--bg-tertiary);
  }

  .course-cover img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }

  .cover-placeholder {
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--text-muted);
  }

  .lock-overlay {
    position: absolute;
    inset: 0;
    background: rgba(0, 0, 0, 0.45);
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
  }

  .access-check {
    position: absolute;
    top: 0.75rem;
    right: 0.75rem;
    background: #10b981;
    color: white;
    border-radius: 50%;
    width: 26px;
    height: 26px;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .course-body {
    padding: 1.15rem;
    flex: 1;
  }

  .badge-access {
    display: inline-block;
    padding: 0.2rem 0.55rem;
    border-radius: 6px;
    font-size: 0.72rem;
    font-weight: 700;
  }

  .course-title {
    font-size: 1.05rem;
    font-weight: 700;
    margin: 0.5rem 0 0.4rem;
    color: var(--text-primary);
  }

  .course-desc {
    font-size: 0.85rem;
    color: var(--text-secondary);
    margin: 0 0 0.75rem;
    line-height: 1.45;
  }

  .course-meta {
    display: flex;
    gap: 1rem;
    font-size: 0.8rem;
    color: var(--text-muted);
  }

  .course-card-footer {
    padding: 0.85rem 1.15rem;
    border-top: 1px solid var(--border-light);
  }

  .btn-full {
    width: 100%;
    justify-content: center;
  }

  @media (max-width: 600px) {
    .area-container {
      padding: 1.5rem 1rem 3rem;
    }
    .feed-toolbar {
      flex-direction: column;
      align-items: stretch;
    }
  }
</style>
