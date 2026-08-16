"""
MÓDULO: offer_api.py
DESCRICÃO: Endpoints da API para a Fábrica de Ofertas
"""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from modules.offer_models import (
    get_offer,
    list_offers,
    update_offer,
    delete_offer
)
from modules.offer_factory import OfferFactory

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/offers", tags=["Ofertas"])

# Instancia o orquestrador
offer_factory = OfferFactory()


# ═══════════════════════════════════════════════════════════════════════════
# SCHMAS
# ═══════════════════════════════════════════════════════════════════════════

class CreateOfferRequest(BaseModel):
    niche: str = Field(..., description="Nicho do produto (ex: emagrecimento, finanças)")
    keyword: str = Field(..., description="Palavra-chave principal")
    public: Optional[str] = Field(None, description="Público-alvo")


class UpdateOfferRequest(BaseModel):
    angle: Optional[str] = None
    mechanism: Optional[str] = None
    promise: Optional[str] = None
    price_cents: Optional[int] = None
    avatar_1_prompt: Optional[str] = None
    avatar_2_prompt: Optional[str] = None
    mascot_prompt: Optional[str] = None
    headlines: Optional[list] = None
    body_long: Optional[str] = None
    body_short: Optional[str] = None
    ctas: Optional[list] = None
    status: Optional[str] = None


class RegenerateAssetRequest(BaseModel):
    slot: str = Field(..., description="Slot do asset (avatar_1, avatar_2, mascot, product_image)")
    style_id: Optional[str] = Field("moderno", description="Estilo do Agnes Studio")


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════

@router.post("/create", summary="Criar nova oferta")
async def api_create_offer(request: CreateOfferRequest):
    """
    Cria uma nova oferta e inicia o pipeline de investigação.
    """
    try:
        offer = await offer_factory.create_offer(
            niche=request.niche,
            keyword=request.keyword,
            public=request.public
        )
        
        logger.info(f"[OfferAPI] Oferta criada: {offer['id']}")
        
        return {
            "success": True,
            "offer": offer
        }
        
    except Exception as e:
        logger.error(f"[OfferAPI] Erro ao criar oferta: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", summary="Listar ofertas")
async def api_list_offers(
    limit: int = Query(50, ge=1, le=200, description="Quantidade máxima de ofertas"),
    status: Optional[str] = Query(None, description="Filtrar por status")
):
    """
    Lista ofertas (mais recentes primeiro).
    """
    try:
        offers = list_offers(limit=limit)
        
        # Filtra por status se fornecido
        if status:
            offers = [o for o in offers if o.get("status") == status]
        
        return {
            "success": True,
            "count": len(offers),
            "offers": offers
        }
        
    except Exception as e:
        logger.error(f"[OfferAPI] Erro ao listar ofertas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{offer_id}", summary="Detalhes da oferta")
