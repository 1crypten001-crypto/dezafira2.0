<script lang="ts">
  import { onMount } from 'svelte';

  let { 
    show = false,
    progress = 0,
    message = 'Carregando...',
    size = 'md'
  }: {
    show?: boolean;
    progress?: number;
    message?: string;
    size?: 'sm' | 'md' | 'lg';
  } = $props();

  const sizes = {
    sm: '2px',
    md: '4px',
    lg: '6px'
  } as const;

  const heights = {
    sm: '20px',
    md: '32px',
    lg: '48px'
  } as const;

  let visible = $state(false);

  $effect(() => {
		if (show && !visible) {
			visible = true;
		} else if (!show && visible) {
			setTimeout(() => { visible = false; }, 300);
		}
	});
</script>

{#if visible}
  <div class="loading-overlay" class:hide={!show}>
    <div class="loading-container" style="height: {heights[size]}">
      {#if size !== 'sm'}
        <span class="loading-message">{message}</span>
      {/if}
      
      <div class="loading-bar-container" style="height: {sizes[size]}">
        {#if progress > 0}
          <div class="loading-progress" style="width: {progress}%"></div>
        {:else}
          <div class="loading-indeterminate"></div>
        {/if}
      </div>
      
      {#if progress > 0 && size !== 'sm'}
        <span class="loading-percent">{Math.round(progress)}%</span>
      {/if}
    </div>
  </div>
{/if}

<style>
  .loading-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    z-index: 9999;
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(4px);
    transition: opacity 0.3s ease;
  }

  .loading-overlay.hide {
    opacity: 0;
    pointer-events: none;
  }

  .loading-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 12px;
    padding: 20px;
  }

  .loading-message {
    font-size: 14px;
    color: #666;
    font-weight: 500;
  }

  .loading-percent {
    font-size: 12px;
    color: #999;
  }

  .loading-bar-container {
    width: 200px;
    max-width: 80%;
    background: #e0e0e0;
    border-radius: 4px;
    overflow: hidden;
  }

  .loading-progress {
    height: 100%;
    background: linear-gradient(
      90deg,
      #4a90d9,
      #67b26f,
      #4a90d9
    );
    background-size: 200% 100%;
    animation: gradient 1.5s ease infinite;
    transition: width 0.3s ease;
    border-radius: 4px;
  }

  .loading-indeterminate {
    height: 100%;
    width: 30%;
    background: linear-gradient(
      90deg,
      #4a90d9 0%,
      #67b26f 50%,
      #4a90d9 100%
    );
    background-size: 200% 100%;
    animation: indeterminate 1.5s ease infinite;
    border-radius: 4px;
  }

  @keyframes gradient {
    0% { background-position: 200% 0; }
    100% { background-position: -200% 0; }
  }

  @keyframes indeterminate {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(400%); }
  }
</style>
