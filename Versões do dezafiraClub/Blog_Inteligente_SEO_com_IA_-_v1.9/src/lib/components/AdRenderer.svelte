<script lang="ts">
    import { page } from '$app/stores';
    import { t } from '$lib/i18n';

    interface Ad {
        id: number;
        name: string;
        placement: string;
        type: string;
        content: string | null;
        image_url: string | null;
        link_url: string | null;
        weight: number;
        style: string | null;
        youtube_video_url?: string | null;
    }

    let { ads, placement }: { ads: Ad[]; placement: string } = $props();
    const lang = $derived($page.data.language || 'pt');

    function selectAd(availableAds: Ad[]) {
        if (!availableAds || availableAds.length === 0) return null;

        const totalWeight = availableAds.reduce(
            (sum, ad) => sum + (ad.weight || 1),
            0,
        );
        let random = Math.random() * totalWeight;

        for (const ad of availableAds) {
            random -= ad.weight || 1;
            if (random <= 0) return ad;
        }

        return availableAds[0];
    }

    function parseStyle(styleStr: string | null): Record<string, string> {
        if (!styleStr) return {};
        try {
            return JSON.parse(styleStr) as Record<string, string>;
        } catch {
            return {};
        }
    }

    function getYouTubeId(url: string | null | undefined): string | null {
        if (!url) return null;
        let str = url.trim();
        if (!str) return null;

        const iframeMatch = str.match(/src=["']([^"']+)["']/i);
        if (iframeMatch) {
            str = iframeMatch[1];
        }

        if (/^[a-zA-Z0-9_-]{11}$/.test(str)) {
            return str;
        }

        const patterns = [
            /(?:youtube\.com\/(?:watch\?.*v=|embed\/|shorts\/|live\/|v\/)|youtu\.be\/)([a-zA-Z0-9_-]{11})/,
            /[?&]v=([a-zA-Z0-9_-]{11})/
        ];

        for (const pattern of patterns) {
            const match = str.match(pattern);
            if (match && match[1]) {
                return match[1];
            }
        }

        if (str.includes('youtu')) {
            const fallback = str.match(/([a-zA-Z0-9_-]{11})/);
            if (fallback && fallback[1]) return fallback[1];
        }

        return null;
    }

    const selectedAd = $derived(selectAd(ads));
    const customStyle = $derived(parseStyle(selectedAd?.style || null));

    let videoExpanded = $state(false);
    const videoId = $derived(selectedAd ? getYouTubeId(selectedAd.youtube_video_url || null) : null);

    // An ad is treated as a video ad if it has a valid youtube_video_url, regardless of type
    const isVideoAd = $derived(!!videoId);

    $effect(() => {
        videoExpanded = false;
        if (videoId) {
            const timer = setTimeout(() => {
                videoExpanded = true;
            }, 2000);
            return () => clearTimeout(timer);
        }
    });
</script>

