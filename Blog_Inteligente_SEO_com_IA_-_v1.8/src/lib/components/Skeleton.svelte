<script lang="ts">
  let { 
    variant = 'text',
    lines = 3,
    width = '100%',
    height = '20px'
  } = $props();
</script>

{#if variant === 'card'}
  <div class="skeleton-card">
    <div class="skeleton-image"></div>
    <div class="skeleton-content">
      <div class="skeleton-line" style="width: 80%; height: 24px;"></div>
      {#each Array(lines) as _, i}
        <div class="skeleton-line" style="width: {100 - (i * 15)}%;"></div>
      {/each}
    </div>
  </div>
{:else if variant === 'avatar'}
  <div class="skeleton-avatar" style="width: {width}; height: {width};"></div>
{:else if variant === 'button'}
  <div class="skeleton-button" style="width: {width};"></div>
{:else}
  {#each Array(lines) as _, i}
    <div 
      class="skeleton-line" 
      style="width: {i === lines - 1 ? '60%' : width}; height: {height};"
    ></div>
  {/each}
{/if}

<style>
  .skeleton-line,
  .skeleton-image,
  .skeleton-avatar,
  .skeleton-button {
    background: linear-gradient(
      90deg,
      #f0f0f0 25%,
      #e8e8e8 50%,
      #f0f0f0 75%
    );
    background-size: 200% 100%;
    animation: shimmer 1.5s infinite;
    border-radius: 4px;
  }

  .skeleton-card {
    display: flex;
    flex-direction: column;
    gap: 12px;
    padding: 16px;
    background: white;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }

  .skeleton-image {
    width: 100%;
    height: 180px;
    border-radius: 8px;
  }

  .skeleton-content {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .skeleton-avatar {
    border-radius: 50%;
  }

  .skeleton-button {
    height: 40px;
    border-radius: 8px;
  }

  @keyframes shimmer {
    0% { background-position: 200% 0; }
    100% { background-position: -200% 0; }
  }
</style>