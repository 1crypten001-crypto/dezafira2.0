import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import {
  getAllPostsAdmin,
  createPost,
  generateUniqueSlug,
  assignCategoriesToPost
} from '$lib/server/database';
import { requireCLIToken } from '../auth';

// GET /api/cli/posts — Lista todos os posts (incluindo rascunhos)
export const GET: RequestHandler = async ({ request }) => {
  const authError = await requireCLIToken(request);
  if (authError) return authError;

  const posts = await getAllPostsAdmin();
  return json({
    posts: posts.map(p => ({
      id: p.id,
      title: p.title,
      slug: p.slug,
      excerpt: p.excerpt,
      cover_image: p.cover_image,
      published: Boolean(p.published),
      pinterest_enabled: Boolean(p.pinterest_enabled),
      pinterest_image: p.pinterest_image,
      is_18_plus: Boolean(p.is_18_plus),
      categories: p.categories || '',
      created_at: p.created_at,
      updated_at: p.updated_at
    }))
  });
};

// POST /api/cli/posts — Cria um novo post
export const POST: RequestHandler = async ({ request }) => {
  const authError = await requireCLIToken(request);
  if (authError) return authError;

  let body: any;
  try {
    body = await request.json();
  } catch {
    return json({ error: 'Body JSON inválido' }, { status: 400 });
  }

  const { title, content, excerpt, cover_image, published, pinterest_enabled, pinterest_image, category_ids, is_18_plus, slug: customSlug } = body;

  if (!title || !content) {
    return json({ error: 'Os campos "title" e "content" são obrigatórios.' }, { status: 400 });
  }
  if (title.trim().length < 3) {
    return json({ error: 'O título deve ter pelo menos 3 caracteres.' }, { status: 400 });
  }

  const slug = customSlug
    ? await generateUniqueSlug(customSlug)
    : await generateUniqueSlug(title);

  const result = await createPost({
    title: title.trim(),
    slug,
    content,
    excerpt: excerpt || '',
    cover_image: cover_image || '',
    published: published ? 1 : 0,
    pinterest_enabled: pinterest_enabled ? 1 : 0,
    pinterest_image: pinterest_image || null,
    is_18_plus: is_18_plus ? 1 : 0
  });

  const postId = result?.lastInsertRowid ?? result?.last_insert_rowid;

  if (postId && Array.isArray(category_ids) && category_ids.length > 0) {
    await assignCategoriesToPost(Number(postId), category_ids.map(Number));
  }

  return json({ success: true, slug, id: Number(postId) }, { status: 201 });
};
