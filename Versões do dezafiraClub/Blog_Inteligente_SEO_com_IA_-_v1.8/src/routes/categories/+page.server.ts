import { error } from '@sveltejs/kit';
import { getAllCategories } from '$lib/server/database';

export async function load() {
  try {
    const categories = await getAllCategories();

    return {
      categories
    };
  } catch (e) {
    console.error('Error loading categories:', e);
    throw error(500, 'Erro ao carregar categorias');
  }
}
