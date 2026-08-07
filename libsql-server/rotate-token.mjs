// ============================================================================
// DEZAFIRA — Rota o token de acesso do libsql-server (uso em CI/rotinas).
// Saída: apenas o token (sem texto), para pipelinar em variáveis/CI.
//
//   SQLD_AUTH_JWT_KEY=seu_segredo node rotate-token.mjs
//
// Para testar/ver o token com texto explicativo, use generate-token.mjs.
// ============================================================================
import { createToken } from './libsql-token.mjs';

const SECRET = process.env.SQLD_AUTH_JWT_KEY;

try {
  process.stdout.write(`${createToken(SECRET)}\n`);
} catch (err) {
  console.error(`❌ ${err.message}`);
  process.exit(1);
}
