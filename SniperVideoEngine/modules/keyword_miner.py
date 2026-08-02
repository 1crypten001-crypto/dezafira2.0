"""
KeywordMiner — Motor de Descoberta de Palavras-Chave para SEO.

Funcionalidades:
  1. Google Autocomplete Scraper (gratuito, sem API key)
  2. Expansão por prefixos/sufixos (long-tail)
  3. People Also Ask (PAA) scraper — perguntas naturais
  4. SERP Difficulty Analyzer — detecta concorrência fraca
  5. Clustering de keywords por tema
  6. Pipeline: Keywords → BlogWriter (gera artigos otimizados)

Baseado nos repositórios open-source:
  - github.com/sundios/Keyword-generator-SEO
  - github.com/hassancs91/Keyword-Research-tool-python

Uso:
    miner = KeywordMiner()
    keywords = await miner.mine("emagrecimento")
    easy = await miner.find_easy_keywords("receitas saudaveis")
"""

import asyncio
import json
import random
import re
from typing import Optional
from urllib.parse import quote


# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTES
# ═══════════════════════════════════════════════════════════════════════════════

GOOGLE_SUGGEST_URL = "https://suggestqueries.google.com/complete/search?output=firefox&q={query}"
GOOGLE_SEARCH_URL = "https://www.google.com/search?q={query}&hl={lang}"
# Autocomplete ESPECIFICO do YouTube (ds=yt) — retorna buscas REAIS que os
# usuarios digitam no YouTube (sem API key). Cada sugestao e uma dor declarada.
YOUTUBE_SUGGEST_URL = "https://suggestqueries.google.com/complete/search?client=youtube&ds=yt&hl={hl}&q={query}"

# Prefixos para expansão de keywords (cauda longa)
PREFIXES = [
    'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
    'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
    'como', 'o que', 'por que', 'quando', 'onde', 'qual', 'quais',
    'melhor', 'melhores', 'top', 'quanto', 'quanto custa',
    'how', 'what', 'why', 'when', 'where', 'which', 'best',
]

# Prefixos/sufixos FOCADOS EM PERGUNTAS para minerar dores no YouTube.
# Subconjunto enxuto (evita ~80 req do PREFIXES/SUFFIXES completos -> rate-limit).
YOUTUBE_PAIN_PREFIXES = [
    'como', 'o que', 'por que', 'quando', 'onde', 'qual', 'quais',
    'melhor', 'melhores', 'quanto', 'quanto custa', 'vale a pena',
    'duvida', 'erro', 'problema', 'ajuda',
]
YOUTUBE_PAIN_SUFFIXES = [
    'para iniciantes', 'como fazer', 'o que e', 'vale a pena', 'dicas',
    'melhor', 'review', 'vs', 'erros', 'problemas', 'ajuda', 'passo a passo',
]

# Sufixos para expansão
SUFFIXES = [
    'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
    'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
    'como fazer', 'o que e', 'dicas', 'para iniciantes',
    'vs', 'versus', 'para', 'sem', 'com', 'preco', 'barato',
    'online', 'perto de mim', 'avaliacao', 'review',
    'how to', 'what is', 'tips', 'for beginners', 'vs', 'review',
    'near me', 'price', 'cheap', 'online', 'best',
]

# User agents para evitar bloqueio
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
]

# Obscura Bridge (opcional, para SERP analysis robusra)
_obscura_bridge = None


def _get_obscura_bridge():
    """Retorna ObscuraBridge se disponível."""
    global _obscura_bridge
    if _obscura_bridge is not None:
        return _obscura_bridge
    try:
        from services.obscura_bridge import get_serp_with_fallback as _obs_fallback
        _obscura_bridge = _obs_fallback
        return _obscura_bridge
    except ImportError:
        _obscura_bridge = False
        return None


# Domínios de "concorrência fraca" — se rankearem, a keyword é fácil
WEAK_DOMAIN_PATTERNS = [
    'reddit.com', 'quora.com', 'forum.', 'fórum', 'answers.',
    'br.answers.', 'yahoo.com', 'pt.wikipedia.org', 'wikihow.com',
    'medium.com', 'blogspot.com', 'wordpress.com', 'tumblr.com',
    'dev.to', 'linkedin.com/pulse', 'hubpages.com', 'ehow.com',
    'scielo.br', 'artigonal.com', 'webartigos.com',
]

