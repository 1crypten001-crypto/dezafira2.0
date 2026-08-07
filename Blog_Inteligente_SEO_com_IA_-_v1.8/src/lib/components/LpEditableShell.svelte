<script lang="ts">
  import type { Snippet } from 'svelte';
  import { t } from '$lib/i18n';

  type DropPosition = 'before' | 'after' | 'inside';

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

  function acceptsChildren(type: string) {
    return type === 'section' || type === 'container' || type === 'column' || type === 'columns';
  }

  function positionFromEvent(e: DragEvent): DropPosition {
    const el = e.currentTarget as HTMLElement | null;
    if (!el) return acceptsChildren(blockType) ? 'inside' : 'after';
    const rect = el.getBoundingClientRect();
    const ratio = rect.height > 0 ? (e.clientY - rect.top) / rect.height : 0.5;
    if (acceptsChildren(blockType)) {
      if (ratio < 0.2) return 'before';
      if (ratio > 0.8) return 'after';
      return 'inside';
    }
    return ratio < 0.5 ? 'before' : 'after';
  }

  function handleSelect(e: MouseEvent) {
    if (!editable || !onSelect) return;
    // Ignore clicks that originated on the drag handle
    if ((e.target as HTMLElement)?.closest?.('.lp-drag-handle')) return;
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
    onDrop(blockId, positionFromEvent(e), e);
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
      faq: 'FAQ'
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
      <div class="lp-block-toolbar" onclick={(e) => e.stopPropagation()} role="toolbar">
        <div
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
        </div>
        
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
    {:else}
      <!-- Hover drag handle when not selected -->
      <button
        type="button"
        class="lp-drag-handle"
        draggable="true"
        title="{dragTitle}: {blockLabel}"
        aria-label={dragTitle}
        ondragstart={handleHandleDragStart}
        ondragend={handleHandleDragEnd}
        onclick={(e) => e.stopPropagation()}
      >
        <svg width="10" height="10" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" style="margin-right: 3px;">
          <circle cx="9" cy="6" r="1.6" />
          <circle cx="15" cy="6" r="1.6" />
          <circle cx="9" cy="12" r="1.6" />
          <circle cx="15" cy="12" r="1.6" />
          <circle cx="9" cy="18" r="1.6" />
          <circle cx="15" cy="18" r="1.6" />
        </svg>
        <span class="lp-drag-handle-text">{blockLabel}</span>
      </button>
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

  /* Soft border on hover */
  .lp-editable:hover {
    outline: 1.5px dashed rgba(37, 99, 235, 0.45);
    outline-offset: 0px;
    border-radius: 4px;
  }

  /* Strong border when selected */
  .lp-selected,
  .lp-editable.lp-selected:hover {
    outline: 2px solid #2563eb;
    outline-offset: 0px;
    border-radius: 4px;
  }

  /* Tag style drag handle positioned above the block top-left */
  .lp-drag-handle {
    position: absolute;
    top: -22px;
    left: 0px;
    z-index: 50;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    height: 22px;
    padding: 0 8px;
    border: none;
    border-radius: 4px 4px 0 0;
    background: #2563eb;
    color: #ffffff;
    cursor: grab;
    box-shadow: 0 -2px 6px rgba(0, 0, 0, 0.12);
    opacity: 0;
    visibility: hidden;
    transition: opacity 0.15s ease-in-out, visibility 0.15s ease-in-out, background-color 0.15s ease;
    touch-action: none;
    -webkit-user-drag: element;
    font-family: var(--font-sans), system-ui, -apple-system, sans-serif;
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    white-space: nowrap;
    user-select: none;
    -webkit-user-select: none;
  }

  /* Crucial: Prevent children from capturing drag/clicks */
  .lp-drag-handle * {
    pointer-events: none;
    user-select: none;
    -webkit-user-select: none;
  }

  .lp-drag-handle-text {
    line-height: 1;
  }

  .lp-drag-handle:hover {
    background: #1d4ed8;
  }

  .lp-drag-handle:active,
  .lp-drag-handle.is-dragging-handle {
    cursor: grabbing;
    background: #1e3a8a;
  }

  /* Show drag handle only on hover or when selected, and keep visible during drag */
  .lp-shell:hover > .lp-drag-handle,
  .lp-shell.lp-selected > .lp-drag-handle,
  .lp-shell.lp-is-dragging > .lp-drag-handle {
    opacity: 1;
    visibility: visible;
  }

  /* Prevent overlapping handles: if a child shell is hovered, hide this shell's drag handle */
  .lp-shell:has(.lp-shell:hover) > .lp-drag-handle {
    opacity: 0 !important;
    visibility: hidden !important;
  }

  .lp-shell.lp-is-dragging {
    opacity: 0.35;
    outline: 2px dashed #3b82f6 !important;
  }

  /* Unified floating block actions toolbar */
  .lp-block-toolbar {
    position: absolute;
    top: -28px;
    left: 0;
    z-index: 100;
    display: inline-flex;
    align-items: center;
    background: #111827;
    color: #ffffff;
    border-radius: 6px 6px 6px 0;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    height: 28px;
    padding: 2px;
    gap: 1px;
    box-sizing: border-box;
    font-family: inherit;
    user-select: none;
    -webkit-user-select: none;
  }

  .lp-toolbar-drag {
    display: inline-flex;
    align-items: center;
    height: 24px;
    padding: 0 8px;
    background: #2563eb;
    color: #ffffff;
    border-radius: 4px;
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
    width: 24px;
    height: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    border-radius: 4px;
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
    left: 8px;
    right: 8px;
    height: 4px;
    border-radius: 4px;
    background: #2563eb;
    z-index: 45;
    pointer-events: none;
    box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.25);
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
    outline: 2px dashed #2563eb !important;
    outline-offset: -2px;
    background-image: linear-gradient(0deg, rgba(37, 99, 235, 0.07), rgba(37, 99, 235, 0.07));
    border-radius: 6px;
  }

  /* Give nested content room so the handle does not cover text */
  .lp-shell.lp-editable :global(.lp-container),
  .lp-shell.lp-editable :global(.lp-text),
  .lp-shell.lp-editable :global(.lp-cta-title),
  .lp-shell.lp-editable :global(.lp-plan-name) {
    /* keep content readable */
  }
</style>
