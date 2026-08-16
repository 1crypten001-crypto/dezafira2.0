import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { updateCategory, getAllCategories } from '$lib/server/database';
import { requireCLIToken } from '../../auth';
import { categoryPinterestSchema, zodError } from '../../validation';

export const PATCH: RequestHandler = async ({ request, params, getClientAddress }) => {
  const authError = await requireCLIToken(request, getClientAddress());
  if (authError) return authError;

  if (!/^\d+$/.test(params.id)) return json({ error: 'ID inválido.' }, { status: 400 });
  const id = Number(params.id);

  let rawBody: unknown;
  try {
    rawBody = await request.json();
  } catch {
    return json({ error: 'Body JSON inválido.' }, { status: 400 });
  }
  const parsed = categoryPinterestSchema.safeParse(rawBody);
  if (!parsed.success) return json(zodError(parsed.error), { status: 400 });

  try {
    const categories = await getAllCategories();
    const category = categories.find((item) => item.id === id);
    if (!category) return json({ error: `Categoria com ID ${id} não encontrada.` }, { status: 404 });

    await updateCategory(id, undefined, category.name, category.slug, parsed.data.pinterest_enabled);
    return json({
      success: true,
      category: {
        id: category.id,
        name: category.name,
        slug: category.slug,
        pinterest_enabled: parsed.data.pinterest_enabled
      }
    });
  } catch (error) {
    console.error(`[CLI CATEGORIES] Failed to update category ${id}:`, error);
    return json({ error: 'Falha ao atualizar categoria.' }, { status: 500 });
  }
};
