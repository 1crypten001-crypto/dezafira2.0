import { redirect } from '@sveltejs/kit';
import { validateSession } from '$lib/server/auth';

export async function load({ cookies, url }) {
  // Não verificar sessão na página de login
  if (url.pathname === '/admin/login') {
    return {};
  }

  const token = cookies.get('admin_session');

  // Validar token de sessão no servidor (não apenas verificar se existe)
  const username = await validateSession(token || '');

  if (!username) {
    // Token inválido ou expirado — limpar cookie e redirecionar
    if (token) {
      cookies.delete('admin_session', { path: '/' });
    }
    throw redirect(303, '/admin/login');
  }

  return {
    admin: { username }
  };
}
