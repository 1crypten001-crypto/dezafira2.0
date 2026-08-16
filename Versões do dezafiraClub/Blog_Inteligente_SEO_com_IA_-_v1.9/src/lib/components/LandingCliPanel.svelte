<script lang="ts">
  import { enhance } from '$app/forms';
  import { LANDING_AGENT_PROMPT } from '$lib/landing-cli-manifest';
  let { tokenConfigured = false, tokenExpiresAt = null, form = undefined }: {
    tokenConfigured?: boolean;
    tokenExpiresAt?: number | null;
    form?: { cliToken?: string; cliTokenExpiresAt?: number | null };
  } = $props();
  let copied = $state<string | null>(null);
  let generating = $state(false);
  const token = $derived(form?.cliToken || '');
  const baseUrl = typeof window !== 'undefined' ? window.location.origin : 'https://seusite.com';
  const example = `{
  "title": "Oferta Premium",
  "slug": "oferta-premium",
  "status": "draft",
  "settings": { "seoTitle": "Oferta Premium", "containerWidth": "1200px" },
  "blocks": [
    {
      "id": "hero-cli",
      "type": "hero",
      "properties": {
        "eyebrow": "CONTEÚDO PREMIUM",
        "title": "Landing criada pela CLI",
        "subtitle": "Depois, edite tudo visualmente no Builder.",
        "primaryText": "Ver oferta",
        "primaryHref": "#oferta",
        "image": "https://exemplo.com/hero.jpg"
      }
    },
    {
      "id": "produto-cli",
      "type": "product-showcase",
      "properties": {
        "productId": 1,
        "name": "Nome do produto",
        "description": "Descrição da oferta",
        "price": "R$ 49,90",
        "image": "https://exemplo.com/produto.jpg",
        "buttonText": "Comprar agora",
        "buttonHref": "/product/slug-do-produto"
      }
    },
    {
      "id": "posts-cli",
      "type": "posts-grid",
      "properties": {
        "title": "Leia também",
        "posts": [{ "id": 10, "title": "Título", "slug": "titulo", "href": "/post/titulo" }]
      }
    },
    {
      "id": "html-cli",
      "type": "html",
      "content": "<section style=\"padding:32px;background:#111827;color:white\"><h2>Bônus</h2></section>"
    }
  ]
}`;
  const fullHtmlExample = `{
  "title": "Landing autoral em HTML",
  "slug": "landing-autoral",
  "status": "draft",
  "blocks": [{
    "id": "pagina-html",
    "type": "html",
    "content": "<main style=\"font-family:Inter,Arial,sans-serif;background:#070b18;color:#fff\"><section style=\"max-width:1120px;margin:auto;padding:96px 24px;text-align:center\"><p style=\"color:#60a5fa;font-weight:800\">NOVA EXPERIÊNCIA</p><h1 style=\"font-size:clamp(42px,7vw,78px);line-height:1;margin:20px 0\">Uma landing totalmente nova</h1><p style=\"max-width:680px;margin:0 auto 32px;color:#cbd5e1;font-size:20px\">HTML autoral, responsivo e editável no Builder.</p><a href=\"#oferta\" style=\"display:inline-block;padding:16px 26px;border-radius:12px;background:#3b82f6;color:#fff;text-decoration:none;font-weight:800\">Conhecer oferta</a></section></main>"
  }]
}`;
  async function copyText(text: string, id: string) {
    await navigator.clipboard.writeText(text);
    copied = id;
    setTimeout(() => copied === id && (copied = null), 1800);
  }
</script>

