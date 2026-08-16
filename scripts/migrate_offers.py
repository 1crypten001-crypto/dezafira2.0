"""
MIGRATION: Criar tabelas da Fábrica de Ofertas
USO: python scripts/migrate_offers.py
"""
import sys
import os

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.database import engine, Base

# Importa os modelos para criar as tabelas
from modules.offer_models import (  # noqa: F401
    OfferModel,
    OfferInvestigation,
    OfferKeyword,
    OfferBacklink,
    OfferAsset
)

def migrate():
    """Cria todas as tabelas necessárias"""
    print("[Migration] Criando tabelas da Fábrica de Ofertas...")
    
    # Cria as tabelas
    Base.metadata.create_all(bind=engine)
    
    print("[Migration] Tabelas criadas com sucesso!")
    print("[Migration] Tabelas criadas:")
    print("  - offer_models")
    print("  - offer_investigations")
    print("  - offer_keywords")
    print("  - offer_backlinks")
    print("  - offer_assets")

if __name__ == "__main__":
    migrate()