async def api_get_offer(offer_id: str):
    """
    Retorna detalhes completos de uma oferta.
    """
    try:
        offer = get_offer(offer_id)
        
        if not offer:
            raise HTTPException(status_code=404, detail="Oferta não encontrada")
        
        return {
            "success": True,
            "offer": offer
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[OfferAPI] Erro ao obter oferta: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{offer_id}/run", summary="Executar pipeline da oferta")
async def api_run_pipeline(offer_id: str):
    """
    Executa o pipeline completo da oferta (todas as fases).
    """
    try:
        # Verifica se a oferta existe
        offer = get_offer(offer_id)
        if not offer:
            raise HTTPException(status_code=404, detail="Oferta não encontrada")
        
        # Executa o pipeline
        result = await offer_factory.run_pipeline(offer_id)
        
        return {
            "success": True,
            "message": "Pipeline concluída com sucesso",
            "offer": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[OfferAPI] Erro ao executar pipeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{offer_id}/investigation", summary="Investigação do Dário")
async def api_get_investigation(offer_id: str):
    """
    Retorna os dados de investigação (Facebook Ads + Google SEO).
    """
    try:
        offer = get_offer(offer_id)
        
        if not offer:
            raise HTTPException(status_code=404, detail="Oferta não encontrada")
        
        investigation = offer.get("investigation")
        
        if not investigation:
            raise HTTPException(status_code=404, detail="Investigação não encontrada")
        
        return {
            "success": True,
            "investigation": investigation
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[OfferAPI] Erro ao obter investigação: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{offer_id}/keywords", summary="Keywords SEO")
async def api_get_keywords(offer_id: str):
    """
    Retorna as keywords SEO identificadas pelo Dário.
    """
    try:
        offer = get_offer(offer_id)
        
        if not offer:
            raise HTTPException(status_code=404, detail="Oferta não encontrada")
        
        keywords = offer.get("keywords", [])
        
        return {
            "success": True,
            "count": len(keywords),
            "keywords": keywords
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[OfferAPI] Erro ao obter keywords: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{offer_id}/backlinks", summary="Backlinks potenciais")
async def api_get_backlinks(offer_id: str):
    """
    Retorna os backlinks potenciais identificados pelo Dário.
    """
    try:
        offer = get_offer(offer_id)
        
        if not offer:
            raise HTTPException(status_code=404, detail="Oferta não encontrada")
        
        backlinks = offer.get("backlinks", [])
        
        return {
            "success": True,
            "count": len(backlinks),
            "backlinks": backlinks
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[OfferAPI] Erro ao obter backlinks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{offer_id}/assets", summary="Assets visuais")
async def api_get_assets(offer_id: str):
    """
    Retorna os assets visuais (avatares, mascote) da oferta.
    """
    try:
        offer = get_offer(offer_id)
        
        if not offer:
            raise HTTPException(status_code=404, detail="Oferta não encontrada")
        
        assets = offer.get("assets", [])
        
        return {
            "success": True,
            "count": len(assets),
            "assets": assets
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[OfferAPI] Erro ao obter assets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{offer_id}/publish", summary="Publicar oferta no Blueprint")
async def api_publish_offer(offer_id: str):
    """
    Publica a oferta no Blueprint Engine para geração do produto completo.
    """
    try:
        offer = get_offer(offer_id)
        
        if not offer:
            raise HTTPException(status_code=404, detail="Oferta não encontrada")
        
        if offer.get("status") != "completed":
            raise HTTPException(
                status_code=400,
                detail="Oferta não está completa. Execute o pipeline primeiro."
            )
        
        # Aqui seria a integração com o Blueprint Engine
        # Por enquanto, apenas atualiza o status
        update_offer(offer_id, status="published")
        
        return {
            "success": True,
            "message": "Oferta publicada no Blueprint com sucesso",
            "offer": offer
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[OfferAPI] Erro ao publicar oferta: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{offer_id}", summary="Remover oferta")
async def api_delete_offer(offer_id: str):
    """
    Remove uma oferta e todos os seus dados relacionados.
    """
    try:
        success = delete_offer(offer_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Oferta não encontrada")
        
        return {
            "success": True,
            "message": "Oferta removida com sucesso"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[OfferAPI] Erro ao remover oferta: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{offer_id}/regenerate-assets", summary="Regenerar assets")
async def api_regenerate_assets(offer_id: str, request: RegenerateAssetRequest):
    """
    Regenera um asset específico (avatar, mascote) usando Agnes Studio.
    """
    try:
        offer = get_offer(offer_id)
        
        if not offer:
            raise HTTPException(status_code=404, detail="Oferta não encontrada")
        
        # Aqui seria a integração com o Agnes Studio para gerar o asset
        # Por enquanto, apenas simula
        logger.info(f"[OfferAPI] Regenerando asset {request.slot} para oferta {offer_id}")
        
        return {
            "success": True,
            "message": f"Asset {request.slot} regenerado com sucesso",
            "slot": request.slot,
            "style_id": request.style_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[OfferAPI] Erro ao regenerar assets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════
# FUNÇÃO PARA REGISTRO DO ROUTER
# ═══════════════════════════════════════════════════════════════════════════

def register_offer_routes(app):
    """
    Registra os rotas de ofertas no app FastAPI.
    """
    app.include_router(router)
    logger.info("[OfferAPI] Rotas registradas com sucesso")
