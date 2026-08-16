// ============================================================================
// DEZAFIRA ADM — Proxy /api/v1/*
// Roteia as chamadas da ADM (static/index.html) para o backend FastAPI.
// O painel admin usa endpoints /api/v1/* relativos — este catch-all encaminha
// tudo (GET/POST/PUT/DELETE/PATCH) com o mesmo método, headers e corpo.
//
// O corpo é repassado como stream (request.body) — uploads binários grandes
// (imagens, vídeos, os 100MB do BODY_SIZE_LIMIT) chegam intactos ao backend
// sem serem bufferizados em memória nem corrompidos por decodificação de texto.
// ============================================================================
import type { RequestHandler } from '$types';

const BACKEND_URL = (process.env.BACKEND_URL || 'https://dezafiraadm-production.up.railway.app').replace(/\/+$/, '');

export const GET: RequestHandler = proxy;
export const POST: RequestHandler = proxy;
export const PUT: RequestHandler = proxy;
export const DELETE: RequestHandler = proxy;
export const PATCH: RequestHandler = proxy;

async function proxy({ request, url }: Parameters<RequestHandler>[0]): Promise<Response> {
  // url.pathname já é /api/v1/... — monta a URL do backend mantendo query
  const backendUrl = `${BACKEND_URL}${url.pathname}${url.search}`;
  const method = request.method;

  const headers = new Headers();
  // Repassa o Authorization (token admin) — essencial para a ADM
  if (request.headers.get('authorization')) {
    headers.set('authorization', request.headers.get('authorization')!);
  }
  // Content-Type (inclui boundary de multipart/form-data — não pode faltar)
  if (request.headers.get('content-type')) {
    headers.set('content-type', request.headers.get('content-type')!);
  }

  // Corpo: stream direto para não corromper binários nem estourar memória
  const hasBody = method !== 'GET' && method !== 'HEAD';
  const body = hasBody ? request.body : undefined;

  try {
    const resp = await fetch(backendUrl, {
      method,
      headers,
      body,
      // Node 18+: necessário ao repassar ReadableStream como body
      ...(hasBody ? { duplex: 'half' as const } : {}),
      cache: 'no-store',
    });
    const respBody = await resp.text();
    return new Response(respBody, {
      status: resp.status,
      headers: {
        'content-type': resp.headers.get('content-type') || 'application/json; charset=utf-8',
        'cache-control': 'no-store',
      },
    });
  } catch (e: unknown) {
    console.error(`[AdmProxy] Erro ao encaminhar ${method} ${url.pathname}:`, e);
    return new Response(
      JSON.stringify({ success: false, error: 'Backend indisponível (proxy /api/v1)' }),
      { status: 502, headers: { 'content-type': 'application/json' } }
    );
  }
}
