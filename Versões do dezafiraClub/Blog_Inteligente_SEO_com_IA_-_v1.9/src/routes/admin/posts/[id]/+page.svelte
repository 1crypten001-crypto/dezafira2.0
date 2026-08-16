<script lang="ts">
  import { page } from "$app/stores";
  import { t, formatDate as fmtDate, formatMoney } from "$lib/i18n";
  import { enhance } from "$app/forms";
  import type { Post, Category } from "$lib/types";

  const lang = $derived($page.data.language || 'pt');

interface FormData {
    post?: Partial<Post>;
    error?: string;
  }

  let {
    data,
    form,
  }: {
    data: { post: Post; categories: Category[]; postCategoryIds: number[]; products?: any[]; postProductIds?: number[] };
    form?: FormData;
  } = $props();
  let post = $derived(form?.post || data.post);
  let loading = $state(false);
  let editorRef = $state<HTMLDivElement | null>(null);
  let showHtml = $state(false);
  let showYoutubeModal = $state(false);
  let youtubeUrl = $state("");
  let activeTab = $state<"general" | "pinterest">("general");
  let pinterestEnabledValue = $state(false);
  let is18PlusValue = $state(false);
  let pinterestImageValue = $state("");
  let youtubeVideoUrlValue = $state("");
  let tagsValue = $state("");

  $effect(() => {
    if (data.post) {
      pinterestEnabledValue = Boolean(data.post.pinterest_enabled);
      is18PlusValue = Boolean(data.post.is_18_plus);
      pinterestImageValue = data.post.pinterest_image || "";
      youtubeVideoUrlValue = data.post.youtube_video_url || "";
      tagsValue = data.post.tags || "";
    }
  });
  let coverImagePreviewUrl = $state<string | null>(null);
  let coverImageFileName = $state<string | null>(null);
  let pinterestImagePreviewUrl = $state<string | null>(null);
  let pinterestImageFileName = $state<string | null>(null);
  let selectedCategoryIds = $state<number[]>(data.postCategoryIds ? [...data.postCategoryIds] : []);
  let selectedProductIds = $state<number[]>(data.postProductIds ? [...data.postProductIds] : []);
  let htmlContent = $state(form?.post?.content || data.post?.content || "");
  let coverImageValue = $state(form?.post?.cover_image || data.post?.cover_image || "");

  function handleCoverFileChange(e: Event) {
    const input = e.target as HTMLInputElement;
    const file = input.files?.[0];

    if (!file) {
      if (coverImagePreviewUrl) {
        URL.revokeObjectURL(coverImagePreviewUrl);
      }
      coverImagePreviewUrl = null;
      coverImageFileName = null;
      return;
    }

    if (coverImagePreviewUrl) {
      URL.revokeObjectURL(coverImagePreviewUrl);
    }
    coverImagePreviewUrl = URL.createObjectURL(file);
    coverImageFileName = file.name;
  }

  let selectedCategories = $derived(
    data.categories.filter((c) => selectedCategoryIds.includes(c.id)),
  );
  let pinterestFeedCategories = $derived(
    selectedCategories.filter((c) => Boolean(c.pinterest_enabled)),
  );
  let pinterestFeedDisabledCategories = $derived(
    selectedCategories.filter((c) => !Boolean(c.pinterest_enabled)),
  );
  let primaryCategory = $derived(selectedCategories[0]);

  let isInserting = $state(false);

  // Sync HTML content from contenteditable
  function syncContent() {
    if (editorRef) {
      htmlContent = editorRef.innerHTML;
    }
  }

  // Action to initialize editor content without Svelte reactivity loop
  function editorAction(node: HTMLElement) {
    node.innerHTML = htmlContent;
    return {
      update(newContent: string) {
        // Only update if significantly different (e.g. external change)
      },
    };
  }

  // Handle clicks inside editor (for delete buttons)
  function handleEditorClick(e: MouseEvent) {
    const target = e.target as HTMLElement;
    if (target.classList.contains("delete-embed-btn")) {
      const embed = target.closest(".video-embed");
      embed?.remove();
      syncContent();
    }
  }

  // Execute formatting command
  function execCommand(command: string, value: string | null = null) {
    document.execCommand(command, false, value ?? undefined);
    editorRef?.focus();
    syncContent();
  }

  function formatBold() {
    execCommand("bold");
  }
  function formatItalic() {
    execCommand("italic");
  }
  function formatH2() {
    execCommand("formatBlock", "h2");
  }
  function formatH3() {
    execCommand("formatBlock", "h3");
  }
  function formatParagraph() {
    execCommand("formatBlock", "p");
  }
  function formatList() {
    execCommand("insertUnorderedList");
  }
  function formatBlockquote() {
    execCommand("formatBlock", "blockquote");
  }

  function formatLink() {
    const url = prompt("Digite a URL do link:");
    if (url) {
      execCommand("createLink", url);
    }
  }

  function handlePinterestFileChange(e: Event) {
    const input = e.target as HTMLInputElement;
    const file = input.files?.[0];

    if (!file) {
      if (pinterestImagePreviewUrl) {
        URL.revokeObjectURL(pinterestImagePreviewUrl);
      }
      pinterestImagePreviewUrl = null;
      pinterestImageFileName = null;
      return;
    }

    if (pinterestImagePreviewUrl) {
      URL.revokeObjectURL(pinterestImagePreviewUrl);
    }
    pinterestImagePreviewUrl = URL.createObjectURL(file);
    pinterestImageFileName = file.name;
  }

  function extractYoutubeId(url: string): string | null {
    const patterns = [
      /(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\s?]+)/,
      /youtube\.com\/shorts\/([^&\s?]+)/,
    ];

    for (const pattern of patterns) {
      const match = url.match(pattern);
      if (match) return match[1];
    }
    return null;
  }

  function insertYoutube() {
    if (isInserting) return;

    // Validate first
    const videoId = extractYoutubeId(youtubeUrl);
    if (!videoId) {
      alert("URL do YouTube inválida.");
      return;
    }

    isInserting = true;

    // Button to delete the embed (only visible in editor via CSS)
    const deleteBtn = `<button type="button" class="delete-embed-btn" contenteditable="false" title="Remover vídeo">❌</button>`;
    const embedCode = `<div class="video-embed" contenteditable="false">${deleteBtn}<iframe src="https://www.youtube.com/embed/${videoId}" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe></div><p><br></p>`;

    // Clear state
    youtubeUrl = "";
    showYoutubeModal = false;

    if (editorRef) {
      editorRef.focus();
      // Use setTimeout to ensure UI update and prevent race conditions
      setTimeout(() => {
        try {
          document.execCommand("insertHTML", false, embedCode);
          syncContent();
        } finally {
          isInserting = false;
        }
      }, 100);
    } else {
      isInserting = false;
    }
  }

  function openYoutubeModal() {
    showYoutubeModal = true;
    youtubeUrl = "";
  }

  function closeYoutubeModal() {
    showYoutubeModal = false;
    youtubeUrl = "";
  }

  function openPinterestImageModal() {
    showPinterestModal = true;
  }

  function closePinterestModal() {
    showPinterestModal = false;
  }

  let showPinterestModal = $state(false);
  let pinterestUrlInput = $state("");

  function applyPinterestImage() {
    pinterestImageValue = pinterestUrlInput;
    closePinterestModal();
  }

  function toggleHtmlView() {
    if (showHtml && editorRef) {
      // Switching from HTML to visual - update editor
      editorRef.innerHTML = htmlContent;
    } else if (editorRef) {
      // Switching from visual to HTML - sync content
      htmlContent = editorRef.innerHTML;
    }
    showHtml = !showHtml;
  }

  function handleHtmlInput(e: Event) {
    const target = e.target as HTMLTextAreaElement;
    htmlContent = target.value;
    if (editorRef) {
      editorRef.innerHTML = htmlContent;
    }
  }

  $effect(() => {
    pinterestEnabledValue = Boolean(post?.pinterest_enabled);
    if (!pinterestImagePreviewUrl) {
      pinterestImageValue = post?.pinterest_image || "";
    }
    coverImageValue = post?.cover_image || "";
  });
