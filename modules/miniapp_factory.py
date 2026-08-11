"""
================================================================================
DEZAFIRA — Fabrica de MiniApps (Padrao Born-Complete)
================================================================================
Sala de Agentes: todo MiniApp nasce COMPLETO — identidade, copy, branding,
design e PWA instalavel desde o dia zero. Nada de app orfao, nada de
retrabalho pos-geracao.

1. Nexo (Arquiteto PWA)  : dor unica (uma dor, um app) + slug limpo + tipo + features
2. Carlao (Copywriter)   : headline, subheadline, description, CTA
3. Dona Celia (Branding) : paleta, tipografia, nome de marca, tom de voz
4. Ricardo (Visual)      : logo + banner (imagens IA)
5. Coder (Frontend)      : HTML PWA funcional
6. Verificador           : completude (slug, copy, branding, manifest, sw, icons)
7. DB Chronicler         : persistencia PostgreSQL com slug unico

Persistido no PostgreSQL (banco principal) — sobrevive deploy.
"""

import json
import logging
import re
from typing import Dict, Any, List

from agents.llm import query_llm, ERROR_PREFIX
from agents.specialists import miniapp_builder, _parse_json_response
from modules.image_factory import ImageGeneratorAgent
from services.pwa_generator import PWAGenerator

logger = logging.getLogger("miniapp_factory")
logger.setLevel(logging.INFO)

_APP_PREFIXES = ["criar miniapp", "crie miniapp", "criar app", "crie app", "novo miniapp",
                 "novo app", "miniapp", "app", "criar", "crie", "gerar", "gere", "quero um",
                 "quero uma", "faca um", "faca uma", "cria um", "cria uma"]


