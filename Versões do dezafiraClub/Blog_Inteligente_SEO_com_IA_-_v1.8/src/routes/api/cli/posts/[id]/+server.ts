import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import {
  getPostById,
  updatePost,
  deletePost,
  generateUniqueSlug,
  assignCategoriesToPost,
  getCategoriesByPostId
} from '$lib/server/database';
import { requireCLIToken } from '../../auth';

// GET /api/cli/posts/:id
export const GET: RequestHandler = async ({ request, params }) => {
  const authError = await requireCLIToken(request);
  if (authError) return authError;

  const id = parseInt(params.id);
  if (isNaN(id)) return json({ error: 'ID inválido' }, { status: 400 });

  const post = await getPostById(id);
  if (!post) return json({ error: 'Post não encontrado' }, { status: 404 });

  const categories = await getCategoriesByPostId(id);

  return json({
    ...post,
    published: Boolean(post.published),
    pinterest_enabled: Boolean(post.pinterest_enabled),
    is_18_plus: Boolean(post.is_18_plus),
    categories: categories.map(c => ({ id: c.id, name: c.name, slug: c.slug }))
  });
};

// PUT /api/cli/posts/:id
export const PUT: RequestHandler = async ({ request, params }) => {
  const authError = await requireCLIToken(request);
  if (authError) return authError;

  const id = parseInt(params.id);
  if (isNaN(id)) return json({ error: 'ID inválido' }, { status: 400 });

  const post = await getPostById(id);
  if (!post) return json({ error: 'Post não encontrado' }, { status: 404 });

  let body: any;
  try {
    body = await request.json();
  } catch {
    return json({ error: 'Body JSON inválido' }, { status: 400 });
  }

  const { title, content, excerpt, cover_image, published, pinterest_enabled, pinterest_image, category_ids, is_18_plus, slug: customSlug } = body;

  let slug = post.slug;
  if (customSlug && customSlug !== post.slug) {
    slug = await generateUniqueSlug(customSlug, post.slug, id);
  } else if (title && title !== post.title && !customSlug) {
    // Don't auto-regenerate slug on title change to avoid breaking URLs
  }

  await updatePost(id, {
    title: title?.trim() ?? undefined,
    slug,
    content: content ?? undefined,
    excerpt: excerpt ?? undefined,
    cover_image: cover_image ?? undefined,
    published: published !== undefined ? (published ? 1 : 0) : undefined,
    pinterest_enabled: pinterest_enabled !== undefined ? (pinterest_enabled ? 1 : 0) : undefined,
    pinterest_image: pinterest_image ?? undefined,
    is_18_plus: is_18_plus !== undefined ? (is_18_plus ? 1 : 0) : undefined
  });

  if (Array.isArray(category_ids)) {
    await assignCategoriesToPost(id, category_ids.map(Number));
  }

  return json({ success: true, id, slug });
};

// DELETE /api/cli/posts/:id
export const DELETE: RequestHandler = async ({ request, params }) => {
  const authError = await requireCLIToken(request);
  if (authError) return authError;

  const id = parseInt(params.id);
  if (isNaN(id)) return json({ error: 'ID inválido' }, { status: 400 });

  const post = await getPostById(id);
  if (!post) return json({ error: 'Post não encontrado' }, { status: 404 });

  await deletePost(id);
  return json({ success: true, message: `Post "${post.title}" deletado.` });
};
