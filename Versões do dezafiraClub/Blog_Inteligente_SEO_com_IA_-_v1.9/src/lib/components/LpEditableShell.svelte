<script lang="ts">
  import type { Snippet } from 'svelte';
  import { t } from '$lib/i18n';
  import {
    acceptsLandingChildren,
    getLandingDropPosition,
    type LandingDropPosition
  } from '$lib/landing-dnd';

  type DropPosition = LandingDropPosition;

  let {
    tag = 'div',
    blockId,
    blockType,
    editable = false,
    selected = false,
    lang = 'pt',
    dropTargetId = null,
    dropPosition = null as DropPosition | null,
    className = '',
    style = undefined as string | undefined,
    onSelect = undefined as undefined | ((id: string, e: MouseEvent) => void),
    onDrop = undefined as
      | undefined
      | ((targetId: string | null, position: DropPosition, e: DragEvent) => void),
    onDragOverTarget = undefined as
      | undefined
      | ((targetId: string | null, position: DropPosition, e: DragEvent) => void),
    onBlockDragStart = undefined as undefined | ((id: string, e: DragEvent) => void),
    onDragEnd = undefined as undefined | ((e: DragEvent) => void),
    onMoveBlock = undefined as undefined | ((id: string, direction: 'up' | 'down') => void),
    onDuplicateBlock = undefined as undefined | ((id: string) => void),
    onDeleteBlock = undefined as undefined | ((id: string) => void),
    children
  }: {
    tag?: string;
    blockId: string;
    blockType: string;
    editable?: boolean;
    selected?: boolean;
    lang?: string;
    dropTargetId?: string | null;
    dropPosition?: DropPosition | null;
    className?: string;
    style?: string;
    onSelect?: (id: string, e: MouseEvent) => void;
    onDrop?: (targetId: string | null, position: DropPosition, e: DragEvent) => void;
    onDragOverTarget?: (targetId: string | null, position: DropPosition, e: DragEvent) => void;
    onBlockDragStart?: (id: string, e: DragEvent) => void;
    onDragEnd?: (e: DragEvent) => void;
    onMoveBlock?: (id: string, direction: 'up' | 'down') => void;
    onDuplicateBlock?: (id: string) => void;
    onDeleteBlock?: (id: string) => void;
    children?: Snippet;
  } = $props();

  function positionFromEvent(e: DragEvent): DropPosition {
    const el = e.currentTarget as HTMLElement | null;
    if (!el) return acceptsLandingChildren(blockType) ? 'inside' : 'after';
    const rect = el.getBoundingClientRect();
    return getLandingDropPosition(blockType, rect.height, e.clientY - rect.top);
  }

  function markedDropPosition(e: DragEvent): DropPosition {
    const el = e.currentTarget as HTMLElement | null;
    if (el?.classList.contains('lp-drop-before')) return 'before';
    if (el?.classList.contains('lp-drop-after')) return 'after';
    if (el?.classList.contains('lp-drop-inside')) return 'inside';
    return positionFromEvent(e);
  }

  function handleSelect(e: MouseEvent) {
    if (!editable || !onSelect) return;
    if ((e.target as HTMLElement)?.closest?.('.lp-block-toolbar')) return;
    e.stopPropagation();
    onSelect(blockId, e);
  }

  function handleDragOver(e: DragEvent) {
    if (!editable) return;
    e.preventDefault();
    e.stopPropagation();
    if (e.dataTransfer) {
      e.dataTransfer.dropEffect = e.dataTransfer.effectAllowed === 'move' ? 'move' : 'copy';
    }
    onDragOverTarget?.(blockId, positionFromEvent(e), e);
  }

  function handleDrop(e: DragEvent) {
    if (!editable || !onDrop) return;
    e.preventDefault();
    e.stopPropagation();
    // Use the exact highlighted destination. Recalculating after the browser
    // paints the indicator can change the measured target at the last moment.
    onDrop(blockId, markedDropPosition(e), e);
  }

  function handleHandleDragStart(e: DragEvent) {
    if (!editable || !onBlockDragStart) return;
    e.stopPropagation();
    // Required by Firefox; parent also writes structured payload
    if (e.dataTransfer) {
      e.dataTransfer.setData('text/plain', `block:${blockId}`);
      e.dataTransfer.effectAllowed = 'move';
    }
    const handle = e.currentTarget as HTMLElement;
    handle.classList.add('is-dragging-handle');
    // Mark the shell for visual feedback without reactive parent state
    const shell = handle.closest('.lp-shell') as HTMLElement | null;
    shell?.classList.add('lp-is-dragging');
    onBlockDragStart(blockId, e);
  }

  function handleHandleDragEnd(e: DragEvent) {
    const handle = e.currentTarget as HTMLElement;
    handle.classList.remove('is-dragging-handle');
    handle.closest('.lp-shell')?.classList.remove('lp-is-dragging');
    document.querySelectorAll('.lp-is-dragging').forEach((n) => n.classList.remove('lp-is-dragging'));
    onDragEnd?.(e);
  }

  const dropClass = $derived(
    editable && dropTargetId === blockId && dropPosition ? `lp-drop-${dropPosition}` : ''
  );

  const blockLabel = $derived(
    ({
      section: t(lang, 'admin.landing_pages.builder.block_section'),
      container: t(lang, 'admin.landing_pages.builder.block_container'),
      columns: t(lang, 'admin.landing_pages.builder.type_columns'),
      column: t(lang, 'admin.landing_pages.builder.type_column'),
      text: t(lang, 'admin.landing_pages.builder.block_text'),
      image: t(lang, 'admin.landing_pages.builder.block_image'),
      button: t(lang, 'admin.landing_pages.builder.block_button'),
      video: t(lang, 'admin.landing_pages.builder.block_video'),
      divider: t(lang, 'admin.landing_pages.builder.block_divider'),
      spacer: t(lang, 'admin.landing_pages.builder.type_spacer'),
      html: 'HTML',
      cta: 'CTA',
      testimonial: t(lang, 'admin.landing_pages.builder.block_testimonial'),
      pricing: t(lang, 'admin.landing_pages.builder.block_pricing'),
      faq: 'FAQ',
      hero: 'Hero premium',
      'product-showcase': 'Produto em destaque',
      'posts-grid': 'Grade de posts',
      'trust-bar': 'Barra de confiança'
    } as Record<string, string>)[blockType] || blockType
  );

  const dragTitle = $derived(t(lang, 'admin.landing_pages.builder.drag_to_reorder'));
