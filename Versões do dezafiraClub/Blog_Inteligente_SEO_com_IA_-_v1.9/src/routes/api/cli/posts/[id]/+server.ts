import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import {
  getPostById,
  updatePost,
  deletePost,
  generateUniqueSlug,
  assignCategoriesToPost,
  getCategoriesByPostId,
  getExistingCategoryIds
} from '$lib/server/database';
import { requireCLIToken } from '../../auth';
import { updatePostSchema, zodError } from '../../validation';

function parseId(value: string): number | null {
  if (!/^\d+$/.test(value)) return null;
  const id = Number(value);
  return Number.isSafeInteger(id) && id > 0 ? id : null;
}

export const GET: RequestHandler = async ({ request, params, getClientAddress }) => {
  const authError = await requireCLIToken(request, getClientAddress());
  if (authError) return authError;
  const id = parseId(params.id);
  if (!id) return json({ error: 'ID inválido.' }, { status: 400 });

  try {
    const post = await getPostById(id);
    if (!post) return json({ error: 'Post não encontrado.' }, { status: 404 });
    const categories = await getCategoriesByPostId(id);
    return json({
      ...post,
      published: Boolean(post.published),
      pinterest_enabled: Boolean(post.pinterest_enabled),
      is_premium: Boolean(post.is_premium),
      is_18_plus: Boolean(post.is_18_plus),
      categories: categories.map(({ id, name, slug }) => ({ id, name, slug }))
    });
  } catch (error) {
    console.error(`[CLI POSTS] Failed to read post ${id}:`, error);
    return json({ error: 'Falha ao consultar post.' }, { status: 500 });
  }
};

export const PUT: RequestHandler = async ({ request, params, getClientAddress }) => {
  const authError = await requireCLIToken(request, getClientAddress());
  if (authError) return authError;
  const id = parseId(params.id);
  if (!id) return json({ error: 'ID inválido.' }, { status: 400 });

  let rawBody: unknown;
  try {
    rawBody = await request.json();
  } catch {
    return json({ error: 'Body JSON inválido.' }, { status: 400 });
  }
  const parsed = updatePostSchema.safeParse(rawBody);
  if (!parsed.success) return json(zodError(parsed.error), { status: 400 });
  const body = parsed.data;

  try {
    const post = await getPostById(id);
    if (!post) return json({ error: 'Post não encontrado.' }, { status: 404 });

    if (body.category_ids) {
      const existingIds = await getExistingCategoryIds(body.category_ids);
      const missingIds = body.category_ids.filter((categoryId) => !existingIds.includes(categoryId));
      if (missingIds.length > 0) {
        return json({ error: 'Categorias inexistentes.', category_ids: missingIds }, { status: 400 });
      }
    }

    const slug = body.slug && body.slug !== post.slug
      ? await generateUniqueSlug(body.slug, post.slug, id)
      : post.slug;

    await updatePost(id, {
      title: body.title,
      slug,
      content: body.content,
      excerpt: body.excerpt,
      cover_image: body.cover_image,
      published: body.published === undefined ? undefined : Number(body.published),
      pinterest_enabled: body.pinterest_enabled === undefined ? undefined : Number(body.pinterest_enabled),
      pinterest_image: body.pinterest_image,
      is_premium: body.is_premium === undefined ? undefined : Number(body.is_premium),
      is_18_plus: body.is_18_plus === undefined ? undefined : Number(body.is_18_plus),
      youtube_video_url: body.youtube_video_url,
      tags: body.tags
    });
    if (body.category_ids) await assignCategoriesToPost(id, body.category_ids);

    return json({ success: true, id, slug });
  } catch (error) {
    console.error(`[CLI POSTS] Failed to update post ${id}:`, error);
    return json({ error: 'Falha ao atualizar post.' }, { status: 500 });
  }
};

export const DELETE: RequestHandler = async ({ request, params, url, getClientAddress }) => {
  const authError = await requireCLIToken(request, getClientAddress());
  if (authError) return authError;
  const id = parseId(params.id);
  if (!id) return json({ error: 'ID inválido.' }, { status: 400 });
  if (url.searchParams.get('confirm') !== String(id)) {
    return json(
      { error: `Confirme a exclusão definitiva usando ?confirm=${id}.` },
      { status: 400 }
    );
  }

  try {
    const post = await getPostById(id);
    if (!post) return json({ error: 'Post não encontrado.' }, { status: 404 });
    await deletePost(id);
    return json({ success: true, id, title: post.title });
  } catch (error) {
    console.error(`[CLI POSTS] Failed to delete post ${id}:`, error);
    return json({ error: 'Falha ao excluir post.' }, { status: 500 });
  }
};
