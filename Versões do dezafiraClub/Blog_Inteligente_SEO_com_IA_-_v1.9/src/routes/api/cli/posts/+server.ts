import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import {
  createPost,
  deletePost,
  generateUniqueSlug,
  assignCategoriesToPost,
  getExistingCategoryIds,
  getPostsAdminPage
} from '$lib/server/database';
import { requireCLIToken } from '../auth';
import { createPostSchema, listPostsQuerySchema, zodError } from '../validation';

export const GET: RequestHandler = async ({ request, url, getClientAddress }) => {
  const authError = await requireCLIToken(request, getClientAddress());
  if (authError) return authError;

  const parsedQuery = listPostsQuerySchema.safeParse(Object.fromEntries(url.searchParams));
  if (!parsedQuery.success) return json(zodError(parsedQuery.error), { status: 400 });

  try {
    const result = await getPostsAdminPage(parsedQuery.data);
    return json({
      posts: result.posts.map((post) => ({
        ...post,
        published: Boolean(post.published),
        pinterest_enabled: Boolean(post.pinterest_enabled),
        is_premium: Boolean(post.is_premium),
        is_18_plus: Boolean(post.is_18_plus),
        categories: post.categories || ''
      })),
      pagination: {
        page: result.page,
        limit: result.limit,
        total: result.total,
        totalPages: result.totalPages
      }
    });
  } catch (error) {
    console.error('[CLI POSTS] Failed to list posts:', error);
    return json({ error: 'Falha ao listar posts.' }, { status: 500 });
  }
};

export const POST: RequestHandler = async ({ request, getClientAddress }) => {
  const authError = await requireCLIToken(request, getClientAddress());
  if (authError) return authError;

  let rawBody: unknown;
  try {
    rawBody = await request.json();
  } catch {
    return json({ error: 'Body JSON inválido.' }, { status: 400 });
  }

  const parsed = createPostSchema.safeParse(rawBody);
  if (!parsed.success) return json(zodError(parsed.error), { status: 400 });
  const body = parsed.data;

  try {
    const categoryIds = body.category_ids || [];
    const existingIds = await getExistingCategoryIds(categoryIds);
    const missingIds = categoryIds.filter((id) => !existingIds.includes(id));
    if (missingIds.length > 0) {
      return json({ error: 'Categorias inexistentes.', category_ids: missingIds }, { status: 400 });
    }

    const slug = await generateUniqueSlug(body.slug || body.title);
    const result = await createPost({
      title: body.title,
      slug,
      content: body.content,
      excerpt: body.excerpt || '',
      cover_image: body.cover_image || '',
      published: body.published ? 1 : 0,
      pinterest_enabled: body.pinterest_enabled ? 1 : 0,
      pinterest_image: body.pinterest_image || undefined,
      is_premium: body.is_premium ? 1 : 0,
      is_18_plus: body.is_18_plus ? 1 : 0,
      youtube_video_url: body.youtube_video_url || undefined,
      tags: body.tags || undefined
    });
    const rawPostId = result?.lastInsertRowid ?? result?.last_insert_rowid;
    const postId = Number(rawPostId);
    if (!Number.isSafeInteger(postId) || postId <= 0) {
      throw new Error('O banco não retornou um ID válido para o novo post.');
    }

    try {
      if (categoryIds.length > 0) await assignCategoriesToPost(postId, categoryIds);
    } catch (error) {
      await deletePost(postId).catch(() => undefined);
      throw error;
    }

    return json({ success: true, slug, id: postId }, { status: 201 });
  } catch (error) {
    console.error('[CLI POSTS] Failed to create post:', error);
    return json({ error: 'Falha ao criar post.' }, { status: 500 });
  }
};
