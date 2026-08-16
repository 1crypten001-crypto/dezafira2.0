// ============================================================================
// DEZAFIRA ADM — Rota /adm
// Proxy para o backend FastAPI que serve o painel admin (static/index.html).
// O backend exige token admin; o HTML e' auto-contido e chama /api/v1/*,
// que tambem sao roteados para o backend via src/routes/api/v1/[...path].
// ============================================================================
import type { RequestHandler } from './$types';

const BACKEND_URL = (process.env.BACKEND_URL || 'https://dezafiraadm-production.up.railway.app').replace(/\/+$/, '');

// /adm → raiz do backend (serve o static/index.html)
export const GET: RequestHandler = async ({ request, url }) => {
  const backendUrl = `${BACKEND_URL}/?${url.searchParams.toString()}`;
  try {
    const resp = await fetch(backendUrl, {
      headers: {
        // Repassa o Authorization (Bearer token) se o browser mandou
        ...(request.headers.get('authorization')
          ? { authorization: request.headers.get('authorization')! }
          : {}),
        'user-agent': request.headers.get('user-agent') || 'dezafira-adm',
      },
      // Sempre revalidar — o painel não deve ficar cacheado
      cache: 'no-store',
    });

    const body = await resp.text();
    return new Response(body, {
      status: resp.status,
      headers: {
        'content-type': resp.headers.get('content-type') || 'text/html; charset=utf-8',
        'cache-control': 'no-store, no-cache, must-revalidate',
        pragma: 'no-cache',
      },
    });
  } catch (e: unknown) {
    console.error('[AdmProxy] Erro ao buscar painel no backend:', e);
    return new Response('Falha ao carregar o painel (backend indisponível)', {
      status: 502,
      headers: { 'content-type': 'text/plain; charset=utf-8' },
    });
  }
};
