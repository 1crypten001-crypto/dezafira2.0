import { error } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import {
	getWebStoryBySlug,
	getWebStorySlides,
	getSettings
} from '$lib/server/database';
import { buildAmpWebStoryHtml } from '$lib/server/web-story-amp';
import { env } from '$env/dynamic/private';

/**
 * Public AMP Web Story — full document response (no SvelteKit chrome).
 * Required for AMP validity: controlled markup only.
 */
export const GET: RequestHandler = async ({ params, url }) => {
	const slug = (params.slug || '').trim().toLowerCase();
	if (!slug) throw error(404, 'Story não encontrada');

	const story = await getWebStoryBySlug(slug);
	if (!story || story.published !== 1) {
		throw error(404, 'Story não encontrada');
	}

	const slides = await getWebStorySlides(story.id);
	const settings = await getSettings();
	const rawSiteUrl = env.SITE_URL || settings.site_url || `${url.protocol}//${url.host}`;
	const siteUrl = rawSiteUrl.replace(/\/$/, '');
	const siteTitle = settings.site_title || 'Blog';
	const siteLogo = settings.site_logo || '/favicon.svg';

	const html = buildAmpWebStoryHtml({
		story,
		slides,
		siteUrl,
		siteTitle,
		siteLogo,
		publisherName: siteTitle
	});

	return new Response(html, {
		headers: {
			'Content-Type': 'text/html; charset=utf-8',
			'Cache-Control': 'public, max-age=60',
			// AMP stories are their own document; avoid framing surprises
			'X-Content-Type-Options': 'nosniff'
		}
	});
};
