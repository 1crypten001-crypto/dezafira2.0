<script lang="ts">
  import type { Block } from '$lib/landing-blocks';
  import { youtubeId } from '$lib/landing-blocks';
  import { t } from '$lib/i18n';
  import LpEditableShell from './LpEditableShell.svelte';
  import VslPlayer from './VslPlayer.svelte';

  export type DropPosition = 'before' | 'after' | 'inside';

  let {
    blocks = [],
    containerWidth = '1200px',
    editable = false,
    lang = 'pt',
    selectedId = null,
    dropTargetId = null,
    dropPosition = null as DropPosition | null,
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
    vslCtaRevealed = null
  }: {
    blocks?: Block[];
    containerWidth?: string;
    editable?: boolean;
    lang?: string;
    selectedId?: string | null;
    dropTargetId?: string | null;
    dropPosition?: DropPosition | null;
    onSelect?: (id: string, e: MouseEvent) => void;
    onDrop?: (targetId: string | null, position: DropPosition, e: DragEvent) => void;
    onDragOverTarget?: (targetId: string | null, position: DropPosition, e: DragEvent) => void;
    onBlockDragStart?: (id: string, e: DragEvent) => void;
    onDragEnd?: (e: DragEvent) => void;
    onMoveBlock?: (id: string, direction: 'up' | 'down') => void;
    onDuplicateBlock?: (id: string) => void;
    onDeleteBlock?: (id: string) => void;
    vslCtaRevealed?: boolean | null;
  } = $props();

  function stars(n: number) {
    const c = Math.max(0, Math.min(5, Number(n) || 0));
    return '★'.repeat(c) + '☆'.repeat(5 - c);
  }

  const lb = (key: string) => t(lang, `admin.landing_pages.builder.${key}`);

  // VSL CTA Reveal state management
  let hasVsl = $derived(blocks.some(b => b.type === 'vsl'));
  let ctaRevealedLocal = $state(true);

  $effect(() => {
    if (hasVsl) {
      ctaRevealedLocal = editable ? true : false;
    } else {
      ctaRevealedLocal = true;
    }
  });

  let activeCtaRevealed = $derived(vslCtaRevealed !== null ? vslCtaRevealed : ctaRevealedLocal);
  let vslPlayerRef = $state<any>(null);
  let activeVariant = $state('A');

  function getActiveHeadline(block: Block) {
    if (!block.properties) return '';
    const vslId = block.properties.vslId || block.id;
    
    if (typeof window !== 'undefined') {
      const cookieName = `lp_variant_${vslId}`;
      let variant = localStorage.getItem(cookieName);
      if (!variant) {
        const variants = ['A', 'B', 'C'];
        variant = variants[Math.floor(Math.random() * variants.length)];
        localStorage.setItem(cookieName, variant);
      }
      activeVariant = variant;
    }

    if (activeVariant === 'B' && block.properties.headline_b) {
      return block.properties.headline_b;
    }
    if (activeVariant === 'C' && block.properties.headline_c) {
      return block.properties.headline_c;
    }
    return block.properties.headline_a || block.properties.title || '';
  }

  function shouldShowBlock(block: Block): boolean {
    if (editable) return true;
    if (activeCtaRevealed) return true;
    if (block.type === 'vsl') return true;
    if (block.properties?.delay === true) return false;
    if (block.type === 'pricing' || block.type === 'cta' || block.type === 'button') {
      return false;
    }
    return true;
  }

  function handleCtaClick() {
    if (vslPlayerRef?.logConversion) {
      vslPlayerRef.logConversion();
    }
  }

  const treeProps = $derived({
    containerWidth,
    editable,
    lang,
    selectedId,
    dropTargetId,
    dropPosition,
    onSelect,
    onDrop,
    onDragOverTarget,
    onBlockDragStart,
    onDragEnd,
    onMoveBlock,
    onDuplicateBlock,
    onDeleteBlock,
    vslCtaRevealed: activeCtaRevealed
  });

  const shellHandlers = $derived({
    editable,
    lang,
    dropTargetId,
    dropPosition,
    onSelect,
    onDrop,
    onDragOverTarget,
    onBlockDragStart,
    onDragEnd,
    onMoveBlock,
    onDuplicateBlock,
    onDeleteBlock
  });

  function replaceEmojisWithSvgs(content: string | undefined | null): string {
    if (!content) return '';

    // Substitui a largura e margem inline antigas dos cards por layout responsivo e com espaçamento no mobile
    let processed = content.replace(
      /width:\s*260px;\s*margin:\s*0\s+10px;/g,
      'width: 100%; max-width: 280px; margin: 15px 10px; box-sizing: border-box; vertical-align: top;'
    );

    // Substitui o SVG sólido antigo do lápis (Heroicons) pelo novo SVG Outline do Lucide (Lápis)
    processed = processed.replace(
      /<svg[^>]*viewBox="0 0 20 20"[^>]*>.*?M13\.586\s+3\.586a2\s+2.*?<\/svg>/gs,
      `<svg viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width: 28px; height: 28px; display: inline-block; vertical-align: middle;"><path d="M12 20h9"/><path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z"/></svg>`
    );

    // Substitui o SVG sólido antigo do celular (Heroicons) pelo novo SVG Outline do Lucide (Celular)
    processed = processed.replace(
      /<svg[^>]*viewBox="0 0 20 20"[^>]*>.*?M3\s+5a2\s+2\s+0\s+012-2h10a2.*?<\/svg>/gs,
      `<svg viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width: 28px; height: 28px; display: inline-block; vertical-align: middle;"><rect width="14" height="20" x="5" y="2" rx="2" ry="2"/><path d="M12 18h.01"/></svg>`
    );

    // Substitui o SVG sólido antigo do gráfico (Heroicons) pelo novo SVG Outline do Lucide (Gráfico)
    processed = processed.replace(
      /<svg[^>]*viewBox="0 0 20 20"[^>]*>.*?M2\s+10a8\s+8\s+0\s+1116.*?<\/svg>/gs,
      `<svg viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width: 28px; height: 28px; display: inline-block; vertical-align: middle;"><path d="m22 7-8.5 8.5-5-5L2 17"/><path d="M16 7h6v6"/></svg>`
    );
    
    // Substitui spans com emojis de pincel, lapis ou paleta (Editor Visual)
    processed = processed.replace(
      /<span[^>]*>\s*(?:🖌️|✏️|🎨)\s*<\/span>/g,
      `<span style="display: block; margin-bottom: 1rem;"><svg viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width: 28px; height: 28px; display: inline-block; vertical-align: middle;"><path d="M12 20h9"/><path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z"/></svg></span>`
    );

    // Substitui spans com emoji de telefone/celular (Responsivo)
    processed = processed.replace(
      /<span[^>]*>\s*(?:📱)\s*<\/span>/g,
      `<span style="display: block; margin-bottom: 1rem;"><svg viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width: 28px; height: 28px; display: inline-block; vertical-align: middle;"><rect width="14" height="20" x="5" y="2" rx="2" ry="2"/><path d="M12 18h.01"/></svg></span>`
    );

    // Substitui spans com emoji de grafico (Alta Conversão)
    processed = processed.replace(
      /<span[^>]*>\s*(?:📈)\s*<\/span>/g,
      `<span style="display: block; margin-bottom: 1rem;"><svg viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width: 28px; height: 28px; display: inline-block; vertical-align: middle;"><path d="m22 7-8.5 8.5-5-5L2 17"/><path d="M16 7h6v6"/></svg></span>`
    );

    // Emojis soltos (fora do span)
    processed = processed.replace(
      /🖌️|✏️|🎨/g,
      `<svg viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width: 28px; height: 28px; display: inline-block; vertical-align: middle; margin-right: 4px;"><path d="M12 20h9"/><path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z"/></svg>`
    );
    processed = processed.replace(
      /📱/g,
      `<svg viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width: 28px; height: 28px; display: inline-block; vertical-align: middle; margin-right: 4px;"><rect width="14" height="20" x="5" y="2" rx="2" ry="2"/><path d="M12 18h.01"/></svg>`
    );
    processed = processed.replace(
      /📈/g,
      `<svg viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width: 28px; height: 28px; display: inline-block; vertical-align: middle; margin-right: 4px;"><path d="m22 7-8.5 8.5-5-5L2 17"/><path d="M16 7h6v6"/></svg>`
    );

    return processed;
  }

  function emptyDropHandlers(parentId: string) {
    return {
      ondragover: (e: DragEvent) => {
        if (!editable) return;
        e.preventDefault();
        e.stopPropagation();
        if (e.dataTransfer) e.dataTransfer.dropEffect = 'copy';
        onDragOverTarget?.(parentId, 'inside', e);
      },
      ondrop: (e: DragEvent) => {
        if (!editable || !onDrop) return;
        e.preventDefault();
        e.stopPropagation();
        onDrop(parentId, 'inside', e);
      }
    };
  }
