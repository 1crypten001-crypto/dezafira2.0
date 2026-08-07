import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { getAllCategories } from '$lib/server/database';
import { requireCLIToken } from '../auth';

// GET /api/cli/categories — Lista todas as categorias
export const GET: RequestHandler = async ({ request }) => {
  const authError = await requireCLIToken(request);
  if (authError) return authError;

  const categories = await getAllCategories();
  return json({
    categories: categories.map(c => ({
      id: c.id,
      name: c.name,
      slug: c.slug,
      description: c.description || null,
      pinterest_enabled: Boolean(c.pinterest_enabled),
      post_count: c.post_count || 0
    }))
  });
};
