<script lang="ts">
  import { t, formatDate as fmtDate, formatMoney } from "$lib/i18n";
  import { applyAction, enhance } from "$app/forms";
    import { invalidateAll } from "$app/navigation";
    import { page } from "$app/stores";
    import { onMount } from "svelte";

  const lang = $derived($page.data.language || 'pt');

let { data, form }: { data: any; form: any } = $props();

    let loading = $state(false);
    let activeTab = $state('general');
    let feedLoadingModeValue = $state('pagination');
    let enableRecommendationsValue = $state('1');
    let defaultThemeValue = $state('light');
    let siteLanguageValue = $state('pt');
    let siteLogoFileName = $state<string | null>(null);
    let siteFaviconFileName = $state<string | null>(null);
    let seoImageFileName = $state<string | null>(null);

    const predefinedModels = [
        'gemini-2.5-flash',
        'gemini-2.5-pro',
        'gemini-2.0-flash',
        'gemini-2.0-pro-exp-02-05',
        'gemini-1.5-flash',
        'gemini-1.5-pro'
    ];
    let selectedModel = $state('gemini-2.5-flash');
    let customModel = $state('');

    let origin = $state('');
    onMount(() => {
        origin = window.location.origin;
    });

    let webhookUrl = $derived(
        data.settings?.site_url 
            ? `${data.settings.site_url.replace(/\/$/, '')}/api/webhook/asaas` 
            : (origin ? `${origin}/api/webhook/asaas` : 'https://seusite.com/api/webhook/asaas')
    );

    let stripeWebhookUrl = $derived(
        data.settings?.site_url
            ? `${data.settings.site_url.replace(/\/$/, '')}/api/webhook/stripe`
            : (origin ? `${origin}/api/webhook/stripe` : 'https://seusite.com/api/webhook/stripe')
    );

    // Default always asaas for production safety
    let paymentGatewayValue = $state(data.settings?.payment_gateway === 'stripe' ? 'stripe' : 'asaas');

    const activeWebhookUrl = $derived(
        paymentGatewayValue === 'stripe' ? stripeWebhookUrl : webhookUrl
    );

    $effect(() => {
        const feedMode = data.settings?.feed_loading_mode;
        const theme = data.settings?.default_theme;
        const dbModel = data.settings?.gemini_api_model || data.envApiModel || 'gemini-2.5-flash';
        const recs = data.settings?.enable_recommendations;
        const siteLang = data.settings?.site_language;
        // Keep gateway select in sync after save / invalidateAll
        paymentGatewayValue = data.settings?.payment_gateway === 'stripe' ? 'stripe' : 'asaas';

        feedLoadingModeValue = feedMode === 'infinite' ? 'infinite' : 'pagination';
        enableRecommendationsValue = recs === '0' ? '0' : '1';
        defaultThemeValue = theme === 'dark' ? 'dark' : 'light';
        siteLanguageValue = siteLang === 'en' || siteLang === 'es' ? siteLang : 'pt';

        if (predefinedModels.includes(dbModel)) {
            selectedModel = dbModel;
        } else {
            selectedModel = 'custom';
            customModel = dbModel;
        }
    });

    $effect(() => {
        const tab = $page.url.searchParams.get('tab');
        if (tab && ['general', 'seo', 'api', 'security'].includes(tab)) {
            activeTab = tab;
        }
    });

    function handleSiteLogoFileChange(e: Event) {
        const input = e.target as HTMLInputElement;
        const file = input.files?.[0];
        siteLogoFileName = file ? file.name : null;
    }

    function handleSiteFaviconFileChange(e: Event) {
        const input = e.target as HTMLInputElement;
        const file = input.files?.[0];
        siteFaviconFileName = file ? file.name : null;
    }

    function handleSeoImageFileChange(e: Event) {
        const input = e.target as HTMLInputElement;
        const file = input.files?.[0];
        seoImageFileName = file ? file.name : null;
    }

    function maskApiKey(value: string) {
        if (!value) return '';
        if (value.length <= 8) return '*'.repeat(value.length);
        return value.substring(0, 4) + '*'.repeat(Math.min(value.length - 8, 20)) + value.substring(value.length - 4);
    }
</script>

<svelte:head>
    <title>{t(lang, "admin.settings.title")}</title>
</svelte:head>

