"""Página pública de ENTREGA + INSTALAÇÃO do 1Convite.

Serve em /instalar (e /entrega) com o passo a passo de como acessar o app
após a compra e como instalá-lo no celular/desktop (PWA).
"""
from html import escape

SALES_URL = "https://www.dezafira.com.br/product/1convite"
APP_URL = "https://1convite.com.br"

_HTML = """<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>1Convite — Entrega e Instalação do App</title>
<meta name="description" content="Como acessar e instalar o app 1Convite no seu celular ou computador depois da compra.">
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  body { font-family:Arial,Helvetica,sans-serif; background:linear-gradient(180deg,#0f172a 0%,#16213e 60%,#0f3460 100%); color:#e2e8f0; min-height:100vh; }
  .wrap { max-width:760px; margin:0 auto; padding:28px 18px 60px; }
  .logo { text-align:center; margin-bottom:6px; }
  .logo .mono { display:inline-flex; align-items:center; justify-content:center; width:64px; height:64px; border-radius:16px; background:#d4af37; color:#14141f; font-size:34px; font-weight:900; }
  h1 { text-align:center; color:#fff; font-size:26px; margin:12px 0 6px; }
  .sub { text-align:center; color:#cfd8e6; font-size:15px; line-height:1.6; margin-bottom:26px; }
  .badge { display:inline-block; background:rgba(212,175,55,.15); border:1px solid rgba(212,175,55,.4); color:#d4af37; font-size:12px; font-weight:700; padding:5px 12px; border-radius:999px; letter-spacing:1px; }
  .card { background:rgba(255,255,255,.04); border:1px solid rgba(212,175,55,.25); border-radius:14px; padding:20px 18px; margin-bottom:16px; }
  .card h2 { color:#d4af37; font-size:17px; margin-bottom:12px; display:flex; align-items:center; gap:8px; }
  .step { display:flex; gap:12px; margin-bottom:14px; }
  .step:last-child { margin-bottom:0; }
  .num { flex-shrink:0; width:26px; height:26px; border-radius:50%; background:#d4af37; color:#14141f; font-weight:900; font-size:13px; display:flex; align-items:center; justify-content:center; }
  .step p { font-size:14px; line-height:1.55; color:#e2e8f0; }
  .step p b { color:#fff; }
  .step code { background:rgba(0,0,0,.35); padding:2px 7px; border-radius:6px; font-size:12.5px; color:#fcd34d; }
  .note { font-size:13px; color:#8fa3bf; line-height:1.6; margin-top:10px; padding-top:10px; border-top:1px dashed rgba(212,175,55,.3); }
  .cta { text-align:center; margin:26px 0 8px; }
  .btn { display:inline-block; background:#d4af37; color:#14141f; font-weight:800; font-size:15px; padding:14px 32px; border-radius:999px; text-decoration:none; }
  .btn.ghost { background:transparent; color:#d4af37; border:1px solid #d4af37; margin-left:8px; }
  .foot { text-align:center; color:#8fa3bf; font-size:12px; margin-top:26px; line-height:1.7; }
  @media (max-width:480px) { h1 { font-size:22px; } .btn.ghost { margin-left:0; margin-top:10px; } }
</style>
</head>
<body>
<div class="wrap">
  <div class="logo"><div class="mono">1C</div></div>
  <h1>1Convite — Entrega &amp; Instalação</h1>
  <p class="sub"><span class="badge">ACESSO IMEDIATO APÓS O PAGAMENTO</span><br>
  Assim que o pagamento for confirmado (PIX ou cartão), o seu acesso é liberado na hora no e-mail usado na compra.</p>

  <div class="card">
    <h2>🛍️ Depois da compra (entrega)</h2>
    <div class="step"><div class="num">1</div><p>Abra o app em <b>https://1convite.com.br</b> no seu celular ou computador.</p></div>
    <div class="step"><div class="num">2</div><p>Entre com o <b>mesmo e-mail usado na compra</b> (ou crie a conta com ele).</p></div>
    <div class="step"><div class="num">3</div><p>Seu plano <b>Premium</b> aparece ativo na aba <b>Minha Conta</b> — e todos os recursos liberados: Bíblia narrada, Trilha do Reino, Arcade bíblico, conselheiros IA e muito mais.</p></div>
    <div class="step"><div class="num">4</div><p>Dúvidas? Fale com a gente pelo WhatsApp comercial (botão de suporte dentro do app).</p></div>
    <p class="note">💡 A liberação acontece automaticamente pelo webhook de pagamento (Asaas). Se pagou e ainda não apareceu, aguarde 1–2 minutos e reabra o app — ou fale conosco.</p>
  </div>

  <div class="card">
    <h2>📱 Como instalar no Android (Chrome)</h2>
    <div class="step"><div class="num">1</div><p>Abra <b>https://1convite.com.br</b> no navegador <b>Chrome</b>.</p></div>
    <div class="step"><div class="num">2</div><p>Toque no menu <code>⋮</code> (canto superior direito).</p></div>
    <div class="step"><div class="num">3</div><p>Toque em <b>“Adicionar à tela inicial”</b> (ou “Instalar app”).</p></div>
    <div class="step"><div class="num">4</div><p>Confirme em <b>“Adicionar”</b> — o ícone do 1Convite aparece na tela inicial como um app normal.</p></div>
  </div>

  <div class="card">
    <h2>📱 Como instalar no iPhone (Safari)</h2>
    <div class="step"><div class="num">1</div><p>Abra <b>https://1convite.com.br</b> no <b>Safari</b>.</p></div>
    <div class="step"><div class="num">2</div><p>Toque no botão <b>Compartilhar</b> <code>⎋</code> (na barra inferior).</p></div>
    <div class="step"><div class="num">3</div><p>Toque em <b>“Adicionar à Tela de Início”</b>.</p></div>
    <div class="step"><div class="num">4</div><p>Confirme em <b>“Adicionar”</b> — pronto, o app fica na tela inicial e funciona até offline (para leituras salvas).</p></div>
  </div>

  <div class="card">
    <h2>💻 Como instalar no computador (Chrome / Edge)</h2>
    <div class="step"><div class="num">1</div><p>Abra <b>https://1convite.com.br</b> no Chrome ou Edge.</p></div>
    <div class="step"><div class="num">2</div><p>Clique no ícone <b>de instalação</b> na barra de endereço (monitor com ↓) ou no menu <code>⋮</code> → <b>“Instalar 1Convite…”</b>.</p></div>
    <div class="step"><div class="num">3</div><p>Confirme — o app abre em janela própria, como um programa.</p></div>
  </div>

  <div class="cta">
    <a class="btn" href="{sales}">🚀 Página de Venda</a>
    <a class="btn ghost" href="{app}">Abrir o App agora</a>
  </div>
  <p class="foot">1Convite — O App do Reino • Bíblia narrada • Matriz diária • Arcade bíblico • Conselheiros IA<br>Pagamento seguro via Asaas (PIX e cartão) • Suporte pelo WhatsApp</p>
</div>
</body>
</html>
"""


def instalar_page_html() -> str:
    return _HTML.replace("{sales}", escape(SALES_URL, quote=True)).replace("{app}", escape(APP_URL, quote=True))
