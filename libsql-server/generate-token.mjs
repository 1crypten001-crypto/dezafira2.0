// ============================================================================
// Gera o token de acesso (JWT HS256) para o libsql-server no Railway.
// Uso:
//   SQLD_AUTH_JWT_KEY=seu_segredo node generate-token.mjs
// Saída: cole o token em DATABASE_AUTH_TOKEN na DezafiraClube.
// Para rotinas/CI, use rotate-token.mjs (imprime só o token).
// ============================================================================
import { createToken } from './libsql-token.mjs';

const SECRET = process.env.SQLD_AUTH_JWT_KEY;

try {
  const token = createToken(SECRET);
  console.log('✅ Token (DATABASE_AUTH_TOKEN):');
  console.log(token);
  console.log('\n📌 Variáveis para a DezafiraClube:');
  console.log(`DATABASE_URL=<URL_HTTP_DO_SERVIÇO_LIBSQL>`);
  console.log(`DATABASE_AUTH_TOKEN=${token}`);
} catch (err) {
  console.error(`❌ ${err.message}`);
  process.exit(1);
}
