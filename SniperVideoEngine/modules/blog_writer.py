"""
BlogWriter — Motor de Geração de Artigos para Blog.
Gera artigos completos e otimizados para SEO usando LLM.

Pipeline:
  1. Geração de ideias baseada em nicho + tendências
  2. Artigo completo (~1500 palavras) com seções, headings, meta
  3. Slug, excerpt, keywords para SEO
  4. Prompt visual para imagem de destaque (Google Flow)
"""
import asyncio
import json
import os
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
BRAND_DIR = BASE_DIR / "brand_config"

# ─── Provedores LLM ───────────────────────────────────────────────────────
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = "meta-llama/llama-3.3-70b-instruct"

NVIDIA_API_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
NVIDIA_MODEL = "meta/llama-3.3-70b-instruct"


def _load_brand_file(name: str) -> str:
    path = BRAND_DIR / name
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def _load_channel_brand(channel_id: str) -> dict:
    """Carrega config de marca do canal específico ou default.
    Prefere versão blog quando disponível."""
    brand = {
        "bible": _load_brand_file("brand_bible.md"),
        "audience": _load_brand_file("target_audience.md"),
        "voice": _load_brand_file("voice_guide.md"),
        "ctas": _load_brand_file("ctas.md"),
    }
    # Tenta carregar versão blog primeiro
    blog_dir = BRAND_DIR / "blog"
    if blog_dir.is_dir():
        for fname in ["brand_bible.md"]:
            fpath = blog_dir / fname
            if fpath.exists():
                brand["bible"] = fpath.read_text(encoding="utf-8")
    # Canal específico
    channel_dir = BRAND_DIR / f"canal_{channel_id}"
    if channel_dir.is_dir():
        for fname in ["brand_bible.md", "target_audience.md", "voice_guide.md", "ctas.md"]:
            fpath = channel_dir / fname
            if fpath.exists():
                brand[fname.replace(".md", "")] = fpath.read_text(encoding="utf-8")
    return brand


