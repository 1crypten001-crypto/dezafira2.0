<script lang="ts">
  import { page } from "$app/stores";
  import { t } from "$lib/i18n";
  import { onMount } from 'svelte';
  import LandingBlockTree from '$lib/components/LandingBlockTree.svelte';
  import LandingPageHeader from '$lib/components/LandingPageHeader.svelte';
  import { createBlock, createTemplate, getDefaultLandingBlocks, uid } from '$lib/landing-blocks';
  import { acceptsLandingChildren } from '$lib/landing-dnd';

  let { data } = $props();

  const lang = $derived($page.data.language || 'pt');
  const products = $derived(data.products || []);
  const posts = $derived(data.posts || []);

  function tr(key: string, fallback: string) {
    const path = `admin.landing_pages.builder.${key}`;
    const value = t(lang, path);
    return !value || value === path ? fallback : value;
  }

  // Metadados Gerais da Página
  let pageTitle = $state(data.landingPage.title);
  let pageSlug = $state(data.landingPage.slug);
  let pageStatus = $state(data.landingPage.status || 'draft');

  function defaultHeaderLinks() {
    return [
      { id: uid('nav'), label: t(lang, 'admin.landing_pages.builder.mock_nav1'), href: '#' },
      { id: uid('nav'), label: t(lang, 'admin.landing_pages.builder.mock_nav2'), href: '#' },
      { id: uid('nav'), label: t(lang, 'admin.landing_pages.builder.mock_nav3'), href: '#' }
    ];
  }

  function normalizeHeaderSettings(raw = {}) {
    const links = Array.isArray(raw.headerLinks)
      ? raw.headerLinks.map((l) => ({
          id: l.id || uid('nav'),
          label: l.label || '',
          href: l.href || '#'
        }))
      : [];
    // Opt-in: only show if explicitly enabled (not a fixed mock)
    return {
      showHeader: raw.showHeader === true || raw.showHeader === 1,
      headerLogo: raw.headerLogo || '',
      headerLinks: links,
      headerCtaEnabled: raw.headerCtaEnabled !== false && raw.headerCtaEnabled !== 0,
      headerCtaText: raw.headerCtaText || '',
      headerCtaHref: raw.headerCtaHref || '#'
    };
  }

  function enableHeaderWithDefaults() {
    pageSettings.showHeader = true;
    if (!pageSettings.headerLogo) {
      pageSettings.headerLogo = t(lang, 'admin.landing_pages.builder.mock_logo');
    }
    if (!pageSettings.headerLinks?.length) {
      pageSettings.headerLinks = defaultHeaderLinks();
    }
    if (!pageSettings.headerCtaText) {
      pageSettings.headerCtaText = t(lang, 'admin.landing_pages.builder.mock_cta');
    }
    if (pageSettings.headerCtaEnabled === undefined) {
      pageSettings.headerCtaEnabled = true;
    }
  }

  function onToggleHeader(e) {
    const on = e.currentTarget.checked;
    if (on) enableHeaderWithDefaults();
    else pageSettings.showHeader = false;
  }

  const savedSettings = (() => {
    try {
      return data.landingPage.settings ? JSON.parse(data.landingPage.settings) : {};
    } catch {
      return {};
    }
  })();

  // Configurações Globais da Página (inclui header editável)
  let pageSettings = $state({
    seoTitle: '',
    seoDesc: '',
    socialImage: '',
    containerWidth: '1200px',
    backgroundColor: '#ffffff',
    textColor: '#111827',
    ...savedSettings,
    ...normalizeHeaderSettings(savedSettings)
  });

  function addHeaderLink() {
    if (!pageSettings.headerLinks) pageSettings.headerLinks = [];
    pageSettings.headerLinks = [
      ...pageSettings.headerLinks,
      { id: uid('nav'), label: t(lang, 'admin.landing_pages.builder.header_link_new'), href: '#' }
    ];
  }

  function removeHeaderLink(index) {
    pageSettings.headerLinks = pageSettings.headerLinks.filter((_, i) => i !== index);
  }

  // Árvore de Blocos / Elementos (starter i18n quando a página está vazia)
  const initialLang = $page.data.language || 'pt';
  let blocks = $state(
    data.landingPage.content && data.landingPage.content !== '[]'
      ? JSON.parse(data.landingPage.content)
      : getDefaultLandingBlocks(initialLang)
  );

  // Histórico de alterações (Undo / Redo)
  let history = $state([JSON.stringify(blocks)]);
  let historyIndex = $state(0);

  function pushHistory() {
    const currentState = JSON.stringify(blocks);
    if (history[historyIndex] === currentState) return;

    history = history.slice(0, historyIndex + 1);
    history.push(currentState);
    historyIndex = history.length - 1;
  }

  function undo() {
    if (historyIndex > 0) {
      historyIndex--;
      blocks = JSON.parse(history[historyIndex]);
    }
  }

  function redo() {
    if (historyIndex < history.length - 1) {
      historyIndex++;
      blocks = JSON.parse(history[historyIndex]);
    }
  }

  // Bloco selecionado no Canvas
  let selectedBlockId = $state(null);
  let selectedBlock = $derived(findBlockById(blocks, selectedBlockId));

  $effect(() => {
    if (selectedBlock && !selectedBlock.styles) selectedBlock.styles = {};
  });

  function setSelectedStyle(property: string, value: string) {
    if (!selectedBlock) return;
    if (!selectedBlock.styles) selectedBlock.styles = {};
    selectedBlock.styles[property] = value;
    blocks = [...blocks];
    pushHistory();
  }

  function applyStylePreset(preset: 'clean' | 'card' | 'dark') {
    if (!selectedBlock) return;
    const presets = {
      clean: { backgroundColor: 'transparent', textColor: '#0f172a', borderRadius: '0px', paddingTop: '0px', paddingBottom: '0px' },
      card: { backgroundColor: '#ffffff', textColor: '#0f172a', borderRadius: '20px', paddingTop: '32px', paddingBottom: '32px' },
      dark: { backgroundColor: '#0f172a', textColor: '#ffffff', borderRadius: '24px', paddingTop: '48px', paddingBottom: '48px' }
    };
    selectedBlock.styles = { ...(selectedBlock.styles || {}), ...presets[preset] };
    blocks = [...blocks];
    pushHistory();
  }

  function findBlockById(arr, id) {
    if (!id) return null;
    for (const item of arr) {
      if (item.id === id) return item;
      if (item.children) {
        const found = findBlockById(item.children, id);
        if (found) return found;
      }
    }
    return null;
  }

  // Abas das Laterais
  let leftSubTab = $state('blocks'); // 'blocks' | 'components'
  let rightTab = $state('page'); // 'page' | 'block' | 'styles'

  // Modo de visualização responsivo
  let deviceMode = $state('desktop'); // 'desktop' | 'mobile'

  // Estado de salvamento
  let saving = $state(false);
  let saveSuccess = $state(false);

  // Estado para o Editor Rich Text (Visual)
  let isEditingVisual = $state(true);
  let visualEditorRef = $state<HTMLDivElement | null>(null);

  // Estado para a largura redimensionável da barra lateral direita (Resizable sidebar)
  let rightSidebarWidth = $state(340);
  let isResizing = $state(false);

  function startResize(e: MouseEvent) {
    e.preventDefault();
    isResizing = true;
    window.addEventListener('mousemove', handleResize);
    window.addEventListener('mouseup', stopResize);
  }

  function handleResize(e: MouseEvent) {
    if (!isResizing) return;
    const newWidth = window.innerWidth - e.clientX;
    if (newWidth >= 260 && newWidth <= 600) {
      rightSidebarWidth = newWidth;
    }
  }

  function stopResize() {
    if (isResizing) {
      isResizing = false;
      localStorage.setItem('lp-builder-sidebar-width', String(rightSidebarWidth));
      window.removeEventListener('mousemove', handleResize);
      window.removeEventListener('mouseup', stopResize);
    }
  }

  // Sincroniza o editor visual quando o bloco selecionado muda
  $effect(() => {
    if (visualEditorRef && selectedBlock && (selectedBlock.type === 'text' || selectedBlock.type === 'html')) {
      const currentContent = selectedBlock.content || '';
      if (visualEditorRef.innerHTML !== currentContent) {
        visualEditorRef.innerHTML = currentContent;
      }
    }
  });

  // Salva alteracoes feitas no contenteditable
  function handleVisualInput() {
    if (visualEditorRef && selectedBlock) {
      selectedBlock.content = visualEditorRef.innerHTML;
      pushHistory();
    }
  }

  // Executa comandos de formatacao visual (Bold, Italic, etc)
  function execVisualCommand(command: string, value: string | null = null) {
    document.execCommand(command, false, value ?? undefined);
    visualEditorRef?.focus();
    handleVisualInput();
  }

  function insertVisualLink() {
    const url = prompt("Digite a URL do link:");
    if (url) {
      execVisualCommand("createLink", url);
    }
  }

  function insertVisualImage() {
    const url = prompt("Digite a URL da imagem:");
    if (url) {
      execVisualCommand("insertImage", url);
    }
  }
  let saveError = $state(null);

  // Drag and Drop (palette + reorder)
  // IMPORTANT: do not use $state for drag session or drop markers during drag —
  // reactive re-renders abort native HTML5 drag (especially on Windows/Chrome).
  /** @type {{ kind: 'palette', type: string } | { kind: 'block', id: string } | null} */
  let dragSession = null;
  let didDrag = false;
  /** @type {string | null} */
  let dropTargetId = null;
  /** @type {'before' | 'after' | 'inside' | null} */
  let dropPosition = null;
  let canvasDragOver = false;

  function acceptsChildren(type) {
    return acceptsLandingChildren(type);
  }

  function isRootSectionType(type) {
    return (
      type === 'section' ||
      type === 'cta_section' ||
      type === 'testimonials' ||
      type === 'pricing' ||
      type === 'faq_section' ||
      type === 'product_cta'
    );
  }

  function isDescendantOf(ancestorId, nodeId) {
    const ancestor = findBlockById(blocks, ancestorId);
    if (!ancestor?.children) return false;
    if (findBlockById(ancestor.children, nodeId)) return true;
    return false;
  }

  function findParentList(arr, id, parent = null) {
    for (let i = 0; i < arr.length; i++) {
      if (arr[i].id === id) return { list: arr, index: i, parent };
      if (arr[i].children) {
        const found = findParentList(arr[i].children, id, arr[i]);
        if (found) return found;
      }
    }
    return null;
  }

  function extractBlockById(arr, id) {
    for (let i = 0; i < arr.length; i++) {
      if (arr[i].id === id) {
        const [removed] = arr.splice(i, 1);
        return removed;
      }
      if (arr[i].children) {
        const removed = extractBlockById(arr[i].children, id);
        if (removed) return removed;
      }
    }
    return null;
  }

  function insertRelative(targetId, position, block) {
    if (!targetId || position === 'inside') {
      if (targetId) {
        const parent = findBlockById(blocks, targetId);
        if (parent && acceptsChildren(parent.type)) {
          if (!parent.children) parent.children = [];
          // columns expects column children only for structure — still allow
          if (block.type === 'section' && parent.type !== 'section') {
            // ok
          }
          if (block.type === 'section' && parent.type === 'section') {
            blocks.push(block);
            return;
          }
          parent.children.push(block);
          return;
        }
      }
      blocks.push(block);
      return;
    }

    const loc = findParentList(blocks, targetId);
    if (!loc) {
      blocks.push(block);
      return;
    }
    const insertAt = position === 'before' ? loc.index : loc.index + 1;
    loc.list.splice(insertAt, 0, block);
  }

  function clearDropMarkers() {
    if (typeof document === 'undefined') return;
    document.querySelectorAll('.lp-shell.lp-drop-before, .lp-shell.lp-drop-after, .lp-shell.lp-drop-inside').forEach((el) => {
      el.classList.remove('lp-drop-before', 'lp-drop-after', 'lp-drop-inside');
    });
    document.querySelectorAll('.builder-canvas-wrapper.is-drag-over, .canvas-tree-wrap.drop-active').forEach((el) => {
      el.classList.remove('is-drag-over', 'drop-active');
    });
    document.querySelectorAll('.canvas-drop-banner').forEach((el) => el.remove());
  }

  function clearDragState() {
    dragSession = null;
    dropTargetId = null;
    dropPosition = null;
    canvasDragOver = false;
    clearDropMarkers();
    if (typeof document !== 'undefined') {
      document.body.classList.remove('lp-dnd-active');
      document.querySelectorAll('.lp-is-dragging').forEach((n) => n.classList.remove('lp-is-dragging'));
      document.querySelectorAll('.is-palette-dragging').forEach((n) => n.classList.remove('is-palette-dragging'));
    }
  }

  function setDropMarker(targetId, position) {
    if (dropTargetId === targetId && dropPosition === position) return;
    dropTargetId = targetId;
    dropPosition = position;
    clearDropMarkers();
    if (!targetId || !position || typeof document === 'undefined') return;
    const el = document.querySelector(`[data-block-id="${CSS.escape(String(targetId))}"]`);
    if (el) el.classList.add(`lp-drop-${position}`);
  }

  function setCanvasDropActive(active) {
    canvasDragOver = active;
    if (typeof document === 'undefined') return;
    document.querySelectorAll('.builder-canvas-wrapper').forEach((el) => {
      el.classList.toggle('is-drag-over', active);
    });
    document.querySelectorAll('.canvas-tree-wrap').forEach((el) => {
      el.classList.toggle('drop-active', active);
    });
    if (active && !dropTargetId) {
      const wrap = document.querySelector('.canvas-tree-wrap');
      if (wrap && !wrap.querySelector('.canvas-drop-banner')) {
        const banner = document.createElement('div');
        banner.className = 'canvas-drop-banner';
        banner.textContent = t(lang, 'admin.landing_pages.builder.drop_here');
        wrap.appendChild(banner);
      }
    } else {
      document.querySelectorAll('.canvas-drop-banner').forEach((el) => el.remove());
    }
  }

  /** @param {DragEvent | null | undefined} e */
  function readDragSession(e) {
    if (dragSession) return dragSession;
    try {
      const raw = e?.dataTransfer?.getData('application/x-lp-drag');
      if (raw) return JSON.parse(raw);
      const plain = e?.dataTransfer?.getData('text/plain') || '';
      if (plain.startsWith('palette:')) return { kind: 'palette', type: plain.slice(8) };
      if (plain.startsWith('block:')) return { kind: 'block', id: plain.slice(6) };
    } catch {
      /* ignore */
    }
    return null;
  }

  function handlePaletteDragStart(type, e) {
    // Do not set $state here — re-renders abort native HTML5 drag.
    didDrag = true;
    dragSession = { kind: 'palette', type };
    e?.currentTarget?.classList?.add('is-palette-dragging');
    if (typeof document !== 'undefined') document.body.classList.add('lp-dnd-active');
    if (e?.dataTransfer) {
      try {
        e.dataTransfer.setData('text/plain', `palette:${type}`);
        e.dataTransfer.setData('application/x-lp-drag', JSON.stringify(dragSession));
      } catch {
        /* some browsers restrict custom mime types */
      }
      e.dataTransfer.effectAllowed = 'copy';
      // Lightweight drag image for clearer feedback
      try {
        const ghost = document.createElement('div');
        const label = e.currentTarget?.querySelector?.('.elem-name')?.textContent?.trim() || type;
        ghost.textContent = `+  ${label}`;
        ghost.style.cssText =
          'position:fixed;top:-1000px;left:-1000px;padding:11px 16px;background:linear-gradient(135deg,#2563eb,#1d4ed8);color:#fff;border:1px solid rgba(255,255,255,.25);border-radius:12px;box-shadow:0 14px 35px rgba(30,64,175,.35);font:750 12px/1 system-ui;letter-spacing:.01em;';
        document.body.appendChild(ghost);
        e.dataTransfer.setDragImage(ghost, 16, 16);
        setTimeout(() => ghost.remove(), 0);
      } catch {
        /* optional */
      }
    }
  }

  function handleBlockDragStart(id, e) {
    // Do not set $state here — re-renders abort native HTML5 drag.
    didDrag = true;
    dragSession = { kind: 'block', id };
    if (typeof document !== 'undefined') document.body.classList.add('lp-dnd-active');
    if (e?.dataTransfer) {
      try {
        e.dataTransfer.setData('text/plain', `block:${id}`);
        e.dataTransfer.setData('application/x-lp-drag', JSON.stringify(dragSession));
      } catch {
        /* ignore */
      }
      e.dataTransfer.effectAllowed = 'move';
    }
  }

  function handleDragOverTarget(targetId, position, e) {
    e?.preventDefault?.();
    e?.stopPropagation?.();
    setDropMarker(targetId, position);
    if (canvasDragOver) setCanvasDropActive(false);
    if (e?.dataTransfer) {
      e.dataTransfer.dropEffect = dragSession?.kind === 'block' ? 'move' : 'copy';
    }
  }

  function handleCanvasDragOver(e) {
    // Only treat as canvas-root when not hovering a block shell
    const overBlock = e.target?.closest?.(
      '.lp-shell, .lp-drag-handle, .lp-empty-drop, .lp-drop-indicator'
    );
    if (overBlock) return;
    e.preventDefault();
    if (dropTargetId !== null || dropPosition !== null) {
      dropTargetId = null;
      dropPosition = null;
      clearDropMarkers();
    }
    setCanvasDropActive(true);
    if (e.dataTransfer) e.dataTransfer.dropEffect = dragSession?.kind === 'block' ? 'move' : 'copy';
  }

  function handleCanvasDrop(e) {
    e.preventDefault();
    const overBlock = e.target?.closest?.('.lp-shell');
    if (overBlock) return;
    applyDrop(null, 'inside', e);
  }

  function handleTreeDrop(targetId, position, e) {
    e?.preventDefault?.();
    e?.stopPropagation?.();
    applyDrop(targetId, position, e);
  }

  function applyDrop(targetId, position, e = null) {
    const payload = readDragSession(e);
    if (!payload) {
      clearDragState();
      return;
    }

    if (payload.kind === 'palette') {
      const type = payload.type;
      const newElem = createBlock(type, lang);
      // Templates inserted as whole sections at root / after target
      if (isRootSectionType(type) || newElem.type === 'section') {
        if (targetId && (position === 'before' || position === 'after')) {
          insertRelative(targetId, position, newElem);
        } else {
          blocks = [...blocks, newElem];
        }
      } else if (targetId && position === 'inside') {
        const parent = findBlockById(blocks, targetId);
        if (parent && acceptsChildren(parent.type)) {
          if (!parent.children) parent.children = [];
          parent.children.push(newElem);
          blocks = [...blocks];
        } else {
          insertRelative(targetId, position === 'before' ? 'before' : 'after', newElem);
        }
      } else if (targetId) {
        insertRelative(targetId, position, newElem);
      } else {
        // Drop on empty canvas / root
        const lastSection = [...blocks].reverse().find((b) => b.type === 'section');
        if (lastSection) {
          if (!lastSection.children) lastSection.children = [];
          lastSection.children.push(newElem);
          blocks = [...blocks];
        } else {
          const sec = createBlock('section', lang);
          sec.children = [newElem];
          blocks = [...blocks, sec];
        }
      }
      // Force array identity for nested inserts via insertRelative
      blocks = [...blocks];
      selectedBlockId = newElem.id;
      rightTab = 'block';
      pushHistory();
      clearDragState();
      return;
    }

    // Reorder existing block
    const movingId = payload.id;
    if (!movingId || movingId === targetId) {
      clearDragState();
      return;
    }
    // Cannot drop into own descendants
    if (targetId && isDescendantOf(movingId, targetId)) {
      clearDragState();
      return;
    }

    const moved = extractBlockById(blocks, movingId);
    if (!moved) {
      clearDragState();
      return;
    }

    if (!targetId) {
      blocks = [...blocks, moved];
    } else if (position === 'inside') {
      const parent = findBlockById(blocks, targetId);
      if (parent && acceptsChildren(parent.type) && moved.type !== 'section') {
        if (!parent.children) parent.children = [];
        parent.children.push(moved);
      } else {
        insertRelative(targetId, 'after', moved);
      }
    } else {
      insertRelative(targetId, position, moved);
    }

    // Force reactivity
    blocks = [...blocks];
    selectedBlockId = movingId;
    rightTab = 'block';
    pushHistory();
    clearDragState();
  }

  function handleDragEnd() {
    // Delay clear so drop handlers can still read dragSession;
    // keep didDrag briefly so palette click after drag is ignored.
    setTimeout(() => {
      clearDragState();
      setTimeout(() => {
        didDrag = false;
      }, 80);
    }, 0);
  }

  function handlePaletteClick(type) {
    // If a drag just happened, ignore the synthetic click
    if (didDrag) {
      didDrag = false;
      return;
    }
    addNewBlock(type);
  }

  // Adicionar bloco via clique na paleta
  function addNewBlock(type, parentId = null) {
    const newElem = createBlock(type, lang);
    const newId = newElem.id;

    if (parentId) {
      const parent = findBlockById(blocks, parentId);
      if (parent) {
        if (!parent.children) parent.children = [];
        if (newElem.type === 'section') {
          blocks.push(newElem);
        } else {
          parent.children.push(newElem);
        }
      }
    } else if (isRootSectionType(type) || newElem.type === 'section') {
      blocks.push(newElem);
    } else {
      const lastSection = [...blocks].reverse().find((b) => b.type === 'section');
      if (lastSection) {
        if (!lastSection.children) lastSection.children = [];
        lastSection.children.push(newElem);
      } else {
        const sec = createBlock('section', lang);
        sec.children = [newElem];
        blocks.push(sec);
      }
    }

    blocks = [...blocks];
    selectedBlockId = newId;
    rightTab = 'block';
    pushHistory();
  }

  function insertTemplate(name) {
    const sec = createTemplate(name, lang);
    blocks = [...blocks, sec];
    selectedBlockId = sec.id;
    rightTab = 'block';
    pushHistory();
  }

  function linkProductToSelected(productId) {
    if (!selectedBlock) return;
    const id = productId ? parseInt(productId) : null;
    const prod = products.find((p) => p.id === id);
    if (!selectedBlock.properties) selectedBlock.properties = {};
    if (prod) {
      selectedBlock.properties.productId = prod.id;
      selectedBlock.properties.productSlug = prod.slug;
      const href = `/product/${prod.slug}`;
      if (selectedBlock.type === 'button') {
        selectedBlock.properties.href = href;
      } else if (selectedBlock.type === 'cta') {
        selectedBlock.properties.buttonHref = href;
      } else if (selectedBlock.type === 'pricing') {
        selectedBlock.properties.buttonHref = href;
      } else if (selectedBlock.type === 'product-showcase') {
        selectedBlock.properties.name = prod.name;
        selectedBlock.properties.description = prod.description || '';
        selectedBlock.properties.image = prod.image_url || '';
        selectedBlock.properties.imageAlt = prod.name;
        selectedBlock.properties.price = new Intl.NumberFormat(lang === 'en' ? 'en-US' : 'pt-BR', { style: 'currency', currency: 'BRL' }).format((prod.price_cents || 0) / 100);
        selectedBlock.properties.buttonHref = href;
      }
    } else {
      selectedBlock.properties.productId = null;
      selectedBlock.properties.productSlug = null;
    }
    pushHistory();
  }

  function togglePostForSelected(postId: number) {
    if (!selectedBlock || selectedBlock.type !== 'posts-grid') return;
    const current = selectedBlock.properties.posts || [];
    const exists = current.some((p: any) => p.id === postId);
    if (exists) {
      selectedBlock.properties.posts = current.filter((p: any) => p.id !== postId);
    } else if (current.length < 6) {
      const post = posts.find((p) => p.id === postId);
      if (post) selectedBlock.properties.posts = [...current, { ...post, href: `/post/${post.slug}` }];
    }
    pushHistory();
  }

  // FAQ helpers
  function addFaqItem() {
    if (!selectedBlock || selectedBlock.type !== 'faq') return;
    if (!selectedBlock.properties.items) selectedBlock.properties.items = [];
    selectedBlock.properties.items = [
      ...selectedBlock.properties.items,
      { q: t(lang, 'admin.landing_pages.builder.new_question'), a: t(lang, 'admin.landing_pages.builder.new_answer') }
    ];
    pushHistory();
  }

  function removeFaqItem(index) {
    if (!selectedBlock || selectedBlock.type !== 'faq') return;
    selectedBlock.properties.items = selectedBlock.properties.items.filter((_, i) => i !== index);
    pushHistory();
  }

  function addPricingFeature() {
    if (!selectedBlock || selectedBlock.type !== 'pricing') return;
    selectedBlock.properties.features = [
      ...(selectedBlock.properties.features || []),
      t(lang, 'admin.landing_pages.builder.new_feature')
    ];
    pushHistory();
  }

  function removePricingFeature(index) {
    if (!selectedBlock || selectedBlock.type !== 'pricing') return;
    selectedBlock.properties.features = selectedBlock.properties.features.filter((_, i) => i !== index);
    pushHistory();
  }

  // Keyboard shortcuts: Ctrl/Cmd+Z, Ctrl+Y / Ctrl+Shift+Z, Ctrl/Cmd+S
  onMount(() => {
    // Carrega largura salva da barra lateral
    if (typeof localStorage !== 'undefined') {
      const savedWidth = localStorage.getItem('lp-builder-sidebar-width');
      if (savedWidth) {
        const parsed = parseInt(savedWidth, 10);
        if (parsed >= 260 && parsed <= 600) {
          rightSidebarWidth = parsed;
        }
      }
    }

    function onKey(e) {
      const mod = e.metaKey || e.ctrlKey;
      if (!mod) return;
      const tag = e.target?.tagName;
      const inField = tag === 'INPUT' || tag === 'TEXTAREA' || e.target?.isContentEditable;

      if (e.key === 's' || e.key === 'S') {
        e.preventDefault();
        saveLandingPage();
        return;
      }
      if (inField) return;
      if (e.key === 'z' || e.key === 'Z') {
        e.preventDefault();
        if (e.shiftKey) redo();
        else undo();
      } else if (e.key === 'y' || e.key === 'Y') {
        e.preventDefault();
        redo();
      } else if (e.key === 'd' || e.key === 'D') {
        if (selectedBlockId) {
          e.preventDefault();
          duplicateBlock(selectedBlockId);
        }
      }
    }
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  });

  // Deletar bloco
  function deleteBlock(id) {
    function removeRecursive(arr) {
      for (let i = 0; i < arr.length; i++) {
        if (arr[i].id === id) {
          arr.splice(i, 1);
          return true;
        }
        if (arr[i].children) {
          const removed = removeRecursive(arr[i].children);
          if (removed) return true;
        }
      }
      return false;
    }

    removeRecursive(blocks);
    if (selectedBlockId === id) {
      selectedBlockId = null;
      rightTab = 'page';
    }
    pushHistory();
  }

  // Duplicar bloco (Puck-style)
  function duplicateBlock(id) {
    if (!id) return;
    function duplicateRecursive(arr) {
      for (let i = 0; i < arr.length; i++) {
        if (arr[i].id === id) {
          const clone = JSON.parse(JSON.stringify(arr[i]));
          function regenerateIds(block) {
            block.id = uid(block.type);
            if (block.children && Array.isArray(block.children)) {
              block.children.forEach(regenerateIds);
            }
          }
          regenerateIds(clone);
          arr.splice(i + 1, 0, clone);
          return clone.id;
        }
        if (arr[i].children && Array.isArray(arr[i].children)) {
          const newId = duplicateRecursive(arr[i].children);
          if (newId) return newId;
        }
      }
      return null;
    }

    const newId = duplicateRecursive(blocks);
    if (newId) {
      selectedBlockId = newId;
      pushHistory();
    }
  }

  // Reordenar blocos
  function moveBlock(id, direction) {
    function moveRecursive(arr) {
      for (let i = 0; i < arr.length; i++) {
        if (arr[i].id === id) {
          if (direction === 'up' && i > 0) {
            const temp = arr[i];
            arr[i] = arr[i - 1];
            arr[i - 1] = temp;
            return true;
          }
          if (direction === 'down' && i < arr.length - 1) {
            const temp = arr[i];
            arr[i] = arr[i + 1];
            arr[i + 1] = temp;
            return true;
          }
          return false;
        }
        if (arr[i].children) {
          const moved = moveRecursive(arr[i].children);
          if (moved) return true;
        }
      }
      return false;
    }

    moveRecursive(blocks);
    pushHistory();
  }

  // Upload
  let uploadingImage = $state(false);

  async function handleImageUpload(e, targetProp) {
    const input = e.target;
    if (!input.files || input.files.length === 0) return;

    const file = input.files[0];
    const formData = new FormData();
    formData.append('file', file);

    uploadingImage = true;
    try {
      const response = await fetch('?/uploadImage', {
        method: 'POST',
        body: formData
      });

      const resultText = await response.text();
      const resultObj = JSON.parse(resultText);

      let url = '';
      if (resultObj.data) {
        const dataParsed = JSON.parse(resultObj.data);
        if (dataParsed && dataParsed[1]) {
          url = dataParsed[1].url;
        }
      }

      if (url) {
        if (selectedBlock && targetProp !== 'bg') {
          selectedBlock.properties[targetProp] = url;
        } else if (targetProp === 'bg') {
          pageSettings.socialImage = url;
        }
        pushHistory();
      } else {
        alert(t(lang, 'admin.landing_pages.builder.upload_fail_url'));
      }
    } catch (err) {
      console.error(err);
      alert(t(lang, 'admin.landing_pages.builder.upload_fail'));
    } finally {
      uploadingImage = false;
      input.value = '';
    }
  }

  // Salvar
  async function saveLandingPage() {
    saving = true;
    saveSuccess = false;
    saveError = null;

    const formData = new FormData();
    formData.append('title', pageTitle);
    formData.append('slug', pageSlug);
    formData.append('status', pageStatus);
    formData.append('content', JSON.stringify(blocks));
    formData.append('settings', JSON.stringify(pageSettings));

    try {
      const response = await fetch('?/save', {
        method: 'POST',
        body: formData
      });

      const resultText = await response.text();
      const resultObj = JSON.parse(resultText);

      let success = false;
      let errorMsg = t(lang, 'admin.landing_pages.builder.save_fail');

      if (resultObj.data) {
        const dataParsed = JSON.parse(resultObj.data);
        if (dataParsed && dataParsed[0] === 'success') {
          success = true;
        } else if (dataParsed && dataParsed[1]?.error) {
          errorMsg = dataParsed[1].error;
        }
      }

      if (success) {
        saveSuccess = true;
        setTimeout(() => (saveSuccess = false), 3000);
      } else {
        saveError = errorMsg;
      }
    } catch (err) {
      console.error(err);
      saveError = t(lang, 'admin.landing_pages.builder.save_network');
    } finally {
      saving = false;
    }
  }
