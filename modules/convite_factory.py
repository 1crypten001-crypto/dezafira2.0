"""
MÓDULO: convite_factory.py
DESCRIÇÃO: Fábrica de Convites — transforma o 1Convite em produto da fábrica.

Fluxo (padrão das outras fábricas do DezafiraADM):
  1. apply_branding()   — aplica branding no miniapp 1Convite (paleta, nome, copy)
  2. create_blueprint() — cria o Blueprint do produto (formats=["app"]) com o
                          app_url apontando para o PWA (/app/1convite ou domínio)
  3. publish()          — publica no DezafiraClube via ponte (publish_blueprint)

O produto entregue no Clube usa resource_type="link" com external_link = URL do
PWA — o membro acessa o super app pelo link (domínio dedicado quando o DNS
estiver apontado; fallback: BACKEND_URL/app/1convite).
"""

import json
import logging
from typing import Dict, Optional

from modules.clube_bridge import backend_url
from modules.database import (SessionLocal, MiniApp, create_db_blueprint,
                              get_db_blueprint, update_db_blueprint)

logger = logging.getLogger("convite_factory")

SLUG = "1convite"

# Paleta padrão (nicho espiritual) — sobrescrita pelo branding informado
_DEFAULT_THEME = {
    "primary": "#A78BFA", "accent": "#C4B5FD",
    "gradient": "135deg, #2E1065, #7C3AED",
    "bg": "#090D16", "surface": "#161320",
    "emoji": "✨", "tagline": "Um app sobre o Reino",
}

_DEFAULT_DESCRIPTION = (
    "Super app cristão que integra a Palavra de Deus, interatividade, "
    "ferramentas de IA e criatividade em um só lugar: Bíblia ACF, matriz "
    "diária, trilhas de crescimento, arcade bíblico e a Trilha do Reino."
)


def _app_url(dedicated_domain: Optional[str] = None) -> str:
    """URL pública do PWA: domínio dedicado (se configurado) ou backend/app."""
    if dedicated_domain:
        return f"https://{dedicated_domain}"
    return f"{backend_url()}/app/{SLUG}"


def _theme_from_branding(branding: Dict) -> dict:
    theme = dict(_DEFAULT_THEME)
    theme["tagline"] = branding.get("tagline") or _DEFAULT_THEME["tagline"]
    if branding.get("cor_primaria"):
        theme["primary"] = branding["cor_primaria"]
    if branding.get("cor_acento"):
        theme["accent"] = branding["cor_acento"]
    if branding.get("cor_fundo"):
        theme["bg"] = branding["cor_fundo"]
    if branding.get("emoji"):
        theme["emoji"] = branding["emoji"]
    if branding.get("cor_primaria") and branding.get("cor_acento"):
        theme["gradient"] = f"135deg, {branding.get('gradiente_de', '#2E1065')}, {branding['cor_primaria']}"
    return theme


class ConviteFactory:
    """Fábrica de Convites — branding + blueprint + publicação."""

    @staticmethod
    def apply_branding(branding: Dict) -> Dict:
        """Aplica branding no miniapp 1Convite (paleta, nome, copy, logo)."""
        session = SessionLocal()
        try:
            app = session.query(MiniApp).filter(MiniApp.slug == SLUG).first()
            if not app:
                raise ValueError("Miniapp 1Convite não existe — rode seed_convite.py --register-miniapp")

            nome = branding.get("nome") or "1Convite"
            theme = _theme_from_branding(branding)

            app.app_name = nome
            app.brand_name = branding.get("nome_marca") or nome
            if branding.get("tagline"):
                app.headline = branding["tagline"]
            if branding.get("descricao"):
                app.description = branding["descricao"]
            if branding.get("logo_url"):
                app.logo_url = branding["logo_url"]
            if branding.get("banner_url"):
                app.banner_url = branding["banner_url"]
            app.theme = json.dumps(theme, ensure_ascii=False)
            session.commit()

            return {
                "success": True,
                "slug": SLUG,
                "app_url": f"/app/{SLUG}",
                "app_name": app.app_name,
                "brand_name": app.brand_name,
                "theme": theme,
            }
        finally:
            session.close()

    @staticmethod
    def create_blueprint(branding: Dict) -> Dict:
        """Cria o Blueprint do produto 1Convite (formats=['app'], status=review)."""
        name = branding.get("nome") or "1Convite"
        theme = _theme_from_branding(branding)
        price_cents = int(branding.get("preco_cents") or 0)
        dedicated = branding.get("dominio_dedicado") or "1convite.com.br"
        url = _app_url(dedicated)

        bp = create_db_blueprint(
            name=name,
            theme=theme.get("tagline") or "Espiritual",
            niche="espiritual",
            price_cents=price_cents,
            formats=["app"],
            config={
                "slug": SLUG,
                "app_slug": SLUG,
                "app_url": url,
                "dedicated_domain": dedicated,
                "category": "app",
                "branding": {
                    "theme": theme,
                    "nome_marca": branding.get("nome_marca") or name,
                    "logo_url": branding.get("logo_url"),
                    "banner_url": branding.get("banner_url"),
                    "tagline": theme.get("tagline"),
                },
            },
        )
        if not bp or bp.get("error"):
            raise ValueError(bp.get("error", "Falha ao criar blueprint"))

        # Conteúdo mínimo para o publish_blueprint montar o produto "link"
        update_db_blueprint(
            bp["id"],
            status="review",
            stage="publicacao",
            content={
                "fundacao": {
                    "name": name,
                    "slug": SLUG,
                    "description": branding.get("descricao") or _DEFAULT_DESCRIPTION,
                },
                "conteudo": {
                    "artifacts": [{
                        "format": "app",
                        "status": "completed",
                        "external_link": url,
                    }],
                },
                "funil": {},
            },
        )
        bp = get_db_blueprint(bp["id"])
        logger.info(f"[ConviteFactory] Blueprint criado: {bp['id']} (app_url={url})")
        return {"success": True, "blueprint": bp, "app_url": url}

    @staticmethod
    async def publish(bp_id: str) -> Dict:
        """Publica o blueprint no DezafiraClube via ponte (estágio 6)."""
        from modules.blueprint_engine import publish_blueprint
        bp = get_db_blueprint(bp_id)
        if not bp:
            raise ValueError(f"Blueprint não encontrado: {bp_id}")
        return await publish_blueprint(bp_id)
