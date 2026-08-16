"""
MÓDULO: offer_modeler.py
DESCRICÃO: Conselheiro - Modelagem estratégica da oferta
FUNCÃO: Analisa investigação do Dário e define angle, mecanismo, avatar, promessa
"""
import logging
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)


class Conselheiro:
    """
    Agente Conselheiro - Estrategista da Oferta
    
    Responsabilidades:
    - Definir angle estratégico (dor → desejo)
    - Criar mecanismo único
    - Modelar avatares completos
    - Definir promessa e preço
    """
    
    def __init__(self):
        self.name = "Conselheiro"
        self.personality = "Métodológico, analítico, foco em conversão"
    
    async def model_offer(self, investigation: Dict[str, Any], niche: str, keyword: str) -> Dict[str, Any]:
        """
        Modela a oferta completa baseada na investigação do Dário
        
        Args:
            investigation: Dados da investigação (Facebook Ads + Google SEO)
            niche: Nicho do produto
            keyword: Palavra-chave principal
        
        Returns:
            Dict com modelo completo da oferta
        """
        logger.info(f"[Conselheiro] Modelando oferta para: {keyword}")
        
        # Extrai dados da investigação
        facebook_ads = investigation.get("facebook_ads", [])
        facebook_patterns = investigation.get("facebook_patterns", {})
        google_keywords = investigation.get("google_keywords", [])
        
        # Analisa padrões
        angle = self._define_angle(facebook_patterns, google_keywords)
        mechanism = self._define_mechanism(angle, facebook_ads)
        promise = self._define_promise(angle, facebook_patterns)
        
        # Modela avatares
        avatar_1 = self._create_avatar("masculino", angle, niche)
        avatar_2 = self._create_avatar("feminino", angle, niche)
        mascot = self._create_mascot(angle, niche)
        
        # Define preço baseado em benchmarks
        price_cents = self._calculate_price(facebook_ads, niche)
        
        model = {
            "angle": angle,
            "mechanism": mechanism,
            "promise": promise,
            "price_cents": price_cents,
            "avatar_1": avatar_1,
            "avatar_2": avatar_2,
            "mascot": mascot,
            "bonus_suggestions": self._suggest_bonus(niche, angle),
            "objections": self._identify_objections(facebook_patterns),
            "social_proof": self._generate_social_proof(facebook_ads),
            "status": "completed",
            "created_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"[Conselheiro] Modelagem concluída: angle={angle[:50]}...")
        
        return model
    
    def _define_angle(self, patterns: Dict, keywords: List[Dict]) -> str:
        """
        Define o angle estratégico (dor → desejo)
        """
        common_pains = patterns.get("common_pains", [])
        common_desires = patterns.get("common_desires", [])
        
        # Prioriza dores mais comuns
        primary_pain = common_pains[0] if common_pains else "frustração"
        primary_desire = common_desires[0] if common_desires else "resultados"
        
        # Templates de angle
        angle_templates = [
            f"Transforme seu {primary_pain} em {primary_desire} em 30 dias",
            f"O método {primary_desire.title()} que elimina o {primary_pain} para sempre",
            f"Como {primary_desire} sem {primary_pain} (passo a passo)",
            f"Descubra como {len(common_desires) + 5} pessoas já {primary_desire} sem {primary_pain}"
        ]
        
        # Seleciona o melhor angle baseado nas keywords
        if keywords:
            top_keyword = keywords[0].get("keyword", "")
            angle_templates.append(f"Guia completo: {top_keyword} sem {primary_pain}")
        
        return angle_templates[0]
    
    def _define_mechanism(self, angle: str, ads: List[Dict]) -> str:
        """
        Cria o mecanismo único da oferta
        """
        # Analisa anúncios para encontrar mecanismos comuns
        mechanism_keywords = []
        
        for ad in ads[:5]:
            copy = ad.get("ad_copy", "").lower()
            headline = ad.get("headline", "").lower()
            
            # Extrai palavras-chave de mecanismo
            mech_keywords = ["método", "sistema", "protocolo", "fórmula", "passo a passo", "tecnologia"]
            for kw in mech_keywords:
                if kw in copy or kw in headline:
                    mechanism_keywords.append(kw)
        
        # Cria mecanismo único
        if mechanism_keywords:
            primary_mech = mechanism_keywords[0].title()
        else:
            primary_mech = "Método"
        
        mechanism = f"{primary_mech} exclusivo testado por +10.000 pessoas com resultados garantidos em 30 dias"
        
        return mechanism
    
    def _define_promise(self, angle: str, patterns: Dict) -> str:
        """
        Define a promessa da oferta
        """
        common_desires = patterns.get("common_desires", [])
        
        if common_desires:
            primary_desire = common_desires[0]
        else:
            primary_desire = "resultados excepcionais"
        
        promise = f"Você vai {primary_desire} em até 30 dias ou seu dinheiro de volta"
        
        return promise
    
    def _create_avatar(self, gender: str, angle: str, niche: str) -> Dict:
        """
        Cria prompt para geração de avatar
        """
        if gender == "masculino":
            prompt = f"""Avatar humano profissional masculino, estilo fotografia comercial de alta qualidade, 
            fundo branco limpo, iluminação estúdio profissional, expressão confiável e acessível, 
            homem, 35 anos, cabelo bem cuidado, vestimenta casual business (camisa social dobrada), 
            postura aberta e convidativa, sorriso leve, olhar direto para câmera.
            
            Nicho: {niche}
            Angle: {angle[:80]}
            
            Estilo: Foto comercial profissional, cores naturais, alta resolução, 
            fundo neutro para facilitar uso em marketing digital, 
            formato retrato 4:5, composição centralizada."""
            
            return {
                "prompt": prompt,
                "description": "Homem profissional, 35 anos, confiável",
                "use_case": "Landing page principal, anúncios Facebook"
            }
        else:
            prompt = f"""Avatar humana profissional feminina, estilo fotografia comercial de alta qualidade, 
            fundo branco limpo, iluminação estúdio profissional, expressão confiante e energética, 
            mulher, 28 anos, cabelo longo e bem cuidado, vestimenta moderna (blusa colorida), 
            postura dinâmica e envolvente, sorriso genuíno, olhar inspirador.
            
            Nicho: {niche}
            Angle: {angle[:80]}
            
            Estilo: Foto comercial profissional, cores vibrantes, alta resolução, 
            fundo neutro para facilitar uso em marketing digital, 
            formato retrato 4:5, composição centralizada."""
            
            return {
                "prompt": prompt,
                "description": "Mulher profissional, 28 anos, energética",
                "use_case": "Anúncios Instagram, redes sociais"
            }
    
    def _create_mascot(self, angle: str, niche: str) -> Dict:
        """
        Cria prompt para mascote
        """
        prompt = f"""Mascote cartoon 2D, design amigável e memorável, personagem animado estilo flat design,
        cores vibrantes e saturadas, expressão alegre ehelperful, formas arredondadas e suaves.
        
        Conceito: Personificação do {angle[:50]}
        Nicho: {niche}
        
        Estilo: Ilustração digital profissional, vetor limpo, 
        sem sombras complexas, fundo transparente, 
        formato quadrado 1:1, ideal para logos e ícones.
        
        Detalhes: Olhos grandes e expressivos, sorriso amigável, 
        proporções exageradas estilo cartoon moderno,
        paleta de cores: tons quentes (laranja, amarelo) para energia,
        tons frios (azul, verde) para confiança."""
        
        return {
            "prompt": prompt,
            "description": "Mascote cartoon amigável",
            "use_case": "Branding, interfaces, elementos visuais"
        }
    
    def _calculate_price(self, ads: List[Dict], niche: str) -> int:
        """
        Calcula preço sugerido baseado em benchmarks
        """
        # Benchmarks por nicho (em centavos)
        niche_benchmarks = {
            "emagrecimento": 9700,
            "financas": 19700,
            "relacionamentos": 6700,
            "receitas": 4700,
            "marketing": 29700,
            "desenvolvimento_pessoal": 9700,
            "saude": 12700,
            "diy": 3700
        }
        
        # Preço base por nicho
        base_price = niche_benchmarks.get(niche.lower(), 9700)
        
        # Ajusta baseado em anúncios encontrados
        if len(ads) > 10:
            # Nicho competitivo → preço mais alto (mais valor percebido)
            base_price = int(base_price * 1.2)
        
        return base_price
    
    def _suggest_bonus(self, niche: str, angle: str) -> List[str]:
        """
        Sugere bônus para aumentar valor percebido
        """
        bonus_templates = [
            f"Checklist rápido para {niche} em 7 dias",
            f"Template de {niche} pronto para usar",
            f"Acesso ao grupo VIP de {niche}",
            f"Videoaula bônus: {angle[:40]}",
            f"Planilha de acompanhamento de {niche}",
            f"Mentoria em grupo ao vivo sobre {niche}"
        ]
        
        return bonus_templates[:3]
    
    def _identify_objections(self, patterns: Dict) -> List[str]:
        """
        Identifica objeções comuns baseadas nos anúncios
        """
        common_objections = [
            "Não tenho tempo",
            "Já tentei de tudo e não funcionou",
            "É muito caro",
            "Não acredito que vai funcionar para mim",
            "Preciso de mais informações antes",
            "Vou pensar e te aviso"
        ]
        
        # Se tiver padrões de dor, adiciona objeções específicas
        pains = patterns.get("common_pains", [])
        if pains:
            common_objections.insert(0, f"Tenho {pains[0]} e não creo que isso vá ajudar")
        
        return common_objections[:5]
    
    def _generate_social_proof(self, ads: List[Dict]) -> Dict:
        """
        Gera prova social baseada nos anúncios
        """
        if not ads:
            return {
                "testimonials_count": 0,
                "avg_rating": 0,
                "sample_testimonials": []
            }
        
        # Extrai engajamento dos anúncios
        total_engagement = sum(ad.get("engagement", 0) for ad in ads)
        avg_engagement = total_engagement // len(ads) if ads else 0
        
        # Gera depoimentos simulados
        sample_testimonials = [
            "Resultados incríveis em apenas 2 semanas! - Maria S.",
            "Mudou minha vida completamente. Recomendo! - João P.",
            "Melhor investimento que fiz. Resultados reais. - Ana C."
        ]
        
        return {
            "testimonials_count": len(ads) * 150,  # Estimativa
            "avg_rating": 4.8,
            "sample_testimonials": sample_testimonials,
            "avg_engagement": avg_engagement
        }


# Instância global
conselheiro = Conselheiro()
