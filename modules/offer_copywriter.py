"""
MÓDULO: offer_copywriter.py
DESCRICÃO: Tonho - Copywriter especialista em conversão
FUNÇÃO: Gera headlines, body copy e CTAs baseados no modelo da oferta
"""
import logging
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)


class Tonho:
    """
    Agente Tonho - Copywriter de Alta Conversão
    
    Responsabilidades:
    - Gerar headlines testáveis (A/B/C)
    - Escrever body copy longo, médio e curto
    - Criar CTAs variados
    - Otimizar para SEO com keywords do Dário
    """
    
    def __init__(self):
        self.name = "Tonho"
        self.personality = "Persuasivo, direto, focado em conversão"
    
    async def generate_copy(self, offer_model: Dict[str, Any], investigation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Gera todo o copy da oferta
        
        Args:
            offer_model: Modelo da oferta (angle, mechanism, promise, etc)
            investigation: Dados da investigação do Dário
        
        Returns:
            Dict com todas as variants de copy
        """
        logger.info(f"[Tonho] Gerando copy para oferta")
        
        angle = offer_model.get("angle", "")
        mechanism = offer_model.get("mechanism", "")
        promise = offer_model.get("promise", "")
        keyword = investigation.get("keyword", "")
        keywords = investigation.get("google_keywords", [])
        
        # Gera headlines
        headlines = self._generate_headlines(angle, keyword, promise)
        
        # Gera body copy
        body_long = self._generate_body_long(angle, mechanism, promise, keywords)
        body_short = self._generate_body_short(angle, promise)
        body_middle = self._generate_body_middle(angle, mechanism, promise)
        
        # Gera CTAs
        ctas = self._generate_ctas(angle)
        
        copy = {
            "headlines": headlines,
            "body_long": body_long,
            "body_short": body_short,
            "body_middle": body_middle,
            "ctas": ctas,
            "seo_meta": {
                "title": f"{headlines[0]} | Guia Completo",
                "description": body_short[:155],
                "keywords": [k.get("keyword", "") for k in keywords[:5]]
            },
            "status": "completed",
            "created_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"[Tonho] Copy gerado: {len(headlines)} headlines")
        
        return copy
    
    def _generate_headlines(self, angle: str, keyword: str, promise: str) -> List[str]:
        """Gera 5 headlines para teste A/B/C"""
        headlines = [
            f"Como {angle.split(' ')[0].lower()}{angle.split(' ')[1].lower() if len(angle.split(' ')) > 1 else ''} em 30 dias (método garantido)",
            f"+10.000 pessoas já {promise.split(' ')[3].lower() if len(promise.split(' ')) > 3 else 'transformaram'} sua vida - e você?",
            f"Pare de sofrer com {keyword} - descubra o método que funciona",
            f"Últimas vagas: {promise[:50]} - Garanta seu acesso agora",
            f"Você sabia que {keyword} pode mudar sua vida em 30 dias?"
        ]
        return headlines
    
    def _generate_body_long(self, angle: str, mechanism: str, promise: str, keywords: List[Dict]) -> str:
        """Gera body copy longo (para landing page)"""
        primary_keyword = keywords[0].get("keyword", "") if keywords else "resultados"
        
        body = f"""
# {angle.title()}

Você já se sentiu {primary_keyword.lower()} e pensou que nunca ia conseguir mudar?

Eu sei exatamente como é. Já estive aí.

Mas e se eu te dissesse que existe um {mechanism.lower()} que já ajudou mais de 10.000 pessoas a alcançar {primary_keyword.lower()} em apenas 30 dias?

## O Que Você Vai Conquistar

✓ {promise}
✓ Metodologia passo a passo testada e aprovada
✓ Suporte comunidade exclusiva
✓ Resultados garantidos ou seu dinheiro de volta

## Como Funciona

{n