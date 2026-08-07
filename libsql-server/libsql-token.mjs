// ============================================================================
// DEZAFIRA — Geração de token JWT HS256 para o libsql-server (módulo comum)
// Usado por generate-token.mjs (humano) e rotate-token.mjs (CI/rotina).
// ============================================================================
import crypto from 'crypto';

const b64url = (buf) => Buffer.from(buf).toString('base64url');

/**
 * Gera um token JWT HS256 aceito pelo sqld (claims sub/iat/nbf/exp).
 * @param {string} secret  SQLD_AUTH_JWT_KEY (mesmo segredo do serviço libsql-server)
 * @param {number} ttlSeconds  validade do token (default: 1 ano)
 * @returns {string} token no formato header.payload.signature
 */
export function createToken(secret, ttlSeconds = 365 * 24 * 3600) {
  if (!secret) throw new Error('SQLD_AUTH_JWT_KEY não definido');
  const now = Math.floor(Date.now() / 1000);
  const header = b64url(JSON.stringify({ alg: 'HS256', typ: 'JWT' }));
  const payload = b64url(JSON.stringify({
    sub: 'dezafiraclube',
    iat: now,
    nbf: now,
    exp: now + ttlSeconds,
  }));
  const sig = crypto.createHmac('sha256', secret).update(`${header}.${payload}`).digest('base64url');
  return `${header}.${payload}.${sig}`;
}
