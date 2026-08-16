<script lang="ts">
  import { page } from '$app/stores';
  import { t, formatDate as fmtDate } from '$lib/i18n';
    import { optimizeImageUrl } from "$lib/image-optimizer";
    import { goto } from "$app/navigation";
    import type { PageData } from "./$types";
    import AdRenderer from "$lib/components/AdRenderer.svelte";
    import { ageState } from "$lib/stores/age.svelte";
    import Pagination from "$lib/components/Pagination.svelte";

    let { data }: { data: PageData } = $props();
    const lang = $derived($page.data.language || 'pt');

    let searchInput = $state("");

    function formatDate(dateString: string) {
        const date = new Date(dateString);
        return date
            .toLocaleDateString(lang === "en" ? "en-US" : lang === "es" ? "es-ES" : "pt-BR", {
                day: "numeric",
                month: "short",
                year: "numeric",
            })
            .replace(".", "");
    }

    function handleSearch(e: Event) {
        e.preventDefault();
        goto(`/?q=${encodeURIComponent(searchInput)}`);
    }

    function getPostImage(post: any) {
        if (post.cover_image) return post.cover_image;
        const match = post.content?.match(/<img[^>]+src="([^">]+)"/);
        if (match) return match[1];
        return `https://picsum.photos/seed/${post.id}/800/600`;
    }

    function hasNoImage(post: any) {
        if (post.cover_image && post.cover_image.trim().length > 0) return false;
        if (post.content && post.content.includes('<img')) {
            const match = post.content.match(/<img[^>]+src="([^">]+)"/);
            if (match && match[1]) return false;
        }
        return true;
    }

    function getPlaceholderBackground(post: any) {
        const gradients = [
            'linear-gradient(135deg, #e0f2fe 0%, #bae6fd 100%)', // Blue
            'linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%)', // Emerald
            'linear-gradient(135deg, #fef9c3 0%, #fef08a 100%)', // Yellow
            'linear-gradient(135deg, #fce7f3 0%, #fbcfe8 100%)', // Pink
            'linear-gradient(135deg, #f3e8ff 0%, #e9d5ff 100%)', // Purple
            'linear-gradient(135deg, #ffedd5 0%, #fed7aa 100%)', // Orange
            'linear-gradient(135deg, #ccfbf1 0%, #99f6e4 100%)', // Teal
            'linear-gradient(135deg, #ffe4e6 0%, #fecdd3 100%)', // Rose
            'linear-gradient(135deg, #e0e7ff 0%, #c7d2fe 100%)', // Indigo
            'linear-gradient(135deg, #fef3c7 0%, #fde68a 100%)'  // Amber
        ];
        const idStr = String(post.id || post.slug || '0');
        let hash = 0;
        for (let i = 0; i < idStr.length; i++) {
            hash = idStr.charCodeAt(i) + ((hash << 5) - hash);
        }
        const index = Math.abs(hash) % gradients.length;
        return gradients[index];
    }
</script>

<svelte:head>
    <title>{data.settings?.site_title || "Blog"} | {data.currentCategory?.name || "Categoria"}</title>
</svelte:head>

