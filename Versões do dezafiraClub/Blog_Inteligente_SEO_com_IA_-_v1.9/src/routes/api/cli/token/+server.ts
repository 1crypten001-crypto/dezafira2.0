import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { regenerateCLIToken } from '$lib/server/database';
import { validateSession } from '$lib/server/auth';

// POST /api/cli/token/regenerate — Regenera o token (requer sessão admin ativa)
export const POST: RequestHandler = async ({ cookies }) => {
  const sessionId = cookies.get('admin_session');
  if (!sessionId) {
    return json({ error: 'Não autenticado' }, { status: 401 });
  }
  const username = await validateSession(sessionId);
  if (!username) {
    return json({ error: 'Sessão expirada' }, { status: 401 });
  }

  const token = await regenerateCLIToken();
  return json({ success: true, token });
};
