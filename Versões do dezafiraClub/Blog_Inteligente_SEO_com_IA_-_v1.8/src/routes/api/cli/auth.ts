import { json } from '@sveltejs/kit';
import { validateCLIToken } from '$lib/server/database';

/**
 * Validates the CLI token from the Authorization header.
 * Returns null if valid, or a Response with error if invalid.
 */
export async function requireCLIToken(request: Request): Promise<Response | null> {
  const auth = request.headers.get('Authorization') || request.headers.get('authorization');
  if (!auth || !auth.startsWith('Bearer ')) {
    return json({ error: 'Authorization header missing. Use: Authorization: Bearer <token>' }, { status: 401 });
  }
  const token = auth.slice(7).trim();
  const valid = await validateCLIToken(token);
  if (!valid) {
    return json({ error: 'Token inválido ou expirado. Regenere o token no painel admin.' }, { status: 403 });
  }
  return null;
}
