"""
Landing Templates — Registry de templates de landing do Blueprint.

Cada template monta uma lista de blocos NO MESMO FORMATO que o
DezafiraClube valida em `src/lib/landing-blocks.ts` / `landing-pages.ts`
(tipos: hero, product-showcase, posts-grid, pricing, faq, cta, video...).

A publicação usa a CLI API do Clube (`POST /api/cli/landing-pages` com
`Authorization: Bearer CLI_TOKEN`), então NOVO template aqui = zero mudança
no Clube — ele só recebe blocos que já sabe renderizar.
"""

from __future__ import annotations

from typing import Any, Dict, List


def _uid(prefix: str) -> str:
    import uuid
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def _kit_colors(config: Dict[str, Any], defaults: Dict[str, str]) -> Dict[str, str]:
    """Extrai as cores do brand kit do blueprint (mesmo kit das capas Agnes).
    Aceita o formato canônico {colors: {...}} e o plano {primary_color, accent_color}."""
    bk = config.get("brand_kit") or {}
    kit = bk.get("colors") or {}
    if not kit:
        kit = {
            "bg": bk.get("accent_color") or bk.get("primary_color"),
            "bg2": bk.get("accent_color"),
            "accent": bk.get("primary_color"),
            "text": bk.get("text_color"),
            "muted": bk.get("muted_color"),
        }
    return {k: kit.get(k, defaults[k]) for k in defaults}


def _kit_fonts(config: Dict[str, Any]) -> Dict[str, str]:
    bk = config.get("brand_kit") or {}
    return {
        "font": bk.get("font") or "",
        "font_sans": bk.get("font_sans") or "",
    }


