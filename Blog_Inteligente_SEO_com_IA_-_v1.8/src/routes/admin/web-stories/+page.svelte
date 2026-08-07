<script lang="ts">
  import { enhance } from '$app/forms';
  import { page } from '$app/stores';
  import { t } from '$lib/i18n';

  let { data, form }: { data: any; form: any } = $props();
  const lang = $derived(($page.data.language as string) || 'pt');

  type SlideState = {
    title: string;
    body: string;
    background_image: string;
    cta_url: string;
    cta_text: string;
  };

  function slidesFromData(): SlideState[] {
    if (data.slides?.length) {
      return data.slides.map((s: any) => ({
        title: s.title || '',
        body: s.body || '',
        background_image: s.background_image || '',
        cta_url: s.cta_url || '',
        cta_text: s.cta_text || ''
      }));
    }
    return [
      { title: '', body: '', background_image: '', cta_url: '', cta_text: '' },
      { title: '', body: '', background_image: '', cta_url: '', cta_text: '' }
    ];
  }

  const isEditor = $derived(!!data.editing || $page.url.searchParams.get('new') === '1');
  const isNew = $derived(!data.editing && $page.url.searchParams.get('new') === '1');

  let titleValue = $state('');
  let slugValue = $state('');
  let slugTouched = $state(false);
  let coverImage = $state('');
  let posterImage = $state('');
  let ctaUrl = $state('');
  let ctaText = $state('');
  let sourcePostId = $state('');
  let published = $state(false);
  let slides = $state<SlideState[]>([]);
  let barEnabled = $state(!!data.enableStoriesBar);
  let filter = $state<'all' | 'live' | 'draft'>('all');
  let previewSlide = $state(0);

  let uploadingKey = $state<string | null>(null);
  let uploadError = $state<string | null>(null);
  let saving = $state(false);
  let showFromPost = $state(false);
  let showAdvanced = $state(false);
  let openSlide = $state(0);

  let publishMap = $state<Record<number, number>>({});

  $effect(() => {
    const map: Record<number, number> = {};
    for (const s of data.stories || []) map[s.id] = s.published;
    publishMap = map;
    barEnabled = !!data.enableStoriesBar;
  });

  $effect(() => {
    if (data.editing) {
      titleValue = data.editing.title || '';
      slugValue = data.editing.slug || '';
      slugTouched = true;
      coverImage = data.editing.cover_image || '';
      posterImage = data.editing.poster_portrait || '';
      ctaUrl = data.editing.cta_url || '';
      ctaText = data.editing.cta_text || '';
      sourcePostId = data.editing.source_post_id ? String(data.editing.source_post_id) : '';
      published = data.editing.published === 1;
      slides = slidesFromData();
      showAdvanced = !!(data.editing.source_post_id || (data.editing.cta_text && data.editing.cta_text.length));
      openSlide = 0;
      previewSlide = 0;
    } else if ($page.url.searchParams.get('new') === '1') {
      titleValue = '';
      slugValue = '';
      slugTouched = false;
      coverImage = '';
      posterImage = '';
      ctaUrl = '';
      ctaText = '';
      sourcePostId = '';
      published = false;
      slides = slidesFromData();
      showAdvanced = false;
      openSlide = 0;
      previewSlide = 0;
    }
  });

  function slugify(text: string) {
    return text
      .toLowerCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .replace(/[^a-z0-9\s-]/g, '')
      .replace(/[\s_]+/g, '-')
      .replace(/-+/g, '-')
      .replace(/^-+|-+$/g, '')
      .substring(0, 60);
  }

  function onTitleInput(e: Event) {
    const v = (e.target as HTMLInputElement).value;
    titleValue = v;
    if (!slugTouched) slugValue = slugify(v);
  }

  const publishedCount = $derived(
    (data.stories || []).filter((s: any) => (publishMap[s.id] ?? s.published) === 1).length
  );
  const draftCount = $derived((data.stories || []).length - publishedCount);

  const filteredStories = $derived.by(() => {
    const list = data.stories || [];
    if (filter === 'live') return list.filter((s: any) => (publishMap[s.id] ?? s.published) === 1);
    if (filter === 'draft') return list.filter((s: any) => (publishMap[s.id] ?? s.published) !== 1);
    return list;
  });

  const preview = $derived.by(() => {
    const s = slides[previewSlide] || slides[0];
    const bg = s?.background_image || posterImage || coverImage || '';
    return {
      bg,
      title: s?.title || titleValue || t(lang, 'admin.web_stories.preview_title'),
      body: s?.body || '',
      cta: s?.cta_text || ctaText || t(lang, 'admin.web_stories.cta_ph')
    };
  });

  const bubbleSrc = $derived(coverImage || posterImage || slides[0]?.background_image || '');

  function addSlide() {
    if (slides.length >= 12) return;
    slides = [...slides, { title: '', body: '', background_image: '', cta_url: '', cta_text: '' }];
    openSlide = slides.length - 1;
    previewSlide = openSlide;
  }

  function removeSlide(index: number) {
    if (slides.length <= 1) return;
    slides = slides.filter((_, i) => i !== index);
    openSlide = Math.min(openSlide, slides.length - 1);
    previewSlide = Math.min(previewSlide, slides.length - 1);
  }

  function moveSlide(index: number, dir: -1 | 1) {
    const next = index + dir;
    if (next < 0 || next >= slides.length) return;
    const copy = slides.slice();
    [copy[index], copy[next]] = [copy[next], copy[index]];
    slides = copy;
    openSlide = next;
    previewSlide = next;
  }

  async function uploadImage(file: File, key: string): Promise<string | null> {
    uploadingKey = key;
    uploadError = null;
    try {
      const fd = new FormData();
      fd.append('file', file);
      fd.append('folder', 'blog/stories');
      const res = await fetch('/api/upload', { method: 'POST', body: fd });
      if (!res.ok) throw new Error(t(lang, 'admin.web_stories.upload_fail'));
      const json = await res.json();
      return json.url as string;
    } catch (e: any) {
      uploadError = e?.message || t(lang, 'admin.web_stories.upload_fail');
      return null;
    } finally {
      uploadingKey = null;
    }
  }

  async function onCoverFile(e: Event) {
    const input = e.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;
    const url = await uploadImage(file, 'cover');
    if (url) {
      coverImage = url;
      if (!posterImage) posterImage = url;
    }
    input.value = '';
  }

  async function onPosterFile(e: Event) {
    const input = e.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;
    const url = await uploadImage(file, 'poster');
    if (url) {
      posterImage = url;
      if (!coverImage) coverImage = url;
    }
    input.value = '';
  }

  async function onSlideFile(e: Event, index: number) {
    const input = e.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;
    const url = await uploadImage(file, `slide-${index}`);
    if (url) {
      slides = slides.map((s, i) => (i === index ? { ...s, background_image: url } : s));
      if (!coverImage) coverImage = url;
      if (!posterImage) posterImage = url;
      previewSlide = index;
    }
    input.value = '';
  }

  function confirmDelete() {
    return confirm(t(lang, 'admin.web_stories.confirm_delete'));
  }

  const flash = $derived.by(() => {
    const u = $page.url;
    if (u.searchParams.get('created')) return t(lang, 'admin.web_stories.created');
    if (u.searchParams.get('updated')) return t(lang, 'admin.web_stories.updated');
    if (u.searchParams.get('deleted')) return t(lang, 'admin.web_stories.deleted');
    if (u.searchParams.get('from_post')) return t(lang, 'admin.web_stories.from_post_ok');
    return '';
  });
