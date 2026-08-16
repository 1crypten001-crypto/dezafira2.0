import { json } from '@sveltejs/kit';
import { validateCLIToken } from '$lib/server/database';
import { checkRateLimit } from '$lib/server/security/rateLimit';

const CLI_RATE_LIMIT = {
  windowMs: 60 * 1000,
  maxRequests: 120,
  keyPrefix: 'rl:cli',
  message: 'Muitas requisições à API CLI. Aguarde um minuto.'
};

/** Validates rate limit and the Bearer token used by CLI routes. */
export async function requireCLIToken(request: Request, identifier = 'unknown'): Promise<Response | null> {
  const rateLimit = await checkRateLimit(identifier, CLI_RATE_LIMIT);
  const headers = {
    'X-RateLimit-Limit': String(rateLimit.limit),
    'X-RateLimit-Remaining': String(rateLimit.remaining),
    'X-RateLimit-Reset': new Date(rateLimit.resetAt).toISOString()
  };

  if (!rateLimit.allowed) {
    return json({ error: CLI_RATE_LIMIT.message }, { status: 429, headers });
  }

  const auth = request.headers.get('authorization');
  if (!auth || !auth.startsWith('Bearer ')) {
    return json(
      { error: 'Authorization header missing. Use: Authorization: Bearer <token>' },
      { status: 401, headers }
    );
  }

  const token = auth.slice(7).trim();
  if (!(await validateCLIToken(token))) {
    return json(
      { error: 'Token inválido ou expirado. Regenere o token no painel admin.' },
      { status: 403, headers }
    );
  }

  return null;
}
