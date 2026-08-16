<script lang="ts">
  import { onDestroy } from 'svelte';
  import type { Snippet } from 'svelte';

  let {
    variant = 'default',
    dismissible = true,
    duration = 0,
    children
  }: {
    variant?: 'default' | 'info' | 'success' | 'warning' | 'error';
    dismissible?: boolean;
    duration?: number;
    children?: Snippet;
  } = $props();

  let visible = $state(true);

  $effect(() => {
    if (duration > 0) {
      const timer = setTimeout(() => {
        visible = false;
      }, duration);

      return () => clearTimeout(timer);
    }
  });

  function dismiss() {
    visible = false;
  }
</script>

{#if visible}
  <div class="alert alert-{variant}" role="alert">
    <div class="alert-icon">
      {#if variant === 'success'}
        <svg viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
        </svg>
      {:else if variant === 'error'}
        <svg viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>
        </svg>
      {:else if variant === 'warning'}
        <svg viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
        </svg>
      {:else if variant === 'info'}
        <svg viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"/>
        </svg>
      {:else}
        <svg viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"/>
        </svg>
      {/if}
    </div>

    <div class="alert-content">
      {@render children?.()}
    </div>

    {#if dismissible}
      <button class="alert-dismiss" onclick={dismiss} aria-label="Fechar">
        <svg viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/>
        </svg>
      </button>
    {/if}
  </div>
{/if}

<style>
  .alert {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    padding: 16px;
    border-radius: 8px;
    margin: 16px 0;
    animation: slideIn 0.3s ease;
  }

  @keyframes slideIn {
    from {
      opacity: 0;
      transform: translateY(-10px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  .alert-default {
    background: #f0f9ff;
    border: 1px solid #e0e7ff;
    color: #1e40af;
  }

  .alert-info {
    background: #eff6ff;
    border: 1px solid #bfdbfe;
    color: #1d4ed8;
  }

  .alert-success {
    background: #f0fdf4;
    border: 1px solid #bbf7d0;
    color: #15803d;
  }

  .alert-warning {
    background: #fffbeb;
    border: 1px solid #fde68a;
    color: #b45309;
  }

  .alert-error {
    background: #fef2f2;
    border: 1px solid #fecaca;
    color: #b91c1c;
  }

  .alert-icon {
    flex-shrink: 0;
    width: 20px;
    height: 20px;
  }

  .alert-icon svg {
    width: 100%;
    height: 100%;
  }

  .alert-content {
    flex: 1;
    font-size: 14px;
    line-height: 1.5;
  }

  .alert-content :global(p) {
    margin: 0;
  }

  .alert-dismiss {
    flex-shrink: 0;
    width: 20px;
    height: 20px;
    padding: 0;
    border: none;
    background: none;
    cursor: pointer;
    opacity: 0.5;
    transition: opacity 0.2s;
  }

  .alert-dismiss:hover {
    opacity: 1;
  }

  .alert-dismiss svg {
    width: 100%;
    height: 100%;
  }
</style>