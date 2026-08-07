import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ajustar o path para conseguir importar do diretorio de modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.database import Base, User, Channel
from modules.database import _migrate_add_column

def main():
    print("=" * 60)
    print("🔧 DEZAFIRA: INICIALIZADOR DE BANCO DE DADOS POSTGRESQL")
    print("=" * 60)
    
    # 1. Obter a URL de conexao do Postgres
    # Tenta ler a variavel de ambiente DATABASE_URL
    db_url = os.getenv("DATABASE_URL")
    
    if not db_url:
        print("Erro: A variavel de ambiente DATABASE_URL nao esta definida localmente!")
        print("Defina-a usando:")
        print("  $env:DATABASE_URL=\"sua_string_de_conexao\" (no PowerShell)")
        print("  set DATABASE_URL=sua_string_de_conexao (no CMD)")
        sys.exit(1)
        
    # Ajustar compatibilidade de string de conexao
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
        
    print(f"Conectando ao banco de dados: {db_url.split('@')[-1]} ...")
    
    try:
        engine = create_engine(db_url, pool_pre_ping=True)
        # Testar conexao
        with engine.connect() as conn:
            print("[OK] Conexao com o PostgreSQL estabelecida com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao conectar ao PostgreSQL: {e}")
        print("\nDIAGNOSTICO:")
        print("1. Se voce esta usando a URL publica (reseau.proxy.rlwy.net), certifique-se de que")
        print("   o 'Public Access' esta habilitado nas configuracoes do Postgres no Railway.")
        print("2. Se o 'Public Access' nao estiver ativo, voce so conseguira se conectar a essa URL")
        print("   de dentro da rede interna do Railway (usando o host postgres.railway.internal).")
        sys.exit(1)
        
    # 2. Criar tabelas
    print("\n[1/3] Criando tabelas no PostgreSQL...")
    try:
        Base.metadata.create_all(bind=engine)
        print("[OK] Todas as tabelas declaradas foram criadas com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao criar tabelas: {e}")
        sys.exit(1)
        
    # 3. Aplicar migrations manuais das novas colunas
    print("\n[2/3] Aplicando colunas adicionais...")
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            # Coluna de plano do usuario
            _migrate_add_column(conn, "ALTER TABLE users ADD COLUMN IF NOT EXISTS plan VARCHAR(20) DEFAULT 'free';", "users.plan")
            
            # Outras colunas do motor que podem faltar
            _migrate_add_column(conn, "ALTER TABLE predictions ADD COLUMN IF NOT EXISTS approval_status VARCHAR(30) DEFAULT 'pending';", "predictions.approval_status")
            _migrate_add_column(conn, "ALTER TABLE automation_tasks ADD COLUMN IF NOT EXISTS video_url VARCHAR(500);", "automation_tasks.video_url")
            _migrate_add_column(conn, "ALTER TABLE blog_channels ADD COLUMN IF NOT EXISTS banner_url VARCHAR(1000);", "blog_channels.banner_url")
            _migrate_add_column(conn, "ALTER TABLE blog_channels ADD COLUMN IF NOT EXISTS subdomain VARCHAR(100);", "blog_channels.subdomain")
            _migrate_add_column(conn, "ALTER TABLE blog_channels ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP;", "blog_channels.updated_at")
            _migrate_add_column(conn, "ALTER TABLE blog_posts ADD COLUMN IF NOT EXISTS image_provider VARCHAR(100);", "blog_posts.image_provider")
            _migrate_add_column(conn, "ALTER TABLE blog_posts ADD COLUMN IF NOT EXISTS author VARCHAR(200) DEFAULT 'Equipe Dezafira';", "blog_posts.author")
            _migrate_add_column(conn, "ALTER TABLE blog_posts ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP;", "blog_posts.updated_at")
            _migrate_add_column(conn, "ALTER TABLE blog_posts ADD COLUMN IF NOT EXISTS published_at TIMESTAMP;", "blog_posts.published_at")
            _migrate_add_column(conn, "ALTER TABLE blog_posts ADD COLUMN IF NOT EXISTS lili_score INTEGER;", "blog_posts.lili_score")
            print("[OK] Migrations de colunas verificadas!")
    except Exception as e:
        print(f"⚠️ Alerta ao rodar migracao manual: {e}")
        
    # 4. Criar administrador inicial de teste
    print("\n[3/3] Criando usuario de teste administrador...")
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        admin_email = "admin@dezafira.com"
        # Verificar se o usuario ja existe
        existing_user = db.query(User).filter(User.email == admin_email).first()
        if existing_user:
            print(f"[INFO] Usuario '{admin_email}' ja existe. Garantindo plano Pro...")
            existing_user.plan = "pro"
            existing_user.role = "admin"
            db.commit()
            print("[OK] Usuario ja configurado como PRO e Admin!")
        else:
            # Criar novo usuario admin de teste
            # Nota: Usando gerador de hash simples para compatibilidade
            from passlib.hash import bcrypt
            hashed_password = bcrypt.hash("admin123")
            
            new_admin = User(
                email=admin_email,
                name="Admin Dezafira",
                password=hashed_password,
                role="admin",
                plan="pro",
            )
            db.add(new_admin)
            db.commit()
            print(f"[OK] Usuario '{admin_email}' CRIADO com senha 'admin123' e plano PRO!")
    except Exception as e:
        db.rollback()
        print(f"❌ Erro ao configurar usuario admin: {e}")
    finally:
        db.close()
        
    print("\n" + "=" * 60)
    print("✨ PROCEDIMENTO DE INICIALIZACAO DO POSTGRES CONCLUIDO!")
    print("=" * 60)

if __name__ == "__main__":
    main()