</script>

<svelte:head>
  <title>Builder | {pageTitle}</title>
</svelte:head>

<div class="builder-root">
  <!-- 1. BARRA SUPERIOR (Topbar) -->
  <header class="builder-topbar">
    <div class="topbar-left">
      <a href="/admin/landing-pages" class="back-link" title={t(lang, 'admin.landing_pages.builder.back')}>
        <svg viewBox="0 0 20 20" fill="currentColor" width="20" height="20">
          <path fill-rule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clip-rule="evenodd" />
        </svg>
      </a>
      <span class="breadcrumb-txt">{t(lang, 'admin.landing_pages.title')}</span>
      <span class="divider">/</span>
      <input type="text" class="topbar-title-input" bind:value={pageTitle} />
    </div>

    <div class="topbar-center">
      <button class="device-btn" class:active={deviceMode === 'desktop'} onclick={() => deviceMode = 'desktop'} title={t(lang, 'admin.landing_pages.builder.desktop')}>
        <svg viewBox="0 0 20 20" fill="currentColor" width="18" height="18">
          <path fill-rule="evenodd" d="M3 5a2 2 0 012-2h10a2 2 0 012 2v8a2 2 0 01-2 2h-2.22l.11 1.2a.75.75 0 01-.74.8h-4.3a.75.75 0 01-.74-.8l.11-1.2H5a2 2 0 01-2-2V5zm2-.5a.5.5 0 00-.5.5v7.5a.5.5 0 00.5.5h10a.5.5 0 00.5-.5V5a.5.5 0 00-.5-.5H5z" clip-rule="evenodd" />
        </svg>
      </button>
      <button class="device-btn" class:active={deviceMode === 'mobile'} onclick={() => deviceMode = 'mobile'} title={t(lang, 'admin.landing_pages.builder.mobile')}>
        <svg viewBox="0 0 20 20" fill="currentColor" width="18" height="18">
          <path fill-rule="evenodd" d="M7 2a2 2 0 00-2 2v12a2 2 0 002 2h6a2 2 0 002-2V4a2 2 0 00-2-2H7zm0 1.5h6a.5.5 0 01.5.5v11a.5.5 0 01-.5.5H7a.5.5 0 01-.5-.5V4a.5.5 0 01.5-.5zM10 15a1 1 0 100 2 1 1 0 000-2z" clip-rule="evenodd" />
        </svg>
      </button>
    </div>

    <div class="topbar-right">
      <button class="history-btn" disabled={historyIndex === 0} onclick={undo} title={t(lang, 'admin.landing_pages.builder.undo')}>
        <svg viewBox="0 0 20 20" fill="currentColor" width="18" height="18">
          <path fill-rule="evenodd" d="M7.707 14.707a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 1.414L5.414 9H11a5 5 0 110 10H9a1 1 0 110-2h2a3 3 0 100-6H5.414l2.293 2.293a1 1 0 010 1.414z" clip-rule="evenodd" />
        </svg>
      </button>
      <button class="history-btn" disabled={historyIndex === history.length - 1} onclick={redo} title={t(lang, 'admin.landing_pages.builder.redo')}>
        <svg viewBox="0 0 20 20" fill="currentColor" width="18" height="18">
          <path fill-rule="evenodd" d="M12.293 5.293a1 1 0 011.414 0l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414-1.414L14.586 11H9a5 5 0 110-10h2a1 1 0 110 2H9a3 3 0 100 6h5.586l-2.293-2.293a1 1 0 010-1.414z" clip-rule="evenodd" />
        </svg>
      </button>

      <select class="status-select" bind:value={pageStatus} title="Status">
        <option value="draft">{t(lang, 'admin.landing_pages.draft')}</option>
        <option value="published">{t(lang, 'admin.landing_pages.published')}</option>
      </select>

      <a href="/p/{pageSlug}" target="_blank" rel="noopener noreferrer" class="preview-btn">
        {t(lang, 'admin.landing_pages.preview')}
      </a>

      <button class="save-btn" onclick={saveLandingPage} disabled={saving}>
        {saving ? t(lang, 'admin.landing_pages.saving') : t(lang, 'admin.landing_pages.save')}
      </button>

      {#if saveSuccess}
        <span class="save-toast success">✓ {t(lang, 'admin.landing_pages.saved')}</span>
      {/if}
      {#if saveError}
        <span class="save-toast error">✕ {saveError}</span>
      {/if}
    </div>
  </header>

  <!-- 2. ÁREA DE TRABALHO DO BUILDER -->
  <div class="builder-workspace">
    <!-- A. Painel Esquerdo: Elementos (Fiel ao Mockup) -->
    <aside class="left-sidebar">
      <div class="sidebar-tabs">
        <button class="tab-btn active" type="button">{t(lang, 'admin.landing_pages.builder.elements')}</button>
      </div>

      <div class="sidebar-subtabs">
        <button class="subtab-btn" class:active={leftSubTab === 'blocks'} onclick={() => leftSubTab = 'blocks'}>
          {t(lang, 'admin.landing_pages.builder.blocks')}
        </button>
        <button class="subtab-btn" class:active={leftSubTab === 'components'} onclick={() => leftSubTab = 'components'}>
          {t(lang, 'admin.landing_pages.builder.components')}
        </button>
      </div>

      <p class="dnd-hint">{t(lang, 'admin.landing_pages.builder.dnd_hint')}</p>

      <div class="elements-group-list">
        {#if leftSubTab === 'blocks'}
          <span class="group-title">{t(lang, 'admin.landing_pages.builder.group_basic')}</span>
          <div class="elements-grid">
            <div class="element-item" draggable="true" ondragstart={(e) => handlePaletteDragStart('section', e)} ondragend={handleDragEnd} onclick={() => handlePaletteClick('section')}>
              <span class="elem-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="3" y1="15" x2="21" y2="15"/></svg>
              </span>
              <span class="elem-name">{t(lang, 'admin.landing_pages.builder.block_section')}</span>
            </div>
            <div class="element-item" draggable="true" ondragstart={(e) => handlePaletteDragStart('text', e)} ondragend={handleDragEnd} onclick={() => handlePaletteClick('text')}>
              <span class="elem-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="4 7 4 4 20 4 20 7"/><line x1="9" y1="20" x2="15" y2="20"/><line x1="12" y1="4" x2="12" y2="20"/></svg>
              </span>
              <span class="elem-name">{t(lang, 'admin.landing_pages.builder.block_text')}</span>
            </div>
            <div class="element-item" draggable="true" ondragstart={(e) => handlePaletteDragStart('image', e)} ondragend={handleDragEnd} onclick={() => handlePaletteClick('image')}>
              <span class="elem-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>
              </span>
              <span class="elem-name">{t(lang, 'admin.landing_pages.builder.block_image')}</span>
            </div>
            <div class="element-item" draggable="true" ondragstart={(e) => handlePaletteDragStart('button', e)} ondragend={handleDragEnd} onclick={() => handlePaletteClick('button')}>
              <span class="elem-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="M12 14l3-3-3-3"/></svg>
              </span>
              <span class="elem-name">{t(lang, 'admin.landing_pages.builder.block_button')}</span>
            </div>
            <div class="element-item" draggable="true" ondragstart={(e) => handlePaletteDragStart('video', e)} ondragend={handleDragEnd} onclick={() => handlePaletteClick('video')}>
              <span class="elem-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"/><path d="M10 8l6 3-6 3V8z"/></svg>
              </span>
              <span class="elem-name">{t(lang, 'admin.landing_pages.builder.block_video')}</span>
            </div>
            <div class="element-item" draggable="true" ondragstart={(e) => handlePaletteDragStart('divider', e)} ondragend={handleDragEnd} onclick={() => handlePaletteClick('divider')}>
              <span class="elem-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"/></svg>
              </span>
              <span class="elem-name">{t(lang, 'admin.landing_pages.builder.block_divider')}</span>
            </div>
            <div class="element-item" draggable="true" ondragstart={(e) => handlePaletteDragStart('spacer', e)} ondragend={handleDragEnd} onclick={() => handlePaletteClick('spacer')}>
              <span class="elem-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="8 17 12 21 16 17"/><polyline points="8 7 12 3 16 7"/><line x1="12" y1="3" x2="12" y2="21"/></svg>
              </span>
              <span class="elem-name">{t(lang, 'admin.landing_pages.builder.block_spacer')}</span>
            </div>
            <div class="element-item" draggable="true" ondragstart={(e) => handlePaletteDragStart('html', e)} ondragend={handleDragEnd} onclick={() => handlePaletteClick('html')}>
              <span class="elem-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>
              </span>
              <span class="elem-name">HTML</span>
            </div>
          </div>

          <span class="group-title" style="margin-top: 1.25rem;">Premium</span>
          <div class="elements-grid premium-elements">
            <div class="element-item" role="button" tabindex="0" draggable="true" onkeydown={(e) => e.key === 'Enter' && handlePaletteClick('hero')} ondragstart={(e) => handlePaletteDragStart('hero', e)} ondragend={handleDragEnd} onclick={() => handlePaletteClick('hero')}>
              <span class="elem-icon">✦</span><span class="elem-name">Hero premium</span>
            </div>
            <div class="element-item" role="button" tabindex="0" draggable="true" onkeydown={(e) => e.key === 'Enter' && handlePaletteClick('product-showcase')} ondragstart={(e) => handlePaletteDragStart('product-showcase', e)} ondragend={handleDragEnd} onclick={() => handlePaletteClick('product-showcase')}>
              <span class="elem-icon">◈</span><span class="elem-name">Produto</span>
            </div>
            <div class="element-item" role="button" tabindex="0" draggable="true" onkeydown={(e) => e.key === 'Enter' && handlePaletteClick('posts-grid')} ondragstart={(e) => handlePaletteDragStart('posts-grid', e)} ondragend={handleDragEnd} onclick={() => handlePaletteClick('posts-grid')}>
              <span class="elem-icon">☷</span><span class="elem-name">Posts</span>
            </div>
            <div class="element-item" role="button" tabindex="0" draggable="true" onkeydown={(e) => e.key === 'Enter' && handlePaletteClick('trust-bar')} ondragstart={(e) => handlePaletteDragStart('trust-bar', e)} ondragend={handleDragEnd} onclick={() => handlePaletteClick('trust-bar')}>
              <span class="elem-icon">✓</span><span class="elem-name">Confiança</span>
            </div>
          </div>

          <span class="group-title" style="margin-top: 1.25rem;">{t(lang, 'admin.landing_pages.builder.group_structure')}</span>
          <div class="elements-grid">
            <div class="element-item" draggable="true" ondragstart={(e) => handlePaletteDragStart('columns-2', e)} ondragend={handleDragEnd} onclick={() => handlePaletteClick('columns-2')}>
              <span class="elem-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><line x1="12" y1="3" x2="12" y2="21"/></svg>
              </span>
              <span class="elem-name">{t(lang, 'admin.landing_pages.builder.block_cols2')}</span>
            </div>
            <div class="element-item" draggable="true" ondragstart={(e) => handlePaletteDragStart('columns-3', e)} ondragend={handleDragEnd} onclick={() => handlePaletteClick('columns-3')}>
              <span class="elem-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><line x1="9" y1="3" x2="9" y2="21"/><line x1="15" y1="3" x2="15" y2="21"/></svg>
              </span>
              <span class="elem-name">{t(lang, 'admin.landing_pages.builder.block_cols3')}</span>
            </div>
            <div class="element-item" draggable="true" ondragstart={(e) => handlePaletteDragStart('container', e)} ondragend={handleDragEnd} onclick={() => handlePaletteClick('container')}>
              <span class="elem-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/></svg>
              </span>
              <span class="elem-name">{t(lang, 'admin.landing_pages.builder.block_container')}</span>
            </div>
          </div>

          <span class="group-title" style="margin-top: 1.25rem;">{t(lang, 'admin.landing_pages.builder.group_conversion')}</span>
          <div class="elements-grid">
            <div class="element-item" draggable="true" ondragstart={(e) => handlePaletteDragStart('cta', e)} ondragend={handleDragEnd} onclick={() => handlePaletteClick('cta')}>
              <span class="elem-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4.5 16.5c-1.5 1.26-2.5 3.19-2.5 5.5h20c0-2.31-1-4.24-2.5-5.5M12 2C7.58 2 4 5.58 4 10c0 4.42 3.58 8 8 8s8-3.58 8-8c0-4.42-3.58-8-8-8zM12 6v8M9 10h6"/></svg>
              </span>
              <span class="elem-name">CTA</span>
            </div>
            <div class="element-item" draggable="true" ondragstart={(e) => handlePaletteDragStart('testimonial', e)} ondragend={handleDragEnd} onclick={() => handlePaletteClick('testimonial')}>
              <span class="elem-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
              </span>
              <span class="elem-name">{t(lang, 'admin.landing_pages.builder.block_testimonial')}</span>
            </div>
            <div class="element-item" draggable="true" ondragstart={(e) => handlePaletteDragStart('pricing', e)} ondragend={handleDragEnd} onclick={() => handlePaletteClick('pricing')}>
              <span class="elem-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="4" width="20" height="16" rx="2" ry="2"/><line x1="2" y1="10" x2="22" y2="10"/><path d="M6 15h2"/><path d="M10 15h6"/></svg>
              </span>
              <span class="elem-name">{t(lang, 'admin.landing_pages.builder.block_pricing')}</span>
            </div>
            <div class="element-item" draggable="true" ondragstart={(e) => handlePaletteDragStart('faq', e)} ondragend={handleDragEnd} onclick={() => handlePaletteClick('faq')}>
              <span class="elem-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
              </span>
              <span class="elem-name">FAQ</span>
            </div>
          </div>
        {:else}
          <span class="group-title">{t(lang, 'admin.landing_pages.builder.group_templates')}</span>
          <p class="components-hint">{t(lang, 'admin.landing_pages.builder.templates_hint')}</p>
          <div class="template-list">
            <button type="button" class="template-card" onclick={() => insertTemplate('cta_section')}>
              <strong>{t(lang, 'admin.landing_pages.builder.tpl_cta')}</strong>
              <span>{t(lang, 'admin.landing_pages.builder.tpl_cta_desc')}</span>
            </button>
            <button type="button" class="template-card" onclick={() => insertTemplate('testimonials')}>
              <strong>{t(lang, 'admin.landing_pages.builder.tpl_testimonials')}</strong>
              <span>{t(lang, 'admin.landing_pages.builder.tpl_testimonials_desc')}</span>
            </button>
            <button type="button" class="template-card" onclick={() => insertTemplate('pricing')}>
              <strong>{t(lang, 'admin.landing_pages.builder.tpl_pricing')}</strong>
              <span>{t(lang, 'admin.landing_pages.builder.tpl_pricing_desc')}</span>
            </button>
            <button type="button" class="template-card" onclick={() => insertTemplate('faq_section')}>
              <strong>FAQ</strong>
              <span>{t(lang, 'admin.landing_pages.builder.tpl_faq_desc')}</span>
            </button>
            <button type="button" class="template-card" onclick={() => insertTemplate('product_cta')}>
              <strong>{t(lang, 'admin.landing_pages.builder.tpl_product')}</strong>
              <span>{t(lang, 'admin.landing_pages.builder.tpl_product_desc')}</span>
            </button>
          </div>
        {/if}
      </div>
    </aside>

    <!-- B. Canvas Central -->
    <main
      class="builder-canvas-wrapper"
      ondragover={handleCanvasDragOver}
      ondrop={handleCanvasDrop}
      ondragleave={(e) => {
        if (e.currentTarget === e.target) setCanvasDropActive(false);
      }}
    >
      <div
        class="builder-canvas-frame {deviceMode}"
        style="background-color: {pageSettings.backgroundColor || '#ffffff'}; color: {pageSettings.textColor || '#111827'};"
      >
        {#if pageSettings.showHeader}
          <LandingPageHeader
            logo={pageSettings.headerLogo}
            links={pageSettings.headerLinks || []}
            ctaText={pageSettings.headerCtaText}
            ctaHref={pageSettings.headerCtaHref}
            showCta={!!pageSettings.headerCtaEnabled}
            maxWidth={pageSettings.containerWidth || '1200px'}
          />
        {/if}

        <div
          class="canvas-tree-wrap"
          ondragover={handleCanvasDragOver}
          ondrop={handleCanvasDrop}
        >
          <LandingBlockTree
            {blocks}
            {lang}
            containerWidth={pageSettings.containerWidth || '1200px'}
            editable={true}
            selectedId={selectedBlockId}
            onSelect={(id) => { selectedBlockId = id; rightTab = 'block'; }}
            onDrop={handleTreeDrop}
            onDragOverTarget={handleDragOverTarget}
            onBlockDragStart={handleBlockDragStart}
            onDragEnd={handleDragEnd}
            onMoveBlock={moveBlock}
            onDuplicateBlock={duplicateBlock}
            onDeleteBlock={deleteBlock}
          />
        </div>

        {#if blocks.length === 0}
          <div class="section-empty-placeholder">
            {t(lang, 'admin.landing_pages.builder.empty_canvas')}
          </div>
        {/if}
      </div>
    </main>

    <!-- C. Painel Direito: Configurações & Estilos -->
    <aside class="right-sidebar" style="width: {rightSidebarWidth}px;">
      <div 
        class="sidebar-resize-handle" 
        class:active={isResizing}
        onmousedown={startResize} 
        role="separator" 
        aria-label="Redimensionar painel"
      ></div>
      <div class="sidebar-tabs">
        <button class="tab-btn" class:active={rightTab === 'page'} onclick={() => rightTab = 'page'}>
          <span class="tab-dot"></span>{tr('tab_page', 'Página')}
        </button>
        <button class="tab-btn" class:active={rightTab === 'block'} onclick={() => rightTab = 'block'} disabled={!selectedBlockId}>
          <span class="tab-dot"></span>{tr('tab_block', 'Bloco')}
        </button>
        <button class="tab-btn" class:active={rightTab === 'styles'} onclick={() => rightTab = 'styles'} disabled={!selectedBlockId}>
          <span class="tab-dot"></span>{tr('tab_styles', 'Estilos')}
        </button>
      </div>

      <div class="settings-panel-content">
        {#if rightTab === 'page'}
          <div class="settings-form lp-page-settings-form">
            <div class="panel-heading"><span class="panel-kicker">LANDING PAGE</span><h4>{tr('settings', 'Configurações')}</h4><p>Identidade, publicação e aparência geral da página.</p></div>
            
            <!-- 1. Identificacao -->
            <details class="lp-accordion" open>
              <summary class="lp-accordion-header">
                <span class="lp-accordion-title"><b class="accordion-symbol">01</b><span>{tr('group_identification', 'Identificação')}<small>Título, endereço e publicação</small></span></span>
                <span class="lp-accordion-icon">⌄</span>
              </summary>
              <div class="lp-accordion-content">
                <div class="form-group">
                  <label>{t(lang, 'admin.landing_pages.builder.page_title')}</label>
                  <input type="text" bind:value={pageTitle} />
                </div>

                <div class="form-group">
                  <label>Slug</label>
                  <input type="text" bind:value={pageSlug} />
                </div>

                <div class="form-group">
                  <label>{t(lang, 'admin.landing_pages.col_status')}</label>
                  <div class="choice-grid status-choice">
                    <button type="button" class:active={pageStatus === 'draft'} onclick={() => pageStatus = 'draft'}><span class="status-light draft"></span><b>Rascunho</b><small>Só administradores</small></button>
                    <button type="button" class:active={pageStatus === 'published'} onclick={() => pageStatus = 'published'}><span class="status-light live"></span><b>Publicada</b><small>Visível no site</small></button>
                  </div>
                </div>
              </div>
            </details>

            <!-- 2. SEO & Compartilhamento -->
            <details class="lp-accordion">
              <summary class="lp-accordion-header">
                <span class="lp-accordion-title"><b class="accordion-symbol">SEO</b><span>SEO & {tr('group_social', 'Redes sociais')}<small>Google e compartilhamentos</small></span></span>
                <span class="lp-accordion-icon">⌄</span>
              </summary>
              <div class="lp-accordion-content">
                <div class="form-group">
                  <label>{t(lang, 'admin.landing_pages.builder.meta_title')}</label>
                  <input type="text" bind:value={pageSettings.seoTitle} placeholder={t(lang, 'admin.landing_pages.builder.meta_title_ph')} />
                </div>

                <div class="form-group">
                  <label>{t(lang, 'admin.landing_pages.builder.meta_desc')}</label>
                  <textarea bind:value={pageSettings.seoDesc} placeholder={t(lang, 'admin.landing_pages.builder.meta_desc_ph')}></textarea>
                </div>

                <div class="form-group">
                  <label>{t(lang, 'admin.landing_pages.builder.social_image')}</label>
                  <div class="image-upload-mock-card">
                    {#if pageSettings.socialImage}
                      <img src={pageSettings.socialImage} alt="Social" class="social-img-preview" />
                    {:else}
                      <span class="upload-icon-svg">↑</span>
                      <span class="upload-txt-main">{t(lang, 'admin.landing_pages.builder.add_image')}</span>
                      <span class="upload-txt-sub">{t(lang, 'admin.landing_pages.builder.image_size_hint')}</span>
                    {/if}
                    <input type="file" accept="image/*" class="hidden-upload-input" onchange={(e) => handleImageUpload(e, 'bg')} />
                  </div>
                </div>
              </div>
            </details>

            <!-- 3. Design & Cabecalho -->
            <details class="lp-accordion">
              <summary class="lp-accordion-header">
                <span class="lp-accordion-title"><b class="accordion-symbol">UI</b><span>{tr('group_header_design', 'Design & Cabeçalho')}<small>Largura, fundo e navegação</small></span></span>
                <span class="lp-accordion-icon">⌄</span>
              </summary>
              <div class="lp-accordion-content">
                <div class="form-group">
                  <label>{t(lang, 'admin.landing_pages.builder.container_width')}</label>
                  <div class="choice-grid width-choice">
                    <button type="button" class:active={pageSettings.containerWidth === '900px'} onclick={() => pageSettings.containerWidth = '900px'}><i class="width-icon narrow"></i><b>Compacta</b><small>900px</small></button>
                    <button type="button" class:active={pageSettings.containerWidth === '1200px'} onclick={() => pageSettings.containerWidth = '1200px'}><i class="width-icon normal"></i><b>Padrão</b><small>1200px</small></button>
                    <button type="button" class:active={pageSettings.containerWidth === '1400px'} onclick={() => pageSettings.containerWidth = '1400px'}><i class="width-icon wide"></i><b>Ampla</b><small>1400px</small></button>
                  </div>
                </div>

                <div class="form-group">
                  <label>{t(lang, 'admin.landing_pages.builder.page_bg')}</label>
                  <div class="color-control"><input type="color" bind:value={pageSettings.backgroundColor} aria-label="Escolher fundo da página" /><input type="text" bind:value={pageSettings.backgroundColor} aria-label="Cor hexadecimal do fundo" /></div>
                </div>

                <hr class="lp-accordion-divider" />

                <div class="form-group checkbox-row">
                  <label>
                    <input type="checkbox" checked={!!pageSettings.showHeader} onchange={onToggleHeader} />
                    {t(lang, 'admin.landing_pages.builder.show_header')}
                  </label>
                </div>

                {#if pageSettings.showHeader}
                  <div class="form-group">
                    <label>{t(lang, 'admin.landing_pages.builder.header_logo')}</label>
                    <input type="text" bind:value={pageSettings.headerLogo} placeholder={t(lang, 'admin.landing_pages.builder.mock_logo')} />
                  </div>

                  <div class="form-group">
                    <label>{t(lang, 'admin.landing_pages.builder.header_links')}</label>
                    {#each pageSettings.headerLinks || [] as link, i (link.id || i)}
                      <div class="header-link-row">
                        <input
                          type="text"
                          bind:value={link.label}
                          placeholder={t(lang, 'admin.landing_pages.builder.header_link_label')}
                        />
                        <input
                          type="text"
                          bind:value={link.href}
                          placeholder="#section"
                        />
                        <button type="button" class="mini-btn" onclick={() => removeHeaderLink(i)} title={t(lang, 'admin.landing_pages.builder.remove')}>✕</button>
                      </div>
                    {/each}
                    <button type="button" class="mini-btn add" onclick={addHeaderLink}>
                      + {t(lang, 'admin.landing_pages.builder.add_header_link')}
                    </button>
                  </div>

                  <div class="form-group checkbox-row">
                    <label>
                      <input type="checkbox" bind:checked={pageSettings.headerCtaEnabled} />
                      {t(lang, 'admin.landing_pages.builder.show_header_cta')}
                    </label>
                  </div>

                  {#if pageSettings.headerCtaEnabled}
                    <div class="form-group">
                      <label>{t(lang, 'admin.landing_pages.builder.header_cta_text')}</label>
                      <input type="text" bind:value={pageSettings.headerCtaText} />
                    </div>
                    <div class="form-group">
                      <label>{t(lang, 'admin.landing_pages.builder.header_cta_href')}</label>
                      <input type="text" bind:value={pageSettings.headerCtaHref} placeholder="# ou /products" />
                    </div>
                  {/if}
                {/if}
              </div>
            </details>
          </div>
        {/if}

        <!-- GUIA: BLOCO -->
        {#if rightTab === 'block' && selectedBlock}
          <div class="settings-form">
            <h4 class="settings-group-title">{t(lang, 'admin.landing_pages.builder.content')}: {selectedBlock.type.toUpperCase()}</h4>

            {#if selectedBlock.type === 'hero'}
              <div class="form-group"><span class="form-label">Selo superior</span><input type="text" bind:value={selectedBlock.properties.eyebrow} oninput={pushHistory} /></div>
              <div class="form-group"><span class="form-label">Título</span><textarea bind:value={selectedBlock.properties.title} rows="3" oninput={pushHistory}></textarea></div>
              <div class="form-group"><span class="form-label">Subtítulo</span><textarea bind:value={selectedBlock.properties.subtitle} rows="3" oninput={pushHistory}></textarea></div>
              <div class="form-group"><span class="form-label">Botão principal</span><input type="text" bind:value={selectedBlock.properties.primaryText} oninput={pushHistory} /></div>
              <div class="form-group"><span class="form-label">Link principal</span><input type="text" bind:value={selectedBlock.properties.primaryHref} oninput={pushHistory} /></div>
              <div class="form-group"><span class="form-label">Botão secundário</span><input type="text" bind:value={selectedBlock.properties.secondaryText} oninput={pushHistory} /></div>
              <div class="form-group"><span class="form-label">Link secundário</span><input type="text" bind:value={selectedBlock.properties.secondaryHref} oninput={pushHistory} /></div>
              <div class="form-group"><span class="form-label">Imagem</span><input type="text" bind:value={selectedBlock.properties.image} oninput={pushHistory} /></div>
              <div class="form-group"><div class="upload-btn-wrapper"><input type="file" accept="image/*" id="hero-img-upload" onchange={(e) => handleImageUpload(e, 'image')} /><label for="hero-img-upload" class="upload-file-label">{uploadingImage ? 'Enviando...' : 'Enviar imagem'}</label></div></div>
            {:else if selectedBlock.type === 'product-showcase'}
              <div class="form-group"><span class="form-label">Produto do blog</span><select value={selectedBlock.properties.productId || ''} onchange={(e) => linkProductToSelected(e.currentTarget.value)}><option value="">Selecione</option>{#each products as prod}<option value={prod.id}>{prod.name}</option>{/each}</select><small class="field-hint">Preenche nome, preço, imagem, descrição e link automaticamente.</small></div>
              <div class="form-group"><span class="form-label">Título</span><input type="text" bind:value={selectedBlock.properties.name} oninput={pushHistory} /></div>
              <div class="form-group"><span class="form-label">Descrição</span><textarea bind:value={selectedBlock.properties.description} rows="4" oninput={pushHistory}></textarea></div>
              <div class="form-group"><span class="form-label">Benefícios (um por linha)</span><textarea value={(selectedBlock.properties.bullets || []).join('\n')} rows="4" oninput={(e) => { selectedBlock.properties.bullets = e.currentTarget.value.split('\n').map((v) => v.trim()).filter(Boolean).slice(0, 6); pushHistory(); }}></textarea></div>
              <div class="form-group"><span class="form-label">Preço exibido</span><input type="text" bind:value={selectedBlock.properties.price} oninput={pushHistory} /></div>
              <div class="form-group"><span class="form-label">Imagem</span><input type="text" bind:value={selectedBlock.properties.image} oninput={pushHistory} /></div>
              <div class="form-group"><div class="upload-btn-wrapper"><input type="file" accept="image/*" id="product-img-upload" onchange={(e) => handleImageUpload(e, 'image')} /><label for="product-img-upload" class="upload-file-label">{uploadingImage ? 'Enviando...' : 'Trocar imagem'}</label></div></div>
              <div class="form-group"><span class="form-label">Texto do botão</span><input type="text" bind:value={selectedBlock.properties.buttonText} oninput={pushHistory} /></div>
              <div class="form-group"><span class="form-label">Link</span><input type="text" bind:value={selectedBlock.properties.buttonHref} oninput={pushHistory} /></div>
            {:else if selectedBlock.type === 'posts-grid'}
              <div class="form-group"><span class="form-label">Título da seção</span><input type="text" bind:value={selectedBlock.properties.title} oninput={pushHistory} /></div>
              <div class="form-group"><span class="form-label">Subtítulo</span><textarea bind:value={selectedBlock.properties.subtitle} rows="2" oninput={pushHistory}></textarea></div>
              <div class="form-group"><span class="form-label">Posts publicados (máx. 6)</span><div class="content-picker">{#each posts as post}<label class="content-picker-item"><input type="checkbox" checked={(selectedBlock.properties.posts || []).some((p: any) => p.id === post.id)} disabled={(selectedBlock.properties.posts || []).length >= 6 && !(selectedBlock.properties.posts || []).some((p: any) => p.id === post.id)} onchange={() => togglePostForSelected(post.id)} /><span>{post.title}</span></label>{/each}</div></div>
            {:else if selectedBlock.type === 'trust-bar'}
              <div class="form-group"><span class="form-label">Itens de confiança (um por linha)</span><textarea value={(selectedBlock.properties.items || []).join('\n')} rows="6" oninput={(e) => { selectedBlock.properties.items = e.currentTarget.value.split('\n').map((v) => v.trim()).filter(Boolean).slice(0, 8); pushHistory(); }}></textarea></div>
            {:else if selectedBlock.type === 'text' || selectedBlock.type === 'html'}
              <div class="form-group">
                <div class="html-editor-header">
                  <label>{t(lang, 'admin.landing_pages.builder.html_content')}</label>
                  
                  <!-- Toggle entre Visual e HTML -->
                  <div class="editor-toggle-pills">
                    <button 
                      type="button" 
                      class="toggle-pill-btn" 
                      class:active={isEditingVisual} 
                      onclick={() => {
                        isEditingVisual = true;
                        // Sincroniza visualEditor com content atual
                        if (visualEditorRef) {
                          visualEditorRef.innerHTML = selectedBlock.content || '';
                        }
                      }}
                    >
                      📝 Visual
                    </button>
                    <button 
                      type="button" 
                      class="toggle-pill-btn" 
                      class:active={!isEditingVisual} 
                      onclick={() => {
                        isEditingVisual = false;
                      }}
                    >
                      💻 HTML
                    </button>
                  </div>
                </div>

                {#if isEditingVisual}
                  <!-- Rich Text Toolbar (Puck-style) -->
                  <div class="visual-editor-toolbar">
                    <button type="button" class="toolbar-btn" onclick={() => execVisualCommand('bold')} title="Negrito"><b>B</b></button>
                    <button type="button" class="toolbar-btn" onclick={() => execVisualCommand('italic')} title="Itálico"><i>I</i></button>
                    <button type="button" class="toolbar-btn" onclick={() => execVisualCommand('formatBlock', 'h2')} title="Título 2">H2</button>
                    <button type="button" class="toolbar-btn" onclick={() => execVisualCommand('formatBlock', 'h3')} title="Título 3">H3</button>
                    <button type="button" class="toolbar-btn" onclick={() => execVisualCommand('formatBlock', 'p')} title="Parágrafo">P</button>
                    <button type="button" class="toolbar-btn" onclick={() => execVisualCommand('insertUnorderedList')} title="Lista">• Lista</button>
                    <button type="button" class="toolbar-btn" onclick={insertVisualLink} title="Adicionar Link">🔗 Link</button>
                    <button type="button" class="toolbar-btn" onclick={insertVisualImage} title="Inserir Imagem">🖼️ Foto</button>
                  </div>
                  
                  <!-- Area editável com fundo branco e design premium -->
                  <div
                    bind:this={visualEditorRef}
                    contenteditable="true"
                    class="visual-editor-container"
                    oninput={handleVisualInput}
                    spellcheck="false"
                  ></div>
                {:else}
                  <!-- Raw HTML Editor (fundo preto tradicional para estrutura) -->
                  {#if selectedBlock.content && (selectedBlock.content.indexOf('div') !== -1 || selectedBlock.content.indexOf('svg') !== -1)}
                    <p class="html-editor-help" style="margin-bottom: 0.5rem;">Este bloco contém marcação de layout e ícones. Edite as tags com cuidado para manter o design.</p>
                  {/if}
                  <textarea 
                    class="code-editor-textarea" 
                    bind:value={selectedBlock.content} 
                    rows="12" 
                    oninput={pushHistory}
                    spellcheck="false"
                  ></textarea>
                {/if}
              </div>
            {:else if selectedBlock.type === 'image'}
              <div class="form-group">
                <label>{t(lang, 'admin.landing_pages.builder.image_url')}</label>
                <input type="text" bind:value={selectedBlock.properties.src} onchange={pushHistory} />
              </div>
              <div class="form-group">
                <label>Alt</label>
                <input type="text" bind:value={selectedBlock.properties.alt} oninput={pushHistory} />
              </div>
              <div class="form-group">
                <label>{t(lang, 'admin.landing_pages.builder.upload')}</label>
                <div class="upload-btn-wrapper">
                  <input type="file" accept="image/*" id="block-img-upload" onchange={(e) => handleImageUpload(e, 'src')} />
                  <label for="block-img-upload" class="upload-file-label">
                    {uploadingImage ? t(lang, 'admin.landing_pages.builder.uploading') : t(lang, 'admin.landing_pages.builder.upload_image')}
                  </label>
                </div>
              </div>
            {:else if selectedBlock.type === 'button'}
              <div class="form-group">
                <label>{t(lang, 'admin.landing_pages.builder.button_text')}</label>
                <input type="text" bind:value={selectedBlock.content} oninput={pushHistory} />
              </div>
              <div class="form-group">
                <label>{t(lang, 'admin.landing_pages.builder.link_url')}</label>
                <input type="text" bind:value={selectedBlock.properties.href} oninput={pushHistory} />
              </div>
              <div class="form-group">
                <label>{t(lang, 'admin.landing_pages.builder.link_product')}</label>
                <select
                  value={selectedBlock.properties.productId || ''}
                  onchange={(e) => linkProductToSelected(e.currentTarget.value)}
                >
                  <option value="">{t(lang, 'admin.landing_pages.builder.none')}</option>
                  {#each products as prod}
                    <option value={prod.id}>{prod.name}</option>
                  {/each}
                </select>
                <small class="field-hint">{t(lang, 'admin.landing_pages.builder.product_href_hint')}</small>
              </div>
            {:else if selectedBlock.type === 'video'}
              <div class="form-group">
                <label>{t(lang, 'admin.landing_pages.builder.youtube_link')}</label>
                <input type="text" bind:value={selectedBlock.properties.src} oninput={pushHistory} />
              </div>
            {:else if selectedBlock.type === 'cta'}
              <div class="form-group">
                <label>{t(lang, 'admin.landing_pages.builder.label_title')}</label>
                <input type="text" bind:value={selectedBlock.content} oninput={pushHistory} />
              </div>
              <div class="form-group">
                <label>{t(lang, 'admin.landing_pages.builder.subtitle_field')}</label>
                <textarea bind:value={selectedBlock.properties.subtitle} rows="3" oninput={pushHistory}></textarea>
              </div>
              <div class="form-group">
                <label>{t(lang, 'admin.landing_pages.builder.button_text')}</label>
                <input type="text" bind:value={selectedBlock.properties.buttonText} oninput={pushHistory} />
              </div>
              <div class="form-group">
                <label>{t(lang, 'admin.landing_pages.builder.button_link')}</label>
                <input type="text" bind:value={selectedBlock.properties.buttonHref} oninput={pushHistory} />
              </div>
              <div class="form-group">
                <label>{t(lang, 'admin.landing_pages.builder.link_product')}</label>
                <select
                  value={selectedBlock.properties.productId || ''}
                  onchange={(e) => linkProductToSelected(e.currentTarget.value)}
                >
                  <option value="">{t(lang, 'admin.landing_pages.builder.none')}</option>
                  {#each products as prod}
                    <option value={prod.id}>{prod.name}</option>
                  {/each}
                </select>
              </div>
              <div class="form-group">
                <label>{t(lang, 'admin.landing_pages.builder.button_color')}</label>
                <input type="color" bind:value={selectedBlock.properties.buttonBg} onchange={pushHistory} />
              </div>
            {:else if selectedBlock.type === 'testimonial'}
              <div class="form-group">
                <label>{t(lang, 'admin.landing_pages.builder.quote')}</label>
                <textarea bind:value={selectedBlock.properties.quote} rows="4" oninput={pushHistory}></textarea>
              </div>
              <div class="form-group">
                <label>{t(lang, 'admin.landing_pages.builder.author')}</label>
                <input type="text" bind:value={selectedBlock.properties.author} oninput={pushHistory} />
              </div>
              <div class="form-group">
                <label>{t(lang, 'admin.landing_pages.builder.role')}</label>
                <input type="text" bind:value={selectedBlock.properties.role} oninput={pushHistory} />
              </div>
              <div class="form-group">
                <label>{t(lang, 'admin.landing_pages.builder.avatar_url')}</label>
                <input type="text" bind:value={selectedBlock.properties.avatar} oninput={pushHistory} />
              </div>
              <div class="form-group">
                <label>{t(lang, 'admin.landing_pages.builder.rating')}</label>
                <input type="number" min="1" max="5" bind:value={selectedBlock.properties.rating} oninput={pushHistory} />
              </div>
            {:else if selectedBlock.type === 'pricing'}
              <div class="form-group">
                <label>{t(lang, 'admin.landing_pages.builder.plan_name')}</label>
                <input type="text" bind:value={selectedBlock.properties.name} oninput={pushHistory} />
              </div>
              <div class="form-group">
                <label>{t(lang, 'admin.landing_pages.builder.price')}</label>
                <input type="text" bind:value={selectedBlock.properties.price} oninput={pushHistory} />
              </div>
              <div class="form-group">
                <label>{t(lang, 'admin.landing_pages.builder.period')}</label>
                <input type="text" bind:value={selectedBlock.properties.period} oninput={pushHistory} />
              </div>
              <div class="form-group">
                <label>{t(lang, 'admin.landing_pages.builder.button_text')}</label>
                <input type="text" bind:value={selectedBlock.properties.buttonText} oninput={pushHistory} />
              </div>
              <div class="form-group">
                <label>{t(lang, 'admin.landing_pages.builder.button_link')}</label>
                <input type="text" bind:value={selectedBlock.properties.buttonHref} oninput={pushHistory} />
              </div>
              <div class="form-group">
                <label>{t(lang, 'admin.landing_pages.builder.link_product')}</label>
                <select
                  value={selectedBlock.properties.productId || ''}
                  onchange={(e) => linkProductToSelected(e.currentTarget.value)}
                >
                  <option value="">{t(lang, 'admin.landing_pages.builder.none')}</option>
                  {#each products as prod}
                    <option value={prod.id}>{prod.name}</option>
                  {/each}
                </select>
              </div>
              <div class="form-group checkbox-row">
                <label>
                  <input type="checkbox" bind:checked={selectedBlock.properties.featured} onchange={pushHistory} />
                  {t(lang, 'admin.landing_pages.builder.feature_plan')}
                </label>
              </div>
              <div class="form-group">
                <label>{t(lang, 'admin.landing_pages.builder.features')}</label>
                {#each selectedBlock.properties.features || [] as feat, i}
                  <div class="inline-row">
                    <input
                      type="text"
                      value={feat}
                      oninput={(e) => {
                        selectedBlock.properties.features[i] = e.currentTarget.value;
                        pushHistory();
                      }}
                    />
                    <button type="button" class="mini-btn" onclick={() => removePricingFeature(i)}>✕</button>
                  </div>
                {/each}
                <button type="button" class="mini-btn add" onclick={addPricingFeature}>+ {t(lang, 'admin.landing_pages.builder.add_feature')}</button>
              </div>
            {:else if selectedBlock.type === 'faq'}
              <div class="form-group">
                <label>{t(lang, 'admin.landing_pages.builder.section_title')}</label>
                <input type="text" bind:value={selectedBlock.properties.title} oninput={pushHistory} />
              </div>
              {#each selectedBlock.properties.items || [] as item, i}
                <div class="faq-editor-card">
                  <div class="form-group">
                    <label>{t(lang, 'admin.landing_pages.builder.question')} {i + 1}</label>
                    <input type="text" bind:value={item.q} oninput={pushHistory} />
                  </div>
                  <div class="form-group">
                    <label>{t(lang, 'admin.landing_pages.builder.answer')}</label>
                    <textarea bind:value={item.a} rows="2" oninput={pushHistory}></textarea>
                  </div>
                  <button type="button" class="mini-btn" onclick={() => removeFaqItem(i)}>{t(lang, 'admin.landing_pages.builder.remove')}</button>
                </div>
              {/each}
              <button type="button" class="mini-btn add" onclick={addFaqItem}>+ {t(lang, 'admin.landing_pages.builder.add_question')}</button>
            {:else if selectedBlock.type === 'columns'}
              <div class="form-group">
                <label>{t(lang, 'admin.landing_pages.builder.columns')}</label>
                <select
                  value={String(selectedBlock.properties.cols || 2)}
                  onchange={(e) => {
                    selectedBlock.properties.cols = parseInt(e.currentTarget.value);
                    pushHistory();
                  }}
                >
                  <option value="2">2</option>
                  <option value="3">3</option>
                </select>
              </div>
              <div class="form-group">
                <label>Gap</label>
                <input type="text" bind:value={selectedBlock.properties.gap} oninput={pushHistory} />
              </div>
              <p class="field-hint">{t(lang, 'admin.landing_pages.builder.columns_hint')}</p>
            {:else}
              <p class="field-hint">{t(lang, 'admin.landing_pages.builder.select_block_hint')}</p>
            {/if}
          </div>
        {/if}

        {#if rightTab === 'styles' && selectedBlock}
          <div class="settings-form style-inspector">
            <div class="panel-heading style-heading"><span class="panel-kicker">{selectedBlock.type.toUpperCase()}</span><h4>Design do bloco</h4><p>Ajuste o visual e acompanhe no canvas em tempo real.</p></div>

            <section class="inspector-section">
              <div class="inspector-title"><span>Aparência rápida</span><small>Presets</small></div>
              <div class="preset-grid">
                <button type="button" onclick={() => applyStylePreset('clean')}><i class="preset-preview clean"></i><b>Clean</b></button>
                <button type="button" onclick={() => applyStylePreset('card')}><i class="preset-preview card"></i><b>Card</b></button>
                <button type="button" onclick={() => applyStylePreset('dark')}><i class="preset-preview dark"></i><b>Dark</b></button>
              </div>
            </section>

            <section class="inspector-section">
              <div class="inspector-title"><span>Cores</span><small>Hexadecimal</small></div>
              <div class="form-group">
                <label>Texto</label>
                <div class="color-control"><input type="color" value={selectedBlock.styles.textColor || '#0f172a'} oninput={(e) => setSelectedStyle('textColor', e.currentTarget.value)} aria-label="Escolher cor do texto" /><input type="text" value={selectedBlock.styles.textColor || '#0f172a'} oninput={(e) => setSelectedStyle('textColor', e.currentTarget.value)} aria-label="Cor hexadecimal do texto" /></div>
              </div>
              <div class="form-group">
                <label>Fundo</label>
                <div class="color-control"><input type="color" value={selectedBlock.styles.backgroundColor === 'transparent' ? '#ffffff' : selectedBlock.styles.backgroundColor || '#ffffff'} oninput={(e) => setSelectedStyle('backgroundColor', e.currentTarget.value)} aria-label="Escolher cor do fundo" /><input type="text" value={selectedBlock.styles.backgroundColor || 'transparent'} oninput={(e) => setSelectedStyle('backgroundColor', e.currentTarget.value)} aria-label="Cor hexadecimal do fundo" /></div>
              </div>
            </section>

            <section class="inspector-section">
              <div class="inspector-title"><span>Alinhamento</span><small>Conteúdo</small></div>
              <div class="segmented-control" aria-label="Alinhamento do conteúdo">
                <button type="button" class:active={(selectedBlock.styles.textAlign || 'left') === 'left'} onclick={() => setSelectedStyle('textAlign', 'left')} title="Esquerda">≡<span>Esquerda</span></button>
                <button type="button" class:active={selectedBlock.styles.textAlign === 'center'} onclick={() => setSelectedStyle('textAlign', 'center')} title="Centro">≡<span>Centro</span></button>
                <button type="button" class:active={selectedBlock.styles.textAlign === 'right'} onclick={() => setSelectedStyle('textAlign', 'right')} title="Direita">≡<span>Direita</span></button>
              </div>
            </section>

            {#if selectedBlock.type === 'text' || selectedBlock.type === 'button'}
              <section class="inspector-section">
                <div class="inspector-title"><span>Tipografia</span><small>Tamanho</small></div>
                <div class="form-group"><label>Tamanho da fonte</label><div class="unit-input"><input type="text" value={selectedBlock.styles.fontSize || '16px'} oninput={(e) => setSelectedStyle('fontSize', e.currentTarget.value)} /><span>CSS</span></div></div>
              </section>
            {/if}

            <section class="inspector-section">
              <div class="inspector-title"><span>Forma</span><small>Cantos e borda</small></div>
              <div class="two-field-grid">
                <div class="form-group"><label>Raio</label><div class="unit-input"><input type="text" value={selectedBlock.styles.borderRadius || '0px'} oninput={(e) => setSelectedStyle('borderRadius', e.currentTarget.value)} /><span>CSS</span></div></div>
                {#if selectedBlock.type === 'button'}
                  <div class="form-group"><label>Borda</label><div class="unit-input"><input type="text" value={selectedBlock.styles.borderWidth || '0px'} oninput={(e) => setSelectedStyle('borderWidth', e.currentTarget.value)} /><span>CSS</span></div></div>
                {/if}
              </div>
              {#if selectedBlock.type === 'button'}
                <div class="form-group"><label>Cor da borda</label><div class="color-control"><input type="color" value={selectedBlock.styles.borderColor || '#0f172a'} oninput={(e) => { setSelectedStyle('borderColor', e.currentTarget.value); setSelectedStyle('borderStyle', 'solid'); }} aria-label="Escolher cor da borda" /><input type="text" value={selectedBlock.styles.borderColor || 'transparent'} oninput={(e) => { setSelectedStyle('borderColor', e.currentTarget.value); setSelectedStyle('borderStyle', 'solid'); }} /></div></div>
              {/if}
            </section>

            <section class="inspector-section spacing-section">
              <div class="inspector-title"><span>Espaçamento</span><small>Use px, rem ou %</small></div>
              <div class="spacing-box">
                <span class="spacing-caption">MARGEM</span>
                <div class="spacing-row"><label>Topo</label><input type="text" value={selectedBlock.styles.marginTop || '0px'} oninput={(e) => setSelectedStyle('marginTop', e.currentTarget.value)} /><label>Base</label><input type="text" value={selectedBlock.styles.marginBottom || '0px'} oninput={(e) => setSelectedStyle('marginBottom', e.currentTarget.value)} /></div>
                <div class="padding-box"><span class="spacing-caption">PADDING</span><div class="spacing-row"><label>Topo</label><input type="text" value={selectedBlock.styles.paddingTop || '0px'} oninput={(e) => setSelectedStyle('paddingTop', e.currentTarget.value)} /><label>Base</label><input type="text" value={selectedBlock.styles.paddingBottom || '0px'} oninput={(e) => setSelectedStyle('paddingBottom', e.currentTarget.value)} /></div></div>
              </div>
            </section>
          </div>
        {/if}
      </div>
    </aside>
  </div>
</div>

<style>
  .builder-root {
    display: flex;
    flex-direction: column;
    height: 100dvh;
    background: #f8fafc;
    font-family: Inter, sans-serif;
    overflow: hidden;
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    z-index: 9999;
  }

  /* TOPBAR */
  .builder-topbar {
    height: 56px;
    background: #ffffff;
    border-bottom: 1px solid #e5e7eb;
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0 1rem;
    flex-shrink: 0;
  }

  .topbar-left {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    max-width: 35%;
  }

  .back-link {
    color: #4b5563;
    display: flex;
    align-items: center;
    text-decoration: none;
    border-radius: 6px;
    padding: 0.25rem;
  }

  .back-link:hover {
    background: #f3f4f6;
  }

  .breadcrumb-txt {
    font-size: 0.8125rem;
    color: #6b7280;
    font-weight: 500;
  }

  .divider {
    color: #d1d5db;
    font-size: 0.8125rem;
  }

  .topbar-title-input {
    border: 1px solid transparent;
    font-size: 0.8125rem;
    color: #111827;
    font-weight: 600;
    padding: 0.25rem 0.5rem;
    background: transparent;
    border-radius: 6px;
    width: 200px;
    outline: none;
  }

  .topbar-title-input:focus {
    border-color: #d1d5db;
    background: #f9fafb;
  }

  .topbar-center {
    display: flex;
    gap: 0.25rem;
    background: #f3f4f6;
    padding: 0.25rem;
    border-radius: 8px;
  }

  .device-btn {
    border: none;
    background: transparent;
    padding: 0.375rem 0.75rem;
    border-radius: 6px;
    color: #4b5563;
    cursor: pointer;
    display: flex;
    align-items: center;
  }

  .device-btn.active {
    background: #ffffff;
    color: #111827;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  }

  .status-select {
    height: 36px;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 0 0.5rem;
    font-size: 0.8rem;
    font-weight: 600;
    background: #fff;
    color: #111827;
    cursor: pointer;
  }

  .components-hint {
    font-size: 0.75rem;
    color: #6b7280;
    margin: 0 0 0.75rem;
    line-height: 1.4;
  }

  .template-list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .template-card {
    text-align: left;
    border: 1px solid #e5e7eb;
    background: #fff;
    border-radius: 10px;
    padding: 0.75rem 0.85rem;
    cursor: pointer;
    transition: border-color 0.15s, box-shadow 0.15s;
  }

  .template-card:hover {
    border-color: #3b82f6;
    box-shadow: 0 2px 8px rgba(59, 130, 246, 0.12);
  }

  .template-card strong {
    display: block;
    font-size: 0.85rem;
    margin-bottom: 0.2rem;
    color: #111827;
  }

  .template-card span {
    font-size: 0.75rem;
    color: #6b7280;
    line-height: 1.35;
  }

  .dnd-hint {
    font-size: 0.72rem;
    color: #6b7280;
    margin: 0 0 0.75rem;
    line-height: 1.4;
    padding: 0 0.15rem;
  }

  .builder-canvas-wrapper.is-drag-over {
    outline: 2px solid #60a5fa;
    outline-offset: -4px;
    box-shadow: inset 0 0 0 7px rgba(96, 165, 250, 0.08);
  }

  .canvas-tree-wrap {
    position: relative;
    min-height: 280px;
  }

  .canvas-tree-wrap.drop-active {
    background: rgba(239, 246, 255, 0.72);
  }

  .canvas-drop-banner {
    position: absolute;
    left: 50%;
    top: 50%;
    transform: translate(-50%, -50%);
    z-index: 40;
    pointer-events: none;
    border: 3px solid #fff;
    background: linear-gradient(135deg, #2563eb, #1d4ed8);
    color: #fff;
    font-size: 0.85rem;
    font-weight: 700;
    padding: 0.65rem 1.25rem;
    border-radius: 999px;
    box-shadow: 0 10px 30px rgba(29, 78, 216, 0.35), 0 0 0 5px rgba(59, 130, 246, 0.14);
  }

  .element-item {
    cursor: grab;
    user-select: none;
    -webkit-user-select: none;
    touch-action: none;
    -webkit-user-drag: element;
  }

  .element-item:active {
    cursor: grabbing;
    opacity: 0.85;
  }

  .element-item.is-palette-dragging {
    opacity: 0.45;
    transform: scale(0.96);
    border-color: #3b82f6;
    background: #eff6ff;
  }

  :global(body.lp-dnd-active) {
    cursor: grabbing !important;
  }

  :global(body.lp-dnd-active *) {
    cursor: grabbing !important;
  }

  :global(body.lp-dnd-active .builder-canvas-wrapper) {
    outline: 2px solid #93c5fd;
    outline-offset: -4px;
  }



  .field-hint {
    font-size: 0.72rem;
    color: #6b7280;
    margin: 0.35rem 0 0;
    line-height: 1.35;
  }

  .inline-row {
    display: flex;
    gap: 0.35rem;
    margin-bottom: 0.35rem;
  }

  .inline-row input {
    flex: 1;
  }

  .mini-btn {
    border: 1px solid #e5e7eb;
    background: #f9fafb;
    border-radius: 6px;
    padding: 0.25rem 0.5rem;
    font-size: 0.75rem;
    cursor: pointer;
  }

  .mini-btn.add {
    margin-top: 0.35rem;
    width: 100%;
    background: #eff6ff;
    border-color: #bfdbfe;
    color: #1d4ed8;
    font-weight: 600;
  }

  .faq-editor-card {
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 0.65rem;
    margin-bottom: 0.5rem;
    background: #fafafa;
  }

  .checkbox-row label {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    font-weight: 500;
    text-transform: none;
    letter-spacing: 0;
  }

  .topbar-right {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    position: relative;
  }

  .history-btn {
    border: none;
    background: transparent;
    color: #4b5563;
    cursor: pointer;
    padding: 0.375rem;
    border-radius: 6px;
    display: flex;
    align-items: center;
  }

  .history-btn:disabled {
    color: #d1d5db;
    cursor: not-allowed;
  }

  .history-btn:not(:disabled):hover {
    background: #f3f4f6;
  }

  .preview-btn {
    border: 1px solid #d1d5db;
    background: #ffffff;
    color: #374151;
    padding: 0.4375rem 0.875rem;
    font-size: 0.8125rem;
    font-weight: 600;
    border-radius: 6px;
    cursor: pointer;
    text-decoration: none;
  }

  .preview-btn:hover {
    background: #f9fafb;
  }

  .save-btn {
    border: none;
    background: #111827;
    color: #ffffff;
    padding: 0.5rem 1.25rem;
    font-size: 0.8125rem;
    font-weight: 600;
    border-radius: 6px;
    cursor: pointer;
    transition: background 150ms;
  }

  .save-btn:hover {
    background: #1f2937;
  }

  .save-toast {
    position: absolute;
    bottom: -45px;
    right: 0;
    padding: 0.375rem 0.75rem;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 600;
    z-index: 200;
  }

  .save-toast.success {
    background: #d1fae5;
    color: #065f46;
    border: 1px solid #a7f3d0;
  }

  /* WORKSPACE */
  .builder-workspace {
    display: flex;
    flex: 1;
    overflow: hidden;
  }

  .left-sidebar {
    width: 280px;
    background: #ffffff;
    border-right: 1px solid #e5e7eb;
    display: flex;
    flex-direction: column;
    flex-shrink: 0;
  }

  .right-sidebar {
    width: 340px;
    background: #ffffff;
    border-left: 1px solid #e2e8f0;
    display: flex;
    flex-direction: column;
    flex-shrink: 0;
  }

  .sidebar-tabs {
    display: flex;
    border-bottom: 1px solid #e2e8f0;
    background: #f8fafc;
    flex-shrink: 0;
  }

  .tab-btn {
    flex: 1;
    border: none;
    background: transparent;
    padding: 0.875rem 0.5rem;
    font-size: 0.8125rem;
    font-weight: 600;
    color: #64748b;
    cursor: pointer;
    border-bottom: 2px solid transparent;
    transition: all 0.15s ease;
  }

  .tab-btn:hover {
    color: #0f172a;
    background: rgba(241, 245, 249, 0.5);
  }

  .tab-btn.active {
    color: #2563eb;
    border-bottom-color: #2563eb;
    background: #ffffff;
  }

  .sidebar-subtabs {
    display: flex;
    gap: 0.5rem;
    padding: 0.75rem 1rem;
    border-bottom: 1px solid #f3f4f6;
  }

  .subtab-btn {
    border: none;
    background: #f3f4f6;
    padding: 0.375rem 0.75rem;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 600;
    color: #4b5563;
    cursor: pointer;
  }

  .subtab-btn.active {
    background: #eff6ff;
    color: #2563eb;
  }

  .elements-group-list {
    padding: 1rem;
    overflow-y: auto;
    flex: 1;
  }

  .group-title {
    font-size: 0.6875rem;
    font-weight: 700;
    color: #9ca3af;
    letter-spacing: 0.05em;
    display: block;
    margin-bottom: 0.75rem;
  }

  .elements-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 0.5rem;
  }

  .element-item {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 0.75rem;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 0.25rem;
    cursor: grab;
    transition: all 150ms;
  }

  .element-item:hover {
    background: #f8fafc;
    border-color: #3b82f6;
  }

  .elem-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 24px;
    height: 24px;
    color: #64748b;
    transition: color 0.15s ease;
  }

  .element-item:hover .elem-icon {
    color: #2563eb;
  }

  .elem-icon :global(svg) {
    width: 20px;
    height: 20px;
    stroke-width: 1.75;
    transition: transform 0.15s ease;
  }

  .element-item:hover .elem-icon :global(svg) {
    transform: scale(1.08);
  }

  .elem-name {
    font-size: 0.72rem;
    font-weight: 500;
    color: #475569;
  }

  /* CANVAS (Center) */
  .builder-canvas-wrapper {
    flex: 1;
    display: flex;
    align-items: flex-start;
    justify-content: center;
    padding: 2rem;
    overflow-y: auto;
    background: #f1f5f9;
  }

  .builder-canvas-frame {
    background: #ffffff;
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.04), 0 4px 6px -2px rgba(0, 0, 0, 0.02);
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    min-height: 800px;
    transition: width 200ms ease-in-out;
  }

  .builder-canvas-frame.desktop {
    width: 100%;
  }

  .builder-canvas-frame.mobile {
    width: 375px;
  }

  .header-link-row {
    display: grid;
    grid-template-columns: 1fr 1fr auto;
    gap: 0.35rem;
    margin-bottom: 0.4rem;
  }

  .header-link-row input {
    min-width: 0;
  }

  .canvas-section {
    position: relative;
    border: 1px dashed transparent;
    transition: border-color 150ms;
  }

  .canvas-section:hover {
    border-color: #cbd5e1;
  }

  .canvas-section.selected {
    border-color: #3b82f6;
    border-style: solid;
  }

  .canvas-element-wrapper {
    position: relative;
    border: 1px dashed transparent;
    margin: 2px 0;
    transition: border-color 150ms;
  }

  .canvas-element-wrapper:hover {
    border-color: #93c5fd;
  }

  .canvas-element-wrapper.selected {
    border-color: #3b82f6;
    border-style: solid;
  }

  /* Controles de Bloco */
  .block-controls-overlay {
    position: absolute;
    top: -24px;
    right: 8px;
    background: #3b82f6;
    color: #ffffff;
    border-radius: 4px 4px 0 0;
    font-size: 0.6875rem;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 0.25rem;
    padding: 2px 6px;
    z-index: 100;
  }

  .block-controls-overlay.inner {
    background: #3b82f6;
  }

  .block-controls-overlay button {
    background: transparent;
    border: none;
    color: #ffffff;
    font-size: 0.75rem;
    font-weight: bold;
    cursor: pointer;
    padding: 0 4px;
    display: flex;
    align-items: center;
  }

  .block-controls-overlay button:hover {
    color: #f3f4f6;
  }

  .block-controls-overlay button.delete-btn {
    color: #fca5a5;
    margin-left: 2px;
  }

  .block-label {
    margin-right: 4px;
    opacity: 0.9;
  }

  .element-box {
    width: 100%;
  }

  .placeholder-img-mock {
    width: 100%;
    height: 380px;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .img-mock-icon {
    font-size: 3.5rem;
    opacity: 0.2;
  }

  .video-container {
    position: relative;
    padding-bottom: 56.25%;
    height: 0;
    overflow: hidden;
  }

  .video-container iframe {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
  }

  .section-empty-placeholder {
    padding: 2rem;
    border: 2px dashed #cbd5e1;
    border-radius: 8px;
    color: #64748b;
    font-size: 0.8125rem;
    text-align: center;
  }

  /* PAINEL DIREITO */
  .settings-panel-content {
    flex: 1;
    overflow-y: auto;
    background: #ffffff;
  }

  .settings-form {
    padding: 1.25rem;
    display: flex;
    flex-direction: column;
    gap: 1.25rem;
  }

  .settings-group-title {
    font-size: 0.8125rem;
    font-weight: 700;
    color: #1e293b;
    border-bottom: 1px solid #f1f5f9;
    padding-bottom: 0.375rem;
    margin: 0;
  }

  .form-group {
    display: flex;
    flex-direction: column;
    gap: 0.375rem;
  }

  .form-group label {
    font-size: 0.75rem;
    font-weight: 600;
    color: #475569;
  }

  .form-group input[type="text"], .form-group select, .form-group textarea {
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 0.5rem;
    font-size: 0.8125rem;
    background: #ffffff;
    color: #0f172a;
    outline: none;
    transition: border-color 0.15s ease, box-shadow 0.15s ease;
  }

  .form-group input[type="text"]:focus, .form-group select:focus, .form-group textarea:focus {
    border-color: #3b82f6;
    box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.15);
  }

  .form-group input[type="color"] {
    border: 1px solid #cbd5e1;
    background: transparent;
    padding: 0;
    width: 100%;
    height: 32px;
    border-radius: 6px;
    cursor: pointer;
  }

  /* SEO Image Card */
  .image-upload-mock-card {
    border: 1px dashed #cbd5e1;
    border-radius: 8px;
    background: #f8fafc;
    padding: 1.5rem 1rem;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    position: relative;
  }

  .upload-icon-svg {
    font-size: 1.5rem;
    color: #64748b;
    margin-bottom: 0.375rem;
  }

  .upload-txt-main {
    font-size: 0.75rem;
    font-weight: 700;
    color: #334155;
  }

  .upload-txt-sub {
    font-size: 0.625rem;
    color: #94a3b8;
  }

  .hidden-upload-input {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    opacity: 0;
    cursor: pointer;
  }

  .social-img-preview {
    max-width: 100%;
    max-height: 120px;
    border-radius: 4px;
  }

  /* File Upload Wrapper */
  .upload-btn-wrapper {
    position: relative;
    overflow: hidden;
    display: inline-block;
    margin-top: 0.25rem;
  }

  .upload-btn-wrapper input[type=file] {
    font-size: 100px;
    position: absolute;
    left: 0;
    top: 0;
    opacity: 0;
    cursor: pointer;
  }

  .upload-file-label {
    border: 1px solid #cbd5e1;
    background-color: #f8fafc;
    color: #334155;
    padding: 0.4375rem 1rem;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 600;
    cursor: pointer;
    display: inline-block;
  }

  .upload-file-label:hover {
    background-color: #f1f5f9;
  }

  /* HTML Code Editor Styling */
  .html-editor-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.35rem;
  }

  .html-badge-advanced {
    font-size: 9px;
    font-weight: 700;
    background: #eff6ff;
    color: #1d4ed8;
    border: 1px solid #bfdbfe;
    padding: 2px 6px;
    border-radius: 4px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .html-editor-help {
    font-size: 11px;
    color: #6b7280;
    line-height: 1.4;
    margin: 0 0 0.5rem 0;
  }

  .code-editor-textarea {
    font-family: 'Consolas', 'Monaco', 'Andale Mono', 'Ubuntu Mono', monospace !important;
    font-size: 11px !important;
    line-height: 1.5 !important;
    background: #1e1e1e !important;
    color: #d4d4d4 !important;
    border: 1px solid #2d2d2d !important;
    border-radius: 8px !important;
    padding: 10px !important;
    resize: vertical;
    width: 100%;
    box-sizing: border-box;
    box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.15);
  }

  .code-editor-textarea:focus {
    outline: none !important;
    border-color: #3b82f6 !important;
    box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.15), 0 0 0 2px rgba(59, 130, 246, 0.15) !important;
  }

  /* Accordion Styling (Puck-style) */
  .lp-accordion {
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    background: #ffffff;
    margin-bottom: 0.75rem;
    overflow: hidden;
    transition: box-shadow 0.15s ease;
  }

  .lp-accordion[open] {
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04);
    border-color: #cbd5e1;
  }

  .lp-accordion-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.75rem 1rem;
    background: #f8fafc;
    cursor: pointer;
    font-weight: 600;
    font-size: 0.8125rem;
    color: #334155;
    user-select: none;
    -webkit-user-select: none;
    list-style: none;
  }

  .lp-accordion-header::-webkit-details-marker {
    display: none;
  }

  .lp-accordion-header:hover {
    background: #f1f5f9;
    color: #0f172a;
  }

  .lp-accordion-title {
    display: flex;
    align-items: center;
    gap: 0.375rem;
  }

  .lp-accordion-icon {
    font-size: 0.75rem;
    color: #64748b;
    transition: transform 0.2s ease;
  }

  .lp-accordion[open] .lp-accordion-icon {
    transform: rotate(180deg);
  }

  .lp-accordion-content {
    padding: 1rem;
    border-top: 1px solid #e2e8f0;
    background: #ffffff;
  }

  .lp-accordion-divider {
    border: 0;
    border-top: 1px solid #e2e8f0;
    margin: 1rem 0;
  }

  /* Rich Text Editor Styling (Puck-style) */
  .editor-toggle-pills {
    display: inline-flex;
    background: #f1f5f9;
    padding: 2px;
    border-radius: 6px;
    gap: 2px;
  }

  .toggle-pill-btn {
    border: none;
    background: transparent;
    color: #475569;
    font-size: 0.7rem;
    font-weight: 600;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.15s ease;
  }

  .toggle-pill-btn:hover {
    color: #0f172a;
  }

  .toggle-pill-btn.active {
    background: #ffffff;
    color: #2563eb;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
  }

  .visual-editor-toolbar {
    display: flex;
    flex-wrap: wrap;
    gap: 2px;
    background: #f8fafc;
    border: 1px solid #cbd5e1;
    border-bottom: none;
    border-radius: 8px 8px 0 0;
    padding: 4px;
  }

  .toolbar-btn {
    border: none;
    background: transparent;
    color: #475569;
    font-size: 11px;
    font-weight: 600;
    height: 24px;
    padding: 0 6px;
    border-radius: 4px;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    transition: all 0.15s ease;
  }

  .toolbar-btn:hover {
    background: #e2e8f0;
    color: #0f172a;
  }

  .visual-editor-container {
    background: #ffffff !important;
    color: #0f172a !important;
    border: 1px solid #cbd5e1;
    border-radius: 0 0 8px 8px;
    padding: 10px;
    min-height: 180px;
    max-height: 350px;
    overflow-y: auto;
    outline: none;
    font-size: 13px;
    line-height: 1.5;
    box-sizing: border-box;
    transition: border-color 0.15s ease, box-shadow 0.15s ease;
  }

  .visual-editor-container:focus {
    border-color: #3b82f6;
    box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.15);
  }

  /* Font size normalization to prevent layout breaking with massive title styles */
  .visual-editor-container :global(*) {
    font-size: 13px !important;
    line-height: 1.5 !important;
    font-family: inherit !important;
  }

  .visual-editor-container :global(h1),
  .visual-editor-container :global(h2),
  .visual-editor-container :global(h3),
  .visual-editor-container :global(h4) {
    font-size: 15px !important;
    font-weight: 700 !important;
    margin: 0.75rem 0 0.4rem 0 !important;
    color: #0f172a !important;
  }

  .visual-editor-container :global(p) {
    margin: 0 0 0.75rem 0 !important;
  }

  .visual-editor-container :global(ul), .visual-editor-container :global(ol) {
    margin: 0 0 0.75rem 1.25rem !important;
    padding: 0;
  }

  .visual-editor-container :global(img) {
    max-width: 100%;
    height: auto;
    border-radius: 6px;
    margin: 0.5rem 0;
  }

  .visual-editor-container :global(a) {
    color: #2563eb;
    text-decoration: underline;
  }

  /* Resizable sidebar handle styling */
  .right-sidebar {
    position: relative;
  }

  .sidebar-resize-handle {
    position: absolute;
    left: -3px;
    top: 0;
    bottom: 0;
    width: 6px;
    cursor: ew-resize;
    z-index: 1000;
    background: transparent;
    transition: background-color 0.15s ease;
  }

  .sidebar-resize-handle:hover,
  .sidebar-resize-handle.active {
    background-color: #2563eb;
    box-shadow: 0 0 4px rgba(37, 99, 235, 0.4);
  }

  .premium-elements .element-item { border-color: #bfdbfe; background: linear-gradient(145deg, #ffffff, #eff6ff); }
  .premium-elements .elem-icon { color: #2563eb; font-size: 1.25rem; font-weight: 900; }
  .content-picker { display: grid; gap: .4rem; max-height: 280px; overflow: auto; padding: .35rem; border: 1px solid #e2e8f0; border-radius: 10px; background: #f8fafc; }
  .content-picker-item { display: flex; align-items: flex-start; gap: .55rem; padding: .55rem; border-radius: 7px; background: white; font-size: .8rem; line-height: 1.35; cursor: pointer; }
  .content-picker-item input { margin-top: .15rem; }
  .form-label { display: block; margin-bottom: .4rem; color: #334155; font-size: .75rem; font-weight: 700; }

  /* Premium property inspector */
  .sidebar-tabs { padding: .5rem; gap: .35rem; background: #f8fafc; }
  .tab-btn { display: inline-flex; align-items: center; justify-content: center; gap: .4rem; padding: .65rem .45rem; border: 1px solid transparent; border-radius: 9px; }
  .tab-btn.active { color: #1d4ed8; border-color: #dbeafe; border-bottom-color: #dbeafe; background: #fff; box-shadow: 0 3px 12px rgba(15,23,42,.06); }
  .tab-btn:disabled { cursor: not-allowed; opacity: .42; }
  .tab-dot { width: 6px; height: 6px; border-radius: 50%; background: #cbd5e1; }
  .tab-btn.active .tab-dot { background: #2563eb; box-shadow: 0 0 0 3px #dbeafe; }
  .settings-panel-content { background: linear-gradient(180deg,#fff 0,#f8fafc 100%); }
  .settings-form { padding: 1rem; gap: .85rem; }
  .panel-heading { padding: .35rem .25rem .7rem; }
  .panel-heading h4 { margin: .25rem 0 .3rem; color: #0f172a; font-size: 1.12rem; letter-spacing: -.025em; }
  .panel-heading p { margin: 0; color: #64748b; font-size: .72rem; line-height: 1.5; }
  .panel-kicker { color: #2563eb; font-size: .6rem; font-weight: 900; letter-spacing: .14em; }
  .lp-accordion { margin-bottom: .1rem; border-radius: 13px; border-color: #e2e8f0; box-shadow: 0 3px 14px rgba(15,23,42,.035); }
  .lp-accordion[open] { border-color: #bfdbfe; box-shadow: 0 8px 26px rgba(37,99,235,.08); }
  .lp-accordion-header { min-height: 62px; padding: .8rem; background: #fff; }
  .lp-accordion[open] .lp-accordion-header { background: linear-gradient(135deg,#eff6ff,#fff); }
  .lp-accordion-title { gap: .7rem; min-width: 0; }
  .lp-accordion-title > span { display: grid; gap: .12rem; color: #0f172a; font-size: .78rem; }
  .lp-accordion-title small { color: #94a3b8; font-size: .62rem; font-weight: 500; }
  .accordion-symbol { display: grid; place-items: center; width: 34px; height: 34px; flex: 0 0 34px; border: 1px solid #bfdbfe; border-radius: 10px; background: #eff6ff; color: #2563eb; font-size: .6rem; letter-spacing: .04em; }
  .lp-accordion-icon { display: grid; place-items: center; width: 24px; height: 24px; border-radius: 7px; background: #f1f5f9; font-size: 1rem; }
  .lp-accordion-content { padding: 1rem; border-color: #dbeafe; }
  .form-group { gap: .45rem; }
  .form-group label,.form-label { color: #334155; font-size: .68rem; font-weight: 750; letter-spacing: .015em; }
  .form-group input[type="text"],.form-group select,.form-group textarea { min-height: 38px; padding: .6rem .7rem; border-color: #dbe3ee; border-radius: 9px; background: #fff; }
  .form-group textarea { min-height: 82px; }
  .choice-grid { display: grid; gap: .45rem; }
  .choice-grid button { position: relative; display: flex; flex-direction: column; align-items: flex-start; gap: .1rem; min-width: 0; padding: .65rem; border: 1px solid #e2e8f0; border-radius: 10px; background: #fff; color: #334155; cursor: pointer; }
  .choice-grid button:hover { border-color: #93c5fd; }
  .choice-grid button.active { border-color: #2563eb; background: #eff6ff; box-shadow: inset 0 0 0 1px #2563eb; }
  .choice-grid b { font-size: .67rem; }
  .choice-grid small { color: #94a3b8; font-size: .56rem; }
  .status-choice { grid-template-columns: 1fr 1fr; }
  .status-choice button { padding-left: 1.65rem; }
  .status-light { position: absolute; top: .75rem; left: .65rem; width: 7px; height: 7px; border-radius: 50%; }
  .status-light.draft { background: #f59e0b; box-shadow: 0 0 0 3px #fef3c7; }
  .status-light.live { background: #10b981; box-shadow: 0 0 0 3px #d1fae5; }
  .width-choice { grid-template-columns: repeat(3,1fr); }
  .width-choice button { align-items: center; padding: .55rem .2rem; }
  .width-icon { display: block; height: 18px; border: 2px solid #94a3b8; border-radius: 3px; }
  .width-icon.narrow { width: 17px; }.width-icon.normal { width: 25px; }.width-icon.wide { width: 34px; }
  .width-choice button.active .width-icon { border-color: #2563eb; background: #dbeafe; }
  .color-control { display: grid; grid-template-columns: 44px 1fr; gap: .45rem; }
  .color-control input[type="color"] { width: 44px; height: 38px; padding: 3px; border: 1px solid #dbe3ee; border-radius: 9px; background: #fff; }
  .color-control input[type="text"] { min-width: 0; font-family: ui-monospace,Consolas,monospace; text-transform: uppercase; }
  .style-inspector { padding-bottom: 2rem; }
  .style-heading { padding-bottom: .35rem; }
  .inspector-section { display: grid; gap: .7rem; padding: .85rem; border: 1px solid #e2e8f0; border-radius: 13px; background: #fff; box-shadow: 0 4px 18px rgba(15,23,42,.035); }
  .inspector-title { display: flex; align-items: center; justify-content: space-between; padding-bottom: .55rem; border-bottom: 1px solid #f1f5f9; }
  .inspector-title span { color: #0f172a; font-size: .75rem; font-weight: 800; }
  .inspector-title small { color: #94a3b8; font-size: .58rem; font-weight: 650; text-transform: uppercase; letter-spacing: .08em; }
  .preset-grid { display: grid; grid-template-columns: repeat(3,1fr); gap: .45rem; }
  .preset-grid button { display: grid; gap: .4rem; padding: .45rem; border: 1px solid #e2e8f0; border-radius: 9px; background: #fff; color: #475569; font-size: .61rem; cursor: pointer; }
  .preset-grid button:hover { border-color: #60a5fa; color: #1d4ed8; transform: translateY(-1px); }
  .preset-preview { display: block; height: 32px; border-radius: 6px; }
  .preset-preview.clean { border: 1px dashed #cbd5e1; background: #fff; }.preset-preview.card { border: 1px solid #e2e8f0; background: #fff; box-shadow: 0 4px 10px #0f172a14; }.preset-preview.dark { background: linear-gradient(135deg,#0f172a,#1e3a8a); }
  .segmented-control { display: grid; grid-template-columns: repeat(3,1fr); padding: 3px; border-radius: 10px; background: #f1f5f9; }
  .segmented-control button { display: grid; place-items: center; gap: .1rem; min-height: 44px; border: 0; border-radius: 8px; background: transparent; color: #64748b; font-size: 1.15rem; cursor: pointer; }
  .segmented-control button:nth-child(2) { text-align: center; }.segmented-control button:nth-child(3) { text-align: right; }
  .segmented-control button span { font-size: .55rem; font-weight: 700; }
  .segmented-control button.active { background: #fff; color: #2563eb; box-shadow: 0 2px 8px rgba(15,23,42,.09); }
  .two-field-grid { display: grid; grid-template-columns: 1fr 1fr; gap: .55rem; }
  .unit-input { display: grid; grid-template-columns: 1fr 35px; align-items: center; border: 1px solid #dbe3ee; border-radius: 9px; overflow: hidden; background: #fff; }
  .unit-input input { min-width: 0; min-height: 36px; padding: .5rem .6rem; border: 0; outline: 0; font-size: .72rem; }
  .unit-input span { color: #94a3b8; font-size: .5rem; font-weight: 800; text-align: center; }
  .spacing-box { padding: .55rem; border: 1px dashed #cbd5e1; border-radius: 10px; background: #f8fafc; }
  .spacing-caption { display: block; margin-bottom: .4rem; color: #94a3b8; font-size: .5rem; font-weight: 900; letter-spacing: .1em; }
  .spacing-row { display: grid; grid-template-columns: auto 1fr auto 1fr; align-items: center; gap: .35rem; }
  .spacing-row label { color: #64748b; font-size: .55rem; }
  .spacing-row input { min-width: 0; width: 100%; padding: .38rem; border: 1px solid #dbe3ee; border-radius: 6px; font-size: .63rem; box-sizing: border-box; }
  .padding-box { margin-top: .55rem; padding: .55rem; border: 1px solid #bfdbfe; border-radius: 8px; background: #eff6ff; }
</style>
