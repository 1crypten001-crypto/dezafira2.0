<script lang="ts">
  import { page } from "$app/stores";
  import { t, formatDate as fmtDate, formatMoney } from "$lib/i18n";
  import { enhance } from '$app/forms';

  let { data, form } = $props();
  const lang = $derived($page.data.language || 'pt');
let accessType = $state(data.course.access_type || 'premium');
  let coverPreview = $state(data.course.cover_image || '');
  let uploading = $state(false);
  let editingLessonId = $state<number | null>(null);
  let showAddLesson = $state(false);
  let showAddMaterial = $state(false);
  let matUploading = $state(false);
  let matFileUrl = $state('');

  async function handleCoverUpload(e: Event) {
    const file = (e.target as HTMLInputElement).files?.[0];
    if (!file) return;
    uploading = true;
    const fd = new FormData(); fd.append('file', file);
    try {
      const res = await fetch('/api/upload', { method: 'POST', body: fd });
      const json = await res.json();
      if (json.url) coverPreview = json.url;
    } finally { uploading = false; }
  }

  async function handleMaterialUpload(e: Event) {
    const file = (e.target as HTMLInputElement).files?.[0];
    if (!file) return;
    matUploading = true;
    const fd = new FormData(); fd.append('file', file);
    try {
      const res = await fetch('/api/upload', { method: 'POST', body: fd });
      const json = await res.json();
      if (json.url) matFileUrl = json.url;
    } finally { matUploading = false; }
  }

  function toggleEdit(lessonId: number) {
    editingLessonId = editingLessonId === lessonId ? null : lessonId;
  }
</script>

