<script lang="ts">
  import { onMount } from 'svelte';

  type ToastType = 'info' | 'success' | 'warning' | 'error';

  interface Toast {
    id: string;
    type: ToastType;
    message: string;
    duration: number;
  }

  let toasts = $state<Toast[]>([]);

  export function showToast(message: string, type: ToastType = 'info', duration: number = 3000) {
    const id = `toast-${Date.now()}-${Math.random().toString(36).slice(2)}`;
    
    toasts = [...toasts, { id, type, message, duration }];

    if (duration > 0) {
      setTimeout(() => {
        removeToast(id);
      }, duration);
    }
  }

  function removeToast(id: string) {
    toasts = toasts.filter(t => t.id !== id);
  }

  function getIcon(type: ToastType) {
    switch (type) {
      case 'success': return '✓';
      case 'warning': return '⚠';
      case 'error': return '✕';
      default: return 'ℹ';
    }
  }
</script>

<div class="toast-container" aria-live="polite">
  {#each toasts as toast (toast.id)}
    <div class="toast toast-{toast.type}" role="alert">
      <span class="toast-icon">{getIcon(toast.type)}</span>
      <span class="toast-message">{toast.message}</span>
      <button 
        class="toast-close" 
        onclick={() => removeToast(toast.id)}
        aria-label="Fechar"
      >
        ✕
      </button>
    </div>
  {/each}
</div>

<style>
  .toast-container {
    position: fixed;
    bottom: 20px;
    right: 20px;
    z-index: 9999;
    display: flex;
    flex-direction: column;
    gap: 8px;
    max-width: 400px;
  }

  .toast {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 16px;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    animation: slideIn 0.3s ease;
    font-size: 14px;
  }

  @keyframes slideIn {
    from {
      opacity: 0;
      transform: translateX(100%);
    }
    to {
      opacity: 1;
      transform: translateX(0);
    }
  }

  .toast-info {
    background: #3b82f6;
    color: white;
  }

  .toast-success {
    background: #10b981;
    color: white;
  }

  .toast-warning {
    background: #f59e0b;
    color: white;
  }

  .toast-error {
    background: #ef4444;
    color: white;
  }

  .toast-icon {
    font-size: 16px;
    font-weight: bold;
  }

  .toast-message {
    flex: 1;
    line-height: 1.4;
  }

  .toast-close {
    background: none;
    border: none;
    color: white;
    opacity: 0.7;
    cursor: pointer;
    font-size: 14px;
    padding: 0;
    line-height: 1;
  }

  .toast-close:hover {
    opacity: 1;
  }

  @media (max-width: 480px) {
    .toast-container {
      left: 20px;
      right: 20px;
      max-width: none;
    }
  }
</style>