<div class="page-wrapper container">
    <header class="category-header">
        <div class="header-content">
            <span class="category-badge">{t(lang, "category.explore")}</span>
            <h1 class="category-title">{data.currentCategory?.name || "Posts"}</h1>
            <div class="category-stats">
                <span class="stat-item">{data.posts.length} artigos encontrados</span>
            </div>
        </div>
    </header>

    <div class="main-layout">
        <div class="content-area">
            {#if data.posts.length === 0}
                <div class="empty-state">
                    <div class="empty-icon">
                        <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1">
                            <path d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                        </svg>
                    </div>
                    <h3>{t(lang, "category.empty_title")}</h3>
                    <p>Ainda não publicamos artigos nesta seção. Volte em breve!</p>
                    <a href="/" class="btn btn-primary">{t(lang, "category.view_all")}</a>
                </div>
            {:else}
                <div class="posts-masonry">
                    {#each data.posts as post}
                        <article class="post-card">
                            <a href="/post/{post.slug}" class="post-image-link">
                                {#if hasNoImage(post)}
                                    <div class="no-image-placeholder" style="background: {getPlaceholderBackground(post)}">
                                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="placeholder-icon">
                                            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                                            <polyline points="14 2 14 8 20 8"></polyline>
                                            <line x1="16" y1="13" x2="8" y2="13"></line>
                                            <line x1="16" y1="17" x2="8" y2="17"></line>
                                            <polyline points="10 9 9 9 8 9"></polyline>
                                        </svg>
                                        <div class="no-image-placeholder-title">
                                            {post.title}
                                        </div>
                                    </div>
                                {:else}
                                    <img
                                        src={optimizeImageUrl(getPostImage(post), 800)}
                                        alt={post.title}
                                        class="post-image"
                                        class:blurred={post.is_18_plus && !ageState.confirmed}
                                        loading="lazy"
                                        width="800"
                                        height="450"
                                    />
                                {/if}
                            </a>
                            <div class="post-info">
                                <div class="post-meta">
                                    <span class="post-date">{formatDate(post.created_at)}</span>
                                    {#if post.is_18_plus}
                                        <span class="age-badge-small">+18</span>
                                    {/if}
                                </div>
                                <h2 class="post-title">
                                    <a href="/post/{post.slug}">{post.title}</a>
                                </h2>
                            </div>
                        </article>
                    {/each}
                </div>
            {/if}

            <Pagination
                currentPage={data.currentPage}
                totalPages={data.totalPages}
            />
        </div>

        <aside class="sidebar">
            <div class="widget search-widget">
                <form onsubmit={handleSearch} class="search-form-premium">
                    <div class="search-input-wrapper">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <circle cx="11" cy="11" r="8"></circle>
                            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                        </svg>
                        <input
                            type="text"
                            bind:value={searchInput}
                            placeholder={t(lang, "category.search_label")}
                            class="search-input"
                        />
                    </div>
                    <button type="submit" class="search-submit">{t(lang, "category.search_btn")}</button>
                </form>
            </div>

            {#if data.sidebarAds && data.sidebarAds.length > 0}
                <div class="widget ad-widget">
                    <AdRenderer ads={data.sidebarAds} placement="sidebar" />
                </div>
            {/if}

            <div class="widget categories-widget">
                <h2 class="widget-title">{t(lang, "common.categories")}</h2>
                <ul class="categories-list">
                    <li>
                        <a href="/" class="category-link">
                            <svg
                                width="16"
                                height="16"
                                viewBox="0 0 24 24"
                                fill="none"
                                stroke="currentColor"
                                stroke-width="2"
                            >
                                <rect x="3" y="3" width="7" height="7" />
                                <rect x="14" y="3" width="7" height="7" />
                                <rect x="3" y="14" width="7" height="7" />
                                <rect x="14" y="14" width="7" height="7" />
                            </svg>
                            {t(lang, "common.all_posts")}
                        </a>
                    </li>
                    {#each data.categories as cat}
                        <li>
                            <a
                                href="/category/{cat.slug}"
                                class="category-link"
                                class:active={cat.slug === data.categorySlug}
                            >
                                <svg
                                    width="16"
                                    height="16"
                                    viewBox="0 0 24 24"
                                    fill="none"
                                    stroke="currentColor"
                                    stroke-width="2"
                                >
                                    <path
                                        d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z"
                                    />
                                </svg>
                                {cat.name}
                            </a>
                        </li>
                    {/each}
                </ul>
            </div>

            <div class="widget popular-widget">
                <h2 class="widget-title">{t(lang, "common.popular_posts")}</h2>
                <div class="popular-list">
                    {#each data.popularPosts.slice(0, 4) as pop, i}
                        <a href="/post/{pop.slug}" class="popular-item">
                            <span class="popular-number">{i + 1}</span>
                            <div class="popular-thumb-wrapper">
                                {#if hasNoImage(pop)}
                                    <div class="popular-placeholder" style="background: {getPlaceholderBackground(pop)}">
                                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="placeholder-small-icon">
                                            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                                        </svg>
                                    </div>
                                {:else}
                                    <img
                                        src={optimizeImageUrl(getPostImage(pop), 200)}
                                        alt={pop.title}
                                        class="popular-thumb"
                                        loading="lazy"
                                        width="80"
                                        height="60"
                                    />
                                {/if}
                            </div>
                            <div class="popular-info">
                                <h4>{pop.title}</h4>
                                <span class="popular-date"
                                    >{formatDate(pop.created_at)}</span
                                >
                            </div>
                        </a>
                    {/each}
                </div>
            </div>
        </aside>
    </div>
</div>

<style>
    .page-wrapper {
        padding: 3rem 0 5rem;
    }

    .category-header {
        margin-bottom: 4rem;
        text-align: center;
        padding: 4rem 0;
        background: var(--bg-secondary);
        border-radius: 24px;
        border: 1px solid var(--border-light);
        position: relative;
        overflow: hidden;
    }

    .category-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, transparent, var(--text-primary), transparent);
    }

    .category-badge {
        display: inline-block;
        background: var(--text-primary);
        color: var(--bg-primary);
        padding: 0.4rem 1.2rem;
        border-radius: 100px;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }

    .category-title {
        font-family: var(--font-serif);
        font-size: clamp(2.5rem, 8vw, 4.5rem);
        font-weight: 400;
        margin: 0 0 1.5rem 0;
        line-height: 1.1;
        letter-spacing: -0.02em;
    }

    .category-stats {
        color: var(--text-secondary);
        font-family: var(--font-serif);
        font-size: 1rem;
        font-style: italic;
        opacity: 0.8;
    }

    .main-layout {
        display: grid;
        grid-template-columns: 1fr 320px;
        gap: 4rem;
    }

    .posts-masonry {
        column-count: 2;
        column-gap: 2.5rem;
    }

    .post-card {
        break-inside: avoid;
        margin-bottom: 2.5rem;
        display: inline-block;
        width: 100%;
        background: var(--bg-primary);
        border: 1px solid var(--border-light);
        border-radius: 24px;
        overflow: hidden;
        transition: all 0.4s cubic-bezier(0.165, 0.84, 0.44, 1);
        box-shadow: var(--shadow-sm);
    }

    .post-card:hover {
        box-shadow: var(--shadow-xl);
        transform: translateY(-8px);
        border-color: var(--text-primary);
    }

    .post-image-link {
        display: block;
        width: 100%;
        overflow: hidden;
        background: var(--bg-secondary);
    }

    .post-image {
        width: 100%;
        height: auto;
        display: block;
        transition: transform 0.6s cubic-bezier(0.165, 0.84, 0.44, 1);
    }

    .post-card:hover .post-image {
        transform: scale(1.05);
    }

    .post-info {
        padding: 1.75rem;
    }

    .post-meta {
        margin-bottom: 0.75rem;
    }

    .post-date {
        font-size: 0.75rem;
        color: var(--text-tertiary);
        text-transform: uppercase;
        letter-spacing: 1.5px;
        font-weight: 600;
    }

    .post-title {
        font-size: 1.4rem;
        margin: 0;
        line-height: 1.4;
        font-family: var(--font-serif);
    }

    .post-title a {
        color: var(--text-primary);
        text-decoration: none;
        transition: color 0.3s ease;
    }

    .post-title a:hover {
        color: var(--text-secondary);
    }

    .sidebar {
        position: sticky;
        top: 2rem;
        display: flex;
        flex-direction: column;
        gap: 2.5rem;
    }

    .widget {
        background: var(--bg-primary);
        border: 1px solid var(--border-light);
        border-radius: 20px;
        padding: 1.75rem;
        box-shadow: var(--shadow-sm);
    }

    .widget-title {
        font-size: 0.8rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-bottom: 1.5rem;
        padding-bottom: 0.75rem;
        border-bottom: 2px solid var(--bg-secondary);
        color: var(--text-primary);
    }

    .categories-list {
        list-style: none;
        padding: 0;
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
    }

    .category-link {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding: 0.75rem 1rem;
        text-decoration: none;
        color: var(--text-secondary);
        border-radius: 12px;
        font-size: 0.9rem;
        transition: all 0.3s ease;
        background: transparent;
    }

    .category-link:hover,
    .category-link.active {
        background: var(--bg-secondary);
        color: var(--text-primary);
        transform: translateX(5px);
    }

    .search-form-premium {
        display: flex;
        gap: 0.75rem;
    }

    .search-input-wrapper {
        position: relative;
        flex: 1;
    }

    .search-input-wrapper svg {
        position: absolute;
        left: 1.25rem;
        top: 50%;
        transform: translateY(-50%);
        color: var(--text-tertiary);
        pointer-events: none;
    }

    .search-input-wrapper .search-input {
        width: 100%;
        background: var(--bg-secondary);
        border: 1px solid var(--border-light);
        padding: 0.875rem 1rem 0.875rem 3.25rem;
        border-radius: 14px;
        font-size: 0.9rem;
        color: var(--text-primary);
        transition: all 0.3s ease;
    }

    .search-input-wrapper .search-input:focus {
        outline: none;
        border-color: var(--text-primary);
        background: var(--bg-primary);
        box-shadow: 0 0 0 4px rgba(0,0,0,0.03);
    }

    .search-submit {
        background: var(--text-primary);
        color: var(--bg-primary);
        border: none;
        padding: 0 1.5rem;
        border-radius: 14px;
        font-weight: 600;
        font-size: 0.9rem;
        cursor: pointer;
        transition: all 0.3s ease;
    }

    .search-submit:hover {
        opacity: 0.9;
        transform: translateY(-1px);
    }

    .popular-list {
        display: flex;
        flex-direction: column;
        gap: 1.25rem;
    }

    .popular-item {
        display: flex;
        gap: 1rem;
        text-decoration: none;
        color: var(--text-primary);
        group: hover;
    }

    .popular-thumb-wrapper {
        width: 80px;
        height: 60px;
        border-radius: 12px;
        overflow: hidden;
        flex-shrink: 0;
        box-shadow: var(--shadow-sm);
    }

    .popular-thumb {
        width: 100%;
        height: 100%;
        object-fit: cover;
        transition: transform 0.4s ease;
    }

    .popular-item:hover .popular-thumb {
        transform: scale(1.1);
    }

    .popular-number {
        font-size: 1.1rem;
        font-weight: 700;
        color: var(--text-tertiary);
        min-width: 1.25rem;
        text-align: right;
        opacity: 0.7;
        line-height: 1.2;
        padding-top: 0.15rem;
    }

    .popular-info {
        flex: 1;
        min-width: 0;
        display: flex;
        flex-direction: column;
    }

    .popular-info h4 {
        font-size: 0.9rem;
        margin: 0 0 0.25rem 0;
        line-height: 1.4;
        font-family: var(--font-serif);
        font-weight: 600;
        display: -webkit-box;
        -webkit-line-clamp: 2; /* Limit title to 2 lines maximum */
        -webkit-box-orient: vertical;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .popular-date {
        font-size: 0.75rem;
        color: var(--text-tertiary);
    }

    @media (max-width: 1200px) {
        .main-layout {
            grid-template-columns: 1fr;
            gap: 3rem;
        }
        .sidebar {
            display: none;
        }
    }

    @media (max-width: 768px) {
        .category-header {
            padding: 3rem 1.5rem;
            margin-bottom: 2.5rem;
        }
        .posts-masonry {
            column-count: 2;
            column-gap: 1rem;
        }
        .post-card {
            margin-bottom: 1.5rem;
            border-radius: 16px;
        }
        .post-info {
            padding: 1.25rem;
        }
        .post-title {
            font-size: 1.1rem;
        }
    }

    /* No-image placeholder styling */
    .no-image-placeholder {
        width: 100%;
        aspect-ratio: 16 / 9;
        max-height: 220px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        padding: 1.5rem;
        box-sizing: border-box;
        text-align: center;
        position: relative;
        overflow: hidden;
        user-select: none;
        border-radius: inherit;
    }

    .no-image-placeholder-title {
        font-family: var(--font-sans), sans-serif;
        font-weight: 700;
        color: #1f2937;
        font-size: 1rem;
        line-height: 1.4;
        padding: 0 1rem;
        margin: 0;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
        text-overflow: ellipsis;
        z-index: 2;
    }

    .placeholder-icon {
        position: absolute;
        top: 1.25rem;
        right: 1.25rem;
        color: rgba(17, 24, 39, 0.12);
        z-index: 1;
    }

    .popular-placeholder {
        width: 100%;
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
        position: relative;
        background: #f3f4f6;
    }

    .placeholder-small-icon {
        color: rgba(17, 24, 39, 0.15);
    }
</style>