</script>

{#each blocks as block (block.id)}
  {#if shouldShowBlock(block)}
  {#if block.type === 'section'}
    <LpEditableShell
      tag="section"
      blockId={block.id}
      blockType={block.type}
      selected={selectedId === block.id}
      className="lp-section"
      style="padding-top:{block.styles?.paddingTop || '40px'};padding-bottom:{block.styles?.paddingBottom || '40px'};margin-top:{block.styles?.marginTop || '0px'};margin-bottom:{block.styles?.marginBottom || '0px'};background-color:{block.styles?.backgroundColor || 'transparent'};color:{block.styles?.textColor || 'inherit'};text-align:{block.styles?.textAlign || 'left'};border-radius:{block.styles?.borderRadius || '0px'};width:100%;"
      {...shellHandlers}
    >
      <div class="lp-container" style:max-width={containerWidth}>
        {#if block.children?.length}
          <svelte:self blocks={block.children} {...treeProps} />
        {:else if editable}
          <div class="lp-empty-drop" {...emptyDropHandlers(block.id)}></div>
        {/if}
      </div>
    </LpEditableShell>
  {:else if block.type === 'container' || block.type === 'column'}
    <LpEditableShell
      blockId={block.id}
      blockType={block.type}
      selected={selectedId === block.id}
      className="lp-container-block"
      style="padding-top:{block.styles?.paddingTop || '0px'};padding-bottom:{block.styles?.paddingBottom || '0px'};margin-top:{block.styles?.marginTop || '0px'};margin-bottom:{block.styles?.marginBottom || '0px'};text-align:{block.styles?.textAlign || 'inherit'};background:{block.styles?.backgroundColor || 'transparent'};color:{block.styles?.textColor || 'inherit'};border-radius:{block.styles?.borderRadius || '0px'};"
      {...shellHandlers}
    >
      {#if block.children?.length}
        <svelte:self blocks={block.children} {...treeProps} />
      {:else if editable}
        <div class="lp-empty-drop" {...emptyDropHandlers(block.id)}></div>
      {/if}
    </LpEditableShell>
  {:else if block.type === 'columns'}
    <LpEditableShell
      blockId={block.id}
      blockType={block.type}
      selected={selectedId === block.id}
      className="lp-columns"
      style="--lp-cols:{String(block.properties?.cols || block.children?.length || 2)};--lp-gap:{block.properties?.gap || '1.5rem'};margin-top:{block.styles?.marginTop || '0px'};margin-bottom:{block.styles?.marginBottom || '16px'};padding-top:{block.styles?.paddingTop || '0px'};padding-bottom:{block.styles?.paddingBottom || '0px'};background:{block.styles?.backgroundColor || 'transparent'};color:{block.styles?.textColor || 'inherit'};border-radius:{block.styles?.borderRadius || '0px'};"
      {...shellHandlers}
    >
      {#if block.children?.length}
        {#each block.children as col (col.id)}
          <LpEditableShell
            blockId={col.id}
            blockType={col.type || 'column'}
            selected={selectedId === col.id}
            className="lp-col"
            {...shellHandlers}
          >
            {#if col.children?.length}
              <svelte:self blocks={col.children} {...treeProps} />
            {:else if editable}
              <div class="lp-empty-drop" {...emptyDropHandlers(col.id)}></div>
            {/if}
          </LpEditableShell>
        {/each}
      {/if}
    </LpEditableShell>
  {:else if block.type === 'hero'}
    <LpEditableShell
      blockId={block.id} blockType={block.type} selected={selectedId === block.id}
      className="lp-premium-hero {block.properties?.image ? 'has-media' : 'no-media'}"
      style="padding-top:{block.styles?.paddingTop || '72px'};padding-bottom:{block.styles?.paddingBottom || '72px'};background:{block.styles?.backgroundColor || '#0b1220'};color:{block.styles?.textColor || '#fff'};border-radius:{block.styles?.borderRadius || '24px'};margin-top:{block.styles?.marginTop || '0px'};margin-bottom:{block.styles?.marginBottom || '24px'};text-align:{block.styles?.textAlign || 'left'};"
      {...shellHandlers}
    >
      <div class="lp-hero-copy">
        {#if block.properties?.eyebrow}<span class="lp-eyebrow">{block.properties.eyebrow}</span>{/if}
        <h1 style:color={block.styles?.textColor || '#ffffff'}>{block.properties?.title || 'Landing page premium'}</h1>
        <p style:color={block.properties?.subtitleColor || '#cbd5e1'}>{block.properties?.subtitle || ''}</p>
        <div class="lp-hero-actions">
          <a class="lp-btn lp-btn-primary" href={block.properties?.primaryHref || '#'} onclick={(e) => editable && e.preventDefault()}>{block.properties?.primaryText || 'Começar'}</a>
          {#if block.properties?.secondaryText}<a class="lp-btn lp-btn-secondary" href={block.properties?.secondaryHref || '#'} onclick={(e) => editable && e.preventDefault()}>{block.properties.secondaryText}</a>{/if}
        </div>
      </div>
      {#if block.properties?.image}
        <div class="lp-hero-media"><img src={block.properties.image} alt={block.properties?.imageAlt || ''} draggable="false" /></div>
      {/if}
    </LpEditableShell>
  {:else if block.type === 'product-showcase'}
    <LpEditableShell
      blockId={block.id} blockType={block.type} selected={selectedId === block.id}
      className="lp-product-showcase {block.properties?.image ? 'has-product-image' : 'no-product-image'}"
      style="padding-top:{block.styles?.paddingTop || '32px'};padding-bottom:{block.styles?.paddingBottom || '32px'};background:{block.styles?.backgroundColor || '#fff'};color:{block.styles?.textColor || '#111827'};border-radius:{block.styles?.borderRadius || '24px'};margin-top:{block.styles?.marginTop || '0px'};margin-bottom:{block.styles?.marginBottom || '24px'};text-align:{block.styles?.textAlign || 'left'};"
      {...shellHandlers}
    >
      <div class="lp-product-media">
        {#if block.properties?.image}<img src={block.properties.image} alt={block.properties?.imageAlt || block.properties?.name || ''} draggable="false" />{:else}<div class="lp-media-placeholder"><span>OFERTA DIGITAL</span><strong>Seu produto<br />em destaque</strong><i>Imagem 1200 × 900</i></div>{/if}
      </div>
      <div class="lp-product-copy">
        <span class="lp-eyebrow">{block.properties?.eyebrow || 'Oferta em destaque'}</span>
        <h2 style:color={block.styles?.textColor || '#111827'}>{block.properties?.name || 'Selecione um produto'}</h2>
        <p>{block.properties?.description || ''}</p>
        {#if block.properties?.bullets?.length}
          <ul class="lp-product-bullets">{#each block.properties.bullets as bullet}<li><span>✓</span>{bullet}</li>{/each}</ul>
        {/if}
        {#if block.properties?.price}<div class="lp-product-price">{block.properties.price}</div>{/if}
        <a class="lp-btn lp-btn-dark" href={block.properties?.buttonHref || '/products'} onclick={(e) => editable && e.preventDefault()}>{block.properties?.buttonText || 'Ver oferta'}</a>
      </div>
    </LpEditableShell>
  {:else if block.type === 'posts-grid'}
    <LpEditableShell
      blockId={block.id} blockType={block.type} selected={selectedId === block.id}
      className="lp-posts-section"
      style="padding-top:{block.styles?.paddingTop || '40px'};padding-bottom:{block.styles?.paddingBottom || '40px'};background:{block.styles?.backgroundColor || '#f8fafc'};color:{block.styles?.textColor || '#111827'};border-radius:{block.styles?.borderRadius || '24px'};margin-bottom:{block.styles?.marginBottom || '24px'};"
      {...shellHandlers}
    >
      <div class="lp-section-heading"><h2>{block.properties?.title || 'Conteúdos recomendados'}</h2><p>{block.properties?.subtitle || ''}</p></div>
      <div class="lp-posts-grid">
        {#each block.properties?.posts || [] as post}
          <a class="lp-post-card" href={post.href || `/post/${post.slug}`} onclick={(e) => editable && e.preventDefault()}>
            {#if post.cover_image}<img src={post.cover_image} alt="" loading="lazy" draggable="false" />{:else}<div class="lp-post-placeholder">POST</div>{/if}
            <div><h3>{post.title}</h3>{#if post.excerpt}<p>{post.excerpt}</p>{/if}<span>Ler artigo →</span></div>
          </a>
        {/each}
        {#if !(block.properties?.posts?.length)}<div class="lp-empty-content">Selecione posts no painel do bloco.</div>{/if}
      </div>
    </LpEditableShell>
  {:else if block.type === 'trust-bar'}
    <LpEditableShell
      blockId={block.id} blockType={block.type} selected={selectedId === block.id}
      className="lp-trust-bar"
      style="padding-top:{block.styles?.paddingTop || '20px'};padding-bottom:{block.styles?.paddingBottom || '20px'};background:{block.styles?.backgroundColor || '#eff6ff'};color:{block.styles?.textColor || '#1e3a8a'};border-radius:{block.styles?.borderRadius || '18px'};margin-bottom:{block.styles?.marginBottom || '24px'};"
      {...shellHandlers}
    >
      {#each block.properties?.items || [] as item}<div><span>✓</span>{item}</div>{/each}
    </LpEditableShell>
  {:else if block.type === 'cta'}
    <LpEditableShell
      blockId={block.id}
      blockType={block.type}
      selected={selectedId === block.id}
      className="lp-cta"
      style="padding-top:{block.styles?.paddingTop || '48px'};padding-bottom:{block.styles?.paddingBottom || '48px'};background-color:{block.styles?.backgroundColor || '#111827'};color:{block.styles?.textColor || '#ffffff'};text-align:{block.styles?.textAlign || 'center'};border-radius:{block.styles?.borderRadius || '16px'};margin-bottom:{block.styles?.marginBottom || '16px'};"
      {...shellHandlers}
    >
      <h2 class="lp-cta-title">{block.content || lb('fallback_cta')}</h2>
      {#if block.properties?.subtitle}
        <p class="lp-cta-sub">{block.properties.subtitle}</p>
      {/if}
      <a
        class="lp-btn"
        href={block.properties?.buttonHref || '#'}
        style:background-color={block.properties?.buttonBg || '#22c55e'}
        style:color={block.properties?.buttonColor || '#052e16'}
        target={block.properties?.buttonHref?.startsWith('http') ? '_blank' : undefined}
        rel={block.properties?.buttonHref?.startsWith('http') ? 'noopener noreferrer' : undefined}
        onclick={(e) => editable && e.preventDefault()}
        draggable="false"
      >
        {block.properties?.buttonText || lb('fallback_start')}
      </a>
    </LpEditableShell>
  {:else if block.type === 'testimonial'}
    <LpEditableShell
      blockId={block.id}
      blockType={block.type}
      selected={selectedId === block.id}
      className="lp-testimonial"
      style="padding-top:{block.styles?.paddingTop || '24px'};padding-bottom:{block.styles?.paddingBottom || '24px'};background-color:{block.styles?.backgroundColor || '#f9fafb'};color:{block.styles?.textColor || '#111827'};border-radius:{block.styles?.borderRadius || '16px'};margin-bottom:{block.styles?.marginBottom || '16px'};"
      {...shellHandlers}
    >
      <div class="lp-stars" aria-label="{block.properties?.rating || 5} stars">
        {stars(block.properties?.rating ?? 5)}
      </div>
      <blockquote class="lp-quote">“{block.properties?.quote || ''}”</blockquote>
      <div class="lp-author-row">
        {#if block.properties?.avatar}
          <img class="lp-avatar" src={block.properties.avatar} alt="" draggable="false" />
        {:else}
          <div class="lp-avatar placeholder">
            {(block.properties?.author || 'A').slice(0, 1).toUpperCase()}
          </div>
        {/if}
        <div>
          <div class="lp-author">{block.properties?.author || lb('fallback_customer')}</div>
          {#if block.properties?.role}
            <div class="lp-role">{block.properties.role}</div>
          {/if}
        </div>
      </div>
    </LpEditableShell>
  {:else if block.type === 'pricing'}
    <LpEditableShell
      blockId={block.id}
      blockType={block.type}
      selected={selectedId === block.id}
      className="lp-pricing {block.properties?.featured ? 'featured' : ''}"
      style="padding-top:{block.styles?.paddingTop || '28px'};padding-bottom:{block.styles?.paddingBottom || '28px'};background-color:{block.styles?.backgroundColor || '#ffffff'};color:{block.styles?.textColor || '#111827'};border-radius:{block.styles?.borderRadius || '16px'};margin-bottom:{block.styles?.marginBottom || '16px'};"
      {...shellHandlers}
    >
      {#if block.properties?.featured}
        <span class="lp-badge">{lb('fallback_popular')}</span>
      {/if}
      <div class="lp-plan-name">{block.properties?.name || lb('fallback_plan')}</div>
      <div class="lp-price">
        <span class="lp-price-value">{block.properties?.price || 'R$ 0'}</span>
        <span class="lp-price-period">{block.properties?.period || ''}</span>
      </div>
      <ul class="lp-features">
        {#each block.properties?.features || [] as feat}
          <li>✓ {feat}</li>
        {/each}
      </ul>
      <a
        class="lp-btn"
        href={block.properties?.buttonHref || '#'}
        style:background-color={block.properties?.featured ? '#22c55e' : '#111827'}
        style:color={block.properties?.featured ? '#052e16' : '#ffffff'}
        onclick={(e) => editable && e.preventDefault()}
        draggable="false"
      >
        {block.properties?.buttonText || lb('fallback_subscribe')}
      </a>
    </LpEditableShell>
  {:else if block.type === 'faq'}
    <LpEditableShell
      blockId={block.id}
      blockType={block.type}
      selected={selectedId === block.id}
      className="lp-faq"
      style="padding-top:{block.styles?.paddingTop || '16px'};padding-bottom:{block.styles?.paddingBottom || '16px'};margin-bottom:{block.styles?.marginBottom || '16px'};"
      {...shellHandlers}
    >
      {#if block.properties?.title}
        <h2 class="lp-faq-title">{block.properties.title}</h2>
      {/if}
      <div class="lp-faq-list">
        {#each block.properties?.items || [] as item, i}
          <details class="lp-faq-item" open={i === 0 && !editable}>
            <summary>{item.q}</summary>
            <p>{item.a}</p>
          </details>
        {/each}
      </div>
    </LpEditableShell>
  {:else}
    <LpEditableShell
      blockId={block.id}
      blockType={block.type}
      selected={selectedId === block.id}
      className="lp-element"
      style="margin-top:{block.styles?.marginTop || '0px'};margin-bottom:{block.styles?.marginBottom || '12px'};padding-top:{block.styles?.paddingTop || '0px'};padding-bottom:{block.styles?.paddingBottom || '0px'};text-align:{block.styles?.textAlign || 'inherit'};background:{block.styles?.backgroundColor || 'transparent'};color:{block.styles?.textColor || 'inherit'};border-radius:{block.styles?.borderRadius || '0px'};"
      {...shellHandlers}
    >
      {#if block.type === 'text' || block.type === 'html'}
        <div
          class="lp-text"
          style:font-size={block.styles?.fontSize || '1rem'}
          style:color={block.styles?.textColor || 'inherit'}
        >
          {@html replaceEmojisWithSvgs(block.content)}
        </div>
      {:else if block.type === 'image'}
        {#if block.properties?.src}
          <img
            src={block.properties.src}
            alt={block.properties.alt || ''}
            loading="lazy"
            style:max-width="100%"
            style:height="auto"
            style:border-radius={block.styles?.borderRadius || '0px'}
            style:display="inline-block"
            draggable="false"
          />
        {/if}
      {:else if block.type === 'button'}
        <a
          href={block.properties?.href || '#'}
          class="lp-btn"
          style:background-color={block.styles?.backgroundColor || '#111827'}
          style:color={block.styles?.textColor || '#ffffff'}
          style:padding-top={block.styles?.paddingTop || '12px'}
          style:padding-bottom={block.styles?.paddingBottom || '12px'}
          style:border-radius={block.styles?.borderRadius || '8px'}
          style:font-size={block.styles?.fontSize || '0.875rem'}
          style:margin-left={block.styles?.marginLeft || '0'}
          style:border-width={block.styles?.borderWidth || '0'}
          style:border-style={block.styles?.borderStyle || 'none'}
          style:border-color={block.styles?.borderColor || 'transparent'}
          target={block.properties?.href?.startsWith('http') ? '_blank' : undefined}
          rel={block.properties?.href?.startsWith('http') ? 'noopener noreferrer' : undefined}
          onclick={(e) => { if (editable) e.preventDefault(); else handleCtaClick(); }}
          draggable="false"
        >
          {block.content || lb('fallback_button')}
        </a>
      {:else if block.type === 'video'}
        {@const vid = youtubeId(block.properties?.src)}
        {#if vid}
          <div class="lp-video-card">
            <div class="video-header">
              <span class="video-pulse-container">
                <span class="pulse-dot"></span>
                <span class="pulse-label">Vídeo</span>
              </span>
            </div>
            <div class="video-wrapper">
              <iframe
                title="YouTube video"
                src="https://www.youtube.com/embed/{vid}"
                loading="lazy"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowfullscreen
                class:lp-iframe-editable={editable}
              ></iframe>
            </div>
          </div>
        {/if}
      {:else if block.type === 'vsl'}
        {@const activeHeadline = getActiveHeadline(block)}
        <div class="lp-vsl-card">
          {#if activeHeadline}
            <h1 class="lp-vsl-headline">{activeHeadline}</h1>
          {/if}
          <VslPlayer
            vslId={block.properties?.vslId || block.id}
            src={block.properties?.src}
            thumbnail={block.properties?.thumbnail}
            delaySeconds={block.properties?.delaySeconds || 0}
            headlineVariant={activeVariant}
            onCtaReveal={() => { ctaRevealedLocal = true; }}
            bind:this={vslPlayerRef}
          />
        </div>
      {:else if block.type === 'divider'}
        <hr
          class="lp-divider"
          style:border-top-width={block.styles?.borderWidth || '1px'}
          style:border-top-style={block.styles?.borderStyle || 'solid'}
          style:border-top-color={block.styles?.borderColor || '#e5e7eb'}
        />
      {:else if block.type === 'spacer'}
        <div style:height={block.styles?.paddingTop || '24px'} aria-hidden="true"></div>
      {/if}
    </LpEditableShell>
  {/if}
  {/if}
{/each}

<style>
  .lp-container {
    margin: 0 auto;
    padding: 0 1.25rem;
    width: 100%;
    box-sizing: border-box;
  }

  :global(.lp-section) {
    width: 100%;
    box-sizing: border-box;
  }

  :global(.lp-columns) {
    display: grid;
    grid-template-columns: repeat(var(--lp-cols, 2), minmax(0, 1fr));
    gap: var(--lp-gap, 1.5rem);
    width: 100%;
  }

  :global(.lp-col) {
    min-width: 0;
    min-height: 48px;
  }

  @media (max-width: 768px) {
    :global(.lp-columns) {
      grid-template-columns: 1fr;
    }
  }

  /* Force single column layout inside mobile preview frame in the admin editor */
  :global(.builder-canvas-frame.mobile) :global(.lp-columns) {
    grid-template-columns: 1fr !important;
  }

  .lp-btn {
    display: inline-block;
    padding: 0.75rem 1.75rem;
    text-decoration: none;
    font-weight: 700;
    border-radius: 8px;
    transition: filter 150ms ease, transform 150ms ease;
    box-sizing: border-box;
  }

  .lp-btn:hover {
    filter: brightness(0.94);
    transform: translateY(-1px);
  }

  :global(.lp-premium-hero), :global(.lp-product-showcase), :global(.lp-posts-section), :global(.lp-trust-bar) { box-sizing: border-box; padding-left: clamp(1.5rem, 5vw, 4.5rem); padding-right: clamp(1.5rem, 5vw, 4.5rem); overflow: hidden; }
  :global(.lp-premium-hero) { position:relative; isolation:isolate; display:grid; grid-template-columns:minmax(0,1.1fr) minmax(280px,.9fr); align-items:center; gap:clamp(2rem,5vw,5rem); border:1px solid rgba(96,165,250,.4); box-shadow:0 30px 90px rgba(15,23,42,.28); background-image:radial-gradient(circle at 90% 10%,rgba(59,130,246,.28),transparent 38%),radial-gradient(circle at 5% 100%,rgba(14,165,233,.12),transparent 32%); }
  :global(.lp-premium-hero)::after { content:''; position:absolute; z-index:-1; inset:0; opacity:.13; background-image:linear-gradient(rgba(255,255,255,.08) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.08) 1px,transparent 1px); background-size:44px 44px; mask-image:linear-gradient(to right,black,transparent 82%); }
  :global(.lp-premium-hero.no-media) { grid-template-columns:1fr; }
  :global(.lp-premium-hero.no-media) .lp-hero-copy { max-width:850px; }
  .lp-hero-copy h1 { margin: .75rem 0 1rem; font-size: clamp(2.35rem, 6vw, 4.75rem); line-height: .98; letter-spacing: -.055em; max-width: 820px; }
  .lp-hero-copy > p { max-width:660px; font-size:clamp(1rem,2vw,1.2rem); line-height:1.65; }
  .lp-eyebrow { display:inline-flex; align-items:center; gap:.4rem; padding:.45rem .75rem; border:1px solid rgba(96,165,250,.24); border-radius:999px; background:rgba(59,130,246,.14); color:#60a5fa; font-size:.7rem; font-weight:850; letter-spacing:.12em; text-transform:uppercase; }
  .lp-eyebrow::before { content:''; width:.38rem; height:.38rem; border-radius:50%; background:currentColor; box-shadow:0 0 0 4px rgba(96,165,250,.12); }
  .lp-hero-actions { display: flex; flex-wrap: wrap; gap: .75rem; margin-top: 1.75rem; }
  .lp-btn-primary { background:linear-gradient(135deg,#3b82f6,#2563eb); color:white; box-shadow:0 12px 28px rgba(37,99,235,.32); }
  .lp-btn-secondary { color:white; border:1px solid rgba(255,255,255,.22); background:rgba(255,255,255,.04); }
  .lp-btn-dark { background: #111827; color: white; }
  .lp-hero-media img { width: 100%; aspect-ratio: 4/5; object-fit: cover; border-radius: 22px; box-shadow: 0 28px 90px rgba(0,0,0,.45); }
  :global(.lp-product-showcase) { position:relative; display:grid; grid-template-columns:minmax(260px,.85fr) minmax(0,1.15fr); align-items:center; gap:clamp(2rem,5vw,5rem); border:1px solid rgba(15,23,42,.08); box-shadow:0 24px 70px rgba(15,23,42,.1); }
  :global(.lp-product-showcase)::before { content:''; position:absolute; top:0; right:0; width:180px; height:180px; border-radius:0 24px 0 100%; background:linear-gradient(135deg,transparent,rgba(59,130,246,.08)); pointer-events:none; }
  .lp-product-media img, .lp-media-placeholder { width: 100%; aspect-ratio: 4/3; object-fit: cover; border-radius: 18px; }
  .lp-media-placeholder, .lp-post-placeholder { display:grid; place-items:center; background:linear-gradient(145deg,#eff6ff,#e0e7ff); color:#3730a3; }
  .lp-media-placeholder { position:relative; align-content:center; gap:.75rem; overflow:hidden; border:1px solid #c7d2fe; }
  .lp-media-placeholder::before,.lp-media-placeholder::after { content:''; position:absolute; border-radius:50%; border:1px solid rgba(79,70,229,.16); }
  .lp-media-placeholder::before { width:260px; height:260px; }
  .lp-media-placeholder::after { width:170px; height:170px; }
  .lp-media-placeholder span,.lp-media-placeholder strong,.lp-media-placeholder i { position:relative; z-index:1; }
  .lp-media-placeholder span { font-size:.65rem; font-weight:900; letter-spacing:.18em; }
  .lp-media-placeholder strong { color:#1e1b4b; font-size:clamp(1.35rem,3vw,2rem); line-height:1.05; letter-spacing:-.04em; text-align:center; }
  .lp-media-placeholder i { padding:.35rem .55rem; border-radius:99px; background:rgba(255,255,255,.7); color:#6366f1; font-size:.63rem; font-style:normal; font-weight:750; letter-spacing:.04em; }
  .lp-product-copy h2, .lp-section-heading h2 { margin: .8rem 0 .65rem; font-size: clamp(1.8rem,4vw,3rem); letter-spacing:-.035em; }
  .lp-product-copy p { color:#64748b; line-height:1.7; }
  .lp-product-price { font-size:1.6rem; font-weight:900; margin:1rem 0 1.25rem; }
  .lp-product-bullets { display:grid; gap:.55rem; margin:1rem 0 1.35rem; padding:0; list-style:none; color:#334155; }
  .lp-product-bullets li { display:flex; align-items:center; gap:.55rem; }
  .lp-product-bullets span { display:grid; place-items:center; width:1.25rem; height:1.25rem; flex:0 0 auto; border-radius:50%; background:#dcfce7; color:#15803d; font-size:.7rem; font-weight:900; }
  .lp-section-heading { margin-bottom:1.6rem; }
  .lp-section-heading p { color:#64748b; margin:.4rem 0 0; }
  .lp-posts-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:1rem; }
  .lp-post-card { background:white; color:inherit; border:1px solid #e5e7eb; border-radius:16px; overflow:hidden; text-decoration:none; transition:transform .18s ease,box-shadow .18s ease; }
  .lp-post-card:hover { transform:translateY(-3px); box-shadow:0 16px 40px rgba(15,23,42,.1); }
  .lp-post-card img, .lp-post-placeholder { width:100%; aspect-ratio:16/9; object-fit:cover; }
  .lp-post-card > div:last-child { padding:1rem; }
  .lp-post-card h3 { margin:0 0 .5rem; font-size:1.05rem; line-height:1.35; }
  .lp-post-card p { margin:0 0 .8rem; color:#64748b; font-size:.88rem; line-height:1.5; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden; }
  .lp-post-card span { color:#2563eb; font-weight:750; font-size:.85rem; }
  :global(.lp-trust-bar) { display:flex; justify-content:center; flex-wrap:wrap; gap:1rem 2rem; font-weight:750; }
  :global(.lp-trust-bar) > div { display:flex; align-items:center; gap:.45rem; }
  :global(.lp-trust-bar) span { display:grid; place-items:center; width:1.35rem; height:1.35rem; border-radius:50%; background:currentColor; color:white; font-size:.72rem; }
  .lp-empty-content { grid-column:1/-1; padding:2rem; border:1px dashed #94a3b8; border-radius:14px; color:#64748b; text-align:center; }

  @media (max-width: 820px) {
    :global(.lp-premium-hero), :global(.lp-product-showcase) { grid-template-columns:1fr; }
    .lp-posts-grid { grid-template-columns:1fr; }
    .lp-hero-copy h1 { font-size:clamp(2.25rem,12vw,3.5rem); }
  }

  :global(.lp-cta) {
    padding-left: 1.5rem;
    padding-right: 1.5rem;
  }

  .lp-cta-title {
    margin: 0 0 0.75rem;
    font-size: clamp(1.5rem, 3vw, 2.25rem);
    font-weight: 800;
    letter-spacing: -0.02em;
  }

  .lp-cta-sub {
    margin: 0 auto 1.5rem;
    max-width: 36rem;
    opacity: 0.9;
    font-size: 1.05rem;
    line-height: 1.6;
  }

  :global(.lp-testimonial) {
    padding-left: 1.5rem;
    padding-right: 1.5rem;
    border: 1px solid rgba(0, 0, 0, 0.06);
    height: 100%;
    box-sizing: border-box;
  }

  .lp-stars {
    color: #f59e0b;
    letter-spacing: 0.08em;
    margin-bottom: 0.75rem;
    font-size: 0.95rem;
  }

  .lp-quote {
    margin: 0 0 1.25rem;
    font-size: 1rem;
    line-height: 1.65;
    font-style: italic;
  }

  .lp-author-row {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }

  .lp-avatar {
    width: 40px;
    height: 40px;
    border-radius: 999px;
    object-fit: cover;
  }

  .lp-avatar.placeholder {
    display: grid;
    place-items: center;
    background: #e5e7eb;
    color: #374151;
    font-weight: 700;
  }

  .lp-author {
    font-weight: 700;
    font-size: 0.9rem;
  }

  .lp-role {
    font-size: 0.8rem;
    opacity: 0.7;
  }

  :global(.lp-pricing) {
    padding-left: 1.5rem;
    padding-right: 1.5rem;
    border: 1px solid rgba(0, 0, 0, 0.08);
    height: 100%;
    box-sizing: border-box;
  }

  :global(.lp-pricing.featured) {
    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.12);
    border-color: transparent;
  }

  .lp-badge {
    position: absolute;
    top: 12px;
    right: 12px;
    background: #22c55e;
    color: #052e16;
    font-size: 0.7rem;
    font-weight: 800;
    padding: 0.25rem 0.5rem;
    border-radius: 999px;
    text-transform: uppercase;
  }

  .lp-plan-name {
    font-weight: 700;
    font-size: 0.95rem;
    margin-bottom: 0.5rem;
    opacity: 0.85;
  }

  .lp-price {
    margin-bottom: 1rem;
  }

  .lp-price-value {
    font-size: 2rem;
    font-weight: 800;
    letter-spacing: -0.03em;
  }

  .lp-price-period {
    opacity: 0.65;
    font-size: 0.9rem;
  }

  .lp-features {
    list-style: none;
    padding: 0;
    margin: 0 0 1.25rem;
    text-align: left;
    display: grid;
    gap: 0.45rem;
    font-size: 0.9rem;
  }

  .lp-faq-title {
    margin: 0 0 1rem;
    font-size: 1.5rem;
    font-weight: 800;
  }

  .lp-faq-list {
    display: grid;
    gap: 0.5rem;
  }

  .lp-faq-item {
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    padding: 0.85rem 1rem;
    background: #fff;
  }

  .lp-faq-item summary {
    cursor: pointer;
    font-weight: 700;
    list-style: none;
  }

  .lp-faq-item summary::-webkit-details-marker {
    display: none;
  }

  .lp-faq-item p {
    margin: 0.65rem 0 0;
    color: #4b5563;
    line-height: 1.55;
    font-size: 0.95rem;
  }

  .lp-video-card {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    border-radius: 16px;
    padding: 0.875rem;
    box-shadow: 0 20px 40px -15px rgba(0, 0, 0, 0.4), 0 0 20px rgba(59, 130, 246, 0.12);
    margin: 0 auto;
    max-width: 800px;
    width: 100%;
    box-sizing: border-box;
    border: 1px solid rgba(255, 255, 255, 0.1);
  }

  .lp-video-card .video-header {
    display: flex;
    align-items: center;
    justify-content: flex-start;
    margin-bottom: 0.6rem;
  }

  .lp-video-card .video-pulse-container {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    background: rgba(239, 68, 68, 0.15);
    border: 1px solid rgba(239, 68, 68, 0.3);
    padding: 0.2rem 0.6rem;
    border-radius: 20px;
  }

  .lp-video-card .pulse-dot {
    width: 8px;
    height: 8px;
    background-color: #ef4444;
    border-radius: 50%;
    display: inline-block;
    box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7);
    animation: pulse-post 1.5s infinite;
  }

  .lp-video-card .pulse-label {
    font-size: 0.7rem;
    font-weight: 700;
    color: #f87171;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  @keyframes pulse-post {
    0%   { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7); }
    70%  { transform: scale(1);    box-shadow: 0 0 0 8px rgba(239, 68, 68, 0); }
    100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
  }

  .lp-video-card .video-wrapper {
    position: relative;
    width: 100%;
    aspect-ratio: 16 / 9;
    border-radius: 10px;
    overflow: hidden;
    border: 1px solid rgba(255, 255, 255, 0.1);
    background: #000;
  }

  .lp-video-card .video-wrapper iframe {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    border: 0;
    pointer-events: auto;
  }

  .lp-video-card .video-wrapper iframe.lp-iframe-editable {
    pointer-events: none;
  }

  .lp-divider {
    border: none;
    margin: 0;
  }

  .lp-text :global(h1),
  .lp-text :global(h2),
  .lp-text :global(h3),
  .lp-text :global(h4) {
    margin-top: 0;
    font-weight: 800;
  }

  .lp-text :global(p) {
    margin: 0;
  }

  .lp-empty-drop {
    min-height: 64px;
    border: 1.5px dashed #94a3b8;
    border-radius: 8px;
    margin: 0.5rem 0;
    background: repeating-linear-gradient(
      -45deg,
      transparent,
      transparent 6px,
      rgba(148, 163, 184, 0.1) 6px,
      rgba(148, 163, 184, 0.1) 12px
    );
  }

  .lp-vsl-card {
    width: 100%;
    max-width: 800px;
    margin: 24px auto;
    padding: 0 16px;
    text-align: center;
    box-sizing: border-box;
  }

  .lp-vsl-headline {
    font-size: 2.25rem;
    font-weight: 800;
    line-height: 1.25;
    margin-bottom: 24px;
    letter-spacing: -0.025em;
    color: inherit;
  }

  @media (max-width: 768px) {
    .lp-vsl-headline {
      font-size: 1.65rem;
      margin-bottom: 16px;
    }
  }
</style>
