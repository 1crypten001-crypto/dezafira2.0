"""
MÓDULO: google_seo_spy.py
DESCRICÃO: Dário - Especialista em SEO para Google
USO: Pesquisa keywords, backlinks e conteúdo relevante
"""
import os
import re
import json
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class GoogleSEOSpy:
    """
    Agente Dário - Especialista em SEO Google
    Pesquisa keywords, backlinks potenciais e conteúdos relevantes
    """
    
    def __init__(self, max_keywords: int = 20, cache_ttl_hours: int = 24):
        self.max_keywords = max_keywords
        self.cache_ttl = timedelta(hours=cache_ttl_hours)
        self._cache: Dict[str, Dict] = {}
    
    async def search_seo(self, keyword: str, niche: str = "") -> Dict[str, Any]:
        """
        Pesquisa dados SEO para uma keyword/nicho
        
        Args:
            keyword: Palavra-chave principal
            niche: Nicho específico
        
        Returns:
            Dict com keywords, backlinks e conteúdos relevantes
        """
        # Verifica cache
        cache_key = f"seo_{keyword}"
        if self._is_cached(cache_key):
            logger.info(f"[Dário SEO] Cache válido para: {keyword}")
            return self._cache[cache_key]
        
        try:
            # 1. Google Custom Search JSON API (requer GOOGLE_API_KEY + GOOGLE_CSE_ID)
            google_api_key = os.getenv("GOOGLE_API_KEY")
            
            if google_api_key:
                result = await self._search_with_api(keyword, niche)
            else:
                # 2. Motor de busca do dono (GOOGLE_CSE_ID/cx) via Chrome/Obscura
                #    — funciona sem API key: renderiza cse.google.com/cse?cx=... e extrai
                cse_id = os.getenv("GOOGLE_CSE_ID")
                if cse_id:
                    try:
                        result = await self._search_via_cse_scraper(keyword, niche, cse_id)
                    except Exception as e:
                        logger.warning(f"[Dário SEO] CSE via scraper falhou ({e}), usando SERP Google")
                        result = await self._search_via_scraper(keyword, niche)
                else:
                    # 3. Fallback: scraping direto da SERP do Google
                    result = await self._search_via_scraper(keyword, niche)
            
            # Salva no cache
            self._cache[cache_key] = result
            return result
            
        except Exception as e:
            logger.error(f"[Dário SEO] Erro na pesquisa SEO: {e}")
            return await self._generate_sample_seo_data(keyword, niche)
    
    async def _search_with_api(self, keyword: str, niche: str) -> Dict:
        """
        Pesquisa usando Google Custom Search API
        """
        google_api_key = os.getenv("GOOGLE_API_KEY")
        google_cse_id = os.getenv("GOOGLE_CSE_ID")
        
        if not google_api_key or not google_cse_id:
            logger.warning("[Dário SEO] Google API não configurada, usando scraping")
            return await self._search_via_scraper(keyword, niche)
        
        try:
            import httpx
            
            async with httpx.AsyncClient() as client:
                # Busca keywords relacionadas
                keywords_response = await client.get(
                    "https://www.googleapis.com/customsearch/v1",
                    params={
                        "key": google_api_key,
                        "cx": google_cse_id,
                        "q": f"{keyword} nicho {niche}",
                        "num": 10
                    }
                )
                
                if keywords_response.status_code == 200:
                    data = keywords_response.json()
                    items = data.get("items", [])
                    
                    keywords = []
                    for item in items:
                        keywords.append({
                            "keyword": item.get("title", "")[:60],
                            "url": item.get("link", ""),
                            "snippet": item.get("snippet", "")[:150]
                        })
                    
                    return {
                        "keyword": keyword,
                        "niche": niche,
                        "searched_at": datetime.utcnow().isoformat(),
                        "keywords": keywords[:self.max_keywords],
                        "backlinks": await self._find_backlinks(keywords),
                        "content Ideas": self._generate_content_ideas(keywords)
                    }
                else:
                    raise Exception(f"API error: {keywords_response.status_code}")
                    
        except Exception as e:
            logger.error(f"[Dário SEO] Erro na API: {e}")
            return await self._search_via_scraper(keyword, niche)
    
    async def _search_via_cse_scraper(self, keyword: str, niche: str, cse_id: str) -> Dict:
        """
        Usa o Google Programmable Search Engine do dono (cx) via Chrome/Obscura.

        Renderiza a página do CSE (cse.google.com/cse?cx=...) e extrai os
        resultados — gera as PALAVRAS-CHAVE para artigos de blog/backlinks
        mesmo sem GOOGLE_API_KEY (o motor já está configurado na conta).
        """
        from services.obscura_bridge import ObscuraBridge

        query = f"{keyword} {niche}".strip()
        url = f"https://cse.google.com/cse?cx={cse_id}#gsc.tab=0&gsc.q={query.replace(' ', '+')}"
        async with ObscuraBridge() as bridge:
            await bridge.navigate(url)
            await asyncio.sleep(4)
            # espera os resultados do motor renderizarem
            results_html = await bridge.execute_js("""
                () => {
                    const results = [];
                    const seen = new Set();
                    document.querySelectorAll('.gsc-webResult .gs-title a, .gsc-result .gs-title a').forEach(a => {
                        const title = a.textContent?.trim();
                        const link = a.href;
                        const block = a.closest('.gs-result') || a.closest('.gsc-webResult');
                        const snippet = block?.querySelector('.gs-snippet')?.textContent?.trim() || '';
                        if (title && link && !seen.has(link)) {
                            seen.add(link);
                            results.push({ title, url: link, snippet });
                        }
                    });
                    return JSON.stringify(results.slice(0, 20));
                }
            """)
            results = json.loads(results_html) if results_html else []
            if not results:
                logger.info("[Dário SEO] CSE sem resultados via scraper — usa fallback SERP")
                return await self._search_via_scraper(keyword, niche)

            keywords = await self._extract_keywords_from_results(results)
            return {
                "keyword": keyword,
                "niche": niche,
                "source": "google_cse_scraper",
                "cse_id": cse_id,
                "searched_at": datetime.utcnow().isoformat(),
                "keywords": keywords[:self.max_keywords],
                "backlinks": await self._find_backlinks(keywords),
                "content Ideas": self._generate_content_ideas(keywords),
                "results": results[:10],
            }

    async def _search_via_scraper(self, keyword: str, niche: str) -> Dict:
        """
        Scraping estruturado de dados SEO
        """
        try:
            from services.obscura_bridge import ObscuraBridge
            
            bridge = ObscuraBridge()
            await bridge.connect()
            
            # Busca no Google
            url = f"https://www.google.com/search?q={keyword}+{niche}&num=20"
            await bridge.navigate(url)
            await asyncio.sleep(3)
            
            # Extrai resultados
            results_html = await bridge.execute_js("""
                () => {
                    const results = [];
                    const elements = document.querySelectorAll('div.g, .result');
                    
                    elements.forEach((el, index) => {
                        const title = el.querySelector('h3')?.textContent?.trim();
                        const link = el.querySelector('a')?.href;
                        const snippet = el.querySelector('[data-sncf], .aCOpRe']?.textContent?.trim();
                        
                        if (title && link) {
                            results.push({
                                title: title,
                                url: link,
                                snippet: snippet || ''
                            });
                        }
                    });
                    
                    return JSON.stringify(results);
                }
            """)
            
            results = json.loads(results_html) if results_html else []
            
            # Extrai keywords das SERPs
            keywords = await self._extract_keywords_from_results(results)
            
            # Busca backlinks
            backlinks = await self._find_backlinks(keywords)
            
            await bridge.disconnect()
            
            return {
                "keyword": keyword,
                "niche": niche,
                "searched_at": datetime.utcnow().isoformat(),
                "keywords": keywords[:self.max_keywords],
                "backlinks": backlinks,
                "content_ideas": self._generate_content_ideas(keywords)
            }
            
        except Exception as e:
            logger.error(f"[Dário SEO] Erro no scraping: {e}")
            return await self._generate_sample_seo_data(keyword, niche)
    
    async def _extract_keywords_from_results(self, results: List[Dict]) -> List[Dict]:
        """
        Extrai keywords dos resultados de busca
        """
        keywords = []
        
        for result in results:
            title = result.get("title", "")
            snippet = result.get("snippet", "")
            
            # Extrai phrases relevantes
            phrases = re.findall(r'\b\w+\s*\w+\s*\w+\b', title + " " + snippet)
            
            for phrase in phrases[:3]:
                if len(phrase) > 10 and phrase.lower() not in [k["keyword"].lower() for k in keywords]:
                    keywords.append({
                        "keyword": phrase,
                        "search_volume": self._estimate_volume(phrase),
                        "difficulty": self._estimate_difficulty(phrase),
                        "intent": self._classify_intent(phrase)
                    })
        
        return keywords[:self.max_keywords]
    
    async def _find_backlinks(self, keywords: List[Dict]) -> List[Dict]:
        """
        Encontra backlinks potenciais baseado nas keywords
        """
        backlinks = []
        
        # Domínios comuns que aceitam guest posts
        potential_domains = [
            {"domain": "medium.com", "url": "https://medium.com/", "type": "guest_post", "relevance": "alta"},
            {"domain": "linkedin.com", "url": "https://linkedin.com/pulse/", "type": "article", "relevance": "alta"},
            {"domain": "reddit.com", "url": "https://reddit.com/", "type": "forum", "relevance": "media"},
            {"domain": "quora.com", "url": "https://quora.com/", "type": "forum", "relevance": "media"},
            {"domain": "hackernoon.com", "url": "https://hackernoon.com/", "type": "guest_post", "relevance": "alta"},
        ]
        
        for kw in keywords[:5]:
            for domain in potential_domains:
                backlinks.append({
                    **domain,
                    "keyword": kw["keyword"],
                    "url": f"{domain['url']}{kw['keyword'].replace(' ', '-')}"
                })
        
        return backlinks[:20]
    
    def _generate_content_ideas(self, keywords: List[Dict]) -> List[Dict]:
        """
        Gera ideias de conteúdo baseado nas keywords
        """
        ideas = []
        
        for kw in keywords[:10]:
            keyword = kw["keyword"]
            
            # Gera títulos de artigos
            templates = [
                f"Como {keyword} pode transformar sua vida",
                f"10 coisas que você não sabia sobre {keyword}",
                f"Guia completo: {keyword} para iniciantes",
                f"{keyword}: O que é e como funciona",
                f"Os melhores métodos para {keyword}"
            ]
            
            for template in templates[:2]:
                ideas.append({
                    "title": template,
                    "keyword": keyword,
                    "type": "artigo_blog",
                    "priority": "alta" if kw.get("difficulty", 50) < 40 else "media"
                })
        
        return ideas[:15]
    
    def _estimate_volume(self, keyword: str) -> int:
        """Estima volume de busca (simulado)"""
        # Heurística baseada no tamanho e complexidade
        base_volume = len(keyword) * 100
        return min(base_volume, 10000)
    
    def _estimate_difficulty(self, keyword: str) -> int:
        """Estima dificuldade (0-100)"""
        # Keywords mais longas tendem a ser menos competitivas
        words = keyword.split()
        if len(words) >= 4:
            return 20
        elif len(words) >= 3:
            return 40
        else:
            return 60
    
    def _classify_intent(self, keyword: str) -> str:
        """Classifica intenção de busca"""
        transactional = ["comprar", "preço", "custo", "vale", "oferta"]
        informational = ["como", "o que", "porque", "quando", "onde", "guia"]
        
        kw_lower = keyword.lower()
        
        if any(t in kw_lower for t in transactional):
            return "transacional"
        elif any(i in kw_lower for i in informational):
            return "informacional"
        else:
            return "navegacional"
    
    async def _generate_sample_seo_data(self, keyword: str, niche: str) -> Dict:
        """
        Gera dados simulados quando a pesquisa não é possível
        """
        logger.warning(f"[Dário SEO] Gerando dados simulados para: {keyword}")
        
        keywords = [
            {"keyword": f"{keyword} nicho {niche}", "search_volume": 5000, "difficulty": 35, "intent": "informacional"},
            {"keyword": f"como {keyword} funciona", "search_volume": 3200, "difficulty": 28, "intent": "informacional"},
            {"keyword": f"{keyword} para iniciantes", "search_volume": 2800, "difficulty": 25, "intent": "informacional"},
            {"keyword": f"melhor {keyword} 2024", "search_volume": 4100, "difficulty": 42, "intent": "transacional"},
            {"keyword": f"{keyword} preço", "search_volume": 1900, "difficulty": 55, "intent": "transacional"},
        ]
        
        backlinks = [
            {"domain": "medium.com", "url": "https://medium.com/", "type": "guest_post", "relevance": "alta"},
            {"domain": "linkedin.com", "url": "https://linkedin.com/", "type": "article", "relevance": "alta"},
            {"domain": "reddit.com", "url": "https://reddit.com/r/", "type": "forum", "relevance": "media"},
        ]
        
        return {
            "keyword": keyword,
            "niche": niche,
            "searched_at": datetime.utcnow().isoformat(),
            "keywords": keywords,
            "backlinks": backlinks,
            "content_ideas": self._generate_content_ideas(keywords),
            "is_sample": True
        }
    
    def _is_cached(self, key: str) -> bool:
        """Verifica se há cache válido (< 24h)"""
        entry = self._cache.get(key)
        if not entry:
            return False
        
        searched_at = entry.get("searched_at")
        if not searched_at:
            return False
        
        try:
            search_time = datetime.fromisoformat(searched_at.replace("Z", "+00:00"))
            return datetime.utcnow() - search_time < self.cache_ttl
        except:
            return False
    
    def clear_cache(self):
        """Limpa o cache"""
        self._cache.clear()
        logger.info("[Dário SEO] Cache limpo")


# Instância global do Dário (SEO)
dario_seo = GoogleSEOSpy()
