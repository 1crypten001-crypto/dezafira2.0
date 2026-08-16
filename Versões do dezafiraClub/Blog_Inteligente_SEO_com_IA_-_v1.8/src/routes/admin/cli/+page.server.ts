import type { PageServerLoad, Actions } from './$types';
import { fail } from '@sveltejs/kit';
import { getCLIToken, regenerateCLIToken, getAllCategories, getAllPostsAdmin } from '$lib/server/database';

export const load: PageServerLoad = async () => {
  const [token, categories, allPosts] = await Promise.all([
    getCLIToken(),
    getAllCategories(),
    getAllPostsAdmin()
  ]);

  const posts = allPosts.slice(0, 10).map(p => ({
    id: p.id,
    title: p.title,
    slug: p.slug,
    published: Boolean(p.published),
    created_at: p.created_at
  }));

  return {
    token,
    categories,
    posts
  };
};

export const actions: Actions = {
  regenerate: async () => {
    try {
      const token = await regenerateCLIToken();
      return { success: true, token };
    } catch (e) {
      return fail(500, { error: 'Erro ao regenerar token' });
    }
  }
};