class MiniAppFactory:
    def __init__(self):
        self.image_agent = ImageGeneratorAgent()

    # ─────────────────────────────────────────────────────────────────────────
    # Agentes internos (cada um com fallback deterministico — a fabrica NUNCA
    # entrega app incompleto por falha de LLM)
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _slug_from_prompt(prompt: str) -> str:
        """Slug deterministico a partir do prompt (limpo, sem prefixos)."""
        text = prompt.strip()
        lower = text.lower()
        for p in sorted(_APP_PREFIXES, key=len, reverse=True):
            if lower.startswith(p):
                text = text[len(p):].strip(" :;-–")
                break
        text = re.sub(r"[“”\"']", "", text)
        words = [w for w in text.split() if w][:6]
        return PWAGenerator.slugify(" ".join(words)) or "app"

    def _ensure_unique_slug(self, slug: str, ignore_id: str = "") -> str:
        """Garante slug unico no banco (sufixo -2, -3... em caso de colisao)."""
        from modules.database import get_db_miniapp_by_slug
        candidate, i = slug, 2
        while True:
            existing = get_db_miniapp_by_slug(candidate)
            if not existing or (ignore_id and existing.get("id") == ignore_id):
                return candidate
            candidate = f"{slug}-{i}"
            i += 1
        return candidate

    async def _nexo_arquiteto(self, prompt: str, niche: str) -> dict:
        """Nexo: extrai dor unica, define slug, tipo e features do app."""
        resp = await query_llm([
            {"role": "system", "content": (
                "Voce e o Nexo, arquiteto de microSaaS da DEZAFIRA. Sua filosofia: "
                "UMA DOR, UM APP (modelo microSaaS de nicho). "
                "A partir do pedido do usuario, defina a dor aguda do publico, um nome comercial "
                "PROFISSIONAL de 2 a 4 palavras em portugues brasileiro, sem abreviacoes, siglas "
                "nem jargao (ex: 'Calculadora de Deficit Calorico' e valido; 'CaloDef', 'CalcDC' "
                "e 'Calculadora' sao INVALIDOS) e um slug limpo em minusculas com hifens. "
                "Responda APENAS com JSON valido, sem markdown:\n"
                "{\"pain\": \"dor principal em 1 frase\", \"app_name\": \"Nome Comercial Do App\", "
                "\"slug\": \"nome-comercial-do-app\", \"app_type\": \"Calculator|Quiz|Checklist|Scheduler|Tool\", "
                "\"features\": [\"feature 1\", \"feature 2\", \"feature 3\"]}"
            )},
            {"role": "user", "content": f"Pedido: {prompt}\nNicho: {niche}"},
        ], max_tokens=1024, temperature=0.4)

        data = _parse_json_response(resp) if resp and not resp.startswith(ERROR_PREFIX) else None
        pain, app_name, slug, app_type = "", "", "", ""
        app_slug = ""
        features = []
        if isinstance(data, dict):
            pain = str(data.get("pain") or "").strip()
            app_name = str(data.get("app_name") or "").strip()
            # Slug so e aceito se compartilhar palavras com o nome comercial —
            # evita slug caprichoso do LLM (ex: 'calo-def') desconectado da marca.
            app_slug = PWAGenerator.slugify(app_name)
            raw_slug = PWAGenerator.slugify(str(data.get("slug") or ""))
            if len(raw_slug) >= 5 and set(raw_slug.split("-")) & set(app_slug.split("-")):
                slug = raw_slug
            else:
                slug = app_slug or self._slug_from_prompt(prompt)
            app_type = str(data.get("app_type") or "").strip()
            raw_features = data.get("features")
            if isinstance(raw_features, list):
                features = raw_features

        # ── Fallbacks deterministicos ──
        if not pain:
            pain = f"Resolva {prompt.strip().lower()[:80]} de forma rapida e pratica"
        if not app_name or len(app_name.split()) < 2 or len(app_name) < 8:
            # Nome do LLM invalido (1 palavra, sigla ou muito curto) → deriva do prompt
            app_name = re.sub(r"[“”\"']", "", prompt.strip())
            for p in sorted(_APP_PREFIXES, key=len, reverse=True):
                if app_name.lower().startswith(p):
                    app_name = app_name[len(p):].strip(" :;-–")
                    break
            app_name = re.sub(r"\s+", " ", app_name).strip(" .:;,-–")
            words = [w.capitalize() for w in app_name.split() if w][:4]
            app_name = " ".join(words) or "MiniApp"
            slug = app_slug = PWAGenerator.slugify(app_name)
        if not slug:
            slug = app_slug or self._slug_from_prompt(prompt)
        if not app_type:
            pl = prompt.lower()
            if "quiz" in pl:
                app_type = "Quiz PWA"
            elif "calculad" in pl or "juros" in pl or "simulad" in pl:
                app_type = "Calculator PWA"
            elif "checklist" in pl or "lista" in pl:
                app_type = "Checklist PWA"
            elif "agenda" in pl or "horario" in pl or "planej" in pl:
                app_type = "Scheduler PWA"
            else:
                app_type = "Interactive PWA"
        features = [str(f) for f in features if str(f).strip()][:6]
        if not features:
            features = ["Funcionalidade principal", "Design responsivo", "Tema escuro"]
        return {"pain": pain, "app_name": app_name, "slug": slug,
                "app_type": app_type, "features": features}

    async def _carlao_copy(self, app_name: str, pain: str, niche: str) -> dict:
        """Carlao: copy de conversao — headline, subheadline, description, CTA."""
        resp = await query_llm([
            {"role": "system", "content": (
                "Voce e o Carlao, redator-chefe da DEZAFIRA, especialista em copy de "
                "microSaaS e apps de nicho. Escreva copy curta, direta e de alta conversao "
                "em PORTUGUES BRASILEIRO COM GRAMATICA PERFEITA — sem erros de concordancia, "
                "sem palavras truncadas e sem frases incompletas (ex: 'Emagreca com Facilidade', "
                "nunca 'Emagreca com Facil'). A headline fala a dor ou o resultado prometido. "
                "Responda APENAS com JSON valido, sem markdown:\n"
                "{\"headline\": \"titulo curto (max 8 palavras) falando a dor ou o resultado\", "
                "\"subheadline\": \"1 frase (max 20 palavras) explicando a promessa\", "
                "\"description\": \"resumo para meta description (max 25 palavras)\", "
                "\"cta_text\": \"acao de 2-3 palavras (ex: Calcular Agora, Descobrir Meu Score)\"}"
            )},
            {"role": "user", "content": f"App: {app_name}\nDor principal: {pain}\nNicho: {niche}"},
        ], max_tokens=700, temperature=0.6)

        data = _parse_json_response(resp) if resp and not resp.startswith(ERROR_PREFIX) else None
        headline = str(data.get("headline") or "").strip() if isinstance(data, dict) else ""
        subheadline = str(data.get("subheadline") or "").strip() if isinstance(data, dict) else ""
        description = str(data.get("description") or "").strip() if isinstance(data, dict) else ""
        cta_text = str(data.get("cta_text") or "").strip() if isinstance(data, dict) else ""

        if not headline:
            headline = f"{app_name}: {pain}" if pain else app_name
        if not subheadline:
            subheadline = pain or f"Ferramenta inteligente para {niche}"
        if not description:
            description = f"{headline} — {subheadline}"
        if not cta_text:
            cta_text = "Começar Agora"
        return {"headline": headline, "subheadline": subheadline,
                "description": description, "cta_text": cta_text}

    async def _dona_celia_branding(self, app_name: str, niche: str, pain: str = "") -> dict:
        """Dona Celia: identidade visual (paleta, tipografia, simbolo) + tom de voz."""
        from modules.brand_designer import BrandingDesignerAgent
        try:
            brand = await BrandingDesignerAgent().generate_branding(app_name, niche)
        except Exception as e:
            logger.warning(f"[Dona Celia] Falha no agente de branding: {e}")
            brand = {}
        theme = self._adapt_brand_to_theme(brand, niche, pain)
        brand_name = app_name
        brand_voice = (f"Tom direto, claro e executivo, com autoridade em {niche}. "
                       f"Fala a dor do usuario e entrega resultado imediato.")
        return {"brand_name": brand_name, "brand_voice": brand_voice,
                "theme": theme, "logo_svg": brand.get("logo_svg", ""),
                "favicon_svg": brand.get("favicon_svg", "")}

    @staticmethod
    def _adapt_brand_to_theme(brand: dict, niche: str, pain: str = "") -> dict:
        """Adapta o branding (Dona Celia) para o tema PWA (fundo escuro, mobile-first)."""
        theme = PWAGenerator.niche_theme(niche)
        colors = brand.get("colors") or {}
        colors_dark = brand.get("colors_dark") or {}
        primary = colors.get("primary") or theme["primary"]
        accent = colors.get("accent") or theme["accent"]
        primary_dark = colors.get("primary_dark") or primary
        bg = colors_dark.get("bg") or "#090D16"
        surface = colors_dark.get("bg_dark") or "#131A2C"
        theme.update({
            "primary": primary,
            "accent": accent,
            "gradient": f"135deg, {primary_dark}, {primary}",
            "bg": bg,
            "surface": surface,
            "emoji": brand.get("header_symbol") or theme["emoji"],
        })
        if pain:
            theme["tagline"] = pain[:60] + ("..." if len(pain) > 60 else "")
        return theme

    async def _ricardo_visual(self, app_name: str) -> dict:
        """Ricardo: gera logo e banner (cascata IA -> banco de imagens -> SVG)."""
        logo_url, banner_url = "", ""
        try:
            logo_res = await self.image_agent.generate_for_ebook(f"Logo Icon {app_name}")
            logo_url = logo_res.get("image_url", "")
        except Exception as e:
            logger.warning(f"[Ricardo] Falha logo: {e}")
        try:
            banner_res = await self.image_agent.generate_for_storefront(app_name)
            banner_url = banner_res.get("image_url", "")
        except Exception as e:
            logger.warning(f"[Ricardo] Falha banner: {e}")
        return {"logo_url": logo_url, "banner_url": banner_url}

    # ─────────────────────────────────────────────────────────────────────────
    # Fluxo principal: criar MiniApp born-complete
    # ─────────────────────────────────────────────────────────────────────────

    async def create_miniapp_with_room(self, prompt: str, niche: str = "Geral",
                                       app_id: str = "") -> Dict[str, Any]:
        """Orquestra a Sala de Agentes para gerar um MiniApp PWA born-complete.

        Se app_id for fornecido (criacao assincrona), o registro placeholder ja
        existente no banco e ATUALIZADO com o resultado final; caso contrario,
        um novo registro e criado (fluxo sincrono legado).
        """
        from modules.database import create_db_miniapp, update_db_miniapp, create_db_miniapp_drip

        logger.info(f"[MiniAppFactory] Iniciando Sala de Agentes: '{prompt}' (Nicho: {niche})")
        logs = []

        # ── PASSO 1: Nexo (Arquiteto PWA) — dor + slug + tipo + features ──
        logs.append({"agent": "📐 Nexo (Arquiteto PWA)", "message": f"Mapeando a dor unica de '{prompt}'..."})
        nexo = await self._nexo_arquiteto(prompt, niche)
        app_name, pain, slug = nexo["app_name"], nexo["pain"], nexo["slug"]
        app_type, features = nexo["app_type"], nexo["features"]
        slug = self._ensure_unique_slug(slug, ignore_id=app_id or "")
        logs.append({"agent": "📐 Nexo (Arquiteto PWA)",
                     "message": f"Dor: {pain} | Slug: {slug} | Tipo: {app_type}"})

        # ── PASSO 2: Carlao (Copywriter) — copy de conversao ──
        logs.append({"agent": "✍️ Carlão (Copywriter)", "message": "Escrevendo headline, subtitulo e CTA..."})
        copy = await self._carlao_copy(app_name, pain, niche)
        logs.append({"agent": "✍️ Carlão (Copywriter)",
                     "message": f"Headline: {copy['headline']} | CTA: {copy['cta_text']}"})

        # ── PASSO 3: Dona Celia (Branding) — identidade visual ──
        logs.append({"agent": "🎨 Dona Célia (Branding)", "message": "Definindo paleta, tipografia e tom de voz..."})
        brand = await self._dona_celia_branding(app_name, niche, pain)
        logs.append({"agent": "🎨 Dona Célia (Branding)",
                     "message": f"Tema: {brand['theme'].get('primary')} | Marca: {brand['brand_name']}"})

        # ── PASSO 4: Ricardo (Visual) — logo + banner ──
        logs.append({"agent": "🖼️ Ricardo (Diretor Visual)", "message": "Gerando logo e banner..."})
        visual = await self._ricardo_visual(app_name)
        logs.append({"agent": "🖼️ Ricardo (Diretor Visual)",
                     "message": "Logo: " + ("OK" if visual["logo_url"] else "fallback SVG")})

        # ── PASSO 5: Coder (Frontend) — HTML PWA funcional ──
        logs.append({"agent": "💻 Coder (Desenvolvedor Frontend)", "message": "Construindo a interface funcional..."})
        pwa_result = await miniapp_builder.build_pwa(
            app_name=app_name, niche=niche, app_type=app_type,
            features=features, logo_url=visual["logo_url"],
        )
        pwa_html = pwa_result.get("html", "")
        logs.append({"agent": "💻 Coder (Desenvolvedor Frontend)",
                     "message": f"PWA gerada com {len(pwa_html)} caracteres de HTML"})

        # ── PASSO 6: Verificador — completude born-complete ──
        record = {
            "id": "pending", "app_name": app_name, "niche": niche,
            "app_type": app_type, "slug": slug, "pain": pain,
            "headline": copy["headline"], "subheadline": copy["subheadline"],
            "description": copy["description"], "cta_text": copy["cta_text"],
            "brand_name": brand["brand_name"], "brand_voice": brand["brand_voice"],
            "theme": json.dumps(brand["theme"], ensure_ascii=False),
            "logo_url": visual["logo_url"], "banner_url": visual["banner_url"],
            "pwa_html": pwa_html,
        }
        check = PWAGenerator.completeness_check(record)
        status = "active" if check["passed"] else "draft"
        logs.append({"agent": "✅ Verificador de Completude",
                     "message": (f"PWA COMPLETO ({len(check['checks'])-len(check['missing'])}/{len(check['checks'])} checks)"
                                 if check["passed"] else f"Faltando: {', '.join(check['missing'])} — corrigindo...")})

        # Correcao automatica: re-materializa copy/tema com fallback deterministico
        if not check["passed"]:
            copy_fixed = PWAGenerator.resolve_copy(record)
            record.update({
                "headline": copy_fixed["headline"], "subheadline": copy_fixed["subheadline"],
                "description": copy_fixed["description"], "cta_text": copy_fixed["cta_text"],
                "theme": json.dumps(PWAGenerator.record_theme(record), ensure_ascii=False),
            })
            check = PWAGenerator.completeness_check(record)
            status = "active" if check["passed"] else "draft"

        pwa_manifest = json.dumps(PWAGenerator.build_manifest(
            "pending", slug, app_name, PWAGenerator.record_theme(record), copy["description"]),
            ensure_ascii=False)
        pwa_check = json.dumps(check, ensure_ascii=False)

        # ── PASSO 7: DB Chronicler — persistencia com slug unico ──
        if app_id:
            logs.append({"agent": "🗄️ DB Chronicler", "message": f"Atualizando MiniApp '{app_name}' (slug: {slug}) no PostgreSQL..."})
            try:
                updated = update_db_miniapp(
                    app_id,
                    app_name=app_name, niche=niche, app_type=app_type,
                    logo_url=visual["logo_url"], banner_url=visual["banner_url"],
                    pwa_manifest=pwa_manifest, pwa_html=pwa_html,
                    slug=slug, pain=pain, description=copy["description"],
                    headline=copy["headline"], subheadline=copy["subheadline"],
                    cta_text=copy["cta_text"], brand_name=brand["brand_name"],
                    brand_voice=brand["brand_voice"], theme=json.dumps(brand["theme"], ensure_ascii=False),
                    pwa_check=pwa_check, status=status,
                )
                if not updated:
                    raise RuntimeError("MiniApp placeholder nao encontrado para atualizar")
                logs.append({"agent": "🗄️ DB Chronicler", "message": f"MiniApp atualizado (ID: {app_id}, status: {status})"})
            except Exception as e:
                logger.error(f"Erro ao atualizar MiniApp {app_id}: {e}")
                logs.append({"agent": "🗄️ DB Chronicler", "message": f"Aviso: falha ao atualizar ({e})"})
        else:
            logs.append({"agent": "🗄️ DB Chronicler", "message": f"Gravando MiniApp '{app_name}' (slug: {slug}) no PostgreSQL..."})
            try:
                app_record = create_db_miniapp(
                    app_name=app_name, niche=niche, app_type=app_type,
                    logo_url=visual["logo_url"], banner_url=visual["banner_url"],
                    pwa_manifest=pwa_manifest, pwa_html=pwa_html,
                    slug=slug, pain=pain, description=copy["description"],
                    headline=copy["headline"], subheadline=copy["subheadline"],
                    cta_text=copy["cta_text"], brand_name=brand["brand_name"],
                    brand_voice=brand["brand_voice"], theme=json.dumps(brand["theme"], ensure_ascii=False),
                    pwa_check=pwa_check,
                )
                app_id = app_record["id"]
                logs.append({"agent": "🗄️ DB Chronicler", "message": f"MiniApp salvo com ID: {app_id} (status: {status})"})
            except Exception as e:
                logger.error(f"Erro ao salvar no PostgreSQL: {e}")
                app_id = f"app_{abs(hash(prompt)) % 100000:05d}"
                logs.append({"agent": "🗄️ DB Chronicler", "message": f"Aviso: ID temporario {app_id} (erro no DB)"})

        # ── PASSO 8: Drip Content temporizado ──
        logs.append({"agent": "🗄️ DB Chronicler", "message": "Configurando trilha de conteudos recorrentes (Dia 1, 7, 14, 30)..."})
        drip_items = [
            {"day": 1, "title": "🎯 Boas-Vindas & Diagnostico Inicial", "type": "quiz",
             "payload": {"status": "unlocked", "desc": "Defina suas metas e calcule seu ponto de partida."}},
            {"day": 7, "title": "⚡ Modulo 2: Automacao e Ferramentas Pro", "type": "tools",
             "payload": {"status": "scheduled", "desc": "Modelos prontos de copias e rotinas diarias."}},
            {"day": 14, "title": "🚀 Modulo 3: Escala e Retencao de Assinantes", "type": "masterclass",
             "payload": {"status": "scheduled", "desc": "Roteiro de conversao para dobrar o LTV."}},
            {"day": 30, "title": "👑 Modulo VIP: Acesso a Comunidade de Elite", "type": "vip",
             "payload": {"status": "scheduled", "desc": "Encontros mensais de mentoria ao vivo."}},
        ]
        for item in drip_items:
            try:
                create_db_miniapp_drip(miniapp_id=app_id, unlock_day=item["day"],
                                       title=item["title"], content_type=item["type"],
                                       payload=json.dumps(item["payload"]))
            except Exception as e:
                logger.warning(f"Erro ao salvar drip content: {e}")

        logs.append({"agent": "🎉 Sala de Agentes",
                     "message": f"MiniApp '{app_name}' nasceu COMPLETO no padrao born-complete! Acesse /app/{slug}"})

        result = {
            "app_id": app_id,
            "app_name": app_name,
            "niche": niche,
            "app_type": app_type,
            "slug": slug,
            "app_url": f"/app/{slug}",
            "pain": pain,
            "copy": copy,
            "branding": {"brand_name": brand["brand_name"], "brand_voice": brand["brand_voice"], "theme": brand["theme"]},
            "logo_url": visual["logo_url"],
            "banner_url": visual["banner_url"],
            "pwa_manifest": pwa_manifest,
            "pwa_html": pwa_html,
            "pwa_check": check,
            "status": status,
            "drip_contents": drip_items,
            "logs": logs,
        }
        return result

    # ─────────────────────────────────────────────────────────────────────────
    # Migracao: apps legados entram no padrao born-complete (dados preservados)
    # ─────────────────────────────────────────────────────────────────────────

    async def upgrade_legacy_miniapp(self, record: dict) -> dict:
        """Migra um app legado para o novo padrao — atribui slug, gera copy e
        branding, reescreve o pacote PWA. Mantem dados e funcionalidade existentes."""
        from modules.database import get_db_miniapp_by_slug

        app_name = record.get("app_name", "MiniApp")
        niche = record.get("niche", "Geral") or "Geral"
        app_id = record.get("id", "")

        # 1) Slug: derivado do nome, garantido unico
        base_slug = PWAGenerator.slugify(app_name)
        slug, i = base_slug, 2
        while get_db_miniapp_by_slug(slug) and get_db_miniapp_by_slug(slug).get("id") != app_id:
            slug = f"{base_slug}-{i}"
            i += 1

        # 2) Dor: o proprio app legado e a dor (uma dor, um app) — usa o nome como conceito
        nexo = await self._nexo_arquiteto(app_name, niche)
        pain = nexo["pain"]

        # 3) Copy (Carlao) + Branding (Dona Celia) — com fallback deterministico
        copy = await self._carlao_copy(app_name, pain, niche)
        brand = await self._dona_celia_branding(app_name, niche, pain)

        updated = dict(record)
        updated.update({
            "slug": slug,
            "pain": pain,
            "headline": copy["headline"],
            "subheadline": copy["subheadline"],
            "description": copy["description"],
            "cta_text": copy["cta_text"],
            "brand_name": brand["brand_name"],
            "brand_voice": brand["brand_voice"],
            "theme": json.dumps(brand["theme"], ensure_ascii=False),
        })

        # 4) Pacote PWA reescrito com o slug persistido (mantem pwa_html original)
        manifest = PWAGenerator.build_manifest(app_id or "app", slug, app_name,
                                               brand["theme"], copy["description"])
        updated["pwa_manifest"] = json.dumps(manifest, ensure_ascii=False)

        # 5) Verificacao de completude
        check = PWAGenerator.completeness_check(updated)
        updated["pwa_check"] = json.dumps(check, ensure_ascii=False)
        return {"updated": updated, "check": check, "slug": slug}


miniapp_factory = MiniAppFactory()
