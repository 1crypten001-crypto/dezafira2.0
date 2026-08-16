"""
MÓDULO: offer_critic.py
DESCRICÃO: Dona Benta - Validadora e criticadora da oferta
FUNÇÃO: Analisa conversion score, SEO score e gera recomendações
"""
import logging
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)


class DonaBenta:
    """
    Agente Dona Benta - Criticadora da Oferta
    
    Responsabilidades:
    - Calcular score de conversão (0-100)
    - Calcular score SEO (0-100)
    - Identificar pontos de melhoria
    - Validar estrutura da oferta
    """
    
    def __init__(self):
        self.name = "Dona Benta"
        self.personality = "Exigente, analítica, focada em qualidade e performance"
    
    async def validate_offer(self, offer_data: Dict[str, Any], copy_data: Dict[str, Any], assets_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valida a oferta completa e gera score + recomendações
        
        Args:
            offer_data: Dados da oferta (modelo, angle, mechanism, etc)
            copy_data: Dados do copy (headlines, body, CTAs)
            assets_data: Dados dos assets (avatares, mascote)
        
        Returns:
            Dict com scores e recomendações
        """
        logger.info(f"[Dona Benta] Validando oferta completa")
        
        # Calcula scores
        conversion_score = self._calculate_conversion_score(offer_data, copy_data)
        seo_score = self._calculate_seo_score(copy_data, offer_data)
        overall_score = int((conversion_score + seo_score) / 2)
        
        # Gera recomendações
        recommendations = self._generate_recommendations(
            conversion_score,
            seo_score,
            offer_data,
            copy_data,
            assets_data
        )
        
        # Identifica pontos fortes e fracos
        strengths = self._identify_strengths(offer_data, copy_data, assets_data)
        weaknesses = self._identify_weaknesses(offer_data, copy_data, assets_data)
        
        validation = {
            "conversion_score": conversion_score,
            "seo_score": seo_score,
            "overall_score": overall_score,
            "recommendations": recommendations,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "is_ready": overall_score >= 70,
            "status": "completed",
            "created_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"[Dona Benta] Validação concluída: score={overall_score}/100, ready={validation['is_ready']}")
        
        return validation
    
    def _calculate_conversion_score(self, offer: Dict, copy: Dict) -> int:
        """
        Calcula score de conversão (0-100)
        """
        score = 0
        
        # Angle claro e direto (20 pontos)
        angle = offer.get("angle", "")
        if angle and len(angle) > 20:
            score += 20
        elif angle:
            score += 10
        
        # Mechanism definido (15 pontos)
        mechanism = offer.get("mechanism", "")
        if mechanism and len(mechanism) > 30:
            score += 15
        elif mechanism:
            score += 7
        
        # Promise clara (15 pontos)
        promise = offer.get("promise", "")
        if promise and "garantido" in promise.lower():
            score += 15
        elif promise:
            score += 8
        
        # Headlines testáveis (20 pontos)
        headlines = copy.get("headlines", [])
        if len(headlines) >= 3:
            score += 20
        elif len(headlines) >= 1:
            score += 10
        
        # Body copy completo (15 pontos)
        body_long = copy.get("body_long", "")
        if body_long and len(body_long) > 500:
            score += 15
        elif body_long and len(body_long) > 200:
            score += 8
        
        # CTAs presentes (10 pontos)
        ctas = copy.get("ctas", [])
        if len(ctas) >= 2:
            score += 10
        elif len(ctas) >= 1:
            score += 5
        
        # Avatares gerados (5 pontos)
        avatar_1 = offer.get("avatar_1_url") or offer.get("avatar_1", {}).get("url")
        if avatar_1:
            score += 5
        
        return min(score, 100)
    
    def _calculate_seo_score(self, copy: Dict, offer: Dict) -> int:
        """
        Calcula score SEO (0-100)
        """
        score = 0
        
        # Meta title otimizado (20 pontos)
        meta_title = copy.get("seo_meta", {}).get("title", "")
        if meta_title and len(meta_title) > 30:
            score += 20
        elif meta_title:
            score += 10
        
        # Meta description presente (20 pontos)
        meta_desc = copy.get("seo_meta", {}).get("description", "")
        if meta_desc and 100 < len(meta_desc) < 160:
            score += 20
        elif meta_desc:
            score += 10
        
        # Keywords presentes (25 pontos)
        keywords = copy.get("seo_meta", {}).get("keywords", [])
        if len(keywords) >= 3:
            score += 25
        elif len(keywords) >= 1:
            score += 12
        
        # Keywords no body copy (20 pontos)
        body_long = copy.get("body_long", "")
        if body_long:
            keyword_count = sum(1 for kw in keywords if kw.lower() in body_long.lower())
            if keyword_count >= 2:
                score += 20
            elif keyword_count >= 1:
                score += 10
        
        # Headlines com keywords (15 pontos)
        headlines = copy.get("headlines", [])
        if headlines:
            keyword_inheadline = any(kw.lower() in headlines[0].lower() for kw in keywords)
            if keyword_inheadline:
                score += 15
        
        return min(score, 100)
    
    def _generate_recommendations(self, conversion_score: int, seo_score: int, 
                                   offer: Dict, copy: Dict, assets: Dict) -> List[str]:
        """
        Gera recomendações de melhoria
        """
        recommendations = []
        
        # Recomendações de conversão
        if conversion_score < 70:
            if not offer.get("angle"):
                recommendations.append("Defina um angle mais claro e direto (dor → desejo)")
            if not offer.get("mechanism"):
                recommendations.append("Crie um mecanismo único para diferenciar sua oferta")
            if not offer.get("promise"):
                recommendations.append("Adicione uma promessa clara e garantida")
            if len(copy.get("headlines", [])) < 3:
                recommendations.append("Gere mais headlines para teste A/B")
            if len(copy.get("ctas", [])) < 2:
                recommendations.append("Adicione mais CTAs variados")
        
        # Recomendações de SEO
        if seo_score < 70:
            if len(copy.get("seo_meta", {}).get("keywords", [])) < 3:
                recommendations.append("Aumente o número de keywords SEO (mínimo 3)")
            if not copy.get("seo_meta", {}).get("description"):
                recommendations.append("Adicione meta description otimizada")
        
        # Recomendações de assets
        avatar_1 = offer.get("avatar_1_url") or offer.get("avatar_1", {}).get("url")
        avatar_2 = offer.get("avatar_2_url") or offer.get("avatar_2", {}).get("url")
        mascot = offer.get("mascot_url") or offer.get("mascot", {}).get("url")
        
        if not avatar_1:
            recommendations.append("Gere o avatar humano #1")
        if not avatar_2:
            recommendations.append("Gere o avatar humano #2")
        if not mascot:
            recommendations.append("Gere o mascote da marca")
        
        # Recomendações positivas
        if conversion_score >= 80:
            recommendations.append("✓ Oferta com alto potencial de conversão!")
        if seo_score >= 80:
            recommendations.append("✓ SEO bem otimizado!")
        
        return recommendations[:5]  # Máx 5 recomendações
    
    def _identify_strengths(self, offer: Dict, copy: Dict, assets: Dict) -> List[str]:
        """
        Identifica pontos fortes
        """
        strengths = []
        
        if offer.get("angle") and len(offer["angle"]) > 30:
            strengths.append("Angle claro e persuasivo")
        if offer.get("mechanism"):
            strengths.append("Mecanismo único definido")
        if copy.get("headlines") and len(copy["headlines"]) >= 3:
            strengths.append("Múltiplas headlines para teste")
        if copy.get("body_long") and len(copy["body_long"]) > 500:
            strengths.append("Copy completa e detalhada")
        
        return strengths
    
    def _identify_weaknesses(self, offer: Dict, copy: Dict, assets: Dict) -> List[str]:
        """
        Identifica pontos fracos
        """
        weaknesses = []
        
        if not offer.get("angle"):
            weaknesses.append("Angle não definido")
        if not offer.get("mechanism"):
            weaknesses.append("Mecanismo único ausente")
        if not copy.get("headlines"):
            weaknesses.append("Headlines não geradas")
        if not copy.get("body_long"):
            weaknesses.append("Body copy longo ausente")
        
        return weaknesses


# Instância global
dona_benta = DonaBenta()
