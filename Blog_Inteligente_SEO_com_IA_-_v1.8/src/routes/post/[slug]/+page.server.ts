import { error } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';
import {
	getPostBySlug,
	getSettings,
	getAllCategories,
	getAllPosts,
	getActiveAdsByPlacement,
	getRelatedPosts,
	isUserPremium,
	getProductsByPostId,
	hasUserPurchasedProduct,
	getUserInterests,
	getCollaborativeRecommendations
} from '$lib/server/database';
import { getRecommendationReason } from '$lib/server/interest-engine';
import { sanitizeHtml, sanitizeAds } from '$lib/server/sanitize';
import { getTenantId } from '$lib/server/tenant';


export const load: PageServerLoad = async ({ params, locals, cookies }) => {

	const tenantId = getTenantId();
	const post = await getPostBySlug(params.slug, tenantId);

	if (!post) {
		throw error(404, 'Post não encontrado');
	}

	let hasAccess = true;
	if (post.is_premium === 1) {
		if (!locals.user) {
			hasAccess = false;
		} else if (locals.user.role !== 'admin') {
			const userIsPremium = await isUserPremium(locals.user.id);
			if (!userIsPremium) {
				hasAccess = false;
			}
		}
	}

	// Sanitizar conteúdo do post para prevenir XSS e truncar se não houver acesso
	const previewContent = post.excerpt 
		? post.excerpt 
		: (post.content.replace(/<[^>]*>/g, '').substring(0, 350) + '...');

	const sanitizedPost = {
		...post,
		content: hasAccess ? sanitizeHtml(post.content) : sanitizeHtml(previewContent),
		excerpt: post.excerpt ? sanitizeHtml(post.excerpt) : null
	};

	const settings = await getSettings(tenantId);
	const categories = await getAllCategories(tenantId);
	const popularPosts = await getAllPosts({ limit: 4 }, tenantId);
	
	const rawProducts = await getProductsByPostId(post.id);
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
			// Player de curso do Adm: anexa token de acesso assinado (mesma chave da ponte).
			let external_link = p.external_link;
			if (hasPurchased && locals.user && external_link && String(external_link).includes('/curso/')) {
				const { decorateCourseLink } = await import('$lib/server/courseAccess');
				external_link = decorateCourseLink(external_link, String(locals.user.id));
			}
			return {
				...p,
				external_link,
				hasPurchased
			};
		})
	);

	// Buscar posts relacionados (mesma categoria ou mais recentes) com ordenação baseada em interesses se ativo
	let userInterests = undefined;
	let collaborativePosts: any[] = [];
	if (settings.enable_recommendations !== '0') {
		if (locals.user) {
			userInterests = await getUserInterests(locals.user.id);
		} else {
			const cookieVal = cookies.get('user_interests');
			if (cookieVal) {
				try {
					userInterests = JSON.parse(cookieVal);
				} catch (e) {}
			}
		}
		try {
			collaborativePosts = await getCollaborativeRecommendations(post.id, 3);
		} catch (e) {
			console.error('Error fetching collaborative recommendations:', e);
		}
	}

	const collaborativeIds = new Set(collaborativePosts.map(p => p.id));
	const sanitizedCollaborative = collaborativePosts.map((p) => ({
		...p,
		excerpt: p.excerpt ? sanitizeHtml(p.excerpt) : null,
		recommendationReason: getRecommendationReason(p, userInterests)
	}));

	const normalRelated = (await getRelatedPosts(post.id, 6, userInterests))
		.filter(p => !collaborativeIds.has(p.id))
		.map((p) => ({
			...p,
			excerpt: p.excerpt ? sanitizeHtml(p.excerpt) : null,
			recommendationReason: getRecommendationReason(p, userInterests)
		}));

	const relatedPosts = [...sanitizedCollaborative, ...normalRelated].slice(0, 3);



	// Ads sanitizados para prevenir XSS
	const sidebarAds = sanitizeAds(await getActiveAdsByPlacement('sidebar', tenantId));
	const postInlineAds = sanitizeAds(await getActiveAdsByPlacement('post_inline', tenantId));

	return {
		post: sanitizedPost,
		hasAccess,
		settings,
		categories,
		popularPosts,
		sidebarAds,
		postInlineAds,
		relatedPosts,
		products
	};
};
