import { redirect, fail } from '@sveltejs/kit';
import { deletePost } from '$lib/server/database';
import type { Actions } from './$types';

export const actions: Actions = {
  default: async ({ params }) => {
    const id = parseInt(params.id);

    try {
      await deletePost(id);
      throw redirect(303, '/admin/posts');
    } catch (error) {
      if ((error as { status?: number }).status === 303) {
        throw error;
      }
      return fail(500, { error: 'Erro ao excluir post' });
    }
  }
};
