import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { regenerateCLIToken, getDBSession } from '$lib/server/database';

// POST /api/cli/token/regenerate — Regenera o token (requer sessão admin ativa)
export const POST: RequestHandler = async ({ request, cookies }) => {
  const sessionId = cookies.get('session');
  if (!sessionId) {
    return json({ error: 'Não autenticado' }, { status: 401 });
  }
  const { getDBSession: getSession } = await import('$lib/server/database');
  const session = await getSession(sessionId);
  if (!session || session.expires_at < Date.now()) {
    return json({ error: 'Sessão expirada' }, { status: 401 });
  }

  const token = await regenerateCLIToken();
  return json({ success: true, token });
};