# Domínios de "concorrência forte" — se rankearem, a keyword é difícil
STRONG_DOMAIN_PATTERNS = [
    'amazon.com', 'mercadolivre.com', 'magazineluiza.com',
    'americanas.com', 'shopee.com', 'aliexpress.com',
    'youtube.com', 'instagram.com', 'facebook.com',
    'globo.com', 'uol.com.br', 'terra.com.br',
    'abril.com.br', 'exame.com', 'infomoney.com',
]

def _is_relevant_keyword(seed: str, kw: str) -> bool:
    """Retorna True se a keyword é relevante ao seed (contém OU overlap significativo)."""
    kw_lower = kw.lower()
    if seed in kw_lower:
        return True
    seed_words = set(seed.split())
    kw_words = set(kw_lower.split())
    overlap = len(seed_words & kw_words)
    return overlap >= max(1, len(seed_words) // 2)


# Países para busca (gl parameter)
COUNTRIES = {
    "br": "brazil",
    "pt": "portugal",
    "us": "usa",
    "uk": "united kingdom",
}


# ═══════════════════════════════════════════════════════════════════════════════
# KEYWORD RESULT
# ═══════════════════════════════════════════════════════════════════════════════

class KeywordResult:
    """Resultado de uma palavra-chave minerada com metadados."""

    def __init__(self, keyword: str, source: str = "autocomplete",
                 volume_estimate: int = 0, difficulty: int = 50,
                 has_questions: bool = False, questions: list = None,
                 difficulty_label: str = "medium",
                 search_url: str = ""):
        self.keyword = keyword
        self.source = source
        self.volume_estimate = volume_estimate  # 0-100 (estimativa relativa)
        self.difficulty = difficulty             # 0-100 (0=fácil, 100=difícil)
        self.has_questions = has_questions
        self.questions = questions or []
        self.difficulty_label = difficulty_label  # easy, medium, hard
        self.search_url = search_url

    def to_dict(self) -> dict:
        return {
            "keyword": self.keyword,
            "source": self.source,
            "volume_estimate": self.volume_estimate,
            "difficulty": self.difficulty,
            "difficulty_label": self.difficulty_label,
            "has_questions": self.has_questions,
            "questions": self.questions[:5],
            "search_url": self.search_url,
        }

    def __repr__(self):
        return f"<KeywordResult '{self.keyword}' [{self.difficulty_label}]>"


# ═══════════════════════════════════════════════════════════════════════════════
# KEYWORD MINER
# ═══════════════════════════════════════════════════════════════════════════════

class KeywordMiner:
    """Minerador de palavras-chave via Google Autocomplete + SERP Analysis."""

    def __init__(self, use_obscura: bool = True):
        self._session = None
        self._http_client = None
        self.use_obscura = use_obscura and (_get_obscura_bridge() is not None)
        if use_obscura and self.use_obscura:
            print("[KeywordMiner] Obscura Bridge disponivel — SERP analysis robusta ativada!")
        elif use_obscura:
            print("[KeywordMiner] Obscura nao disponivel — usando fallback regex para SERP.")
        else:
            print("[KeywordMiner] Obscura desabilitado — usando metodo regex.")

    @property
    def obscura_disponivel(self) -> bool:
        return self.use_obscura

    async def _get_http(self):
        """Retorna cliente HTTP (lazy load)."""
        if self._http_client is None:
            import httpx
            self._http_client = httpx.AsyncClient(
                timeout=15,
                follow_redirects=True,
                headers={"User-Agent": random.choice(USER_AGENTS)},
            )
        return self._http_client

    async def close(self):
        """Fecha o cliente HTTP."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

    # ─── GOOGLE AUTOCOMPLETE ────────────────────────────────────────────────

    async def _fetch_suggestions(self, query: str, lang: str = "pt") -> list:
        """
        Busca sugestões do Google Autocomplete para uma query.
        Retorna lista de strings.
        """
        url = GOOGLE_SUGGEST_URL.format(query=quote(query))
        if lang == "pt":
            url += "&gl=br&hl=pt-BR"
        elif lang == "en":
            url += "&gl=us&hl=en"

        try:
            client = await self._get_http()
            response = await client.get(url)
            response.raise_for_status()

            # O endpoint retorna XML (output=firefox) ou JSON
            text = response.text

            # Tenta parsear como JSON
            try:
                data = json.loads(text)
                if isinstance(data, list) and len(data) > 1:
                    suggestions = []
                    for item in data[1]:
                        if isinstance(item, list) and len(item) > 0:
                            suggestions.append(str(item[0]))
                        elif isinstance(item, str):
                            suggestions.append(item)
                    return suggestions
            except (json.JSONDecodeError, IndexError):
                pass

            # Fallback: parse XML
            import xml.etree.ElementTree as ET
            root = ET.fromstring(text)
            suggestions = []
            for complete_suggestion in root.findall(".//CompleteSuggestion"):
                suggestion = complete_suggestion.find("suggestion")
                if suggestion is not None:
                    data_text = suggestion.get("data", "")
                    if data_text:
                        suggestions.append(data_text)
            return suggestions

        except Exception as e:
            print(f"[KeywordMiner] Erro ao buscar sugestões para '{query}': {e}")
            return []

    # ─── YOUTUBE AUTOCOMPLETE (ds=yt) ──────────────────────────────────────

    async def fetch_youtube_suggestions(self, query: str, lang: str = "pt") -> list:
        """
        Busca sugestões do autocomplete ESPECIFICO do YouTube (ds=yt).

        Diferente do Google web, essas sugestões refletem exatamente o que
        os usuários digitam na busca do YouTube — a dor já vem declarada
        na própria busca (ex: "como sair das dívidas", "investimento vale a pena").
        """
        hl = "pt-BR" if lang == "pt" else "en"
        url = YOUTUBE_SUGGEST_URL.format(hl=hl, query=quote(query))

        try:
            client = await self._get_http()
            response = await client.get(url, headers={"Accept-Language": hl})
            response.raise_for_status()

            text = response.text.strip()
            # O endpoint ds=yt devolve JSONP (window.google.ac.h(<json>))
            # quando chamado sem contexto de navegador — extrai o JSON puro.
            if text.startswith("window.google.ac.h"):
                start = text.find("(")
                end = text.rfind(")")
                if start != -1 and end > start:
                    text = text[start + 1:end]

            data = json.loads(text)
            if isinstance(data, list) and len(data) > 1:
                suggestions = []
                for item in data[1]:
                    if isinstance(item, list) and len(item) > 0:
                        suggestions.append(str(item[0]))
                return suggestions

        except Exception as e:
            print(f"[KeywordMiner] Erro ao buscar sugestões YouTube para '{query}': {e}")
            return []

    # ─── EXPANSÃO POR PREFIXOS ──────────────────────────────────────────────

    async def expand_by_prefixes(self, keyword: str, lang: str = "pt") -> list:
        """
        Expande keyword testando prefixos (a, b, c..., como, o que, melhor...).
        Ex: "receita" → "a receita", "b receita", "como receita", "melhor receita"
        """
        all_keywords = set()
        all_keywords.add(keyword.lower().strip())

        for prefix in PREFIXES:
            expanded_query = f"{prefix} {keyword}"
            suggestions = await self._fetch_suggestions(expanded_query, lang)
            for suggestion in suggestions:
                all_keywords.add(suggestion.lower().strip())
            await asyncio.sleep(0.3)  # Delay para não tomar block

        return list(all_keywords)

    # ─── EXPANSÃO POR SUFIXOS ───────────────────────────────────────────────

    async def expand_by_suffixes(self, keyword: str, lang: str = "pt") -> list:
        """
        Expande keyword testando sufixos (keyword + sufixo).
        Ex: "receita" → "receita a", "receita b", "receita como fazer"
        """
        all_keywords = set()
        all_keywords.add(keyword.lower().strip())

        for suffix in SUFFIXES:
            expanded_query = f"{keyword} {suffix}"
            suggestions = await self._fetch_suggestions(expanded_query, lang)
            for suggestion in suggestions:
                all_keywords.add(suggestion.lower().strip())
            await asyncio.sleep(0.3)

        return list(all_keywords)

    # ─── MINERAÇÃO DE DORES NO YOUTUBE ─────────────────────────────────────

    async def mine_youtube_pains(self, seed_keyword: str, lang: str = "pt",
                                 max_pains: int = 30) -> list:
        """
        Descobre DORES REAIS a partir das BUSCAS que as pessoas fazem no YouTube.

        Expande o seed por prefixos/sufixos no autocomplete do YouTube (ds=yt)
        e coleta as sugestões — cada uma é uma busca real de um usuário,
        ou seja, uma dor/pedido declarado ("como", "por que", "melhor", "vale a pena").

        Returns:
            Lista de dicts: [{"text", "source": "youtube_search", "url", "views_evidence"}]
        """
        seed = seed_keyword.lower().strip()
        print(f"[KeywordMiner] Minerando dores no YouTube para: '{seed}'")

        queries = set()
        queries.add(seed)

        # Expansão por prefixos focados em perguntas (como, por que, melhor...)
        for prefix in YOUTUBE_PAIN_PREFIXES:
            expanded_query = f"{prefix} {seed}"
            suggestions = await self.fetch_youtube_suggestions(expanded_query, lang)
            for s in suggestions:
                queries.add(s.lower().strip())
            await asyncio.sleep(0.2)  # Delay para não tomar block

        # Expansão por sufixos (para iniciantes, vale a pena, vs...)
        for suffix in YOUTUBE_PAIN_SUFFIXES:
            expanded_query = f"{seed} {suffix}"
            suggestions = await self.fetch_youtube_suggestions(expanded_query, lang)
            for s in suggestions:
                queries.add(s.lower().strip())
            await asyncio.sleep(0.2)

        # Filtra: só relevantes (contém o seed OU overlap significativo)
        relevant = [q for q in queries if _is_relevant_keyword(seed, q) and len(q) > 5]

        pains = [{
            "text": q,
            "source": "youtube_search",
            "url": f"https://www.youtube.com/results?search_query={quote(q)}",
            "views_evidence": "",  # preenchido na validacao de demanda
        } for q in relevant[:max_pains]]

        print(f"[KeywordMiner] {len(pains)} dores reais encontradas no YouTube")
        return pains

    # ─── PEOPLE ALSO ASK (PAA) ──────────────────────────────────────────────

    async def fetch_people_also_ask(self, keyword: str, lang: str = "pt") -> list:
        """
        Busca perguntas do "People Also Ask" do Google.
        Tenta Obscura primeiro (se disponivel), fallback para regex.
        """

        # Tenta Obscura primeiro
        if self.use_obscura:
            try:
                obs = _get_obscura_bridge()
                if obs:
                    data = await obs(keyword, lang)
                    if data.get("source") == "obscura" and data.get("people_also_ask"):
                        return data["people_also_ask"][:10]
            except Exception as e:
                print(f"[KeywordMiner] Obscura PAA falhou, fallback regex: {e}")

        # Fallback: regex
        search_url = GOOGLE_SEARCH_URL.format(
            query=quote(keyword),
            lang="pt-BR" if lang == "pt" else "en",
        )

        try:
            client = await self._get_http()
            response = await client.get(
                search_url,
                headers={
                    "User-Agent": random.choice(USER_AGENTS),
                    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8" if lang == "pt" else "en-US,en;q=0.9",
                },
            )
            text = response.text

            questions = []

            # Padrão 1: data-q="pergunta"
            matches = re.findall(r'data-q="([^"]+)"', text)
            questions.extend(matches)

            # Padrão 2: data-hveid + texto de pergunta
            matches = re.findall(r'class="[^"]*related-question-pair[^"]*"[^>]*>\s*<span[^>]*>([^<]+)</span>', text, re.DOTALL)
            questions.extend(matches)

            # Padrão 3: aria-label + texto de pergunta
            matches = re.findall(r'jsname="[^"]*"[^>]*aria-label="([^"]+)"', text)
            questions.extend(matches)

            # Padrão 4: Qualquer span com role="heading" dentro de div de pergunta
            matches = re.findall(r'<span[^>]*role="heading"[^>]*aria-level="[23]"[^>]*>([^<]+)</span>', text)
            questions.extend(matches)

            # Padrão 5: blocos de PAA com texto de pergunta
            matches = re.findall(r'<div[^>]*jsname="[^"]*"[^>]*jscontroller="[^"]*"[^>]*>[^<]*<span[^>]*>([^<]+)</span>', text)
            questions.extend(matches)

            # Deduplica e limpa
            seen = set()
            unique_questions = []
            for q in questions:
                q = q.strip()
                if q and len(q) > 5 and q not in seen and "?" in q or q.endswith("?"):
                    seen.add(q)
                    unique_questions.append(q)
                elif q and len(q) > 5 and q not in seen:
                    seen.add(q)
                    unique_questions.append(q)

            return unique_questions[:10]

        except Exception as e:
            print(f"[KeywordMiner] Erro ao buscar PAA para '{keyword}': {e}")
            return []

    # ─── SERP DIFFICULTY ANALYSIS ──────────────────────────────────────────

    async def analyze_serp_difficulty(self, keyword: str, lang: str = "pt") -> dict:
        """
        Analisa a dificuldade de rankeamento de uma keyword.
        Usa Obscura quando disponível para renderização JS real.
        """
        search_url = GOOGLE_SEARCH_URL.format(
            query=quote(keyword),
            lang="pt-BR" if lang == "pt" else "en",
        )

        # Tenta Obscura primeiro
        if self.use_obscura:
            try:
                obs = _get_obscura_bridge()
                if obs:
                    data = await obs(keyword, lang)
                    if data.get("source") == "obscura" and data.get("urls"):
                        # Usa URLs extraidas via Obscura (JS real, mais confiavel)
                        result_urls = data.get("urls", [])
                        paas = data.get("people_also_ask", [])

                        weak_count, strong_count, weak_sites, strong_sites = self._analyze_urls(result_urls)
                        difficulty, label = self._calculate_difficulty(weak_count, strong_count)

                        return {
                            "keyword": keyword,
                            "difficulty": difficulty,
                            "difficulty_label": label,
                            "weak_sites": weak_sites,
                            "strong_sites": strong_sites,
                            "weak_count": weak_count,
                            "strong_count": strong_count,
                            "result_urls_found": len(result_urls),
                            "people_also_ask": paas,
                            "search_url": search_url,
                            "source": "obscura",
                        }
            except Exception as e:
                print(f"[KeywordMiner] Obscura SERP falhou, fallback regex: {e}")

        # Fallback: regex
        try:
            client = await self._get_http()
            response = await client.get(
                search_url,
                headers={
                    "User-Agent": random.choice(USER_AGENTS),
                    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8" if lang == "pt" else "en-US,en;q=0.9",
                },
            )
            text = response.text

            # Extrai URLs dos resultados
            url_pattern = r'href="(https?://[^"]+)"'
            all_urls = re.findall(url_pattern, text)

            # Filtra URLs do Google (não resultados)
            result_urls = []
            for url in all_urls:
                if (url.startswith("http") and
                    not url.startswith("https://www.google.") and
                    not url.startswith("https://accounts.google.") and
                    not url.startswith("https://support.google.") and
                    not "google.com/search" in url and
                    not "googleadservices" in url):
                    result_urls.append(url)

            weak_count, strong_count, weak_sites, strong_sites = self._analyze_urls(result_urls)
            difficulty, label = self._calculate_difficulty(weak_count, strong_count)

            # PAA
            paas = await self.fetch_people_also_ask(keyword, lang)

            return {
                "keyword": keyword,
                "difficulty": difficulty,
                "difficulty_label": label,
                "weak_sites": weak_sites,
                "strong_sites": strong_sites,
                "weak_count": weak_count,
                "strong_count": strong_count,
                "result_urls_found": len(result_urls),
                "people_also_ask": paas,
                "search_url": search_url,
                "source": "regex_fallback",
            }

        except Exception as e:
            print(f"[KeywordMiner] Erro na análise SERP para '{keyword}': {e}")
            return {
                "keyword": keyword,
                "difficulty": 50,
                "difficulty_label": "medium",
                "weak_sites": [],
                "strong_sites": [],
                "weak_count": 0,
                "strong_count": 0,
                "result_urls_found": 0,
                "people_also_ask": [],
                "search_url": search_url,
                "source": "error",
            }

    def _analyze_urls(self, urls: list) -> tuple:
        """Analisa URLs e retorna (weak_count, strong_count, weak_sites, strong_sites)."""
        weak_count = 0
        strong_count = 0
        weak_sites = []
        strong_sites = []

        for url in urls[:20]:
            domain = re.search(r'https?://([^/]+)', url)
            if domain:
                domain_name = domain.group(1).lower()

                for pattern in WEAK_DOMAIN_PATTERNS:
                    if pattern in domain_name:
                        weak_count += 1
                        weak_sites.append(domain_name)
                        break

                for pattern in STRONG_DOMAIN_PATTERNS:
                    if pattern in domain_name:
                        strong_count += 1
                        strong_sites.append(domain_name)
                        break

        return weak_count, strong_count, list(set(weak_sites)), list(set(strong_sites))

    def _calculate_difficulty(self, weak_count: int, strong_count: int) -> tuple:
        """Calcula difficulty (0-100) e label a partir da contagem."""
        total = weak_count + strong_count
        if total == 0:
            difficulty = 50
        else:
            strong_ratio = strong_count / max(total, 1)

            if weak_count >= 2 and strong_count == 0:
                difficulty = random.randint(10, 25)
            elif weak_count >= 1 and strong_count <= 1:
                difficulty = random.randint(15, 35)
            elif strong_ratio > 0.6:
                difficulty = random.randint(65, 90)
            elif strong_ratio > 0.3:
                difficulty = random.randint(45, 65)
            else:
                difficulty = random.randint(30, 50)

        if difficulty <= 30:
            label = "easy"
        elif difficulty <= 60:
            label = "medium"
        else:
            label = "hard"

        return difficulty, label

    # ─── MINE PRINCIPAL ─────────────────────────────────────────────────────

    async def mine(self, seed_keyword: str, lang: str = "pt",
                   max_keywords: int = 50, analyze_serp: bool = True,
                   include_questions: bool = True) -> list:
        """
        Pipeline completa de keyword mining.

        1. Sugestões iniciais do autocomplete
        2. Expansão por prefixos
        3. Expansão por sufixos
        4. (Opcional) Análise SERP de dificuldade
        5. (Opcional) Perguntas do PAA

        Retorna lista de KeywordResult ordenados por dificuldade (mais fáceis primeiro).
        """
        seed = seed_keyword.lower().strip()
        print(f"[KeywordMiner] Mining keywords for: '{seed}'")

        # 1. Sugestões iniciais
        initial = await self._fetch_suggestions(seed, lang)
        print(f"[KeywordMiner] Initial suggestions: {len(initial)}")

        # 2. Expansão por prefixos
        prefixed = await self.expand_by_prefixes(seed, lang)
        print(f"[KeywordMiner] After prefix expansion: {len(prefixed)}")

        # 3. Expansão por sufixos
        suffixed = await self.expand_by_suffixes(seed, lang)
        print(f"[KeywordMiner] After suffix expansion: {len(suffixed)}")

        # 4. Unir, filtrar, deduplicar
        all_raw = set(initial + prefixed + suffixed)
        all_raw.add(seed)

        # Filtra: só keywords que contêm o seed ou são variações próximas
        relevant = [kw for kw in all_raw if _is_relevant_keyword(seed, kw)]
        print(f"[KeywordMiner] Relevant keywords: {len(relevant)}")

        # 5. Limitar
        relevant = relevant[:max_keywords]

        # 6. Analisar SERP (se solicitado) ou estimar
        results = []
        batch_size = 5  # Quantas SERP analysis paralelas

        for i in range(0, len(relevant), batch_size):
            batch = relevant[i:i + batch_size]

            if analyze_serp:
                # Análise SERP em paralelo
                tasks = [self.analyze_serp_difficulty(kw, lang) for kw in batch]
                serp_results = await asyncio.gather(*tasks)

                for kw, serp in zip(batch, serp_results):
                    result = KeywordResult(
                        keyword=kw,
                        source="autocomplete",
                        difficulty=serp["difficulty"],
                        difficulty_label=serp["difficulty_label"],
                        has_questions=len(serp.get("people_also_ask", [])) > 0,
                        questions=serp.get("people_also_ask", []),
                        search_url=serp.get("search_url", ""),
                        volume_estimate=max(10, 100 - serp["difficulty"]),
                    )
                    results.append(result)
            else:
                # Estimativa sem análise SERP
                result = KeywordResult(
                    keyword=kw,
                    source="autocomplete",
                    difficulty=50,
                    difficulty_label="medium",
                    volume_estimate=50,
                )
                results.append(result)

            await asyncio.sleep(0.2)  # Pequeno delay entre lotes

        # 7. Ordenar por dificuldade (mais fáceis primeiro)
        results.sort(key=lambda r: r.difficulty)

        print(f"[KeywordMiner] Final results: {len(results)} keywords")
        return results

    # ─── EASY KEYWORDS ──────────────────────────────────────────────────────

    async def find_easy_keywords(self, seed_keyword: str, lang: str = "pt",
                                  max_results: int = 20) -> list:
        """
        Encontra keywords FÁCEIS de rankear (low-hanging fruit).
        Mesmo que mine(), mas filtra só as com difficulty <= 40.
        """
        all_results = await self.mine(
            seed_keyword=seed_keyword,
            lang=lang,
            max_keywords=max_results * 3,  # Pega mais para filtrar
            analyze_serp=True,
        )
        easy = [r for r in all_results if r.difficulty <= 40]
        return easy[:max_results]

    # ─── CLUSTERING ─────────────────────────────────────────────────────────

    @staticmethod
    def cluster_keywords(keywords: list, min_cluster_size: int = 3) -> dict:
        """
        Agrupa keywords por tema/semelhança.

        Retorna dict: { "tema": [KeywordResult, ...] }
        """
        from collections import defaultdict

        clusters = defaultdict(list)
        assigned = set()

        for kw in keywords:
            if kw.keyword in assigned:
                continue

            # Pega as palavras mais significativas da keyword
            words = set(kw.keyword.lower().split())
            words = {w for w in words if len(w) > 3 and w not in
                     {'para', 'como', 'com', 'sem', 'mais', 'mas', 'que', 'por', 'dos', 'das'}}

            if not words:
                clusters["geral"].append(kw)
                assigned.add(kw.keyword)
                continue

            # Encontra o melhor cluster existente
            best_cluster = None
            best_overlap = 0

            for cluster_name, cluster_items in clusters.items():
                cluster_words = set(cluster_name.split())
                overlap = len(words & cluster_words)
                if overlap > best_overlap:
                    best_overlap = overlap
                    best_cluster = cluster_name

            if best_cluster and best_overlap >= 1:
                clusters[best_cluster].append(kw)
            else:
                # Cria novo cluster com a palavra mais significativa
                cluster_name = max(words, key=len)
                clusters[cluster_name].append(kw)

            assigned.add(kw.keyword)

        # Remove clusters muito pequenos
        return {k: v for k, v in clusters.items() if len(v) >= min_cluster_size}

    # ─── INTEGRAÇÃO COM BLOG WRITER ─────────────────────────────────────────

    @staticmethod
    def format_for_blog_writer(keywords: list, max_keywords: int = 5) -> str:
        """
        Formata keywords para usar como parâmetro 'keywords' no BlogWriter.

        Ex: "emagrecimento rapido, como emagrecer, dieta para emagrecer"
        """
        seen = set()
        formatted = []
        for kw in keywords[:max_keywords]:
            if kw.keyword not in seen:
                formatted.append(kw.keyword)
                seen.add(kw.keyword)
        return ", ".join(formatted)

    @staticmethod
    def get_best_keywords_for_article(keywords: list) -> dict:
        """
        Seleciona a melhor keyword + variações para um artigo.

        Retorna:
          - "main_keyword": keyword principal (a mais fácil)
          - "related_keywords": lista de variações
          - "people_also_ask": perguntas relacionadas
          - "keyword_string": string formatada para BlogWriter
        """
        if not keywords:
            return {
                "main_keyword": "",
                "related_keywords": [],
                "people_also_ask": [],
                "keyword_string": "",
            }

        # Pega a mais fácil
        sorted_kws = sorted(keywords, key=lambda r: r.difficulty)
        main = sorted_kws[0]

        # Pega variações (excluindo a principal)
        related = [kw.keyword for kw in sorted_kws[1:6]]

        # Perguntas
        paas = []
        for kw in sorted_kws[:5]:
            if kw.questions:
                paas.extend(kw.questions[:2])

        return {
            "main_keyword": main.keyword,
            "related_keywords": related,
            "people_also_ask": list(set(paas))[:8],
            "keyword_string": ", ".join([main.keyword] + related),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# FUNÇÃO DE ALTO NÍVEL — usado pelo server.py e Hermes
# ═══════════════════════════════════════════════════════════════════════════════

async def research_keywords(seed: str, lang: str = "pt",
                            max_results: int = 30,
                            use_obscura: bool = True) -> dict:
    """
    Função principal exposta para o ecossistema Dezafira.

    Exemplo:
        result = await research_keywords("emagrecimento")
        # result["keywords"] = [...]
        # result["easy_keywords"] = [...]
        # result["clusters"] = {...}
        # result["best_for_article"] = {...}
    """
    miner = KeywordMiner(use_obscura=use_obscura)
    try:
        all_kws = await miner.mine(
            seed_keyword=seed,
            lang=lang,
            max_keywords=max_results,
            analyze_serp=True,
        )

        # Filtra fáceis
        easy_kws = [kw for kw in all_kws if kw.difficulty_label == "easy"]
        medium_kws = [kw for kw in all_kws if kw.difficulty_label == "medium"]

        # Clusters
        clusters = miner.cluster_keywords(all_kws)

        # Melhor keyword para artigo
        best = miner.get_best_keywords_for_article(all_kws)

        return {
            "success": True,
            "seed": seed,
            "total_found": len(all_kws),
            "easy_count": len(easy_kws),
            "medium_count": len(medium_kws),
            "hard_count": len(all_kws) - len(easy_kws) - len(medium_kws),
            "keywords": [kw.to_dict() for kw in all_kws],
            "easy_keywords": [kw.to_dict() for kw in easy_kws[:10]],
            "medium_keywords": [kw.to_dict() for kw in medium_kws[:10]],
            "clusters": {k: [kw.to_dict() for kw in v] for k, v in clusters.items()},
            "best_for_article": best,
            "people_also_ask": best["people_also_ask"],
            "keyword_string": best["keyword_string"],
        }
    finally:
        await miner.close()


async def research_youtube_pains(seed: str, lang: str = "pt",
                                 max_pains: int = 30) -> dict:
    """
    Função de alto nível: minera as DORES REAIS que as pessoas buscam no YouTube
    (autocomplete ds=yt) para um nicho. Cada dor é uma busca real de usuário.

    Exemplo:
        result = await research_youtube_pains("investimento")
        # result["pains"] = [{"text": "como investir primeiro salário", ...}]
    """
    from services.obscura_bridge import obscura_enabled
    miner = KeywordMiner(use_obscura=obscura_enabled())
    try:
        pains = await miner.mine_youtube_pains(seed, lang, max_pains)
        return {
            "success": True,
            "seed": seed,
            "total_found": len(pains),
            "pains": pains,
            "source": "youtube_search",
            "tip": (
                "Cada dor veio do autocomplete REAL do YouTube (ds=yt): são as "
                "buscas que os usuários realmente digitam. Use-as como tópicos "
                "e keywords dos artigos para capturar esse público."
            ),
        }
    finally:
        await miner.close()


async def find_low_hanging_fruits(seed: str, lang: str = "pt",
                                   max_results: int = 10,
                                   use_obscura: bool = True) -> dict:
    """
    Encontra "frutas baixas" — keywords com concorrência fraca
    onde fóruns, Reddit, Quora, etc. rankeiam.

    Essas são as melhores oportunidades para rankear rápido.
    """
    miner = KeywordMiner(use_obscura=use_obscura)
    try:
        easy_kws = await miner.find_easy_keywords(
            seed_keyword=seed,
            lang=lang,
            max_results=max_results,
        )

        return {
            "success": True,
            "seed": seed,
            "total_found": len(easy_kws),
            "keywords": [kw.to_dict() for kw in easy_kws],
            "keyword_string": miner.format_for_blog_writer(easy_kws),
            "tip": (
                "Keywords classificadas como 'easy' são aquelas onde "
                "fóruns, Reddit, Quora ou sites fracos estão rankeando. "
                "Crie um artigo bem feito para roubar a posição!"
            ),
        }
    finally:
        await miner.close()
