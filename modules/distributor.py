"""
Distributor — Distribuição automática de conteúdo do Dezafira.

Plataformas suportadas:
  📧 Email (Resend) — newsletter automática
  📌 Pinterest (API v5) — pins automáticos
  📸 Instagram (Graph API) — posts automáticos
  🎵 TikTok (Content Posting API) — vídeos automáticos
  🐦 Twitter/X (API) — tweets automáticos

Custo: $0 (tudo gratuito via APIs)
"""

import os
import json
import asyncio
from datetime import datetime
from typing import Optional, List
from pathlib import Path

RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
RESEND_FROM_EMAIL = os.environ.get("RESEND_FROM_EMAIL", "newsletter@dezafira.com")
RESEND_FROM_NAME = os.environ.get("RESEND_FROM_NAME", "Dezafira")
OBSCURA_WS_URL = os.environ.get("OBSCURA_WS_URL", "ws://localhost:9222")

CONFIG_DIR = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) / "data"
CONFIG_FILE = CONFIG_DIR / "social_config.json"
HISTORY_FILE = CONFIG_DIR / "social_history.json"

def _load_config():
    CONFIG_DIR.mkdir(exist_ok=True)
    if CONFIG_FILE.exists():
        try: return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except: return {}
    return {}

def _save_config(cfg):
    CONFIG_DIR.mkdir(exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")

def _load_history():
    CONFIG_DIR.mkdir(exist_ok=True)
    if HISTORY_FILE.exists():
        try: return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
        except: return []
    return []

def _save_history(posts):
    CONFIG_DIR.mkdir(exist_ok=True)
    HISTORY_FILE.write_text(json.dumps(posts, indent=2, ensure_ascii=False), encoding="utf-8")

def _add_to_history(post):
    history = _load_history()
    history.insert(0, post)
    history = history[:100]
    _save_history(history)

async def send_email(to, subject, html, from_email=None, from_name=None):
    if not RESEND_API_KEY: return {"success": False, "error": "RESEND_API_KEY nao configurado"}
    try:
        import httpx
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post("https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"},
                json={"from": f"{from_name or RESEND_FROM_NAME} <{from_email or RESEND_FROM_EMAIL}>", "to": [to], "subject": subject, "html": html})
            data = r.json()
            if r.status_code == 200 and data.get("id"):
                _add_to_history({"platform": "email", "text": subject[:200], "link": "", "platform_post_id": data["id"], "status": "ok", "created_at": datetime.now().isoformat()})
                return {"success": True, "id": data["id"]}
            return {"success": False, "error": data.get("message", "Falha no envio")}
    except Exception as e: return {"success": False, "error": str(e)}

