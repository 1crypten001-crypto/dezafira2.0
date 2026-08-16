"""
MÓDULO: offer_models.py
DESCRICÃO: Modelos ORM para a Fábrica de Ofertas (Dário + Team)
"""
import os
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, Integer, Boolean, Text
from sqlalchemy.orm import relationship
from modules.database import Base, SessionLocal


# ═══════════════════════════════════════════════════════════════════════════
# MODELOS — FÁBRICA DE OFERTAS (DÁRIO + TEAM)
# ═══════════════════════════════════════════════════════════════════════════

class OfferModel(Base):
    """Modelo de oferta criado pela Fábrica de Ofertas."""
    __tablename__ = "offer_models"
    
    id = Column(String(50), primary_key=True, index=True)
    slug = Column(String(255), unique=True, nullable=False)
    niche = Column(String(100), nullable=True)
    keyword = Column(String(255), nullable=True)
    
    # Estrutura da oferta
    angle = Column(Text, nullable=True)  # dor → desejo
    mechanism = Column(Text, nullable=True)  # mecanismo único
    promise = Column(Text, nullable=True)  # promessa principal
    price_cents = Column(Integer, default=0)
    
    # Avatares e personagens
    avatar_1_prompt = Column(Text, nullable=True)
    avatar_1_url = Column(String(1000), nullable=True)
    avatar_2_prompt = Column(Text, nullable=True)
    avatar_2_url = Column(String(1000), nullable=True)
    mascot_prompt = Column(Text, nullable=True)
    mascot_url = Column(String(1000), nullable=True)
    
    # Copy
    headlines = Column(JSON, nullable=True)  # ["Headline A", "Headline B", ...]
    body_long = Column(Text, nullable=True)
    body_short = Column(Text, nullable=True)
    ctas = Column(JSON, nullable=True)  # ["Botão 1", "Botão 2", ...]
    
    # Status
    status = Column(String(30), default="draft")  # draft, reviewing, completed, published
    conversion_score = Column(Integer, nullable=True)  # 0-100
    seo_score = Column(Integer, nullable=True)  # 0-100
    
    # Pipeline
    pipeline_run_id = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = Column(DateTime, nullable=True)
    
    # Relações
    investigation = relationship("OfferInvestigation", back_populates="offer", uselist=False)
    keywords = relationship("OfferKeyword", back_populates="offer")
    backlinks = relationship("OfferBacklink", back_populates="offer")
    assets = relationship("OfferAsset", back_populates="offer")


class OfferInvestigation(Base):
    """Investigação feita pelo Dário (Facebook Ads + Google SEO)."""
    __tablename__ = "offer_investigations"
    
    id = Column(String(50), primary_key=True, index=True)
    offer_id = Column(String(50), ForeignKey("offer_models.id"), nullable=False)
    keyword = Column(String(255), nullable=True)
    niche = Column(String(100), nullable=True)
    
    # Dados do Facebook Ads
    facebook_ads = Column(JSON, nullable=True)  # Lista de anúncios encontrados
    facebook_patterns = Column(JSON, nullable=True)  # Padrões identificados
    
    # Dados do Google SEO
    google_keywords = Column(JSON, nullable=True)  # Keywords top
    google_backlinks = Column(JSON, nullable=True)  # Backlinks potenciais
    google_content = Column(JSON, nullable=True)  # Conteúdos relevantes
    
    status = Column(String(20), default="pending")  # pending, running, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Relações
    offer = relationship("OfferModel", back_populates="investigation")


class OfferKeyword(Base):
    """Keywords SEO identificadas pelo Dário."""
    __tablename__ = "offer_keywords"
    
    id = Column(String(50), primary_key=True, index=True)
    offer_id = Column(String(50), ForeignKey("offer_models.id"), nullable=False)
    keyword = Column(String(255), nullable=False)
    search_volume = Column(Integer, nullable=True)
    difficulty = Column(Integer, nullable=True)
    intent = Column(String(50), nullable=True)  # informacional, transacional, navegacional
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relações
    offer = relationship("OfferModel", back_populates="keywords")


class OfferBacklink(Base):
    """Backlinks potenciais identificados pelo Dário."""
    __tablename__ = "offer_backlinks"
    
    id = Column(String(50), primary_key=True, index=True)
    offer_id = Column(String(50), ForeignKey("offer_models.id"), nullable=False)
    domain = Column(String(255), nullable=True)
    url = Column(String(500), nullable=True)
    relevance = Column(String(20), nullable=True)  # alta, media, baixa
    link_type = Column(String(50), nullable=True)  # guest_post, resource, forum
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relações
    offer = relationship("OfferModel", back_populates="backlinks")


