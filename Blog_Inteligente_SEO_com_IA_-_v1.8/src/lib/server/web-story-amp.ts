/**
 * Server-side AMP Web Story HTML builder.
 * Markup is fully controlled here so we stay AMP-valid (no free HTML from editors).
 */
import type { WebStory, WebStorySlide } from './database';

function esc(value: string | null | undefined): string {
	if (!value) return '';
	return String(value)
		.replace(/&/g, '&amp;')
		.replace(/</g, '&lt;')
		.replace(/>/g, '&gt;')
		.replace(/"/g, '&quot;')
		.replace(/'/g, '&#39;');
}

function escAttr(value: string | null | undefined): string {
	return esc(value).replace(/\n/g, ' ');
}

function absoluteUrl(url: string | null | undefined, siteUrl: string): string {
	if (!url) return '';
	if (/^https?:\/\//i.test(url)) return url;
	const base = siteUrl.replace(/\/$/, '');
	return url.startsWith('/') ? `${base}${url}` : `${base}/${url}`;
}

function truncate(text: string, max: number): string {
	const t = text.trim();
	if (t.length <= max) return t;
	return t.slice(0, max - 1).trimEnd() + '…';
}

export function buildAmpWebStoryHtml(options: {
	story: WebStory;
	slides: WebStorySlide[];
	siteUrl: string;
	siteTitle: string;
	siteLogo: string;
	publisherName?: string;
}): string {
	const { story, slides, siteUrl, siteTitle } = options;
	const publisher = options.publisherName || siteTitle || 'Blog';
	const logo = absoluteUrl(options.siteLogo || '/favicon.svg', siteUrl) || absoluteUrl('/favicon.svg', siteUrl);
	const poster =
		absoluteUrl(story.poster_portrait || story.cover_image, siteUrl) || logo;
	const canonical = `${siteUrl.replace(/\/$/, '')}/stories/${story.slug}`;
	const storyTitle = truncate(story.title || 'Story', 70);

	const pages = slides.length
		? slides
		: [
				{
					id: 0,
					story_id: story.id,
					sort_order: 0,
					background_image: story.cover_image,
					title: story.title,
					body: null,
					cta_url: story.cta_url,
					cta_text: story.cta_text
				} as WebStorySlide
			];

	const pagesHtml = pages
		.map((slide, index) => {
			const bg = absoluteUrl(slide.background_image || story.cover_image || poster, siteUrl);
			const title = truncate(slide.title || (index === 0 ? story.title : '') || '', 60);
			const body = truncate(slide.body || '', 140);
			const ctaUrl = slide.cta_url || story.cta_url || '';
			const ctaText = truncate(slide.cta_text || story.cta_text || 'Saiba mais', 32);
			const pageId = `page-${index + 1}`;

			const bgLayer = bg
				? `<amp-story-grid-layer template="fill">
        <amp-img src="${escAttr(bg)}" width="720" height="1280" layout="responsive" alt=""></amp-img>
      </amp-story-grid-layer>`
				: `<amp-story-grid-layer template="fill">
        <div class="bg-fallback"></div>
      </amp-story-grid-layer>`;

			const ctaLayer =
				ctaUrl && /^https?:\/\//i.test(ctaUrl)
					? `<amp-story-page-outlink layout="nodisplay">
        <a href="${escAttr(ctaUrl)}">${esc(ctaText)}</a>
      </amp-story-page-outlink>`
					: ctaUrl
						? `<amp-story-page-outlink layout="nodisplay">
        <a href="${escAttr(absoluteUrl(ctaUrl, siteUrl))}">${esc(ctaText)}</a>
      </amp-story-page-outlink>`
						: '';

			return `
    <amp-story-page id="${pageId}">
      ${bgLayer}
      <amp-story-grid-layer template="vertical" class="bottom">
        <div class="content">
          ${title ? `<h1 class="slide-title">${esc(title)}</h1>` : ''}
          ${body ? `<p class="slide-body">${esc(body)}</p>` : ''}
        </div>
      </amp-story-grid-layer>
      ${ctaLayer}
    </amp-story-page>`;
		})
		.join('\n');

	const jsonLd = {
		'@context': 'https://schema.org',
		'@type': 'Article',
		headline: storyTitle,
		image: [poster],
		datePublished: story.created_at,
		dateModified: story.updated_at || story.created_at,
		author: { '@type': 'Organization', name: publisher },
		publisher: {
			'@type': 'Organization',
			name: publisher,
			logo: { '@type': 'ImageObject', url: logo }
		},
		mainEntityOfPage: canonical
	};

	return `<!doctype html>
<html ⚡ lang="pt-BR">
<head>
  <meta charset="utf-8">
  <script async src="https://cdn.ampproject.org/v0.js"></script>
  <script async custom-element="amp-story" src="https://cdn.ampproject.org/v0/amp-story-1.0.js"></script>
  <title>${esc(storyTitle)}</title>
  <link rel="canonical" href="${escAttr(canonical)}">
  <meta name="viewport" content="width=device-width,minimum-scale=1,initial-scale=1">
  <meta name="description" content="${escAttr(truncate(pages[0]?.body || story.title, 155))}">
  <script type="application/ld+json">${JSON.stringify(jsonLd).replace(/</g, '\\u003c')}</script>
  <style amp-boilerplate>body{-webkit-animation:-amp-start 8s steps(1,end) 0s 1 normal both;-moz-animation:-amp-start 8s steps(1,end) 0s 1 normal both;-ms-animation:-amp-start 8s steps(1,end) 0s 1 normal both;animation:-amp-start 8s steps(1,end) 0s 1 normal both}@-webkit-keyframes -amp-start{from{visibility:hidden}to{visibility:visible}}@-moz-keyframes -amp-start{from{visibility:hidden}to{visibility:visible}}@-ms-keyframes -amp-start{from{visibility:hidden}to{visibility:visible}}@-o-keyframes -amp-start{from{visibility:hidden}to{visibility:visible}}@keyframes -amp-start{from{visibility:hidden}to{visibility:visible}}</style>
  <noscript><style amp-boilerplate>body{-webkit-animation:none;-moz-animation:none;-ms-animation:none;animation:none}</style></noscript>
  <style amp-custom>
    amp-story { font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; }
    .bg-fallback { width: 100%; height: 100%; background: linear-gradient(160deg, #0f172a, #334155); }
    .bottom { align-content: end; padding: 0; }
    .content {
      padding: 2.5rem 1.25rem 3.5rem;
      background: linear-gradient(to top, rgba(0,0,0,.78) 0%, rgba(0,0,0,.35) 55%, transparent 100%);
      color: #fff;
    }
    .slide-title {
      font-size: 1.65rem;
      line-height: 1.2;
      font-weight: 800;
      margin: 0 0 .6rem;
      text-shadow: 0 2px 12px rgba(0,0,0,.45);
    }
    .slide-body {
      font-size: 1rem;
      line-height: 1.45;
      margin: 0;
      opacity: .95;
      text-shadow: 0 1px 8px rgba(0,0,0,.4);
    }
  </style>
</head>
<body>
  <amp-story standalone
    title="${escAttr(storyTitle)}"
    publisher="${escAttr(publisher)}"
    publisher-logo-src="${escAttr(logo)}"
    poster-portrait-src="${escAttr(poster)}">
    ${pagesHtml}
  </amp-story>
</body>
</html>`;
}

/** Split plain text into short slide-sized chunks for reuse from posts. */
export function textToStoryBodies(plain: string, maxSlides = 8): string[] {
	const cleaned = plain.replace(/\s+/g, ' ').trim();
	if (!cleaned) return [];
	const sentences = cleaned.split(/(?<=[.!?…])\s+/).filter(Boolean);
	const chunks: string[] = [];
	let buf = '';
	for (const s of sentences) {
		const next = buf ? `${buf} ${s}` : s;
		if (next.length > 130 && buf) {
			chunks.push(buf);
			buf = s;
			if (chunks.length >= maxSlides) break;
		} else {
			buf = next;
		}
	}
	if (buf && chunks.length < maxSlides) chunks.push(buf);
	return chunks.slice(0, maxSlides).map((c) => truncate(c, 140));
}

export function htmlToPlainText(html: string): string {
	return html
		.replace(/<script[\s\S]*?<\/script>/gi, ' ')
		.replace(/<style[\s\S]*?<\/style>/gi, ' ')
		.replace(/<[^>]+>/g, ' ')
		.replace(/&nbsp;/g, ' ')
		.replace(/&amp;/g, '&')
		.replace(/&lt;/g, '<')
		.replace(/&gt;/g, '>')
		.replace(/&quot;/g, '"')
		.replace(/\s+/g, ' ')
		.trim();
}
