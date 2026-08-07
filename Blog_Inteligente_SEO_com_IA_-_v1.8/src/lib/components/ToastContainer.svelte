<script lang="ts">
  let { 
    toasts = [],
    position = 'bottom-right'
  } = $props();

  const icons: Record<string, string> = {
    info: 'M12 16v-4m0-4h.01M22 12c0 5.523-4.477 10-10 10S2 17.523 2 12 6.477 2 12 2s10 4.477 10 10z',
    success: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z',
    warning: 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z',
    error: 'M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z'
  };

  const colors: Record<string, { bg: string; border: string; icon: string }> = {
    info: { bg: '#3b82f6', border: '#2563eb', icon: 'white' },
    success: { bg: '#10b981', border: '#059669', icon: 'white' },
    warning: { bg: '#f59e0b', border: '#d97706', icon: 'white' },
    error: { bg: '#ef4444', border: '#dc2626', icon: 'white' }
  };

  function removeToast(id: string) {
    toasts = toasts.filter(t => t.id !== id);
  }
</script>

<div class="toast-container position-{position}">
  {#each toasts as toast (toast.id)}
    <div 
      class="toast"
      style="background: {colors[toast.type].bg}; border-color: {colors[toast.type].border}"
    >
      <svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke={colors[toast.type].icon} stroke-width="2">
        <path d={icons[toast.type]} stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
      
      <span class="toast-message">{toast.message}</span>
      
      <button 
        class="toast-close"
        onclick={() => removeToast(toast.id)}
        aria-label="Fechar"
        style="color: {colors[toast.type].icon}"
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M6 18L18 6M6 6l12 12"/>
        </svg>
      </button>
      
      {#if toast.duration}
        <div 
          class="toast-progress"
          style="background: {colors[toast.type].icon}"
        ></div>
      {/if}
    </div>
  {/each}
</div>

<style>
  .toast-container {
    position: fixed;
    z-index: 9999;
    display: flex;
    flex-direction: column;
    gap: 12px;
    max-width: 400px;
    pointer-events: none;
  }

  .toast-container > :global(*) {
    pointer-events: auto;
  }

  /* Positions */
  .position-top-right { top: 20px; right: 20px; }
  .position-top-left { top: 20px; left: 20px; }
  .position-bottom-right { bottom: 20px; right: 20px; }
  .position-bottom-left { bottom: 20px; left: 20px; }
  .position-top-center { top: 20px; left: 50%; transform: translateX(-50%); }
  .position-bottom-center { bottom: 20px; left: 50%; transform: translateX(-50%); }

  .toast {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 14px 16px;
    border-radius: 10px;
    border: 1px solid;
    box-shadow: 0 8px 20px rgba(0, 0, 0, 0.2);
    animation: slideIn 0.3s ease;
    position: relative;
    overflow: hidden;
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

  .position-top-left .toast,
  .position-bottom-left .toast {
    animation-name: slideInLeft;
  }

  @keyframes slideInLeft {
    from {
      opacity: 0;
      transform: translateX(-100%);
    }
    to {
      opacity: 1;
      transform: translateX(0);
    }
  }

  .position-top-center .toast,
  .position-bottom-center .toast {
    animation-name: slideInCenter;
  }

  @keyframes slideInCenter {
    from {
      opacity: 0;
      transform: translateX(-50%) translateY(-20px);
    }
    to {
      opacity: 1;
      transform: translateX(-50%) translateY(0);
    }
  }

  .toast-icon {
    width: 24px;
    height: 24px;
    flex-shrink: 0;
  }

  .toast-message {
    flex: 1;
    font-size: 14px;
    font-weight: 500;
    color: white;
    line-height: 1.4;
  }

  .toast-close {
    width: 24px;
    height: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: none;
    border: none;
    cursor: pointer;
    opacity: 0.7;
    transition: opacity 0.2s;
    flex-shrink: 0;
  }

  .toast-close:hover {
    opacity: 1;
  }

  .toast-close svg {
    width: 16px;
    height: 16px;
  }

  .toast-progress {
    position: absolute;
    bottom: 0;
    left: 0;
    height: 3px;
    opacity: 0.3;
    animation: shrink linear forwards;
  }

  @keyframes shrink {
    from { width: 100%; }
    to { width: 0%; }
  }

  /* Mobile */
  @media (max-width: 480px) {
    .toast-container {
      left: 16px;
      right: 16px;
      max-width: none;
    }

    .position-top-center,
    .position-bottom-center {
      left: 16px;
      right: 16px;
      transform: none;
    }

    .position-top-center .toast,
    .position-bottom-center .toast {
      animation-name: slideIn;
    }
  }
</style>