{#if selectedAd}
    <div
        class="ad-container ad-{placement}"
        class:ad-native={selectedAd.type === 'native' && !isVideoAd}
        class:ad-video={isVideoAd}
        class:expanded={isVideoAd && videoExpanded}
        data-ad-id={selectedAd.id}
        style={Object.entries(customStyle)
            .map(([k, v]) => `--ad-${k}: ${v}`)
            .join('; ')}
    >
        {#if isVideoAd}
            <div class="ad-video-header">
                <span class="video-pulse-container">
                    <span class="pulse-dot"></span>
                </span>
                {#if selectedAd.link_url}
                    <a href={selectedAd.link_url} target="_blank" rel="nofollow noopener" class="ad-video-title">
                        {selectedAd.name}
                    </a>
                {:else}
                    <h4 class="ad-video-title">{selectedAd.name}</h4>
                {/if}
            </div>
            <div class="ad-video-wrapper">
                {#if videoExpanded}
                    <iframe
                        src="https://www.youtube.com/embed/{videoId}?autoplay=1&mute=1&enablejsapi=1"
                        title={selectedAd.name}
                        frameborder="0"
                        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                        allowfullscreen
                    ></iframe>
                {:else}
                    <button class="ad-video-thumbnail" onclick={() => videoExpanded = true}>
                        <img src="https://img.youtube.com/vi/{videoId}/maxresdefault.jpg" alt={selectedAd.name} />
                        <div class="ad-play-button">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                                <polygon points="5 3 19 12 5 21 5 3"/>
                            </svg>
                        </div>
                    </button>
                {/if}
            </div>
        {:else if selectedAd.type === 'native'}
            <a href={selectedAd.link_url} target="_blank" rel="nofollow noopener" class="native-ad-link">
                {#if selectedAd.image_url}
                    <div class="native-image-wrapper">
                        <img src={selectedAd.image_url} alt={selectedAd.name} class="native-image" />
                        <span class="native-badge">{t(lang, 'ad.exclusive')}</span>
                    </div>
                {/if}
                <div class="native-content">
                    <span class="native-label">{selectedAd.content || t(lang, 'ad.recommended')}</span>
                    <h4 class="native-title">{selectedAd.name}</h4>
                    {#if selectedAd.link_url}
                        <span class="native-cta">{t(lang, 'ad.learn_more')}</span>
                    {/if}
                </div>
            </a>
        {:else if selectedAd.type === 'image'}
            <a
                href={selectedAd.link_url}
                target="_blank"
                rel="nofollow noopener"
                class="ad-link"
            >
                <img
                    src={selectedAd.image_url}
                    alt={selectedAd.name}
                    class="ad-image"
                />
            </a>
        {:else if selectedAd.type === 'html'}
            <div class="ad-html">
                {@html selectedAd.content}
            </div>
        {:else if selectedAd.type === 'text'}
            <a
                href={selectedAd.link_url}
                target="_blank"
                rel="nofollow noopener"
                class="ad-text-link"
            >
                {selectedAd.content}
            </a>
        {/if}
        <span class="ad-label">{t(lang, 'ad.label')}</span>
    </div>
{/if}


<style>
    .ad-container {
        position: relative;
        width: 100%;
        margin: 2rem 0;
        background: var(--bg-secondary);
        border: 1px solid var(--border-light);
        border-radius: 12px;
        overflow: hidden;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }

    .ad-container:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-md);
    }

    .ad-sidebar {
        margin: 0;
        min-height: 250px;
        border-radius: 8px;
    }

    /* When sidebar has a video ad, reset min-height and use card style */
    .ad-sidebar.ad-video {
        min-height: unset;
    }

    .ad-home_middle {
        max-height: 250px;
        border-radius: 12px;
    }

    .ad-post_inline {
        margin: 3rem 0;
        border: none;
        background: transparent;
        border-top: 1px solid var(--border-light);
        border-bottom: 1px solid var(--border-light);
        padding: 1.5rem 0;
        border-radius: 0;
    }

    .ad-in_article {
        margin: 2rem 0;
        background: linear-gradient(135deg, var(--bg-secondary) 0%, var(--bg-primary) 100%);
        border: 1px solid var(--border-color);
        border-radius: 16px;
        padding: 1.5rem;
    }

    .ad-image {
        max-width: 100%;
        height: auto;
        display: block;
    }

    .ad-link {
        display: block;
        width: 100%;
    }

    .ad-text-link {
        padding: 1.5rem;
        color: var(--text-primary);
        font-weight: 600;
        text-decoration: underline;
        text-align: center;
        transition: color 0.2s ease;
    }

    .ad-text-link:hover {
        color: var(--accent-color, #3b82f6);
    }

    .ad-label {
        position: absolute;
        top: 8px;
        right: 10px;
        font-size: 10px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: var(--text-muted);
        opacity: 0.6;
        pointer-events: none;
        font-family: var(--font-sans);
    }

    .ad-html {
        width: 100%;
        display: flex;
        justify-content: center;
    }

    /* Native Ad Styles */
    .ad-native {
        background: var(--bg-primary);
        border: 1px solid var(--border-light);
        padding: 0;
        overflow: hidden;
    }

    .native-ad-link {
        display: block;
        text-decoration: none;
        color: inherit;
        width: 100%;
    }

    .native-image-wrapper {
        position: relative;
        width: 100%;
        aspect-ratio: 16/9;
        overflow: hidden;
    }

    .native-image {
        width: 100%;
        height: 100%;
        object-fit: cover;
        transition: transform 0.4s ease;
    }

    .native-ad-link:hover .native-image {
        transform: scale(1.03);
    }

    .native-badge {
        position: absolute;
        top: 12px;
        left: 12px;
        background: var(--accent-color, #3b82f6);
        color: white;
        padding: 4px 10px;
        border-radius: 4px;
        font-size: 0.65rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-family: var(--font-sans);
    }

    .native-content {
        padding: 1.25rem;
    }

    .native-label {
        display: block;
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: var(--accent-color, #3b82f6);
        margin-bottom: 0.5rem;
        font-family: var(--font-sans);
    }

    .native-title {
        font-family: var(--font-sans);
        font-size: 1rem;
        font-weight: 600;
        line-height: 1.4;
        color: var(--text-primary);
        margin: 0 0 0.5rem 0;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
        transition: color 0.2s ease;
    }

    .native-ad-link:hover .native-title {
        color: var(--accent-color, #3b82f6);
    }

    .native-cta {
        display: inline-block;
        font-size: 0.8rem;
        font-weight: 600;
        color: var(--text-muted);
        transition: color 0.2s ease, transform 0.2s ease;
    }

    .native-ad-link:hover .native-cta {
        color: var(--accent-color, #3b82f6);
        transform: translateX(4px);
    }

    /* In-Article Native Ad (more integrated look) */
    .ad-in_article .native-ad-link {
        display: grid;
        grid-template-columns: 120px 1fr;
        gap: 1rem;
        align-items: center;
    }

    .ad-in_article .native-image-wrapper {
        aspect-ratio: 1/1;
        border-radius: 8px;
    }

    .ad-in_article .native-content {
        padding: 0;
    }

    .ad-in_article .native-title {
        font-size: 0.95rem;
        margin-bottom: 0.25rem;
    }

    .ad-in_article .native-label {
        margin-bottom: 0.25rem;
    }

    .ad-in_article .native-badge {
        display: none;
    }

    @media (max-width: 640px) {
        .ad-in_article .native-ad-link {
            grid-template-columns: 80px 1fr;
            gap: 0.75rem;
        }

        .ad-in_article .native-content {
            padding: 0;
        }
    }

    /* Video Ad Styles */
    .ad-container.ad-video {
        max-height: 0;
        opacity: 0;
        overflow: hidden;
        transform: scale(0.95);
        padding: 0;
        margin: 0;
        border: none;
        box-shadow: none;
        transition: max-height 0.8s cubic-bezier(0.16, 1, 0.3, 1),
                    opacity 0.8s cubic-bezier(0.16, 1, 0.3, 1),
                    transform 0.8s cubic-bezier(0.16, 1, 0.3, 1),
                    padding 0.8s cubic-bezier(0.16, 1, 0.3, 1),
                    margin 0.8s cubic-bezier(0.16, 1, 0.3, 1);
        display: flex;
        flex-direction: column;
        gap: 0.75rem;
        align-items: stretch;
        justify-content: flex-start;
        background: var(--bg-primary);
        border: 1px solid var(--border-color);
        border-radius: 12px;
    }
    
    .ad-container.ad-video.expanded {
        max-height: 800px;
        opacity: 1;
        transform: scale(1);
        padding: 1.25rem;
        margin: 1.5rem 0;
        border: 1px solid var(--border-color);
        box-shadow: var(--shadow-md);
    }

    /* Style for sidebar video ads specifically to blend into the outer widget card */
    .ad-container.ad-sidebar.ad-video.expanded {
        padding: 1.25rem;
        margin: 0;
        border: none;
        box-shadow: none;
        background: transparent;
    }

    
    .ad-video-header {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        width: 100%;
        margin-top: 0.25rem;
    }
    
    .video-pulse-container {
        display: inline-flex;
        align-items: center;
        justify-content: center;
    }
    
    .pulse-dot {
        width: 8px;
        height: 8px;
        background-color: #ef4444;
        border-radius: 50%;
        display: inline-block;
        box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7);
        animation: pulse-ad 1.5s infinite;
    }
    
    @keyframes pulse-ad {
        0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7); }
        70% { transform: scale(1); box-shadow: 0 0 0 8px rgba(239, 68, 68, 0); }
        100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
    }
    
    .ad-video-title {
        margin: 0;
        font-family: var(--font-sans);
        font-size: 0.95rem;
        font-weight: 600;
        color: var(--text-primary);
        text-decoration: none;
    }
    a.ad-video-title:hover {
        color: var(--accent-color, #3b82f6);
        text-decoration: underline;
    }
    
    .ad-video-wrapper {
        position: relative;
        width: 100%;
        padding-bottom: 56.25%; /* 16:9 */
        height: 0;
        border-radius: 8px;
        overflow: hidden;
        background: #000;
        border: 1px solid var(--border-light);
    }
    
    .ad-video-wrapper iframe {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
    }
    
    .ad-video-thumbnail {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        padding: 0;
        border: none;
        background: transparent;
    }
    
    .ad-video-thumbnail img {
        width: 100%;
        height: 100%;
        object-fit: cover;
        opacity: 0.6;
    }
    
    .ad-play-button {
        position: absolute;
        width: 48px;
        height: 48px;
        background: rgba(239, 68, 68, 0.9);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #fff;
        box-shadow: 0 4px 15px rgba(239, 68, 68, 0.4);
        transition: transform 0.2s ease;
    }
    .ad-play-button svg {
        margin-left: 2px;
    }
</style>