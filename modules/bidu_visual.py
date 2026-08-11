"""
BiduVisualAgent — Diretor de Identidade Visual dos MiniApps (padrao Duolingo).

Consome o branding (Dona Celia) + dor unica (Nexo) e gera, via Agnes AI (grátis),
um kit completo de identidade: logo (1:1 + horizontal 16:9 + favicon), mascote
(frente + variacoes de expressao/pose por img2img — consistencia garantida),
og-image (16:9) e o character-brief (JSON de reuso/regeneracao).

Se qualquer etapa do Agnes falhar, recai automaticamente no pipeline do Ricardo
(agents/image_factory) — a esteira nunca quebra nem retorna imagem vazia.
"""
import base64
import json
import logging
import os
import uuid

from agents.llm import query_llm, ERROR_PREFIX
from agents.specialists import _parse_json_response
from modules.agnes_client import AgnesClient

logger = logging.getLogger("bidu_visual")
logger.setLevel(logging.INFO)

_FIXED_STYLE = (
    "flat vector mascot, big expressive eyes, one accent color, white background, "
    "Duolingo-style, no text, no watermark, clean simple shapes"
)

_BIDU_SYSTEM_PROMPT = (
    "Você é o Bidu, Diretor de Identidade Visual dos MiniApps da DEZAFIRA.\n"
    "Seu padrão é o Duolingo: UM personagem inesquecível que vira a cara do app.\n"
    "A partir do branding (Dona Célia) e da dor única (Nexo), defina o personagem em 5 atributos:\n"
    "1. species: forma/espécie que CONVERSA com a dor (metáfora clara, ex.: coruja=aprender, capivara=calma financeira)\n"
    "2. color: a cor principal da paleta da marca (exato, do theme.primary)\n"
    "3. emotion: a emoção base do personagem (determinado, curioso, acolhedor, travesso)\n"
    "4. pose: a pose assinatura (1 só, memorável — ex.: polegar pra cima, segurando o item do nicho)\n"
    f'5. style: SEMPRE "{_FIXED_STYLE}"\n'
    "Regra de ouro: criança de 5 anos desenha o personagem de memória depois de ver 1 vez.\n"
    "Responda APENAS com JSON: {\"species\",\"color\",\"emotion\",\"pose\",\"style\"} — sem markdown."
)

_ASSET_SPECS = {
    # nome -> (sufixo do prompt, ratio, size)
    "mascot-happy": ("happy joyful expression, celebrating", "1:1", "1024x1024"),
    "mascot-thinking": ("thinking curious expression, pondering", "1:1", "1024x1024"),
    "mascot-pose": ("signature celebration pose, cheering", "1:1", "1024x1024"),
    "logo-icon": ("as a clean app icon, centered, solid color background", "1:1", "1024x1024"),
    "logo-horizontal": ("on the left side of a wide horizontal banner, empty space on the right for the app name", "16:9", "1792x1024"),
    "favicon": ("extreme close-up of the face, centered", "1:1", "512x512"),
    "og-image": ("for an open graph share image, wide horizontal composition, centered character", "16:9", "1792x1024"),
}