async def _call_llm(system_prompt: str, user_prompt: str,
                    temperature: float = 0.8, max_tokens: int = 4096) -> str:
    """
    Chama LLM com fallback em cascata:
    1. OpenRouter (primário — gratuito, vários modelos)
    2. NVIDIA NIM (se chave real disponível)
    3. HuggingFace Inference API (fallback gratuito com token HF)
    4. DeepSeek via API direta
    """
    import httpx
    last_error = None

    def _build_payload(model: str) -> dict:
        return {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

    def _try_extract(data: dict) -> str:
        try:
            return data["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, AttributeError):
            return ""

    # ─── TENTATIVA 1: OpenRouter ────────────────────────────────────────────
    or_key = os.getenv("OPENROUTER_API_KEY", "")
    if or_key:
        # Modelos gratuitos do OpenRouter (tag ) em ordem de qualidade
        or_models = [
            "meta-llama/llama-3.3-70b-instruct",
            "mistralai/mistral-small-24b-instruct-2501",
            "deepseek/deepseek-chat",
            "qwen/qwen-2.5-72b-instruct",
            "google/gemini-2.0-flash-lite-preview-02-05",
        ]
        for model in or_models:
            try:
                headers = {
                    "Authorization": f"Bearer {or_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://dezafira.com.br",
                    "X-Title": "Dezafira Blog Factory",
                }
                payload = _build_payload(model)
                async with httpx.AsyncClient(timeout=300) as client:
                    r = await client.post(OPENROUTER_API_URL, json=payload, headers=headers)
                    if r.status_code == 200:
                        text = _try_extract(r.json())
                        if text:
                            print(f"[LLM] OpenRouter {model}: OK")
                            return text
                    elif r.status_code == 402:
                        # Modelo sem créditos — tenta próximo
                        print(f"[LLM] OpenRouter {model}: sem créditos (402), tentando próximo...")
                        continue
                    else:
                        print(f"[LLM] OpenRouter {model}: {r.status_code}, tentando próximo...")
            except Exception as e:
                last_error = f"OpenRouter {model}: {e}"
                print(f"[LLM] OpenRouter {model} falhou: {e}")
                continue

    # ─── TENTATIVA 2: Google Gemini ───────────────────────────────────────────
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    if gemini_key:
        gemini_models = [
            "gemini-2.0-flash",
            "gemini-1.5-pro",
            "gemini-1.5-flash",
        ]
        for model in gemini_models:
            try:
                gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={gemini_key}"
                gemini_payload = {
                    "system_instruction": {"parts": [{"text": system_prompt}]},
                    "contents": [{"parts": [{"text": user_prompt}]}],
                    "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens},
                }
                async with httpx.AsyncClient(timeout=60) as client:
                    r = await client.post(gemini_url, json=gemini_payload)
                    if r.status_code == 200:
                        data = r.json()
                        candidates = data.get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            if parts:
                                text = parts[0].get("text", "").strip()
                                if text:
                                    print(f"[LLM] Gemini {model}: OK")
                                    return text
                    else:
                        print(f"[LLM] Gemini {model}: {r.status_code}, tentando proximo...")
            except Exception as e:
                last_error = f"Gemini {model}: {e}"
                print(f"[LLM] Gemini {model} falhou: {e}")
                continue

    # ─── TENTATIVA 3: NVIDIA NIM ─────────────────────────────────────────────
    nvidia_key = os.getenv("NVIDIA_API_KEY", "") or os.getenv("NVAPI_KEY", "")
    if nvidia_key and nvidia_key != "mock_key_for_testing":
        try:
            headers = {
                "Authorization": f"Bearer {nvidia_key}",
                "Content-Type": "application/json",
            }
            payload = _build_payload(NVIDIA_MODEL)
            async with httpx.AsyncClient(timeout=180) as client:
                r = await client.post(NVIDIA_API_URL, json=payload, headers=headers)
                r.raise_for_status()
                text = _try_extract(r.json())
                if text:
                    print("[LLM] NVIDIA NIM: OK")
                    return text
        except Exception as e:
            last_error = f"NVIDIA: {e}"
            print(f"[LLM] NVIDIA falhou: {e}")

    # ─── TENTATIVA 4: HuggingFace Inference API ──────────────────────────────
    hf_token = os.getenv("HUGGINGFACE_TOKEN", "")
    if hf_token:
        try:
            hf_headers = {
                "Authorization": f"Bearer {hf_token}",
                "Content-Type": "application/json",
            }
            hf_payload = {
                "inputs": f"{system_prompt}\n\n{user_prompt}",
                "parameters": {
                    "temperature": temperature,
                    "max_new_tokens": min(max_tokens, 4096),
                    "return_full_text": False,
                },
            }
            hf_models = [
                "mistralai/Mixtral-8x7B-Instruct-v0.1",
                "HuggingFaceH4/zephyr-7b-beta",
                "microsoft/Phi-3-mini-4k-instruct",
            ]
            for model in hf_models:
                try:
                    hf_url = f"https://api-inference.huggingface.co/models/{model}"
                    async with httpx.AsyncClient(timeout=120) as client:
                        r = await client.post(hf_url, json=hf_payload, headers=hf_headers)
                        if r.status_code == 200:
                            data = r.json()
                            if isinstance(data, list) and len(data) > 0:
                                text = data[0].get("generated_text", "")
                                if text:
                                    print(f"[LLM] HuggingFace {model}: OK")
                                    return text.strip()
                        elif r.status_code == 503:
                            continue
                except Exception as e:
                    print(f"[LLM] HF {model} falhou: {e}")
                    continue
        except Exception as e:
            last_error = f"HF: {e}"

    # ─── TENTATIVA 5: DeepSeek API ───────────────────────────────────────────
    deepseek_key = os.getenv("DEEPSEEK_API_KEY", "")
    if deepseek_key:
        try:
            ds_headers = {
                "Authorization": f"Bearer {deepseek_key}",
                "Content-Type": "application/json",
            }
            ds_payload = _build_payload("deepseek-chat")
            async with httpx.AsyncClient(timeout=180) as client:
                r = await client.post(
                    "https://api.deepseek.com/v1/chat/completions",
                    json=ds_payload, headers=ds_headers,
                )
                r.raise_for_status()
                text = _try_extract(r.json())
                if text:
                    print("[LLM] DeepSeek: OK")
                    return text
        except Exception as e:
            last_error = f"DeepSeek: {e}"

    error_msg = f"Todos os LLMs falharam. Ultimo erro: {last_error}"
    print(f"[LLM] {error_msg}")
    raise RuntimeError(error_msg)


def _extract_json(text: str) -> dict:
    """Extrai JSON do texto LLM com múltiplas estratégias de fallback."""
    # Limpeza inicial
    text = text.strip()

    # Estratégia 1: Tentar parse direto
    try:
        return json.loads(text)
    except Exception:
        pass

    # Estratégia 2: Extrair de bloco ```json ... ```
    m = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
    if m:
        candidate = m.group(1).strip()
        try:
            return json.loads(candidate)
        except Exception:
            pass

    # Estratégia 3: Encontrar primeiro { e último } — robusto para JSON aninhado
    start = text.find('{')
    end = text.rfind('}')
    if start >= 0 and end > start:
        candidate = text[start:end+1]
        try:
            return json.loads(candidate)
        except Exception as e:
            # Se falhou, tenta corrigir problemas comuns
            pass

    # Estratégia 4: Tentar com replace de quebras de linha no JSON
    if start >= 0 and end > start:
        candidate = text[start:end+1]
        # Remove newlines dentro de strings (raro, mas acontece)
        candidate = re.sub(r'"[^"]*"', lambda m: m.group(0).replace('\n', '\\n'), candidate)
        try:
            return json.loads(candidate)
        except Exception:
            pass

    # Estratégia 5: Fallback — extrair campos individuais via regex
    result = {}
    title_m = re.search(r'"title"\s*:\s*"([^"]+)"', text)
    if title_m:
        result["title"] = title_m.group(1)
    slug_m = re.search(r'"slug"\s*:\s*"([^"]+)"', text)
    if slug_m:
        result["slug"] = slug_m.group(1)
    excerpt_m = re.search(r'"excerpt"\s*:\s*"([^"]+)"', text)
    if excerpt_m:
        result["excerpt"] = excerpt_m.group(1)
    content_m = re.search(r'"content_html"\s*:\s*"([^"]+)"', text)
    if content_m:
        result["content_html"] = content_m.group(1)

    if result:
        # Só aceita parcial se tiver título E conteúdo
        if result.get("title") and result.get("content_html"):
            result["_partial"] = True
            print(f"[BlogWriter] Extracao parcial de JSON: {len(result)} campos")
            return result
        # Se não tem conteúdo, é um erro — melhor que artigo vazio no DB
        return {"error": "Extração parcial sem conteúdo HTML", "raw": text[:500]}

    return {"error": "Falha ao extrair JSON", "raw": text[:500]}


# ═══════════════════════════════════════════════════════════════════════════════
# INSTRUCOES DE ESCRITA POR NICHO
# ═══════════════════════════════════════════════════════════════════════════════

_NICHE_INSTRUCTIONS = {
    "financas": {
        "keywords": ["financ","invest","econom","dinheiro","renda","orcamento","poupanca",
                     "divida","credito","juros","aposentadoria","imposto","bolsa","CDB","Tesouro"],
        "style": [
            "Use dados numericos, estatisticas e exemplos concretos (ex: 'CDI esta em 13,65% aa')",
            "Inclua comparacoes entre opcoes (CDB vs Tesouro, Renda Fixa vs Variavel)",
            "Explique conceitos financeiros de forma simples para leigos",
            "Use regras praticas (ex: 'regra 50/30/20', 'fundo de emergencia de 6 meses')",
            "Cite fontes brasileiras quando possivel (IBGE, BC, ANBIMA, B3)",
            "De passos acaoaveis: 'Passo 1: abrir conta, Passo 2: depositar R$ 100'"
        ],
    },
    "cristao": {
        "keywords": ["jesus","crist","biblic","fe","oracao","evangelho","igreja",
                     "deus","senhor","espirito","santo","graca","salvacao","reino"],
        "style": [
            "Inclua referencias biblicas com livro, capitulo e versiculo (ex: 'Mateus 6:33')",
            "Contextualize o ensinamento biblico para o dia a dia",
            "Use tom pastoral e inspirador, mas sem ser moralista",
            "Facilite a aplicacao pratica da fe na vida cotidiana",
            "Inclua reflexoes que gerem conexao pessoal com o tema",
        ],
    },
    "saude": {
        "keywords": ["saude","bem-estar","aliment","exercicio","doenca","prevencao",
                     "nutricao","suplemento","natural","bem estar"],
        "style": [
            "Cite fontes cientificas e estudos quando possivel",
            "Inclua recomendacoes de especialistas (medicos, nutricionistas)",
            "Deixe claro que nao substitui consulta medica profissional",
            "Use dados de organizacoes de saude (OMS, ANS, MS)",
            "Diferencie mitos de fatos sobre saude",
        ],
    },
    "tecnologia": {
        "keywords": ["tecnolog","app","digital","software","hardware","internet","ia",
                     "inteligencia artificial","programacao","inovacao"],
        "style": [
            "Inclua comparacoes entre ferramentas e tecnologias",
            "Use benchmarks e metricas de performance",
            "Explique conceitos tecnicos de forma acessivel",
            "De exemplos praticos de uso no dia a dia",
            "Mencione tendencias e inovacoes do setor",
        ],
    },
    "casa": {
        "keywords": ["casa","decoracao","organizacao","limpeza","jardinagem","DIY","faça voce","reforma"],
        "style": [
            "Inclua dicas praticas e passo a passo",
            "Use comparacoes de custo-beneficio",
            "Sugira materiais e ferramentas acessiveis",
            "Diferencie opcoes para diferentes orcamentos",
            "Inclua fotos/videos ilustrativos quando possivel",
        ],
    },
}

_DEFAULT_INSTRUCTIONS = [
    "Escreva de forma clara, direta e envolvente",
    "Use exemplos praticos que o leitor possa aplicar",
    "Estruture o texto com paragrafos curtos e subtitulos",
    "Mantenha tom adequado ao tema (informativo, inspirador ou educacional)",
]


def _detect_niche(topic: str, keywords: str = "") -> str:
    """Detecta o nicho com base no topico e keywords."""
    text = (topic + " " + keywords).lower()
    scores = {}
    for niche, config in _NICHE_INSTRUCTIONS.items():
        score = sum(1 for kw in config["keywords"] if kw in text)
        if score > 0:
            scores[niche] = score
    if not scores:
        return "default"
    return max(scores, key=scores.get)


def _get_niche_instructions(topic: str, keywords: str = "") -> str:
    """Retorna instrucoes de escrita especificas para o nicho detectado."""
    niche = _detect_niche(topic, keywords)
    if niche == "default":
        return "\n".join(f"- {inst}" for inst in _DEFAULT_INSTRUCTIONS)
    config = _NICHE_INSTRUCTIONS[niche]
    instructions = [f"- {inst}" for inst in config["style"]]
    return "\n".join(instructions)


def _slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text[:100]


async def generate_ideas(nicho: str, count: int = 5, language: str = "pt") -> list:
    """Gera ideias de posts para um nicho."""
    system_prompt = (
        f"Você é um estrategista de conteúdo SEO. Gere {count} ideias de posts "
        f"para blogs no nicho: {nicho}. "
        "Cada ideia deve incluir: título gancho, palavra-chave principal, "
        "e uma breve descrição do que o post abordará. "
        "Retorne APENAS JSON array: [{\"title\": \"...\", \"keyword\": \"...\", \"description\": \"...\"}]"
    )
    user_prompt = f"Gere {count} ideias de posts para blog sobre {nicho} em {language}."
    raw = await _call_llm(system_prompt, user_prompt, temperature=0.9, max_tokens=2048)

    try:
        ideas = json.loads(raw) if raw.startswith("[") else json.loads(re.search(r'\[.*\]', raw, re.DOTALL).group())
        return ideas[:count]
    except Exception:
        return [{"title": nicho, "keyword": nicho, "description": f"Artigo sobre {nicho}"}]


async def generate_full_article(
    topic: str,
    channel_id: str = "default",
    language: str = "pt",
    target_words: int = 1000,
    keywords: str = "",
) -> dict:
    """
    Gera artigo completo usando múltiplas chamadas LLM (multipart).
    Cada seção é uma chamada separada para profundidade máxima.

    Returns:
        dict com title, slug, content (HTML), excerpt, keywords
    """
    return await generate_multipart_article(
        topic=topic,
        channel_id=channel_id,
        language=language,
        target_words=target_words,
        keywords=keywords,
    )


async def generate_multipart_article(
    topic: str,
    channel_id: str = "default",
    language: str = "pt",
    target_words: int = 1000,
    keywords: str = "",
) -> dict:
    """
    Gera artigo em múltiplas chamadas LLM — cada seção é escrita separadamente
    para garantir profundidade e qualidade. Depois tudo é compilado.

    Etapas:
      1. Planejamento: outline com título, seções, keywords
      2. Introdução: gancho forte + contexto
      3. Seções (3-4): cada uma em chamada LLM separada
      4. Conclusão: reflexão + CTA
      5. Compilação: tudo concatenado + metadados

    Returns:
        dict com title, slug, content_html, excerpt, keywords, word_count
    """
    print(f"[BlogWriter] Iniciando geracao multiparte: {topic}")
    print(f"[BlogWriter] Alvo: ~{target_words} palavras em 4-5 chamadas LLM")

    # ─── ETAPA 1: PLANEJAMENTO ──────────────────────────────────────
    print("[BlogWriter] Etapa 1/5: Planejando estrutura do artigo...")
    outline_system = f"""Você é um editor-chefe e estrategista de conteúdo.

Crie um PLANO DETALHADO para um artigo sobre "{topic}".

Diretrizes:
- Idioma: {language}
- Keywords: {keywords if keywords else topic}
- O artigo terá ~{min(target_words, 1300)} palavras no total (MAXIMO 1500)
- NAO repita a mesma frase, paragrafo ou ideia mais de uma vez no artigo
- LIMITE o artigo completo a 1100-1500 palavras (NUNCA ultrapasse 1500)
- VARIE a estrutura das frases e evite padroes repetitivos
- NAO use o mesmo paragrafo introdutorio mais de uma vez
- NAO inclua marcadores de chat como 'assistant:' ou 'user:'
- EVITE verbosidade: cada paragrafo deve adicionar informacao nova
- SE sentir que esta repetindo algo, PARE e mude de topico

Retorne APENAS JSON:
{{
  "title": "Título SEO irresistível (max 65 chars)",
  "slug": "url-friendly-slug",
  "meta_description": "Meta descrição persuasiva (max 160 chars)",
  "keywords": "keyword1, keyword2, keyword3",
  "excerpt": "Resumo para home page (max 200 chars)",
  "sections": [
    {{
      "h2": "Título da Seção 1",
      "description": "O que esta seção vai cobrir",
      "target_words": {max(200, target_words // 4)}
    }},
    {{
      "h2": "Título da Seção 2",
      "description": "O que esta seção vai cobrir",
      "target_words": {max(200, target_words // 4)}
    }}
  ]
}}

Gera de 3 a 5 seções dependendo da profundidade necessária."""

    outline_prompt = f"Crie o plano para um artigo sobre: {topic}. Keywords: {keywords if keywords else topic}"

    print("[BlogWriter] Chamada LLM #1: Planejamento...")
    raw_outline = await _call_llm(outline_system, outline_prompt, temperature=0.7, max_tokens=2048)
    outline = _extract_json(raw_outline)

    if "error" in outline:
        print(f"[BlogWriter] Falha no planejamento: {outline['error']}")
        print("[BlogWriter] Usando fallback: estrutura padrão")
        outline = {
            "title": topic[:65],
            "slug": _slugify(topic),
            "meta_description": f"Artigo completo sobre {topic}",
            "keywords": keywords or topic,
            "excerpt": f"Artigo completo sobre {topic}",
            "sections": [
                {"h2": f"O que é {topic}", "description": f"Introdução ao tema {topic}", "target_words": 600},
                {"h2": f"A importância de {topic}", "description": f"Por que {topic} é relevante", "target_words": 600},
                {"h2": f"Como aplicar {topic}", "description": f"Aplicações práticas de {topic}", "target_words": 600},
            ]
        }

    print(f"[BlogWriter] Plano: {outline.get('title')} — {len(outline.get('sections', []))} secoes")

    # ─── ETAPA 2: INTRODUÇÃO ────────────────────────────────────────
    print("[BlogWriter] Etapa 2/5: Escrevendo introdução...")
    niche_instructions = _get_niche_instructions(topic, keywords)
    intro_system = f"""Você é um redator SEO especialista.

Escreva uma INTRODUÇÃO IMPACTANTE sobre:
"{topic}"

Diretrizes:
- Idioma: {language}
- Gancho forte: pergunta provocativa, afirmação ousada ou história curta
- Contextualize o tema e mostre por que o leitor deve continuar lendo
- ~200-300 palavras (seja conciso)
- Use <h2>Introdução</h2> seguido de parágrafos <p>
- Retorne APENAS o HTML da introdução (sem JSON)
- NAO repita a mesma ideia em paragrafos diferentes
- Instrucoes especificas do nicho:
{niche_instructions}"""

    print("[BlogWriter] Chamada LLM #2: Introdução...")
    intro_html = await _call_llm(intro_system, f"Escreva a introdução sobre {topic}", temperature=0.75, max_tokens=4096)
    # Limpa possíveis ```html ou ``` markers (abertura E fechamento)
    intro_html = re.sub(r'```(?:html)?\s*|\s*```', '', intro_html).strip()
    # Garante que está dentro de <h2>Introdução</h2>
    if not re.match(r'<\s*h2[\s>]', intro_html, re.IGNORECASE):
        intro_html = f"<h2>Introdução</h2>\n{intro_html}"
    print(f"[BlogWriter] Introdução gerada: {len(intro_html)} chars")

    # ─── ETAPA 3: SEÇÕES ───────────────────────────────────────────
    sections_html = []
    sections = outline.get("sections", [])
    section_target = max(200, target_words // max(len(sections), 3))

    for i, sec in enumerate(sections):
        sec_title = sec.get("h2", f"Seção {i+1}")
        sec_desc = sec.get("description", f"Continuação sobre {topic}")
        sec_target = sec.get("target_words", section_target)

        print(f"[BlogWriter] Etapa 3/5: Seção {i+1}/{len(sections)}: '{sec_title}'...")

        sec_system = f"""Você é um redator SEO especialista.

Escreva a seção "{sec_title}" para um artigo sobre "{topic}".

Diretrizes:
- Idioma: {language}
- Contexto da seção: {sec_desc}
- ~{min(sec_target, 350)} palavras (seja conciso, maximo 350)
- Aprox. 3-5 parágrafos informativos (profundidade > quantidade)
- Inclua dados, exemplos praticos e contexto do nicho
- Mantenha tom adequado ao tema
- NAO repita informacao ja dita em secoes anteriores
- Instrucoes especificas do nicho:
{_get_niche_instructions(topic, keywords)}
- Use <h2>{sec_title}</h2> no início
- Use <h3> para subseções se necessário
- Retorne APENAS o HTML da seção (sem JSON, sem markdown)"""

        print(f"[BlogWriter] Chamada LLM #{3+i}: Seção {i+1} '{sec_title}'...")
        try:
            sec_html = await _call_llm(sec_system, f"Escreva a seção '{sec_title}' sobre {topic}", temperature=0.75, max_tokens=4096)
        except Exception as e:
            print(f"[BlogWriter] ERRO na seção {i+1}: {e}. Usando fallback.")
            sec_html = f"<p>_Conteúdo em desenvolvimento_</p>"
        sec_html = re.sub(r'```(?:html)?\s*|\s*```', '', sec_html).strip()

        if not re.match(r'<\s*h2[\s>]', sec_html, re.IGNORECASE):
            sec_html = f"<h2>{sec_title}</h2>\n{sec_html}"

        sections_html.append(sec_html)
        print(f"[BlogWriter] Seção {i+1} gerada: {len(sec_html)} chars")

    # ─── ETAPA 4: CONCLUSÃO ─────────────────────────────────────────
    print("[BlogWriter] Etapa 4/5: Escrevendo conclusão...")
    conc_system = f"""Você é um redator SEO especialista.

Escreva uma CONCLUSÃO PODEROSA para um artigo sobre "{topic}".

Diretrizes:
- Idioma: {language}
- Resuma os pontos principais SEM REPETIR o que ja foi dito
- Reflexão final que gere engajamento
- CTA natural (convide o leitor a agir)
- ~150-250 palavras (seja direto)
- Use <h2>Conclusão</h2> no início
- Retorne APENAS o HTML (sem JSON, sem markdown)
- NAO repita a introducao ou as secoes
- Instrucoes especificas do nicho:
{_get_niche_instructions(topic, keywords)}"""

    print("[BlogWriter] Chamada LLM #{4+len(sections)}: Conclusão...")
    try:
        conc_html = await _call_llm(conc_system, f"Escreva a conclusão sobre {topic}", temperature=0.75, max_tokens=2048)
    except Exception as e:
        print(f"[BlogWriter] ERRO na conclusão: {e}. Usando fallback.")
        conc_html = "<p>_Conclusão em desenvolvimento_</p>"
    conc_html = re.sub(r'```(?:html)?\s*|\s*```', '', conc_html).strip()
    if not re.match(r'<\s*h2[\s>]', conc_html, re.IGNORECASE):
        conc_html = f"<h2>Conclusão</h2>\n{conc_html}"
    print(f"[BlogWriter] Conclusão gerada: {len(conc_html)} chars")

    # ─── ETAPA 5: COMPILAÇÃO ───────────────────────────────────────
    print("[BlogWriter] Etapa 5/5: Compilando artigo final...")

    # Montar content_html completo
    all_parts = [intro_html] + sections_html + [conc_html]
    full_content_html = "\n\n".join(all_parts)

    # Estimar word count (stripping HTML tags first)
    text_only = re.sub(r'<[^>]+>', '', full_content_html)
    estimated_words = len(text_only.split())

    # --- TRUNCAMENTO: limitar a target_words + 200 maximo ---
    max_allowed = max(target_words + 200, 1500)
    if estimated_words > max_allowed and len(all_parts) > 2:
        print(f'[BlogWriter] Artigo tem {estimated_words} palavras, truncando para ~{max_allowed}...')
        words_so_far = 0
        truncated = []
        for part in all_parts:
            part_text = re.sub(r'<[^>]+>', '', part)
            part_words = len(part_text.split())
            if words_so_far + part_words > max_allowed and len(truncated) >= 2:
                break
            truncated.append(part)
            words_so_far += part_words
        full_content_html = "\n\n".join(truncated)
        text_only = re.sub(r'<[^>]+>', '', full_content_html)
        estimated_words = len(text_only.split())
        print(f'[BlogWriter] Artigo truncado para ~{estimated_words} palavras')

    print(f"[BlogWriter] Artigo compilado: ~{estimated_words} palavras")
    print(f"[BlogWriter] Chamadas LLM totais: {2 + len(sections) + 1} (planejamento + introducao + {len(sections)} secoes + conclusao)")

    # Extrair excerpt do outline ou gerar
    excerpt = outline.get("excerpt", "") or f"Artigo completo sobre {topic}"

    result = {
        "title": outline.get("title", topic)[:65],
        "slug": outline.get("slug", _slugify(topic)),
        "meta_description": outline.get("meta_description", excerpt)[:160],
        "keywords": outline.get("keywords", keywords or topic),
        "content_html": full_content_html,
        "excerpt": excerpt[:200],
        "word_count": estimated_words,
        "topic": topic,
        "channel_id": channel_id,
        "language": language,
    }

    return result


async def write(topic: str, channel_id: str = "default", language: str = "pt",
                target_words: int = 1000, keywords: str = "") -> dict:
    """Interface principal — gera e salva o artigo no banco."""
    from .database import create_db_blog_post

    article = await generate_full_article(
        topic=topic,
        channel_id=channel_id,
        language=language,
        target_words=target_words,
        keywords=keywords,
    )

    if "error" in article:
        return {"success": False, "error": article["error"]}

    saved = create_db_blog_post(
        channel_id=channel_id,
        title=article["title"],
        slug=article["slug"],
        content=article.get("content_html", ""),
        excerpt=article.get("excerpt", ""),
        keywords=article.get("keywords", keywords),
        topic=topic,
    )

    return {
        "success": True,
        "post_id": saved["id"],
        "title": article["title"],
        "slug": article["slug"],
        "word_count": article.get("word_count", 0),
        "featured_image_prompt": article.get("featured_image_prompt", ""),
        "article": article,
    }