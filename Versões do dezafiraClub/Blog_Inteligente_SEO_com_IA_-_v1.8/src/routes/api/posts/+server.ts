import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { countPosts, getUserInterests, getSettings } from '$lib/server/database';
import { getTenantId } from '$lib/server/tenant';
import {
	getHomeFeed,
	getRecommendationReason,
	loadRecentlySeen
} from '$lib/server/interest-engine';

/**
 * Infinite-scroll endpoint — must use the same ranking as the home page
 * (personalized mixed feed + interests + recently-seen cooldown).
 */
export const GET: RequestHandler = async ({ url, locals, cookies }) => {
	const tenantId = getTenantId();
	const page = Math.max(1, Number(url.searchParams.get('page')) || 1);
	const search = url.searchParams.get('q') || '';
	const limit = 7;

	const settings = await getSettings(tenantId);
	const recommendationsEnabled = settings.enable_recommendations !== '0';
	let userInterests: { categories: Record<string, number>; tags: Record<string, number> } | undefined;
	let recentlySeen: Map<number, number> | undefined;

	if (recommendationsEnabled) {
		if (locals.user) {
			userInterests = await getUserInterests(locals.user.id);
		} else {
			const cookieVal = cookies.get('user_interests');
			if (cookieVal) {
				try {
					userInterests = JSON.parse(cookieVal);
				} catch {
					// ignore
				}
			}
		}
		recentlySeen = await loadRecentlySeen(locals, cookies);
	}

	const rawPosts = await getHomeFeed({
		page,
		limit,
		search,
		userInterests,
		recommendationsEnabled,
		recentlySeen
	});

	const posts = rawPosts.map((p) => ({
		...p,
		recommendationReason: getRecommendationReason(p, userInterests)
	}));

	const totalPosts = await countPosts({ search }, tenantId);
	const totalPages = Math.ceil(totalPosts / limit);

	return json({
		posts,
		currentPage: page,
		totalPages
	});
};