</script>

<svelte:head>
  <title>{t(lang, 'admin.web_stories.title')}</title>
</svelte:head>

<div class="ws" class:editor-mode={isEditor}>
  {#if flash}
    <div class="toast ok">{flash}</div>
  {/if}
  {#if form?.message}
    <div class="toast err">{form.message}</div>
  {/if}
  {#if uploadError}
    <div class="toast err">{uploadError}</div>
  {/if}

  <!-- ═══════════════ LIST ═══════════════ -->
  {#if !isEditor}
    <header class="top">
      <h1>{t(lang, 'admin.web_stories.heading')}</h1>
      <div class="top-actions">
        <form method="POST" action="?/saveBarSetting" use:enhance class="bar-mini">
          <label class="mini-switch" title={t(lang, 'admin.web_stories.bar_enable')}>
            <input
              type="checkbox"
              name="enable_web_stories_bar"
              value="1"
              bind:checked={barEnabled}
              onchange={(e) => e.currentTarget.form?.requestSubmit()}
            />
            <span class="knob"></span>
          </label>
          <span class="mini-label">{t(lang, 'admin.web_stories.bar_short')}</span>
        </form>
        <button type="button" class="btn ghost" onclick={() => (showFromPost = !showFromPost)}>
          {t(lang, 'admin.web_stories.from_post_short')}
        </button>
        <a href="/admin/web-stories?new=1" class="btn primary">+ {t(lang, 'admin.web_stories.create_btn')}</a>
      </div>
    </header>

    {#if showFromPost}
      <form method="POST" action="?/fromPost" use:enhance class="from-strip">
        <select name="post_id" required>
          <option value="">{t(lang, 'admin.web_stories.pick_post')}</option>
          {#each data.posts as post}
            <option value={post.id}>{post.title}</option>
          {/each}
        </select>
        <button type="submit" class="btn primary">{t(lang, 'admin.web_stories.generate')}</button>
        <button type="button" class="btn ghost" onclick={() => (showFromPost = false)}>✕</button>
      </form>
    {/if}

    <div class="stats">
      <button type="button" class="stat" class:on={filter === 'all'} onclick={() => (filter = 'all')}>
        <b>{data.stories.length}</b><span>{t(lang, 'admin.web_stories.filter_all')}</span>
      </button>
      <button type="button" class="stat" class:on={filter === 'live'} onclick={() => (filter = 'live')}>
        <b class="live">{publishedCount}</b><span>{t(lang, 'admin.web_stories.filter_live')}</span>
      </button>
      <button type="button" class="stat" class:on={filter === 'draft'} onclick={() => (filter = 'draft')}>
        <b>{draftCount}</b><span>{t(lang, 'admin.web_stories.filter_draft')}</span>
      </button>
    </div>

    {#if filteredStories.length === 0}
      <div class="empty">
        <div class="empty-visual">
          <span class="empty-ring"></span>
          <span class="empty-ring mid"></span>
          <span class="empty-ring sm"></span>
        </div>
        <p>{t(lang, 'admin.web_stories.empty_short')}</p>
        <a href="/admin/web-stories?new=1" class="btn primary">+ {t(lang, 'admin.web_stories.create_btn')}</a>
      </div>
    {:else}
      <div class="grid">
        {#each filteredStories as story (story.id)}
          {@const isLive = (publishMap[story.id] ?? story.published) === 1}
          <article class="card" class:off={!isLive}>
            <a href="/admin/web-stories?edit={story.id}" class="thumb">
              {#if story.poster_portrait || story.cover_image}
                <img src={story.poster_portrait || story.cover_image} alt="" />
              {:else}
                <span class="ph">{(story.title || '?').charAt(0)}</span>
              {/if}
              <span class="slide-n">{story.slide_count ?? 0}</span>
            </a>
            <div class="card-body">
              <a href="/admin/web-stories?edit={story.id}" class="name">{story.title}</a>
              <span class="slug">/stories/{story.slug}</span>
              <div class="card-foot">
                <form
                  method="POST"
                  action="?/togglePublish"
                  use:enhance={() => {
                    const prev = publishMap[story.id] ?? story.published;
                    publishMap[story.id] = prev === 1 ? 0 : 1;
                    return async ({ result, update }) => {
                      if (result.type === 'failure') publishMap[story.id] = prev;
                      await update({ reset: false });
                    };
                  }}
                >
                  <input type="hidden" name="id" value={story.id} />
                  <button type="submit" class="status" class:live={isLive}>
                    <span class="dot"></span>
                    {isLive ? t(lang, 'admin.web_stories.filter_live') : t(lang, 'admin.web_stories.filter_draft')}
                  </button>
                </form>
                <div class="acts">
                  <a href="/admin/web-stories?edit={story.id}" class="ico" title={t(lang, 'admin.web_stories.edit_btn')}>✎</a>
                  <a href="/stories/{story.slug}" class="ico" target="_blank" rel="noopener" data-sveltekit-reload>↗</a>
                  <form method="POST" action="?/delete" use:enhance onsubmit={confirmDelete}>
                    <input type="hidden" name="id" value={story.id} />
                    <button type="submit" class="ico danger">🗑</button>
                  </form>
                </div>
              </div>
            </div>
          </article>
        {/each}
      </div>
    {/if}

  <!-- ═══════════════ EDITOR ═══════════════ -->
  {:else}
    <form
      method="POST"
      action={data.editing ? '?/update' : '?/create'}
      class="editor"
      use:enhance={() => {
        saving = true;
        return async ({ update }) => {
          await update();
          saving = false;
        };
      }}
    >
      {#if data.editing}
        <input type="hidden" name="id" value={data.editing.id} />
      {/if}
      <input type="hidden" name="cover_image" value={coverImage} />
      <input type="hidden" name="poster_portrait" value={posterImage || coverImage} />
      <input type="hidden" name="cta_text" value={ctaText} />
      <input type="hidden" name="source_post_id" value={sourcePostId} />

      <!-- Top bar -->
      <div class="ed-bar">
        <div class="ed-bar-left">
          <a href="/admin/web-stories" class="back-link">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 18l-6-6 6-6"/></svg>
            {t(lang, 'admin.web_stories.heading')}
          </a>
          <span class="ed-title-sep">/</span>
          <span class="ed-title">{isNew ? t(lang, 'admin.web_stories.create') : t(lang, 'admin.web_stories.edit')}</span>
        </div>
        <div class="ed-bar-right">
          <label class="status-toggle">
            <input type="checkbox" name="published" value="1" bind:checked={published} />
            <span class="status-ui" class:live={published}>
              <span class="dot"></span>
              {published ? t(lang, 'admin.web_stories.filter_live') : t(lang, 'admin.web_stories.filter_draft')}
            </span>
          </label>
          {#if data.editing}
            <a href="/stories/{data.editing.slug}" class="btn ghost" target="_blank" rel="noopener" data-sveltekit-reload>
              {t(lang, 'admin.web_stories.preview')}
            </a>
          {/if}
          <button type="submit" class="btn primary" disabled={saving || !!uploadingKey}>
            {saving ? t(lang, 'admin.web_stories.saving') : t(lang, 'admin.web_stories.save')}
          </button>
        </div>
      </div>

      <div class="ed-layout">
        <!-- FORM -->
        <div class="ed-main">
          <!-- Identity -->
          <section class="panel">
            <div class="panel-label">{t(lang, 'admin.web_stories.section_basic')}</div>
            <label class="field">
              <span class="lbl">{t(lang, 'admin.web_stories.field_title')}</span>
              <input
                name="title"
                required
                value={titleValue}
                oninput={onTitleInput}
                placeholder={t(lang, 'admin.web_stories.title_ph')}
                class="input-lg"
                autocomplete="off"
              />
            </label>
            <div class="fields-2">
              <label class="field">
                <span class="lbl">{t(lang, 'admin.web_stories.field_slug')}</span>
                <div class="prefix-input">
                  <span>/stories/</span>
                  <input
                    name="slug"
                    bind:value={slugValue}
                    oninput={() => (slugTouched = true)}
                    pattern="[a-z0-9\-_]*"
                    placeholder="auto"
                    autocomplete="off"
                  />
                </div>
              </label>
              <label class="field">
                <span class="lbl">{t(lang, 'admin.web_stories.field_cta_url')}</span>
                <input name="cta_url" bind:value={ctaUrl} placeholder="/post/slug" />
              </label>
            </div>
          </section>

          <!-- Media -->
          <section class="panel">
            <div class="panel-label">{t(lang, 'admin.web_stories.section_images')}</div>
            <div class="media-row">
              <div class="drop" class:has={!!posterImage}>
                <div class="drop-preview portrait">
                  {#if posterImage || coverImage}
                    <img src={posterImage || coverImage} alt="" />
                  {:else}
                    <div class="drop-empty">
                      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="M21 15l-5-5L5 21"/></svg>
                      <span>9:16</span>
                    </div>
                  {/if}
                  {#if uploadingKey === 'poster'}
                    <div class="drop-loading">{t(lang, 'admin.web_stories.uploading')}</div>
                  {/if}
                </div>
                <div class="drop-meta">
                  <strong>{t(lang, 'admin.web_stories.field_poster_short')}</strong>
                  <label class="btn ghost sm file">
                    {t(lang, 'admin.web_stories.upload_btn')}
                    <input type="file" accept="image/*" hidden disabled={!!uploadingKey} onchange={onPosterFile} />
                  </label>
                </div>
              </div>

              <div class="drop" class:has={!!coverImage}>
                <div class="drop-preview bubble">
                  {#if bubbleSrc}
                    <img src={bubbleSrc} alt="" />
                  {:else}
                    <div class="drop-empty">
                      <span>○</span>
                    </div>
                  {/if}
                  {#if uploadingKey === 'cover'}
                    <div class="drop-loading">{t(lang, 'admin.web_stories.uploading')}</div>
                  {/if}
                </div>
                <div class="drop-meta">
                  <strong>{t(lang, 'admin.web_stories.field_cover_short')}</strong>
                  <label class="btn ghost sm file">
                    {t(lang, 'admin.web_stories.upload_btn')}
                    <input type="file" accept="image/*" hidden disabled={!!uploadingKey} onchange={onCoverFile} />
                  </label>
                </div>
              </div>
            </div>
            <button type="button" class="linkish" onclick={() => (showAdvanced = !showAdvanced)}>
              {showAdvanced ? '▾' : '▸'} {t(lang, 'admin.web_stories.advanced')}
            </button>
            {#if showAdvanced}
              <div class="adv-box">
                <label class="field">
                  <span class="lbl">{t(lang, 'admin.web_stories.field_cta_text')}</span>
                  <input bind:value={ctaText} placeholder={t(lang, 'admin.web_stories.cta_ph')} />
                </label>
                <label class="field">
                  <span class="lbl">{t(lang, 'admin.web_stories.field_source_post')}</span>
                  <select bind:value={sourcePostId}>
                    <option value="">{t(lang, 'admin.web_stories.none')}</option>
                    {#each data.posts as post}
                      <option value={String(post.id)}>{post.title}</option>
                    {/each}
                  </select>
                </label>
                <label class="field">
                  <span class="lbl">URL — {t(lang, 'admin.web_stories.field_poster_short')}</span>
                  <input type="url" bind:value={posterImage} placeholder="https://..." />
                </label>
                <label class="field">
                  <span class="lbl">URL — {t(lang, 'admin.web_stories.field_cover_short')}</span>
                  <input type="url" bind:value={coverImage} placeholder="https://..." />
                </label>
              </div>
            {/if}
          </section>

          <!-- Slides -->
          <section class="panel">
            <div class="panel-head">
              <div class="panel-label" style="margin:0">{t(lang, 'admin.web_stories.slides')} · {slides.length}</div>
              <button type="button" class="btn ghost sm" onclick={addSlide} disabled={slides.length >= 12}>
                + {t(lang, 'admin.web_stories.add_slide')}
              </button>
            </div>

            <div class="slide-list">
              {#each slides as slide, i}
                <div class="slide" class:open={openSlide === i} class:previewing={previewSlide === i}>
                  <button
                    type="button"
                    class="slide-summary"
                    onclick={() => {
                      openSlide = openSlide === i ? -1 : i;
                      previewSlide = i;
                    }}
                  >
                    <span class="slide-idx">{i + 1}</span>
                    <span class="slide-thumb">
                      {#if slide.background_image || posterImage || coverImage}
                        <img src={slide.background_image || posterImage || coverImage} alt="" />
                      {:else}
                        <span class="st-empty"></span>
                      {/if}
                    </span>
                    <span class="slide-sum-text">
                      <strong>{slide.title || t(lang, 'admin.web_stories.slide_n', { n: String(i + 1) })}</strong>
                      {#if slide.body}<em>{slide.body}</em>{/if}
                    </span>
                    <span class="chev">{openSlide === i ? '▾' : '▸'}</span>
                  </button>

                  {#if openSlide === i}
                    <div class="slide-body">
                      <div class="slide-media-col">
                        <div class="slide-media-preview">
                          {#if slide.background_image}
                            <img src={slide.background_image} alt="" />
                          {:else if posterImage || coverImage}
                            <img src={posterImage || coverImage} alt="" class="faded" />
                          {:else}
                            <span>+</span>
                          {/if}
                          {#if uploadingKey === `slide-${i}`}
                            <div class="drop-loading">…</div>
                          {/if}
                        </div>
                        <label class="btn ghost sm file full">
                          {t(lang, 'admin.web_stories.upload_btn')}
                          <input type="file" accept="image/*" hidden disabled={!!uploadingKey} onchange={(e) => onSlideFile(e, i)} />
                        </label>
                        <input type="hidden" name="slide_image" value={slide.background_image} />
                      </div>
                      <div class="slide-fields">
                        <input name="slide_title" bind:value={slide.title} placeholder={t(lang, 'admin.web_stories.slide_title')} maxlength="80" onfocus={() => (previewSlide = i)} />
                        <textarea name="slide_body" bind:value={slide.body} rows="3" maxlength="200" placeholder={t(lang, 'admin.web_stories.slide_body')} onfocus={() => (previewSlide = i)}></textarea>
                        <div class="fields-2">
                          <input name="slide_cta_url" bind:value={slide.cta_url} placeholder="CTA URL" />
                          <input name="slide_cta_text" bind:value={slide.cta_text} placeholder="CTA" />
                        </div>
                        <input type="url" bind:value={slide.background_image} placeholder="URL imagem" />
                        <div class="slide-actions">
                          <button type="button" class="ico" onclick={() => moveSlide(i, -1)} disabled={i === 0} title="↑">↑</button>
                          <button type="button" class="ico" onclick={() => moveSlide(i, 1)} disabled={i === slides.length - 1} title="↓">↓</button>
                          <button type="button" class="ico danger" onclick={() => removeSlide(i)} disabled={slides.length <= 1} title={t(lang, 'admin.web_stories.remove_slide')}>🗑</button>
                        </div>
                      </div>
                    </div>
                  {:else}
                    <!-- keep fields in DOM for submit when collapsed -->
                    <div class="sr-only" aria-hidden="true">
                      <input name="slide_title" value={slide.title} />
                      <textarea name="slide_body">{slide.body}</textarea>
                      <input name="slide_image" value={slide.background_image} />
                      <input name="slide_cta_url" value={slide.cta_url} />
                      <input name="slide_cta_text" value={slide.cta_text} />
                    </div>
                  {/if}
                </div>
              {/each}
            </div>
          </section>

          <div class="ed-footer">
            <a href="/admin/web-stories" class="btn ghost">{t(lang, 'admin.web_stories.cancel')}</a>
            <button type="submit" class="btn primary" disabled={saving || !!uploadingKey}>
              {saving ? t(lang, 'admin.web_stories.saving') : t(lang, 'admin.web_stories.save')}
            </button>
          </div>
        </div>

        <!-- PHONE PREVIEW -->
        <aside class="ed-preview">
          <div class="phone">
            <div class="phone-notch"></div>
            <div class="phone-screen">
              {#if preview.bg}
                <img class="phone-bg" src={preview.bg} alt="" />
              {:else}
                <div class="phone-bg empty-bg"></div>
              {/if}
              <div class="phone-grad"></div>
              <div class="phone-progress">
                {#each slides as _, i}
                  <button
                    type="button"
                    class="seg"
                    class:on={i === previewSlide}
                    class:done={i < previewSlide}
                    onclick={() => {
                      previewSlide = i;
                      openSlide = i;
                    }}
                  ></button>
                {/each}
              </div>
              <div class="phone-content">
                <h3>{preview.title}</h3>
                {#if preview.body}
                  <p>{preview.body}</p>
                {/if}
                {#if preview.cta}
                  <span class="phone-cta">{preview.cta}</span>
                {/if}
              </div>
            </div>
          </div>
          <p class="preview-hint">{t(lang, 'admin.web_stories.preview_hint')}</p>
          {#if bubbleSrc}
            <div class="bubble-preview">
              <span class="bp-ring"><img src={bubbleSrc} alt="" /></span>
              <span class="bp-label">{titleValue || 'Story'}</span>
            </div>
          {/if}
        </aside>
      </div>
    </form>
  {/if}
</div>

<style>
  .ws {
    max-width: 1100px;
    margin: 0 auto;
    padding-bottom: 3rem;
  }
  .ws.editor-mode {
    max-width: 1180px;
  }

  .toast {
    padding: 0.7rem 1rem;
    border-radius: var(--radius-md, 10px);
    font-size: 0.875rem;
    margin-bottom: 0.85rem;
  }
  .toast.ok {
    background: #ecfdf5;
    color: #065f46;
    border: 1px solid #a7f3d0;
  }
  .toast.err {
    background: #fef2f2;
    color: #991b1b;
    border: 1px solid #fecaca;
  }

  /* ── List header ── */
  .top {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 0.75rem;
    margin-bottom: 1.1rem;
  }
  .top h1 {
    margin: 0;
    font-size: 1.4rem;
    letter-spacing: -0.03em;
    font-weight: 750;
  }
  .top-actions {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 0.4rem;
  }

  .bar-mini {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.3rem 0.65rem;
    border: 1px solid var(--border-color);
    border-radius: 999px;
    background: var(--bg-secondary);
  }
  .mini-label {
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--text-secondary);
  }
  .mini-switch {
    position: relative;
    width: 36px;
    height: 22px;
    cursor: pointer;
  }
  .mini-switch input {
    opacity: 0;
    position: absolute;
    width: 0;
    height: 0;
  }
  .knob {
    position: absolute;
    inset: 0;
    background: #d0d0d0;
    border-radius: 999px;
    transition: 0.15s;
  }
  .knob::after {
    content: '';
    position: absolute;
    width: 16px;
    height: 16px;
    left: 3px;
    top: 3px;
    background: #fff;
    border-radius: 50%;
    transition: 0.15s;
    box-shadow: var(--shadow-xs);
  }
  .mini-switch input:checked + .knob {
    background: #22c55e;
  }
  .mini-switch input:checked + .knob::after {
    transform: translateX(14px);
  }

  .from-strip {
    display: flex;
    flex-wrap: wrap;
    gap: 0.4rem;
    margin-bottom: 0.9rem;
    padding: 0.7rem;
    border: 1px solid var(--border-color);
    border-radius: var(--radius-lg);
    background: var(--bg-secondary);
  }
  .from-strip select {
    flex: 1;
    min-width: 160px;
    min-height: 42px;
    border-radius: var(--radius-md);
    border: 1px solid var(--border-color);
    padding: 0.45rem 0.65rem;
    font: inherit;
    background: var(--bg-primary);
  }

  .stats {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 0.55rem;
    margin-bottom: 1.1rem;
  }
  .stat {
    border: 1px solid var(--border-color);
    background: var(--bg-primary);
    border-radius: var(--radius-lg);
    padding: 0.85rem 0.5rem;
    text-align: center;
    cursor: pointer;
    font: inherit;
    box-shadow: var(--shadow-xs);
    transition: border-color 0.15s, box-shadow 0.15s;
  }
  .stat b {
    display: block;
    font-size: 1.3rem;
    letter-spacing: -0.03em;
  }
  .stat b.live {
    color: #16a34a;
  }
  .stat span {
    font-size: 0.68rem;
    font-weight: 650;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }
  .stat.on {
    border-color: var(--text-primary);
    box-shadow: var(--shadow-sm);
  }

  .grid {
    display: grid;
    grid-template-columns: 1fr;
    gap: 0.75rem;
  }
  @media (min-width: 560px) {
    .grid {
      grid-template-columns: 1fr 1fr;
    }
  }
  @media (min-width: 900px) {
    .grid {
      grid-template-columns: 1fr 1fr 1fr;
    }
  }

  .card {
    display: flex;
    gap: 0.8rem;
    padding: 0.75rem;
    border: 1px solid var(--border-color);
    border-radius: var(--radius-lg);
    background: var(--bg-primary);
    box-shadow: var(--shadow-xs);
    transition: opacity 0.15s, box-shadow 0.15s;
  }
  .card:hover {
    box-shadow: var(--shadow-sm);
  }
  .card.off {
    opacity: 0.7;
  }
  .thumb {
    position: relative;
    width: 70px;
    height: 94px;
    border-radius: 12px;
    overflow: hidden;
    flex-shrink: 0;
    background: var(--bg-tertiary);
    display: block;
  }
  .thumb img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
  .thumb .ph {
    width: 100%;
    height: 100%;
    display: grid;
    place-items: center;
    font-weight: 800;
    color: var(--text-muted);
  }
  .slide-n {
    position: absolute;
    bottom: 4px;
    right: 4px;
    background: rgba(0, 0, 0, 0.6);
    color: #fff;
    font-size: 0.62rem;
    font-weight: 700;
    padding: 0.1rem 0.35rem;
    border-radius: 6px;
  }
  .card-body {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    gap: 0.2rem;
  }
  .name {
    font-weight: 700;
    font-size: 0.95rem;
    color: inherit;
    text-decoration: none;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .slug {
    font-size: 0.72rem;
    color: var(--text-muted);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .card-foot {
    margin-top: auto;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.35rem;
    padding-top: 0.4rem;
  }

  .status {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    border: none;
    background: var(--bg-tertiary);
    color: var(--text-secondary);
    font: inherit;
    font-size: 0.72rem;
    font-weight: 700;
    padding: 0.35rem 0.65rem;
    border-radius: 999px;
    cursor: pointer;
    min-height: 32px;
  }
  .status .dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #a3a3a3;
  }
  .status.live {
    background: #dcfce7;
    color: #166534;
  }
  .status.live .dot {
    background: #22c55e;
    box-shadow: 0 0 0 3px rgba(34, 197, 94, 0.2);
  }
  .acts {
    display: flex;
    gap: 0.2rem;
  }
  .ico {
    width: 32px;
    height: 32px;
    border-radius: 8px;
    border: 1px solid var(--border-color);
    background: var(--bg-primary);
    display: grid;
    place-items: center;
    cursor: pointer;
    text-decoration: none;
    color: inherit;
    font-size: 0.8rem;
    padding: 0;
  }
  .ico.danger {
    color: #b91c1c;
  }
  .ico:disabled {
    opacity: 0.35;
    cursor: not-allowed;
  }

  .empty {
    text-align: center;
    padding: 3.5rem 1rem;
    color: var(--text-secondary);
  }
  .empty-visual {
    display: flex;
    justify-content: center;
    gap: 0.5rem;
    margin-bottom: 1rem;
  }
  .empty-ring {
    width: 48px;
    height: 48px;
    border-radius: 50%;
    border: 2px dashed var(--border-dark);
    opacity: 0.5;
  }
  .empty-ring.mid {
    width: 56px;
    height: 56px;
    opacity: 0.7;
  }
  .empty-ring.sm {
    width: 40px;
    height: 40px;
    opacity: 0.35;
  }

  /* Buttons */
  .btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 0.3rem;
    min-height: 40px;
    padding: 0.5rem 1rem;
    border-radius: var(--radius-md);
    border: none;
    font: inherit;
    font-weight: 650;
    font-size: 0.875rem;
    cursor: pointer;
    text-decoration: none;
    color: inherit;
    background: transparent;
    transition: background 0.15s, border-color 0.15s, transform 0.1s;
  }
  .btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
  .btn.primary {
    background: var(--accent);
    color: var(--bg-primary);
  }
  .btn.primary:hover:not(:disabled) {
    background: var(--accent-hover);
  }
  .btn.ghost {
    border: 1px solid var(--border-color);
    background: var(--bg-primary);
  }
  .btn.ghost:hover:not(:disabled) {
    border-color: var(--border-dark);
    background: var(--bg-secondary);
  }
  .btn.sm {
    min-height: 34px;
    padding: 0.35rem 0.7rem;
    font-size: 0.8rem;
  }
  .file {
    cursor: pointer;
  }
  .file.full {
    width: 100%;
  }

  /* ══════════ EDITOR ══════════ */
  .editor {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .ed-bar {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 0.65rem;
    padding: 0.7rem 0.9rem;
    background: var(--bg-primary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-sm);
    position: sticky;
    top: 0.5rem;
    z-index: 30;
  }
  .ed-bar-left,
  .ed-bar-right {
    display: flex;
    align-items: center;
    gap: 0.45rem;
    flex-wrap: wrap;
  }
  .back-link {
    display: inline-flex;
    align-items: center;
    gap: 0.15rem;
    color: var(--text-secondary);
    text-decoration: none;
    font-size: 0.85rem;
    font-weight: 600;
  }
  .back-link:hover {
    color: var(--text-primary);
  }
  .ed-title-sep {
    color: var(--text-muted);
    opacity: 0.5;
  }
  .ed-title {
    font-weight: 700;
    font-size: 0.9rem;
  }

  .status-toggle {
    cursor: pointer;
  }
  .status-toggle input {
    position: absolute;
    opacity: 0;
    width: 0;
    height: 0;
  }
  .status-ui {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.4rem 0.8rem;
    border-radius: 999px;
    background: var(--bg-tertiary);
    color: var(--text-secondary);
    font-size: 0.8rem;
    font-weight: 700;
    min-height: 36px;
    border: 1px solid transparent;
    transition: 0.15s;
  }
  .status-ui .dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #a3a3a3;
  }
  .status-ui.live {
    background: #dcfce7;
    color: #166534;
    border-color: #bbf7d0;
  }
  .status-ui.live .dot {
    background: #22c55e;
    box-shadow: 0 0 0 3px rgba(34, 197, 94, 0.2);
  }

  .ed-layout {
    display: grid;
    grid-template-columns: 1fr;
    gap: 1.1rem;
    align-items: start;
  }
  @media (min-width: 960px) {
    .ed-layout {
      grid-template-columns: minmax(0, 1fr) 280px;
    }
  }

  .ed-main {
    display: flex;
    flex-direction: column;
    gap: 0.85rem;
    min-width: 0;
  }

  .panel {
    background: var(--bg-primary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-lg);
    padding: 1.1rem 1.15rem;
    box-shadow: var(--shadow-xs);
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }
  .panel-label {
    font-size: 0.7rem;
    font-weight: 750;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: var(--text-muted);
    margin-bottom: 0.1rem;
  }
  .panel-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.5rem;
  }

  .field {
    display: flex;
    flex-direction: column;
    gap: 0.3rem;
  }
  .lbl {
    font-size: 0.78rem;
    font-weight: 650;
    color: var(--text-secondary);
  }
  input,
  select,
  textarea {
    width: 100%;
    min-height: 44px;
    padding: 0.6rem 0.8rem;
    border: 1px solid var(--border-color);
    border-radius: var(--radius-md);
    font: inherit;
    font-size: 0.925rem;
    background: var(--bg-primary);
    color: inherit;
    box-sizing: border-box;
    transition: border-color 0.15s, box-shadow 0.15s;
  }
  textarea {
    min-height: 84px;
    resize: vertical;
    line-height: 1.45;
  }
  input:focus,
  select:focus,
  textarea:focus {
    outline: none;
    border-color: var(--text-primary);
    box-shadow: 0 0 0 3px rgba(42, 42, 42, 0.08);
  }
  .input-lg {
    font-size: 1.05rem;
    font-weight: 600;
    min-height: 50px;
  }

  .fields-2 {
    display: grid;
    grid-template-columns: 1fr;
    gap: 0.65rem;
  }
  @media (min-width: 640px) {
    .fields-2 {
      grid-template-columns: 1fr 1fr;
    }
  }

  .prefix-input {
    display: flex;
    border: 1px solid var(--border-color);
    border-radius: var(--radius-md);
    overflow: hidden;
    min-height: 44px;
  }
  .prefix-input span {
    display: flex;
    align-items: center;
    padding: 0 0.65rem;
    font-size: 0.78rem;
    color: var(--text-muted);
    background: var(--bg-secondary);
    border-right: 1px solid var(--border-color);
    white-space: nowrap;
  }
  .prefix-input input {
    border: none;
    border-radius: 0;
    min-height: 42px;
  }
  .prefix-input:focus-within {
    border-color: var(--text-primary);
    box-shadow: 0 0 0 3px rgba(42, 42, 42, 0.08);
  }

  .media-row {
    display: flex;
    flex-wrap: wrap;
    gap: 1rem;
  }
  .drop {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.45rem;
    padding: 0.75rem;
    border: 1px dashed var(--border-dark);
    border-radius: var(--radius-lg);
    background: var(--bg-secondary);
    min-width: 120px;
    transition: border-color 0.15s, background 0.15s;
  }
  .drop.has {
    border-style: solid;
    border-color: var(--border-color);
    background: var(--bg-primary);
  }
  .drop-preview {
    position: relative;
    overflow: hidden;
    background: var(--bg-tertiary);
    display: grid;
    place-items: center;
  }
  .drop-preview.portrait {
    width: 100px;
    height: 156px;
    border-radius: 14px;
  }
  .drop-preview.bubble {
    width: 72px;
    height: 72px;
    min-width: 72px;
    min-height: 72px;
    max-width: 72px;
    max-height: 72px;
    aspect-ratio: 1 / 1;
    border-radius: 50%;
    overflow: hidden;
    flex-shrink: 0;
    box-sizing: border-box;
    border: 2.5px solid transparent;
    background:
      linear-gradient(var(--bg-tertiary), var(--bg-tertiary)) padding-box,
      linear-gradient(135deg, #f59e0b, #ec4899, #8b5cf6) border-box;
  }
  .drop-preview img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    object-position: center;
    display: block;
  }
  .drop-preview.bubble img {
    border-radius: 50%;
    aspect-ratio: 1 / 1;
  }
  .drop-empty {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.25rem;
    color: var(--text-muted);
    font-size: 0.7rem;
    font-weight: 700;
  }
  .drop-loading {
    position: absolute;
    inset: 0;
    background: rgba(0, 0, 0, 0.5);
    color: #fff;
    display: grid;
    place-items: center;
    font-size: 0.75rem;
    font-weight: 600;
  }
  .drop-meta {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.3rem;
  }
  .drop-meta strong {
    font-size: 0.75rem;
    font-weight: 700;
  }

  .linkish {
    border: none;
    background: none;
    font: inherit;
    font-size: 0.8rem;
    font-weight: 650;
    color: var(--text-muted);
    cursor: pointer;
    text-align: left;
    padding: 0.2rem 0;
    width: fit-content;
  }
  .linkish:hover {
    color: var(--text-primary);
  }
  .adv-box {
    display: flex;
    flex-direction: column;
    gap: 0.6rem;
    padding: 0.75rem;
    border-radius: var(--radius-md);
    background: var(--bg-secondary);
    border: 1px solid var(--border-light);
  }

  /* Slides accordion */
  .slide-list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }
  .slide {
    border: 1px solid var(--border-color);
    border-radius: var(--radius-md);
    background: var(--bg-secondary);
    overflow: hidden;
    transition: border-color 0.15s, box-shadow 0.15s;
  }
  .slide.open,
  .slide.previewing {
    border-color: var(--border-dark);
    background: var(--bg-primary);
    box-shadow: var(--shadow-xs);
  }
  .slide-summary {
    width: 100%;
    display: flex;
    align-items: center;
    gap: 0.65rem;
    padding: 0.65rem 0.75rem;
    border: none;
    background: transparent;
    font: inherit;
    cursor: pointer;
    text-align: left;
    color: inherit;
  }
  .slide-idx {
    width: 24px;
    height: 24px;
    border-radius: 8px;
    background: var(--bg-tertiary);
    display: grid;
    place-items: center;
    font-size: 0.72rem;
    font-weight: 800;
    flex-shrink: 0;
  }
  .slide-thumb {
    width: 36px;
    height: 48px;
    border-radius: 8px;
    overflow: hidden;
    flex-shrink: 0;
    background: var(--bg-tertiary);
  }
  .slide-thumb img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
  .st-empty {
    display: block;
    width: 100%;
    height: 100%;
    background: repeating-linear-gradient(-45deg, #eee, #eee 4px, #f5f5f5 4px, #f5f5f5 8px);
  }
  .slide-sum-text {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    gap: 0.1rem;
  }
  .slide-sum-text strong {
    font-size: 0.875rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .slide-sum-text em {
    font-style: normal;
    font-size: 0.75rem;
    color: var(--text-muted);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .chev {
    color: var(--text-muted);
    font-size: 0.75rem;
  }

  .slide-body {
    display: grid;
    grid-template-columns: 1fr;
    gap: 0.75rem;
    padding: 0 0.75rem 0.85rem;
    border-top: 1px solid var(--border-light);
    padding-top: 0.75rem;
  }
  @media (min-width: 560px) {
    .slide-body {
      grid-template-columns: 88px 1fr;
    }
  }
  .slide-media-col {
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
    align-items: stretch;
  }
  .slide-media-preview {
    position: relative;
    width: 100%;
    max-width: 88px;
    aspect-ratio: 9/14;
    border-radius: 10px;
    overflow: hidden;
    background: var(--bg-tertiary);
    display: grid;
    place-items: center;
    color: var(--text-muted);
    margin: 0 auto;
  }
  .slide-media-preview img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
  .slide-media-preview img.faded {
    opacity: 0.45;
  }
  .slide-fields {
    display: flex;
    flex-direction: column;
    gap: 0.45rem;
  }
  .slide-actions {
    display: flex;
    gap: 0.3rem;
    padding-top: 0.15rem;
  }

  .sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    border: 0;
  }

  .ed-footer {
    display: flex;
    justify-content: flex-end;
    gap: 0.5rem;
    padding: 0.25rem 0 0.5rem;
  }

  /* Phone preview */
  .ed-preview {
    display: none;
    flex-direction: column;
    align-items: center;
    gap: 0.85rem;
    position: sticky;
    top: 5rem;
  }
  @media (min-width: 960px) {
    .ed-preview {
      display: flex;
    }
  }

  .phone {
    width: 240px;
    border-radius: 28px;
    padding: 10px;
    background: linear-gradient(160deg, #2a2a2a, #1a1a1a);
    box-shadow: var(--shadow-xl);
  }
  .phone-notch {
    width: 72px;
    height: 6px;
    border-radius: 999px;
    background: #404040;
    margin: 4px auto 8px;
  }
  .phone-screen {
    position: relative;
    width: 100%;
    aspect-ratio: 9 / 16;
    border-radius: 20px;
    overflow: hidden;
    background: #111;
  }
  .phone-bg {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
  .phone-bg.empty-bg {
    background: linear-gradient(160deg, #1e293b, #0f172a 60%, #334155);
  }
  .phone-grad {
    position: absolute;
    inset: 0;
    background: linear-gradient(to top, rgba(0, 0, 0, 0.78) 0%, rgba(0, 0, 0, 0.15) 45%, transparent 70%);
  }
  .phone-progress {
    position: absolute;
    top: 10px;
    left: 10px;
    right: 10px;
    display: flex;
    gap: 3px;
    z-index: 2;
  }
  .seg {
    flex: 1;
    height: 2.5px;
    border: none;
    border-radius: 2px;
    background: rgba(255, 255, 255, 0.3);
    padding: 0;
    cursor: pointer;
  }
  .seg.on,
  .seg.done {
    background: rgba(255, 255, 255, 0.95);
  }
  .phone-content {
    position: absolute;
    left: 0;
    right: 0;
    bottom: 0;
    padding: 1.25rem 0.9rem 1.4rem;
    color: #fff;
    z-index: 2;
  }
  .phone-content h3 {
    margin: 0 0 0.4rem;
    font-size: 1.05rem;
    font-weight: 800;
    line-height: 1.2;
    text-shadow: 0 2px 10px rgba(0, 0, 0, 0.4);
  }
  .phone-content p {
    margin: 0 0 0.75rem;
    font-size: 0.78rem;
    line-height: 1.4;
    opacity: 0.95;
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
  .phone-cta {
    display: inline-block;
    padding: 0.4rem 0.75rem;
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.95);
    color: #111;
    font-size: 0.7rem;
    font-weight: 700;
  }
  .preview-hint {
    margin: 0;
    font-size: 0.72rem;
    color: var(--text-muted);
    text-align: center;
  }
  .bubble-preview {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.3rem;
  }
  .bp-ring {
    width: 52px;
    height: 52px;
    min-width: 52px;
    min-height: 52px;
    max-width: 52px;
    max-height: 52px;
    aspect-ratio: 1 / 1;
    border-radius: 50%;
    padding: 2px;
    box-sizing: border-box;
    background: linear-gradient(135deg, #f59e0b, #ec4899, #8b5cf6);
    display: grid;
    place-items: center;
    overflow: hidden;
    flex-shrink: 0;
  }
  .bp-ring img {
    width: 100%;
    height: 100%;
    aspect-ratio: 1 / 1;
    border-radius: 50%;
    object-fit: cover;
    object-position: center;
    border: 2px solid var(--bg-primary);
    display: block;
    box-sizing: border-box;
  }
  .bp-label {
    font-size: 0.65rem;
    color: var(--text-secondary);
    max-width: 72px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
</style>
