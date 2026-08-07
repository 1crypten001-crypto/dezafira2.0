<script lang="ts">
  import { t, formatDate as formatDateI18n, adminErrorMessage } from "$lib/i18n";
  import { enhance } from "$app/forms";
  import { goto } from "$app/navigation";
  import { page } from "$app/stores";

  let { data, form } = $props();
  const lang = $derived($page.data.language || 'pt');

  const formError = $derived(adminErrorMessage(lang, form?.error));
  const formSuccessMsg = $derived.by(() => {
    if (!form?.success) return '';
    if (form.message === 'NL_DELETE_SUCCESS') return t(lang, 'admin.newsletter.errors.delete_success');
    if (form.message === 'NL_CAMPAIGN_SENT') {
      return t(lang, 'admin.newsletter.errors.campaign_sent', {
        subject: form.subject || '',
        n: String(form.count ?? 0)
      });
    }
    return adminErrorMessage(lang, form.message) || t(lang, 'admin.newsletter.success_generic');
  });

  let searchInput = $state(data.searchQuery || "");
  let activeTab = $state("subscribers"); // "subscribers" | "campaigns"
  
  let isModalOpen = $state(false);
  let campaignSubject = $state("");
  let campaignContent = $state("");
  let campaignYoutubeUrl = $state("");
  let isSending = $state(false);

  let sendToMode = $state("all"); // "all" | "selected"
  let selectedEmails = $state<string[]>([]);
  let emailSearchQuery = $state("");
  
  let mobileViewMode = $state("editor"); // "editor" | "preview"
  
  let editorRef = $state<HTMLDivElement | null>(null);

  function handleSearch(e: Event) {
    e.preventDefault();
    goto(`?q=${encodeURIComponent(searchInput)}`);
  }

  function formatDate(dateString: string) {
    return formatDateI18n(lang, dateString, {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }

  function handleDelete(event: Event) {
    if (!confirm(t(lang, 'admin.newsletter.confirm_delete_sub'))) {
      event.preventDefault();
    }
  }

  function openModal() {
    isModalOpen = true;
    mobileViewMode = "editor";
    campaignSubject = "";
    campaignContent = "<p><br></p>";
    campaignYoutubeUrl = "";
    sendToMode = "all";
    selectedEmails = data.activeEmails ? [...data.activeEmails] : [];
    emailSearchQuery = "";
  }

  function closeModal() {
    isModalOpen = false;
  }

  // Regex para ID do YouTube
  function getYouTubeId(url: string): string | null {
    if (!url) return null;
    const regExp = /^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|\&v=|shorts\/)([^#\&\?]*).*/;
    const match = url.match(regExp);
    return (match && match[2].length === 11) ? match[2] : null;
  }

  // Sincroniza o conteúdo do editor contenteditable com a variável campaignContent
  function syncContent() {
    if (editorRef) {
      campaignContent = editorRef.innerHTML;
    }
  }

  // Comando de formatação do editor
  function execCommand(command: string, value: string | null = null) {
    document.execCommand(command, false, value ?? undefined);
    editorRef?.focus();
    syncContent();
  }

  function formatBold() { execCommand("bold"); }
  function formatItalic() { execCommand("italic"); }
  function formatH2() { execCommand("formatBlock", "h2"); }
  function formatH3() { execCommand("formatBlock", "h3"); }
  function formatParagraph() { execCommand("formatBlock", "p"); }
  
  function formatList(ordered: boolean) {
    execCommand(ordered ? "insertOrderedList" : "insertUnorderedList");
  }

  // Estados para inserção de link customizado
  let showLinkInput = $state(false);
  let linkUrl = $state("https://");
  let savedSelection = $state<Range | null>(null);

  // Estados para upload de imagem
  let isUploadingImage = $state(false);
  let fileInputRef = $state<HTMLInputElement | null>(null);

  function saveSelection() {
    const sel = window.getSelection();
    if (sel && sel.rangeCount > 0) {
      savedSelection = sel.getRangeAt(0).cloneRange();
    }
  }

  function restoreSelection() {
    if (savedSelection) {
      const sel = window.getSelection();
      if (sel) {
        sel.removeAllRanges();
        sel.addRange(savedSelection);
      }
    }
  }

  function toggleLinkInput() {
    if (showLinkInput) {
      showLinkInput = false;
    } else {
      saveSelection();
      showLinkInput = true;
      // focar input após renderizar
      setTimeout(() => {
        const input = document.getElementById("link-input-field") as HTMLInputElement;
        input?.focus();
        input?.select();
      }, 50);
    }
  }

  function applyLink(e: Event) {
    e.preventDefault();
    restoreSelection();
    if (linkUrl && linkUrl !== "https://") {
      execCommand("createLink", linkUrl);
    }
    showLinkInput = false;
    linkUrl = "https://";
  }

  function cancelLink() {
    showLinkInput = false;
    linkUrl = "https://";
  }

  function triggerImageUpload() {
    saveSelection();
    fileInputRef?.click();
  }

  async function handleImageUpload(e: Event) {
    const input = e.target as HTMLInputElement;
    if (!input.files || input.files.length === 0) return;

    const file = input.files[0];
    isUploadingImage = true;

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch("/api/upload", {
        method: "POST",
        body: formData
      });

      if (!res.ok) {
        throw new Error(t(lang, "admin.newsletter.upload_fail"));
      }

      const responseData = await res.json();
      const imageUrl = responseData.url;

      restoreSelection();
      
      if (!savedSelection && editorRef) {
        editorRef.focus();
      }

      const imgHtml = `<p><img src="${imageUrl}" width="100%" style="max-width:100%; height:auto; border-radius:8px; display:block; margin: 16px auto;" alt="" /></p><p><br></p>`;
      execCommand("insertHTML", imgHtml);
    } catch (err: any) {
      console.error(err);
      alert(err.message || t(lang, "admin.newsletter.upload_fail"));
    } finally {
      isUploadingImage = false;
      input.value = "";
    }
  }

  // Lista filtrada de assinantes ativos com base na busca dentro do modal
  const filteredActiveEmails = $derived(() => {
    if (!data.activeEmails) return [];
    if (!emailSearchQuery) return data.activeEmails;
    const query = emailSearchQuery.toLowerCase();
    return data.activeEmails.filter((email: string) => email.toLowerCase().includes(query));
  });

  function selectAllEmails() {
    selectedEmails = data.activeEmails ? [...data.activeEmails] : [];
  }

  function deselectAllEmails() {
    selectedEmails = [];
  }

  function toggleEmailSelection(email: string) {
    if (selectedEmails.includes(email)) {
      selectedEmails = selectedEmails.filter(e => e !== email);
    } else {
      selectedEmails = [...selectedEmails, email];
    }
  }

  const youtubeId = $derived(getYouTubeId(campaignYoutubeUrl));
</script>

<svelte:head>
  <title>{t(lang, "admin.newsletter.title")} & {t(lang, "admin.newsletter.campaigns")}</title>
</svelte:head>

<div class="admin-header-row">
  <div>
    <h1 class="admin-title">{t(lang, "admin.newsletter.manager_title")}</h1>
    <p class="admin-subtitle">{t(lang, "admin.newsletter.subtitle")}</p>
  </div>
  
  <div class="header-actions">
    {#if data.resendReady}
      <button class="btn btn-primary" onclick={openModal}>
        ✉️ {t(lang, "admin.newsletter.new_campaign")}
      </button>
    {:else}
      <a href="/admin/settings" class="btn btn-secondary" style="border-color: #eab308; color: #d97706;">
        ⚠️ {t(lang, "admin.newsletter.configure_resend")}
      </a>
    {/if}
  </div>
</div>

<div class="stats-grid">
  <div class="stat-card">
    <div class="stat-icon">👥</div>
    <div class="stat-details">
      <span class="stat-label">{t(lang, "admin.newsletter.active_subs")}</span>
      <span class="stat-value">{data.activeCount}</span>
    </div>
  </div>
  <div class="stat-card">
    <div class="stat-icon">📨</div>
    <div class="stat-details">
      <span class="stat-label">{t(lang, "admin.newsletter.campaigns_sent")}</span>
      <span class="stat-value">{data.total || 0}</span>
    </div>
  </div>
  <div class="stat-card">
    <div class="stat-icon">⚙️</div>
    <div class="stat-details">
      <span class="stat-label">{t(lang, "admin.newsletter.resend_integration")}</span>
      <span class="stat-value" class:configured={data.resendReady}>
        {data.resendReady ? t(lang, "admin.newsletter.status_active") : t(lang, "admin.newsletter.status_pending")}
      </span>
    </div>
  </div>
</div>

{#if formError}
  <div class="alert error">{formError}</div>
{/if}

{#if form?.success}
  <div class="alert success">{formSuccessMsg}</div>
{/if}

<div class="tabs-container">
  <button 
    class="tab-btn" 
    class:active={activeTab === 'subscribers'} 
    onclick={() => activeTab = 'subscribers'}
  >
    {t(lang, "admin.newsletter.tab_subscribers")}
  </button>
  <button 
    class="tab-btn" 
    class:active={activeTab === 'campaigns'} 
    onclick={() => activeTab = 'campaigns'}
  >
    {t(lang, "admin.newsletter.tab_campaigns")}
  </button>
</div>

{#if activeTab === 'subscribers'}
  <div class="search-bar-wrapper">
    <form class="search-form" onsubmit={handleSearch}>
      <input 
        type="text" 
        bind:value={searchInput} 
        placeholder={t(lang, "admin.newsletter.search_placeholder")} 
        class="search-input"
      />
      <button type="submit" class="btn btn-search">{t(lang, "admin.ui.search")}</button>
      {#if data.searchQuery}
        <a href="/admin/newsletter" class="btn btn-secondary">{t(lang, "admin.newsletter.clear")}</a>
      {/if}
    </form>
  </div>

  <div class="admin-table-container">
    <table class="table">
      <thead>
        <tr>
          <th>{t(lang, "admin.newsletter.col_id")}</th>
          <th>{t(lang, "admin.ui.email")}</th>
          <th>{t(lang, "admin.ui.name")}</th>
          <th>{t(lang, "admin.newsletter.col_subscribed_at")}</th>
          <th>{t(lang, "admin.ui.status")}</th>
          <th>{t(lang, "admin.ui.actions")}</th>
        </tr>
      </thead>
      <tbody>
        {#if data.subscribers.length === 0}
          <tr>
            <td colspan="6" class="text-center py-4">{data.searchQuery ? t(lang, "admin.newsletter.empty_search") : t(lang, "admin.newsletter.empty_subs")}</td>
          </tr>
        {/if}
        {#each data.subscribers as sub}
          <tr>
            <td>{sub.id}</td>
            <td><strong>{sub.email}</strong></td>
            <td>{sub.name || '-'}</td>
            <td>{formatDate(sub.created_at)}</td>
            <td>
              <span class="status status-{sub.status === 'active' ? 'published' : 'draft'}">
                {sub.status === 'active' ? t(lang, "admin.newsletter.status_sub_active") : t(lang, "admin.newsletter.status_sub_inactive")}
              </span>
            </td>
            <td>
              <form action="?/delete" method="POST" use:enhance>
                <input type="hidden" name="id" value={sub.id} />
                <button type="submit" class="btn btn-small btn-danger" onclick={handleDelete}>
                  {t(lang, "admin.ui.delete")}
                </button>
              </form>
            </td>
          </tr>
        {/each}
      </tbody>
    </table>
  </div>

  {#if data.totalPages > 1}
    <div class="pagination">
      {#if data.page > 1}
        <a href="?page={data.page - 1}{data.searchQuery ? `&q=${data.searchQuery}` : ''}" class="btn">
          {t(lang, "admin.newsletter.previous")}
        </a>
      {/if}
      
      <span class="page-info">{t(lang, "admin.newsletter.page_of", { current: String(data.page), total: String(data.totalPages) })}</span>
      
      {#if data.page < data.totalPages}
        <a href="?page={data.page + 1}{data.searchQuery ? `&q=${data.searchQuery}` : ''}" class="btn">
          {t(lang, "admin.newsletter.next")}
        </a>
      {/if}
    </div>
  {/if}
{/if}

{#if activeTab === 'campaigns'}
  <div class="admin-table-container">
    <table class="table">
      <thead>
        <tr>
          <th>{t(lang, "admin.newsletter.col_id")}</th>
          <th>{t(lang, "admin.newsletter.col_campaign_subject")}</th>
          <th>{t(lang, "admin.newsletter.col_video")}</th>
          <th>{t(lang, "admin.newsletter.col_recipients")}</th>
          <th>{t(lang, "admin.newsletter.col_sent_at")}</th>
        </tr>
      </thead>
      <tbody>
        {#if !data.campaigns || data.campaigns.length === 0}
          <tr>
            <td colspan="5" class="text-center py-4">{t(lang, "admin.newsletter.empty_campaigns")}</td>
          </tr>
        {/if}
        {#if data.campaigns}
          {#each data.campaigns as campaign}
            <tr>
              <td>{campaign.id}</td>
              <td><strong>{campaign.subject}</strong></td>
              <td>
                {#if campaign.youtube_video_url}
                  <a href={campaign.youtube_video_url} target="_blank" class="yt-badge">
                    📺 YouTube
                  </a>
                {:else}
                  <span class="no-video">-</span>
                {/if}
              </td>
              <td>{t(lang, "admin.newsletter.recipients_count", { n: String(campaign.recipients_count) })}</td>
              <td>{formatDate(campaign.sent_at)}</td>
            </tr>
          {/each}
        {/if}
      </tbody>
    </table>
  </div>
  
  {#if data.totalPages > 1}
    <div class="pagination">
      {#if data.campaignPage > 1}
        <a href="?cpage={data.campaignPage - 1}" class="btn">
          {t(lang, "admin.newsletter.previous")}
        </a>
      {/if}
      
      <span class="page-info">{t(lang, "admin.newsletter.page_of", { current: String(data.campaignPage || 1), total: String(data.totalPages) })}</span>
      
      {#if data.campaignPage < data.totalPages}
        <a href="?cpage={(data.campaignPage || 1) + 1}" class="btn">
          {t(lang, "admin.newsletter.next")}
        </a>
      {/if}
    </div>
  {/if}
{/if}

<!-- Modal para Nova Campanha (Mobile First & WYSIWYG) -->
{#if isModalOpen}
  <div class="modal-backdrop" onclick={closeModal}>
    <div class="modal-card" onclick={(e) => e.stopPropagation()}>
      <div class="modal-header">
        <h2>{t(lang, "admin.newsletter.modal_title")}</h2>
        <button class="modal-close-btn" onclick={closeModal}>&times;</button>
      </div>
      
      <div class="mobile-view-tabs">
        <button 
          type="button" 
          class="mview-btn" 
          class:active={mobileViewMode === 'editor'} 
          onclick={() => mobileViewMode = 'editor'}
        >
          📝 {t(lang, "admin.newsletter.editor")}
        </button>
        <button 
          type="button" 
          class="mview-btn" 
          class:active={mobileViewMode === 'preview'} 
          onclick={() => mobileViewMode = 'preview'}
        >
          👁️ {t(lang, "admin.newsletter.preview")}
        </button>
      </div>
      
      <form 
        action="?/sendCampaign" 
        method="POST" 
        use:enhance={() => {
          isSending = true;
          return async ({ update }) => {
            isSending = false;
            closeModal();
            await update();
          };
        }}
      >
        <!-- Envia o HTML gerado pelo contenteditable -->
        <input type="hidden" name="content" value={campaignContent} />
        <input type="hidden" name="send_to" value={sendToMode} />
        <input type="hidden" name="selected_emails" value={selectedEmails.join(',')} />

        <div class="modal-body-split">
          <!-- Form do Editor -->
          <div class="editor-side" class:hidden-mobile={mobileViewMode !== 'editor'}>
            <div class="form-group">
              <label class="form-label text-bold">{t(lang, "admin.newsletter.send_to")}</label>
              <div class="radio-group-horizontal">
                <label class="radio-label">
                  <input type="radio" name="send_to_selector" value="all" bind:group={sendToMode} />
                  <span>{t(lang, "admin.newsletter.send_to_all", { n: String(data.activeCount) })}</span>
                </label>
                <label class="radio-label">
                  <input type="radio" name="send_to_selector" value="selected" bind:group={sendToMode} />
                  <span>{t(lang, "admin.newsletter.send_to_manual", { n: String(selectedEmails.length) })}</span>
                </label>
              </div>
            </div>

            {#if sendToMode === 'selected'}
              <div class="form-group active-subscribers-selector-box">
                <div class="selector-actions-row">
                  <input 
                    type="text" 
                    placeholder={t(lang, "admin.newsletter.filter_emails")} 
                    bind:value={emailSearchQuery} 
                    class="email-filter-input"
                  />
                  <div class="select-quick-actions">
                    <button type="button" onclick={selectAllEmails}>{t(lang, "admin.newsletter.select_all")}</button>
                    <button type="button" onclick={deselectAllEmails}>{t(lang, "admin.newsletter.deselect_all")}</button>
                  </div>
                </div>

                <div class="emails-selection-list">
                  {#if filteredActiveEmails().length === 0}
                    <p class="no-emails-msg">{t(lang, "admin.newsletter.no_email_match")}</p>
                  {:else}
                    {#each filteredActiveEmails() as email}
                      <label class="checkbox-email-row">
                        <input 
                          type="checkbox" 
                          value={email} 
                          checked={selectedEmails.includes(email)} 
                          onchange={() => toggleEmailSelection(email)}
                        />
                        <span>{email}</span>
                      </label>
                    {/each}
                  {/if}
                </div>
              </div>
            {/if}

            <div class="form-group">
              <label for="subject" class="form-label">{t(lang, "admin.newsletter.email_subject")}</label>
              <input 
                type="text" 
                id="subject" 
                name="subject" 
                required 
                bind:value={campaignSubject}
                placeholder={t(lang, "admin.newsletter.subject_ph")} 
                class="form-input"
              />
            </div>
            
            <div class="form-group">
              <label for="youtube_video_url" class="form-label">{t(lang, "admin.newsletter.youtube_optional")}</label>
              <input 
                type="url" 
                id="youtube_video_url" 
                name="youtube_video_url" 
                bind:value={campaignYoutubeUrl}
                placeholder="https://www.youtube.com/watch?v=..." 
                class="form-input"
              />
              <small class="field-hint">{t(lang, "admin.newsletter.youtube_hint")}</small>
            </div>
            
            <div class="form-group">
                            <!-- Input oculto para selecionar imagem do dispositivo -->
              <input 
                type="file" 
                bind:this={fileInputRef} 
                accept="image/*" 
                onchange={handleImageUpload} 
                style="display:none" 
              />

              <div class="rich-editor-container">
                <!-- Barra de ferramentas (Toolbar estilo WordPress) -->
                <div class="rich-toolbar">
                  <button type="button" onclick={formatBold} title={t(lang, "admin.newsletter.bold")}><b>B</b></button>
                  <button type="button" onclick={formatItalic} title={t(lang, "admin.newsletter.italic")}><i>I</i></button>
                  <button type="button" onclick={formatH2} title={t(lang, "admin.newsletter.heading_2")}>H2</button>
                  <button type="button" onclick={formatH3} title={t(lang, "admin.newsletter.heading_3")}>H3</button>
                  <button type="button" onclick={formatParagraph} title={t(lang, "admin.newsletter.paragraph")}>P</button>
                  <button type="button" onclick={() => formatList(false)} title={t(lang, "admin.newsletter.bullet_list")}>• List</button>
                  <button type="button" onclick={() => formatList(true)} title={t(lang, "admin.newsletter.numbered_list")}>1. List</button>
                  <button type="button" onclick={toggleLinkInput} class:active={showLinkInput} title={t(lang, "admin.newsletter.add_link")}>🔗 Link</button>
                  <button type="button" onclick={triggerImageUpload} disabled={isUploadingImage} title={t(lang, "admin.newsletter.add_image")}>
                    {isUploadingImage ? `⌛ ${t(lang, "admin.newsletter.uploading")}` : `🖼️ ${t(lang, "admin.newsletter.image")}`}
                  </button>
                </div>

                {#if showLinkInput}
                  <div class="link-popover-panel">
                    <form onsubmit={applyLink}>
                      <input 
                        type="url" 
                        id="link-input-field" 
                        bind:value={linkUrl} 
                        placeholder={t(lang, "admin.newsletter.link_url_ph")} 
                        required
                        class="link-popover-input"
                      />
                      <button type="submit" class="btn-link-apply">{t(lang, "admin.newsletter.insert")}</button>
                      <button type="button" class="btn-link-cancel" onclick={cancelLink}>{t(lang, "admin.ui.cancel")}</button>
                    </form>
                  </div>
                {/if}
                
                <!-- Área editável WYSIWYG -->
                <div 
                  bind:this={editorRef}
                  contenteditable="true"
                  class="visual-editor-area"
                  oninput={syncContent}
                  role="textbox"
                  tabindex="0"
                >
                  <p><br></p>
                </div>
              </div>
            </div>
          </div>
          
          <div class="preview-side" class:hidden-mobile={mobileViewMode !== 'preview'}>
            <h3>{t(lang, "admin.newsletter.live_preview")}</h3>
            <div class="email-sandbox">
              <div class="email-header">
                <span class="site-logo">{data.siteTitle}</span>
              </div>
              <div class="email-body">
                <h2 class="email-title">{campaignSubject || t(lang, "admin.newsletter.subject_preview")}</h2>
                <div class="email-text">
                  {@html campaignContent || `<p style="color:#a0a0a0">${t(lang, "admin.newsletter.content_placeholder")}</p>`}
                </div>
                
                {#if youtubeId}
                  <div class="youtube-preview-card">
                    <img src="https://img.youtube.com/vi/{youtubeId}/mqdefault.jpg" alt="" />
                    <div class="play-overlay">
                      <span class="play-icon">▶</span>
                      {t(lang, "admin.newsletter.watch_youtube")}
                    </div>
                  </div>
                {/if}
              </div>
              <div class="email-footer">
                <p>{t(lang, "admin.newsletter.email_footer")}</p>
                <p><a href="#">{t(lang, "admin.newsletter.unsubscribe")}</a></p>
                <p>© {data.siteTitle} — {data.siteUrl.replace(/^https?:\/\//, '')}</p>
              </div>
            </div>
          </div>
        </div>
        
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" onclick={closeModal}>{t(lang, "admin.ui.cancel")}</button>
          <button 
            type="submit" 
            class="btn btn-send" 
            disabled={isSending}
            onclick={(e) => {
              const count = sendToMode === 'all' ? data.activeCount : selectedEmails.length;
              if (count === 0) {
                alert(t(lang, 'admin.newsletter.select_subs'));
                e.preventDefault();
                return;
              }
              const msgKey = sendToMode === 'all'
                ? 'admin.newsletter.confirm_send_all'
                : 'admin.newsletter.confirm_send_selected';
              if (!confirm(t(lang, msgKey, { n: String(count) }))) {
                e.preventDefault();
              }
            }}
          >
            {isSending
              ? t(lang, "admin.newsletter.dispatching")
              : t(lang, "admin.newsletter.dispatch_to", {
                  n: String(sendToMode === 'all' ? data.activeCount : selectedEmails.length)
                })}
          </button>
        </div>
      </form>
    </div>
  </div>
{/if}

<style>
  /* Global Fonts */
  :global(.modal-backdrop), :global(.modal-card), :global(.btn), :global(.form-input), :global(.visual-editor-area) {
    font-family: var(--font-sans), system-ui, -apple-system, sans-serif !important;
  }

  /* Gerenciador Header e Grid de Stats */
  .admin-header-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 2rem;
    flex-wrap: wrap;
    gap: 1rem;
  }
  .admin-subtitle {
    margin: 0.25rem 0 0 0;
    color: var(--text-muted);
    font-size: 0.95rem;
  }
  
  .stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 1.5rem;
    margin-bottom: 2.5rem;
  }
  .stat-card {
    background: var(--bg-primary);
    border: 1px solid var(--border-light);
    border-radius: var(--radius-lg);
    padding: 1.25rem 1.5rem;
    display: flex;
    align-items: center;
    gap: 1rem;
    box-shadow: var(--shadow-xs);
  }
  .stat-icon {
    font-size: 1.75rem;
    background: var(--bg-secondary);
    width: 48px;
    height: 48px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 1px solid var(--border-light);
  }
  .stat-details {
    display: flex;
    flex-direction: column;
  }
  .stat-label {
    font-size: 0.8rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
  .stat-value {
    font-size: 1.35rem;
    font-weight: 700;
    color: var(--text-primary);
  }
  .stat-value.configured {
    color: #10b981;
  }
  
  /* Abas */
  .tabs-container {
    display: flex;
    gap: 0.5rem;
    border-bottom: 1px solid var(--border-light);
    margin-bottom: 1.5rem;
  }
  .tab-btn {
    background: transparent;
    border: none;
    border-bottom: 2px solid transparent;
    padding: 0.75rem 1.25rem;
    font-family: var(--font-sans);
    font-size: 0.95rem;
    font-weight: 600;
    color: var(--text-muted);
    cursor: pointer;
    transition: all 0.2s ease;
  }
  .tab-btn:hover {
    color: var(--text-primary);
  }
  .tab-btn.active {
    color: var(--accent-color, #3b82f6);
    border-bottom-color: var(--accent-color, #3b82f6);
  }

  /* Barra de Busca */
  .search-bar-wrapper {
    margin-bottom: 1.25rem;
  }
  .search-form {
    display: flex;
    gap: 0.5rem;
  }
  .search-input {
    padding: 0.6rem 1.25rem;
    border: 1px solid var(--border-light);
    border-radius: var(--radius-md);
    background: var(--bg-secondary);
    color: var(--text-primary);
    width: 100%;
    max-width: 320px;
    font-size: 0.9rem;
  }
  .btn-search {
    background: var(--text-primary);
    color: var(--bg-primary);
  }
  .btn-search:hover {
    opacity: 0.9;
  }

  /* Tabelas */
  .admin-table-container {
    background: var(--bg-primary);
    border: 1px solid var(--border-light);
    border-radius: var(--radius-lg);
    overflow-x: auto;
    width: 100%;
    margin-bottom: 2rem;
    box-shadow: var(--shadow-xs);
  }
  .table th {
    background: var(--bg-secondary);
    color: var(--text-muted);
    font-weight: 600;
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
  .table td {
    padding: 1rem 1.25rem;
    font-size: 0.9rem;
    border-bottom: 1px solid var(--border-light);
  }
  .yt-badge {
    display: inline-block;
    padding: 0.25rem 0.6rem;
    background: #fef2f2;
    color: #ef4444;
    border: 1px solid #fee2e2;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 700;
    text-decoration: none;
  }
  .yt-badge:hover {
    background: #ef4444;
    color: #ffffff;
  }
  .no-video {
    color: var(--text-muted);
    opacity: 0.5;
  }

  /* Statuses */
  .status {
    display: inline-block;
    padding: 0.25rem 0.6rem;
    font-family: var(--font-sans);
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    border-radius: var(--radius-sm);
  }
  .status-published {
    background: #d1fae5;
    color: #065f46;
  }
  .status-draft {
    background: #fee2e2;
    color: #991b1b;
  }
  
  .btn-danger {
    border-color: #ef4444;
    color: #ef4444;
    background: transparent;
  }
  .btn-danger:hover {
    background: #ef4444;
    color: white;
  }
  
  /* Modal Overlay */
  .modal-backdrop {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background: rgba(0, 0, 0, 0.45);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
    backdrop-filter: blur(4px);
  }
  .modal-card {
    background: var(--bg-primary);
    border: 1px solid var(--border-light);
    border-radius: var(--radius-xl);
    width: 92%;
    max-width: 1050px;
    max-height: 90vh;
    display: flex;
    flex-direction: column;
    box-shadow: var(--shadow-xl);
    overflow: hidden;
  }
  .modal-header {
    padding: 1.25rem 1.75rem;
    border-bottom: 1px solid var(--border-light);
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: var(--bg-secondary);
  }
  .modal-header h2 {
    font-size: 1.25rem;
    font-weight: 700;
    margin: 0;
    color: var(--text-primary);
  }
  .modal-close-btn {
    background: transparent;
    border: none;
    font-size: 1.75rem;
    color: var(--text-muted);
    cursor: pointer;
    line-height: 1;
  }
  .modal-close-btn:hover {
    color: var(--text-primary);
  }

  /* Alternador de abas mobile */
  .mobile-view-tabs {
    display: none;
    border-bottom: 1px solid var(--border-light);
    background: var(--bg-secondary);
  }
  .mview-btn {
    flex: 1;
    background: transparent;
    border: none;
    padding: 0.85rem 1rem;
    font-size: 0.9rem;
    font-weight: 600;
    color: var(--text-muted);
    cursor: pointer;
    border-bottom: 2px solid transparent;
    transition: all 0.2s;
  }
  .mview-btn.active {
    color: var(--text-primary);
    border-bottom-color: var(--text-primary);
    background: var(--bg-primary);
  }
  
  .modal-body-split {
    padding: 1.75rem;
    display: grid;
    grid-template-columns: 1.2fr 1fr;
    gap: 2rem;
    overflow-y: auto;
    max-height: 60vh;
  }
  
  /* Editor Side */
  .editor-side {
    display: flex;
    flex-direction: column;
    gap: 1.25rem;
  }
  .form-group {
    display: flex;
    flex-direction: column;
  }
  .form-label {
    font-size: 0.85rem;
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 0.35rem;
    display: block;
  }
  .form-input {
    width: 100%;
    padding: 0.75rem 1rem;
    border: 1px solid var(--border-light);
    border-radius: var(--radius-md);
    background: var(--bg-secondary);
    color: var(--text-primary);
    font-size: 0.95rem;
    box-sizing: border-box;
  }
  
  /* Rich WYSIWYG Editor */
  .rich-editor-container {
    border: 1px solid var(--border-light);
    border-radius: var(--radius-md);
    overflow: hidden;
    background: var(--bg-primary);
  }
  .rich-toolbar {
    background: var(--bg-secondary);
    border-bottom: 1px solid var(--border-light);
    padding: 0.5rem;
    display: flex;
    flex-wrap: wrap;
    gap: 0.25rem;
  }
  .rich-toolbar button {
    background: var(--bg-primary);
    border: 1px solid var(--border-light);
    border-radius: var(--radius-sm);
    color: var(--text-primary);
    padding: 0.35rem 0.65rem;
    font-size: 0.8rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.15s ease;
  }
  .rich-toolbar button:hover {
    background: var(--text-primary);
    color: var(--bg-primary);
    border-color: var(--text-primary);
  }
  .rich-toolbar button.active {
    background: var(--text-primary);
    color: var(--bg-primary);
    border-color: var(--text-primary);
  }

  /* Link Popover Panel */
  .link-popover-panel {
    background: var(--bg-secondary);
    border-bottom: 1px solid var(--border-light);
    padding: 0.75rem 1rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    box-sizing: border-box;
  }
  .link-popover-panel form {
    display: flex;
    width: 100%;
    gap: 0.5rem;
  }
  .link-popover-input {
    flex: 1;
    padding: 0.4rem 0.75rem;
    border: 1px solid var(--border-light);
    border-radius: var(--radius-sm);
    background: var(--bg-primary);
    color: var(--text-primary);
    font-size: 0.85rem;
    outline: none;
  }
  .btn-link-apply {
    background: var(--text-primary, #111827);
    color: var(--bg-primary, #ffffff);
    border: 1px solid var(--text-primary, #111827);
    border-radius: var(--radius-sm);
    padding: 0.4rem 0.85rem;
    font-size: 0.8rem;
    font-weight: 600;
    cursor: pointer;
  }
  .btn-link-apply:hover {
    opacity: 0.9;
  }
  .btn-link-cancel {
    background: transparent;
    color: var(--text-muted);
    border: 1px solid var(--border-light);
    border-radius: var(--radius-sm);
    padding: 0.4rem 0.85rem;
    font-size: 0.8rem;
    font-weight: 600;
    cursor: pointer;
  }
  .btn-link-cancel:hover {
    background: var(--bg-secondary);
    color: var(--text-primary);
  }

  .visual-editor-area {
    min-height: 250px;
    max-height: 400px;
    overflow-y: auto;
    padding: 1rem;
    background: var(--bg-primary);
    color: var(--text-primary);
    font-size: 0.95rem;
    line-height: 1.6;
    outline: none;
    box-sizing: border-box;
  }
  .visual-editor-area :global(img) {
    max-width: 100% !important;
    height: auto !important;
    border-radius: 8px;
  }
  .visual-editor-area :global(p) {
    margin: 0 0 1rem 0;
  }
  .visual-editor-area :global(a) {
    color: var(--accent-color, #3b82f6);
    text-decoration: underline;
  }
  .visual-editor-area :global(h2), .visual-editor-area :global(h3) {
    font-weight: 700;
    margin: 1.5rem 0 1rem 0;
  }
  .visual-editor-area :global(ul), .visual-editor-area :global(ol) {
    padding-left: 1.5rem;
    margin: 0 0 1rem 0;
  }
  .visual-editor-area :global(blockquote) {
    border-left: 3px solid var(--border-dark, #374151);
    padding-left: 1rem;
    margin: 1.5rem 0;
    font-style: italic;
    color: var(--text-muted);
  }

  .field-hint {
    font-size: 0.75rem;
    color: var(--text-muted);
    margin-top: 0.25rem;
    display: block;
  }

  /* Preview Side */
  .preview-side {
    display: flex;
    flex-direction: column;
  }
  .preview-side h3 {
    margin: 0 0 0.75rem 0;
    font-size: 0.85rem;
    font-weight: 700;
    text-transform: uppercase;
    color: var(--text-muted);
    letter-spacing: 0.5px;
  }
  .email-sandbox {
    border: 1px solid #e8e8e8;
    background: #ffffff;
    border-radius: 8px;
    padding: 20px;
    overflow-y: auto;
    height: 380px;
    box-shadow: inset 0 2px 8px rgba(0,0,0,0.03);
  }
  
  /* Layout do E-mail Simulado no Preview */
  .email-header {
    border-bottom: 1px solid #f0f0f0;
    padding-bottom: 12px;
    margin-bottom: 18px;
    text-align: center;
  }
  .site-logo {
    font-family: sans-serif;
    font-size: 16px;
    font-weight: 800;
    color: #111111;
  }
  .email-body {
    font-family: sans-serif;
  }
  .email-title {
    font-size: 18px;
    color: #111111;
    font-weight: 700;
    margin: 0 0 14px 0;
  }
  .email-text {
    color: #444444;
    font-size: 14px;
    line-height: 1.5;
  }
  .email-text :global(img) {
    max-width: 100% !important;
    height: auto !important;
    border-radius: 8px;
  }
  .email-text :global(p) {
    margin: 0 0 12px 0;
  }
  .email-text :global(a) {
    color: #3b82f6;
    text-decoration: underline;
  }
  .email-text :global(h2), .email-text :global(h3) {
    margin: 1.25rem 0 0.75rem 0;
  }
  .email-text :global(ul), .email-text :global(ol) {
    padding-left: 1.25rem;
    margin: 0 0 12px 0;
  }
  .email-text :global(blockquote) {
    border-left: 3px solid #666;
    padding-left: 10px;
    margin: 15px 0;
    font-style: italic;
    color: #666;
  }
  .email-footer {
    border-top: 1px solid #f0f0f0;
    padding-top: 15px;
    margin-top: 25px;
    text-align: center;
    color: #999999;
    font-size: 11px;
    line-height: 1.4;
  }
  .email-footer a {
    color: #666666;
    text-decoration: underline;
  }
  
  /* Card do YouTube no Preview */
  .youtube-preview-card {
    margin: 18px 0;
    border: 1px solid #e8e8e8;
    border-radius: 8px;
    overflow: hidden;
    position: relative;
    background: #000000;
    aspect-ratio: 16/9;
  }
  .youtube-preview-card img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    opacity: 0.65;
  }
  .play-overlay {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    background: rgba(239, 68, 68, 0.95);
    color: #ffffff;
    padding: 8px 16px;
    border-radius: 6px;
    font-weight: 700;
    font-size: 11px;
    text-transform: uppercase;
    display: flex;
    align-items: center;
    gap: 6px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  }
  .play-icon {
    font-size: 10px;
  }
  
  .modal-footer {
    padding: 1.25rem 1.75rem;
    border-top: 1px solid var(--border-light);
    display: flex;
    justify-content: flex-end;
    gap: 0.75rem;
    background: var(--bg-secondary);
  }
  
  /* Black button like dashboard style */
  .btn-send {
    background: var(--text-primary, #111827);
    color: var(--bg-primary, #ffffff);
    border: 1px solid var(--text-primary, #111827);
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
  }
  .btn-send:hover {
    background: var(--text-secondary, #374151);
    border-color: var(--text-secondary, #374151);
    opacity: 0.9;
  }
  
  /* Seletor de Destinatários */
  .radio-group-horizontal {
    display: flex;
    gap: 1.5rem;
    margin: 0.25rem 0 0.5rem 0;
  }
  .radio-label {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.9rem;
    font-weight: 500;
    color: var(--text-primary);
    cursor: pointer;
  }
  .radio-label input[type="radio"] {
    cursor: pointer;
  }
  .active-subscribers-selector-box {
    border: 1px solid var(--border-light);
    border-radius: var(--radius-md);
    padding: 1rem;
    background: var(--bg-secondary);
    margin-bottom: 1rem;
    box-sizing: border-box;
  }
  .selector-actions-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 1rem;
    margin-bottom: 0.75rem;
    flex-wrap: wrap;
  }
  .email-filter-input {
    flex: 1;
    min-width: 150px;
    padding: 0.4rem 0.75rem;
    border: 1px solid var(--border-light);
    border-radius: var(--radius-sm);
    background: var(--bg-primary);
    color: var(--text-primary);
    font-size: 0.85rem;
    outline: none;
  }
  .select-quick-actions {
    display: flex;
    gap: 0.35rem;
  }
  .select-quick-actions button {
    background: var(--bg-primary);
    border: 1px solid var(--border-light);
    border-radius: var(--radius-sm);
    color: var(--text-primary);
    padding: 0.35rem 0.65rem;
    font-size: 0.75rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.15s ease;
  }
  .select-quick-actions button:hover {
    background: var(--text-primary);
    color: var(--bg-primary);
    border-color: var(--text-primary);
  }
  .emails-selection-list {
    max-height: 160px;
    overflow-y: auto;
    background: var(--bg-primary);
    border: 1px solid var(--border-light);
    border-radius: var(--radius-sm);
    padding: 0.5rem;
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    box-sizing: border-box;
  }
  .checkbox-email-row {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.35rem 0.5rem;
    border-radius: var(--radius-sm);
    cursor: pointer;
    font-size: 0.85rem;
    color: var(--text-primary);
    transition: background 0.15s;
    box-sizing: border-box;
  }
  .checkbox-email-row:hover {
    background: var(--bg-secondary);
  }
  .checkbox-email-row input[type="checkbox"] {
    cursor: pointer;
  }
  .no-emails-msg {
    font-size: 0.85rem;
    color: var(--text-muted);
    text-align: center;
    padding: 1rem 0;
    margin: 0;
  }
  .text-bold {
    font-weight: 700;
  }
  
  /* Mobile First Adjustments */
  @media (max-width: 820px) {
    .modal-card {
      width: 100%;
      height: 100%;
      max-height: 100vh;
      border-radius: 0;
    }
    .mobile-view-tabs {
      display: flex;
    }
    .modal-body-split {
      grid-template-columns: 1fr;
      max-height: calc(100vh - 180px);
      padding: 1.25rem;
    }
    .hidden-mobile {
      display: none !important;
    }
    .modal-footer {
      position: absolute;
      bottom: 0;
      left: 0;
      width: 100%;
      box-sizing: border-box;
    }
    .preview-side {
      margin-top: 1.5rem;
      border-top: 1px dashed var(--border-light);
      padding-top: 1.5rem;
    }
  }
</style>

