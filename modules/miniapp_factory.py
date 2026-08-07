"""
================================================================================
DEZAFIRA — Fabrica de MiniApps Profissional (Sala de Agentes + Agnes AI + DB)
================================================================================
Orquestra a criacao autonoma de MiniApps PWA para retencao e recorrencia (MRR):
1. Arquiteto PWA (Nexo Agent): Mapeia conceito, calculadoras, quizzes e geradores.
2. Diretor Visual (Agnes AI): Gera a Logo/Icone 3D personalizado (512x512).
3. Desenvolvedor Frontend (Coder AI): Constrói a aplicacao PWA reativa instalavel.
4. Gestor de Dados (DB Chronicler): Estrutura o banco com conteudo temporizado (Drip Content).

Migrado para PostgreSQL (banco principal) — dados sobrevivem deploy.
"""

import os
import json
import asyncio
import logging
from typing import Dict, Any, List
from modules.image_factory import ImageGeneratorAgent
from agents.specialists import miniapp_builder

logger = logging.getLogger("miniapp_factory")
logger.setLevel(logging.INFO)


class MiniAppFactory:
    def __init__(self):
        self.image_agent = ImageGeneratorAgent()

    async def create_miniapp_with_room(self, prompt: str, niche: str = "Geral") -> Dict[str, Any]:
        """
        Orquestra a Sala de Agentes para gerar um MiniApp PWA completo.
        Salva no PostgreSQL (banco principal) para persistir entre deploys.
        """
        from modules.database import create_db_miniapp, update_db_miniapp, create_db_miniapp_drip

        logger.info(f"[MiniAppFactory] Iniciando Sala de Agentes para: '{prompt}' (Nicho: {niche})")
        logs = []

        # -------------------------------------------------------------------
        # PASSO 1: Arquiteto PWA (Nexo Agent) — Estrutura e Funcionalidades
        # -------------------------------------------------------------------
        logs.append({"agent": "📐 Arquiteto PWA (Nexo)", "message": f"Mapeando arquitetura reativa para '{prompt}'..."})

        app_name = prompt.replace("Criar MiniApp:", "").replace("MiniApp", "").strip() or "Calculadora & Gestor de Alta Performance"

        # Detectar tipo de app baseado no prompt
        app_type = "Interactive PWA"
        features = ["Calculadora basica", "Design responsivo", "Tema escuro"]
        prompt_lower = prompt.lower()
        if "quiz" in prompt_lower:
            app_type = "Quiz PWA"
            features = ["Quiz interativo", "Score automatico", "Compartilhamento"]
        elif "calculad" in prompt_lower:
            app_type = "Calculator PWA"
            features = ["Calculadora avancada", "Historico", "Exportar resultados"]
        elif "checklist" in prompt_lower:
            app_type = "Checklist PWA"
            features = ["Checklist interativo", "Progresso salvo", "Notificacoes"]
        elif "agenda" in prompt_lower or "horario" in prompt_lower:
            app_type = "Scheduler PWA"
            features = ["Agenda interativa", "Lembretes", "Calendario visual"]

        logs.append({"agent": "📐 Arquiteto PWA (Nexo)", "message": f"Tipo definido: {app_type} | Features: {', '.join(features)}"})

        # -------------------------------------------------------------------
        # PASSO 2: Diretor Visual (Agnes AI) — Logo 3D Personalizada & Banner
        # -------------------------------------------------------------------
        logs.append({"agent": "🎨 Diretor Visual (Agnes AI)", "message": "Gerando Logo 3D personalizada e Banner de capa via Agnes AI..."})

        logo_res = await self.image_agent.generate_for_ebook(f"Logo Icon {app_name}")
        logo_url = logo_res.get("image_url", "")

        banner_res = await self.image_agent.generate_for_storefront(app_name)
        banner_url = banner_res.get("image_url", "")

        # -------------------------------------------------------------------
        # PASSO 3: Desenvolvedor Frontend (Coder AI) — Codigo PWA Instalavel
        # -------------------------------------------------------------------
        logs.append({"agent": "💻 Desenvolvedor Frontend (Coder)", "message": "Construindo interface PWA instalavel com suporte offline e Glassmorphism..."})

        # Usar o MiniAppBuilderAgent para gerar HTML real
        pwa_result = await miniapp_builder.build_pwa(
            app_name=app_name,
            niche=niche,
            app_type=app_type,
            features=features,
            logo_url=logo_url,
        )
        pwa_html = pwa_result.get("html", "")

        logs.append({"agent": "💻 Desenvolvedor Frontend (Coder)", "message": f"PWA gerada com {len(pwa_html)} caracteres de HTML funcional"})

        pwa_manifest = {
            "name": app_name,
            "short_name": app_name[:12],
            "description": f"Aplicativo oficial de utilidade diaria para {app_name}",
            "start_url": "/",
            "display": "standalone",
            "background_color": "#0a0a1a",
            "theme_color": "#38bdf8",
            "icons": [{"src": logo_url, "sizes": "512x512", "type": "image/png"}] if logo_url else [],
        }

        # -------------------------------------------------------------------
        # PASSO 4: Salvar no Banco Principal (PostgreSQL)
        # -------------------------------------------------------------------
        logs.append({"agent": "🗄️ Gestor de Conteudos (DB Chronicler)", "message": "Gravando no banco PostgreSQL (sobrevive deploy)..."})

        try:
            app_record = create_db_miniapp(
                app_name=app_name,
                niche=niche,
                app_type=app_type,
                logo_url=logo_url,
                banner_url=banner_url,
                pwa_manifest=json.dumps(pwa_manifest),
                pwa_html=pwa_html,
            )
            app_id = app_record["id"]
            logs.append({"agent": "🗄️ Gestor de Conteudos (DB Chronicler)", "message": f"MiniApp salvo no PostgreSQL com ID: {app_id}"})
        except Exception as e:
            logger.error(f"Erro ao salvar no PostgreSQL: {e}")
            app_id = f"app_{abs(hash(prompt)) % 100000:05d}"
            logs.append({"agent": "🗄️ Gestor de Conteudos (DB Chronicler)", "message": f"Aviso: ID temporario {app_id} (erro no DB)"})

        # -------------------------------------------------------------------
        # PASSO 5: Drip Content Temporizado
        # -------------------------------------------------------------------
        logs.append({"agent": "🗄️ Gestor de Conteudos (DB Chronicler)", "message": "Configurando trilha de conteudos recorrentes (Dia 1, 7, 14, 30)..."})

        drip_items = [
            {"day": 1, "title": "🎯 Boas-Vindas & Diagnostico Inicial", "type": "quiz", "payload": {"status": "unlocked", "desc": "Defina suas metas e calcule seu ponto de partida."}},
            {"day": 7, "title": "⚡ Modulo 2: Automacao e Ferramentas Pro", "type": "tools", "payload": {"status": "scheduled", "desc": "Modelos prontos de copias e rotinas diarias."}},
            {"day": 14, "title": "🚀 Modulo 3: Escala e Retencao de Assinantes", "type": "masterclass", "payload": {"status": "scheduled", "desc": "Roteiro de conversao para dobrar o LTV."}},
            {"day": 30, "title": "👑 Modulo VIP: Acesso a Comunidade de Elite", "type": "vip", "payload": {"status": "scheduled", "desc": "Encontros mensais de mentoria ao vivo."}},
        ]

        for item in drip_items:
            try:
                create_db_miniapp_drip(
                    miniapp_id=app_id,
                    unlock_day=item["day"],
                    title=item["title"],
                    content_type=item["type"],
                    payload=json.dumps(item["payload"]),
                )
            except Exception as e:
                logger.warning(f"Erro ao salvar drip content: {e}")

        logs.append({"agent": "🎉 Sala de Agentes", "message": f"MiniApp PWA '{app_name}' construido e publicado com sucesso no ecossistema!"})

        result = {
            "app_id": app_id,
            "app_name": app_name,
            "niche": niche,
            "app_type": app_type,
            "logo_url": logo_url,
            "banner_url": banner_url,
            "pwa_manifest": pwa_manifest,
            "pwa_html": pwa_html,
            "drip_contents": drip_items,
            "logs": logs,
            "status": "active",
        }
        return result


miniapp_factory = MiniAppFactory()
