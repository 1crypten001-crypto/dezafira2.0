<script lang="ts">
  import { optimizeImageUrl } from '$lib/image-optimizer';
  import { t } from '$lib/i18n';

  type StoryItem = {
    id: number;
    title: string;
    slug: string;
    cover_image?: string | null;
    poster_portrait?: string | null;
  };

  let {
    stories = [],
    language = 'pt'
  }: {
    stories?: StoryItem[];
    language?: string;
  } = $props();

  function thumb(story: StoryItem) {
    return story.poster_portrait || story.cover_image || '';
  }

  function initial(title: string) {
    return (title || '?').trim().charAt(0).toUpperCase();
  }
</script>

{#if stories && stories.length > 0}
  <section class="stories-bar" aria-label={t(language, 'stories.bar_label')}>
    <div class="stories-track">
      {#each stories as story (story.id)}
        <a
          href="/stories/{story.slug}"
          class="story-bubble"
          title={story.title}
          data-sveltekit-reload
        >
          <span class="ring">
            {#if thumb(story)}
              <img
                src={optimizeImageUrl(thumb(story), 160)}
                alt=""
                class="avatar"
                width="64"
                height="64"
                loading="lazy"
              />
            {:else}
              <span class="avatar placeholder">{initial(story.title)}</span>
            {/if}
          </span>
          <span class="label">{story.title}</span>
        </a>
      {/each}
    </div>
  </section>
{/if}

<style>
  /* Only bubbles — no box/background so home hero isn't cut off */
  .stories-bar {
    width: 100%;
    background: transparent;
    border: none;
    position: relative;
    z-index: 1;
  }

  .stories-track {
    display: flex;
    gap: 0.75rem;
    overflow-x: auto;
    padding: 0.5rem 1rem 0.15rem;
    max-width: 1200px;
    margin: 0 auto;
    scrollbar-width: none;
    -webkit-overflow-scrolling: touch;
  }

  .stories-track::-webkit-scrollbar {
    display: none;
  }

  .story-bubble {
    flex: 0 0 auto;
    width: 72px;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.3rem;
    text-decoration: none;
    color: var(--text-primary, #0f172a);
  }

  .ring {
    width: 62px;
    height: 62px;
    border-radius: 50%;
    padding: 2px;
    background: linear-gradient(
      135deg,
      #f59e0b 0%,
      #ec4899 45%,
      #8b5cf6 100%
    );
    display: grid;
    place-items: center;
    transition: transform 0.15s ease;
  }

  .story-bubble:hover .ring,
  .story-bubble:focus-visible .ring {
    transform: scale(1.05);
  }

  .avatar {
    width: 54px;
    height: 54px;
    border-radius: 50%;
    object-fit: cover;
    border: 2px solid var(--bg-primary, #fff);
    background: var(--bg-secondary, #f1f5f9);
    display: block;
    box-shadow: 0 1px 3px rgba(15, 23, 42, 0.12);
  }

  .avatar.placeholder {
    display: grid;
    place-items: center;
    font-weight: 700;
    font-size: 1.15rem;
    color: var(--text-secondary, #64748b);
  }

  .label {
    font-size: 0.65rem;
    line-height: 1.15;
    max-width: 72px;
    text-align: center;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    color: var(--text-secondary, #475569);
  }
</style>