class OfferAsset(Base):
    """Assets visuais da oferta (avatares, mascote, imagens)."""
    __tablename__ = "offer_assets"
    
    id = Column(String(50), primary_key=True, index=True)
    offer_id = Column(String(50), ForeignKey("offer_models.id"), nullable=False)
    slot = Column(String(50), nullable=False)  # avatar_1, avatar_2, mascot, product_image
    url = Column(String(1000), nullable=True)
    prompt = Column(Text, nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    provider = Column(String(50), nullable=True)  # agnes-studio, upload
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relações
    offer = relationship("OfferModel", back_populates="assets")


# ═══════════════════════════════════════════════════════════════════════════
# FUNÇÕES DE ACESSO AO BANCO
# ═══════════════════════════════════════════════════════════════════════════

def create_offer(niche: str, keyword: str) -> dict:
    """Cria um novo modelo de oferta."""
    db = SessionLocal()
    try:
        offer_id = str(uuid.uuid4())
        slug = f"offer-{keyword.lower().replace(' ', '-')[:30]}"
        
        offer = OfferModel(
            id=offer_id,
            slug=slug,
            niche=niche,
            keyword=keyword,
            status="draft"
        )
        db.add(offer)
        db.commit()
        db.refresh(offer)
        
        return {
            "id": offer.id,
            "slug": offer.slug,
            "niche": offer.niche,
            "keyword": offer.keyword,
            "status": offer.status,
            "created_at": offer.created_at.isoformat() if offer.created_at else None
        }
    finally:
        db.close()


def get_offer(offer_id: str) -> dict:
    """Retorna um modelo de oferta completo."""
    db = SessionLocal()
    try:
        offer = db.query(OfferModel).filter(OfferModel.id == offer_id).first()
        if not offer:
            return None
        
        result = {
            "id": offer.id,
            "slug": offer.slug,
            "niche": offer.niche,
            "keyword": offer.keyword,
            "angle": offer.angle,
            "mechanism": offer.mechanism,
            "promise": offer.promise,
            "price_cents": offer.price_cents,
            "avatar_1": {
                "prompt": offer.avatar_1_prompt,
                "url": offer.avatar_1_url
            },
            "avatar_2": {
                "prompt": offer.avatar_2_prompt,
                "url": offer.avatar_2_url
            },
            "mascot": {
                "prompt": offer.mascot_prompt,
                "url": offer.mascot_url
            },
            "headlines": offer.headlines,
            "body_long": offer.body_long,
            "body_short": offer.body_short,
            "ctas": offer.ctas,
            "status": offer.status,
            "conversion_score": offer.conversion_score,
            "seo_score": offer.seo_score,
            "created_at": offer.created_at.isoformat() if offer.created_at else None,
            "updated_at": offer.updated_at.isoformat() if offer.updated_at else None
        }
        
        # Adiciona investigação
        investigation = db.query(OfferInvestigation).filter(OfferInvestigation.offer_id == offer_id).first()
        if investigation:
            result["investigation"] = {
                "id": investigation.id,
                "status": investigation.status,
                "facebook_ads": investigation.facebook_ads,
                "facebook_patterns": investigation.facebook_patterns,
                "google_keywords": investigation.google_keywords,
                "google_backlinks": investigation.google_backlinks,
                "google_content": investigation.google_content,
                "created_at": investigation.created_at.isoformat() if investigation.created_at else None
            }
        
        # Adiciona keywords
        keywords = db.query(OfferKeyword).filter(OfferKeyword.offer_id == offer_id).all()
        result["keywords"] = [
            {
                "id": k.id,
                "keyword": k.keyword,
                "search_volume": k.search_volume,
                "difficulty": k.difficulty,
                "intent": k.intent
            }
            for k in keywords
        ]
        
        # Adiciona backlinks
        backlinks = db.query(OfferBacklink).filter(OfferBacklink.offer_id == offer_id).all()
        result["backlinks"] = [
            {
                "id": b.id,
                "domain": b.domain,
                "url": b.url,
                "relevance": b.relevance,
                "link_type": b.link_type
            }
            for b in backlinks
        ]
        
        return result
    finally:
        db.close()


def list_offers(limit: int = 50) -> list:
    """Lista ofertas (mais recentes primeiro)."""
    db = SessionLocal()
    try:
        offers = db.query(OfferModel).order_by(OfferModel.created_at.desc()).limit(limit).all()
        return [
            {
                "id": o.id,
                "slug": o.slug,
                "niche": o.niche,
                "keyword": o.keyword,
                "status": o.status,
                "conversion_score": o.conversion_score,
                "seo_score": o.seo_score,
                "created_at": o.created_at.isoformat() if o.created_at else None
            }
            for o in offers
        ]
    finally:
        db.close()


def update_offer(offer_id: str, **kwargs) -> bool:
    """Atualiza campos do modelo de oferta."""
    db = SessionLocal()
    try:
        offer = db.query(OfferModel).filter(OfferModel.id == offer_id).first()
        if not offer:
            return False
        
        for key, value in kwargs.items():
            if hasattr(offer, key):
                setattr(offer, key, value)
        
        db.commit()
        return True
    finally:
        db.close()


def delete_offer(offer_id: str) -> bool:
    """Remove uma oferta e seus dados relacionados."""
    db = SessionLocal()
    try:
        offer = db.query(OfferModel).filter(OfferModel.id == offer_id).first()
        if not offer:
            return False
        
        # Remove relações
        db.query(OfferInvestigation).filter(OfferInvestigation.offer_id == offer_id).delete()
        db.query(OfferKeyword).filter(OfferKeyword.offer_id == offer_id).delete()
        db.query(OfferBacklink).filter(OfferBacklink.offer_id == offer_id).delete()
        db.query(OfferAsset).filter(OfferAsset.offer_id == offer_id).delete()
        
        db.delete(offer)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"[OfferModels] Erro ao deletar oferta: {e}")
        return False
    finally:
        db.close()