<div class="settings-page">
    <div class="page-header">
        <h1>{t(lang, "admin.settings.heading")}</h1>
        <p class="subtitle">{t(lang, "admin.settings.subtitle")}</p>
    </div>

    <div class="settings-tabs">
        <button class="tab-btn" class:active={activeTab === 'general'} onclick={() => activeTab = 'general'}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/>
            </svg>
            {t(lang, "admin.settings.tab_general")}
        </button>
        <button class="tab-btn" class:active={activeTab === 'seo'} onclick={() => activeTab = 'seo'}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/>
            </svg>
            {t(lang, "admin.settings.tab_seo")}
        </button>
        <button class="tab-btn" class:active={activeTab === 'api'} onclick={() => activeTab = 'api'}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/>
            </svg>
            {t(lang, "admin.settings.tab_api")}
        </button>
        <button class="tab-btn" class:active={activeTab === 'security'} onclick={() => activeTab = 'security'}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>
            </svg>
            {t(lang, "admin.settings.tab_security")}
        </button>
    </div>

    {#if form?.success || $page.url.searchParams.get('success') === 'true'}
        {@const section = form?.section || $page.url.searchParams.get('tab') || 'general'}
        <div class="alert success">
            {section === 'api' ? t(lang, 'admin.settings.saved_api') : section === 'seo' ? t(lang, 'admin.settings.saved_seo') : section === 'security' ? t(lang, 'admin.settings.saved_security') : t(lang, 'admin.settings.saved_general')}
        </div>
    {/if}
    {#if form?.message}
        <div class="alert error">{form.message}</div>
    {/if}

    {#if activeTab === 'general'}
        <form method="POST" action="?/general" enctype="multipart/form-data" use:enhance={() => {
            loading = true;
            return async ({ result }) => {
                loading = false;
                await applyAction(result);
                await invalidateAll();
            };
        }}>
            <div class="form-card">
                <div class="form-section-title">{t(lang, "admin.settings.section_site")}</div>

                <div class="form-group">
                    <label for="site_title">{t(lang, "admin.settings.blog_title")}</label>
                    <input type="text" id="site_title" name="site_title" value={data.settings.site_title || ""} placeholder="Meu Blog Incrível" />
                    <small>{t(lang, "admin.settings.blog_title_hint")}</small>
                </div>

                <div class="form-group">
                    <label for="site_description">{t(lang, "admin.settings.meta_desc")}</label>
                    <textarea id="site_description" name="site_description" rows="3" placeholder="Um blog sobre tecnologia e design...">{data.settings.site_description || ""}</textarea>
                </div>

                <div class="form-group">
                    <label for="site_keywords">{t(lang, "admin.settings.keywords_label")}</label>
                    <input type="text" id="site_keywords" name="site_keywords" value={data.settings.site_keywords || ""} placeholder="blog, tecnologia, svelte, design" />
                </div>

                <div class="form-group">
                    <label for="site_logo">{t(lang, "admin.settings.site_logo")}</label>
                    <div class="image-input-group">
                        <input type="text" id="site_logo" name="site_logo" value={data.settings.site_logo || ""} placeholder="https://exemplo.com/logo.png" />
                        <div class="file-upload">
                            <span>{t(lang, "admin.settings.or_upload")}</span>
                            <input type="file" id="site_logo_file" name="site_logo_file" class="file-input-hidden" accept="image/*" onchange={handleSiteLogoFileChange} />
                            <label for="site_logo_file" class="btn btn-small">{t(lang, "admin.settings.choose_file")}</label>
                            {#if siteLogoFileName}
                                <span class="file-name" title={siteLogoFileName}>{siteLogoFileName}</span>
                            {/if}
                        </div>
                    </div>
                    {#if data.settings.site_logo}
                        <div class="current-image">
                            <img src={data.settings.site_logo} alt="Logo" />
                        </div>
                    {/if}
                    <small>{t(lang, "admin.settings.logo_hint")}</small>
                </div>

                <div class="form-group">
                    <label for="site_favicon">{t(lang, "admin.settings.site_favicon")}</label>
                    <div class="image-input-group">
                        <input type="text" id="site_favicon" name="site_favicon" value={data.settings.site_favicon || ""} placeholder="https://exemplo.com/favicon.png" />
                        <div class="file-upload">
                            <span>{t(lang, "admin.settings.or_upload")}</span>
                            <input type="file" id="site_favicon_file" name="site_favicon_file" class="file-input-hidden" accept="image/*" onchange={handleSiteFaviconFileChange} />
                            <label for="site_favicon_file" class="btn btn-small">{t(lang, "admin.settings.choose_file")}</label>
                            {#if siteFaviconFileName}
                                <span class="file-name" title={siteFaviconFileName}>{siteFaviconFileName}</span>
                            {/if}
                        </div>
                    </div>
                    {#if data.settings.site_favicon}
                        <div class="current-image">
                            <img src={data.settings.site_favicon} alt="Favicon" style="width: 32px; height: 32px; object-fit: contain;" />
                        </div>
                    {/if}
                    <small>{t(lang, "admin.settings.favicon_hint")}</small>
                </div>
            </div>

            <div class="form-card">
                <div class="form-section-title">{t(lang, "admin.settings.section_feed")}</div>

                <div class="form-group">
                    <label for="feed_loading_mode">{t(lang, "admin.settings.feed_mode")}</label>
                    <select id="feed_loading_mode" name="feed_loading_mode" bind:value={feedLoadingModeValue}>
                        <option value="pagination">{t(lang, "admin.settings.feed_pagination")}</option>
                        <option value="infinite">{t(lang, "admin.settings.feed_infinite")}</option>
                    </select>
                    <small>{t(lang, "admin.settings.feed_hint")}</small>
                </div>
            </div>

            <div class="form-card">
                <div class="form-section-title">{t(lang, "admin.settings.section_recs")}</div>

                <div class="form-group">
                    <label for="enable_recommendations">{t(lang, "admin.settings.recs_label")}</label>
                    <select id="enable_recommendations" name="enable_recommendations" bind:value={enableRecommendationsValue}>
                        <option value="1">{t(lang, "admin.settings.recs_on")}</option>
                        <option value="0">{t(lang, "admin.settings.recs_off")}</option>
                    </select>
                    <small>{t(lang, "admin.settings.recs_hint")}</small>
                </div>
            </div>

            <div class="form-card">
                <div class="form-section-title">{t(lang, "admin.settings.section_theme")}</div>

                <div class="form-group">
                    <label for="default_theme">{t(lang, "admin.settings.theme_label")}</label>
                    <select id="default_theme" name="default_theme" bind:value={defaultThemeValue}>
                        <option value="light">{t(lang, "admin.settings.theme_light")}</option>
                        <option value="dark">{t(lang, "admin.settings.theme_dark")}</option>
                    </select>
                    <small>{t(lang, "admin.settings.theme_hint")}</small>
                </div>
            </div>

            <div class="form-card">
                <div class="form-section-title">{t(lang, "admin.settings.section_lang")}</div>

                <div class="form-group">
                    <label for="site_language">{t(lang, "admin.settings.site_language")}</label>
                    <select id="site_language" name="site_language" bind:value={siteLanguageValue}>
                        <option value="pt">Português (Brasil)</option>
                        <option value="en">English (Estados Unidos)</option>
                        <option value="es">Español (Espanha/América Latina)</option>
                    </select>
                    <small>{t(lang, "admin.settings.lang_hint")}</small>
                </div>
            </div>

            <div class="form-card">
                <div class="form-section-title">{t(lang, "admin.settings.section_og")}</div>

                <div class="form-group">
                    <label for="seo_image">{t(lang, "admin.settings.og_image")}</label>
                    <div class="image-input-group">
                        <input type="text" id="seo_image" name="seo_image" value={data.settings.seo_image || ""} placeholder="https://exemplo.com/og-image.jpg" />
                        <div class="file-upload">
                            <span>{t(lang, "admin.settings.or_upload")}</span>
                            <input type="file" id="seo_image_file" name="seo_image_file" class="file-input-hidden" accept="image/*" onchange={handleSeoImageFileChange} />
                            <label for="seo_image_file" class="btn btn-small">{t(lang, "admin.settings.choose_file")}</label>
                            {#if seoImageFileName}
                                <span class="file-name" title={seoImageFileName}>{seoImageFileName}</span>
                            {/if}
                        </div>
                    </div>
                    {#if data.settings.seo_image}
                        <div class="current-image">
                            <img src={data.settings.seo_image} alt="Preview" />
                        </div>
                    {/if}
                </div>

                <div class="form-row">
                    <div class="form-group">
                        <label for="twitter_handle">Twitter Handle</label>
                        <input type="text" id="twitter_handle" name="twitter_handle" value={data.settings.twitter_handle || ""} placeholder="@meublog" />
                    </div>
                    <div class="form-group">
                        <label for="og_app_id">Facebook App ID</label>
                        <input type="text" id="og_app_id" name="og_app_id" value={data.settings.og_app_id || ""} placeholder="123456789" />
                    </div>
                </div>
            </div>

            <div class="form-card">
                <div class="form-section-title">{t(lang, "admin.settings.section_contact")}</div>

                <div class="form-group">
                    <label for="admin_email">{t(lang, "admin.settings.admin_email")}</label>
                    <input type="email" id="admin_email" name="admin_email" value={data.settings.admin_email || ""} placeholder="admin@seusite.com" />
                    <small>{t(lang, "admin.settings.admin_email_hint")}</small>
                </div>

                <div class="form-group">
                    <label for="footer_text">{t(lang, "admin.settings.footer_text")}</label>
                    <textarea id="footer_text" name="footer_text" rows="2" placeholder="© 2026 Blog. Minimalist Paper Theme.">{data.settings.footer_text || ""}</textarea>
                </div>
            </div>

            <div class="form-card">
                <div class="form-section-title">{t(lang, "admin.settings.section_scripts")}</div>
                <p class="section-description">{t(lang, "admin.settings.scripts_desc")}</p>

                <div class="form-group">
                    <label for="custom_head_script">Script do <code>&lt;head&gt;</code></label>
                    <textarea
                        id="custom_head_script"
                        name="custom_head_script"
                        rows="5"
                        placeholder="<!-- Cole aqui scripts para o <head>: Google Analytics, Meta Pixel, Tag Manager, etc. -->"
                        class="code-textarea"
                    >{data.settings.custom_head_script || ""}</textarea>
                    <small>{t(lang, "admin.settings.head_script_hint")}</small>
                </div>

                <div class="form-group">
                    <label for="custom_body_script">Script antes do <code>&lt;/body&gt;</code></label>
                    <textarea
                        id="custom_body_script"
                        name="custom_body_script"
                        rows="5"
                        placeholder="<!-- Cole aqui scripts para o final do <body>: Autotag de redes de anúncio, chat widgets, etc. -->"
                        class="code-textarea"
                    >{data.settings.custom_body_script || ""}</textarea>
                    <small>{t(lang, "admin.settings.body_script_hint")}</small>
                </div>
            </div>

            <div class="form-card">
                <div class="form-section-title">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right: 0.25rem;">
                        <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/>
                    </svg>
                    {t(lang, "admin.settings.section_whatsapp")}
                </div>

                <div class="form-group checkbox-group" style="margin-top: 1.25rem;">
                    <label class="checkbox-label" style="display: flex; align-items: center; gap: 0.5rem; cursor: pointer; text-transform: none; font-weight: normal; letter-spacing: normal; color: var(--text-primary);">
                        <input type="checkbox" id="whatsapp_enable" name="whatsapp_enable" value="1" checked={data.settings.whatsapp_enable === '1'} style="width: auto; margin: 0; cursor: pointer;" />
                        <span>{t(lang, "admin.settings.wa_enable")}</span>
                    </label>
                    <small>{t(lang, "admin.settings.wa_enable_hint")}</small>
                </div>

                <div class="form-group">
                    <label for="whatsapp_number">{t(lang, "admin.settings.wa_number")}</label>
                    <input type="text" id="whatsapp_number" name="whatsapp_number" value={data.settings.whatsapp_number || ""} placeholder="Ex: 5511999999999" />
                    <small>{t(lang, "admin.settings.wa_number_hint")}</small>
                </div>

                <div class="form-group">
                    <label for="whatsapp_message">{t(lang, "admin.settings.wa_message")}</label>
                    <input type="text" id="whatsapp_message" name="whatsapp_message" value={data.settings.whatsapp_message || ""} placeholder="Olá, gostaria de saber mais informações!" />
                    <small>{t(lang, "admin.settings.wa_message_hint")}</small>
                </div>
            </div>

            <div class="form-actions">
                <button type="submit" class="btn btn-primary" disabled={loading}>
                    {loading ? t(lang, "admin.ui.saving") : t(lang, "admin.settings.save")}
                </button>
            </div>
        </form>
    {:else if activeTab === 'seo'}
        <form method="POST" action="?/seo" use:enhance={() => {
            loading = true;
            return async ({ result }) => {
                loading = false;
                await applyAction(result);
            };
        }}>
            <div class="form-card">
                <div class="form-section-title">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/>
                    </svg>
                    RSS Feed
                </div>

                <div class="form-group">
                    <label for="rss_feed_title">{t(lang, "admin.settings.rss_title")}</label>
                    <input type="text" id="rss_feed_title" name="rss_feed_title" value={data.settings.rss_feed_title || ""} placeholder="Nome do seu blog" />
                    <small>{t(lang, "admin.settings.rss_title_hint")}</small>
                </div>

                <div class="form-group">
                    <label for="rss_feed_description">{t(lang, "admin.settings.rss_desc")}</label>
                    <textarea id="rss_feed_description" name="rss_feed_description" rows="2" placeholder="Descrição do seu feed RSS...">{data.settings.rss_feed_description || ""}</textarea>
                    <small>{t(lang, "admin.settings.rss_desc_hint")}</small>
                </div>
            </div>

            <div class="form-card">
                <div class="form-section-title">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/>
                    </svg>
                    Sitemap XML
                </div>

                <div class="form-group">
                    <label for="sitemap_priority_home">{t(lang, "admin.settings.priority_home_label")}</label>
                    <input type="number" id="sitemap_priority_home" name="sitemap_priority_home" value={data.settings.sitemap_priority_home || "1.0"} step="0.1" min="0" max="1" />
                    <small>{t(lang, "admin.settings.priority_home_hint")}</small>
                </div>

                <div class="form-group">
                    <label for="sitemap_priority_posts">{t(lang, "admin.settings.priority_posts_label")}</label>
                    <input type="number" id="sitemap_priority_posts" name="sitemap_priority_posts" value={data.settings.sitemap_priority_posts || "0.9"} step="0.1" min="0" max="1" />
                    <small>{t(lang, "admin.settings.priority_posts_hint")}</small>
                </div>

                <div class="form-group">
                    <label for="sitemap_priority_categories">{t(lang, "admin.settings.priority_cats_label")}</label>
                    <input type="number" id="sitemap_priority_categories" name="sitemap_priority_categories" value={data.settings.sitemap_priority_categories || "0.6"} step="0.1" min="0" max="1" />
                    <small>{t(lang, "admin.settings.priority_cats_hint")}</small>
                </div>

                <div class="form-row">
                    <div class="form-group">
                        <label for="sitemap_changefreq_home">{t(lang, "admin.settings.freq_home")}</label>
                        <select id="sitemap_changefreq_home" name="sitemap_changefreq_home">
                            <option value="always" selected>Always</option>
                            <option value="hourly">Hourly</option>
                            <option value="daily" selected>Daily</option>
                            <option value="weekly">Weekly</option>
                            <option value="monthly">Monthly</option>
                            <option value="yearly">Yearly</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="sitemap_changefreq_posts">{t(lang, "admin.settings.freq_posts")}</label>
                        <select id="sitemap_changefreq_posts" name="sitemap_changefreq_posts">
                            <option value="always">Always</option>
                            <option value="hourly">Hourly</option>
                            <option value="daily">Daily</option>
                            <option value="weekly" selected>Weekly</option>
                            <option value="monthly">Monthly</option>
                            <option value="yearly">Yearly</option>
                        </select>
                    </div>
                </div>
            </div>

            <div class="form-card">
                <div class="form-section-title">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                    </svg>
                    {t(lang, "admin.settings.news_section")}
                </div>

                <div class="form-group">
                    <label for="google_news_keywords">{t(lang, "admin.settings.news_keywords")}</label>
                    <input type="text" id="google_news_keywords" name="google_news_keywords" value={data.settings.google_news_keywords || ""} placeholder="noticia, brasil, tecnologia, mercado" />
                    <small>{t(lang, "admin.settings.news_keywords_hint")}</small>
                </div>

                <div class="form-group">
                    <label for="google_news_image_min_width">{t(lang, "admin.settings.news_img_width")}</label>
                    <input type="number" id="google_news_image_min_width" name="google_news_image_min_width" value={data.settings.google_news_image_min_width || "1600"} min="0" max="4000" />
                    <small>{t(lang, "admin.settings.news_img_hint")}</small>
                </div>
            </div>

            <div class="form-card">
                <div class="form-section-title">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="2" y="3" width="20" height="14" rx="2" ry="2"/>
                        <line x1="8" y1="21" x2="16" y2="21"/>
                        <line x1="12" y1="17" x2="12" y2="21"/>
                    </svg>
                    {t(lang, "admin.settings.ads_txt_section")}
                </div>

                <div class="form-group">
                    <label for="ads_txt">{t(lang, "admin.settings.ads_txt_label")}</label>
                    <textarea id="ads_txt" name="ads_txt" rows="5" placeholder="google.com, pub-xxxxxxxxxxxxxxxx, DIRECT, f08c47fec0942fa0" style="font-family: var(--font-mono); font-size: 0.85rem;">{data.settings.ads_txt || ""}</textarea>
                    <small>{t(lang, "admin.settings.ads_txt_hint")}</small>
                </div>
            </div>

            <div class="form-actions">
                <button type="submit" class="btn btn-primary" disabled={loading}>
                    {loading ? t(lang, "admin.ui.saving") : t(lang, "admin.settings.save_seo")}
                </button>
            </div>
        </form>
    {:else if activeTab === 'api'}
        <form method="POST" action="?/api" use:enhance={() => {
            loading = true;
            return async ({ result }) => {
                loading = false;
                await applyAction(result);
                await invalidateAll();
            };
        }}>
            <div class="form-card">
                <div class="form-section-title">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="2" y="5" width="20" height="14" rx="2" ry="2"/><line x1="2" y1="10" x2="22" y2="10"/>
                    </svg>
                    {t(lang, "admin.settings.payment_gateway_section")}
                </div>
                <div class="form-group">
                    <label for="payment_gateway">{t(lang, "admin.settings.payment_gateway")}</label>
                    <select id="payment_gateway" name="payment_gateway" bind:value={paymentGatewayValue}>
                        <option value="asaas">{t(lang, "admin.settings.gateway_asaas_default")}</option>
                        <option value="stripe">{t(lang, "admin.settings.gateway_stripe")}</option>
                    </select>
                    <small>{t(lang, "admin.settings.payment_gateway_hint")}</small>
                </div>

                <!-- Webhook do gateway ativo — atualiza ao trocar o select -->
                <div class="gateway-webhook-banner" class:stripe-active={paymentGatewayValue === 'stripe'}>
                    <div class="gateway-webhook-banner-head">
                        <span class="gateway-active-pill">
                            {paymentGatewayValue === 'stripe'
                                ? t(lang, 'admin.settings.gateway_active_stripe')
                                : t(lang, 'admin.settings.gateway_active_asaas')}
                        </span>
                        <strong>
                            {paymentGatewayValue === 'stripe'
                                ? t(lang, 'admin.settings.stripe_webhook_url_label')
                                : t(lang, 'admin.settings.webhook_url_label')}
                        </strong>
                    </div>
                    <div class="gateway-webhook-row">
                        <input
                            type="text"
                            readonly
                            value={activeWebhookUrl}
                            class="gateway-webhook-input"
                        />
                        <button
                            type="button"
                            class="btn btn-secondary gateway-webhook-copy"
                            onclick={() => {
                                navigator.clipboard.writeText(activeWebhookUrl);
                                alert(t(lang, 'admin.settings.webhook_copied'));
                            }}
                        >
                            {t(lang, 'admin.ui.copy')}
                        </button>
                    </div>
                    <small class="gateway-webhook-hint">
                        {paymentGatewayValue === 'stripe'
                            ? t(lang, 'admin.settings.stripe_webhook_paste_hint')
                            : t(lang, 'admin.settings.webhook_paste_hint')}
                    </small>
                    {#if paymentGatewayValue === 'stripe'}
                        <div class="gateway-events-box">
                            <span class="gateway-events-label">{t(lang, 'admin.settings.stripe_events_label')}</span>
                            <code class="gateway-events-code">{t(lang, 'admin.settings.stripe_events_list')}</code>
                        </div>
                    {/if}
                </div>

                <!-- Instruções passo a passo do gateway ativo -->
                <div class="gateway-instructions" class:stripe={paymentGatewayValue === 'stripe'}>
                    <div class="gateway-instructions-title">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/>
                        </svg>
                        {t(lang, 'admin.settings.setup_instructions_title')}
                    </div>
                    {#if paymentGatewayValue === 'stripe'}
                        <h4 class="gateway-instructions-subtitle">{t(lang, 'admin.settings.stripe_setup_title')}</h4>
                        <ul class="gateway-steps">
                            <li>{t(lang, 'admin.settings.stripe_setup_s1')}</li>
                            <li>{t(lang, 'admin.settings.stripe_setup_s2')}</li>
                            <li>{t(lang, 'admin.settings.stripe_setup_s3')}</li>
                            <li>{t(lang, 'admin.settings.stripe_setup_s4')}</li>
                            <li>{t(lang, 'admin.settings.stripe_setup_s5')}</li>
                            <li>{t(lang, 'admin.settings.stripe_setup_s6')}</li>
                            <li>{t(lang, 'admin.settings.stripe_setup_s7')}</li>
                        </ul>
                        <p class="gateway-instructions-note">{t(lang, 'admin.settings.stripe_setup_note')}</p>
                    {:else}
                        <h4 class="gateway-instructions-subtitle">{t(lang, 'admin.settings.asaas_setup_title')}</h4>
                        <ul class="gateway-steps">
                            <li>{t(lang, 'admin.settings.asaas_setup_s1')}</li>
                            <li>{t(lang, 'admin.settings.asaas_setup_s2')}</li>
                            <li>{t(lang, 'admin.settings.asaas_setup_s3')}</li>
                            <li>{t(lang, 'admin.settings.asaas_setup_s4')}</li>
                            <li>{t(lang, 'admin.settings.asaas_setup_s5')}</li>
                            <li>{t(lang, 'admin.settings.asaas_setup_s6')}</li>
                        </ul>
                        <p class="gateway-instructions-note">{t(lang, 'admin.settings.asaas_setup_note')}</p>
                    {/if}
                </div>
            </div>

            <div class="form-card" class:gateway-section-inactive={paymentGatewayValue === 'stripe'}>
                <div class="form-section-title">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="2" y="5" width="20" height="14" rx="2" ry="2"/><line x1="2" y1="10" x2="22" y2="10"/>
                    </svg>
                    {t(lang, "admin.settings.asaas_section")}
                    {#if paymentGatewayValue === 'asaas'}
                        <span class="gateway-section-badge">{t(lang, 'admin.settings.gateway_in_use')}</span>
                    {/if}
                </div>
                <div class="status-badge" class:configured={data.settings.asaas_api_key}>
                    <span class="status-dot"></span>
                    {data.settings.asaas_api_key ? t(lang, 'admin.settings.configured') : t(lang, 'admin.settings.not_configured')}
                </div>

                <div class="form-group">
                    <label for="asaas_api_key">{t(lang, "admin.settings.asaas_key_label")}</label>
                    <input type="password" id="asaas_api_key" name="asaas_api_key" value={data.settings.asaas_api_key || ""} placeholder="$sandbox_..." />
                    <small>{t(lang, "admin.settings.asaas_key_hint")}</small>
                </div>

                <div class="form-group">
                    <label for="asaas_api_url">{t(lang, "admin.settings.asaas_env")}</label>
                    <select id="asaas_api_url" name="asaas_api_url">
                        <option value="https://api-sandbox.asaas.com/v3" selected={data.settings.asaas_api_url === 'https://api-sandbox.asaas.com/v3' || data.settings.asaas_api_url === 'https://sandbox.asaas.com/api/v3' || data.settings.asaas_api_url === 'https://sandbox.asaas.com/v3' || !data.settings.asaas_api_url}>{t(lang, "admin.settings.asaas_sandbox")} - https://api-sandbox.asaas.com/v3</option>
                        <option value="https://api.asaas.com/v3" selected={data.settings.asaas_api_url === 'https://api.asaas.com/v3' || data.settings.asaas_api_url === 'https://api.asaas.com/api/v3'}>{t(lang, "admin.settings.asaas_prod")} - https://api.asaas.com/v3</option>
                    </select>
                </div>

                <div class="form-group">
                    <label for="asaas_webhook_secret">{t(lang, "admin.settings.webhook_token")}</label>
                    <input type="password" id="asaas_webhook_secret" name="asaas_webhook_secret" value={data.settings.asaas_webhook_secret || ""} placeholder="MeuTokenSecreto123" />
                    <small>{t(lang, "admin.settings.webhook_hint2")}</small>
                </div>

                <div class="form-group" style="margin-top: 1.25rem; padding: 1.25rem; background: var(--bg-secondary); border: 1px dashed var(--border-color); border-radius: var(--radius-md);">
                    <label style="font-weight: 700; color: var(--text-primary); text-transform: none; letter-spacing: 0; display: block; margin-bottom: 0.5rem;">{t(lang, "admin.settings.webhook_url_label")}</label>
                    <div style="display: flex; gap: 0.5rem; align-items: center;">
                        <input type="text" readonly value={webhookUrl} style="background: var(--bg-primary); cursor: text; font-family: var(--font-mono); font-size: 0.85rem; padding: 0.5rem 0.75rem; border: 1px solid var(--border-color); border-radius: var(--radius-sm); flex: 1;" />
                        <button type="button" class="btn btn-secondary" onclick={() => {
                            navigator.clipboard.writeText(webhookUrl);
                            alert(t(lang, 'admin.settings.webhook_copied'));
                        }} style="padding: 0 1.25rem; font-size: 0.825rem; height: 38px; border-radius: var(--radius-sm); border: 1px solid var(--border-color); background: var(--bg-primary); color: var(--text-primary); cursor: pointer; transition: all 0.2s;">{t(lang, "admin.ui.copy")}</button>
                    </div>
                    <small style="margin-top: 0.5rem; display: block; color: var(--text-secondary);">{t(lang, "admin.settings.webhook_paste_hint")}</small>
                </div>
            </div>

            <div class="form-card" class:gateway-section-inactive={paymentGatewayValue !== 'stripe'} class:gateway-section-active={paymentGatewayValue === 'stripe'}>
                <div class="form-section-title">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="1" y="4" width="22" height="16" rx="2" ry="2"/><line x1="1" y1="10" x2="23" y2="10"/>
                    </svg>
                    {t(lang, "admin.settings.stripe_section")}
                    {#if paymentGatewayValue === 'stripe'}
                        <span class="gateway-section-badge stripe">{t(lang, 'admin.settings.gateway_in_use')}</span>
                    {/if}
                </div>
                <div class="status-badge" class:configured={data.settings.stripe_secret_key}>
                    <span class="status-dot"></span>
                    {data.settings.stripe_secret_key ? t(lang, 'admin.settings.configured') : t(lang, 'admin.settings.not_configured')}
                </div>
                <p style="font-size: 0.85rem; color: var(--text-secondary); margin: 0 0 1rem;">{t(lang, "admin.settings.stripe_optional_hint")}</p>

                <div class="form-group">
                    <label for="stripe_secret_key">{t(lang, "admin.settings.stripe_secret")}</label>
                    <input type="password" id="stripe_secret_key" name="stripe_secret_key" value={data.settings.stripe_secret_key || ""} placeholder="sk_live_... or sk_test_..." />
                    <small>{t(lang, "admin.settings.stripe_secret_hint")}</small>
                </div>

                <div class="form-group">
                    <label for="stripe_publishable_key">{t(lang, "admin.settings.stripe_publishable")}</label>
                    <input type="text" id="stripe_publishable_key" name="stripe_publishable_key" value={data.settings.stripe_publishable_key || ""} placeholder="pk_live_... or pk_test_..." />
                </div>

                <div class="form-group">
                    <label for="stripe_currency">{t(lang, "admin.settings.stripe_currency")}</label>
                    <select id="stripe_currency" name="stripe_currency">
                        <option value="brl" selected={(data.settings.stripe_currency || 'brl') === 'brl'}>BRL (R$)</option>
                        <option value="usd" selected={data.settings.stripe_currency === 'usd'}>USD ($)</option>
                        <option value="eur" selected={data.settings.stripe_currency === 'eur'}>EUR (€)</option>
                        <option value="gbp" selected={data.settings.stripe_currency === 'gbp'}>GBP (£)</option>
                    </select>
                    <small>{t(lang, "admin.settings.stripe_currency_hint")}</small>
                </div>

                <div class="form-group">
                    <label for="stripe_webhook_secret">{t(lang, "admin.settings.stripe_webhook_secret")}</label>
                    <input type="password" id="stripe_webhook_secret" name="stripe_webhook_secret" value={data.settings.stripe_webhook_secret || ""} placeholder="whsec_..." />
                    <small>{t(lang, "admin.settings.stripe_webhook_hint")}</small>
                </div>

                <div class="form-group" style="margin-top: 1.25rem; padding: 1.25rem; background: var(--bg-secondary); border: 1px dashed var(--border-color); border-radius: var(--radius-md);">
                    <label style="font-weight: 700; color: var(--text-primary); text-transform: none; letter-spacing: 0; display: block; margin-bottom: 0.5rem;">{t(lang, "admin.settings.stripe_webhook_url_label")}</label>
                    <div style="display: flex; gap: 0.5rem; align-items: center;">
                        <input type="text" readonly value={stripeWebhookUrl} style="background: var(--bg-primary); cursor: text; font-family: var(--font-mono); font-size: 0.85rem; padding: 0.5rem 0.75rem; border: 1px solid var(--border-color); border-radius: var(--radius-sm); flex: 1;" />
                        <button type="button" class="btn btn-secondary" onclick={() => {
                            navigator.clipboard.writeText(stripeWebhookUrl);
                            alert(t(lang, 'admin.settings.webhook_copied'));
                        }} style="padding: 0 1.25rem; font-size: 0.825rem; height: 38px; border-radius: var(--radius-sm); border: 1px solid var(--border-color); background: var(--bg-primary); color: var(--text-primary); cursor: pointer;">{t(lang, "admin.ui.copy")}</button>
                    </div>
                    <small style="margin-top: 0.5rem; display: block; color: var(--text-secondary);">{t(lang, "admin.settings.stripe_webhook_paste_hint")}</small>
                </div>
            </div>

            <div class="form-card">
                <div class="form-section-title">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/>
                    </svg>
                    {t(lang, "admin.settings.resend_section")}
                </div>
                <div class="status-badge" class:configured={data.settings.resend_api_key}>
                    <span class="status-dot"></span>
                    {data.settings.resend_api_key ? t(lang, 'admin.settings.configured') : t(lang, 'admin.settings.not_configured')}
                </div>

                <div class="form-group">
                    <label for="resend_api_key">{t(lang, "admin.settings.resend_key")}</label>
                    <input type="password" id="resend_api_key" name="resend_api_key" value={data.settings.resend_api_key || ""} placeholder="re_xxxxxxxxxxxxxxxxxxxxxx" />
                    <small>{t(lang, "admin.settings.resend_key_hint")}</small>
                </div>

                <div class="form-group">
                    <label for="resend_from_email">{t(lang, "admin.settings.resend_from")}</label>
                    <input type="text" id="resend_from_email" name="resend_from_email" value={data.settings.resend_from_email || ""} placeholder="Acme &lt;onboarding@resend.dev&gt;" />
                    <small>Deve ser um e-mail do seu domínio verificado no Resend. Se estiver em testes sem domínio, use o remetente padrão <code>onboarding@resend.dev</code>.</small>
                </div>

                <div class="form-group checkbox-group" style="margin-top: 1.25rem;">
                    <label class="checkbox-label" style="display: flex; align-items: center; gap: 0.5rem; cursor: pointer; text-transform: none; font-weight: normal; letter-spacing: normal; color: var(--text-primary);">
                        <input type="checkbox" id="enable_otp_login" name="enable_otp_login" value="1" checked={data.settings.enable_otp_login === '1'} style="width: auto; margin: 0; cursor: pointer;" />
                        <span>{t(lang, "admin.settings.otp_enable")}</span>
                    </label>
                    <small style="display: block; margin-top: 0.25rem; margin-left: 1.5rem;">Se ativo, o fluxo de login de membros ignorará senhas e enviará um código numérico temporário de 6 dígitos.</small>
                </div>
            </div>

            <div class="form-card">
                <div class="form-section-title">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/>
                    </svg>
                    Google Gemini (YouTube Importer)
                </div>

                <div class="form-group">
                    <label for="gemini_api_key">{t(lang, "admin.settings.gemini_key")}</label>
                    <input 
                        type="password" 
                        id="gemini_api_key" 
                        name="gemini_api_key" 
                        value={data.settings.gemini_api_key || ""} 
                        placeholder={data.hasEnvApiKey ? "•••••••••••••••• (Usando fallback do .env)" : "AIzaSyxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"} 
                    />
                    <small style="display: flex; flex-direction: column; gap: 0.25rem;">
                        <span>Obtida em: Google AI Studio (https://aistudio.google.com/)</span>
                        {#if data.hasEnvApiKey && !data.settings.gemini_api_key}
                            <span style="color: #059669; font-weight: 500;">✓ Chave de API ativa via variável de ambiente (.env)</span>
                        {/if}
                    </small>
                </div>

                <div class="form-group">
                    <label for="gemini_api_model_select">{t(lang, "admin.settings.gemini_model")}</label>
                    <select 
                        id="gemini_api_model_select" 
                        bind:value={selectedModel}
                        onchange={() => { if (selectedModel !== 'custom') customModel = ''; }}
                    >
                        <option value="gemini-2.5-flash">Gemini 2.5 Flash (Recomendado)</option>
                        <option value="gemini-2.5-pro">Gemini 2.5 Pro</option>
                        <option value="gemini-2.0-flash">Gemini 2.0 Flash</option>
                        <option value="gemini-2.0-pro-exp-02-05">Gemini 2.0 Pro</option>
                        <option value="gemini-1.5-flash">Gemini 1.5 Flash</option>
                        <option value="gemini-1.5-pro">Gemini 1.5 Pro</option>
                        <option value="custom">{t(lang, "admin.settings.gemini_custom")}</option>
                    </select>
                </div>

                {#if selectedModel === 'custom'}
                    <div class="form-group" style="margin-top: 1rem;">
                        <label for="gemini_api_model_custom">{t(lang, "admin.settings.gemini_custom_id")}</label>
                        <input 
                            type="text" 
                            id="gemini_api_model_custom" 
                            name="gemini_api_model" 
                            bind:value={customModel} 
                            placeholder="Ex: gemini-3.0-flash" 
                            required 
                        />
                        <small>Insira o identificador exato do modelo da API Gemini (ex: <code>gemini-3.0-flash</code>).</small>
                    </div>
                {:else}
                    <input type="hidden" name="gemini_api_model" value={selectedModel} />
                {/if}
            </div>

            <div class="form-card">
                <div class="form-section-title">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
                    </svg>
                    Site
                </div>

                <div class="form-group">
                    <label for="site_url">{t(lang, "admin.settings.site_url")}</label>
                    <input type="url" id="site_url" name="site_url" value={data.settings.site_url || ""} placeholder="https://seusite.com" />
                    <small>{t(lang, "admin.settings.site_url_hint")}</small>
                </div>

                <div class="form-group">
                    <label for="sidebar_products_display_mode">{t(lang, "admin.settings.sidebar_products")}</label>
                    <select id="sidebar_products_display_mode" name="sidebar_products_display_mode" style="background: var(--bg-secondary); border: 1px solid var(--border-color); color: var(--text-primary); padding: 0.75rem; border-radius: var(--radius-md); width: 100%;">
                        <option value="carousel" selected={data.settings.sidebar_products_display_mode === 'carousel' || !data.settings.sidebar_products_display_mode}>{t(lang, "admin.settings.sidebar_carousel")}</option>
                        <option value="list" selected={data.settings.sidebar_products_display_mode === 'list'}>{t(lang, "admin.settings.sidebar_list")}</option>
                    </select>
                    <small>Escolha se os produtos digitais aparecem na barra lateral em carrossel deslizante ou em lista vertical.</small>
                </div>

                <div class="form-group checkbox-group" style="margin-top: 1.25rem;">
                    <label class="checkbox-label" style="display: flex; align-items: center; gap: 0.5rem; cursor: pointer; text-transform: none; font-weight: normal; letter-spacing: normal; color: var(--text-primary);">
                        <input type="checkbox" id="enable_member_login" name="enable_member_login" value="1" checked={data.settings.enable_member_login === '1'} style="width: auto; margin: 0; cursor: pointer;" />
                        <span>{t(lang, "admin.settings.members_enable")}</span>
                    </label>
                    <small style="display: block; margin-top: 0.25rem; margin-left: 1.5rem;">Se ativo, os leitores poderão se cadastrar e fazer login para acessar posts premium.</small>
                </div>
            </div>

            <div class="form-card">
                <div class="form-section-title">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>
                    </svg>
                    Microsoft Clarity (Analytics de Comportamento)
                </div>

                <div class="form-group">
                    <label for="microsoft_clarity_project_id">{t(lang, "admin.settings.clarity_id")}</label>
                    <input 
                        type="text" 
                        id="microsoft_clarity_project_id" 
                        name="microsoft_clarity_project_id" 
                        value={data.settings.microsoft_clarity_project_id || ""} 
                        placeholder="Ex: abcdefgh12" 
                    />
                    <small>Insira o ID do seu projeto do Microsoft Clarity para habilitar replays de sessão, mapas de calor e análise comportamental em tempo real.</small>
                </div>
            </div>

            <div class="form-actions">
                <button type="submit" class="btn btn-primary" disabled={loading}>
                    {loading ? "Salvando..." : "Salvar Configurações de API"}
                </button>
            </div>
        </form>
    {:else if activeTab === 'security'}
        <form method="POST" action="?/security" use:enhance={() => {
            loading = true;
            return async ({ result }) => {
                loading = false;
                await applyAction(result);
                await invalidateAll();
            };
        }}>
            <div class="form-card">
                <div class="form-section-title">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                    </svg>
                    Alterar Senha do Administrador
                </div>

                <div class="form-group">
                    <label for="current_password">{t(lang, "admin.settings.current_password")}</label>
                    <input type="password" id="current_password" name="current_password" required placeholder="Digite sua senha atual" />
                </div>

                <div class="form-group">
                    <label for="new_password">{t(lang, "admin.settings.new_password")}</label>
                    <input type="password" id="new_password" name="new_password" required placeholder="Mínimo de 8 caracteres, com letra maiúscula, minúscula, número e símbolo" />
                </div>

                <div class="form-group">
                    <label for="confirm_password">{t(lang, "admin.settings.confirm_password")}</label>
                    <input type="password" id="confirm_password" name="confirm_password" required placeholder="Confirme a nova senha" />
                </div>
            </div>

            <div class="form-actions">
                <button type="submit" class="btn btn-primary" disabled={loading}>
                    {loading ? "Salvando..." : "Alterar Senha"}
                </button>
            </div>
        </form>
    {/if}
</div>

<style>
    .settings-page { max-width: 900px; margin: 0 auto; }
    .page-header { margin-bottom: 2rem; }
    h1 { font-family: var(--font-sans); font-size: 1.5rem; font-weight: 700; margin-bottom: 0.5rem; }
    .subtitle { color: var(--text-muted); }

    .settings-tabs { display: flex; gap: 0.5rem; margin-bottom: 2rem; border-bottom: 1px solid var(--border-light); padding-bottom: 0.5rem; }
    .tab-btn {
        display: flex; align-items: center; gap: 0.5rem; padding: 0.75rem 1.25rem; background: transparent; border: none; border-radius: var(--radius-md); font-family: var(--font-sans); font-size: 0.9rem; font-weight: 500; color: var(--text-secondary); cursor: pointer; transition: all 0.2s;
    }
    .tab-btn:hover { background: var(--bg-secondary); color: var(--text-primary); }
    .tab-btn.active { background: var(--bg-primary); color: var(--text-primary); box-shadow: var(--shadow-sm); }

    .form-card { background: var(--bg-primary); padding: 2rem; border-radius: var(--radius-lg); border: 1px solid var(--border-color); margin-bottom: 1.5rem; }
    .form-card.gateway-section-active {
      border-color: #635bff;
      box-shadow: 0 0 0 1px rgba(99, 91, 255, 0.25);
    }
    .form-card.gateway-section-inactive {
      opacity: 0.72;
    }
    .gateway-section-badge {
      margin-left: auto;
      font-size: 0.7rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      padding: 0.25rem 0.6rem;
      border-radius: 999px;
      background: #ecfdf5;
      color: #059669;
    }
    .gateway-section-badge.stripe {
      background: #eef2ff;
      color: #4f46e5;
    }
    .gateway-webhook-banner {
      margin-top: 1.25rem;
      padding: 1.25rem;
      border-radius: var(--radius-md);
      border: 1px dashed var(--border-color);
      background: var(--bg-secondary);
    }
    .gateway-webhook-banner.stripe-active {
      border-color: #635bff;
      background: linear-gradient(135deg, rgba(99, 91, 255, 0.08) 0%, var(--bg-secondary) 100%);
    }
    .gateway-webhook-banner-head {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 0.5rem 0.75rem;
      margin-bottom: 0.75rem;
    }
    .gateway-webhook-banner-head strong {
      font-size: 0.95rem;
      color: var(--text-primary);
    }
    .gateway-active-pill {
      display: inline-flex;
      align-items: center;
      font-size: 0.72rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.03em;
      padding: 0.3rem 0.65rem;
      border-radius: 999px;
      background: #ecfdf5;
      color: #059669;
    }
    .gateway-webhook-banner.stripe-active .gateway-active-pill {
      background: #635bff;
      color: #fff;
    }
    .gateway-webhook-row {
      display: flex;
      gap: 0.5rem;
      align-items: center;
    }
    .gateway-webhook-input {
      background: var(--bg-primary);
      cursor: text;
      font-family: var(--font-mono);
      font-size: 0.85rem;
      padding: 0.5rem 0.75rem;
      border: 1px solid var(--border-color);
      border-radius: var(--radius-sm);
      flex: 1;
      min-width: 0;
      color: var(--text-primary);
    }
    .gateway-webhook-copy {
      padding: 0 1.25rem;
      font-size: 0.825rem;
      height: 38px;
      border-radius: var(--radius-sm);
      white-space: nowrap;
      flex-shrink: 0;
    }
    .gateway-webhook-hint {
      margin-top: 0.5rem;
      display: block;
      color: var(--text-secondary);
      line-height: 1.45;
    }
    .gateway-events-box {
      margin-top: 0.85rem;
      padding: 0.75rem 0.9rem;
      border-radius: var(--radius-sm);
      background: var(--bg-primary);
      border: 1px solid var(--border-color);
      display: flex;
      flex-direction: column;
      gap: 0.35rem;
    }
    .gateway-events-label {
      font-size: 0.72rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      color: var(--text-secondary);
    }
    .gateway-events-code {
      font-family: var(--font-mono);
      font-size: 0.78rem;
      color: var(--text-primary);
      word-break: break-word;
      line-height: 1.4;
    }
    .gateway-instructions {
      margin-top: 1.25rem;
      padding: 1.15rem 1.25rem;
      border-radius: var(--radius-md);
      border: 1px solid var(--border-color);
      background: var(--bg-primary);
    }
    .gateway-instructions.stripe {
      border-color: rgba(99, 91, 255, 0.35);
      background: linear-gradient(180deg, rgba(99, 91, 255, 0.06) 0%, var(--bg-primary) 48%);
    }
    .gateway-instructions-title {
      display: flex;
      align-items: center;
      gap: 0.45rem;
      font-size: 0.8rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      color: var(--text-secondary);
      margin-bottom: 0.65rem;
    }
    .gateway-instructions-subtitle {
      margin: 0 0 0.75rem;
      font-size: 0.98rem;
      font-weight: 700;
      color: var(--text-primary);
      line-height: 1.35;
    }
    .gateway-steps {
      margin: 0;
      padding: 0;
      list-style: none;
      display: flex;
      flex-direction: column;
      gap: 0.55rem;
      color: var(--text-primary);
      font-size: 0.88rem;
      line-height: 1.5;
    }
    .gateway-steps li {
      padding: 0.45rem 0.65rem;
      border-radius: var(--radius-sm);
      background: var(--bg-secondary);
      border: 1px solid var(--border-light, var(--border-color));
    }
    .gateway-instructions-note {
      margin: 0.9rem 0 0;
      padding: 0.7rem 0.85rem;
      border-radius: var(--radius-sm);
      background: #fffbeb;
      border: 1px solid #fde68a;
      color: #92400e;
      font-size: 0.84rem;
      line-height: 1.45;
    }
    :global([data-theme='dark']) .gateway-instructions-note,
    :global(.dark) .gateway-instructions-note {
      background: rgba(245, 158, 11, 0.12);
      border-color: rgba(245, 158, 11, 0.35);
      color: #fbbf24;
    }
    @media (max-width: 640px) {
      .gateway-webhook-row {
        flex-direction: column;
        align-items: stretch;
      }
      .gateway-webhook-copy {
        width: 100%;
      }
    }
    .form-section-title { display: flex; align-items: center; gap: 0.5rem; font-size: 0.8rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; color: var(--text-secondary); margin-bottom: 1.5rem; width: 100%; }

    .form-group { margin-bottom: 1.25rem; }
    .form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }

    label { display: block; margin-bottom: 0.5rem; font-weight: 500; color: var(--text-primary); font-size: 0.875rem; }
    input, textarea, select { width: 100%; padding: 0.75rem; background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: var(--radius-md); color: var(--text-primary); font-family: var(--font-sans); transition: border-color var(--transition-fast); }
    input:focus, textarea:focus, select:focus { outline: none; border-color: var(--text-primary); }
    input[type="password"] { font-family: monospace; letter-spacing: 1px; }

    small { display: block; margin-top: 0.5rem; color: var(--text-muted); font-size: 0.75rem; }

    .section-description { font-size: 0.8rem; color: var(--text-muted); margin-bottom: 1.25rem; margin-top: -0.75rem; line-height: 1.5; }

    .code-textarea { font-family: 'Courier New', Courier, monospace; font-size: 0.8rem; line-height: 1.6; background: var(--bg-secondary); resize: vertical; }

    .status-badge { display: inline-flex; align-items: center; gap: 0.5rem; padding: 0.35rem 0.75rem; border-radius: 20px; font-size: 0.75rem; font-weight: 600; background: var(--bg-secondary); color: var(--text-muted); margin-bottom: 1.5rem; }
    .status-dot { width: 8px; height: 8px; border-radius: 50%; background: currentColor; }
    .status-badge.configured { background: #ecfdf5; color: #059669; }

    .image-input-group { display: flex; flex-direction: column; gap: 0.75rem; }
    .file-upload { display: flex; align-items: center; gap: 0.75rem; padding: 1rem; background: var(--bg-secondary); border: 1px dashed var(--border-color); border-radius: var(--radius-md); flex-wrap: wrap; }
    .file-upload span { font-size: 0.875rem; color: var(--text-muted); white-space: nowrap; }
    .file-input-hidden { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0, 0, 0, 0); white-space: nowrap; border: 0; }
    .file-name { font-size: 0.75rem; color: var(--text-muted); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 280px; }
    .current-image { margin-top: 1rem; width: 100%; max-width: 300px; border-radius: var(--radius-md); overflow: hidden; border: 1px solid var(--border-color); }
    .current-image img { width: 100%; height: auto; display: block; }

    .form-actions { margin-top: 1.5rem; display: flex; justify-content: flex-end; }
    .alert { padding: 1rem; border-radius: var(--radius-md); margin-bottom: 1.5rem; font-size: 0.875rem; }
    .success { background: #ecfdf5; color: #059669; border: 1px solid #a7f3d0; }
    .error { background: #fef2f2; color: #dc2626; border: 1px solid #fecaca; }

    @media (max-width: 640px) {
        .form-row { grid-template-columns: 1fr; }
        .settings-tabs { flex-wrap: wrap; }
        .tab-btn { flex: 1; justify-content: center; }
    }
</style>
