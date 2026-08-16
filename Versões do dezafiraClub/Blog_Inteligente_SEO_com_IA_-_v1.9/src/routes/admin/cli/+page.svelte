<script lang="ts">
  import { page } from "$app/stores";
  import { t, formatDate as fmtDate, formatMoney } from "$lib/i18n";
  import { enhance } from '$app/forms';
  import type { Category } from '$lib/types';

  const lang = $derived($page.data.language || 'pt');

let {
    data,
    form
  }: {
    data: {
      token: string | null;
      tokenConfigured: boolean;
      tokenExpiresAt: number | null;
      categories: Category[];
      posts: { id: number; title: string; slug: string; published: boolean; created_at: string }[];
    };
    form?: { success?: boolean; token?: string; tokenExpiresAt?: number | null; error?: string };
  } = $props();

  // Always use the freshest token: form result takes priority over page data
  let currentToken = $derived(form?.token || data.token || '');
  let tokenConfigured = $derived(Boolean(currentToken) || data.tokenConfigured);

  let showToken = $state(false);
  let copied = $state(false);
  let loading = $state(false);
  let activeCopiedId = $state<string | null>(null);

  // Auto-reveal after regeneration
  $effect(() => {
    if (form?.success && form.token) {
      showToken = true;
    }
  });

  function toggleToken() {
    showToken = !showToken;
  }

  async function copyToken() {
    if (!currentToken) return;
    await navigator.clipboard.writeText(currentToken);
    copied = true;
    setTimeout(() => (copied = false), 2000);
  }

  async function copyCmd(text: string, id: string) {
    if (!text) return;
    await navigator.clipboard.writeText(text);
    activeCopiedId = id;
    setTimeout(() => {
      if (activeCopiedId === id) {
        activeCopiedId = null;
      }
    }, 2000);
  }

  const baseUrl = typeof window !== 'undefined' ? window.location.origin : 'https://seusite.com';

  // Escapes a string for safe rendering inside {@html} in a <code> block
  function cb(str: string): string {
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
  }
</script>

<svelte:head>
  <title>{t(lang, "admin.cli.title")} / API</title>
</svelte:head>

