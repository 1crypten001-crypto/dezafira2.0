import { redirect } from '@sveltejs/kit';
import { destroySession } from '$lib/server/auth';

export const actions = {
  default: async ({ cookies }) => {
    const token = cookies.get('admin_session');

    // Destroir sessão no servidor
    if (token) {
      await destroySession(token);
    }

    cookies.delete('admin_session', { path: '/' });
    throw redirect(303, '/admin/login');
  }
};