def _bundle_offer(content: Dict[str, Any], config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Quando o combo/pacote está habilitado, devolve a oferta do bundle:
    slug/url, nome, preço com desconto, preço original (soma) e CTA dedicado.
    Retorna None quando desabilitado."""
    fund = content.get("fundacao") or {}
    funil = content.get("funil") or {}
    bundle_cfg = funil.get("bundle") or {}
    if not bundle_cfg.get("enabled"):
        return None

    main_slug = fund.get("slug") or config.get("slug") or "produto"
    slug = bundle_cfg.get("slug") or f"{main_slug}-pacote"
    base = config.get("price_cents") or 0
    if bundle_cfg.get("include_upsell") and funil.get("upsell"):
        base += funil["upsell"].get("price_cents") or 0
    if bundle_cfg.get("include_downsell") and funil.get("downsell"):
        base += funil["downsell"].get("price_cents") or 0
    original = base
    price = int(base * (1 - (bundle_cfg.get("discount_pct") or 0) / 100.0))
    return {
        "slug": slug,
        "url": f"/product/{slug}",
        "name": bundle_cfg.get("name") or f"Pacote {fund.get('name') or config.get('name') or 'Produto'}",
        "price_cents": price,
        "original_cents": original,
        "cta": "Quero o pacote completo",
    }


# ── Templates ─────────────────────────────────────────────────────────────────

def build_dezafira_template(content: Dict[str, Any], config: Dict[str, Any],
                            assets: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Template padrão "Dezafira":
      hero → product-showcase → video (opcional) → posts-grid (opcional)
      → faq → cta

    content: blueprint content (fundacao, conteudo/artifacts, funil)
    config:  blueprint config (slug override, youtube, category...)
    assets:  blueprint assets (landing_hero, landing_offer...)
    """
    fund = content.get("fundacao") or {}
    conteudo = content.get("conteudo") or {}
    funil = content.get("funil") or {}
    cfg = config or {}

    name = fund.get("name") or cfg.get("name") or "Produto"
    slug = fund.get("slug") or cfg.get("slug") or "produto"
    product_url = f"/product/{slug}"
    description = fund.get("description") or ""
    pitch = fund.get("pitch") or description
    cta_primary = fund.get("cta_primary") or "Quero acesso agora"
    cta_secondary = fund.get("cta_secondary") or "Ver conteúdo"

    # Combo/pacote nativo: se habilitado, a landing promove o bundle com CTA
    # dedicado e preço original riscado (compareAtPrice = soma dos itens)
    bundle = _bundle_offer(content, cfg)
    bundle_price = None
    bundle_original = None
    if bundle:
        slug = bundle["slug"]
        product_url = bundle["url"]
        name = bundle["name"]
        cta_primary = bundle["cta"]
        bundle_price = bundle["price_cents"]
        bundle_original = bundle["original_cents"]
        description = (
            f"Pacote completo com todos os produtos da oferta ({name}). "
            "Tudo incluso em um único pagamento — aproveite o desconto."
        )

    # Brand kit do blueprint → cores/fontes da landing (mesmo kit das capas)
    cols = _kit_colors(cfg, {"bg": "#0b1220", "bg2": "#16233d", "accent": "#38bdf8", "text": "#ffffff", "muted": "#8aa2c0"})
    c_bg, c_bg2, c_accent, c_text, c_muted = cols["bg"], cols["bg2"], cols["accent"], cols["text"], cols["muted"]
    fonts = _kit_fonts(cfg)

    hero_img = (assets.get("landing_hero") or {}).get("url") or ""
    offer_img = (assets.get("landing_offer") or {}).get("url") or ""

    # Vídeo da landing: VSL nativa (MP4 gerado → bloco `vsl` com headlines A/B/C)
    # ou fallback de YouTube (config.youtube_video_url → bloco `video` iframe)
    vsl_info = content.get("vsl") or {}
    vsl_mp4 = vsl_info.get("video_url") or ""
    youtube = cfg.get("youtube_video_url") or ""
    artifacts = conteudo.get("artifacts") or []
    blog_posts = [a for a in artifacts if a.get("format") == "blog"]
    post_slugs = [p.get("slug") for p in blog_posts if p.get("slug")][:6]

    blocks: List[Dict[str, Any]] = []

    # 1. Hero
    hero_props: Dict[str, Any] = {
        "eyebrow": "CONTEÚDO PREMIUM",
        "title": name,
        "subtitle": pitch,
        "subtitleColor": "#cbd5e1",
        "primaryText": cta_primary,
        "primaryHref": product_url,
        "secondaryText": cta_secondary,
        "secondaryHref": "/posts",
        "image": hero_img,
        "imageAlt": name,
        "badge": "Novo",
    }
    blocks.append({
        "id": _uid("hero"),
        "type": "hero",
        "styles": {
            "paddingTop": "72px", "paddingBottom": "72px",
            "backgroundColor": c_bg, "textColor": c_text,
            "borderRadius": "24px", "marginBottom": "24px",
        },
        "properties": hero_props,
    })

    # 2. Product showcase
    price = bundle_price if bundle_price is not None else (config.get("price_cents") if config else None)
    compare_price = None
    if bundle_original is not None:
        compare_price = f"R$ {bundle_original / 100:.2f}".replace(".", ",")
    blocks.append({
        "id": _uid("product"),
        "type": "product-showcase",
        "styles": {
            "paddingTop": "32px", "paddingBottom": "32px",
            "backgroundColor": c_bg2, "textColor": c_text,
            "borderRadius": "24px", "marginBottom": "24px",
        },
        "properties": {
            "productSlug": slug,
            "name": name,
            "description": description,
            "bullets": [
                "Acesso simples e imediato",
                "Conteúdo prático e atualizado",
                "Compra segura",
            ],
            "price": f"R$ {(price or 0) / 100:.2f}".replace(".", ",") if price is not None else "",
            "compareAtPrice": compare_price,
            "image": offer_img,
            "imageAlt": name,
            "buttonText": cta_primary,
            "buttonHref": product_url,
            "eyebrow": "Oferta em destaque",
        },
    })

    # 3. Vídeo (opcional): VSL nativa do Clube (MP4 + player com A/B/C e
    # analytics) quando o blueprint gerou VSL; senão YouTube (iframe) se
    # configurado. O player do Clube consome vslId/src/thumbnail/headline_a..c.
    if vsl_mp4 and vsl_info.get("vsl_id"):
        blocks.append({
            "id": _uid("vsl"),
            "type": "vsl",
            "styles": {"marginBottom": "24px"},
            "properties": {
                "vslId": vsl_info.get("vsl_id"),
                "src": vsl_mp4,
                "thumbnail": vsl_info.get("thumbnail_url") or "",
                "headline_a": vsl_info.get("headline_a") or "",
                "headline_b": vsl_info.get("headline_b") or "",
                "headline_c": vsl_info.get("headline_c") or "",
            },
        })
    elif youtube:
        blocks.append({
            "id": _uid("video"),
            "type": "video",
            "styles": {"marginBottom": "24px"},
            "properties": {"src": youtube},
        })

    # 4. Posts grid (opcional — se o blueprint gerou blog)
    if post_slugs:
        blocks.append({
            "id": _uid("posts"),
            "type": "posts-grid",
            "styles": {
                "paddingTop": "40px", "paddingBottom": "40px",
                "backgroundColor": c_bg, "textColor": c_text,
                "borderRadius": "24px", "marginBottom": "24px",
            },
            "properties": {
                "title": "Conteúdos para continuar aprendendo",
                "subtitle": "Selecione até seis posts publicados.",
                "posts": post_slugs,
            },
        })

    # 5. FAQ
    faq_items = fund.get("faq") or [
        {"q": "Como recebo o acesso?", "a": "Na hora, após a confirmação do pagamento."},
        {"q": "E se eu não gostar?", "a": "Você pode pedir reembolso."},
        {"q": "Por quanto tempo tenho acesso?", "a": "Acesso vitalício ao conteúdo."},
    ]
    blocks.append({
        "id": _uid("faq"),
        "type": "faq",
        "styles": {"marginBottom": "16px", "textAlign": "left"},
        "properties": {"title": "Perguntas frequentes", "items": faq_items},
    })

    # 6. CTA final
    blocks.append({
        "id": _uid("cta"),
        "type": "cta",
        "content": f"Garanta seu acesso a {name}",
        "styles": {
            "paddingTop": "48px", "paddingBottom": "48px",
            "backgroundColor": c_bg2, "textColor": c_text,
            "textAlign": "center", "borderRadius": "16px", "marginBottom": "16px",
        },
        "properties": {
            "subtitle": "Oferta disponível por tempo limitado.",
            "buttonText": cta_primary,
            "buttonHref": product_url,
            "buttonBg": c_accent,
            "buttonColor": c_bg,
            "productSlug": slug,
        },
    })

    return blocks


# ── Template "dark-sales" — escuro com foco em venda e urgência ──────────────

def build_dark_sales_template(content: Dict[str, Any], config: Dict[str, Any],
                              assets: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Template "dark-sales": hero com badge de urgência → prova (testimonial)
    → product-showcase (preço + preço de comparação) → FAQ → CTA forte."""
    fund = content.get("fundacao") or {}
    conteudo = content.get("conteudo") or {}
    funil = content.get("funil") or {}
    cfg = config or {}

    name = fund.get("name") or cfg.get("name") or "Produto"
    slug = fund.get("slug") or cfg.get("slug") or "produto"
    bundle = _bundle_offer(content, cfg)
    if bundle:
        slug = bundle["slug"]
        name = bundle["name"]
        cta_primary = bundle["cta"]
    product_url = f"/product/{slug}"
    description = fund.get("description") or ""
    pitch = fund.get("pitch") or description
    cta_primary = cta_primary if bundle else (fund.get("cta_primary") or "Garantir minha vaga agora")

    cols = _kit_colors(cfg, {"bg": "#09090b", "bg2": "#18181b", "accent": "#f59e0b", "text": "#ffffff", "muted": "#a1a1aa"})
    c_bg, c_bg2, c_accent, c_text, c_muted = cols["bg"], cols["bg2"], cols["accent"], cols["text"], cols["muted"]

    hero_img = (assets.get("landing_hero") or {}).get("url") or ""
    offer_img = (assets.get("landing_offer") or {}).get("url") or ""
    if bundle:
        # Combo: preço com desconto + original riscado (soma dos itens)
        price = bundle["price_cents"]
        compare_cents = bundle["original_cents"]
        price_str = f"R$ {price / 100:.2f}".replace(".", ",")
        compare = f"R$ {compare_cents / 100:.2f}".replace(".", ",")
    else:
        price = cfg.get("price_cents")
        price_str = f"R$ {price / 100:.2f}".replace(".", ",") if price else ""
        compare = f"R$ {int(price * 1.6) / 100:.2f}".replace(".", ",") if price else ""

    blocks: List[Dict[str, Any]] = []

    blocks.append({
        "id": _uid("hero"),
        "type": "hero",
        "styles": {
            "paddingTop": "88px", "paddingBottom": "72px",
            "backgroundColor": c_bg, "textColor": c_text,
            "borderRadius": "0px", "marginBottom": "8px",
        },
        "properties": {
            "eyebrow": "⚡ OFERTA POR TEMPO LIMITADO",
            "eyebrowColor": c_accent,
            "title": name,
            "subtitle": pitch,
            "subtitleColor": c_muted,
            "primaryText": cta_primary,
            "primaryHref": product_url,
            "primaryBg": c_accent,
            "image": hero_img,
            "imageAlt": name,
            "badge": "Últimas vagas",
            "badgeColor": c_accent,
        },
    })

    blocks.append({
        "id": _uid("prova"),
        "type": "testimonial",
        "styles": {
            "paddingTop": "40px", "paddingBottom": "40px",
            "backgroundColor": c_bg2, "textColor": c_text,
            "borderRadius": "16px", "marginBottom": "16px",
        },
        "properties": {
            "quote": "Resultado acima do esperado — o conteúdo entrega exatamente o que promete.",
            "author": "Aluno Dezafira",
            "role": "Cliente verificado",
            "stars": 5,
        },
    })

    blocks.append({
        "id": _uid("product"),
        "type": "product-showcase",
        "styles": {
            "paddingTop": "40px", "paddingBottom": "40px",
            "backgroundColor": c_bg, "textColor": c_text,
            "borderRadius": "16px", "marginBottom": "16px",
        },
        "properties": {
            "productSlug": slug,
            "name": name,
            "description": description,
            "bullets": ["Acesso imediato", "Atualizações inclusas", "Suporte prioritário"],
            "price": price_str,
            "compareAtPrice": compare,
            "image": offer_img,
            "imageAlt": name,
            "buttonText": cta_primary,
            "buttonHref": product_url,
            "buttonBg": c_accent,
            "eyebrow": "Oferta de lançamento",
        },
    })

    faq_items = fund.get("faq") or [
        {"q": "Como recebo o acesso?", "a": "Na hora, após a confirmação do pagamento."},
        {"q": "E se eu não gostar?", "a": "Você pode pedir reembolso."},
    ]
    blocks.append({
        "id": _uid("faq"),
        "type": "faq",
        "styles": {"marginBottom": "16px", "textAlign": "left", "backgroundColor": c_bg2, "borderRadius": "16px", "paddingTop": "32px", "paddingBottom": "32px"},
        "properties": {"title": "Perguntas frequentes", "items": faq_items},
    })

    blocks.append({
        "id": _uid("cta"),
        "type": "cta",
        "content": f"Não perca tempo — garanta {name} hoje",
        "styles": {
            "paddingTop": "56px", "paddingBottom": "56px",
            "backgroundColor": c_bg2, "textColor": c_text,
            "textAlign": "center", "borderRadius": "16px", "marginBottom": "16px",
        },
        "properties": {
            "subtitle": "Oferta com desconto válida por tempo limitado.",
            "buttonText": cta_primary,
            "buttonHref": product_url,
            "buttonBg": c_accent,
            "buttonColor": c_bg,
            "productSlug": slug,
        },
    })

    return blocks


# ── Template "clean-soft" — claro, minimalista, foco em confiança ────────────

def build_clean_soft_template(content: Dict[str, Any], config: Dict[str, Any],
                              assets: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Template "clean-soft": visual claro e leve (hero → showcase → posts →
    faq → cta), com tipografia suave e cantos arredondados."""
    fund = content.get("fundacao") or {}
    conteudo = content.get("conteudo") or {}
    cfg = config or {}

    name = fund.get("name") or cfg.get("name") or "Produto"
    slug = fund.get("slug") or cfg.get("slug") or "produto"
    bundle = _bundle_offer(content, cfg)
    bundle_compare = None
    if bundle:
        slug = bundle["slug"]
        name = bundle["name"]
        cta_primary = bundle["cta"]
        bundle_compare = bundle["original_cents"]
    product_url = f"/product/{slug}"
    description = fund.get("description") or ""
    pitch = fund.get("pitch") or description
    cta_primary = cta_primary if bundle else (fund.get("cta_primary") or "Quero acesso")

    cols = _kit_colors(cfg, {"bg": "#f8fafc", "bg2": "#ffffff", "accent": "#0ea5e9", "text": "#0f172a", "muted": "#64748b"})
    c_bg, c_bg2, c_accent, c_text, c_muted = cols["bg"], cols["bg2"], cols["accent"], cols["text"], cols["muted"]

    hero_img = (assets.get("landing_hero") or {}).get("url") or ""
    offer_img = (assets.get("landing_offer") or {}).get("url") or ""
    artifacts = conteudo.get("artifacts") or []
    post_slugs = [p.get("slug") for p in artifacts if p.get("format") == "blog" and p.get("slug")][:6]
    if bundle:
        price = bundle["price_cents"]
    else:
        price = cfg.get("price_cents")
    price_str = f"R$ {price / 100:.2f}".replace(".", ",") if price else ""

    blocks: List[Dict[str, Any]] = []

    blocks.append({
        "id": _uid("hero"),
        "type": "hero",
        "styles": {
            "paddingTop": "64px", "paddingBottom": "64px",
            "backgroundColor": c_bg, "textColor": c_text,
            "borderRadius": "24px", "marginBottom": "20px",
        },
        "properties": {
            "eyebrow": "CONTEÚDO CURADO",
            "eyebrowColor": c_accent,
            "title": name,
            "subtitle": pitch,
            "subtitleColor": c_muted,
            "primaryText": cta_primary,
            "primaryHref": product_url,
            "image": hero_img,
            "imageAlt": name,
        },
    })

    blocks.append({
        "id": _uid("product"),
        "type": "product-showcase",
        "styles": {
            "paddingTop": "32px", "paddingBottom": "32px",
            "backgroundColor": c_bg2, "textColor": c_text,
            "borderRadius": "24px", "marginBottom": "20px",
            "boxShadow": "0 4px 24px rgba(15,23,42,0.06)",
        },
        "properties": {
            "productSlug": slug,
            "name": name,
            "description": description,
            "bullets": ["Conteúdo direto ao ponto", "Feito para iniciantes", "Acesso vitalício"],
            "price": price_str,
            "compareAtPrice": f"R$ {bundle_compare / 100:.2f}".replace(".", ",") if bundle_compare else None,
            "image": offer_img,
            "imageAlt": name,
            "buttonText": cta_primary,
            "buttonHref": product_url,
            "buttonBg": c_accent,
            "buttonColor": c_bg,
            "eyebrow": "Simples e completo",
        },
    })

    if post_slugs:
        blocks.append({
            "id": _uid("posts"),
            "type": "posts-grid",
            "styles": {
                "paddingTop": "36px", "paddingBottom": "36px",
                "backgroundColor": c_bg, "textColor": c_text,
                "borderRadius": "24px", "marginBottom": "20px",
            },
            "properties": {
                "title": "Aprenda mais no blog",
                "subtitle": "Artigos complementares ao produto.",
                "posts": post_slugs,
            },
        })

    faq_items = fund.get("faq") or [
        {"q": "Como recebo o acesso?", "a": "Na hora, após a confirmação do pagamento."},
        {"q": "Por quanto tempo tenho acesso?", "a": "Acesso vitalício ao conteúdo."},
    ]
    blocks.append({
        "id": _uid("faq"),
        "type": "faq",
        "styles": {"marginBottom": "16px", "textAlign": "left", "backgroundColor": c_bg2, "borderRadius": "24px", "paddingTop": "28px", "paddingBottom": "28px"},
        "properties": {"title": "Perguntas frequentes", "items": faq_items},
    })

    blocks.append({
        "id": _uid("cta"),
        "type": "cta",
        "content": f"Comece agora com {name}",
        "styles": {
            "paddingTop": "44px", "paddingBottom": "44px",
            "backgroundColor": c_bg2, "textColor": c_text,
            "textAlign": "center", "borderRadius": "24px", "marginBottom": "16px",
        },
        "properties": {
            "subtitle": "Sem complicação: acesso imediato após a confirmação.",
            "buttonText": cta_primary,
            "buttonHref": product_url,
            "buttonBg": c_accent,
            "buttonColor": c_bg,
            "productSlug": slug,
        },
    })

    return blocks


TEMPLATE_REGISTRY: Dict[str, Any] = {
    "dezafira": build_dezafira_template,
    "dark-sales": build_dark_sales_template,
    "clean-soft": build_clean_soft_template,
}


def build_landing_blocks(template_name: str, content: Dict[str, Any],
                         config: Dict[str, Any], assets: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Constrói os blocos de um template registrado (fallback: dezafira)."""
    builder = TEMPLATE_REGISTRY.get(template_name) or TEMPLATE_REGISTRY["dezafira"]
    return builder(content, config, assets)