<div class="cli-page">
  <div class="page-header">
    <div>
      <h1>🖥️ {t(lang, "admin.cli.heading")}</h1>
      <p class="subtitle">{t(lang, "admin.cli.subtitle")}</p>
    </div>
  </div>

  {#if form?.error}
    <div class="alert alert-error">{form.error}</div>
  {/if}

  <!-- Token Card -->
  <section class="section">
    <div class="token-card">
      <div class="token-card-header">
        <div class="token-header-left">
          <div class="token-icon">🔑</div>
          <div>
            <h2>{t(lang, "admin.cli.auth_token")}</h2>
            <p>{t(lang, "admin.cli.auth_token_desc")}</p>
          </div>
        </div>
        <form method="POST" action="?/regenerate" use:enhance={() => {
          loading = true;
          return async ({ result, update }) => {
            loading = false;
            await update();
          };
        }}>
          <button type="submit" class="btn btn-danger" disabled={loading}>
            {loading ? '⟳ Gerando...' : '🔄 Regenerar Token'}
          </button>
        </form>
      </div>

      <div class="token-display">
        <div class="token-field">
          <span class="token-value" class:revealed={showToken}>
            {#if showToken}
              {currentToken || (tokenConfigured ? 'Token protegido — regenere para revelar' : t(lang, 'admin.cli.no_token'))}
            {:else}
              {tokenConfigured ? '••••••••••••••••••••••••••••••••••••••' : t(lang, 'admin.cli.no_token')}
            {/if}
          </span>
          <div class="token-actions">
            <button type="button" class="icon-btn" onclick={toggleToken} title={showToken ? 'Ocultar' : 'Mostrar'}>
              {#if showToken}
                <!-- Eye-off SVG -->
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/>
                  <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/>
                  <line x1="1" y1="1" x2="23" y2="23"/>
                </svg>
              {:else}
                <!-- Eye SVG -->
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                  <circle cx="12" cy="12" r="3"/>
                </svg>
              {/if}
            </button>
            <button type="button" class="icon-btn" onclick={copyToken} title="{t(lang, "admin.cli.copy_token")}" disabled={!currentToken}>
              {#if copied}
                <!-- Check SVG -->
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
              {:else}
                <!-- Copy SVG -->
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
                  <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
                </svg>
              {/if}
            </button>
          </div>
        </div>
        {#if !tokenConfigured}
          <p class="token-hint">⚠️ Clique em "Regenerar Token" para gerar seu primeiro token.</p>
        {:else if !currentToken}
          <p class="token-hint">🔒 Token protegido. Por segurança, ele só é exibido uma vez. Regenere para obter um novo valor.</p>
        {:else}
          <p class="token-hint">⚠️ Copie agora: o token não será exibido novamente e expira em 90 dias.</p>
        {/if}
      </div>

      <div class="token-usage">
        <span class="usage-label">Uso no header:</span>
        <code>Authorization: Bearer {currentToken || 'SEU_TOKEN'}</code>
        <button type="button" class="copy-inline" onclick={() => copyCmd(`Authorization: Bearer ${currentToken || 'SEU_TOKEN'}`, 'header-token')} title="Copiar Header">
          {#if activeCopiedId === 'header-token'}
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#22c55e" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="20 6 9 17 4 12"/>
            </svg>
          {:else}
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
              <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
            </svg>
          {/if}
        </button>
      </div>
    </div>
  </section>

  <!-- Quick Reference: Categories -->
  <section class="section">
    <h2 class="section-title">🏷️ {t(lang, "admin.cli.categories_title")}</h2>
    <div class="table-card">
      <table class="ref-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>{t(lang, "admin.ui.name")}</th>
            <th>{t(lang, "admin.ui.slug")}</th>
            <th>Pinterest</th>
            <th>Posts</th>
          </tr>
        </thead>
        <tbody>
          {#each data.categories as cat}
            <tr>
              <td><code>{cat.id}</code></td>
              <td>{cat.name}</td>
              <td><code>{cat.slug}</code></td>
              <td class="center">{cat.pinterest_enabled ? '✅' : '—'}</td>
              <td class="center">{cat.post_count || 0}</td>
            </tr>
          {/each}
          {#if data.categories.length === 0}
            <tr><td colspan="5" class="empty">{t(lang, "admin.cli.no_categories")}</td></tr>
          {/if}
        </tbody>
      </table>
    </div>
  </section>

  <!-- Recent Posts -->
  <section class="section">
    <h2 class="section-title">📝 {t(lang, "admin.cli.recent_posts")}</h2>
    <div class="table-card">
      <table class="ref-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>{t(lang, "admin.ui.title")}</th>
            <th>{t(lang, "admin.ui.slug")}</th>
            <th>{t(lang, "admin.ui.status")}</th>
            <th>{t(lang, "admin.ui.date")}</th>
          </tr>
        </thead>
        <tbody>
          {#each data.posts as post}
            <tr>
              <td><code>{post.id}</code></td>
              <td class="post-title">{post.title}</td>
              <td><code class="small">{post.slug}</code></td>
              <td class="center">
                <span class="badge" class:badge-pub={post.published} class:badge-draft={!post.published}>
                  {post.published ? t(lang, 'admin.ui.published') : t(lang, 'admin.ui.draft')}
                </span>
              </td>
              <td>{new Date(post.created_at).toLocaleDateString(lang === 'en' ? 'en-US' : lang === 'es' ? 'es-ES' : 'pt-BR')}</td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  </section>

  <!-- Full API Documentation -->
  <section class="section">
    <h2 class="section-title">📚 {t(lang, "admin.cli.full_docs")}</h2>

    <!-- Listar Posts -->
    <div class="doc-card">
      <div class="doc-header">
        <span class="method get">GET</span>
        <code class="endpoint">/api/cli/posts</code>
        <span class="doc-desc">Listar posts com paginação</span>
      </div>
      <div class="doc-body">
        <div class="code-block-wrapper">
          <div class="code-label">curl</div>
          <button class="copy-btn" onclick={() => copyCmd(`curl -H "Authorization: Bearer ${currentToken || 'SEU_TOKEN'}" "${baseUrl}/api/cli/posts?page=1&limit=25"`, 'get-posts')}>
            {#if activeCopiedId === 'get-posts'}
              <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#22c55e" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 4px;"><polyline points="20 6 9 17 4 12"/></svg>
              Copiado!
            {:else}
              <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 4px;"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
              {t(lang, "admin.ui.copy")}
            {/if}
          </button>
          <pre><code>curl -H "Authorization: Bearer {currentToken || 'SEU_TOKEN'}" \
  "{baseUrl}/api/cli/posts?page=1&amp;limit=25"</code></pre>
        </div>
        <div class="response-example">
          <div class="code-label">Resposta</div>
          <pre><code>{`{ "posts": [...], "pagination": { "page": 1, "limit": 25, "total": 42, "totalPages": 2 } }`}</code></pre>
        </div>
      </div>
    </div>

    <!-- Criar Post -->
    <div class="doc-card">
      <div class="doc-header">
        <span class="method post">POST</span>
        <code class="endpoint">/api/cli/posts</code>
        <span class="doc-desc">{t(lang, "admin.cli.create_post")}</span>
      </div>
      <div class="doc-body">
        <div class="fields-grid">
          <div class="field-item required"><code>title</code> <span>string — obrigatório</span></div>
          <div class="field-item required"><code>content</code> <span>string HTML — obrigatório</span></div>
          <div class="field-item"><code>excerpt</code> <span>string — resumo</span></div>
          <div class="field-item"><code>cover_image</code> <span>string URL — imagem de capa</span></div>
          <div class="field-item"><code>published</code> <span>boolean — publicar (default: false)</span></div>
          <div class="field-item"><code>pinterest_enabled</code> <span>boolean — incluir no feed Pinterest</span></div>
          <div class="field-item"><code>pinterest_image</code> <span>string URL — imagem vertical 9:16</span></div>
          <div class="field-item"><code>category_ids</code> <span>number[] — ex: [1, 2]</span></div>
          <div class="field-item"><code>is_18_plus</code> <span>boolean — conteúdo adulto</span></div>
          <div class="field-item"><code>is_premium</code> <span>boolean — conteúdo premium</span></div>
          <div class="field-item"><code>youtube_video_url</code> <span>string URL — vídeo relacionado</span></div>
          <div class="field-item"><code>tags</code> <span>string — tags separadas por vírgula</span></div>
          <div class="field-item"><code>slug</code> <span>string — URL customizada (opcional)</span></div>
        </div>
        <div class="code-block-wrapper">
          <div class="code-label">curl</div>
          <button class="copy-btn" onclick={() => copyCmd(`curl -X POST \\
  -H "Authorization: Bearer ${currentToken || 'SEU_TOKEN'}" \\
  -H "Content-Type: application/json" \\
  -d '{
    "title": "Meu Post Incrível",
    "content": "<p>Conteúdo do post em <strong>HTML</strong>.</p>",
    "excerpt": "Resumo do post",
    "cover_image": "https://exemplo.com/imagem.jpg",
    "published": true,
    "pinterest_enabled": true,
    "pinterest_image": "https://exemplo.com/vertical.jpg",
    "category_ids": [${data.categories[0]?.id || 1}],
    "is_18_plus": false
  }' \\
  ${baseUrl}/api/cli/posts`, 'create-post')}>
            {#if activeCopiedId === 'create-post'}
              <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#22c55e" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 4px;"><polyline points="20 6 9 17 4 12"/></svg>
              Copiado!
            {:else}
              <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 4px;"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
              {t(lang, "admin.ui.copy")}
            {/if}
          </button>
          <pre><code>curl -X POST \
  -H "Authorization: Bearer {currentToken || 'SEU_TOKEN'}" \
  -H "Content-Type: application/json" \
  -d '{'{'}
    "title": "Meu Post Incrível",
    "content": "&lt;p&gt;Conteúdo do post em &lt;strong&gt;HTML&lt;/strong&gt;.&lt;/p&gt;",
    "excerpt": "Resumo do post",
    "cover_image": "https://exemplo.com/imagem.jpg",
    "published": true,
    "pinterest_enabled": true,
    "pinterest_image": "https://exemplo.com/vertical.jpg",
    "category_ids": [{data.categories[0]?.id || 1}],
    "is_18_plus": false
  {'}'}' \
  {baseUrl}/api/cli/posts</code></pre>
        </div>
        <div class="response-example">
          <div class="code-label">Resposta 201</div>
          <pre><code>{'{ "success": true, "id": 42, "slug": "meu-post-incrivel" }'}</code></pre>
        </div>
      </div>
    </div>

    <!-- Ver Post -->
    <div class="doc-card">
      <div class="doc-header">
        <span class="method get">GET</span>
        <code class="endpoint">/api/cli/posts/:id</code>
        <span class="doc-desc">{t(lang, "admin.cli.get_post")}</span>
      </div>
      <div class="doc-body">
        <div class="code-block-wrapper">
          <div class="code-label">curl</div>
          <button class="copy-btn" onclick={() => copyCmd(`curl -H "Authorization: Bearer ${currentToken || 'SEU_TOKEN'}" ${baseUrl}/api/cli/posts/1`, 'view-post')}>
            {#if activeCopiedId === 'view-post'}
              <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#22c55e" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 4px;"><polyline points="20 6 9 17 4 12"/></svg>
              Copiado!
            {:else}
              <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 4px;"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
              {t(lang, "admin.ui.copy")}
            {/if}
          </button>
          <pre><code>curl -H "Authorization: Bearer {currentToken || 'SEU_TOKEN'}" \
  {baseUrl}/api/cli/posts/1</code></pre>
        </div>
      </div>
    </div>

    <!-- Editar Post -->
    <div class="doc-card">
      <div class="doc-header">
        <span class="method put">PUT</span>
        <code class="endpoint">/api/cli/posts/:id</code>
        <span class="doc-desc">{t(lang, "admin.cli.edit_post")}</span>
      </div>
      <div class="doc-body">
        <div class="code-block-wrapper">
          <div class="code-label">curl — Publicar + ativar Pinterest</div>
          <button class="copy-btn" onclick={() => copyCmd(`curl -X PUT \\
  -H "Authorization: Bearer ${currentToken || 'SEU_TOKEN'}" \\
  -H "Content-Type: application/json" \\
  -d '{"published": true, "pinterest_enabled": true}' \\
  ${baseUrl}/api/cli/posts/1`, 'edit-post-pub')}>
            {#if activeCopiedId === 'edit-post-pub'}
              <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#22c55e" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 4px;"><polyline points="20 6 9 17 4 12"/></svg>
              Copiado!
            {:else}
              <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 4px;"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
              {t(lang, "admin.ui.copy")}
            {/if}
          </button>
          <pre><code>{@html cb(`curl -X PUT \\\n  -H "Authorization: Bearer ${currentToken || 'SEU_TOKEN'}" \\\n  -H "Content-Type: application/json" \\\n  -d '{"published": true, "pinterest_enabled": true}' \\\n  ${baseUrl}/api/cli/posts/1`)}</code></pre>
        </div>
        <div class="code-block-wrapper">
          <div class="code-label">curl — Atualizar categorias</div>
          <pre><code>{@html cb(`curl -X PUT \\\n  -H "Authorization: Bearer ${currentToken || 'SEU_TOKEN'}" \\\n  -H "Content-Type: application/json" \\\n  -d '{"category_ids": [${data.categories.map(c => c.id).join(', ') || '1, 2'}]}' \\\n  ${baseUrl}/api/cli/posts/1`)}</code></pre>
        </div>
      </div>
    </div>

    <!-- Deletar Post -->
    <div class="doc-card">
      <div class="doc-header">
        <span class="method delete">DELETE</span>
        <code class="endpoint">/api/cli/posts/:id</code>
        <span class="doc-desc">{t(lang, "admin.cli.delete_post")}</span>
      </div>
      <div class="doc-body">
        <div class="code-block-wrapper">
          <div class="code-label">curl</div>
          <button class="copy-btn" onclick={() => copyCmd(`curl -X DELETE -H "Authorization: Bearer ${currentToken || 'SEU_TOKEN'}" ${baseUrl}/api/cli/posts/1?confirm=1`, 'delete-post')}>
            {#if activeCopiedId === 'delete-post'}
              <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#22c55e" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 4px;"><polyline points="20 6 9 17 4 12"/></svg>
              Copiado!
            {:else}
              <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 4px;"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
              {t(lang, "admin.ui.copy")}
            {/if}
          </button>
          <pre><code>curl -X DELETE \
  -H "Authorization: Bearer {currentToken || 'SEU_TOKEN'}" \
  {baseUrl}/api/cli/posts/1?confirm=1</code></pre>
        </div>
      </div>
    </div>

    <!-- ===== SEÇÃO UPLOAD ===== -->
    <div class="section-divider">
      <span>🖼️ Upload de Imagens — Cloudinary</span>
    </div>

    <div class="doc-card upload-card">
      <div class="doc-header">
        <span class="method post">POST</span>
        <code class="endpoint">/api/cli/upload</code>
        <span class="doc-desc">{t(lang, "admin.cli.upload_desc")}</span>
      </div>
      <div class="doc-body">
        <div class="pinterest-tip">
          <span>💡</span>
          <div>
            <strong>Fluxo recomendado:</strong> Faça o upload da imagem primeiro com este endpoint, 
            pegue a <code>url</code> retornada e use-a nos campos <code>cover_image</code> ou 
            <code>pinterest_image</code> ao criar/editar posts. O upload é feito diretamente 
            para o Cloudinary via servidor — seguro, sem expor credenciais.
          </div>
        </div>
        <div class="fields-grid">
          <div class="field-item required"><code>file</code> <span>arquivo — JPG, PNG, WEBP, GIF, AVIF (máx 20MB)</span></div>
          <div class="field-item"><code>folder</code> <span>string — subpasta no Cloudinary (default: "blog")</span></div>
        </div>
        <div class="code-block-wrapper">
          <div class="code-label">curl — Upload de imagem</div>
          <button class="copy-btn" onclick={() => copyCmd(`curl -X POST \\\n  -H "Authorization: Bearer ${currentToken || 'SEU_TOKEN'}" \\\n  -F "file=@/caminho/para/imagem.jpg" \\\n  -F "folder=blog" \\\n  ${baseUrl}/api/cli/upload`, 'upload-image')}>
            {#if activeCopiedId === 'upload-image'}
              <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#22c55e" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 4px;"><polyline points="20 6 9 17 4 12"/></svg>
              Copiado!
            {:else}
              <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 4px;"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
              {t(lang, "admin.ui.copy")}
            {/if}
          </button>
          <pre><code>{@html cb(`curl -X POST \\
  -H "Authorization: Bearer ${currentToken || 'SEU_TOKEN'}" \\
  -F "file=@/caminho/para/imagem.jpg" \\
  -F "folder=blog" \\
  ${baseUrl}/api/cli/upload`)}</code></pre>
        </div>
        <div class="code-block-wrapper">
          <div class="code-label">curl — Criar post com imagem em um só fluxo (shell script)</div>
          <button class="copy-btn" onclick={() => copyCmd(`#!/bin/bash\nTOKEN="${currentToken || 'SEU_TOKEN'}"\nBASE="${baseUrl}"\n\n# 1. Faz upload da imagem\nIMAGEM_URL=$(curl -s -X POST \\\n  -H "Authorization: Bearer $TOKEN" \\\n  -F "file=@capa.jpg" \\\n  "$BASE/api/cli/upload" | grep -o '"url":"[^"]*"' | cut -d'"' -f4)\n\necho "Imagem enviada: $IMAGEN_URL"\n\n# 2. Cria o post com a URL da imagem\ncurl -X POST \\\n  -H "Authorization: Bearer $TOKEN" \\\n  -H "Content-Type: application/json" \\\n  -d "{\\"title\\": \\"Título do Post\\", \\"content\\": \\"<p>Conteúdo</p>\\", \\"cover_image\\": \\"$IMAGEM_URL\\", \\"published\\": true}" \\\n  "$BASE/api/cli/posts"`, 'upload-post-flow')}>
            {#if activeCopiedId === 'upload-post-flow'}
              <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#22c55e" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 4px;"><polyline points="20 6 9 17 4 12"/></svg>
              Copiado!
            {:else}
              <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 4px;"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
              {t(lang, "admin.ui.copy")}
            {/if}
          </button>
          <pre><code>{@html cb(`#!/bin/bash
TOKEN="${currentToken || 'SEU_TOKEN'}"
BASE="${baseUrl}"

# 1. Faz upload da imagem
IMAGEM_URL=$(curl -s -X POST \\
  -H "Authorization: Bearer $TOKEN" \\
  -F "file=@capa.jpg" \\
  "$BASE/api/cli/upload" | python3 -c "import sys,json; print(json.load(sys.stdin)['url'])")

echo "Imagem: $IMAGEM_URL"

# 2. Cria o post com a URL retornada
curl -X POST \\
  -H "Authorization: Bearer $TOKEN" \\
  -H "Content-Type: application/json" \\
  -d "{\\"title\\": \\"Título\\", \\"content\\": \\"<p>Corpo</p>\\", \\"cover_image\\": \\"$IMAGEM_URL\\", \\"published\\": true}" \\
  "$BASE/api/cli/posts"`)}</code></pre>
        </div>
        <div class="response-example">
          <div class="code-label">Resposta 201</div>
          <pre><code>{'{ "success": true, "url": "https://res.cloudinary.com/SEU_CLOUD/image/upload/v123/blog/imagem.jpg", "filename": "capa.jpg", "size": 348210, "type": "image/jpeg" }'}</code></pre>
        </div>
      </div>
    </div>

    <!-- ===== SEÇÃO PINTEREST ===== -->
    <div class="section-divider">
      <span>📌 Pinterest — Automação de Feed</span>
    </div>


    <!-- Pinterest em Post: criar -->
    <div class="doc-card pinterest-card">
      <div class="doc-header">
        <span class="method post">POST</span>
        <code class="endpoint">/api/cli/posts</code>
        <span class="doc-desc">Criar post com Pinterest ativado (exemplo completo)</span>
      </div>
      <div class="doc-body">
        <div class="pinterest-tip">
          <span>💡</span>
          <div>
            <strong>Como funciona:</strong> Ao criar ou editar um post, passe <code>pinterest_enabled: true</code> 
            e opcionalmente <code>pinterest_image</code> com URL de uma imagem vertical (9:16, ideal 1000×1500px). 
            O post aparecerá automaticamente em <code>/pinterest.xml</code> e nos feeds por categoria.
          </div>
        </div>
        <div class="code-block-wrapper">
          <div class="code-label">curl — Post com Pinterest</div>
          <button class="copy-btn" onclick={() => copyCmd(`curl -X POST \\
  -H "Authorization: Bearer ${currentToken || 'SEU_TOKEN'}" \\
  -H "Content-Type: application/json" \\
  -d '{
    "title": "Look do Dia: Casual Chic",
    "content": "<p>Conteúdo do post...</p>",
    "excerpt": "Visual leve e sofisticado para o dia a dia",
    "cover_image": "https://res.cloudinary.com/exemplo/imagem.jpg",
    "published": true,
    "pinterest_enabled": true,
    "pinterest_image": "https://res.cloudinary.com/exemplo/vertical-9x16.jpg",
    "category_ids": [${data.categories[0]?.id || 1}],
    "is_18_plus": false
  }' \\
  ${baseUrl}/api/cli/posts`, 'create-post-pinterest')}>
            {#if activeCopiedId === 'create-post-pinterest'}
              <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#22c55e" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 4px;"><polyline points="20 6 9 17 4 12"/></svg>
              Copiado!
            {:else}
              <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 4px;"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
              {t(lang, "admin.ui.copy")}
            {/if}
          </button>
          <pre><code>curl -X POST \
  -H "Authorization: Bearer {currentToken || 'SEU_TOKEN'}" \
  -H "Content-Type: application/json" \
  -d '{'{'} 
    "title": "Look do Dia: Casual Chic",
    "content": "&lt;p&gt;Conteúdo do post...&lt;/p&gt;",
    "excerpt": "Visual leve e sofisticado para o dia a dia",
    "cover_image": "https://res.cloudinary.com/exemplo/imagem.jpg",
    "published": true,
    "pinterest_enabled": true,
    "pinterest_image": "https://res.cloudinary.com/exemplo/vertical-9x16.jpg",
    "category_ids": [{data.categories[0]?.id || 1}],
    "is_18_plus": false
  {'}'}' \
  {baseUrl}/api/cli/posts</code></pre>
        </div>
      </div>
    </div>

    <!-- Pinterest em Post: ativar/desativar -->
    <div class="doc-card pinterest-card">
      <div class="doc-header">
        <span class="method put">PUT</span>
        <code class="endpoint">/api/cli/posts/:id</code>
        <span class="doc-desc">Ativar ou desativar Pinterest em post existente</span>
      </div>
      <div class="doc-body">
        <div class="code-block-wrapper">
          <div class="code-label">curl — Ativar Pinterest + definir imagem vertical</div>
          <button class="copy-btn" onclick={() => copyCmd(`curl -X PUT \\
  -H "Authorization: Bearer ${currentToken || 'SEU_TOKEN'}" \\
  -H "Content-Type: application/json" \\
  -d '{"pinterest_enabled": true, "pinterest_image": "https://res.cloudinary.com/exemplo/vertical.jpg"}' \\
  ${baseUrl}/api/cli/posts/1`, 'edit-post-pinterest')}>
            {#if activeCopiedId === 'edit-post-pinterest'}
              <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#22c55e" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 4px;"><polyline points="20 6 9 17 4 12"/></svg>
              Copiado!
            {:else}
              <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 4px;"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
              {t(lang, "admin.ui.copy")}
            {/if}
          </button>
          <pre><code>{@html cb(`curl -X PUT \\\n  -H "Authorization: Bearer ${currentToken || 'SEU_TOKEN'}" \\\n  -H "Content-Type: application/json" \\\n  -d '{"pinterest_enabled": true, "pinterest_image": "https://res.cloudinary.com/exemplo/vertical.jpg"}' \\\n  ${baseUrl}/api/cli/posts/1`)}</code></pre>
        </div>
        <div class="code-block-wrapper">
          <div class="code-label">curl — Desativar Pinterest</div>
          <button class="copy-btn" onclick={() => copyCmd(`curl -X PUT -H "Authorization: Bearer ${currentToken || 'SEU_TOKEN'}" -H "Content-Type: application/json" -d '{"pinterest_enabled": false}' ${baseUrl}/api/cli/posts/1`, 'disable-post-pinterest')}>
            {#if activeCopiedId === 'disable-post-pinterest'}
              <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#22c55e" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 4px;"><polyline points="20 6 9 17 4 12"/></svg>
              Copiado!
            {:else}
              <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 4px;"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
              {t(lang, "admin.ui.copy")}
            {/if}
          </button>
          <pre><code>{@html cb(`curl -X PUT \\\n  -H "Authorization: Bearer ${currentToken || 'SEU_TOKEN'}" \\\n  -H "Content-Type: application/json" \\\n  -d '{"pinterest_enabled": false}' \\\n  ${baseUrl}/api/cli/posts/1`)}</code></pre>
        </div>
      </div>
    </div>

    <!-- PATCH categories/:id — Pinterest da categoria -->
    <div class="doc-card pinterest-card">
      <div class="doc-header">
        <span class="method patch">PATCH</span>
        <code class="endpoint">/api/cli/categories/:id</code>
        <span class="doc-desc">Ativar ou desativar o feed Pinterest de uma categoria</span>
      </div>
      <div class="doc-body">
        <div class="pinterest-tip">
          <span>💡</span>
          <div>
            <strong>Por que isso importa:</strong> Cada categoria com <code>pinterest_enabled: true</code> gera 
            automaticamente o feed <code>/pinterest_{"<slug>"}.xml</code> para conectar como board separado no Pinterest.
            Por exemplo, a categoria "Looks" gera o feed <code>/pinterest_looks.xml</code>.
          </div>
        </div>
        <div class="fields-grid">
          <div class="field-item required"><code>pinterest_enabled</code> <span>boolean — obrigatório</span></div>
        </div>
        <div class="code-block-wrapper">
          <div class="code-label">curl — Ativar Pinterest na categoria</div>
          <button class="copy-btn" onclick={() => copyCmd(`curl -X PATCH \\
  -H "Authorization: Bearer ${currentToken || 'SEU_TOKEN'}" \\
  -H "Content-Type: application/json" \\
  -d '{"pinterest_enabled": true}' \\
  ${baseUrl}/api/cli/categories/${data.categories[0]?.id || 1}`, 'enable-cat-pinterest')}>
            {#if activeCopiedId === 'enable-cat-pinterest'}
              <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#22c55e" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 4px;"><polyline points="20 6 9 17 4 12"/></svg>
              Copiado!
            {:else}
              <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 4px;"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
              {t(lang, "admin.ui.copy")}
            {/if}
          </button>
          <pre><code>{@html cb(`curl -X PATCH \\\n  -H "Authorization: Bearer ${currentToken || 'SEU_TOKEN'}" \\\n  -H "Content-Type: application/json" \\\n  -d '{"pinterest_enabled": true}' \\\n  ${baseUrl}/api/cli/categories/${data.categories[0]?.id || 1}`)}</code></pre>
        </div>
        <div class="code-block-wrapper">
          <div class="code-label">curl — Desativar Pinterest na categoria</div>
          <button class="copy-btn" onclick={() => copyCmd(`curl -X PATCH -H "Authorization: Bearer ${currentToken || 'SEU_TOKEN'}" -H "Content-Type: application/json" -d '{"pinterest_enabled": false}' ${baseUrl}/api/cli/categories/${data.categories[0]?.id || 1}`, 'disable-cat-pinterest')}>
            {#if activeCopiedId === 'disable-cat-pinterest'}
              <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#22c55e" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 4px;"><polyline points="20 6 9 17 4 12"/></svg>
              Copiado!
            {:else}
              <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 4px;"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
              {t(lang, "admin.ui.copy")}
            {/if}
          </button>
          <pre><code>{@html cb(`curl -X PATCH \\\n  -H "Authorization: Bearer ${currentToken || 'SEU_TOKEN'}" \\\n  -H "Content-Type: application/json" \\\n  -d '{"pinterest_enabled": false}' \\\n  ${baseUrl}/api/cli/categories/${data.categories[0]?.id || 1}`)}</code></pre>
        </div>
        <div class="response-example">
          <div class="code-label">Resposta</div>
          <pre><code>{'{ "success": true, "category": { "id": 1, "name": "Looks", "slug": "looks", "pinterest_enabled": true }, "message": "Pinterest ativado para a categoria \\"Looks\\"." }'}</code></pre>
        </div>

        {#if data.categories.length > 0}
          <div class="categories-quick">
            <strong>Suas categorias (use o ID no comando acima):</strong>
            <div class="cat-pills">
              {#each data.categories as cat}
                <div class="cat-pill" class:pill-active={Boolean(cat.pinterest_enabled)}>
                  <code>{cat.id}</code>
                  <span>{cat.name}</span>
                  <span class="pill-status">{cat.pinterest_enabled ? ('📌 ' + t(lang, 'admin.cli.active')) : ('— ' + t(lang, 'admin.cli.inactive'))}</span>
                </div>
              {/each}
            </div>
          </div>
        {/if}
      </div>
    </div>


    <!-- Erros -->
    <div class="doc-card error-codes-card">
      <div class="doc-header">
        <span class="method info">INFO</span>
        <code class="endpoint">{t(lang, "admin.cli.error_codes")}</code>
      </div>
      <div class="doc-body">
        <table class="ref-table">
          <thead><tr><th>{t(lang, "admin.cli.code")}</th><th>{t(lang, "admin.cli.meaning")}</th><th>{t(lang, "admin.cli.solution")}</th></tr></thead>
          <tbody>
            <tr><td><code>401</code></td><td>Header Authorization ausente</td><td>Adicione <code>-H "Authorization: Bearer TOKEN"</code></td></tr>
            <tr><td><code>403</code></td><td>Token inválido ou expirado</td><td>Regenere o token nesta página</td></tr>
            <tr><td><code>400</code></td><td>Dados inválidos</td><td>Verifique o JSON e campos obrigatórios</td></tr>
            <tr><td><code>404</code></td><td>Post/recurso não encontrado</td><td>Verifique o ID ou slug</td></tr>
            <tr><td><code>201</code></td><td>Post criado com sucesso</td><td>—</td></tr>
            <tr><td><code>200</code></td><td>Sucesso</td><td>—</td></tr>
          </tbody>
        </table>
      </div>
    </div>
  </section>
</div>


<style>
  .cli-page {
    max-width: 1100px;
    margin: 0 auto;
    display: flex;
    flex-direction: column;
    gap: 2rem;
  }

  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
  }

  .page-header h1 {
    font-family: var(--font-sans);
    font-size: 1.5rem;
    font-weight: 700;
    margin: 0 0 0.25rem;
  }

  .subtitle {
    color: var(--text-secondary);
    font-size: 0.9375rem;
    margin: 0;
  }

  .section {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .section-title {
    font-family: var(--font-sans);
    font-size: 1.25rem;
    font-weight: 600;
    margin: 0;
    padding-bottom: 0.75rem;
    border-bottom: 1px solid var(--border-light);
  }

  /* Token Card */
  .token-card {
    background: var(--bg-primary);
    border: 1px solid var(--border-light);
    border-radius: var(--radius-lg);
    overflow: hidden;
  }

  .token-card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1.5rem;
    border-bottom: 1px solid var(--border-light);
    gap: 1rem;
    flex-wrap: wrap;
  }

  .token-header-left {
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  .token-icon {
    font-size: 2rem;
    line-height: 1;
  }

  .token-card-header h2 {
    font-family: var(--font-sans);
    font-size: 1rem;
    font-weight: 600;
    margin: 0 0 0.25rem;
  }

  .token-card-header p {
    font-size: 0.875rem;
    color: var(--text-secondary);
    margin: 0;
  }

  .token-display {
    padding: 1.5rem;
    background: var(--bg-secondary);
    border-bottom: 1px solid var(--border-light);
  }

  .token-field {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    background: var(--bg-primary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-md);
    padding: 0.875rem 1rem;
    margin-bottom: 0.75rem;
  }

  .token-value {
    flex: 1;
    font-family: 'Monaco', 'Consolas', monospace;
    font-size: 0.8125rem;
    color: var(--text-secondary);
    word-break: break-all;
    transition: color 0.2s;
  }

  .token-value.revealed {
    color: var(--text-primary);
  }

  .token-actions {
    display: flex;
    gap: 0.5rem;
    flex-shrink: 0;
  }

  .icon-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
    background: none;
    border: 1px solid var(--border-color);
    border-radius: var(--radius-sm);
    color: var(--text-secondary);
    cursor: pointer;
    transition: all 0.15s;
    flex-shrink: 0;
  }

  .icon-btn:hover {
    background: var(--bg-tertiary);
    color: var(--text-primary);
    border-color: var(--text-muted);
  }

  .icon-btn:disabled { opacity: 0.35; cursor: not-allowed; }
  .icon-btn:disabled:hover { background: none; border-color: var(--border-color); color: var(--text-secondary); }

  .token-hint {
    font-size: 0.8125rem;
    color: var(--text-muted);
    margin: 0;
  }

  .token-usage {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 1rem 1.5rem;
    flex-wrap: wrap;
  }

  .usage-label {
    font-size: 0.8125rem;
    font-weight: 600;
    color: var(--text-secondary);
    white-space: nowrap;
  }

  .token-usage code {
    background: var(--bg-tertiary);
    padding: 0.25rem 0.5rem;
    border-radius: var(--radius-sm);
    font-size: 0.8125rem;
    flex: 1;
    word-break: break-all;
  }

  .copy-inline {
    background: none;
    border: none;
    cursor: pointer;
    font-size: 0.875rem;
    padding: 0.25rem;
    transition: transform 0.15s, color 0.15s;
    color: var(--text-secondary);
    display: inline-flex;
    align-items: center;
    justify-content: center;
  }

  .copy-inline:hover {
    transform: scale(1.1);
    color: var(--text-primary);
  }

  /* Buttons */
  .btn {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.625rem 1.25rem;
    border-radius: var(--radius-md);
    font-size: 0.875rem;
    font-weight: 500;
    border: 1px solid transparent;
    cursor: pointer;
    transition: all 0.15s;
    text-decoration: none;
  }

  .btn-danger {
    background: #fee2e2;
    color: #dc2626;
    border-color: #fca5a5;
  }

  .btn-danger:hover { background: #fecaca; }
  .btn:disabled { opacity: 0.6; cursor: not-allowed; }

  /* Tables */
  .table-card {
    background: var(--bg-primary);
    border: 1px solid var(--border-light);
    border-radius: var(--radius-lg);
    overflow: auto;
  }

  .ref-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.875rem;
  }

  .ref-table th {
    padding: 0.75rem 1rem;
    text-align: left;
    font-weight: 600;
    font-size: 0.8125rem;
    color: var(--text-secondary);
    background: var(--bg-secondary);
    border-bottom: 1px solid var(--border-light);
  }

  .ref-table td {
    padding: 0.75rem 1rem;
    border-bottom: 1px solid var(--border-light);
    vertical-align: middle;
  }

  .ref-table tr:last-child td { border-bottom: none; }
  .ref-table tr:hover td { background: var(--bg-secondary); }

  .ref-table code {
    background: var(--bg-tertiary);
    padding: 0.15rem 0.4rem;
    border-radius: 3px;
    font-size: 0.8125rem;
  }

  .center { text-align: center; }

  .post-title {
    max-width: 300px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .small { font-size: 0.75rem; }

  .badge {
    display: inline-block;
    padding: 0.2rem 0.6rem;
    border-radius: 99px;
    font-size: 0.75rem;
    font-weight: 500;
  }

  .badge-pub { background: #d1fae5; color: #065f46; }
  .badge-draft { background: var(--bg-tertiary); color: var(--text-muted); }

  .empty { color: var(--text-muted); font-style: italic; text-align: center; padding: 2rem; }

  /* Doc Cards */
  .doc-card {
    background: var(--bg-primary);
    border: 1px solid var(--border-light);
    border-radius: var(--radius-lg);
    overflow: hidden;
  }

  .doc-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 1rem 1.25rem;
    background: var(--bg-secondary);
    border-bottom: 1px solid var(--border-light);
    flex-wrap: wrap;
  }

  .method {
    display: inline-block;
    padding: 0.25rem 0.6rem;
    border-radius: var(--radius-sm);
    font-size: 0.75rem;
    font-weight: 700;
    font-family: monospace;
    min-width: 60px;
    text-align: center;
  }

  .get { background: #dbeafe; color: #1d4ed8; }
  .post { background: #d1fae5; color: #065f46; }
  .put { background: #fef3c7; color: #92400e; }
  .delete { background: #fee2e2; color: #dc2626; }
  .patch { background: #f3e8ff; color: #7c3aed; }
  .info { background: var(--bg-tertiary); color: var(--text-secondary); }

  .section-divider {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-top: 1rem;
    color: var(--text-secondary);
    font-size: 0.875rem;
    font-weight: 600;
  }

  .section-divider::before,
  .section-divider::after {
    content: '';
    flex: 1;
    height: 1px;
    background: var(--border-light);
  }

  .pinterest-card {
    border-color: #e9d5ff;
  }

  .upload-card {
    border-color: #bbf7d0;
  }

  .pinterest-tip {
    display: flex;
    gap: 0.75rem;
    background: #faf5ff;
    border: 1px solid #e9d5ff;
    border-radius: var(--radius-md);
    padding: 0.875rem 1rem;
    font-size: 0.875rem;
    color: var(--text-secondary);
    line-height: 1.6;
  }

  .pinterest-tip span:first-child {
    font-size: 1.25rem;
    flex-shrink: 0;
    margin-top: 0.1rem;
  }

  .pinterest-tip code {
    background: #ede9fe;
    color: #6d28d9;
    padding: 0.1rem 0.35rem;
    border-radius: 3px;
    font-size: 0.8125rem;
  }

  .categories-quick {
    background: var(--bg-secondary);
    border: 1px solid var(--border-light);
    border-radius: var(--radius-md);
    padding: 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    font-size: 0.875rem;
  }

  .cat-pills {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  .cat-pill {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.35rem 0.75rem;
    border-radius: 99px;
    border: 1px solid var(--border-color);
    background: var(--bg-primary);
    font-size: 0.8125rem;
  }

  .cat-pill.pill-active {
    border-color: #c4b5fd;
    background: #f5f3ff;
  }

  .pill-status {
    color: var(--text-muted);
    font-size: 0.75rem;
  }

  .cat-pill.pill-active .pill-status {
    color: #7c3aed;
  }

  .endpoint {
    font-family: monospace;
    font-size: 0.9375rem;
    color: var(--text-primary);
  }

  .doc-desc {
    color: var(--text-secondary);
    font-size: 0.875rem;
  }

  .doc-body {
    padding: 1.25rem;
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .fields-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 0.5rem;
  }

  .field-item {
    display: flex;
    align-items: baseline;
    gap: 0.5rem;
    font-size: 0.8125rem;
    padding: 0.4rem 0.75rem;
    background: var(--bg-secondary);
    border-radius: var(--radius-sm);
    border-left: 3px solid var(--border-color);
  }

  .field-item.required {
    border-left-color: #dc2626;
  }

  .field-item code {
    font-weight: 600;
    color: var(--text-primary);
    white-space: nowrap;
  }

  .field-item span {
    color: var(--text-secondary);
    font-size: 0.75rem;
  }

  .code-block-wrapper {
    position: relative;
    background: #1e1e2e;
    border-radius: var(--radius-md);
    overflow: hidden;
  }

  .code-label {
    font-size: 0.75rem;
    font-weight: 600;
    color: #6c7086;
    padding: 0.5rem 1rem 0;
    font-family: monospace;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .copy-btn {
    position: absolute;
    top: 0.5rem;
    right: 0.75rem;
    background: rgba(255,255,255,0.15);
    border: 1px solid rgba(255,255,255,0.2);
    border-radius: var(--radius-sm);
    color: #cdd6f4;
    font-size: 0.75rem;
    padding: 0.35rem 0.6rem;
    cursor: pointer;
    transition: background 0.15s, border-color 0.15s;
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    font-family: var(--font-sans);
  }

  .copy-btn:hover {
    background: rgba(255,255,255,0.25);
    border-color: rgba(255,255,255,0.3);
  }

  .code-block-wrapper pre {
    margin: 0;
    padding: 0.75rem 1rem 1rem;
    overflow-x: auto;
  }

  .code-block-wrapper code {
    font-family: 'Monaco', 'Consolas', monospace;
    font-size: 0.8125rem;
    color: #cdd6f4;
    line-height: 1.7;
    white-space: pre;
  }

  .response-example {
    background: var(--bg-secondary);
    border: 1px solid var(--border-light);
    border-radius: var(--radius-md);
    overflow: hidden;
  }

  .response-example .code-label {
    color: var(--text-muted);
    padding: 0.5rem 1rem 0;
  }

  .response-example pre {
    margin: 0;
    padding: 0.5rem 1rem 0.75rem;
    overflow-x: auto;
  }

  .response-example code {
    font-family: monospace;
    font-size: 0.8125rem;
    color: var(--text-secondary);
    white-space: pre-wrap;
    word-break: break-all;
  }

  .error-codes-card .ref-table {
    font-size: 0.8125rem;
  }

  .alert {
    padding: 0.875rem 1rem;
    border-radius: var(--radius-md);
    font-size: 0.875rem;
  }

  .alert-error {
    background: #fee2e2;
    color: #dc2626;
    border: 1px solid #fca5a5;
  }

  @media (max-width: 640px) {
    .token-card-header {
      flex-direction: column;
      align-items: flex-start;
    }

    .doc-header {
      flex-direction: column;
      align-items: flex-start;
      gap: 0.5rem;
    }
  }
</style>
