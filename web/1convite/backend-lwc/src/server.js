// ────────────────────────────────────────────────────────────────────────────
// 1Convite — sidecar LWC (Conselheiros IA via ChatGPT)
// ────────────────────────────────────────────────────────────────────────────
// Servidor MÍNIMO que monta o handler oficial `@opencoredev/loginwithchatgpt-server`
// sob /api/v1/chatgpt/*. O DezafiraADM (FastAPI) faz proxy transparente para cá:
//
//   LWC_SIDECAR_URL=http://127.0.0.1:3111  python server.py
//
// Mantém exatamente o mesmo fluxo do backend original do 1Convite (device flow
// do ChatGPT) e o mesmo segredo (LWC_SECRET) — sem reimplementar o protocolo.
// ────────────────────────────────────────────────────────────────────────────
import cors from 'cors';
import express from 'express';
import { createChatGPTHandler } from '@opencoredev/loginwithchatgpt-server';

const PORT = process.env.PORT || 3111;
const LWC_SECRET = process.env.LWC_SECRET || 'a-very-stable-secret-for-development-1convite-32-chars-long!';
const allowedOrigins = (process.env.ALLOWED_ORIGINS || '')
  .split(',')
  .map((s) => s.trim())
  .filter(Boolean);

const app = express();
app.use(cors({ origin: allowedOrigins.length ? allowedOrigins : true, credentials: true }));
app.use(express.json());

const chatGptHandler = createChatGPTHandler({
  secret: LWC_SECRET,
  basePath: '/api/v1/chatgpt',
  dangerouslyAllowTokenExport: true,
  allowedOrigins: allowedOrigins.length ? allowedOrigins : undefined,
});

async function toWebRequest(req) {
  const protocol = req.protocol;
  const host = req.get('host');
  const url = `${protocol}://${host}${req.originalUrl}`;
  const headers = new Headers();
  for (const [key, value] of Object.entries(req.headers)) {
    if (value) {
      if (Array.isArray(value)) value.forEach((v) => headers.append(key, v));
      else headers.set(key, value);
    }
  }
  let body = null;
  if (req.method !== 'GET' && req.method !== 'HEAD') {
    body = typeof req.body === 'object' ? JSON.stringify(req.body) : req.body;
  }
  return new Request(url, { method: req.method, headers, body });
}

async function fromWebResponse(webRes, res) {
  res.status(webRes.status);
  webRes.headers.forEach((value, key) => res.setHeader(key, value));
  if (webRes.body) {
    const reader = webRes.body.getReader();
    const decoder = new TextDecoder();
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      res.write(value);
    }
    res.end();
  } else {
    res.end();
  }
}

app.all('/api/v1/chatgpt/*', async (req, res) => {
  console.log(`[LWC] ${req.method} ${req.originalUrl}`);
  try {
    const webReq = await toWebRequest(req);
    const webRes = await chatGptHandler.handler(webReq);
    await fromWebResponse(webRes, res);
  } catch (err) {
    console.error('[LWC] Erro:', err.message);
    res.status(500).json({ error: err.message });
  }
});

app.get('/healthz', (_req, res) => res.json({ status: 'ok', service: '1convite-lwc' }));

app.listen(PORT, '0.0.0.0', () => {
  console.log(`[LWC] sidecar ouvindo em 0.0.0.0:${PORT} (basePath /api/v1/chatgpt)`);
});