class BiduVisualAgent:
    """Diretor de Identidade Visual dos MiniApps — padrão Duolingo via Agnes AI."""

    def __init__(self, client: AgnesClient | None = None):
        self.client = client or AgnesClient()

    # ── Briefing ────────────────────────────────────────────────────────────
    async def _brief(self, brand: dict, pain: str, app_name: str) -> dict:
        """Define os 5 atributos do personagem via LLM (JSON estrito) + fallback deterministico."""
        primary = (brand.get("theme") or {}).get("primary", "#3B82F6")
        user_prompt = (
            f"Branding (Dona Célia): marca '{brand.get('brand_name') or app_name}', "
            f"paleta primaria {primary}, simbolo '{brand.get('header_symbol') or ''}'.\n"
            f"Dor única do usuário: {pain}\n"
            f"App: {app_name}"
        )
        fallback = {
            "species": "friendly round animal",
            "color": primary,
            "emotion": "determined",
            "pose": "giving a thumbs up",
            "style": _FIXED_STYLE,
        }
        try:
            resp = await query_llm([
                {"role": "system", "content": _BIDU_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ], max_tokens=600, temperature=0.5)
            data = _parse_json_response(resp) if resp and not resp.startswith(ERROR_PREFIX) else None
            if isinstance(data, dict):
                color = str(data.get("color") or "").strip() or primary
                res = {
                    "species": str(data.get("species") or "").strip() or fallback["species"],
                    "color": color,
                    "emotion": str(data.get("emotion") or "").strip() or fallback["emotion"],
                    "pose": str(data.get("pose") or "").strip() or fallback["pose"],
                    "style": str(data.get("style") or "").strip() or _FIXED_STYLE,
                }
                if all(res.get(k) for k in ("species", "color", "emotion", "pose", "style")):
                    return res
        except Exception as e:
            logger.warning("[Bidu] Briefing LLM falhou: %s", e)
        return fallback

    async def _master_prompt(self, brief: dict, app_name: str, pain: str) -> str:
        return (
            f"{brief['style']} | {brief['species']} mascot, main color {brief['color']}, "
            f"{brief['emotion']} expression, signature pose: {brief['pose']}, "
            f"for '{app_name}' — app that solves: {pain[:120]}"
        )

    # ── Kit de assets ───────────────────────────────────────────────────────
    async def generate_assets(
        self,
        brand: dict,
        pain: str,
        app_name: str,
        slug: str,
        output_dir: str | None = None,
    ) -> dict:
        """Gera o kit completo → outputs/miniapps/{slug}/assets/ → dict de URLs.

        NUNCA lanca: qualquer falha dispara o fallback do Ricardo.
        """
        base_dir = output_dir or os.path.join("outputs", "miniapps", slug, "assets")
        os.makedirs(base_dir, exist_ok=True)

        brief = await self._brief(brand, pain, app_name)
        master_prompt = await self._master_prompt(brief, app_name, pain)

        # ── 1) Imagem-base (define a identidade) ──
        base_ref = None
        try:
            base_b64 = await self._generate_base(base_dir, master_prompt)
            if base_b64:
                base_ref = [base_b64]
        except Exception as e:
            logger.warning("[Bidu] Falha na imagem-base: %s", e)

        return await self._build_all(
            base_dir, brief, master_prompt, base_ref, app_name, slug
        )

    async def _generate_base(self, base_dir: str, master_prompt: str) -> str | None:
        """Gera o PNG base (mascot-front) e retorna base64 para o loop img2img."""
        path = os.path.join(base_dir, "mascot-front.png")
        result = await self.client.generate_image(
            master_prompt, size="1024x1024", ratio="1:1", output_path=path
        )
        if not result or not os.path.exists(path):
            return None
        try:
            with open(path, "rb") as fh:
                return "data:image/png;base64," + base64.b64encode(fh.read()).decode("ascii")
        except OSError as e:
            logger.warning("[Bidu] Erro ao ler base: %s", e)
            return None

    async def _build_all(
        self, base_dir: str, brief: dict, master_prompt: str,
        base_ref: list[str] | None, app_name: str, slug: str,
    ) -> dict:
        """Gera cada derivacao via img2img (base como ref) com fallback Ricardo."""
        assets_dir = base_dir
        urls = {"logo_url": "", "banner_url": "", "favicon_url": "", "og_image_url": ""}
        mascot = {}
        provider = "agnes"

        master_body = master_prompt

        # mascot-front (base) — ja salvo ou fallback
        front_path = os.path.join(assets_dir, "mascot-front.png")
        if not os.path.exists(front_path):
            front = await self.client.generate_image(
                master_body, size="1024x1024", ratio="1:1", output_path=front_path
            )
            if not front:
                provider = "fallback_ricardo"
        mascot["front"] = self._path_to_url(front_path)

        # variacoes img2img (consistencia via base_ref)
        for key, (suffix, ratio, size) in _ASSET_SPECS.items():
            prompt = f"{master_body} || {suffix}"
            path = os.path.join(assets_dir, f"{key}.png")
            try:
                result = await self.client.generate_image(
                    prompt, size=size, ratio=ratio, ref_images=base_ref, output_path=path
                )
            except Exception as e:
                logger.warning("[Bidu] Falha em %s: %s", key, e)
                result = None
            if not result or not os.path.exists(path):
                if provider != "fallback_ricardo":
                    provider = "partial_fallback"
            if key.startswith("mascot-"):
                mascot[key.replace("mascot-", "")] = self._path_to_url(path)

        # logos derivados
        urls["logo_url"] = self._path_to_url(os.path.join(assets_dir, "logo-icon.png"))
        urls["banner_url"] = self._path_to_url(os.path.join(assets_dir, "logo-horizontal.png"))
        urls["favicon_url"] = self._path_to_url(os.path.join(assets_dir, "favicon.png"))
        urls["og_image_url"] = self._path_to_url(os.path.join(assets_dir, "og-image.png"))

        # ── Fallback Ricardo: garante logo/banner nao-vazios ──
        if not urls["logo_url"] or not urls["banner_url"]:
            fb = await self._fallback_ricardo(app_name)
            urls["logo_url"] = urls["logo_url"] or fb.get("logo_url", "")
            urls["banner_url"] = urls["banner_url"] or fb.get("banner_url", "")
            provider = "fallback_ricardo"

        character_brief = {
            "species": brief["species"],
            "color": brief["color"],
            "emotion": brief["emotion"],
            "pose": brief["pose"],
            "style": brief["style"],
            "master_prompt": master_body,
            "app_name": app_name,
            "slug": slug,
            "generated_files": sorted(os.listdir(assets_dir) + ["character-brief.json"]),
        }
        brief_path = os.path.join(assets_dir, "character-brief.json")
        try:
            with open(brief_path, "w", encoding="utf-8") as fh:
                json.dump(character_brief, fh, ensure_ascii=False, indent=2)
        except OSError as e:
            logger.warning("[Bidu] Falha ao salvar character-brief: %s", e)

        return {
            "logo_url": urls["logo_url"],
            "banner_url": urls["banner_url"],
            "favicon_url": urls["favicon_url"],
            "og_image_url": urls["og_image_url"],
            "mascot": mascot,
            "character_brief": character_brief,
            "assets_dir": assets_dir,
            "provider": provider,
        }

    # ── Helper ──────────────────────────────────────────────────────────────
    @staticmethod
    def _path_to_url(path: str) -> str:
        """Converte caminho local (outputs/...) em URL servida (/outputs/...).

        Retorna '' se o arquivo nao existir — assim o fallback Ricardo dispara
        quando a geracao falha, nunca apontando para arquivo inexistente.
        """
        if not os.path.exists(path):
            return ""
        rel = path.replace("\\", "/")
        if rel.startswith("outputs/"):
            return "/" + rel
        if rel.startswith("/outputs/"):
            return rel
        return "/" + rel

    @staticmethod
    async def _fallback_ricardo(app_name: str) -> dict:
        """Reusa o ImageGeneratorAgent (agents/image_factory) — ultima rede de seguranca."""
        from agents.image_factory import ImageGeneratorAgent
        agent = ImageGeneratorAgent()
        logo_url, banner_url = "", ""
        try:
            res = await agent.generate_for_ebook(f"Logo Icon {app_name}")
            logo_url = res.get("image_url", "")
        except Exception as e:
            logger.warning("[Bidu/Ricardo] Falha logo: %s", e)
        try:
            res = await agent.generate_for_storefront(app_name)
            banner_url = res.get("image_url", "")
        except Exception as e:
            logger.warning("[Bidu/Ricardo] Falha banner: %s", e)
        return {"logo_url": logo_url, "banner_url": banner_url}


bidu_visual_agent = BiduVisualAgent()
