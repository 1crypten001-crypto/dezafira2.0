import type { PageServerLoad } from './$types';
import {
	getAllPosts,
	countPosts,
	getAllCategories,
	getSettings,
	getActiveAdsByPlacement
} from '$lib/server/database';
import { sanitizeAds } from '$lib/server/sanitize';
import { getTenantId } from '$lib/server/tenant';

export const load: PageServerLoad = async ({ params, url }) => {
	const tenantId = getTenantId();
	const categorySlug = params.slug;
	const page = Number(url.searchParams.get('page')) || 1;
	const limit = 7;

	const posts = await getAllPosts({ page, limit, categorySlug }, tenantId);
	const totalPosts = await countPosts({ categorySlug }, tenantId);
	const totalPages = Math.ceil(totalPosts / limit);

	const categories = await getAllCategories(tenantId);
	const currentCategory = categories.find((c) => c.slug === categorySlug);
	const popularPosts = await getAllPosts({ limit: 4 }, tenantId);
	const settings = await getSettings(tenantId);

	// Ads sanitizados para prevenir XSS
	const sidebarAds = sanitizeAds(await getActiveAdsByPlacement('sidebar', tenantId));

	return {
		posts,
		currentPage: page,
		totalPages,
		categorySlug,
		currentCategory,
		categories,
		popularPosts,
		settings,
		sidebarAds
	};
};
