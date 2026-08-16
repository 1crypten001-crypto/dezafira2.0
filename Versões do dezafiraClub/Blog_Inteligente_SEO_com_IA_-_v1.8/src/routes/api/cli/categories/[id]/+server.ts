import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { getCategoryBySlug, updateCategory, getAllCategories } from '$lib/server/database';
import { requireCLIToken } from '../../auth';

// PATCH /api/cli/categories/:id — Ativa/desativa Pinterest de uma categoria
export const PATCH: RequestHandler = async ({ request, params }) => {
  const authError = await requireCLIToken(request);
  if (authError) return authError;

  const id = parseInt(params.id);
  if (isNaN(id)) {
    return json({ error: 'ID inválido. Use o ID numérico da categoria.' }, { status: 400 });
  }

  let body: any;
  try {
    body = await request.json();
  } catch {
    return json({ error: 'Body JSON inválido' }, { status: 400 });
  }

  if (body.pinterest_enabled === undefined) {
    return json({ error: 'Campo "pinterest_enabled" (true ou false) é obrigatório.' }, { status: 400 });
  }

  // Fetch the category to get current name/slug (required by updateCategory)
  const categories = await getAllCategories();
  const cat = categories.find(c => c.id === id);
  if (!cat) {
    return json({ error: `Categoria com ID ${id} não encontrada.` }, { status: 404 });
  }

  const pinterestEnabled = Boolean(body.pinterest_enabled);

  await updateCategory(id, undefined, cat.name, cat.slug, pinterestEnabled);

  return json({
    success: true,
    category: {
      id: cat.id,
      name: cat.name,
      slug: cat.slug,
      pinterest_enabled: pinterestEnabled
    },
    message: `Pinterest ${pinterestEnabled ? 'ativado' : 'desativado'} para a categoria "${cat.name}".`
  });
};