</script>

<svelte:element
  this={tag}
  class="lp-shell {className} {dropClass}"
  class:lp-selected={editable && selected}
  class:lp-editable={editable}
  style={style}
  role={editable ? 'group' : undefined}
  data-block-id={blockId}
  data-block-type={blockType}
  onclick={handleSelect}
  ondragover={handleDragOver}
  ondragenter={handleDragOver}
  ondrop={handleDrop}
>
  {#if editable}
    {#if selected}
      <!-- Unified toolbar when selected (Puck-style) -->
      <div class="lp-block-toolbar" onclick={(e) => e.stopPropagation()} role="toolbar" tabindex="-1" aria-label="Ações do bloco">
        <button
          type="button"
          class="lp-toolbar-drag"
          draggable="true"
          title="{dragTitle}: {blockLabel}"
          aria-label={dragTitle}
          ondragstart={handleHandleDragStart}
          ondragend={handleHandleDragEnd}
        >
          <svg width="10" height="10" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" style="margin-right: 3px; display: inline-block; vertical-align: middle;">
            <circle cx="9" cy="6" r="1.6" />
            <circle cx="15" cy="6" r="1.6" />
            <circle cx="9" cy="12" r="1.6" />
            <circle cx="15" cy="12" r="1.6" />
            <circle cx="9" cy="18" r="1.6" />
            <circle cx="15" cy="18" r="1.6" />
          </svg>
          <span class="lp-toolbar-label">{blockLabel}</span>
        </button>
        
        {#if onMoveBlock}
          <button type="button" class="lp-tb-btn" onclick={() => onMoveBlock?.(blockId, 'up')} title={t(lang, 'admin.landing_pages.builder.move_up')}>▲</button>
          <button type="button" class="lp-tb-btn" onclick={() => onMoveBlock?.(blockId, 'down')} title={t(lang, 'admin.landing_pages.builder.move_down')}>▼</button>
        {/if}
        {#if onDuplicateBlock}
          <button type="button" class="lp-tb-btn duplicate-btn" onclick={() => onDuplicateBlock?.(blockId)} title={t(lang, 'admin.landing_pages.builder.duplicate') || 'Duplicar'}>❐</button>
        {/if}
        {#if onDeleteBlock}
          <button type="button" class="lp-tb-btn delete-btn" onclick={() => onDeleteBlock?.(blockId)} title={t(lang, 'admin.landing_pages.builder.delete')}>✕</button>
        {/if}
      </div>
    {/if}
    <span class="lp-drop-indicator" aria-hidden="true"></span>
  {/if}
  {@render children?.()}
</svelte:element>

<style>
  .lp-shell {
    position: relative;
    box-sizing: border-box;
    transition: outline 0.15s ease, outline-offset 0.15s ease;
  }

  .lp-editable {
    user-select: none;
    -webkit-user-select: none;
  }

  /* Highlight only the deepest hovered block; nested parent shells stay quiet. */
  .lp-editable:hover {
    outline: 1px solid rgba(37, 99, 235, 0.38);
    outline-offset: 2px;
    border-radius: 8px;
  }

  /* Strong border when selected */
  .lp-selected,
  .lp-editable.lp-selected:hover {
    outline: 2px solid #3b82f6;
    outline-offset: 3px;
    border-radius: 8px;
    box-shadow: 0 0 0 5px rgba(59, 130, 246, 0.08);
  }

  .lp-shell.lp-is-dragging {
    opacity: 0.28;
    outline: 2px dashed #3b82f6 !important;
    filter: saturate(0.55);
  }

  /* Unified floating block actions toolbar */
  .lp-block-toolbar {
    position: absolute;
    bottom: calc(100% + 9px);
    left: 8px;
    z-index: 100;
    display: inline-flex;
    align-items: center;
    background: #111827;
    color: #ffffff;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 10px;
    box-shadow: 0 10px 30px rgba(15, 23, 42, 0.28);
    height: 34px;
    padding: 3px;
    gap: 2px;
    box-sizing: border-box;
    font-family: inherit;
    user-select: none;
    -webkit-user-select: none;
  }

  .lp-toolbar-drag {
    display: inline-flex;
    align-items: center;
    height: 27px;
    padding: 0 10px;
    border: 0;
    background: linear-gradient(135deg, #3b82f6, #2563eb);
    color: #ffffff;
    border-radius: 7px;
    font-size: 9px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    cursor: grab;
    margin-right: 2px;
  }

  .lp-toolbar-drag:active {
    cursor: grabbing;
    background: #1e3a8a;
  }

  .lp-toolbar-label {
    line-height: 1;
    margin-left: 2px;
  }

  .lp-tb-btn {
    border: none;
    background: transparent;
    color: #ffffff;
    width: 27px;
    height: 27px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    border-radius: 7px;
    transition: background 0.15s ease, color 0.15s ease;
    font-size: 0.75rem;
    padding: 0;
  }

  .lp-tb-btn:hover {
    background: rgba(255, 255, 255, 0.15);
  }

  .lp-tb-btn.duplicate-btn {
    color: #93c5fd;
  }

  .lp-tb-btn.duplicate-btn:hover {
    background: rgba(59, 130, 246, 0.2);
    color: #3b82f6;
  }

  .lp-tb-btn.delete-btn {
    color: #fca5a5;
  }

  .lp-tb-btn.delete-btn:hover {
    background: #dc2626;
    color: #ffffff;
  }

  .lp-drop-indicator {
    display: none;
    position: absolute;
    left: 14px;
    right: 14px;
    height: 3px;
    border-radius: 4px;
    background: #2563eb;
    z-index: 45;
    pointer-events: none;
    box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.12), 0 4px 16px rgba(37, 99, 235, 0.3);
  }

  .lp-drop-indicator::before {
    content: '+';
    position: absolute;
    left: 50%;
    top: 50%;
    display: grid;
    place-items: center;
    width: 22px;
    height: 22px;
    transform: translate(-50%, -50%);
    border: 3px solid white;
    border-radius: 50%;
    background: #2563eb;
    color: white;
    font: 800 15px/1 system-ui;
    box-shadow: 0 3px 10px rgba(37, 99, 235, 0.35);
  }

  /* Classes may be applied via DOM during drag (non-reactive markers) */
  :global(.lp-shell.lp-drop-before) > .lp-drop-indicator {
    display: block;
    top: -2px;
  }

  :global(.lp-shell.lp-drop-after) > .lp-drop-indicator {
    display: block;
    bottom: -2px;
  }

  :global(.lp-shell.lp-drop-inside) {
    outline: 2px solid #3b82f6 !important;
    outline-offset: -3px;
    background-image: linear-gradient(0deg, rgba(219, 234, 254, 0.72), rgba(219, 234, 254, 0.72));
    border-radius: 10px;
  }

  :global(body.lp-dnd-active) .lp-block-toolbar {
    opacity: 0;
    pointer-events: none;
  }

  /* Give nested content room so the handle does not cover text */
  .lp-shell.lp-editable :global(.lp-container),
  .lp-shell.lp-editable :global(.lp-text),
  .lp-shell.lp-editable :global(.lp-cta-title),
  .lp-shell.lp-editable :global(.lp-plan-name) {
    /* keep content readable */
  }
</style>