async def post_to_pinterest(title, description, image_url, link, board_id=None, blog_post_id=None):
    cfg = _load_config(); pcfg = cfg.get("pinterest", {})
    token = pcfg.get("token", ""); target_board = board_id or pcfg.get("board_id", "")
    if not token: return {"success": False, "error": "Pinterest Access Token nao configurado"}
    if not target_board: return {"success": False, "error": "Pinterest Board ID nao configurado"}
    try:
        import httpx
        async with httpx.AsyncClient(timeout=30) as client:
            payload = {"title": title[:100], "link": link, "description": description[:500], "board_id": target_board}
            if image_url: payload["media_source"] = {"source_type": "image_url", "url": image_url}
            r = await client.post("https://api.pinterest.com/v5/pins",
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"}, json=payload)
            data = r.json()
            if r.status_code in (200, 201) and data.get("id"):
                _add_to_history({"platform": "pinterest", "text": title, "image_url": image_url, "link": link, "platform_post_id": data["id"], "blog_post_id": blog_post_id, "status": "ok", "created_at": datetime.now().isoformat()})
                return {"success": True, "pin_id": data["id"]}
            return {"success": False, "error": data.get("message", str(data))}
    except Exception as e: return {"success": False, "error": str(e)}

async def post_to_instagram(image_url, caption, hashtags=None):
    cfg = _load_config(); icfg = cfg.get("instagram", {})
    token = icfg.get("token", ""); business_id = icfg.get("business_id", "")
    if not token: return {"success": False, "error": "Instagram Access Token nao configurado"}
    if not business_id: return {"success": False, "error": "Instagram Business Account ID nao configurado"}
    if hashtags: caption = caption + "\n\n" + " ".join(f"#{h.lstrip('#')}" for h in hashtags)
    try:
        import httpx
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(f"https://graph.facebook.com/v18.0/{business_id}/media",
                headers={"Content-Type": "application/json"},
                json={"image_url": image_url, "caption": caption[:2200], "access_token": token})
            data = r.json(); container_id = data.get("id")
            if not container_id: return {"success": False, "error": data.get("error", {}).get("message", "Falha ao criar container")}
            await asyncio.sleep(5)
            for _ in range(10):
                r2 = await client.get(f"https://graph.facebook.com/v18.0/{container_id}", params={"fields": "status_code", "access_token": token})
                if r2.json().get("status_code") == "FINISHED": break
                await asyncio.sleep(3)
            r3 = await client.post(f"https://graph.facebook.com/v18.0/{business_id}/media_publish",
                headers={"Content-Type": "application/json"}, json={"creation_id": container_id, "access_token": token})
            data3 = r3.json(); post_id = data3.get("id")
            if post_id:
                _add_to_history({"platform": "instagram", "text": caption[:200], "image_url": image_url, "platform_post_id": post_id, "status": "ok", "created_at": datetime.now().isoformat()})
                return {"success": True, "post_id": post_id}
            return {"success": False, "error": data3.get("error", {}).get("message", "Falha ao publicar")}
    except Exception as e: return {"success": False, "error": str(e)}

async def post_to_tiktok(video_path=None, image_url=None, caption="", hashtags=None):
    cfg = _load_config(); tcfg = cfg.get("tiktok", {}); token = tcfg.get("token", "")
    if not token: return {"success": False, "error": "TikTok Access Token nao configurado"}
    hashtag_text = " ".join(f"#{h.lstrip('#')}" for h in (hashtags or []))
    full_caption = f"{caption} {hashtag_text}".strip()
    try:
        import httpx
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post("https://open.tiktokapis.com/v2/post/publish/content/init/",
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json={"post_info": {"title": full_caption[:150], "privacy_level": "PUBLIC_TO_EVERYONE"},
                      "source_info": {"source": "FILE_UPLOAD", "video_info": {"source": "FILE_UPLOAD", "images": [{"image_url": image_url}] if image_url else []}}})
            data = r.json().get("data", {}); publish_id = data.get("publish_id")
            if publish_id:
                _add_to_history({"platform": "tiktok", "text": full_caption[:200], "image_url": image_url, "platform_post_id": publish_id, "status": "ok", "created_at": datetime.now().isoformat()})
                return {"success": True, "publish_id": publish_id}
            return {"success": False, "error": r.json().get("error", {}).get("message", "Falha")}
    except Exception as e: return {"success": False, "error": str(e)}

async def post_to_twitter(text, media_paths=None, blog_post_id=None):
    TWITTER_API_KEY = os.environ.get("TWITTER_API_KEY", "")
    TWITTER_ACCESS_TOKEN = os.environ.get("TWITTER_ACCESS_TOKEN", "")
    if not all([TWITTER_API_KEY, TWITTER_ACCESS_TOKEN]): return {"success": False, "error": "Twitter API keys nao configuradas"}
    try:
        import tweepy
        auth = tweepy.OAuth1UserHandler(TWITTER_API_KEY, os.environ.get("TWITTER_API_SECRET", ""), TWITTER_ACCESS_TOKEN, os.environ.get("TWITTER_ACCESS_SECRET", ""))
        api = tweepy.API(auth)
        if media_paths:
            media_ids = []
            for path in media_paths[:4]:
                if os.path.exists(path): media = api.media_upload(path); media_ids.append(media.media_id_string)
            tweet = api.update_status(status=text, media_ids=media_ids)
        else: tweet = api.update_status(status=text)
        _add_to_history({"platform": "twitter", "text": text[:200], "platform_post_id": str(tweet.id), "blog_post_id": blog_post_id, "status": "ok", "created_at": datetime.now().isoformat()})
        return {"success": True, "id": str(tweet.id)}
    except Exception as e: return {"success": False, "error": str(e)}

def save_social_config(platform, token, **kwargs):
    cfg = _load_config()
    if platform not in cfg: cfg[platform] = {}
    cfg[platform]["token"] = token; cfg[platform]["updated_at"] = datetime.now().isoformat()
    for k, v in kwargs.items():
        if v: cfg[platform][k] = v
    _save_config(cfg); return {"success": True}

def get_social_status():
    cfg = _load_config(); history = _load_history()
    platforms = {}
    for p in ["pinterest", "instagram", "tiktok"]:
        pcfg = cfg.get(p, {})
        platforms[p] = {"configured": bool(pcfg.get("token")), "has_board": bool(pcfg.get("board_id")) if p == "pinterest" else None, "has_business_id": bool(pcfg.get("business_id")) if p == "instagram" else None}
    stats = {"total_posts": len(history), "pinterest": sum(1 for h in history if h.get("platform") == "pinterest"), "instagram": sum(1 for h in history if h.get("platform") == "instagram"), "tiktok": sum(1 for h in history if h.get("platform") == "tiktok")}
    return {"platforms": platforms, "stats": stats}

def get_social_history(): return _load_history()

def get_platform_status():
    cfg = _load_config()
    return {
        "email": {"configured": bool(RESEND_API_KEY), "provider": "Resend"},
        "pinterest": {"configured": bool(cfg.get("pinterest", {}).get("token")), "provider": "Pinterest API v5"},
        "instagram": {"configured": bool(cfg.get("instagram", {}).get("token")), "provider": "Instagram Graph API"},
        "tiktok": {"configured": bool(cfg.get("tiktok", {}).get("token")), "provider": "TikTok Content Posting API"},
        "twitter": {"configured": bool(os.environ.get("TWITTER_API_KEY", "")), "provider": "Tweepy"},
    }


def _plataformas_ativas():
    """Retorna as plataformas de distribuição de artigos configuradas."""
    cfg = _load_config()
    pinterest_cfg = cfg.get("pinterest", {})
    return {
        "pinterest": bool(pinterest_cfg.get("token") and pinterest_cfg.get("board_id")),
        "twitter": bool(os.environ.get("TWITTER_API_KEY", "") and os.environ.get("TWITTER_ACCESS_TOKEN", "")),
    }


def _post_ja_distribuido(post_id: str, platform: str) -> bool:
    """True se o artigo já foi distribuído com sucesso nessa plataforma."""
    history = _load_history()
    return any(
        h.get("blog_post_id") == post_id and h.get("platform") == platform and h.get("status") == "ok"
        for h in history
    )


def _link_publico_do_post(p: dict) -> str:
    """URL pública canônica do viewer: https://dezafira.com.br/blog/{slug}?post={id}
    (não usar site_url como raiz: o seed grava path tipo .../oreino)."""
    slug = p.get("slug") or p.get("id") or ""
    return f"https://dezafira.com.br/blog/{slug}?post={p.get('id')}"


async def _distribuir_post(p: dict, ativas: dict = None) -> dict:
    """Distribui UM artigo (dict do banco) para as plataformas ativas.

    Returns:
        {"post_id", "title", "link", "distribuidos", "falhas", "detalhes": [...]}
    """
    cfg = _load_config()
    pinterest_cfg = cfg.get("pinterest", {})
    ativas = ativas or _plataformas_ativas()

    post_id = p.get("id")
    title = p.get("title") or ""
    post_link = _link_publico_do_post(p)
    image = p.get("featured_image_url") or ""
    description = (p.get("excerpt") or title)[:300]

    distribuidos = 0
    falhas = 0
    detalhes = []

    # Pinterest — pin com imagem + link do artigo
    if ativas.get("pinterest"):
        if _post_ja_distribuido(post_id, "pinterest"):
            detalhes.append({"platform": "pinterest", "ok": True, "skipped": True, "message": "Já distribuído"})
        else:
            try:
                r = await post_to_pinterest(
                    title=title[:100],
                    description=description,
                    image_url=image,
                    link=post_link,
                    board_id=pinterest_cfg.get("board_id"),
                    blog_post_id=post_id,
                )
                if r.get("success"):
                    distribuidos += 1
                    detalhes.append({"platform": "pinterest", "ok": True})
                else:
                    falhas += 1
                    detalhes.append({"platform": "pinterest", "ok": False, "error": r.get("error", "")})
            except Exception as e:
                falhas += 1
                detalhes.append({"platform": "pinterest", "ok": False, "error": str(e)})

    # Twitter/X — tweet com link (imagem opcional: o link mesmo já dá preview)
    if ativas.get("twitter"):
        if _post_ja_distribuido(post_id, "twitter"):
            detalhes.append({"platform": "twitter", "ok": True, "skipped": True, "message": "Já distribuído"})
        else:
            try:
                # Margem segura para o limite de 280 chars (URL conta ~23 via t.co)
                tweet_text = f"{title[:200]} {post_link}"
                r = await post_to_twitter(tweet_text, blog_post_id=post_id)
                if r.get("success"):
                    distribuidos += 1
                    detalhes.append({"platform": "twitter", "ok": True})
                else:
                    falhas += 1
                    detalhes.append({"platform": "twitter", "ok": False, "error": r.get("error", "")})
            except Exception as e:
                falhas += 1
                detalhes.append({"platform": "twitter", "ok": False, "error": str(e)})

    return {
        "post_id": post_id,
        "title": title[:60],
        "link": post_link,
        "distribuidos": distribuidos,
        "falhas": falhas,
        "detalhes": detalhes,
    }


async def distribuir_artigo_especifico(post_id: str) -> dict:
    """Distribui UM artigo específico (pelo ID no banco) para as plataformas ativas.

    Usado pelo botão "📤 Distribuir" no painel de Blogs.

    Returns:
        {"success": bool, "distribuidos": int, "falhas": int, "detalhes": [...]}
    """
    ativas = _plataformas_ativas()
    if not any(ativas.values()):
        return {"success": False, "error": "Nenhuma plataforma social configurada (Pinterest com board_id ou Twitter com TWITTER_*)."}

    try:
        from modules.database import get_db_blog_post
        p = get_db_blog_post(post_id)
    except Exception as e:
        return {"success": False, "error": f"Erro ao buscar artigo: {str(e)}"}

    if not p:
        return {"success": False, "error": "Artigo não encontrado"}
    if not p.get("featured_image_url"):
        return {"success": False, "error": "Artigo sem imagem de destaque — gere a imagem antes de distribuir"}

    result = await _distribuir_post(p, ativas)
    return {
        "success": True,
        "distribuidos": result["distribuidos"],
        "falhas": result["falhas"],
        "detalhes": result["detalhes"],
        "title": result["title"],
        "link": result["link"],
    }


async def distribuir_artigos_do_blog(channel_id: str, limit: int = 3) -> dict:
    """Distribui os artigos publicados mais recentes de um blog para as
    plataformas sociais configuradas (Pinterest e Twitter/X).

    Usado no fim da Fábrica de Blogs (Fase 5 — Entrega). Cada artigo
    distribuído com sucesso é registrado no histórico social.

    Returns:
        {"distribuidos": int, "falhas": int, "detalhes": [{"title", "platform", "ok", "error"}]}
    """
    ativas = _plataformas_ativas()
    if not any(ativas.values()):
        return {"distribuidos": 0, "falhas": 0, "detalhes": [], "message": "Nenhuma plataforma social configurada (Pinterest com board_id ou Twitter com TWITTER_*)."}

    # Busca os artigos publicados do canal com imagem de destaque
    posts = []
    try:
        from modules.database import get_db_blog_posts
        raw = get_db_blog_posts(channel_id=channel_id, limit=limit * 4)
        posts = [p for p in raw if p.get("status") == "published" and p.get("featured_image_url")][:limit]
    except Exception as e:
        return {"distribuidos": 0, "falhas": 0, "detalhes": [], "error": str(e)}

    distribuidos = 0
    falhas = 0
    detalhes = []
    for p in posts:
        r = await _distribuir_post(p, ativas)
        distribuidos += r["distribuidos"]
        falhas += r["falhas"]
        for d in r["detalhes"]:
            detalhes.append({"title": r["title"], **d})

    return {"distribuidos": distribuidos, "falhas": falhas, "detalhes": detalhes}


async def distribuir_artigos_recentes(por_canal: int = 2, apenas_nao_distribuidos: bool = True) -> dict:
    """Distribui artigos recentes de TODOS os canais de blog ativos.

    Usado pelo agendador automático (cron/intervalo) e por trigger manual.

    Returns:
        {"distribuidos": int, "falhas": int, "canais": int, "detalhes": [...]}
    """
    ativas = _plataformas_ativas()
    if not any(ativas.values()):
        return {"distribuidos": 0, "falhas": 0, "canais": 0, "detalhes": [], "message": "Nenhuma plataforma social configurada."}

    try:
        from modules.database import get_db_blog_channels, get_db_blog_posts
        canais = [c for c in get_db_blog_channels() if c.get("status") == "active"]
    except Exception as e:
        return {"distribuidos": 0, "falhas": 0, "canais": 0, "detalhes": [], "error": str(e)}

    distribuidos = 0
    falhas = 0
    detalhes = []
    for chan in canais:
        chan_id = chan.get("id")
        try:
            raw = get_db_blog_posts(channel_id=chan_id, limit=por_canal * 6)
            posts = [p for p in raw if p.get("status") == "published" and p.get("featured_image_url")][:por_canal]
        except Exception:
            posts = []

        for p in posts:
            if apenas_nao_distribuidos and _post_ja_distribuido(p.get("id"), "pinterest") and _post_ja_distribuido(p.get("id"), "twitter"):
                continue
            r = await _distribuir_post(p, ativas)
            distribuidos += r["distribuidos"]
            falhas += r["falhas"]
            for d in r["detalhes"]:
                detalhes.append({"title": r["title"], "channel": chan.get("name"), **d})

    return {"distribuidos": distribuidos, "falhas": falhas, "canais": len(canais), "detalhes": detalhes}
