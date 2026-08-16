import type { PageServerLoad } from './$types';
import {
	countPosts,
	getAllCategories,
	getActiveAdsByPlacement,
	getAllProducts,
	hasUserPurchasedProduct,
	getUserInterests,
	getSettings,
	getAllPosts
} from '$lib/server/database';
import { sanitizeAds } from '$lib/server/sanitize';
import { getTenantId } from '$lib/server/tenant';
import {
	getHomeFeed,
	getRecommendationReason,
	loadRecentlySeen
} from '$lib/server/interest-engine';

export const load: PageServerLoad = async ({ url, locals, cookies }) => {
	const tenantId = getTenantId();
	const page = Number(url.searchParams.get('page')) || 1;
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
	// Mixed feed ranks a candidate window; pagination still reflects total published posts
	const totalPages = Math.ceil(totalPosts / limit);

	const categories = await getAllCategories(tenantId);
	// Sidebar popular: always chronological (stable, no personalization noise)
	const popularPosts = await getAllPosts({ limit: 4 }, tenantId);

	const rawProducts = await getAllProducts();
	const products = await Promise.all(
		rawProducts.map(async (p) => {
			let hasPurchased = false;
			if (p.price_cents <= 0) {
				hasPurchased = true;
			} else if (locals.user) {
				if (locals.user.role === 'admin') {
					hasPurchased = true;
				} else {
					hasPurchased = await hasUserPurchasedProduct(locals.user.id, p.id);
				}
			}
			return {
				...p,
				hasPurchased
			};
		})
	);

	const sidebarAds = sanitizeAds(await getActiveAdsByPlacement('sidebar', tenantId));
	const homeMiddleAds = sanitizeAds(await getActiveAdsByPlacement('home_middle', tenantId));

	return {
		posts,
		currentPage: page,
		totalPages,
		searchQuery: search,
		categories,
		popularPosts,
		sidebarAds,
		homeMiddleAds,
		products
	};
};
