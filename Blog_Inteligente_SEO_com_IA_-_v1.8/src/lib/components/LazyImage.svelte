<script lang="ts">
  import { onMount } from 'svelte';

  let loadedImages = $state(new Set<number>());
  let observer: IntersectionObserver | null = null;

  let { 
    images = []
  }: { 
    images: Array<{
      src: string;
      alt: string;
      id: number;
      class?: string;
    }> 
  } = $props();

  onMount(() => {
    if (typeof IntersectionObserver !== 'undefined') {
      observer = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting) {
              const img = entry.target as HTMLElement;
              const id = parseInt(img.dataset.id || '0');
              loadedImages.add(id);
              loadedImages = loadedImages; // trigger reactivity
              observer?.unobserve(img);
            }
          });
        },
        {
          rootMargin: '50px 0px',
          threshold: 0.1
        }
      );
    }

    return () => {
      observer?.disconnect();
    };
  });

  function observe(node: HTMLElement, id: number) {
    if (observer) {
      node.dataset.id = id.toString();
      observer.observe(node);
    }
  }
</script>

{#each images as img (img.id)}
  <div
    class="lazy-image-container {img.class || ''}"
    use:observe={img.id}
  >
    {#if loadedImages.has(img.id)}
      <img
        src={img.src}
        alt={img.alt}
        class="lazy-loaded"
        loading="lazy"
      />
    {:else}
      <div class="lazy-placeholder">
        <div class="skeleton"></div>
      </div>
    {/if}
  </div>
{/each}

<style>
  .lazy-image-container {
    width: 100%;
    height: 100%;
    position: relative;
    overflow: hidden;
    background: #f0f0f0;
  }

  .lazy-placeholder {
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .skeleton {
    width: 100%;
    height: 100%;
    background: linear-gradient(
      90deg,
      #f0f0f0 25%,
      #e0e0e0 50%,
      #f0f0f0 75%
    );
    background-size: 200% 100%;
    animation: shimmer 1.5s infinite;
  }

  @keyframes shimmer {
    0% { background-position: 200% 0; }
    100% { background-position: -200% 0; }
  }

  .lazy-loaded {
    width: 100%;
    height: 100%;
    object-fit: cover;
    animation: fadeIn 0.3s ease-in;
  }

  @keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
  }
</style>