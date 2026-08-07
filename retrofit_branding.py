import asyncio
import json
import os
import sys

# Adicionar pasta do projeto ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.database import SessionLocal, BlogChannel, update_db_blog_channel
from modules.brand_designer import BrandingDesignerAgent

async def main():
    print("=== RETROFIT DE BRANDING AUTOMÁTICO ===")
    print("Este script gera e salva identidades visuais personalizadas para canais sem branding.")
    
    db = SessionLocal()
    try:
        channels = db.query(BlogChannel).all()
        if not channels:
            print("[Info] Nenhum canal de blog encontrado.")
            return
            
        designer = BrandingDesignerAgent()
        for chan in channels:
            # Força o retrofit em todos, ou apenas nos vazios (podemos passar argumento para forçar)
            force = len(sys.argv) > 1 and sys.argv[1] == "--force"
            
            if not chan.brand_config or force:
                print(f"\n[*] Gerando branding para: {chan.name} ({chan.nicho})...")
                try:
                    brand = await designer.generate_branding(
                        blog_name=chan.name,
                        niche=chan.nicho,
                        is_affiliate=chan.is_affiliate
                    )
                    brand_str = json.dumps(brand)
                    success = update_db_blog_channel(chan.id, brand_config=brand_str)
                    if success:
                        print(f"[OK] Branding atualizado com sucesso!")
                    else:
                        print(f"[Erro] Falha ao salvar no banco.")
                except Exception as e:
                    print(f"[Erro] Falha no Seu Design para {chan.name}: {e}")
            else:
                print(f"[Info] {chan.name} já possui branding configurado. Pulei. (Use '--force' para sobrescrever)")
    finally:
        db.close()
        print("\n=== PROCESSO CONCLUÍDO ===")

if __name__ == "__main__":
    asyncio.run(main())
