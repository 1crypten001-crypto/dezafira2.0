"""
MÓDULO: facebook_ads_spy.py
DESCRICÃO: Dário - Espião de Anúncios do Facebook Ads Library
USO: Pesquisa anúncios escalados via Obscura/Chrome headless
"""
import os
import re
import json
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class FacebookAdsSpy:
    """
    Agente Dário - Especialista em Facebook Ads
    Usa Obscura/Chrome headless para scraping estruturado da Biblioteca de Anúncios
    """
    
    def __init__(self, max_ads: int = 20, cache_ttl_hours: int = 24):
        self.max_ads = max_ads
        self.cache_ttl = timedelta(hours=cache_ttl_hours)
        self._cache: Dict[str, Dict] = {}
    
    async def search_ads(self, keyword: str, niche: str = "", limit: int = None) -> Dict[str, Any]:
        """
        Pesquisa anúncios no Facebook Ads Library
        
        Args:
            keyword: Palavra-chave principal do nicho
            niche: Nicho específico (ex: emagrecimento, finanças)
            limit: Quantidade máxima de anúncios (padrão: self.max_ads)
        
        Returns:
            Dict com anúncios encontrados + padrões identificados
        """
        limit = limit or self.max_ads
        
        # Verifica cache
        cache_key = f"fb_{keyword}_{limit}"
        if self._is_cached(cache_key):
            logger.info(f"[Dário] Cache válido para: {keyword}")
            return self._cache[cache_key]
        
        ads = []
        try:
            # 1. Tentar API oficial primeiro se credenciais estiverem disponíveis
            ads = await self._query_graph_api(keyword, limit)
            
            # 2. Fallback para Obscura Scraping se a API oficial não retornou anúncios
            if not ads:
                from services.obscura_bridge import ObscuraBridge, get_obscura_status
                
                status = await get_obscura_status()
                if status.get("online"):
                    logger.info(f"[Dário] Pesquisando anúncios via Obscura para: {keyword}")
                    ads = await self._scrape_facebook_ads(keyword, limit)
                else:
                    logger.warning("[Dário] Obscura não disponível para fallback.")
            
            # 3. Fallback para dados simulados se nenhum método acima funcionou
            if not ads:
                return await self._generate_sample_data(keyword, niche, limit)
                
            # Analisa padrões
            patterns = self._analyze_patterns(ads)
            
            result = {
                "keyword": keyword,
                "niche": niche,
                "searched_at": datetime.utcnow().isoformat(),
                "ads_count": len(ads),
                "ads": ads[:limit],
                "patterns": patterns
            }
            
            # Cacheia resultado
            self._cache[cache_key] = result
            return result
            
        except Exception as e:
            logger.error(f"[Dário] Erro na pesquisa Facebook Ads: {e}")
            # Fallback final
            return await self._generate_sample_data(keyword, niche, limit)

    async def _query_graph_api(self, keyword: str, limit: int) -> List[Dict]:
        """
        Consulta a API oficial do Facebook Ads Archive
        """
        import httpx
        
        token = os.getenv("FACEBOOK_ACCESS_TOKEN")
        if not token or token == "seu_token_aqui":
            app_id = os.getenv("FACEBOOK_APP_ID")
            app_secret = os.getenv("FACEBOOK_APP_SECRET")
            if app_id and app_secret:
                token = f"{app_id.strip()}|{app_secret.strip()}"
            else:
                return []
                
        url = "https://graph.facebook.com/v18.0/ads_archive"
        params = {
            "access_token": token,
            "search_terms": keyword,
            "ad_reached_countries": "['BR']",
            "ad_active_status": "ACTIVE",
            "fields": "id,page_id,page_name,ad_creative_bodies,ad_creative_link_titles,ad_creative_link_captions",
            "limit": limit
        }
        
        try:
            logger.info(f"[Dário] Consultando API oficial do Facebook Ads Archive...")
            async with httpx.AsyncClient(timeout=15.0) as client:
                r = await client.get(url, params=params)
                if r.status_code != 200:
                    logger.error(f"[Dário] Erro na API do Facebook ({r.status_code}): {r.text}")
                    return []
                    
                data = r.json()
                results = data.get("data", [])
                
                ads = []
                for item in results:
                    bodies = item.get("ad_creative_bodies") or []
                    titles = item.get("ad_creative_link_titles") or []
                    captions = item.get("ad_creative_link_captions") or []
                    
                    ad_copy = bodies[0] if bodies else ""
                    headline = titles[0] if titles else ""
                    cta = captions[0] if captions else "Saiba Mais"
                    
                    ads.append({
                        "page_name": item.get("page_name", "Anunciante"),
                        "ad_copy": ad_copy,
                        "headline": headline,
                        "cta": cta,
                        "media_url": "",
                        "media_type": "image",
                        "engagement": None
                    })
                return ads
        except Exception as e:
            logger.error(f"[Dário] Falha na consulta à API do Facebook: {e}")
            return []
    
    async def _scrape_facebook_ads(self, keyword: str, limit: int) -> List[Dict]:
        """
        Scraping estruturado da Facebook Ads Library via Obscura
        """
        ads = []
        
        try:
            from services.obscura_bridge import ObscuraBridge
            
            bridge = ObscuraBridge()
            await bridge.connect()
            
            # Navega para a biblioteca de anúncios
            url = f"https://www.facebook.com/ads/library/?active_status=active&q={keyword}&country=BR"
            await bridge.navigate(url)
            
            # Aguarda carregamento
            await asyncio.sleep(3)
            
            # Extrai anúncios via JavaScript
            ads_html = await bridge.execute_js("""
                () => {
                    const ads = [];
                    const adElements = document.querySelectorAll('[data-testid*="ad"], [role="article"]');
                    
                    adElements.forEach((el, index) => {
                        if (index >= 20) return;
                        
                        const ad = {
                            page_name: '',
                            ad_copy: '',
                            headline: '',
                            cta: '',
                            media_url: '',
                            media_type: 'image',
                            engagement: null
                        };
                        
                        // Extrai nome da página
                        const pageNameEl = el.querySelector('[data-testid*="page"]');
                        if (pageNameEl) ad.page_name = pageNameEl.textContent.trim();
                        
                        // Extrai copy do anúncio
                        const copyEl = el.querySelector('[data-testid="ad-copy"]');
                        if (copyEl) ad.ad_copy = copyEl.textContent.trim();
                        
                        // Extrai headline
                        const headlineEl = el.querySelector('h3, [data-testid*="headline"]');
                        if (headlineEl) ad.headline = headlineEl.textContent.trim();
                        
                        // Extrai CTA
                        const ctaEl = el.querySelector('button, [data-testid*="cta"]');
                        if (ctaEl) ad.cta = ctaEl.textContent.trim();
                        
                        // Extrai mídia
                        const mediaEl = el.querySelector('img, video');
                        if (mediaEl) {
                            ad.media_url = mediaEl.src || mediaEl.getAttribute('src') || '';
                            ad.media_type = mediaEl.tagName.toLowerCase();
                        }
                        
                        ads.push(ad);
                    });
                    
                    return ads;
                }
            """)
            
            if ads_html:
                ads = json.loads(ads_html) if isinstance(ads_html, str) else ads_html
                
        except Exception as e:
            logger.error(f"[Dário] Erro no scraping: {e}")
        finally:
            try:
                await bridge.disconnect()
            except:
                pass
        
        return ads
    
    def _analyze_patterns(self, ads: List[Dict]) -> Dict[str, Any]:
        """
        Analisa padrões nos anúncios encontrados
        """
        patterns = {
            "common_pains": [],
            "common_desires": [],
            "common_hooks": [],
            "common_ctas": [],
            "media_types": {"image": 0, "video": 0},
            "avg_copy_length": 0
        }
        
        if not ads:
            return patterns
        
        total_copy_length = 0
        
        for ad in ads:
            copy = ad.get("ad_copy", "").lower()
            headline = ad.get("headline", "").lower()
            cta = ad.get("cta", "").lower()
            media_type = ad.get("media_type", "image")
            
            # Conta tipos de mídia
            patterns["media_types"][media_type] = patterns["media_types"].get(media_type, 0) + 1
            
            # Calcula tamanho médio da copy
            total_copy_length += len(copy)
            
            # Identifica padrões de dor (heurística simples)
            pain_keywords = ["dor", "problema", "difícil", "lento", "caro", "inbfelis", "ansioso", "preocupado"]
            for kw in pain_keywords:
                if kw in copy or kw in headline:
                    if kw not in patterns["common_pains"]:
                        patterns["common_pains"].append(kw)
            
            # Identifica padrões de desejo
            desire_keywords = ["resultado", "rapido", "fácil", "barato", "feliz", "confiante", "sucesso", "transformação"]
            for kw in desire_keywords:
                if kw in copy or kw in headline:
                    if kw not in patterns["common_desires"]:
                        patterns["common_desires"].append(kw)
            
            # Identifica CTAs comuns
            cta_keywords = ["compre", "saiba mais", "inscreva-se", "baixe", "teste", "garanta", "comece"]
            for kw in cta_keywords:
                if kw in cta:
                    if kw not in patterns["common_ctas"]:
                        patterns["common_ctas"].append(kw)
        
        patterns["avg_copy_length"] = total_copy_length // len(ads) if ads else 0
        
        return patterns
    
    async def _generate_sample_data(self, keyword: str, niche: str, limit: int) -> Dict:
        """
        Gera dados simulados quando Obscura não está disponível
        """
        logger.warning(f"[Dário] Gerando dados simulados para: {keyword}")
        
        # Dados de exemplo baseados no nicho
        sample_ads = [
            {
                "page_name": f"Clínica {niche.title()}",
                "ad_copy": f"Descubra o método natural para {keyword} sem sofrimento. Resultados em 30 dias garantidos!",
                "headline": f"Método Natural para {keyword.title()}",
                "cta": "Saiba Mais",
                "media_url": "https://example.com/ad1.jpg",
                "media_type": "image",
                "engagement": 1250
            },
            {
                "page_name": "Especialista em Emagrecimento",
                "ad_copy": "Já tentou de tudo e não consegue emagrecer? Nosso método já ajudou +10.000 pessoas.",
                "headline": "Emagreça sem Dietas Restritivas",
                "cta": "Quero Começar",
                "media_url": "https://example.com/ad2.mp4",
                "media_type": "video",
                "engagement": 3420
            }
        ]
        
        return {
            "keyword": keyword,
            "niche": niche,
            "searched_at": datetime.utcnow().isoformat(),
            "ads_count": len(sample_ads),
            "ads": sample_ads,
            "patterns": self._analyze_patterns(sample_ads),
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
        logger.info("[Dário] Cache limpo")


# Instância global do Dário
dario = FacebookAdsSpy()
