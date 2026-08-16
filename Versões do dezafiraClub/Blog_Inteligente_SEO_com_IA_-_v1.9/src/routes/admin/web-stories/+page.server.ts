import { fail, redirect } from '@sveltejs/kit';
import type { Actions, PageServerLoad } from './$types';
import { validateSession } from '$lib/server/auth';
import {
	getAllWebStories,
	getWebStoryById,
	getWebStoryBySlug,
	getWebStorySlides,
	createWebStory,
	updateWebStory,
	deleteWebStory,
	replaceWebStorySlides,
	generateWebStorySlug,
	getAllPostsAdmin,
	getPostById,
	getSettings,
	updateSetting
} from '$lib/server/database';
import { htmlToPlainText, textToStoryBodies } from '$lib/server/web-story-amp';
import { env } from '$env/dynamic/private';

export const load: PageServerLoad = async ({ cookies, url }) => {
	const token = cookies.get('admin_session');
	const username = await validateSession(token || '');
	if (!username) throw redirect(302, '/admin/login');

	const editId = url.searchParams.get('edit');
	const stories = await getAllWebStories();
	const settings = await getSettings();
	const rawSiteUrl = env.SITE_URL || settings.site_url || 'https://seusite.com';
	const siteUrl = rawSiteUrl.replace(/\/$/, '');

	// Lightweight list for "from post" selector
	const posts = (await getAllPostsAdmin()).slice(0, 100).map((p: any) => ({
		id: p.id,
		title: p.title,
		slug: p.slug,
		cover_image: p.cover_image,
		excerpt: p.excerpt,
		published: p.published
	}));

	let editing: any = null;
	let slides: any[] = [];
	if (editId) {
		editing = await getWebStoryById(editId);
		if (editing) {
			slides = await getWebStorySlides(editing.id);
		}
	}

	return {
		stories,
		posts,
		editing,
		slides,
		siteUrl,
		enableStoriesBar: settings.enable_web_stories_bar === '1'
	};
};

function parseSlidesFromForm(data: FormData) {
	const titles = data.getAll('slide_title') as string[];
	const bodies = data.getAll('slide_body') as string[];
	const images = data.getAll('slide_image') as string[];
	const ctaUrls = data.getAll('slide_cta_url') as string[];
	const ctaTexts = data.getAll('slide_cta_text') as string[];
	const max = Math.max(titles.length, bodies.length, images.length, 1);
	const slides = [];
	for (let i = 0; i < max; i++) {
		const title = (titles[i] || '').trim();
		const body = (bodies[i] || '').trim();
		const backgroundImage = (images[i] || '').trim() || null;
		const ctaUrl = (ctaUrls[i] || '').trim() || null;
		const ctaText = (ctaTexts[i] || '').trim() || null;
		if (!title && !body && !backgroundImage) continue;
		slides.push({ title, body, backgroundImage, ctaUrl, ctaText });
	}
	return slides;
}

