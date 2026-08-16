"""
MÓDULO: offer_factory.py
DESCRICÃO: Orquestrador principal da Fábrica de Ofertas (Dário + Team)
FLUXO: Sequencial - Dário investiga → Hermes analisa → Conselheiro modela → Tonho copy → Zé do Traço assets → Dona Benta valida
"""
import os
import uuid
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from modules.offer_models import (
    create_offer,
    get_offer,
    update_offer,
    save_investigation,
    save_keywords,
    save_backlinks,
    save_asset
)
from modules.facebook_ads_spy import dario as dario_facebook
from modules.google_seo_spy import dario_seo
from modules.offer_modeler import Conselheiro
from modules.offer_copywriter import Tonho
from modules.offer_character import ZéDoTraco
from modules.offer_critic import DonaBenta
from modules.agnes_studio import AgnesStudio

logger = logging.getLogger(__name__)


class OfferFactory:
    """
    Orquestrador da Fábrica de Ofertas
    
    Fases:
    1. INVESTIGAÇÃO (Dário) - Facebook Ads + Google SEO
    2. ANÁLISE (Hermes) - Padrões + Angle estratégico
    3. MODELAGEM (Conselheiro) - Avatar + Mecanismo + Promessa
    4. COPYWRITING (Tonho) - Headlines + Body + CTAs
    5. ASSETS (Zé do Traço) - Personagens via Agnes Studio
    6. VALIDAÇÃO (Dona Benta) - Score de conversão + SEO
    """
    
    def __init__(self):
        self.agnes = AgnesStudio()
        self.conselheiro = Conselheiro()
        self.tonho = Tonho()
        self.ze_do_traco = ZéDoTraco()
        self.dona_benta = DonaBenta()
        self._tasks: Dict[str, Dict] = {}
    
    async def create_offer(self, niche: str, keyword: str, public: str = "") -> Dict[str, Any]:
        """
        Cria uma nova oferta e inicia o pipeline
        
        Args:
            niche: Nicho do produto (ex: emagrecimento, finanças)
            keyword: Palavra-chave principal
            public: Público-alvo (opcional)
        
        Returns:
            Dict com dados da oferta criada
        """
        logger.info(f"[OfferFactory] Criando oferta: niche={niche}, keyword={keyword}")
        
        # Fase 0: Criar registro no banco
        offer_data = create_offer(niche, keyword)
        offer_id = offer_data["id"]
        
        # Inicializa task
        self._tasks[offer_id] = {
            "status": "created",
            "stage": "investigation",
            "started_at": datetime.utcnow().isoformat(),
            "offer_id": offer_id
        }
        
        return offer_data
    
    async def run_pipeline(self, offer_id: str) -> Dict[str, Any]:
        """
        Executa o pipeline completo da oferta (todas as fases)
        
        Args:
            offer_id: ID da oferta
        
        Returns:
            Dict com resultado completo
        """
        logger.info(f"[OfferFactory] Iniciando pipeline para oferta: {offer_id}")
        
        # Atualiza status
        update_offer(offer_id, status="running")
        self._tasks[offer_id]["status"] = "running"
        
        try:
            # FASE 1: INVESTIGAÇÃO (Dário)
            offer = get_offer(offer_id)
            if not offer:
                raise ValueError(f"Oferta {offer_id} não encontrada")
            
            investigation = await self._phase_investigation(
                offer_id,
                offer["keyword"],
                offer["niche"]
            )
            
            # FASE 2: ANÁLISE (Hermes) - Simplificado
            analysis = await self._phase_analysis(offer_id, investigation)
            
            # FASE 3: MODELAGEM (Conselheiro)
            model = await self._phase_modeling(offer_id, analysis, investigation)
            
            # FASE 4: COPYWRITING (Tonho)
            copy = await self._phase_copywriting(offer_id, model, investigation)
            
            # FASE 5: ASSETS (Zé do Traço)
            assets = await self._phase_assets(offer_id, model)
            
            # FASE 6: VALIDAÇÃO (Dona Benta)
            validation = await self._phase_validation(offer_id, copy, assets)
            
            # Atualiza status final
            update_offer(
                offer_id,
                status="completed",
                conversion_score=validation.get("conversion_score"),
                seo_score=validation.get("seo_score")
            )
            self._tasks[offer_id]["status"] = "completed"
            self._tasks[offer_id]["completed_at"] = datetime.utcnow().isoformat()
            
            # Retorna resultado completo
            final_offer = get_offer(offer_id)
            final_offer["validation"] = validation
            
            return final_offer
            
        except Exception as e:
            logger.error(f"[OfferFactory] Erro no pipeline: {e}")
            update_offer(offer_id, status="failed", error=str(e))
            self._tasks[offer_id]["status"] = "failed"
            self._tasks[offer_id]["error"] = str(e)
            raise
    
    async def _phase_investigation(self, offer_id: str, keyword: str, niche: str) -> Dict:
        """
        FASE 1: Dário investiga Facebook Ads + Google SEO
        """
        logger.info(f"[OfferFactory] Fase 1: Dário investigando - {keyword}")
        
        # Pesquisa Facebook Ads
        facebook_result = await dario_facebook.search_ads(keyword, niche, limit=20)
        
        # Pesquisa Google SEO
        seo_result = await dario_seo.search_seo(keyword, niche)
        
        # Combina resultados
        investigation = {
            "facebook_ads": facebook_result.get("ads", []),
            "facebook_patterns": facebook_result.get("patterns", {}),
            "google_keywords": seo_result.get("keywords", []),
            "google_backlinks": seo_result.get("backlinks", []),
            "google_content_ideas": seo_result.get("content_ideas", []),
            "status": "completed"
        }
        
        # Salva no banco
        save_investigation(offer_id, {
            "keyword": keyword,
            "niche": niche,
            "facebook_ads": investigation["facebook_ads"],
            "facebook_patterns": investigation["facebook_patterns"],
            "google_keywords": seo_result.get("keywords", []),
            "google_backlinks": seo_result.get("backlinks", []),
            "google_content": seo_result.get("content_ideas", []),
            "status": "completed"
        })
        
        # Salva keywords e backlinks separadamente
        save_keywords(offer_id, seo_result.get("keywords", []))
        save_backlinks(offer_id, seo_result.get("backlinks", []))
        
        logger.info(f"[OfferFactory] Fase 1 concluída: {len(investigation['facebook_ads'])} anúncios, {len(seo_result.get('keywords', []))} keywords")
        
        return investigation
    
    async def _phase_analysis(self, offer_id: str, investigation: Dict) -> Dict:
        """
        FASE 2: Hermes analisa padrões e define angle estratégico
        """
        logger.info(f"[OfferFactory] Fase 2: Hermes analisando padrões")
        
        # Simula análise do Hermes (em produção, chamaria a LLM)
        facebook_ads = investigation.get("facebook_ads", [])
        patterns = investigation.get("facebook_patterns", {})
        
        # Extrai padrões comuns
        common_pains = patterns.get("common_pains", [])
        common_desires = patterns.get("common_desires", [])
        common_ctas = patterns.get("common_ctas", [])
        
        # Define angle estratégico
        angle = f"Transforme sua vida com {common_desires[0] if common_desires else 'resultados'} sem {common_pains[0] if common_pains else 'dificuldade'}"
        
        # Define mecanismo único
        mechanism = "Método testado por +10.000 pessoas com resultados garantidos em 30 dias"
        
        analysis = {
            "angle": angle,
            "mechanism": mechanism,
            "common_pains": common_pains,
            "common_desires": common_desires,
            "common_ctas": common_ctas,
            "recommended_price_cents": 9700,  # R$ 97,00
            "status": "completed"
        }
        
        # Salva no banco
        update_offer(offer_id, 
                     angle=angle,
                     mechanism=mechanism,
                     price_cents=analysis["recommended_price_cents"])
        
        logger.info(f"[OfferFactory] Fase 2 concluída: angle={angle[:50]}...")
        
        return analysis
    
    async def _phase_modeling(self, offer_id: str, analysis: Dict, investigation: Dict) -> Dict:
        """
        FASE 3: Conselheiro modela a oferta completa
        """
        logger.info(f"[OfferFactory] Fase 3: Conselheiro modelando oferta")
        
        # Usa o Conselheiro para modelar
        model = await self.conselheiro.model_offer(investigation, analysis.get("niche", ""), investigation.get("keyword", ""))
        
        # Salva prompts no banco
        update_offer(offer_id,
                     avatar_1_prompt=model.get("avatar_1", {}).get("prompt"),
                     avatar_2_prompt=model.get("avatar_2", {}).get("prompt"),
                     mascot_prompt=model.get("mascot", {}).get("prompt"))
        
        logger.info(f"[OfferFactory] Fase 3 concluída: modelagem completa")
        
        return model
    
    async def _phase_copywriting(self, offer_id: str, model: Dict, investigation: Dict) -> Dict:
        """
        FASE 4: Tonho gera copies de alta conversão
        """
        logger.info(f"[OfferFactory] Fase 4: Tonho gerando copies")
        
        # Usa o Tonho para gerar copy
        copy = await self.tonho.generate_copy(model, investigation)
        
        # Salva no banco
        update_offer(offer_id,
                     headlines=copy.get("headlines"),
                     body_long=copy.get("body_long"),
                     body_short=copy.get("body_short"),
                     ctas=copy.get("ctas"))
        
        logger.info(f"[OfferFactory] Fase 4 concluída: {len(copy.get('headlines', []))} headlines geradas")
        
        return copy
    
    async def _phase_assets(self, offer_id: str, model: Dict) -> Dict:
        """
        FASE 5: Zé do Traço gera personagens via Agnes Studio
        """
        logger.info(f"[OfferFactory] Fase 5: Zé do Traço gerando personagens")
        
        # Usa o Zé do Traço para gerar personagens
        assets = await self.ze_do_traco.generate_characters(offer_id, model)
        
        # Atualiza URLs no banco
        if assets.get("avatar_1"):
            update_offer(offer_id, avatar_1_url=assets["avatar_1"].get("url"))
        if assets.get("avatar_2"):
            update_offer(offer_id, avatar_2_url=assets["avatar_2"].get("url"))
        if assets.get("mascot"):
            update_offer(offer_id, mascot_url=assets["mascot"].get("url"))
        
        logger.info(f"[OfferFactory] Fase 5 concluída: personagens gerados")
        
        return assets
    
    async def _phase_validation(self, offer_id: str, copy: Dict, assets: Dict) -> Dict:
        """
        FASE 6: Dona Benta valida e gera scores
        """
        logger.info(f"[OfferFactory] Fase 6: Dona Benta validando oferta")
        
        # Usa a Dona Benta para validar
        validation = await self.dona_benta.validate_offer(copy, copy, assets)
        
        # Atualiza scores no banco
        update_offer(offer_id,
                     conversion_score=validation.get("conversion_score"),
                     seo_score=validation.get("seo_score"))
        
        logger.info(f"[OfferFactory] Fase 6 concluída: conversion={validation.get('conversion_score')}, seo={validation.get('seo_score')}")
        
        return validation
    
    async def regenerate_asset(self, offer_id: str, slot: str, style_id: str = "moderno") -> Dict:
        """
        Regenera um asset específico
        """
        logger.info(f"[OfferFactory] Regenerando asset: {slot}")
        
        offer = get_offer(offer_id)
        if not offer:
            raise ValueError(f"Oferta {offer_id} não encontrada")
        
        # Gera novo asset
        if slot == "avatar_1":
            prompt = offer.get("avatar_1_prompt")
            if not prompt:
                raise ValueError("Prompt do avatar_1 não encontrado")
            asset = await self.ze_do_traco._generate_character(offer_id, slot, prompt, style_id)
        elif slot == "avatar_2":
            prompt = offer.get("avatar_2_prompt")
            if not prompt:
                raise ValueError("Prompt do avatar_2 não encontrado")
            asset = await self.ze_do_traco._generate_character(offer_id, slot, prompt, style_id)
        elif slot == "mascot":
            prompt = offer.get("mascot_prompt")
            if not prompt:
                raise ValueError("Prompt do mascot não encontrado")
            asset = await self.ze_do_traco._generate_mascot(offer_id, prompt, style_id)
        else:
            raise ValueError(f"Slot inválido: {slot}")
        
        return asset or {}
    
    def get_task_status(self, offer_id: str) -> Dict:
        """
        Retorna o status atual da task
        """
        return self._tasks.get(offer_id, {"status": "not_found"})


# Instância global
offer_factory = OfferFactory()
