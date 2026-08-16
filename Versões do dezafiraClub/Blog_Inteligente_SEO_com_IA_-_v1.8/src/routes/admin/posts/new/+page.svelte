<script lang="ts">
  import { page } from "$app/stores";
  import { t, formatMoney, adminErrorMessage } from "$lib/i18n";
  import { enhance } from "$app/forms";
  import type { Category } from "$lib/types";

  const lang = $derived($page.data.language || 'pt');

  let {
    data,
    form,
  }: {
    data: { categories: Category[]; products?: any[] };
    form?: {
      error?: string;
      title?: string;
      content?: string;
      excerpt?: string;
      published?: boolean;
      slug?: string;
      cover_image?: string;
      pinterest_enabled?: boolean;
      pinterest_image?: string;
      youtube_video_url?: string;
      tags?: string;
      is_18_plus?: boolean;
    };
  } = $props();
  let loading = $state(false);
  const formError = $derived(adminErrorMessage(lang, form?.error));
  let editorRef = $state<HTMLDivElement | null>(null);
  let showHtml = $state(false);
  let showYoutubeModal = $state(false);
  let youtubeUrl = $state("");
  let activeTab = $state<"general" | "pinterest">("general");
  let showPinterestModal = $state(false);
  let pinterestUrlInput = $state("");

  // Input states
  let titleValue = $state(form?.title || "");
  let htmlContent = $state(form?.content || "");
  let excerptValue = $state(form?.excerpt || "");
  let slugValue = $state(form?.slug || "");
  let coverImageValue = $state(form?.cover_image || "");
  let coverImagePreviewUrl = $state<string | null>(null);
  let coverImageFileName = $state<string | null>(null);
  let pinterestImageValue = $state(form?.pinterest_image || "");
  let youtubeVideoUrlValue = $state(form?.youtube_video_url || "");
  let tagsValue = $state(form?.tags || "");


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

  $effect(() => {
    const imported = sessionStorage.getItem("importedPost");
    if (imported && !form) {
      const data = JSON.parse(imported);
      titleValue = data.title;
      htmlContent = data.content;
      excerptValue = data.excerpt;
      coverImageValue = data.cover_image;

      // Clear after using
      sessionStorage.removeItem("importedPost");

      // If we are in visual mode, update the editor div
      if (editorRef && !showHtml) {
        editorRef.innerHTML = htmlContent;
      }
    }
  });

  let isInserting = $state(false);

  // Clean sensitive/messy HTML
  function cleanHtml(html: string): string {
    return html
      .replace(/<!--[\s\S]*?-->/g, "") // Remove comments
      .replace(/<p><br><\/p>\s*<p><br><\/p>/g, "<p><br></p>"); // Debounce multiple empty lines slightly? User complained about duplicates.
  }

  // Sync HTML content from contenteditable
  function syncContent() {
    if (editorRef) {
      // Clean comments and sync
      const raw = editorRef.innerHTML;
      const clean = cleanHtml(raw);
      if (raw !== clean) {
        // If we cleaned something meaningful (like removing comments), update DOM to be clean?
        // No, updating DOM resets cursor. Just save clean version to state.
        // But then visual editor still has garbage comments?
        // If we remove {@html}, Svelte won't inject comments anymore!
        // So just saving clean is enough.
      }
      htmlContent = clean;
    }
  }

  // Action to initialize editor content without Svelte reactivity loop
  function editorAction(node: HTMLElement) {
    node.innerHTML = htmlContent;
    return {
      update(newContent: string) {
        // Only update if significantly different (e.g. external change)
        // For now, we trust internal updates don't need flowing back
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
    const url = prompt(t(lang, "admin.posts.prompt_link_url"));
    if (url) {
      execCommand("createLink", url);
    }
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
      alert(t(lang, "admin.posts.invalid_youtube"));
      return;
    }

    isInserting = true;

    // Button to delete the embed (only visible in editor via CSS)
    const deleteBtn = `<button type="button" class="delete-embed-btn" contenteditable="false" title="${t(lang, "admin.posts.remove_video")}">❌</button>`;
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

  function applyPinterestImage() {
    pinterestImageValue = pinterestUrlInput;
    closePinterestModal();
  }

  function toggleHtmlView() {
    if (showHtml && editorRef) {
      // Switching from HTML to visual - update editor (editorRef is bound to div when !showHtml)
      // Wait, when showHtml is true, editorRef (div) might not exist or be hidden?
      // With if block, it is destroyed.
      // So when we toggle showHtml = false, the div is mounted, and editorAction runs.
      // So we just need to ensure htmlContent is up to date.
    } else if (editorRef) {
      // Switching from visual to HTML - sync content first
      // cleanHtml not strictly necessary here as syncContent does it, but purely for safety
      htmlContent = cleanHtml(editorRef.innerHTML);
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
</script>

<svelte:head>
  <title>Admin | {t(lang, "admin.posts.create_title")}</title>
</svelte:head>

<div class="editor-page">
  <div class="editor-header">
    <h1>{t(lang, "admin.posts.create_title")}</h1>
    <div class="header-actions">
      <a href="/admin/posts" class="btn">{t(lang, "admin.ui.cancel")}</a>
    </div>
  </div>

  {#if formError}
    <div class="message message-error">{formError}</div>
  {/if}

  <form
    method="POST"
    enctype="multipart/form-data"
    use:enhance={({ formData }) => {
      // Garantir sincronização do estado
      syncContent();
      
      // Obter o título diretamente do DOM para evitar atrasos de reatividade do Svelte 5
      const titleInput = document.querySelector('input[name="title"]') as HTMLInputElement;
      const finalTitle = titleInput ? titleInput.value : titleValue;
      formData.set('title', finalTitle);

      // Obter o conteúdo diretamente do DOM (seja do editor visual ou do textarea HTML)
      let finalContent = '';
      if (showHtml) {
        const textarea = document.querySelector('.html-textarea') as HTMLTextAreaElement;
        finalContent = textarea ? textarea.value : htmlContent;
      } else if (editorRef) {
        finalContent = cleanHtml(editorRef.innerHTML);
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
    <div class="editor-layout">
      <div class="editor-main">
        <!-- Title Input -->
        <div class="title-input-wrapper">
          <input
            type="text"
            id="title"
            name="title"
            class="title-input"
            bind:value={titleValue}
            required
            placeholder={t(lang, "admin.posts.title_placeholder")}
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
                title={t(lang, "admin.posts.bold")}
              >
                <strong>B</strong>
              </button>
              <button
                type="button"
                class="toolbar-btn"
                onclick={formatItalic}
                title={t(lang, "admin.posts.italic")}
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
                title={t(lang, "admin.posts.heading_2")}
              >
                H2
              </button>
              <button
                type="button"
                class="toolbar-btn"
                onclick={formatH3}
                title={t(lang, "admin.posts.heading_3")}
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
                title={t(lang, "admin.posts.paragraph")}
              >
                ¶
              </button>
              <button
                type="button"
                class="toolbar-btn"
                onclick={formatList}
                title={t(lang, "admin.posts.list")}
              >
                ☰
              </button>
              <button
                type="button"
                class="toolbar-btn"
                onclick={formatBlockquote}
                title={t(lang, "admin.posts.quote")}
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
                title={t(lang, "admin.posts.link")}
              >
                🔗
              </button>
              <button
                type="button"
                class="toolbar-btn youtube-btn"
                onclick={openYoutubeModal}
                title={t(lang, "admin.posts.insert_youtube")}
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
                title={t(lang, "admin.posts.toggle_html")}
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
              placeholder={t(lang, "admin.posts.html_placeholder")}
            ></textarea>
          {:else}
            <div
              bind:this={editorRef}
              use:editorAction
              class="visual-editor article-content"
              contenteditable="true"
              oninput={syncContent}
              onclick={handleEditorClick}
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
              role="textbox"
              aria-multiline="true"
              data-placeholder={t(lang, "admin.posts.editor_placeholder")}
              tabindex="0"
            ></div>
          {/if}

          <!-- Hidden input to submit content -->
          <input type="hidden" name="content" value={htmlContent} />
        </div>
      </div>

      <div class="editor-sidebar">
        <div class="sidebar-card">
          <h3>{t(lang, "admin.posts.publication")}</h3>
          <div class="publish-options">
            <label class="checkbox-label">
              <input
                type="checkbox"
                name="published"
                checked={form?.published || false}
              />
              <span>{t(lang, "admin.posts.publish_now")}</span>
            </label>
            <label class="checkbox-label">
              <input
                type="checkbox"
                name="is_18_plus"
                checked={form?.is_18_plus || false}
              />
              <span>{t(lang, "admin.posts.is_18")}</span>
            </label>
          </div>
          <button
            type="submit"
            class="btn btn-primary publish-btn"
            disabled={loading}
          >
            {loading ? t(lang, "admin.ui.saving") : t(lang, "admin.posts.publish")}
          </button>
        </div>

        <div class="sidebar-card">
          <h3>{t(lang, "admin.posts.post_url")}</h3>
          <div class="form-group">
            <input
              type="text"
              id="slug"
              name="slug"
              class="form-input"
              bind:value={slugValue}
              placeholder={t(lang, "admin.posts.slug_placeholder")}
            />
            <small class="hint">{t(lang, "admin.posts.slug_hint")}</small>
          </div>
        </div>

        <div class="sidebar-card">
          <h3>{t(lang, "admin.posts.cover_image")}</h3>
          <div class="form-group">
            <input
              type="text"
              id="cover_image"
              name="cover_image"
              class="form-input"
              bind:value={coverImageValue}
              placeholder={t(lang, "admin.posts.cover_url_placeholder")}
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
              <label for="cover_image_file" class="btn btn-small">{t(lang, "admin.posts.choose_file")}</label>
              {#if coverImageFileName}
                <span class="file-name" title={coverImageFileName}>{coverImageFileName}</span>
              {/if}
            </div>
            {#if coverImagePreviewUrl}
              <div class="cover-preview">
                <img src={coverImagePreviewUrl} alt={t(lang, "admin.posts.preview")} />
              </div>
            {:else if coverImageValue}
              <div class="cover-preview">
                <img src={coverImageValue} alt={t(lang, "admin.posts.preview")} />
              </div>
            {/if}
            <small class="hint">{t(lang, "admin.posts.cover_hint")}</small>
          </div>
        </div>

        <div class="sidebar-card">
          <h3>{t(lang, "admin.posts.featured_video")}</h3>
          <div class="form-group">
            <input
              type="url"
              id="youtube_video_url"
              name="youtube_video_url"
              class="form-input"
              bind:value={youtubeVideoUrlValue}
              placeholder={t(lang, "admin.posts.youtube_url_placeholder")}
            />
            <small class="hint">{t(lang, "admin.posts.featured_video_hint")}</small>
          </div>
        </div>

        <div class="sidebar-card">
          <h3>{t(lang, "admin.posts.excerpt")}</h3>
          <div class="form-group">
            <textarea
              id="excerpt"
              name="excerpt"
              class="form-textarea excerpt-textarea"
              rows="4"
              placeholder={t(lang, "admin.posts.excerpt_placeholder")}
              bind:value={excerptValue}
            ></textarea>
          </div>
        </div>

        <div class="sidebar-card">
          <h3>{t(lang, "admin.posts.tags")}</h3>
          <div class="form-group">
            <input
              type="text"
              id="tags"
              name="tags"
              class="form-input"
              placeholder={t(lang, "admin.posts.tags_placeholder")}
              bind:value={tagsValue}
            />
            <small class="hint">{t(lang, "admin.posts.tags_hint")}</small>
          </div>
        </div>

        {#if data.categories && data.categories.length > 0}
          <div class="sidebar-card">
            <h3>{t(lang, "admin.posts.categories")}</h3>
            <div class="categories-checkboxes">
              {#each data.categories as category}
                <label class="checkbox-label">
                  <input
                    type="checkbox"
                    name="categories"
                    value={category.id}
                  />
                  <span>{category.name}</span>
                </label>
              {/each}
            </div>
          </div>
        {/if}

        {#if data.products && data.products.length > 0}
          <div class="sidebar-card">
            <h3>{t(lang, "admin.posts.products_attached")}</h3>
            <div class="categories-checkboxes">
              {#each data.products as product}
                <label class="checkbox-label">
                  <input
                    type="checkbox"
                    name="products"
                    value={product.id}
                  />
                  <span>
                    {product.name}
                    ({product.price_cents === 0
                      ? t(lang, "admin.posts.free")
                      : formatMoney(lang, product.price_cents)})
                  </span>
                </label>
              {/each}
            </div>
          </div>
        {/if}
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
    <div
      class="modal"
      role="presentation"
      onclick={(e) => e.stopPropagation()}
      onkeydown={(e) => e.stopPropagation()}
    >
      <div class="modal-header">
        <h2>{t(lang, "admin.posts.insert_youtube_title")}</h2>
        <button type="button" class="modal-close" onclick={closeYoutubeModal}
          >✕</button
        >
      </div>
      <div class="modal-body">
        <div class="form-group">
          <label for="youtube-url" class="form-label">{t(lang, "admin.posts.youtube_url_label")}</label>
          <input
            type="text"
            id="youtube-url"
            class="form-input"
            bind:value={youtubeUrl}
            placeholder={t(lang, "admin.posts.youtube_url_placeholder")}
          />
          <small class="hint">{t(lang, "admin.posts.youtube_formats")}</small>
        </div>
      </div>
      <div class="modal-footer">
        <button type="button" class="btn" onclick={closeYoutubeModal}
          >{t(lang, "admin.ui.cancel")}</button
        >
        <button type="button" class="btn btn-primary" onclick={insertYoutube}
          >{t(lang, "admin.posts.insert_video")}</button
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

  .file-picker-row {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-top: 0.75rem;
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
    font-family: var(--font-sans);
    font-size: 0.75rem;
    color: var(--text-muted);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    max-width: 180px;
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
</style>