export const actions: Actions = {
	saveBarSetting: async ({ request, cookies }) => {
		const token = cookies.get('admin_session');
		if (!(await validateSession(token || ''))) return fail(401, { message: 'UNAUTHORIZED' });

		const data = await request.formData();
		const enabled = data.get('enable_web_stories_bar') === 'on' || data.get('enable_web_stories_bar') === '1';
		await updateSetting('enable_web_stories_bar', enabled ? '1' : '0');
		return { success: true, action: 'bar' };
	},

	create: async ({ request, cookies }) => {
		const token = cookies.get('admin_session');
		if (!(await validateSession(token || ''))) return fail(401, { message: 'UNAUTHORIZED' });

		const data = await request.formData();
		const title = (data.get('title') as string || '').trim();
		let slug = (data.get('slug') as string || '').trim().toLowerCase();
		const coverImage = (data.get('cover_image') as string || '').trim() || null;
		const posterPortrait = (data.get('poster_portrait') as string || '').trim() || coverImage;
		const ctaUrl = (data.get('cta_url') as string || '').trim() || null;
		const ctaText = (data.get('cta_text') as string || '').trim() || null;
		const published = data.get('published') === 'on' || data.get('published') === '1';
		const sourcePostIdRaw = data.get('source_post_id') as string;
		const sourcePostId = sourcePostIdRaw ? parseInt(sourcePostIdRaw, 10) : null;

		if (!title) return fail(400, { message: 'WS_TITLE_REQUIRED' });

		if (!slug) slug = await generateWebStorySlug(title);
		else slug = await generateWebStorySlug(slug.replace(/\s+/g, '-'));

		if (!/^[a-z0-9-_]+$/.test(slug)) return fail(400, { message: 'WS_INVALID_SLUG' });

		const existing = await getWebStoryBySlug(slug);
		if (existing) return fail(400, { message: 'WS_SLUG_IN_USE', slug });

		let slides = parseSlidesFromForm(data);

		// Optional: seed from linked post if no slides provided
		if (slides.length === 0 && sourcePostId) {
			const post = await getPostById(sourcePostId);
			if (post) {
				const plain = htmlToPlainText(post.content || post.excerpt || '');
				const bodies = textToStoryBodies(plain, 8);
				const img = post.cover_image || coverImage;
				slides = [
					{ title: post.title, body: (post.excerpt || bodies[0] || '').slice(0, 140), backgroundImage: img, ctaUrl: `/post/${post.slug}`, ctaText: 'Ler artigo' },
					...bodies.slice(post.excerpt ? 0 : 1).map((body) => ({
						title: '',
						body,
						backgroundImage: img,
						ctaUrl: `/post/${post.slug}`,
						ctaText: 'Ler artigo'
					}))
				].slice(0, 10);
			}
		}

		if (slides.length === 0) {
			slides = [
				{
					title,
					body: '',
					backgroundImage: coverImage,
					ctaUrl,
					ctaText: ctaText || 'Saiba mais'
				}
			];
		}

		const result = await createWebStory({
			title,
			slug,
			coverImage: coverImage || slides[0]?.backgroundImage,
			posterPortrait: posterPortrait || coverImage || slides[0]?.backgroundImage,
			sourceType: sourcePostId ? 'post' : 'manual',
			sourcePostId: sourcePostId || null,
			ctaUrl: ctaUrl || slides[0]?.ctaUrl,
			ctaText: ctaText || slides[0]?.ctaText,
			published
		});

		// better-sqlite3 lastInsertRowid / libsql
		const insertId =
			(result as any)?.lastInsertRowid ||
			(result as any)?.lastInsertRowId ||
			(await getWebStoryBySlug(slug))?.id;

		if (insertId) {
			await replaceWebStorySlides(Number(insertId), slides);
		}

		throw redirect(303, '/admin/web-stories?created=1');
	},

	update: async ({ request, cookies }) => {
		const token = cookies.get('admin_session');
		if (!(await validateSession(token || ''))) return fail(401, { message: 'UNAUTHORIZED' });

		const data = await request.formData();
		const id = parseInt(data.get('id') as string, 10);
		if (!id) return fail(400, { message: 'WS_ID_REQUIRED' });

		const existing = await getWebStoryById(id);
		if (!existing) return fail(404, { message: 'WS_NOT_FOUND' });

		const title = (data.get('title') as string || '').trim();
		let slug = (data.get('slug') as string || '').trim().toLowerCase();
		const coverImage = (data.get('cover_image') as string || '').trim() || null;
		const posterPortrait = (data.get('poster_portrait') as string || '').trim() || coverImage;
		const ctaUrl = (data.get('cta_url') as string || '').trim() || null;
		const ctaText = (data.get('cta_text') as string || '').trim() || null;
		const published = data.get('published') === 'on' || data.get('published') === '1';
		const sourcePostIdRaw = data.get('source_post_id') as string;
		const sourcePostId = sourcePostIdRaw ? parseInt(sourcePostIdRaw, 10) : null;

		if (!title) return fail(400, { message: 'WS_TITLE_REQUIRED' });
		if (!slug) slug = await generateWebStorySlug(title, id);
		if (!/^[a-z0-9-_]+$/.test(slug)) return fail(400, { message: 'WS_INVALID_SLUG' });

		const clash = await getWebStoryBySlug(slug);
		if (clash && clash.id !== id) return fail(400, { message: 'WS_SLUG_IN_USE', slug });

		const slides = parseSlidesFromForm(data);
		if (slides.length === 0) return fail(400, { message: 'WS_SLIDES_REQUIRED' });

		await updateWebStory(id, {
			title,
			slug,
			coverImage: coverImage || slides[0]?.backgroundImage,
			posterPortrait: posterPortrait || coverImage || slides[0]?.backgroundImage,
			sourceType: sourcePostId ? 'post' : existing.source_type || 'manual',
			sourcePostId: sourcePostId || null,
			ctaUrl,
			ctaText,
			published,
			sortOrder: existing.sort_order
		});
		await replaceWebStorySlides(id, slides);

		throw redirect(303, '/admin/web-stories?updated=1');
	},

	fromPost: async ({ request, cookies }) => {
		const token = cookies.get('admin_session');
		if (!(await validateSession(token || ''))) return fail(401, { message: 'UNAUTHORIZED' });

		const data = await request.formData();
		const postId = parseInt(data.get('post_id') as string, 10);
		if (!postId) return fail(400, { message: 'WS_POST_REQUIRED' });

		const post = await getPostById(postId);
		if (!post) return fail(404, { message: 'WS_POST_NOT_FOUND' });

		const slug = await generateWebStorySlug(post.title);
		const plain = htmlToPlainText(post.content || post.excerpt || '');
		const bodies = textToStoryBodies(plain, 8);
		const img = post.cover_image || null;
		const cta = `/post/${post.slug}`;

		const slides = [
			{
				title: post.title,
				body: (post.excerpt || bodies[0] || '').slice(0, 140),
				backgroundImage: img,
				ctaUrl: cta,
				ctaText: 'Ler artigo'
			},
			...bodies.slice(post.excerpt ? 0 : 1).map((body) => ({
				title: '',
				body,
				backgroundImage: img,
				ctaUrl: cta,
				ctaText: 'Ler artigo'
			}))
		].slice(0, 10);

		await createWebStory({
			title: post.title,
			slug,
			coverImage: img,
			posterPortrait: img,
			sourceType: 'post',
			sourcePostId: post.id,
			ctaUrl: cta,
			ctaText: 'Ler artigo',
			published: false
		});

		const created = await getWebStoryBySlug(slug);
		if (created) {
			await replaceWebStorySlides(created.id, slides);
			throw redirect(303, `/admin/web-stories?edit=${created.id}&from_post=1`);
		}

		throw redirect(303, '/admin/web-stories?created=1');
	},

	delete: async ({ request, cookies }) => {
		const token = cookies.get('admin_session');
		if (!(await validateSession(token || ''))) return fail(401, { message: 'UNAUTHORIZED' });

		const data = await request.formData();
		const id = parseInt(data.get('id') as string, 10);
		if (!id) return fail(400, { message: 'WS_ID_REQUIRED' });
		await deleteWebStory(id);
		throw redirect(303, '/admin/web-stories?deleted=1');
	},

	/** One-click publish / draft from the management list */
	togglePublish: async ({ request, cookies }) => {
		const token = cookies.get('admin_session');
		if (!(await validateSession(token || ''))) return fail(401, { message: 'UNAUTHORIZED' });

		const data = await request.formData();
		const id = parseInt(data.get('id') as string, 10);
		if (!id) return fail(400, { message: 'WS_ID_REQUIRED' });

		const existing = await getWebStoryById(id);
		if (!existing) return fail(404, { message: 'WS_NOT_FOUND' });

		const next = existing.published === 1 ? 0 : 1;
		await updateWebStory(id, {
			title: existing.title,
			slug: existing.slug,
			coverImage: existing.cover_image,
			posterPortrait: existing.poster_portrait,
			sourceType: existing.source_type,
			sourcePostId: existing.source_post_id,
			ctaUrl: existing.cta_url,
			ctaText: existing.cta_text,
			published: next,
			sortOrder: existing.sort_order
		});

		return { success: true, action: 'toggle', id, published: next };
	}
};
