import type { PageServerLoad, Actions } from './$types';
import { fail } from '@sveltejs/kit';
import { getCLITokenStatus, regenerateCLIToken, getAllCategories, getPostsAdminPage } from '$lib/server/database';

export const load: PageServerLoad = async () => {
  const [tokenStatus, categories, postPage] = await Promise.all([
    getCLITokenStatus(),
    getAllCategories(),
    getPostsAdminPage({ page: 1, limit: 10 })
  ]);

  const posts = postPage.posts.map(p => ({
    id: p.id,
    title: p.title,
    slug: p.slug,
    published: Boolean(p.published),
    created_at: p.created_at
  }));

  return {
    token: null,
    tokenConfigured: tokenStatus.configured,
    tokenExpiresAt: tokenStatus.expiresAt,
    categories,
    posts
  };
};

export const actions: Actions = {
  regenerate: async () => {
    try {
      const token = await regenerateCLIToken();
      const status = await getCLITokenStatus();
      return { success: true, token, tokenExpiresAt: status.expiresAt };
    } catch (e) {
      return fail(500, { error: 'Erro ao regenerar token' });
    }
  }
};
