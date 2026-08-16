<script lang="ts">
  import { page } from "$app/stores";
  import { t, formatDate as fmtDate, formatMoney } from "$lib/i18n";

let { form } = $props();
  const lang = $derived($page.data.language || 'pt');
let accessType = $state(form?.values?.access_type || 'premium');
  let coverPreview = $state(form?.values?.cover_image || '');
  let uploading = $state(false);

  async function handleCoverUpload(e: Event) {
    const file = (e.target as HTMLInputElement).files?.[0];
    if (!file) return;
    uploading = true;
    const fd = new FormData();
    fd.append('file', file);
    try {
      const res = await fetch('/api/upload', { method: 'POST', body: fd });
      const json = await res.json();
      if (json.url) coverPreview = json.url;
    } finally { uploading = false; }
  }
</script>

<div class="form-page">
  <div class="form-header">
    <a href="/admin/courses" class="back-link">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 12H5M12 5l-7 7 7 7"/></svg>
      Voltar
    </a>
    <h1>{t(lang, "admin.courses.new")}</h1>
  </div>

  {#if form?.error}
    <div class="alert error">{form.error}</div>
  {/if}

  <form method="POST" class="course-form">
    <div class="form-grid">
      <div class="form-main">
        <div class="form-group">
          <label for="title">Título do Curso *</label>
          <input id="title" name="title" type="text" required placeholder="Ex: Marketing Digital para Iniciantes" value={form?.values?.title || ''} />
        </div>

        <div class="form-group">
          <label for="description">{t(lang, "admin.ui.description")}</label>
          <textarea id="description" name="description" rows="4" placeholder="Descreva o que o aluno vai aprender...">{form?.values?.description || ''}</textarea>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label for="access_type">Tipo de Acesso</label>
            <select id="access_type" name="access_type" bind:value={accessType}>
              <option value="free">Gratuito (qualquer membro)</option>
              <option value="premium">Premium (assinantes)</option>
              <option value="paid">Pago individualmente</option>
            </select>
          </div>

          {#if accessType === 'paid'}
            <div class="form-group">
              <label for="price">Preço (R$)</label>
              <input id="price" name="price" type="number" min="0" step="0.01" placeholder="0,00" value={form?.values?.price || ''} />
            </div>
          {:else}
            <input type="hidden" name="price" value="0" />
          {/if}
        </div>

        <div class="form-group">
          <label class="toggle-label">
            <input type="hidden" name="published" value="0" />
            <input type="checkbox" name="published" value="1" checked={form?.values?.published === '1'} />
            <span class="toggle-text">Publicar agora</span>
          </label>
        </div>
      </div>

      <div class="form-side">
        <div class="cover-section">
          <label class="section-label">Imagem de Capa</label>
          {#if coverPreview}
            <div class="cover-preview">
              <img src={coverPreview} alt="Capa do curso" />
              <button type="button" class="remove-cover" onclick={() => coverPreview = ''}>✕</button>
            </div>
          {:else}
            <label class="cover-upload" class:uploading>
              <input type="file" accept="image/*" onchange={handleCoverUpload} style="display:none" />
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>
              <span>{uploading ? 'Enviando...' : 'Clique para enviar'}</span>
            </label>
          {/if}
          <input type="hidden" name="cover_image" value={coverPreview} />
        </div>
      </div>
    </div>

    <div class="form-footer">
      <a href="/admin/courses" class="btn btn-secondary">{t(lang, "admin.ui.cancel")}</a>
      <button type="submit" class="btn btn-primary">Criar Curso</button>
    </div>
  </form>
</div>

<style>
  .form-page { max-width: 900px; }
  .form-header { margin-bottom: 2rem; }
  .back-link { display: inline-flex; align-items: center; gap: 0.5rem; color: var(--text-secondary); text-decoration: none; font-size: 0.875rem; margin-bottom: 1rem; }
  .back-link:hover { color: var(--text-primary); }
  h1 { font-size: 1.75rem; font-weight: 800; margin: 0; }
  .alert { padding: 0.875rem 1rem; border-radius: var(--radius-md); margin-bottom: 1.5rem; font-size: 0.9rem; }
  .error { background: #fef2f2; color: #dc2626; border: 1px solid #fee2e2; }
  .course-form { background: var(--bg-primary); border: 1px solid var(--border-light); border-radius: var(--radius-lg); padding: 2rem; }
  .form-grid { display: grid; grid-template-columns: 1fr 280px; gap: 2rem; }
  @media (max-width: 700px) { .form-grid { grid-template-columns: 1fr; } }
  .form-group { display: flex; flex-direction: column; gap: 0.5rem; margin-bottom: 1.25rem; }
  .form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
  label { font-size: 0.875rem; font-weight: 600; color: var(--text-secondary); }
  input[type="text"], input[type="number"], select, textarea {
    padding: 0.625rem 0.875rem; border: 1px solid var(--border-color);
    border-radius: var(--radius-md); font-size: 0.9rem; font-family: inherit;
    background: var(--bg-primary); color: var(--text-primary);
    transition: border-color 0.15s;
  }
  input:focus, select:focus, textarea:focus { outline: none; border-color: var(--text-primary); }
  textarea { resize: vertical; min-height: 100px; }
  .toggle-label { display: flex; align-items: center; gap: 0.75rem; cursor: pointer; }
  .toggle-label input[type="checkbox"] { width: 18px; height: 18px; cursor: pointer; }
  .toggle-text { font-size: 0.9rem; font-weight: 500; color: var(--text-primary); }
  .section-label { font-size: 0.875rem; font-weight: 600; color: var(--text-secondary); display: block; margin-bottom: 0.75rem; }
  .cover-upload {
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    gap: 0.75rem; padding: 2rem 1rem; border: 2px dashed var(--border-color);
    border-radius: var(--radius-lg); cursor: pointer; color: var(--text-muted);
    transition: all 0.2s; text-align: center; font-size: 0.875rem;
  }
  .cover-upload:hover, .cover-upload.uploading { border-color: var(--text-primary); color: var(--text-primary); }
  .cover-preview { position: relative; border-radius: var(--radius-lg); overflow: hidden; }
  .cover-preview img { width: 100%; aspect-ratio: 16/9; object-fit: cover; display: block; }
  .remove-cover {
    position: absolute; top: 0.5rem; right: 0.5rem; background: rgba(0,0,0,0.6);
    color: white; border: none; border-radius: 50%; width: 28px; height: 28px;
    cursor: pointer; font-size: 0.75rem; display: flex; align-items: center; justify-content: center;
  }
  .form-footer { display: flex; justify-content: flex-end; gap: 0.75rem; margin-top: 2rem; padding-top: 1.5rem; border-top: 1px solid var(--border-light); }
</style>
