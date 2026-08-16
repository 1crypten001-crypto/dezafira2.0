export const LANDING_BLOCK_CONTRACTS = {
  hero: {
    purpose: 'Primeira dobra de alto impacto com CTAs e imagem opcional.',
    properties: {
      eyebrow: 'string', title: 'string', subtitle: 'string', subtitleColor: 'CSS color opcional',
      primaryText: 'string', primaryHref: 'URL relativa ou HTTPS', secondaryText: 'string opcional',
      secondaryHref: 'URL relativa ou HTTPS', image: 'URL HTTPS opcional', imageAlt: 'string opcional'
    }
  },
  'product-showcase': {
    purpose: 'Oferta ligada a um produto real ou preenchida manualmente.',
    properties: {
      productId: 'number|null', productSlug: 'string|null', eyebrow: 'string', name: 'string',
      description: 'string', price: 'string formatada', image: 'URL HTTPS', imageAlt: 'string',
      bullets: 'string[] opcional', buttonText: 'string', buttonHref: '/product/slug ou URL HTTPS'
    }
  },
  'posts-grid': {
    purpose: 'Grade editorial com até seis posts publicados.',
    properties: {
      title: 'string', subtitle: 'string',
      posts: 'Array<{id,title,slug,excerpt,cover_image,href}> com no máximo 6 itens'
    }
  },
  'trust-bar': {
    purpose: 'Linha curta de garantias, benefícios ou sinais de confiança.',
    properties: { items: 'string[] com até 8 itens' }
  },
  cta: {
    purpose: 'Chamada para ação destacada.',
    properties: { subtitle: 'string', buttonText: 'string', buttonHref: 'URL', buttonBg: 'CSS color', buttonColor: 'CSS color' }
  },
  testimonial: {
    purpose: 'Prova social individual.',
    properties: { quote: 'string', author: 'string', role: 'string', avatar: 'URL HTTPS opcional', rating: 'number 1..5' }
  },
  pricing: {
    purpose: 'Plano ou oferta com lista de benefícios.',
    properties: { name: 'string', price: 'string', period: 'string', features: 'string[]', buttonText: 'string', buttonHref: 'URL', featured: 'boolean' }
  },
  faq: {
    purpose: 'Perguntas frequentes.',
    properties: { title: 'string', items: 'Array<{q:string,a:string}>' }
  },
  html: {
    purpose: 'Layout totalmente personalizado em HTML seguro com CSS inline.',
    content: 'HTML string. Use <a> para CTAs; <button>, <script>, <style>, iframe, forms e event handlers são removidos.'
  },
  text: { purpose: 'Texto rico seguro.', content: 'HTML com headings, parágrafos, listas, links e imagens.' },
  image: { purpose: 'Imagem responsiva.', properties: { src: 'URL HTTPS ou caminho relativo', alt: 'string' } },
  button: { purpose: 'CTA simples.', content: 'Texto', properties: { href: 'URL relativa ou HTTPS' } },
  video: { purpose: 'Vídeo YouTube.', properties: { src: 'URL do YouTube' } },
  section: { purpose: 'Seção de largura total.', children: 'Block[]' },
  container: { purpose: 'Agrupador vertical.', children: 'Block[]' },
  columns: { purpose: 'Estrutura de 2 ou 3 colunas.', properties: { cols: '2|3', gap: 'CSS length' }, children: 'Somente blocos column' },
  column: { purpose: 'Coluna que recebe blocos.', children: 'Block[]' },
  divider: { purpose: 'Separador visual.' },
  spacer: { purpose: 'Espaçamento vertical.' }
} as const;

export const LANDING_AGENT_PROMPT = `Crie uma landing page premium via CLI para este projeto.

1. Consulte GET /api/cli/landing-pages/schema para aprender o contrato atualizado.
2. Consulte GET /api/cli/landing-pages/resources para obter produtos e posts reais.
3. Planeje a narrativa: hero, problema/benefícios, oferta, prova social, conteúdo relacionado, FAQ e CTA final.
4. Gere um JSON com title, slug, status="draft", settings e blocks.
5. Use IDs únicos em todos os blocos. Nunca coloque blocos diretamente em columns.children: crie column e coloque o conteúdo dentro dela.
6. Prefira os blocos estruturados. Para um design totalmente original, use um bloco html com HTML semântico e estilos inline.
7. Não use script, style, iframe, form, input, button, onclick ou URLs javascript:. Para CTA em HTML, use <a href="...">.
8. Garanta contraste, responsividade, espaçamento consistente, imagens com alt e CTAs claros.
9. Crie em draft via POST /api/cli/landing-pages e informe edit_url e public_url retornadas.

Autentique todas as requisições com Authorization: Bearer SEU_TOKEN.`;

export const LANDING_CLI_MANIFEST = {
  version: 1,
  basePath: '/api/cli/landing-pages',
  authentication: 'Authorization: Bearer SEU_TOKEN',
  workflow: [
    'GET /api/cli/landing-pages/schema',
    'GET /api/cli/landing-pages/resources',
    'POST /api/cli/landing-pages com status draft',
    'GET /api/cli/landing-pages/:id para revisar',
    'PUT /api/cli/landing-pages/:id para editar ou publicar'
  ],
  page: {
    required: ['title', 'blocks'],
    optional: ['slug', 'status', 'settings'],
    status: ['draft', 'published'],
    limits: { maxBlocks: 250, maxDepth: 8 }
  },
  blockShape: {
    required: ['id', 'type'],
    optional: ['content', 'styles', 'properties', 'children'],
    styles: 'Record<string,string> com valores CSS inline'
  },
  designRules: [
    'Use uma seção visual principal por objetivo.',
    'Mantenha contraste AA e hierarquia tipográfica clara.',
    'Use no máximo dois CTAs concorrentes por seção.',
    'Use imagens reais retornadas por resources ou URLs HTTPS.',
    'Crie primeiro como draft para revisão visual.'
  ],
  blocks: LANDING_BLOCK_CONTRACTS,
  agentPrompt: LANDING_AGENT_PROMPT
};