</script>

<svelte:head>
  <title>Admin | {t(lang, "admin.posts.edit_title")}: {post.title}</title>
</svelte:head>

<div class="editor-page">
  <div class="editor-header">
    <h1>{t(lang, "admin.posts.edit_title")}</h1>
    <div class="header-actions">
      <a href="/post/{post.slug}" class="btn" target="_blank">👁️ Ver Post</a>
      <a href="/admin/posts" class="btn">{t(lang, "admin.ui.cancel")}</a>
    </div>
  </div>

  {#if form?.error}
    <div class="message message-error">{form.error}</div>
  {/if}

  <form
    method="POST"
    enctype="multipart/form-data"
    use:enhance={({ formData }) => {
      // Garantir sincronização do estado
      syncContent();
      
      // Capturar o título atual do input diretamente do DOM
      const titleInput = document.querySelector('input[name="title"]') as HTMLInputElement;
      const finalTitle = titleInput ? titleInput.value : titleValue;
      formData.set('title', finalTitle);
      
      // Obter o conteúdo diretamente do DOM (seja do editor visual ou do textarea HTML)
      let finalContent = '';
      if (showHtml) {
        const textarea = document.querySelector('.html-textarea') as HTMLTextAreaElement;
        finalContent = textarea ? textarea.value : htmlContent;
      } else if (editorRef) {
        finalContent = editorRef.innerHTML;
      } else {
        finalContent = htmlContent;
      }
      formData.set('content', finalContent);
      
      loading = true;
      
      return async ({ result, update }) => {
        loading = false;
        await update();
      };
    }}
  >
    <!-- Tab Navigation -->
    <div class="tab-navigation">
      <button
        type="button"
        class="tab-button"
        class:active={activeTab === "general"}
        onclick={() => activeTab = "general"}
      >
        📝 Geral
      </button>
      <button
        type="button"
        class="tab-button"
        class:active={activeTab === "pinterest"}
        onclick={() => activeTab = "pinterest"}
      >
        <svg viewBox="0 0 20 20" fill="currentColor" width="14" height="14" style="color: #e60023; display: inline-block; margin-right: 4px; vertical-align: middle;">
          <path d="M9.04 14.63c-.35 1.89-.78 3.7-2.06 4.65-.39-2.79.58-4.87 1.03-7.09-1.73-2.9 1.5-5.87 3.37-2.79 2.34 3.69-2.03 7.14.91 8.01 3.07.91 4.33-3.94 2.42-5.36-2.76-1.97-8.02-.45-6.97 4.42.27 1.22 1.41 1.59.49 2.28-.73.53-1.97-.17-2.3-1.21-.79-2.57.28-5.35 1.68-7.11 1.4-1.76 3.5-2.01 5.43-1.99 3.29.03 6.38 1.48 6.81 5.26.49 4.28-1.82 8.98-6.12 8.66-1.17-.08-1.99-.64-2.16-1.73zM10 0C4.48 0 0 4.48 0 10s4.48 10 10 10 10-4.48 10-10S15.52 0 10 0z"/>
        </svg>Pinterest
      </button>
    </div>

    <!-- Tab Content: General -->
    <div class="tab-panel" hidden={activeTab !== "general"}>
    <div class="editor-layout">
      <div class="editor-main">
        <!-- Title Input -->
        <div class="title-input-wrapper">
          <input
            type="text"
            id="title"
            name="title"
            class="title-input"
            value={post.title}
            required
            placeholder="Adicionar título"
          />
        </div>

        <!-- Content Editor -->
        <div class="content-editor-wrapper">
          <div class="editor-toolbar">
            <div class="toolbar-group">
              <button
                type="button"
                class="toolbar-btn"
                onclick={formatBold}
                title="Negrito (Ctrl+B)"
              >
                <strong>B</strong>
              </button>
              <button
                type="button"
                class="toolbar-btn"
                onclick={formatItalic}
                title="Itálico (Ctrl+I)"
              >
                <em>I</em>
              </button>
            </div>
            <div class="toolbar-divider"></div>
            <div class="toolbar-group">
              <button
                type="button"
                class="toolbar-btn"
                onclick={formatH2}
                title="Título 2"
              >
                H2
              </button>
              <button
                type="button"
                class="toolbar-btn"
                onclick={formatH3}
                title="Título 3"
              >
                H3
              </button>
            </div>
            <div class="toolbar-divider"></div>
            <div class="toolbar-group">
              <button
                type="button"
                class="toolbar-btn"
                onclick={formatParagraph}
                title="Parágrafo"
              >
                ¶
              </button>
              <button
                type="button"
                class="toolbar-btn"
                onclick={formatList}
                title="Lista"
              >
                ☰
              </button>
              <button
                type="button"
                class="toolbar-btn"
                onclick={formatBlockquote}
                title="Citação"
              >
                "
              </button>
            </div>
            <div class="toolbar-divider"></div>
            <div class="toolbar-group">
              <button
                type="button"
                class="toolbar-btn"
                onclick={formatLink}
                title="Link"
              >
                🔗
              </button>
              <button
                type="button"
                class="toolbar-btn youtube-btn"
                onclick={openYoutubeModal}
                title="Inserir vídeo do YouTube"
              >
                ▶️
              </button>
            </div>
            <div class="toolbar-spacer"></div>
            <div class="toolbar-group">
              <button
                type="button"
                class="toolbar-btn html-btn"
                class:active={showHtml}
                onclick={toggleHtmlView}
                title="Ver/Editar HTML"
              >
                {"</>"}
              </button>
            </div>
          </div>

          {#if showHtml}
            <textarea
              class="html-textarea"
              value={htmlContent}
              oninput={handleHtmlInput}
              placeholder="Edite o HTML aqui..."
            ></textarea>
          {:else}
            <div
              bind:this={editorRef}
              use:editorAction
              class="visual-editor article-content"
              contenteditable="true"
              oninput={syncContent}
              onkeydown={(e) => {
                if (e.ctrlKey) {
                  if (e.key === "b") {
                    e.preventDefault();
                    formatBold();
                  }
                  if (e.key === "i") {
                    e.preventDefault();
                    formatItalic();
                  }
                }
              }}
              onclick={handleEditorClick}
              role="textbox"
              aria-multiline="true"
              data-placeholder="Comece a escrever seu post..."
              tabindex="0"
            ></div>
          {/if}

          <!-- Hidden input to submit content -->
          <input type="hidden" name="content" value={htmlContent} />
        </div>
      </div>

      <div class="editor-sidebar">
        <div class="sidebar-card">
          <h3>Publicação</h3>
          <div class="publish-options">
            <label class="checkbox-label">
              <input
                type="checkbox"
                name="published"
                checked={Boolean(post.published)}
              />
              <span>Publicado</span>
            </label>
            <label class="checkbox-label">
              <input
                type="checkbox"
                name="is_18_plus"
                bind:checked={is18PlusValue}
              />
              <span>Conteúdo +18</span>
            </label>
          </div>
          <button
            type="submit"
            class="btn btn-primary publish-btn"
            disabled={loading}
          >
            {loading ? t(lang, "admin.ui.saving") : t(lang, "admin.ui.save_changes")}
          </button>
        </div>

        <div class="sidebar-card">
          <h3>URL do Post</h3>
          <div class="form-group">
            <input
              type="text"
              id="slug"
              name="slug"
              class="form-input"
              value={post.slug}
              placeholder="url-do-post"
            />
            <small class="hint"
              >Altere com cuidado (pode quebrar links existentes)</small
            >
          </div>
        </div>

        <div class="sidebar-card">
          <h3>Imagem de Capa</h3>
          <div class="form-group">
            <input
              type="text"
              id="cover_image"
              name="cover_image"
              class="form-input"
              bind:value={coverImageValue}
              placeholder="https://exemplo.com/imagem.jpg ou escolha um arquivo abaixo"
            />
            <div class="file-picker-row">
              <input
                id="cover_image_file"
                type="file"
                name="cover_image_file"
                class="file-input-hidden"
                accept="image/*"
                onchange={handleCoverFileChange}
              />
              <label for="cover_image_file" class="btn btn-small">Escolher arquivo</label>
              {#if coverImageFileName}
                <span class="file-name" title={coverImageFileName}>{coverImageFileName}</span>
              {/if}
            </div>
            {#if coverImagePreviewUrl}
              <div class="cover-preview">
                <img src={coverImagePreviewUrl} alt="Preview" />
              </div>
            {:else if coverImageValue}
              <div class="cover-preview">
                <img src={coverImageValue} alt="Preview" />
              </div>
            {/if}
            <small class="hint">URL da imagem de destaque ou envie um arquivo (proporção 16:9 recomendada)</small>
          </div>
        </div>

        <div class="sidebar-card">
          <h3>Vídeo em Destaque (YouTube)</h3>
          <div class="form-group">
            <input
              type="url"
              id="youtube_video_url"
              name="youtube_video_url"
              class="form-input"
              bind:value={youtubeVideoUrlValue}
              placeholder="https://www.youtube.com/watch?v=..."
            />
            <small class="hint"
              >Opcional. Insira a URL do vídeo do YouTube para ativar o player automático com animação premium no post.</small
            >
          </div>
        </div>

        <div class="sidebar-card">
          <h3>Resumo</h3>
          <div class="form-group">
            <textarea
              id="excerpt"
              name="excerpt"
              class="form-textarea excerpt-textarea"
              rows="4"
              placeholder="Breve descrição do post..."
              >{post.excerpt || ""}</textarea
            >
          </div>
        </div>

        <div class="sidebar-card">
          <h3>Tags (Invisíveis)</h3>
          <div class="form-group">
            <input
              type="text"
              id="tags"
              name="tags"
              class="form-input"
              placeholder="Ex: IA, SEO, Pinterest, Svelte"
              bind:value={tagsValue}
            />
            <small class="hint">Separadas por vírgula. Usadas para melhorar as recomendações de conteúdo do blog.</small>
          </div>
        </div>

        {#if data.categories && data.categories.length > 0}
          <div class="sidebar-card">
            <h3>Categorias</h3>
            <div class="categories-checkboxes">
              {#each data.categories as category}
                <label class="checkbox-label">
                  <input
                    type="checkbox"
                    name="categories"
                    value={category.id}
                    bind:group={selectedCategoryIds}
                  />
                  <span>{category.name}</span>
                </label>
              {/each}
            </div>
          </div>
        {/if}

        {#if data.products && data.products.length > 0}
          <div class="sidebar-card">
            <h3>Produtos Digitais Anexados</h3>
            <div class="categories-checkboxes">
              {#each data.products as product}
                <label class="checkbox-label">
                  <input
                    type="checkbox"
                    name="products"
                    value={product.id}
                    bind:group={selectedProductIds}
                  />
                  <span>{product.name} ({product.price_cents === 0 ? 'Grátis' : (product.price_cents / 100).toLocaleString(lang === 'en' ? 'en-US' : lang === 'es' ? 'es-ES' : 'pt-BR', { style: 'currency', currency: 'BRL' })})</span>
                </label>
              {/each}
            </div>
          </div>
        {/if}

        <div class="sidebar-card">
          <h3>Informações</h3>
          <div class="info-item">
            <span class="info-label">Criado em:</span>
            <span class="info-value">
              {post.created_at
                ? new Date(post.created_at).toLocaleDateString(lang === 'en' ? 'en-US' : lang === 'es' ? 'es-ES' : 'pt-BR')
                : "-"}
            </span>
          </div>
          {#if post.updated_at}
            <div class="info-item">
              <span class="info-label">Atualizado em:</span>
              <span class="info-value">
                {new Date(post.updated_at).toLocaleDateString(lang === 'en' ? 'en-US' : lang === 'es' ? 'es-ES' : 'pt-BR')}
              </span>
            </div>
          {/if}
        </div>
      </div>
    </div>
    </div>

    <!-- Tab Content: Pinterest -->
    <div class="tab-panel" hidden={activeTab !== "pinterest"}>
    <div class="pinterest-layout">
      <div class="pinterest-main">
        <div class="pinterest-card">
          <h2>
            <svg viewBox="0 0 20 20" fill="currentColor" width="18" height="18" style="color: #e60023; display: inline-block; margin-right: 6px; vertical-align: middle;">
              <path d="M9.04 14.63c-.35 1.89-.78 3.7-2.06 4.65-.39-2.79.58-4.87 1.03-7.09-1.73-2.9 1.5-5.87 3.37-2.79 2.34 3.69-2.03 7.14.91 8.01 3.07.91 4.33-3.94 2.42-5.36-2.76-1.97-8.02-.45-6.97 4.42.27 1.22 1.41 1.59.49 2.28-.73.53-1.97-.17-2.3-1.21-.79-2.57.28-5.35 1.68-7.11 1.4-1.76 3.5-2.01 5.43-1.99 3.29.03 6.38 1.48 6.81 5.26.49 4.28-1.82 8.98-6.12 8.66-1.17-.08-1.99-.64-2.16-1.73zM10 0C4.48 0 0 4.48 0 10s4.48 10 10 10 10-4.48 10-10S15.52 0 10 0z"/>
            </svg>Configuração do Pinterest
          </h2>
          <p class="pinterest-description">
            Configure este post para ser distribuído automaticamente via feed RSS para o Pinterest.
            O Pinterest importará seus artigos como Pins automaticamente.
          </p>

          <div class="pinterest-toggle-wrapper">
            <label class="pinterest-toggle-label">
              <input
                type="checkbox"
                name="pinterest_enabled"
                bind:checked={pinterestEnabledValue}
              />
              <span class="toggle-switch"></span>
              <span class="toggle-text">
                <strong>Disponibilizar no Feed do Pinterest</strong>
                <small>Ative para incluir este post no feed RSS do Pinterest</small>
              </span>
            </label>
          </div>

          <div class="pinterest-image-section">
            <h3>Imagem Vertical para o Pin (9:16)</h3>
            <p class="hint">
              Use uma imagem vertical otimizada para o Pinterest (1000×1500px ou 1080×1920px recomendado).
              Esta imagem é independente da imagem de capa do blog.
            </p>

            <div class="form-group">
              <label for="pinterest_image" class="form-label">URL da Imagem Pinterest</label>
              <input
                type="text"
                id="pinterest_image"
                name="pinterest_image"
                class="form-input"
                bind:value={pinterestImageValue}
                placeholder="https://exemplo.com/imagem-vertical.jpg"
              />
              <div class="file-upload-row">
                <input
                  id="pinterest_image_file"
                  type="file"
                  name="pinterest_image_file"
                  class="file-input-hidden"
                  accept="image/*"
                  onchange={handlePinterestFileChange}
                />
                <label for="pinterest_image_file" class="btn btn-small">Escolher arquivo</label>
                {#if pinterestImageFileName}
                  <span class="file-name" title={pinterestImageFileName}>{pinterestImageFileName}</span>
                {/if}
              </div>
              <button
                type="button"
                class="btn btn-small"
                onclick={openPinterestImageModal}
              >
                🔗 Inserir URL da Imagem
              </button>
            </div>

            {#if pinterestImagePreviewUrl}
              <div class="pimage-preview-container">
                <div class="pimage-preview">
                  <img src={pinterestImagePreviewUrl} alt="Preview Pinterest" />
                  <div class="pimage-aspect-ratio">9:16</div>
                </div>
                <p class="hint">Pré-visualização da imagem vertical para o Pinterest</p>
              </div>
            {:else if pinterestImageValue}
              <div class="pimage-preview-container">
                <div class="pimage-preview">
                  <img src={pinterestImageValue} alt="Preview Pinterest" />
                  <div class="pimage-aspect-ratio">9:16</div>
                </div>
                <p class="hint">Pré-visualização da imagem vertical para o Pinterest</p>
              </div>
            {/if}
          </div>

          <div class="pinterest-info">
            <h3>📋 Como funciona</h3>
            <ol class="pinterest-steps">
              <li>Ative o toggle "Disponibilizar no Feed do Pinterest"</li>
              <li>Faça upload de uma imagem vertical (proporção 9:16)</li>
              <li>Salve o post</li>
              <li>
                Cadastre no Pinterest o feed global (<code>/pinterest.xml</code>) ou um feed por categoria
                (<code>/pinterest_categoria.xml</code>) para usar como pasta/board
              </li>
            </ol>
            
            {#if pinterestEnabledValue}
              <div class="pinterest-feed-url">
                <strong>URL do Feed para cadastrar no Pinterest:</strong>
                {#if primaryCategory}
                  <code class="feed-url-code">{new URL(`/pinterest_${primaryCategory.slug}.xml`, typeof window !== 'undefined' ? window.location.origin : 'http://localhost:5174').href}</code>
                {:else}
                  <code class="feed-url-code">{new URL('/pinterest.xml', typeof window !== 'undefined' ? window.location.origin : 'http://localhost:5174').href}</code>
                {/if}
                <button type="button" class="btn btn-small copy-btn" onclick={() => {
                  const url = primaryCategory
                    ? new URL(`/pinterest_${primaryCategory.slug}.xml`, typeof window !== 'undefined' ? window.location.origin : 'http://localhost:5174').href
                    : new URL('/pinterest.xml', typeof window !== 'undefined' ? window.location.origin : 'http://localhost:5174').href;
                  navigator.clipboard.writeText(url);
                  alert('URL copiada!');
                }}>
                  📋 Copiar URL
                </button>
              </div>

              <div class="pinterest-feed-url">
                <strong>Feed global (todos os posts habilitados):</strong>
                <code class="feed-url-code">{new URL('/pinterest.xml', typeof window !== 'undefined' ? window.location.origin : 'http://localhost:5174').href}</code>
                <button type="button" class="btn btn-small copy-btn" onclick={() => {
                  const url = new URL('/pinterest.xml', typeof window !== 'undefined' ? window.location.origin : 'http://localhost:5174').href;
                  navigator.clipboard.writeText(url);
                  alert('URL copiada!');
                }}>
                  📋 Copiar URL
                </button>
              </div>

              {#if pinterestFeedCategories.length > 0 || pinterestFeedDisabledCategories.length > 0}
                <div class="pinterest-feed-url">
                  <strong>Feeds por categoria (para pastas/boards):</strong>
                  {#each pinterestFeedCategories as cat}
                    <div class="category-feed-row">
                      <code class="feed-url-code">{new URL(`/pinterest_${cat.slug}.xml`, typeof window !== 'undefined' ? window.location.origin : 'http://localhost:5174').href}</code>
                      <button type="button" class="btn btn-small copy-btn" onclick={() => {
                        const url = new URL(`/pinterest_${cat.slug}.xml`, typeof window !== 'undefined' ? window.location.origin : 'http://localhost:5174').href;
                        navigator.clipboard.writeText(url);
                        alert('URL copiada!');
                      }}>
                        📋 Copiar URL
                      </button>
                    </div>
                  {/each}
                  {#each pinterestFeedDisabledCategories as cat}
                    <div class="category-feed-row">
                      <code class="feed-url-code">{new URL(`/pinterest_${cat.slug}.xml`, typeof window !== 'undefined' ? window.location.origin : 'http://localhost:5174').href}</code>
                      <button type="button" class="btn btn-small copy-btn" onclick={() => {
                        const url = new URL(`/pinterest_${cat.slug}.xml`, typeof window !== 'undefined' ? window.location.origin : 'http://localhost:5174').href;
                        navigator.clipboard.writeText(url);
                        alert('URL copiada!');
                      }}>
                        📋 Copiar URL
                      </button>
                      <span class="feed-status">Desativado</span>
                    </div>
                  {/each}
                </div>
              {/if}

              {#if pinterestFeedDisabledCategories.length > 0}
                <p class="hint">
                  Algumas categorias deste post não estão habilitadas para Pinterest. Ative em
                  <a href="/admin/categories" class="inline-link">Categorias</a>.
                </p>
              {/if}
            {/if}
          </div>

          <div class="pinterest-actions">
            <button
              type="submit"
              class="btn btn-primary"
              disabled={loading}
            >
              {loading ? t(lang, "admin.ui.saving") : t(lang, "admin.ui.save_changes")}
            </button>
            <p class="hint">
              Salve o post nesta aba para manter o toggle e a imagem do Pinterest após recarregar a página.
            </p>
          </div>
        </div>
      </div>
    </div>
    </div>
  </form>
</div>

<!-- YouTube Modal -->
{#if showYoutubeModal}
  <div
    class="modal-overlay"
    role="dialog"
    aria-modal="true"
    tabindex="-1"
    onclick={closeYoutubeModal}
    onkeydown={(e) => e.key === "Escape" && closeYoutubeModal()}
  >
    <div class="modal" role="document" onclick={(e) => e.stopPropagation()} onkeydown={(e) => e.stopPropagation()}>
      <div class="modal-header">
        <h2>Inserir Vídeo do YouTube</h2>
        <button type="button" class="modal-close" onclick={closeYoutubeModal}
          >✕</button
        >
      </div>
      <div class="modal-body">
        <div class="form-group">
          <label for="youtube-url" class="form-label">URL do Vídeo</label>
          <input
            type="text"
            id="youtube-url"
            class="form-input"
            bind:value={youtubeUrl}
            placeholder="https://youtube.com/watch?v=..."
          />
          <small class="hint">
            Formatos aceitos: youtube.com/watch?v=..., youtu.be/...,
            youtube.com/shorts/...
          </small>
        </div>
      </div>
      <div class="modal-footer">
        <button type="button" class="btn" onclick={closeYoutubeModal}
          >{t(lang, "admin.ui.cancel")}</button
        >
        <button type="button" class="btn btn-primary" onclick={insertYoutube}
          >Inserir Vídeo</button
        >
      </div>
    </div>
  </div>
{/if}

<!-- Pinterest Image Modal -->
{#if showPinterestModal}
  <div
    class="modal-overlay"
    role="dialog"
    aria-modal="true"
    tabindex="-1"
    onclick={closePinterestModal}
    onkeydown={(e) => e.key === "Escape" && closePinterestModal()}
  >
    <div class="modal" role="document" onclick={(e) => e.stopPropagation()} onkeydown={(e) => e.stopPropagation()}>
      <div class="modal-header">
        <h2>
          <svg viewBox="0 0 20 20" fill="currentColor" width="18" height="18" style="color: #e60023; display: inline-block; margin-right: 6px; vertical-align: middle;">
            <path d="M9.04 14.63c-.35 1.89-.78 3.7-2.06 4.65-.39-2.79.58-4.87 1.03-7.09-1.73-2.9 1.5-5.87 3.37-2.79 2.34 3.69-2.03 7.14.91 8.01 3.07.91 4.33-3.94 2.42-5.36-2.76-1.97-8.02-.45-6.97 4.42.27 1.22 1.41 1.59.49 2.28-.73.53-1.97-.17-2.3-1.21-.79-2.57.28-5.35 1.68-7.11 1.4-1.76 3.5-2.01 5.43-1.99 3.29.03 6.38 1.48 6.81 5.26.49 4.28-1.82 8.98-6.12 8.66-1.17-.08-1.99-.64-2.16-1.73zM10 0C4.48 0 0 4.48 0 10s4.48 10 10 10 10-4.48 10-10S15.52 0 10 0z"/>
          </svg>Inserir URL da Imagem Pinterest
        </h2>
        <button type="button" class="modal-close" onclick={closePinterestModal}
          >✕</button
        >
      </div>
      <div class="modal-body">
        <div class="form-group">
          <label for="pinterest-url-input" class="form-label">URL da Imagem Vertical (9:16)</label>
          <input
            type="text"
            id="pinterest-url-input"
            class="form-input"
            bind:value={pinterestUrlInput}
            placeholder="https://exemplo.com/imagem-vertical.jpg"
          />
          <small class="hint">
            Proporção recomendada: 9:16 (1000×1500px ou 1080×1920px)
          </small>
        </div>
      </div>
      <div class="modal-footer">
        <button type="button" class="btn" onclick={closePinterestModal}
          >{t(lang, "admin.ui.cancel")}</button
        >
        <button type="button" class="btn btn-primary" onclick={applyPinterestImage}
          >Aplicar Imagem</button
        >
      </div>
    </div>
  </div>
{/if}

<style>
  .editor-page {
    max-width: 1400px;
    margin: 0 auto;
  }

  .editor-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1.5rem;
  }

  .editor-header h1 {
    font-family: var(--font-sans);
    font-size: 1.5rem;
    font-weight: 700;
  }

  .header-actions {
    display: flex;
    gap: 0.75rem;
  }

  .editor-layout {
    display: grid;
    grid-template-columns: 1fr 320px;
    gap: 1.5rem;
    align-items: start;
  }

  .editor-main {
    display: flex;
    flex-direction: column;
    gap: 0;
  }

  /* Title Input */
  .title-input-wrapper {
    background: var(--bg-primary);
    border: 1px solid var(--border-color);
    border-bottom: none;
    border-radius: var(--radius-lg) var(--radius-lg) 0 0;
    overflow: hidden;
  }

  .title-input {
    width: 100%;
    padding: 1.5rem;
    font-family: var(--font-sans);
    font-size: 1.75rem;
    font-weight: 600;
    border: none;
    background: transparent;
    color: var(--text-primary);
    outline: none;
  }

  .title-input::placeholder {
    color: var(--text-muted);
  }

  /* Content Editor */
  .content-editor-wrapper {
    background: var(--bg-primary);
    border: 1px solid var(--border-color);
    border-radius: 0 0 var(--radius-lg) var(--radius-lg);
    overflow: hidden;
  }

  .editor-toolbar {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    padding: 0.75rem 1rem;
    background: var(--bg-tertiary);
    border-bottom: 1px solid var(--border-color);
    flex-wrap: wrap;
  }

  .toolbar-group {
    display: flex;
    gap: 2px;
  }

  .toolbar-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 36px;
    height: 36px;
    background: var(--bg-primary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-sm);
    font-family: var(--font-sans);
    font-size: 0.875rem;
    color: var(--text-primary);
    cursor: pointer;
    transition: all var(--transition-fast);
  }

  .toolbar-btn:hover {
    background: var(--bg-secondary);
    border-color: var(--border-dark);
  }

  .toolbar-btn:active {
    transform: scale(0.95);
  }

  .youtube-btn {
    background: #fee2e2;
  }

  .youtube-btn:hover {
    background: #fecaca;
  }

  .html-btn.active {
    background: var(--text-primary);
    color: var(--bg-primary);
    border-color: var(--text-primary);
  }

  .toolbar-divider {
    width: 1px;
    height: 24px;
    background: var(--border-color);
    margin: 0 0.5rem;
  }

  .toolbar-spacer {
    flex: 1;
  }

  /* Visual Editor (Contenteditable) */
  .visual-editor {
    min-height: 500px;
    padding: 1.5rem;
    outline: none;
    cursor: text;
  }

  .visual-editor:empty::before {
    content: attr(data-placeholder);
    color: var(--text-muted);
    pointer-events: none;
  }

  .visual-editor:focus {
    outline: none;
  }

  /* HTML Textarea */
  .html-textarea {
    width: 100%;
    min-height: 500px;
    padding: 1.5rem;
    font-family: "Monaco", "Consolas", "Courier New", monospace;
    font-size: 0.9375rem;
    line-height: 1.7;
    border: none;
    background: var(--bg-tertiary);
    color: var(--text-primary);
    resize: vertical;
    outline: none;
  }

  /* Sidebar */
  .editor-sidebar {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    position: sticky;
    top: 1rem;
  }

  .sidebar-card {
    background: var(--bg-primary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-lg);
    padding: 1.25rem;
  }

  .sidebar-card h3 {
    font-family: var(--font-sans);
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: var(--text-secondary);
    margin-bottom: 1rem;
  }

  .publish-options {
    margin-bottom: 1rem;
  }

  .checkbox-label {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    cursor: pointer;
    font-family: var(--font-sans);
    font-size: 0.875rem;
    color: var(--text-primary);
  }

  .checkbox-label input {
    width: 1.125rem;
    height: 1.125rem;
    cursor: pointer;
  }

  .publish-btn {
    width: 100%;
    padding: 0.875rem;
  }

  .form-group {
    margin-bottom: 0;
  }

  .excerpt-textarea {
    min-height: 100px;
    font-size: 0.9375rem;
  }

  .hint {
    display: block;
    margin-top: 0.5rem;
    font-family: var(--font-sans);
    font-size: 0.75rem;
    color: var(--text-muted);
  }

  .cover-preview {
    margin-top: 0.75rem;
    border-radius: var(--radius-md);
    overflow: hidden;
    aspect-ratio: 16 / 9;
    border: 1px solid var(--border-color);
  }

  .cover-preview img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }

  .info-item {
    display: flex;
    justify-content: space-between;
    padding: 0.5rem 0;
    border-bottom: 1px solid var(--border-light);
    font-family: var(--font-sans);
    font-size: 0.8125rem;
  }

  .info-item:last-child {
    border-bottom: none;
    padding-bottom: 0;
  }

  .info-label {
    color: var(--text-muted);
  }

  .info-value {
    color: var(--text-primary);
  }

  /* Embedded Objects Styles for Editor */
  :global(.video-embed) {
    position: relative;
    user-select: none;
  }

  :global(.delete-embed-btn) {
    position: absolute;
    top: -12px;
    right: -12px;
    z-index: 10;
    width: 24px;
    height: 24px;
    border-radius: 50%;
    background: #ff4444;
    color: white;
    border: 2px solid white;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    cursor: pointer;
    opacity: 0;
    transition: opacity 0.2s;
  }

  :global(.video-embed:hover .delete-embed-btn) {
    opacity: 1;
  }

  /* Modal */
  .modal-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
    animation: fadeIn 0.2s ease-out;
  }

  .modal {
    background: var(--bg-primary);
    border-radius: var(--radius-lg);
    width: 100%;
    max-width: 500px;
    margin: 1rem;
    box-shadow: var(--shadow-xl);
    animation: scaleIn 0.2s ease-out;
  }

  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1.25rem 1.5rem;
    border-bottom: 1px solid var(--border-color);
  }

  .modal-header h2 {
    font-family: var(--font-sans);
    font-size: 1.25rem;
    font-weight: 600;
  }

  .modal-close {
    background: none;
    border: none;
    font-size: 1.25rem;
    color: var(--text-muted);
    cursor: pointer;
    padding: 0.25rem;
    line-height: 1;
  }

  .modal-close:hover {
    color: var(--text-primary);
  }

  .modal-body {
    padding: 1.5rem;
  }

  .modal-footer {
    display: flex;
    justify-content: flex-end;
    gap: 0.75rem;
    padding: 1rem 1.5rem;
    border-top: 1px solid var(--border-color);
    background: var(--bg-secondary);
    border-radius: 0 0 var(--radius-lg) var(--radius-lg);
  }

  @keyframes fadeIn {
    from {
      opacity: 0;
    }
    to {
      opacity: 1;
    }
  }

  @keyframes scaleIn {
    from {
      opacity: 0;
      transform: scale(0.95);
    }
    to {
      opacity: 1;
      transform: scale(1);
    }
  }

  @media (max-width: 1024px) {
    .editor-layout {
      grid-template-columns: 1fr;
    }

    .editor-sidebar {
      position: static;
      flex-direction: row;
      flex-wrap: wrap;
    }

    .sidebar-card {
      flex: 1;
      min-width: 200px;
    }
  }

  @media (max-width: 640px) {
    .editor-header {
      flex-direction: column;
      gap: 1rem;
      align-items: stretch;
    }

    .header-actions {
      justify-content: flex-end;
    }

    .title-input {
      font-size: 1.25rem;
      padding: 1rem;
    }

    .visual-editor,
    .html-textarea {
      min-height: 400px;
      padding: 1rem;
    }

    .editor-toolbar {
      padding: 0.5rem;
    }

    .toolbar-btn {
      width: 32px;
      height: 32px;
      font-size: 0.75rem;
    }

    .sidebar-card {
      min-width: 100%;
    }
  }

  /* Tab Navigation */
  .tab-navigation {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 1.5rem;
    border-bottom: 2px solid var(--border-color);
    padding-bottom: 0;
  }

  .tab-panel[hidden] {
    display: none !important;
  }

  .tab-button {
    padding: 0.75rem 1.5rem;
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-bottom: none;
    border-radius: var(--radius-lg) var(--radius-lg) 0 0;
    font-family: var(--font-sans);
    font-size: 0.9375rem;
    font-weight: 500;
    color: var(--text-secondary);
    cursor: pointer;
    transition: all var(--transition-fast);
    position: relative;
    bottom: -2px;
  }

  .tab-button:hover {
    background: var(--bg-tertiary);
    color: var(--text-primary);
  }

  .tab-button.active {
    background: var(--bg-primary);
    color: var(--text-primary);
    border-color: var(--border-dark);
    border-bottom: 2px solid var(--bg-primary);
    font-weight: 600;
  }

  /* Pinterest Layout */
  .pinterest-layout {
    max-width: 900px;
    margin: 0 auto;
  }

  .pinterest-main {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }

  .pinterest-card {
    background: var(--bg-primary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-lg);
    padding: 2rem;
  }

  .pinterest-card h2 {
    font-family: var(--font-sans);
    font-size: 1.25rem;
    font-weight: 600;
    margin-bottom: 1rem;
    color: var(--text-primary);
  }

  .pinterest-description {
    font-family: var(--font-sans);
    font-size: 0.9375rem;
    color: var(--text-secondary);
    line-height: 1.6;
    margin-bottom: 1.5rem;
  }

  /* Pinterest Toggle */
  .pinterest-toggle-wrapper {
    margin-bottom: 2rem;
    padding: 1.5rem;
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-md);
  }

  .pinterest-toggle-label {
    display: flex;
    align-items: center;
    gap: 1rem;
    cursor: pointer;
  }

  .pinterest-toggle-label input[type="checkbox"] {
    display: none;
  }

  .toggle-switch {
    position: relative;
    width: 52px;
    height: 28px;
    background: var(--border-color);
    border-radius: 14px;
    transition: background var(--transition-fast);
    flex-shrink: 0;
  }

  .toggle-switch::after {
    content: '';
    position: absolute;
    top: 3px;
    left: 3px;
    width: 22px;
    height: 22px;
    background: white;
    border-radius: 50%;
    transition: transform var(--transition-fast);
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  }

  .pinterest-toggle-label input[type="checkbox"]:checked + .toggle-switch {
    background: #e60023; /* Pinterest Red */
  }

  .pinterest-toggle-label input[type="checkbox"]:checked + .toggle-switch::after {
    transform: translateX(24px);
  }

  .toggle-text {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .toggle-text strong {
    font-family: var(--font-sans);
    font-size: 1rem;
    color: var(--text-primary);
  }

  .toggle-text small {
    font-family: var(--font-sans);
    font-size: 0.8125rem;
    color: var(--text-muted);
  }

  /* Pinterest Image Section */
  .pinterest-image-section {
    margin-bottom: 2rem;
  }

  .pinterest-image-section h3 {
    font-family: var(--font-sans);
    font-size: 1.125rem;
    font-weight: 600;
    margin-bottom: 0.75rem;
    color: var(--text-primary);
  }

  .pimage-preview-container {
    margin-top: 1rem;
    position: relative;
  }

  .file-upload-row {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin: 0.75rem 0;
    flex-wrap: wrap;
  }

  .file-input-hidden {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border: 0;
  }

  .file-name {
    font-size: 0.75rem;
    color: var(--text-muted);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    max-width: 280px;
  }

  .category-feed-row {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-top: 0.5rem;
    flex-wrap: wrap;
  }

  .feed-status {
    font-size: 0.75rem;
    color: var(--text-muted);
    border: 1px solid var(--border-color);
    background: var(--bg-tertiary);
    padding: 0.25rem 0.5rem;
    border-radius: var(--radius-sm);
  }

  .inline-link {
    text-decoration: underline;
  }

  .pimage-preview {
    position: relative;
    width: 100%;
    max-width: 300px;
    margin: 0 auto;
    border-radius: var(--radius-md);
    overflow: hidden;
    border: 2px solid var(--border-color);
    aspect-ratio: 9 / 16;
    background: var(--bg-secondary);
  }

  .pimage-preview img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
  }

  .pimage-aspect-ratio {
    position: absolute;
    top: 8px;
    right: 8px;
    background: rgba(0, 0, 0, 0.7);
    color: white;
    padding: 4px 8px;
    border-radius: var(--radius-sm);
    font-family: var(--font-sans);
    font-size: 0.75rem;
    font-weight: 600;
  }

  /* Pinterest Info */
  .pinterest-info {
    margin-top: 2rem;
    padding-top: 2rem;
    border-top: 1px solid var(--border-color);
  }

  .pinterest-info h3 {
    font-family: var(--font-sans);
    font-size: 1.125rem;
    font-weight: 600;
    margin-bottom: 1rem;
    color: var(--text-primary);
  }

  .pinterest-steps {
    list-style: none;
    counter-reset: step-counter;
    padding-left: 0;
  }

  .pinterest-steps li {
    counter-increment: step-counter;
    position: relative;
    padding-left: 2.5rem;
    margin-bottom: 1rem;
    font-family: var(--font-sans);
    font-size: 0.9375rem;
    color: var(--text-secondary);
    line-height: 1.6;
  }

  .pinterest-steps li::before {
    content: counter(step-counter);
    position: absolute;
    left: 0;
    top: 0;
    width: 1.75rem;
    height: 1.75rem;
    background: var(--bg-secondary);
    border: 2px solid var(--border-color);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.8125rem;
    font-weight: 600;
    color: var(--text-primary);
  }

  .pinterest-steps li code {
    background: var(--bg-tertiary);
    padding: 2px 6px;
    border-radius: var(--radius-sm);
    font-family: "Monaco", "Consolas", "Courier New", monospace;
    font-size: 0.875rem;
    color: var(--text-primary);
  }

  .pinterest-feed-url {
    margin-top: 1.5rem;
    padding: 1.25rem;
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-md);
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .pinterest-feed-url strong {
    font-family: var(--font-sans);
    font-size: 0.875rem;
    color: var(--text-primary);
  }

  .feed-url-code {
    background: var(--bg-primary);
    padding: 0.75rem;
    border-radius: var(--radius-sm);
    border: 1px solid var(--border-color);
    font-family: "Monaco", "Consolas", "Courier New", monospace;
    font-size: 0.8125rem;
    color: var(--text-primary);
    word-break: break-all;
  }

  .copy-btn {
    align-self: flex-start;
    margin-top: 0.5rem;
  }

  .pinterest-actions {
    margin-top: 2rem;
    padding-top: 1.5rem;
    border-top: 1px solid var(--border-color);
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    align-items: flex-start;
  }

  .btn-small {
    padding: 0.5rem 1rem;
    font-size: 0.875rem;
  }
</style>
