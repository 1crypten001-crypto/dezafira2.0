import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { query } from '$lib/server/database';

// GET /healthz — healthcheck do Railway (railway.toml: healthcheckPath = "/healthz")
// Verifica a conexão REAL com o banco (SQLite local ou libsql-server) com timeout
// de 4s, para o Railway detectar banco fora do ar sem esperar o timeout do proxy.
export const GET: RequestHandler = async () => {
  const started = Date.now();
  const noStore = { 'Cache-Control': 'no-store' };

  try {
    await withTimeout(query('SELECT 1'), 4000);
    return json({ status: 'ok', db: 'connected', ms: Date.now() - started }, { headers: noStore });
  } catch (err) {
    console.error('[healthz] falha ao checar banco:', err);
    return json(
      { status: 'error', db: 'disconnected', error: String(err), ms: Date.now() - started },
      { status: 503, headers: noStore }
    );
  }
};

// Executa a promise com timeout — o timer é sempre limpo (clearTimeout),
// para não deixar handles pendentes no event loop a cada probe.
function withTimeout<T>(promise: Promise<T>, ms: number): Promise<T> {
  let timer: ReturnType<typeof setTimeout> | undefined;
  const timeout = new Promise<never>((_, reject) => {
    timer = setTimeout(() => reject(new Error(`timeout: banco não respondeu em ${ms / 1000}s`)), ms);
  });
  return Promise.race([promise, timeout]).finally(() => clearTimeout(timer));
}
