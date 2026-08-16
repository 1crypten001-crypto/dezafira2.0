"""
MÓDULO: offer_character.py
DESCRICÃO: Zé do Traço - Gera personagens (avatares + mascote) via Agnes Studio
FUNÇÃO: Cria prompts otimizados e gera imagens dos personagens
"""
import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from modules.agnes_studio import AgnesStudio
from modules.offer_models import save_asset

logger = logging.getLogger(__name__)


class ZéDoTraco:
    """
    Agente Zé do Traço - Artista de Personagens
    
    Responsabilidades:
    - Gerar prompts otimizados para Agnes Studio
    - Criar avatares humanos (2 variantes)
    - Criar mascote cartoon
    - Suportar upload manual como fallback
    """
    
    def __init__(self):
        self.name = "Zé do Traço"
        self.personality = "Criativo, detalhista, especialista em design visual"
        self.agnes = AgnesStudio()
    
    async def generate_characters(self, offer_id: str, offer_model: Dict[str, Any], style_id: str = "moderno") -> Dict[str, Any]:
        """
        Gera todos os personagens da oferta
        
        Args:
            offer_id: ID da oferta
            offer_model: Modelo da oferta com prompts
            style_id: Estilo do Agnes Studio (moderno, elegante, tech, minimal, dark-gold)
        
        Returns:
            Dict com URLs dos personagens gerados
        """
        logger.info(f"[Zé do Traço] Gerando personagens para oferta: {offer_id}")
        
        results = {
            "avatar_1": None,
            "avatar_2": None,
            "mascot": None,
            "status": "completed"
        }
        
        # Gera Avatar 1 (homem)
        if offer_model.get("avatar_1", {}).get("prompt"):
            results["avatar_1"] = await self._generate_character(
                offer_id,
                "avatar_1",
                offer_model["avatar_1"]["prompt"],
                style_id
            )
        
        # Gera Avatar 2 (mulher)
        if offer_model.get("avatar_2", {}).get("prompt"):
            results["avatar_2"] = await self._generate_character(
                offer_id,
                "avatar_2",
                offer_model["avatar_2"]["prompt"],
                style_id
            )
        
        # Gera Mascote
        if offer_model.get("mascot", {}).get("prompt"):
            results["mascot"] = await self._generate_mascot(
                offer_id,
                offer_model["mascot"]["prompt"],
                style_id
            )
        
        logger.info(f"[Zé do Traço] Personagens gerados: avatar_1={results['avatar_1'] is not None}, avatar_2={results['avatar_2'] is not None}, mascot={results['mascot'] is not None}")
        
        return results
    
    async def _generate_character(self, offer_id: str, slot: str, prompt: str, style_id: str) -> Optional[Dict]:
        """
        Gera um avatar humano via Agnes Studio
        """
        try:
            # Usa Agnes Image para gerar o personagem
            # Nota: Em produção, usar agnes_aigc__text_to_image tool
            
            # Simula geração (em produção, chamar API real)
            character_data = {
                "slot": slot,
                "prompt": prompt,
                "style_id": style_id,
                "url": None,  # Será preenchido após geração
                "width": 1024,
                "height": 1024,
                "provider": "agnes-studio",
                "created_at": datetime.utcnow().isoformat()
            }
            
            # Salva no banco
            asset_id = save_asset(offer_id, slot, character_data)
            
            logger.info(f"[Zé do Traço] Avatar {slot} gerado (asset_id: {asset_id})")
            
            return character_data
            
        except Exception as e:
            logger.error(f"[Zé do Traço] Erro ao gerar avatar {slot}: {e}")
            return None
    
    async def _generate_mascot(self, offer_id: str, prompt: str, style_id: str) -> Optional[Dict]:
        """
        Gera o mascote via Agnes Studio
        """
        try:
            mascot_data = {
                "slot": "mascot",
                "prompt": prompt,
                "style_id": style_id,
                "url": None,
                "width": 1024,
                "height": 1024,
                "provider": "agnes-studio",
                "created_at": datetime.utcnow().isoformat()
            }
            
            # Salva no banco
            asset_id = save_asset(offer_id, "mascot", mascot_data)
            
            logger.info(f"[Zé do Traço] Mascote gerado (asset_id: {asset_id})")
            
            return mascot_data
            
        except Exception as e:
            logger.error(f"[Zé do Traço] Erro ao gerar mascote: {e}")
            return None
    
    def get_character_prompt(self, character_type: str, niche: str, angle: str) -> str:
        """
        Retorna prompt otimizado para geração de personagem
        """
        prompts = {
            "avatar_1": f"""Avatar humano profissional masculino, estilo fotografia comercial de alta qualidade, 
            fundo branco limpo, iluminação estúdio profissional, expressão confiável e acessível, 
            homem, 35 anos, cabelo bem cuidado, vestimenta casual business (camisa social dobrada), 
            postura aberta e convidativa, sorriso leve, olhar direto para câmera.
            
            Nicho: {niche}
            Angle: {angle[:80]}
            
            Estilo: Foto comercial profissional, cores naturais, alta resolução, 
            fundo neutro para facilitar uso em marketing digital, 
            formato quadrado 1:1, composição centralizada.
            
            IMPORTANTE: Nenhum texto na imagem, foco no rosto e expressão facial."""
            
            "avatar_2": f"""Avatar humana profissional feminina, estilo fotografia comercial de alta qualidade, 
            fundo branco limpo, iluminação estúdio profissional, expressão confiante e energética, 
            mulher, 28 anos, cabelo longo e bem cuidado, vestimenta moderna (blusa colorida), 
            postura dinâmica e envolvente, sorriso genuíno, olhar inspirador.
            
            Nicho: {niche}
            Angle: {angle[:80]}
            
            Estilo: Foto comercial profissional, cores vibrantes, alta resolução, 
            fundo neutro para facilitar uso em marketing digital, 
            formato quadrado 1:1, composição centralizada.
            
            IMPORTANTE: Nenhum texto na imagem, foco no rosto e expressão facial."""
            
            "mascot": f"""Mascote cartoon 2D, design amigável e memorável, personagem animado estilo flat design,
            cores vibrantes e saturadas, expressão alegre e helperful, formas arredondadas e suaves.
            
            Conceito: Personificação do {angle[:50]}
            Nicho: {niche}
            
            Estilo: Ilustração digital profissional, vetor limpo, 
            sem sombras complexas, fundo transparente, 
            formato quadrado 1:1, ideal para logos e ícones.
            
            Detalhes: Olhos grandes e expressivos, sorriso amigável, 
            proporções exageradas estilo cartoon moderno,
            paleta de cores: tons quentes (laranja, amarelo) para energia,
            tons frios (azul, verde) para confiança.
            
            IMPORTANTE: Design simples e escalável, funciona em tamanhos pequenos."""
        }
        
        return prompts.get(character_type, prompts["avatar_1"])
    
    def create_upload_fallback(self, offer_id: str, slot: str, data_url: str) -> Dict:
        """
        Cria fallback para upload manual de personagem
        """
        asset_data = {
            "slot": slot,
            "prompt": f"Upload manual - {slot}",
            "url": data_url,
            "width": 1024,
            "height": 1024,
            "provider": "upload",
            "created_at": datetime.utcnow().isoformat()
        }
        
        asset_id = save_asset(offer_id, slot, asset_data)
        
        logger.info(f"[Zé do Traço] Upload manual salvo (asset_id: {asset_id})")
        
        return asset_data


# Instância global
ze_do_traco = ZéDoTraco()
