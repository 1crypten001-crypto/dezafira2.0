<script lang="ts">
  import type { Snippet } from 'svelte';

  let {
    value = 0,
    max = 100,
    showLabel = true,
    showPercent = true,
    variant = 'default',
    size = 'md',
    animated = true,
    striped = false,
    label
  }: {
    value?: number;
    max?: number;
    showLabel?: boolean;
    showPercent?: boolean;
    variant?: 'default' | 'success' | 'warning' | 'danger';
    size?: 'sm' | 'md' | 'lg';
    animated?: boolean;
    striped?: boolean;
    label?: Snippet;
  } = $props();

  let percent = $derived(Math.min(100, Math.max(0, (value / max) * 100)));

  const variants: Record<string, string> = {
    default: '#4a90d9',
    success: '#10b981',
    warning: '#f59e0b',
    danger: '#ef4444'
  };

  let barColor = $derived(variants[variant] || variants.default);
</script>

<div class="progress size-{size}">
  {#if showLabel}
    <div class="progress-header">
      {#if label}
        {@render label()}
      {:else}
        <span class="progress-label">Progresso</span>
      {/if}
      {#if showPercent}
        <span class="progress-value">{Math.round(percent)}%</span>
      {/if}
    </div>
  {/if}

  <div class="progress-track">
    <div 
      class="progress-bar"
      class:animated
      class:striped
      style="width: {percent}%; background-color: {barColor}"
      role="progressbar"
      aria-valuenow={value}
      aria-valuemin={0}
      aria-valuemax={max}
    >
      {#if animated}
        <div class="progress-glow"></div>
      {/if}
    </div>
  </div>
</div>

<style>
  .progress {
    width: 100%;
  }

  .progress-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
  }

  .progress-label {
    font-size: 14px;
    font-weight: 500;
    color: #374151;
  }

  .progress-value {
    font-size: 14px;
    font-weight: 600;
    color: #6b7280;
  }

  .progress-track {
    width: 100%;
    background: #e5e7eb;
    border-radius: 100px;
    overflow: hidden;
  }

  .progress-bar {
    height: 100%;
    border-radius: 100px;
    position: relative;
    transition: width 0.5s ease;
  }

  /* Sizes */
  .size-sm .progress-track {
    height: 6px;
  }

  .size-md .progress-track {
    height: 10px;
  }

  .size-lg .progress-track {
    height: 16px;
  }

  /* Striped */
  .progress-bar.striped {
    background-image: linear-gradient(
      45deg,
      rgba(255, 255, 255, 0.15) 25%,
      transparent 25%,
      transparent 50%,
      rgba(255, 255, 255, 0.15) 50%,
      rgba(255, 255, 255, 0.15) 75%,
      transparent 75%,
      transparent
    );
    background-size: 1rem 1rem;
  }

  /* Animated */
  .progress-bar.animated.striped {
    animation: stripes 1s linear infinite;
  }

  @keyframes stripes {
    0% { background-position: 1rem 0; }
    100% { background-position: 0 0; }
  }

  /* Glow effect */
  .progress-glow {
    position: absolute;
    top: 0;
    right: 0;
    width: 30%;
    height: 100%;
    background: linear-gradient(
      90deg,
      transparent,
      rgba(255, 255, 255, 0.4),
      transparent
    );
    animation: glow 2s ease-in-out infinite;
  }

  @keyframes glow {
    0%, 100% { opacity: 0; transform: translateX(-100%); }
    50% { opacity: 1; transform: translateX(200%); }
  }
</style>