<script lang="ts">
  import { onMount } from 'svelte';
  import type { Snippet } from 'svelte';
  import { page } from '$app/stores';
  import { t } from '$lib/i18n';

  let {
    open = false,
    title = '',
    size = 'md',
    closable = true,
    onClose = () => {},
    children,
    footer
  }: {
    open?: boolean;
    title?: string;
    size?: 'sm' | 'md' | 'lg' | 'xl';
    closable?: boolean;
    onClose?: () => void;
    children?: Snippet;
    footer?: Snippet;
  } = $props();

  const lang = $derived($page.data.language || 'pt');

  const sizes: Record<string, string> = {
    sm: '400px',
    md: '500px',
    lg: '700px',
    xl: '900px'
  };

  function handleBackdropClick(e: MouseEvent) {
    if (e.target === e.currentTarget && closable) {
      onClose();
    }
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Escape' && closable) {
      onClose();
    }
  }

  function handleClose() {
    if (closable) onClose();
  }

  onMount(() => {
    document.addEventListener('keydown', handleKeydown);
    return () => document.removeEventListener('keydown', handleKeydown);
  });

  $effect(() => {
    if (open) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
  });
</script>

{#if open}
  <div class="modal-backdrop" onclick={handleBackdropClick} onkeydown={handleKeydown} role="dialog" aria-modal="true" tabindex="-1">
    <div class="modal-container" style="max-width: {sizes[size]}">
      <header class="modal-header">
        {#if title}
          <h2 class="modal-title">{title}</h2>
        {/if}
        
        {#if closable}
          <button class="modal-close" onclick={handleClose} aria-label={t(lang, 'common.close')}>
            <svg viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/>
            </svg>
          </button>
        {/if}
      </header>

      <div class="modal-content">
        {@render children?.()}
      </div>

      {#if footer}
        <footer class="modal-footer">
          {@render footer()}
        </footer>
      {/if}
    </div>
  </div>
{/if}

<style>
  .modal-backdrop {
    position: fixed;
    inset: 0;
    z-index: 1000;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(0, 0, 0, 0.5);
    backdrop-filter: blur(4px);
    animation: fadeIn 0.2s ease;
  }

  @keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
  }

  .modal-container {
    width: 90%;
    max-height: 90vh;
    background: white;
    border-radius: 12px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
    display: flex;
    flex-direction: column;
    animation: slideUp 0.3s ease;
    overflow: hidden;
  }

  @keyframes slideUp {
    from {
      opacity: 0;
      transform: translateY(20px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  .modal-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 20px 24px;
    border-bottom: 1px solid #e5e7eb;
    background: #f9fafb;
  }

  .modal-title {
    font-size: 18px;
    font-weight: 600;
    color: #1f2937;
    margin: 0;
  }

  .modal-close {
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: none;
    border: none;
    border-radius: 6px;
    color: #6b7280;
    cursor: pointer;
    transition: background 0.2s, color 0.2s;
  }

  .modal-close:hover {
    background: #e5e7eb;
    color: #1f2937;
  }

  .modal-close svg {
    width: 20px;
    height: 20px;
  }

  .modal-content {
    flex: 1;
    padding: 24px;
    overflow-y: auto;
  }

  .modal-footer {
    padding: 16px 24px;
    border-top: 1px solid #e5e7eb;
    background: #f9fafb;
    display: flex;
    gap: 12px;
    justify-content: flex-end;
  }
</style>