<div class="edit-page">
  <div class="page-header">
    <a href="/admin/courses" class="back-link">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 12H5M12 5l-7 7 7 7"/></svg>
      Cursos
    </a>
    <div class="header-actions">
      <a href="/members/area/{data.course.slug}" target="_blank" class="btn btn-secondary btn-sm">Ver página</a>
      <form method="POST" action="?/deleteCourse" use:enhance>
        <button type="submit" class="btn btn-danger btn-sm"
          onclick={(e) => { if (!confirm(t(lang, 'admin.courses.confirm_delete_course'))) e.preventDefault(); }}>
          Excluir Curso
        </button>
      </form>
    </div>
  </div>

  <!-- ── DADOS DO CURSO ──────────────────────────────── -->
  <section class="section">
    <h2>Dados do Curso</h2>
    {#if form?.courseError}<div class="alert error">{form.courseError}</div>{/if}
    {#if form?.courseSuccess}<div class="alert success">{form.courseSuccess}</div>{/if}

    <form method="POST" action="?/updateCourse" use:enhance class="course-form">
      <div class="form-grid">
        <div class="form-main">
          <div class="form-group">
            <label for="title">Título *</label>
            <input id="title" name="title" type="text" required value={data.course.title} />
          </div>
          <div class="form-group">
            <label for="description">{t(lang, "admin.ui.description")}</label>
            <textarea id="description" name="description" rows="3">{data.course.description || ''}</textarea>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label for="access_type">Tipo de Acesso</label>
              <select id="access_type" name="access_type" bind:value={accessType}>
                <option value="free">Gratuito</option>
                <option value="premium">Premium</option>
                <option value="paid">Pago individualmente</option>
              </select>
            </div>
            {#if accessType === 'paid'}
              <div class="form-group">
                <label for="price">Preço (R$)</label>
                <input id="price" name="price" type="number" min="0" step="0.01" value={(data.course.price_cents / 100).toFixed(2)} />
              </div>
            {:else}
              <input type="hidden" name="price" value="0" />
            {/if}
          </div>
          <div class="form-group">
            <label class="toggle-label">
              <input type="hidden" name="published" value="0" />
              <input type="checkbox" name="published" value="1" checked={data.course.published === 1} />
              <span>Publicado</span>
            </label>
          </div>
        </div>
        <div class="form-side">
          <div class="section-label">Imagem de Capa</div>
          {#if coverPreview}
            <div class="cover-preview">
              <img src={coverPreview} alt="Capa" />
              <button type="button" class="remove-cover" onclick={() => coverPreview = ''}>✕</button>
            </div>
          {:else}
            <label class="cover-upload" class:uploading>
              <input type="file" accept="image/*" onchange={handleCoverUpload} style="display:none" />
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>
              <span>{uploading ? 'Enviando...' : 'Enviar imagem'}</span>
            </label>
          {/if}
          <input type="hidden" name="cover_image" value={coverPreview} />
        </div>
      </div>
      <div class="form-footer">
        <button type="submit" class="btn btn-primary">Salvar Curso</button>
      </div>
    </form>
  </section>

  <!-- ── AULAS ──────────────────────────────────────── -->
  <section class="section">
    <div class="section-header">
      <h2>Aulas ({data.lessons.length})</h2>
      <button type="button" class="btn btn-primary btn-sm"
        onclick={() => { showAddLesson = !showAddLesson; editingLessonId = null; }}>
        {showAddLesson ? 'Cancelar' : '+ Nova Aula'}
      </button>
    </div>

    {#if form?.lessonError}<div class="alert error">{form.lessonError}</div>{/if}
    {#if form?.lessonSuccess}<div class="alert success">{form.lessonSuccess}</div>{/if}

    <!-- Formulário de nova aula (inline expandido) -->
    {#if showAddLesson}
      <div class="lesson-form-box">
        <div class="lesson-form-title">Nova Aula</div>
        <form method="POST" action="?/addLesson"
          use:enhance={() => { return async ({ update }) => { showAddLesson = false; await update(); }; }}>

          <div class="form-group">
            <label>Título da Aula *</label>
            <input name="title" type="text" required placeholder="Ex: Introdução ao módulo" />
          </div>

          <div class="form-group">
            <label>Tópico / Módulo <span class="hint">(opcional — agrupa aulas em seções)</span></label>
            <input name="topic" type="text" placeholder="Ex: Módulo 1 - Fundamentos" />
          </div>

          <div class="form-row">
            <div class="form-group">
              <label>URL do Vídeo</label>
              <input name="video_url" type="text" placeholder="https://youtu.be/... ou https://vimeo.com/..." />
            </div>
            <div class="form-group">
              <label>Plataforma</label>
              <select name="video_type">
                <option value="youtube">YouTube</option>
                <option value="vimeo">Vimeo</option>
              </select>
            </div>
          </div>

          <div class="form-group">
            <label>Conteúdo / Descrição (HTML)</label>
            <textarea name="content" rows="4" placeholder="Texto da aula, links, instruções..."></textarea>
          </div>

          <div class="form-row-checks">
            <label class="toggle-label">
              <input type="hidden" name="published" value="0" />
              <input type="checkbox" name="published" value="1" checked />
              <span>Publicada</span>
            </label>
            <label class="toggle-label">
              <input type="hidden" name="is_preview" value="0" />
              <input type="checkbox" name="is_preview" value="1" />
              <span>Preview gratuito</span>
            </label>
          </div>

          <div class="form-footer">
            <button type="button" class="btn btn-secondary btn-sm" onclick={() => showAddLesson = false}>{t(lang, "admin.ui.cancel")}</button>
            <button type="submit" class="btn btn-primary btn-sm">Adicionar Aula</button>
          </div>
        </form>
      </div>
    {/if}

    <!-- Lista de aulas -->
    <div class="lessons-list">
      {#each data.lessons as lesson, idx}
        <div class="lesson-item" class:editing={editingLessonId === lesson.id}>

          <!-- Cabeçalho da aula (clicável) -->
          <div class="lesson-info" onclick={() => toggleEdit(lesson.id)} role="button" tabindex="0"
            onkeydown={(e) => e.key === 'Enter' && toggleEdit(lesson.id)}>
            <div class="lesson-drag">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="9" cy="5" r="1"/><circle cx="9" cy="12" r="1"/><circle cx="9" cy="19" r="1"/>
                <circle cx="15" cy="5" r="1"/><circle cx="15" cy="12" r="1"/><circle cx="15" cy="19" r="1"/>
              </svg>
            </div>
            <div class="lesson-meta">
              <span class="lesson-num">{idx + 1}</span>
              {#if lesson.topic}<span class="lesson-topic">{lesson.topic}</span>{/if}
              <span class="lesson-title">{lesson.title}</span>
              {#if lesson.video_url}<span class="lesson-badge video">▶ Vídeo</span>{/if}
              {#if lesson.is_preview}<span class="lesson-badge preview">Preview</span>{/if}
              {#if !lesson.published}<span class="lesson-badge draft">Rascunho</span>{/if}
            </div>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
              class="expand-icon" class:rotated={editingLessonId === lesson.id}>
              <path d="M6 9l6 6 6-6"/>
            </svg>
          </div>

          <!-- Formulário de edição (inline) -->
          {#if editingLessonId === lesson.id}
            <div class="lesson-form-box lesson-form-box--inline">
              <form method="POST" action="?/updateLesson"
                use:enhance={() => { return async ({ update }) => { editingLessonId = null; await update(); }; }}>
                <input type="hidden" name="lesson_id" value={lesson.id} />
                <input type="hidden" name="sort_order" value={lesson.sort_order} />

                <div class="form-group">
                  <label>Título da Aula *</label>
                  <input name="title" type="text" required value={lesson.title} />
                </div>

                <div class="form-group">
                  <label>Tópico / Módulo <span class="hint">(agrupa aulas em seções)</span></label>
                  <input name="topic" type="text" placeholder="Ex: Módulo 1 - Fundamentos" value={lesson.topic || ''} />
                </div>

                <div class="form-row">
                  <div class="form-group">
                    <label>URL do Vídeo</label>
                    <input name="video_url" type="text" placeholder="https://youtu.be/..." value={lesson.video_url || ''} />
                  </div>
                  <div class="form-group">
                    <label>Plataforma</label>
                    <select name="video_type">
                      <option value="youtube" selected={!lesson.video_type || lesson.video_type === 'youtube'}>YouTube</option>
                      <option value="vimeo" selected={lesson.video_type === 'vimeo'}>Vimeo</option>
                    </select>
                  </div>
                </div>

                <div class="form-group">
                  <label>Conteúdo / Descrição (HTML)</label>
                  <textarea name="content" rows="4">{lesson.content || ''}</textarea>
                </div>

                <div class="form-row-checks">
                  <label class="toggle-label">
                    <input type="hidden" name="published" value="0" />
                    <input type="checkbox" name="published" value="1" checked={lesson.published === 1} />
                    <span>Publicada</span>
                  </label>
                  <label class="toggle-label">
                    <input type="hidden" name="is_preview" value="0" />
                    <input type="checkbox" name="is_preview" value="1" checked={lesson.is_preview === 1} />
                    <span>Preview gratuito</span>
                  </label>
                </div>

                <div class="form-footer">
                  <button type="submit" formaction="?/deleteLesson" class="btn btn-danger btn-sm"
                    onclick={(e) => { if (!confirm(t(lang, 'admin.courses.confirm_delete_lesson'))) e.preventDefault(); }}>{t(lang, "admin.ui.delete")}</button>
                  <button type="button" class="btn btn-secondary btn-sm" onclick={() => editingLessonId = null}>{t(lang, "admin.ui.cancel")}</button>
                  <button type="submit" class="btn btn-primary btn-sm">Salvar Aula</button>
                </div>
              </form>
            </div>
          {/if}
        </div>
      {/each}

      {#if data.lessons.length === 0 && !showAddLesson}
        <div class="empty-lessons">Nenhuma aula criada ainda. Clique em "+ Nova Aula" para começar.</div>
      {/if}
    </div>
  </section>

  <!-- ── MATERIAIS ──────────────────────────────────── -->
  <section class="section">
    <div class="section-header">
      <h2>Materiais ({data.materials.length})</h2>
      <button type="button" class="btn btn-primary btn-sm" onclick={() => showAddMaterial = !showAddMaterial}>
        {showAddMaterial ? 'Cancelar' : '+ Adicionar Material'}
      </button>
    </div>

    {#if form?.materialError}<div class="alert error">{form.materialError}</div>{/if}
    {#if form?.materialSuccess}<div class="alert success">{form.materialSuccess}</div>{/if}

    {#if showAddMaterial}
      <div class="lesson-form-box">
        <form method="POST" action="?/addMaterial"
          use:enhance={() => { return async ({ update }) => { showAddMaterial = false; matFileUrl = ''; await update(); }; }}>
          <div class="form-group">
            <label for="mat_title">Título do Material *</label>
            <input id="mat_title" name="title" type="text" required placeholder="Ex: Apostila PDF - Módulo 1" />
          </div>
          <div class="form-group">
            <label for="mat_desc">{t(lang, "admin.ui.description")}</label>
            <input id="mat_desc" name="description" type="text" placeholder="Opcional" />
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>Arquivo</label>
              {#if matFileUrl}
                <div class="mat-file-preview">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                  Arquivo carregado
                  <button type="button" onclick={() => matFileUrl = ''} class="remove-mat">✕</button>
                </div>
              {:else}
                <label class="cover-upload" class:uploading={matUploading}>
                  <input type="file" onchange={handleMaterialUpload} style="display:none" />
                  <span>{matUploading ? 'Enviando...' : 'Clique para enviar arquivo'}</span>
                </label>
              {/if}
              <input type="hidden" name="file_url" value={matFileUrl} />
            </div>
            <div class="form-group">
              <label for="file_type">{t(lang, "admin.ui.type")}</label>
              <select id="file_type" name="file_type">
                <option value="pdf">PDF</option>
                <option value="zip">ZIP</option>
                <option value="image">Imagem</option>
                <option value="video">Vídeo</option>
                <option value="other">Outro</option>
              </select>
            </div>
          </div>
          <div class="form-footer">
            <button type="button" class="btn btn-secondary btn-sm" onclick={() => showAddMaterial = false}>{t(lang, "admin.ui.cancel")}</button>
            <button type="submit" class="btn btn-primary btn-sm">{t(lang, "admin.ui.add")}</button>
          </div>
        </form>
      </div>
    {/if}

    <div class="materials-list">
      {#each data.materials as mat}
        <div class="material-item">
          <div class="mat-icon">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
          </div>
          <div class="mat-info">
            <span class="mat-title">{mat.title}</span>
            {#if mat.description}<span class="mat-desc">{mat.description}</span>{/if}
          </div>
          <span class="mat-type">{mat.file_type || 'arquivo'}</span>
          <form method="POST" action="?/deleteMaterial" use:enhance>
            <input type="hidden" name="material_id" value={mat.id} />
            <button type="submit" class="btn-icon-danger"
              onclick={(e) => { if (!confirm(t(lang, 'admin.courses.confirm_delete_material'))) e.preventDefault(); }}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/><path d="M10 11v6M14 11v6"/><path d="M9 6V4h6v2"/></svg>
            </button>
          </form>
        </div>
      {/each}
      {#if data.materials.length === 0 && !showAddMaterial}
        <div class="empty-lessons">Nenhum material adicionado.</div>
      {/if}
    </div>
  </section>
</div>

<style>
  .edit-page { max-width: 900px; }
  .page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; gap: 1rem; }
  .header-actions { display: flex; gap: 0.75rem; align-items: center; }
  .back-link { display: inline-flex; align-items: center; gap: 0.5rem; color: var(--text-secondary); text-decoration: none; font-size: 0.875rem; }
  .back-link:hover { color: var(--text-primary); }

  .section { background: var(--bg-primary); border: 1px solid var(--border-light); border-radius: var(--radius-lg); padding: 1.75rem; margin-bottom: 1.5rem; }
  .section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; }
  h2 { font-size: 1.1rem; font-weight: 700; margin: 0 0 1.5rem; }
  .section-header h2 { margin: 0; }

  .alert { padding: 0.75rem 1rem; border-radius: var(--radius-md); margin-bottom: 1rem; font-size: 0.875rem; }
  .error { background: #fef2f2; color: #dc2626; border: 1px solid #fee2e2; }
  .success { background: #ecfdf5; color: #059669; border: 1px solid #d1fae5; }

  .form-grid { display: grid; grid-template-columns: 1fr 240px; gap: 1.5rem; }
  @media (max-width: 650px) { .form-grid { grid-template-columns: 1fr; } }
  .form-group { display: flex; flex-direction: column; gap: 0.4rem; margin-bottom: 1rem; }
  .form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
  .form-row-checks { display: flex; gap: 1.5rem; margin-bottom: 1rem; }
  label { font-size: 0.8rem; font-weight: 600; color: var(--text-secondary); }
  .hint { font-weight: 400; color: var(--text-muted); font-size: 0.75rem; }
  input[type="text"], input[type="number"], select, textarea {
    padding: 0.55rem 0.75rem; border: 1px solid var(--border-color);
    border-radius: var(--radius-md); font-size: 0.875rem; font-family: inherit;
    background: var(--bg-primary); color: var(--text-primary);
  }
  input:focus, select:focus, textarea:focus { outline: none; border-color: var(--text-primary); }
  textarea { resize: vertical; }
  .toggle-label { display: flex; align-items: center; gap: 0.5rem; cursor: pointer; font-size: 0.875rem; font-weight: 500; color: var(--text-primary); }

  .section-label { font-size: 0.8rem; font-weight: 600; color: var(--text-secondary); display: block; margin-bottom: 0.5rem; }
  .cover-upload {
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    gap: 0.5rem; padding: 1.5rem 1rem; border: 2px dashed var(--border-color);
    border-radius: var(--radius-md); cursor: pointer; color: var(--text-muted);
    font-size: 0.8rem; text-align: center;
  }
  .cover-upload:hover, .cover-upload.uploading { border-color: var(--text-primary); }
  .cover-preview { position: relative; border-radius: var(--radius-md); overflow: hidden; }
  .cover-preview img { width: 100%; aspect-ratio: 16/9; object-fit: cover; display: block; }
  .remove-cover {
    position: absolute; top: 0.4rem; right: 0.4rem; background: rgba(0,0,0,0.6);
    color: white; border: none; border-radius: 50%; width: 24px; height: 24px;
    cursor: pointer; font-size: 0.7rem; display: flex; align-items: center; justify-content: center;
  }

  .form-footer { display: flex; justify-content: flex-end; gap: 0.75rem; margin-top: 1.25rem; padding-top: 1.25rem; border-top: 1px solid var(--border-light); align-items: center; }

  .btn-sm { padding: 0.4rem 0.875rem; font-size: 0.8rem; border-radius: 8px; }
  .btn-danger { background: #fef2f2; color: #ef4444; border: 1px solid #fee2e2; cursor: pointer; font-family: inherit; text-decoration: none; display: inline-flex; align-items: center; }
  .btn-danger:hover { background: #fee2e2; }

  /* Lessons */
  .lessons-list { display: flex; flex-direction: column; gap: 0.5rem; }
  .lesson-item { border: 1px solid var(--border-light); border-radius: var(--radius-md); overflow: hidden; transition: box-shadow 0.15s; }
  .lesson-item.editing { border-color: var(--text-primary); box-shadow: 0 0 0 2px rgba(0,0,0,0.08); }
  .lesson-info {
    display: flex; align-items: center; gap: 0.75rem; padding: 0.875rem 1rem;
    cursor: pointer; transition: background 0.15s;
  }
  .lesson-info:hover { background: var(--bg-secondary); }
  .lesson-drag { color: var(--text-muted); flex-shrink: 0; }
  .lesson-meta { display: flex; align-items: center; gap: 0.5rem; flex: 1; flex-wrap: wrap; }
  .lesson-num { font-size: 0.75rem; font-weight: 700; color: var(--text-muted); min-width: 20px; }
  .lesson-topic { font-size: 0.7rem; font-weight: 700; color: var(--text-muted); background: var(--bg-tertiary); padding: 0.15rem 0.5rem; border-radius: 4px; }
  .lesson-title { font-size: 0.9rem; font-weight: 600; color: var(--text-primary); }
  .lesson-badge {
    font-size: 0.65rem; font-weight: 700; padding: 0.15rem 0.5rem;
    border-radius: 4px; text-transform: uppercase; letter-spacing: 0.3px;
  }
  .lesson-badge.video { background: #e0f2fe; color: #0369a1; }
  .lesson-badge.preview { background: #d1fae5; color: #065f46; }
  .lesson-badge.draft { background: #fef3c7; color: #92400e; }
  .expand-icon { color: var(--text-muted); transition: transform 0.2s; flex-shrink: 0; }
  .expand-icon.rotated { transform: rotate(180deg); }

  .lesson-form-box {
    padding: 1.25rem 1.5rem; background: var(--bg-secondary);
    border-top: 1px solid var(--border-light);
  }
  .lesson-form-box--inline { border-top: 1px solid var(--border-light); }
  .lesson-form-title { font-size: 0.85rem; font-weight: 700; color: var(--text-primary); margin-bottom: 1rem; }
  /* Standalone add form has a border too */
  .section > .lesson-form-box {
    border: 1px solid var(--border-color); border-radius: var(--radius-md);
    margin-bottom: 1rem;
  }

  .empty-lessons { padding: 1.5rem; text-align: center; color: var(--text-muted); font-size: 0.875rem; }

  /* Materials */
  .materials-list { display: flex; flex-direction: column; gap: 0.5rem; }
  .material-item {
    display: flex; align-items: center; gap: 0.75rem; padding: 0.875rem 1rem;
    border: 1px solid var(--border-light); border-radius: var(--radius-md);
  }
  .mat-icon { color: var(--text-muted); flex-shrink: 0; }
  .mat-info { flex: 1; display: flex; flex-direction: column; gap: 0.1rem; }
  .mat-title { font-size: 0.875rem; font-weight: 600; color: var(--text-primary); }
  .mat-desc { font-size: 0.75rem; color: var(--text-muted); }
  .mat-type { font-size: 0.7rem; font-weight: 700; text-transform: uppercase; color: var(--text-muted); background: var(--bg-tertiary); padding: 0.2rem 0.5rem; border-radius: 4px; }
  .mat-file-preview { display: flex; align-items: center; gap: 0.5rem; padding: 0.5rem 0.75rem; background: var(--bg-tertiary); border-radius: var(--radius-md); font-size: 0.875rem; }
  .remove-mat { background: none; border: none; cursor: pointer; color: var(--text-muted); margin-left: auto; }
  .btn-icon-danger { background: none; border: none; cursor: pointer; color: #ef4444; padding: 0.25rem; display: flex; align-items: center; }
  .btn-icon-danger:hover { color: #b91c1c; }
</style>