<section class="cli-panel">
  <header>
    <div><span>Automação</span><h2>CLI de Landing Pages</h2><p>Crie, edite e publique landings por JSON. Elas aparecem na lista e continuam editáveis no Builder visual.</p></div>
    <aside>
      <strong class:ready={tokenConfigured || token}>● {tokenConfigured || token ? 'Token configurado' : 'Token não configurado'}</strong>
      {#if token}<div class="token-row"><code class="token">{token}</code><button type="button" class="token-copy" onclick={() => copyText(token, 'token')}>{copied === 'token' ? 'Copiado' : 'Copiar'}</button></div><small>Copie agora: ele não será exibido novamente.</small>{:else}<small>{tokenExpiresAt ? `Expira em ${new Date(tokenExpiresAt).toLocaleDateString('pt-BR')}.` : 'Gere um token para usar a API.'}</small>{/if}
      <form method="POST" action="?/regenerateCliToken" use:enhance={() => { generating = true; return async ({ update }) => { await update(); generating = false; }; }}>
        <button type="submit" disabled={generating}>{generating ? 'Gerando…' : tokenConfigured ? 'Regenerar token' : 'Gerar token'}</button>
      </form>
    </aside>
  </header>

  <div class="auth"><strong>Header obrigatório</strong><code>Authorization: Bearer {token || 'SEU_TOKEN'}</code></div>

  <div class="endpoints">
    <details open><summary><b class="get">GET</b><code>/api/cli/landing-pages/schema</code><span>Contrato para agentes de IA</span></summary><div><p>Retorna fluxo, limites, regras visuais, tipos de bloco e todas as propriedades aceitas.</p><pre>curl -H "Authorization: Bearer SEU_TOKEN" {baseUrl}/api/cli/landing-pages/schema</pre></div></details>
    <details open><summary><b class="get">GET</b><code>/api/cli/landing-pages/resources</code><span>Produtos e posts disponíveis</span></summary><div><pre>curl -H "Authorization: Bearer SEU_TOKEN" {baseUrl}/api/cli/landing-pages/resources</pre></div></details>
    <details open><summary><b class="ai">IA</b><code>Prompt pronto para o agente</code><span>Instruções copiáveis</span></summary><div><p>Cole o prompt abaixo no agente junto com a URL do site e o token.</p><button class="copy" type="button" onclick={() => copyText(LANDING_AGENT_PROMPT, 'prompt')}>{copied === 'prompt' ? 'Copiado' : 'Copiar prompt do agente'}</button><pre>{LANDING_AGENT_PROMPT}</pre></div></details>
    <details><summary><b class="html">HTML</b><code>Página 100% personalizada</code><span>Uma landing inteira em um bloco</span></summary><div><p>O agente pode criar todo o <code>&lt;main&gt;</code> em um único bloco <code>html</code>, com CSS inline responsivo. Use links <code>&lt;a&gt;</code> para CTAs; scripts, estilos globais, iframes, formulários e eventos JavaScript são removidos por segurança.</p><button class="copy" type="button" onclick={() => copyText(fullHtmlExample, 'html')}>{copied === 'html' ? 'Copiado' : 'Copiar exemplo HTML completo'}</button><pre>{fullHtmlExample}</pre></div></details>
    <details open><summary><b class="post">POST</b><code>/api/cli/landing-pages</code><span>Criar landing</span></summary><div><p>Salve como <code>landing.json</code>, ajuste os recursos e envie:</p><button class="copy" type="button" onclick={() => copyText(example, 'example')}>{copied === 'example' ? 'Copiado' : 'Copiar landing.json'}</button><pre>{example}</pre><pre>curl -X POST -H "Authorization: Bearer SEU_TOKEN" -H "Content-Type: application/json" --data-binary @landing.json {baseUrl}/api/cli/landing-pages</pre></div></details>
    <details><summary><b class="get">GET</b><code>/api/cli/landing-pages</code><span>Listar e pesquisar</span></summary><div><pre>curl -H "Authorization: Bearer SEU_TOKEN" "{baseUrl}/api/cli/landing-pages?page=1&amp;limit=25&amp;search=oferta"</pre></div></details>
    <details><summary><b class="put">PUT</b><code>/api/cli/landing-pages/:id</code><span>Editar ou publicar</span></summary><div><pre>curl -X PUT -H "Authorization: Bearer SEU_TOKEN" -H "Content-Type: application/json" -d '&#123;"status":"published"&#125;' {baseUrl}/api/cli/landing-pages/1</pre></div></details>
    <details><summary><b class="del">DELETE</b><code>/api/cli/landing-pages/:id?confirm=:id</code><span>Excluir definitivamente</span></summary><div><pre>curl -X DELETE -H "Authorization: Bearer SEU_TOKEN" "{baseUrl}/api/cli/landing-pages/1?confirm=1"</pre></div></details>
  </div>
  <footer><strong>Blocos:</strong> hero, product-showcase, posts-grid, trust-bar, section, container, columns, column, text, image, button, video, divider, spacer, html, cta, testimonial, pricing e faq.<small>HTML é sanitizado; scripts, iframes, formulários, eventos e URLs perigosas são removidos.</small></footer>
</section>

<style>
  .cli-panel{margin-top:2rem;color:#0f172a}header{display:grid;grid-template-columns:1.3fr .7fr;gap:2rem;padding:clamp(1.5rem,4vw,2.5rem);border-radius:22px;color:#fff;background:radial-gradient(circle at 85% 0,#2563eb 0,transparent 38%),#0f172a;box-shadow:0 22px 60px #0f172a2e}header span{color:#93c5fd;font-size:.7rem;font-weight:900;letter-spacing:.15em;text-transform:uppercase}h2{margin:.45rem 0 .65rem;font-size:clamp(1.7rem,4vw,2.5rem);letter-spacing:-.035em}header p{margin:0;color:#cbd5e1;line-height:1.65}aside{align-self:center;padding:1rem;border:1px solid #ffffff24;border-radius:15px;background:#ffffff12}aside strong{display:block;color:#fbbf24;font-size:.82rem}.ready{color:#4ade80!important}.token{display:block;overflow:hidden;padding:.5rem;border-radius:7px;background:#020617;text-overflow:ellipsis}.token-row{display:flex;align-items:center;gap:.45rem;margin-top:.65rem}.token-row .token{min-width:0;flex:1}.token-copy{width:auto!important;flex:0 0 auto!important;background:#fff!important;color:#1d4ed8!important}aside small,footer small{display:block;margin:.45rem 0 .75rem;color:#cbd5e1}aside button{width:100%;border:0;padding:.65rem;border-radius:8px;background:#3b82f6;color:#fff;font-weight:800}.auth{display:flex;justify-content:space-between;gap:1rem;margin:1rem 0;padding:1rem;border:1px solid #bfdbfe;border-radius:12px;background:#eff6ff}.endpoints{display:grid;gap:.75rem}details{overflow:hidden;border:1px solid #e2e8f0;border-radius:13px;background:#fff}summary{display:flex;align-items:center;gap:.7rem;padding:1rem;cursor:pointer;font-weight:700}summary b{min-width:3.5rem;padding:.3rem;border-radius:6px;color:#fff;text-align:center;font-size:.65rem}summary span{margin-left:auto;color:#64748b;font-size:.8rem}.get{background:#0284c7}.post{background:#059669}.put{background:#d97706}.del{background:#dc2626}.ai{background:linear-gradient(135deg,#7c3aed,#4f46e5)}.html{background:linear-gradient(135deg,#111827,#475569)}details>div{padding:0 1rem 1rem}.copy{float:right;border:0;padding:.5rem .7rem;border-radius:7px;background:#dbeafe;color:#1d4ed8;font-weight:800}pre{overflow-x:auto;clear:both;margin:.65rem 0 0;padding:1rem;border-radius:9px;background:#0b1220;color:#dbeafe;font:.76rem/1.6 ui-monospace,Consolas,monospace;white-space:pre}footer{margin-top:1rem;padding:1rem;border:1px solid #e2e8f0;border-radius:12px;background:#f8fafc;line-height:1.6}footer small{margin:.35rem 0 0;color:#64748b}@media(max-width:760px){header{grid-template-columns:1fr}.auth{flex-direction:column}summary{flex-wrap:wrap}summary span{width:100%;margin-left:4.2rem}}
  header h2 { color: #ffffff !important; }
</style>