def save_investigation(offer_id: str, data: dict) -> str:
    """Salva ou atualiza a investigação de uma oferta."""
    db = SessionLocal()
    try:
        investigation = db.query(OfferInvestigation).filter(OfferInvestigation.offer_id == offer_id).first()
        
        if investigation:
            # Atualiza existente
            investigation.facebook_ads = data.get("facebook_ads")
            investigation.facebook_patterns = data.get("facebook_patterns")
            investigation.google_keywords = data.get("google_keywords")
            investigation.google_backlinks = data.get("google_backlinks")
            investigation.google_content = data.get("google_content")
            investigation.status = data.get("status", "completed")
            investigation.completed_at = datetime.utcnow()
        else:
            # Cria novo
            investigation = OfferInvestigation(
                id=str(uuid.uuid4()),
                offer_id=offer_id,
                keyword=data.get("keyword"),
                niche=data.get("niche"),
                facebook_ads = data.get("facebook_ads"),
                facebook_patterns = data.get("facebook_patterns"),
                google_keywords = data.get("google_keywords"),
                google_backlinks = data.get("google_backlinks"),
                google_content = data.get("google_content"),
                status=data.get("status", "completed")
            )
            db.add(investigation)
        
        db.commit()
        return investigation.id
    finally:
        db.close()


def save_keywords(offer_id: str, keywords: list) -> int:
    """Salva keywords SEO para uma oferta."""
    db = SessionLocal()
    try:
        # Remove keywords antigas
        db.query(OfferKeyword).filter(OfferKeyword.offer_id == offer_id).delete()
        
        # Adiciona novas
        for kw in keywords:
            keyword = OfferKeyword(
                id=str(uuid.uuid4()),
                offer_id=offer_id,
                keyword=kw.get("keyword"),
                search_volume=kw.get("search_volume"),
                difficulty=kw.get("difficulty"),
                intent=kw.get("intent")
            )
            db.add(keyword)
        
        db.commit()
        return len(keywords)
    finally:
        db.close()


def save_backlinks(offer_id: str, backlinks: list) -> int:
    """Salva backlinks potenciais para uma oferta."""
    db = SessionLocal()
    try:
        # Remove backlinks antigos
        db.query(OfferBacklink).filter(OfferBacklink.offer_id == offer_id).delete()
        
        # Adiciona novos
        for bl in backlinks:
            backlink = OfferBacklink(
                id=str(uuid.uuid4()),
                offer_id=offer_id,
                domain=bl.get("domain"),
                url=bl.get("url"),
                relevance=bl.get("relevance"),
                link_type=bl.get("type")
            )
            db.add(backlink)
        
        db.commit()
        return len(backlinks)
    finally:
        db.close()


def save_asset(offer_id: str, slot: str, data: dict) -> str:
    """Salva ou atualiza um asset de uma oferta."""
    db = SessionLocal()
    try:
        asset = db.query(OfferAsset).filter(
            OfferAsset.offer_id == offer_id,
            OfferAsset.slot == slot
        ).first()
        
        if asset:
            # Atualiza existente
            asset.url = data.get("url")
            asset.prompt = data.get("prompt")
            asset.width = data.get("width")
            asset.height = data.get("height")
            asset.provider = data.get("provider")
            asset.updated_at = datetime.utcnow()
        else:
            # Cria novo
            asset = OfferAsset(
                id=str(uuid.uuid4()),
                offer_id=offer_id,
                slot=slot,
                url=data.get("url"),
                prompt=data.get("prompt"),
                width=data.get("width"),
                height=data.get("height"),
                provider=data.get("provider")
            )
            db.add(asset)
        
        db.commit()
        return asset.id
    finally:
        db.close()


def get_assets(offer_id: str) -> list:
    """Retorna todos os assets de uma oferta."""
    db = SessionLocal()
    try:
        assets = db.query(OfferAsset).filter(OfferAsset.offer_id == offer_id).all()
        return [
            {
                "id": a.id,
                "slot": a.slot,
                "url": a.url,
                "prompt": a.prompt,
                "width": a.width,
                "height": a.height,
                "provider": a.provider,
                "created_at": a.created_at.isoformat() if a.created_at else None,
                "updated_at": a.updated_at.isoformat() if a.updated_at else None
            }
            for a in assets
        ]
    finally:
        db.close()
