import os
import uuid
import re
from datetime import datetime
from sqlalchemy import create_engine, Column, String, DateTime, JSON, ForeignKey, Integer, Boolean, text, Text
from sqlalchemy.orm import declarative_base, sessionmaker

# 1. Determinar URL do banco de dados (Railway Postgres ou SQLite local)
# Usa o diretório onde o server.py está rodando como base
SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not SCRIPT_DIR or not os.path.exists(SCRIPT_DIR):
    SCRIPT_DIR = os.getcwd()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    DB_PATH = os.path.join(SCRIPT_DIR, "dezafira.db")
    # Garante que o diretório existe
    try:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    except Exception as e:
        print(f"[Database] Erro ao buscar subdominio: {e}")
    # No Windows, SQLAlchemy requer forward slashes no path do SQLite
    db_path_unix = DB_PATH.replace("\\", "/")
    DATABASE_URL = f"sqlite:///{db_path_unix}"

# 2. Configurar o Engine e Sessão com Fallback Resiliente
try:
    # Ajuste de compatibilidade para postgresql:// no SQLAlchemy 1.4+
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
        
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    # Testar conexão
    with engine.connect() as conn:
        pass
except Exception as db_err:
    print(f"[Database]  Aviso: falha ao conectar no banco configurado: {str(db_err)}")
    print("[Database] Usando SQLite em memória como fallback. Dados não persistem entre deploys.")
    print("[Database] Para usar PostgreSQL, verifique a variável DATABASE_URL no Railway.")
    DATABASE_URL = "sqlite:///:memory:"
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 3. Modelos ORM
class Channel(Base):
    __tablename__ = "channels"

    id = Column(String(50), primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    nicho = Column(String(100), default="Geral")
    lang = Column(String(10), default="PT")
    status = Column(String(20), default="active")
    monetization_step = Column(String(30), default="setup")
    cookies = Column(String(10000), nullable=True)
    connection_status = Column(String(30), default="idle")
    verification_code = Column(String(20), nullable=True)
    connection_error = Column(String(500), nullable=True)

class AiCreatedChannel(Base):
    __tablename__ = "ai_created_channels"

    id = Column(String(50), primary_key=True, index=True)
    channel_id = Column(String(50), nullable=False) # FK do Canal da conta Google
    name = Column(String(100), nullable=False)
    nicho = Column(String(100), default="Geral")
    lang = Column(String(10), default="PT")
    creation_reason = Column(String(2000), nullable=True)
    subscribers = Column(Integer, default=0)
    videos_posted = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(String(50), primary_key=True, index=True)
    status = Column(String(30), default="starting")
    prompt = Column(String(500), nullable=False)
    error = Column(String(1000), nullable=True)
    video_url = Column(String(500), nullable=True)
    channel_id = Column(String(50), nullable=True)
    approval_status = Column(String(30), default="pending")  # pending, approved, rejected
    created_at = Column(DateTime, default=datetime.utcnow)

class AutomationTask(Base):
    __tablename__ = 'automation_tasks'
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    channel_id = Column(String(50), ForeignKey('channels.id'), nullable=True)
    title_suggestion = Column(String(255), nullable=True)
    status = Column(String(50), default='triage') # triage, writing, SEO, production, ready, done, failed
    script_content = Column(Text, nullable=True)
    metadata_tags = Column(Text, nullable=True)
    video_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ChannelKnowledge(Base):
    """Shared Memory / Shared Brain — agentes armazenam aprendizados aqui."""
    __tablename__ = 'channel_knowledge'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    channel_id = Column(String(50), ForeignKey('channels.id'), nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True)  # style_guide, seo_blacklist, pexels_fallback, audience_insight, growth_hack
    meta_key = Column(String(100), nullable=False, index=True)  # Ex: 'tom_de_voz', 'failed_keyword_X'
    meta_value = Column(Text, nullable=False)  # Ex: 'Sombrio e misterioso', 'Evitar buscar'
    source = Column(String(50), nullable=True)  # Quem escreveu: 'hermes', 'deepseek', 'user_feedback'
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DeliverableApp(Base):
    __tablename__ = "deliverable_apps"

    id = Column(String(50), primary_key=True, index=True)
    channel_id = Column(String(50), nullable=False)
    name = Column(String(100), nullable=False)
    slug = Column(String(100), unique=True, index=True)
    nicho = Column(String(100), nullable=False)
    app_type = Column(String(50), default="quiz_diagnostico")
    config_json = Column(JSON, nullable=False)
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)


class AppPayment(Base):
    __tablename__ = "app_payments"

    id = Column(String(50), primary_key=True, index=True)
    app_id = Column(String(50), nullable=False)
    gateway = Column(String(50), nullable=False)
    transaction_id = Column(String(100), unique=True, index=True)
    status = Column(String(20), default="pending")
    amount = Column(Integer, nullable=False)
    customer_email = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class BlogChannel(Base):
    __tablename__ = "blog_channels"

    id = Column(String(50), primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    nicho = Column(String(100), default="Geral")
    lang = Column(String(10), default="PT")
    platform = Column(String(50), default="wordpress")
    site_url = Column(String(500), nullable=True)
    api_endpoint = Column(String(500), nullable=True)
    api_token = Column(String(2000), nullable=True)
    username = Column(String(100), nullable=True)
    app_password = Column(String(500), nullable=True)
    status = Column(String(20), default="active")
    frequency = Column(String(20), default="daily")
    banner_url = Column(String(1000), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Colunas do Modo Afiliado
    is_affiliate = Column(Boolean, default=False)
    affiliate_providers = Column(String(500), nullable=True)
    amazon_tag = Column(String(100), nullable=True)
    amazon_key = Column(String(200), nullable=True)
    amazon_secret = Column(String(200), nullable=True)
    shopee_app_id = Column(String(100), nullable=True)
    shopee_app_secret = Column(String(200), nullable=True)
    mercadolivre_client_id = Column(String(100), nullable=True)
    mercadolivre_client_secret = Column(String(200), nullable=True)
    mercadolivre_access_token = Column(String(1000), nullable=True)
    mercadolivre_refresh_token = Column(String(1000), nullable=True)
    mercadolivre_token_expires = Column(DateTime, nullable=True)
    
    # Estratégia Google Discover
    is_discover = Column(Boolean, default=False)
    
    # Configuração de branding customizada (JSON em formato string)
    brand_config = Column(Text, nullable=True)


class BlogPost(Base):
    __tablename__ = "blog_posts"

    id = Column(String(50), primary_key=True, index=True)
    channel_id = Column(String(50), ForeignKey("blog_channels.id"), nullable=True)
    title = Column(String(500), nullable=False)
    author = Column(String(200), default="Equipe Dezafira")
    slug = Column(String(500), nullable=True)
    content = Column(Text, nullable=True)
    excerpt = Column(String(1000), nullable=True)
    keywords = Column(String(1000), nullable=True)
    featured_image_url = Column(String(1000), nullable=True)
    image_provider = Column(String(100), default="pexels", nullable=True)
    status = Column(String(30), default="draft")
    platform_status = Column(String(30), nullable=True)
    platform_post_id = Column(String(100), nullable=True)
    platform_url = Column(String(1000), nullable=True)
    word_count = Column(Integer, default=0)
    topic = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    published_at = Column(DateTime, nullable=True)
    lili_score = Column(Integer, nullable=True)
    lili_approved = Column(Boolean, nullable=True)
    lili_reviewed_at = Column(DateTime, nullable=True)


class AffiliateClick(Base):
    __tablename__ = "affiliate_clicks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(String(50), ForeignKey("blog_posts.id"), nullable=True, index=True)
    provider = Column(String(50), nullable=False) # amazon, shopee, mercadolivre
    product_name = Column(String(255), nullable=True)
    clicked_at = Column(DateTime, default=datetime.utcnow)
    user_ip = Column(String(100), nullable=True)



class BlogSubdomain(Base):
    """Mapeamento subdominio -> blog (tabela separada)."""
    __tablename__ = "blog_subdomains"

    id = Column(Integer, primary_key=True, autoincrement=True)
    channel_id = Column(String(50), ForeignKey("blog_channels.id"), nullable=False, index=True)
    subdomain = Column(String(100), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class BlogSection(Base):
    """Seção/micro-nicho dentro de um blog."""
    __tablename__ = "blog_sections"

    id = Column(String(50), primary_key=True, index=True)
    channel_id = Column(String(50), ForeignKey("blog_channels.id"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    slug = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    keywords = Column(String(2000), nullable=True)
    target_articles = Column(Integer, default=5)
    sort_order = Column(Integer, default=0)
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)


class BlogPipelineRun(Base):
    """Registro de execução do pipeline de blog."""
    __tablename__ = "blog_pipeline_runs"

    id = Column(String(50), primary_key=True, index=True)
    channel_id = Column(String(50), ForeignKey("blog_channels.id"), nullable=False, index=True)
    blog_name = Column(String(200), nullable=True)
    niche = Column(String(200), nullable=True)
    language = Column(String(10), default="pt")
    phase = Column(String(30), default="fundacao")  # fundacao, arquitetura, producao, refino, entrega
    status = Column(String(20), default="running")
    total_articles_target = Column(Integer, default=3)
    articles_generated = Column(Integer, default=0)
    current_round = Column(Integer, default=0)
    pipeline_data = Column(JSON, nullable=True)  # Checkpoint completo do estado
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    error = Column(String(2000), nullable=True)


class RegenerationJob(Base):
    """Job de regeneracao em lote (persistido para sobreviver a restarts)."""
    __tablename__ = "regeneration_jobs"

    id = Column(String(50), primary_key=True, index=True)
    status = Column(String(20), default="running")  # running, done, failed
    total = Column(Integer, default=0)
    processed = Column(Integer, default=0)
    succeeded = Column(Integer, default=0)
    failed = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    error = Column(String(2000), nullable=True)


class RegenerationJobItem(Base):
    """Item de um job de regeneracao (1 linha por artigo)."""
    __tablename__ = "regeneration_job_items"

    id = Column(String(50), primary_key=True, index=True)
    job_id = Column(String(50), ForeignKey("regeneration_jobs.id"), index=True)
    post_id = Column(String(50), index=True)
    post_title = Column(String(500), nullable=True)
    status = Column(String(20), default="pending")  # pending, processing, done, failed
    error = Column(String(2000), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ═══════════════════════════════════════════════════════════════════════════════
# MODELOS — FABRICA DE LIVROS
# ═══════════════════════════════════════════════════════════════════════════════

class Book(Base):
    """Livro gerado pela Fabrica de Livros."""
    __tablename__ = "books"

    id = Column(String(50), primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    subtitle = Column(String(500), nullable=True)
    author = Column(String(200), default="Dezafira Editorial")
    description = Column(Text, nullable=True)
    cover_url = Column(String(1000), nullable=True)
    topic = Column(String(500), nullable=True)
    keywords = Column(String(1000), nullable=True)
    status = Column(String(30), default="draft")
    total_chapters = Column(Integer, default=0)
    total_words = Column(Integer, default=0)
    price_cents = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    published_at = Column(DateTime, nullable=True)


class BookChapter(Base):
    """Capitulo de livro."""
    __tablename__ = "book_chapters"

    id = Column(String(50), primary_key=True, index=True)
    book_id = Column(String(50), ForeignKey("books.id"), nullable=False, index=True)
    chapter_number = Column(Integer, nullable=False)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=True)
    word_count = Column(Integer, default=0)
    status = Column(String(20), default="draft")
    created_at = Column(DateTime, default=datetime.utcnow)


class BookFormat(Base):
    """Formato de exportacao do livro."""
    __tablename__ = "book_formats"

    id = Column(String(50), primary_key=True, index=True)
    book_id = Column(String(50), ForeignKey("books.id"), nullable=False, index=True)
    format_type = Column(String(10), nullable=False)
    file_url = Column(String(1000), nullable=True)
    file_size_bytes = Column(Integer, default=0)
    generated_at = Column(DateTime, default=datetime.utcnow)


# ═══════════════════════════════════════════════════════════════════════════════
# MODELOS — FABRICA DE CURSOS
# ═══════════════════════════════════════════════════════════════════════════════

class Course(Base):
    """Curso gerado pela Fabrica de Cursos."""
    __tablename__ = "courses"

    id = Column(String(50), primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    subtitle = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    topic = Column(String(500), nullable=True)
    keywords = Column(String(1000), nullable=True)
    status = Column(String(30), default="draft")  # draft, publishing, completed
    total_modules = Column(Integer, default=0)
    total_lessons = Column(Integer, default=0)
    total_lessons_completed = Column(Integer, default=0)
    estimated_hours = Column(Integer, default=0)
    difficulty = Column(String(20), default="iniciante")  # iniciante, intermediario, avancado
    price_cents = Column(Integer, default=0)
    cover_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    published_at = Column(DateTime, nullable=True)


class CourseModule(Base):
    """Modulo de curso."""
    __tablename__ = "course_modules"

    id = Column(String(50), primary_key=True, index=True)
    course_id = Column(String(50), ForeignKey("courses.id"), nullable=False, index=True)
    module_number = Column(Integer, nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class CourseLesson(Base):
    """Aula de curso."""
    __tablename__ = "course_lessons"

    id = Column(String(50), primary_key=True, index=True)
    module_id = Column(String(50), ForeignKey("course_modules.id"), nullable=False, index=True)
    lesson_number = Column(Integer, nullable=False)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=True)
    content_type = Column(String(30), default="texto")  # texto, video_url, pdf_ref
    word_count = Column(Integer, default=0)
    estimated_minutes = Column(Integer, default=10)
    created_at = Column(DateTime, default=datetime.utcnow)


class CourseMaterial(Base):
    """Material complementar de aula."""
    __tablename__ = "course_materials"

    id = Column(String(50), primary_key=True, index=True)
    lesson_id = Column(String(50), ForeignKey("course_lessons.id"), nullable=False, index=True)
    material_type = Column(String(30), nullable=False)  # pdf_resumo, exercicio, quiz, infografico
    title = Column(String(500), nullable=True)
    content = Column(Text, nullable=True)
    file_url = Column(String(1000), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class CourseQuiz(Base):
    """Questoes de quiz para aula."""
    __tablename__ = "course_quizzes"

    id = Column(String(50), primary_key=True, index=True)
    lesson_id = Column(String(50), ForeignKey("course_lessons.id"), nullable=False, index=True)
    questions_json = Column(JSON, nullable=False)  # Lista de {pergunta, alternativas, resposta_correta}
    created_at = Column(DateTime, default=datetime.utcnow)


# Criar tabelas se não existirem com tratamento de erro
def _migrate_add_column(conn, sql, label):
    """Adiciona coluna de forma idempotente (ADD COLUMN IF NOT EXISTS).
    Em qualquer falha faz rollback para nao abortar a transacao do
    PostgreSQL (transacao abortada derruba todos os ALTERs seguintes)
    e tenta fallback sem IF NOT EXISTS para SQLite antigo."""
    try:
        conn.execute(text(sql))
        conn.commit()
        print(f"[Database] Migration OK: {label}")
        return True
    except Exception as e1:
        conn.rollback()
        if "IF NOT EXISTS" in sql:
            try:
                conn.execute(text(sql.replace("ADD COLUMN IF NOT EXISTS", "ADD COLUMN")))
                conn.commit()
                print(f"[Database] Migration OK (fallback): {label}")
                return True
            except Exception as e2:
                conn.rollback()
                # Ambos os caminhos falharam: registrar para que drift real nunca
                # fique invisivel (coluna/ tabela inexistente ou nome errado).
                print(f"[Database] Migration FAILED: {label} (primary={e1} / fallback={e2})")
        else:
            print(f"[Database] Migration FAILED: {label}: {e1}")
        return False


try:
    Base.metadata.create_all(bind=engine)

    # Migrations manuais — idempotentes e a prova de falhas
    with engine.connect() as conn:
        _migrate_add_column(conn, "ALTER TABLE predictions ADD COLUMN IF NOT EXISTS approval_status VARCHAR(30) DEFAULT 'pending';", "predictions.approval_status")
        _migrate_add_column(conn, "ALTER TABLE automation_tasks ADD COLUMN IF NOT EXISTS video_url VARCHAR(500);", "automation_tasks.video_url")
        _migrate_add_column(conn, "ALTER TABLE blog_channels ADD COLUMN IF NOT EXISTS banner_url VARCHAR(1000);", "blog_channels.banner_url")
        _migrate_add_column(conn, "ALTER TABLE blog_channels ADD COLUMN IF NOT EXISTS subdomain VARCHAR(100);", "blog_channels.subdomain")
        _migrate_add_column(conn, "ALTER TABLE blog_channels ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP;", "blog_channels.updated_at")
        # blog_posts — colunas que podem faltar em bancos criados antes do model atual
        _migrate_add_column(conn, "ALTER TABLE blog_posts ADD COLUMN IF NOT EXISTS image_provider VARCHAR(100);", "blog_posts.image_provider")
        _migrate_add_column(conn, "ALTER TABLE blog_posts ADD COLUMN IF NOT EXISTS author VARCHAR(200) DEFAULT 'Equipe Dezafira';", "blog_posts.author")
        _migrate_add_column(conn, "ALTER TABLE blog_posts ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP;", "blog_posts.updated_at")
        _migrate_add_column(conn, "ALTER TABLE blog_posts ADD COLUMN IF NOT EXISTS published_at TIMESTAMP;", "blog_posts.published_at")
        _migrate_add_column(conn, "ALTER TABLE blog_posts ADD COLUMN IF NOT EXISTS lili_score INTEGER;", "blog_posts.lili_score")
        _migrate_add_column(conn, "ALTER TABLE blog_posts ADD COLUMN IF NOT EXISTS lili_approved BOOLEAN;", "blog_posts.lili_approved")
        _migrate_add_column(conn, "ALTER TABLE blog_posts ADD COLUMN IF NOT EXISTS lili_reviewed_at TIMESTAMP;", "blog_posts.lili_reviewed_at")

        # Migrações do Modo Afiliado no blog_channels
        _migrate_add_column(conn, "ALTER TABLE blog_channels ADD COLUMN IF NOT EXISTS is_affiliate BOOLEAN DEFAULT FALSE;", "blog_channels.is_affiliate")
        _migrate_add_column(conn, "ALTER TABLE blog_channels ADD COLUMN IF NOT EXISTS affiliate_providers VARCHAR(500);", "blog_channels.affiliate_providers")
        _migrate_add_column(conn, "ALTER TABLE blog_channels ADD COLUMN IF NOT EXISTS amazon_tag VARCHAR(100);", "blog_channels.amazon_tag")
        _migrate_add_column(conn, "ALTER TABLE blog_channels ADD COLUMN IF NOT EXISTS amazon_key VARCHAR(200);", "blog_channels.amazon_key")
        _migrate_add_column(conn, "ALTER TABLE blog_channels ADD COLUMN IF NOT EXISTS amazon_secret VARCHAR(200);", "blog_channels.amazon_secret")
        _migrate_add_column(conn, "ALTER TABLE blog_channels ADD COLUMN IF NOT EXISTS shopee_app_id VARCHAR(100);", "blog_channels.shopee_app_id")
        _migrate_add_column(conn, "ALTER TABLE blog_channels ADD COLUMN IF NOT EXISTS shopee_app_secret VARCHAR(200);", "blog_channels.shopee_app_secret")
        _migrate_add_column(conn, "ALTER TABLE blog_channels ADD COLUMN IF NOT EXISTS mercadolivre_client_id VARCHAR(100);", "blog_channels.mercadolivre_client_id")
        _migrate_add_column(conn, "ALTER TABLE blog_channels ADD COLUMN IF NOT EXISTS mercadolivre_client_secret VARCHAR(200);", "blog_channels.mercadolivre_client_secret")
        _migrate_add_column(conn, "ALTER TABLE blog_channels ADD COLUMN IF NOT EXISTS mercadolivre_access_token VARCHAR(1000);", "blog_channels.mercadolivre_access_token")
        _migrate_add_column(conn, "ALTER TABLE blog_channels ADD COLUMN IF NOT EXISTS mercadolivre_refresh_token VARCHAR(1000);", "blog_channels.mercadolivre_refresh_token")
        _migrate_add_column(conn, "ALTER TABLE blog_channels ADD COLUMN IF NOT EXISTS mercadolivre_token_expires TIMESTAMP;", "blog_channels.mercadolivre_token_expires")
        _migrate_add_column(conn, "ALTER TABLE blog_channels ADD COLUMN IF NOT EXISTS is_discover BOOLEAN DEFAULT FALSE;", "blog_channels.is_discover")
        _migrate_add_column(conn, "ALTER TABLE blog_channels ADD COLUMN IF NOT EXISTS brand_config TEXT;", "blog_channels.brand_config")


except Exception as table_err:
    print(f"[Database]  Falha ao criar tabelas no banco original: {str(table_err)}")
    print("[Database] Recaindo para banco em memória (sqlite:///:memory:) para tabelas")
    DATABASE_URL = "sqlite:///:memory:"
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

# 4. Funções auxiliares de compatibilidade para o server.py
def get_db_channels():
    db = SessionLocal()
    try:
        channels = db.query(Channel).all()
        # Se o banco estiver vazio, cria as contas Google e canais criados por IA de teste iniciais
        # Banco limpo
        pass
            
        return [
            {
                "id": c.id,
                "name": c.name,
                "nicho": c.nicho,
                "lang": c.lang,
                "status": c.status,
                "monetization_step": c.monetization_step,
                "has_token": c.cookies is not None,
                "connection_status": c.connection_status,
                "connection_error": c.connection_error
            } for c in channels
        ]
    finally:
        db.close()

def save_db_channel_cookies(channel_id: str, cookies_json: str) -> bool:
    db = SessionLocal()
    try:
        chan = db.query(Channel).filter(Channel.id == channel_id).first()
        if chan:
            chan.cookies = cookies_json
            chan.monetization_step = "publishing"  # Marca o canal como ativo/vinculado
            chan.connection_status = "connected"
            chan.verification_code = None
            chan.connection_error = None
            db.commit()
            return True
        return False
    finally:
        db.close()

def create_db_channel(name: str, nicho: str, lang: str):
    db = SessionLocal()
    try:
        new_chan = Channel(
            id=f"ch_{uuid.uuid4().hex[:6]}",
            name=name,
            nicho=nicho,
            lang=lang,
            status="active",
            monetization_step="setup"
        )
        db.add(new_chan)
        db.flush()
        
        # Store subdomain in separate table
        if not subdomain:
            import unicodedata as _ud, re as _re
            subdomain = name.lower().replace(" ", "").replace("-", "")[:50]
            subdomain = _ud.normalize("NFKD", subdomain).encode("ascii", "ignore").decode("ascii")
            subdomain = subdomain.replace("[", "").replace("]", "").replace("(", "").replace(")", "")
            subdomain = subdomain.replace("?", "").replace("!", "").replace(",", "").replace(".", "")
            subdomain = subdomain.replace(":", "").replace(";", "").replace("'", '').replace('"', "")
            subdomain = subdomain.replace("@", "").replace("#", "").replace("$", "").replace("%", "")
            subdomain = _re.sub(r"[^a-z0-9-]", "", subdomain)
        
        existing_sd = db.query(BlogSubdomain).filter(BlogSubdomain.subdomain == subdomain).first()
        if not existing_sd:
            sd_entry = BlogSubdomain(channel_id=new_chan.id, subdomain=subdomain)
            db.add(sd_entry)
        
        db.commit()
        return {
            "id": new_chan.id,
            "name": new_chan.name,
            "nicho": new_chan.nicho,
            "lang": new_chan.lang,
            "status": new_chan.status,
            "monetization_step": new_chan.monetization_step
        }
    finally:
        db.close()

def delete_db_channel(channel_id: str) -> bool:
    db = SessionLocal()
    try:
        # Remover subcanais da IA em cascata
        db.query(AiCreatedChannel).filter(AiCreatedChannel.channel_id == channel_id).delete(synchronize_session=False)
        # Remover predições
        db.query(Prediction).filter(Prediction.channel_id == channel_id).delete(synchronize_session=False)
        
        chan = db.query(Channel).filter(Channel.id == channel_id).first()
        if chan:
            db.delete(chan)
            db.commit()
            return True
        return False
    except Exception as e:
        print(f"[Database] Erro ao deletar em cascata: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def save_db_prediction(pred_id: str, prompt: str, channel_id: str = "default"):
    db = SessionLocal()
    try:
        pred = Prediction(
            id=pred_id,
            status="starting",
            prompt=prompt,
            channel_id=channel_id
        )
        db.add(pred)
        db.commit()
    finally:
        db.close()

def update_db_prediction(pred_id: str, status: str, video_url: str = None, error: str = None):
    db = SessionLocal()
    try:
        pred = db.query(Prediction).filter(Prediction.id == pred_id).first()
        if pred:
            pred.status = status
            if video_url:
                pred.video_url = video_url
            if error:
                pred.error = error
            db.commit()
    finally:
        db.close()

def get_db_prediction(pred_id: str):
    db = SessionLocal()
    try:
        pred = db.query(Prediction).filter(Prediction.id == pred_id).first()
        if pred:
            return {
                "id": pred.id,
                "status": pred.status,
                "prompt": pred.prompt,
                "error": pred.error,
                "url": pred.video_url
            }
        return None
    finally:
        db.close()

def get_db_ai_created_channels() -> list:
    db = SessionLocal()
    try:
        channels = db.query(AiCreatedChannel).order_by(AiCreatedChannel.created_at.desc()).all()
        return [
            {
                "id": c.id,
                "channel_id": c.channel_id,
                "name": c.name,
                "nicho": c.nicho,
                "lang": c.lang,
                "creation_reason": c.creation_reason,
                "subscribers": c.subscribers,
                "videos_posted": c.videos_posted,
                "created_at": c.created_at.isoformat() if c.created_at else None
            } for c in channels
        ]
    finally:
        db.close()

def create_db_ai_created_channel(channel_id: str, name: str, nicho: str, lang: str, creation_reason: str):
    db = SessionLocal()
    try:
        import uuid
        new_sub = AiCreatedChannel(
            id=f"sub_{uuid.uuid4().hex[:6]}",
            channel_id=channel_id,
            name=name,
            nicho=nicho,
            lang=lang,
            creation_reason=creation_reason,
            subscribers=0,
            videos_posted=0
        )
        db.add(new_sub)
        db.commit()
        return {
            "id": new_sub.id,
            "name": new_sub.name,
            "nicho": new_sub.nicho,
            "lang": new_sub.lang
        }
    finally:
        db.close()

def delete_db_ai_created_channel(sub_id: str) -> bool:
    db = SessionLocal()
    try:
        sub = db.query(AiCreatedChannel).filter(AiCreatedChannel.id == sub_id).first()
        if sub:
            db.delete(sub)
            db.commit()
            return True
        return False
    finally:
        db.close()

def create_automation_task(title_suggestion: str, channel_id: str = None):
    db = SessionLocal()
    try:
        new_task = AutomationTask(
            title_suggestion=title_suggestion,
            channel_id=channel_id,
            status='triage'
        )
        db.add(new_task)
        db.commit()
        db.refresh(new_task)
        return new_task.id
    finally:
        db.close()

def update_automation_task(task_id: int, **kwargs):
    db = SessionLocal()
    try:
        task = db.query(AutomationTask).filter(AutomationTask.id == task_id).first()
        if task:
            for key, value in kwargs.items():
                if hasattr(task, key):
                    setattr(task, key, value)
            db.commit()
    finally:
        db.close()

def get_automation_task(task_id: int):
    db = SessionLocal()
    try:
        task = db.query(AutomationTask).filter(AutomationTask.id == task_id).first()
        if task:
            return {
                'id': task.id,
                'channel_id': task.channel_id,
                'title_suggestion': task.title_suggestion,
                'status': task.status,
                'script_content': task.script_content,
                'metadata_tags': task.metadata_tags,
                'video_url': task.video_url,
                'created_at': task.created_at.isoformat() if task.created_at else None,
                'updated_at': task.updated_at.isoformat() if task.updated_at else None
            }
        return None
    finally:
        db.close()


def create_db_deliverable_app(channel_id: str, name: str, slug: str, nicho: str, app_type: str, config_json: dict):
    db = SessionLocal()
    try:
        new_app = DeliverableApp(
            id=f"app_{uuid.uuid4().hex[:6]}",
            channel_id=channel_id,
            name=name,
            slug=slug,
            nicho=nicho,
            app_type=app_type,
            config_json=config_json,
            status="active"
        )
        db.add(new_app)
        db.commit()
        return {
            "id": new_app.id,
            "channel_id": new_app.channel_id,
            "name": new_app.name,
            "slug": new_app.slug,
            "nicho": new_app.nicho,
            "app_type": new_app.app_type,
            "config_json": new_app.config_json,
            "status": new_app.status,
            "created_at": new_app.created_at.isoformat() if new_app.created_at else None
        }
    finally:
        db.close()

def get_db_deliverable_app_by_slug(slug: str):
    db = SessionLocal()
    try:
        app = db.query(DeliverableApp).filter(DeliverableApp.slug == slug).first()
        if app:
            return {
                "id": app.id,
                "channel_id": app.channel_id,
                "name": app.name,
                "slug": app.slug,
                "nicho": app.nicho,
                "app_type": app.app_type,
                "config_json": app.config_json,
                "status": app.status,
                "created_at": app.created_at.isoformat() if app.created_at else None
            }
        return None
    finally:
        db.close()

def get_db_deliverable_apps():
    db = SessionLocal()
    try:
        apps = db.query(DeliverableApp).order_by(DeliverableApp.created_at.desc()).all()
        return [
            {
                "id": app.id,
                "channel_id": app.channel_id,
                "name": app.name,
                "slug": app.slug,
                "nicho": app.nicho,
                "app_type": app.app_type,
                "config_json": app.config_json,
                "status": app.status,
                "created_at": app.created_at.isoformat() if app.created_at else None
            } for app in apps
        ]
    finally:
        db.close()

def create_db_app_payment(app_id: str, gateway: str, transaction_id: str, amount: int, customer_email: str = None):
    db = SessionLocal()
    try:
        payment = AppPayment(
            id=f"pay_{uuid.uuid4().hex[:6]}",
            app_id=app_id,
            gateway=gateway,
            transaction_id=transaction_id,
            status="pending",
            amount=amount,
            customer_email=customer_email
        )
        db.add(payment)
        db.commit()
        return {
            "id": payment.id,
            "app_id": payment.app_id,
            "gateway": payment.gateway,
            "transaction_id": payment.transaction_id,
            "status": payment.status,
            "amount": payment.amount,
            "customer_email": payment.customer_email
        }
    finally:
        db.close()

def update_db_app_payment(transaction_id: str, status: str):
    db = SessionLocal()
    try:
        pay = db.query(AppPayment).filter(AppPayment.transaction_id == transaction_id).first()
        if pay:
            pay.status = status
            db.commit()
            return True
        return False
    finally:
        db.close()


# ─── Blog CRUD ─────────────────────────────────────────────────────────

def create_db_blog_channel(name: str, nicho: str, lang: str, platform: str = "wordpress",
                           site_url: str = "", api_endpoint: str = "", api_token: str = "",
                           subdomain: str = "", is_affiliate: bool = False, is_discover: bool = False,
                           brand_config: str = None) -> dict:
    db = SessionLocal()
    try:
        # Auto-generate subdomain from name if not provided
        if not subdomain:
            import unicodedata
            subdomain = name.lower().replace(" ", "").replace("-", "")[:50]
            subdomain = unicodedata.normalize('NFKD', subdomain).encode('ascii', 'ignore').decode('ascii')
            subdomain = subdomain.replace("[", "").replace("]", "").replace("(", "").replace(")", "")
            subdomain = subdomain.replace("?", "").replace("!", "").replace(",", "").replace(".", "")
            subdomain = subdomain.replace(":", "").replace(";", "").replace("'", "").replace('"', "")
            subdomain = subdomain.replace("@", "").replace("#", "").replace("$", "").replace("%", "")
            subdomain = re.sub(r'[^a-z0-9-]', '', subdomain)
        
        new_chan = BlogChannel(
            id=f"blg_{uuid.uuid4().hex[:6]}",
            name=name,
            nicho=nicho,
            lang=lang,
            platform=platform,
            site_url=site_url,
            api_endpoint=api_endpoint,
            api_token=api_token,
            status="active",
            is_affiliate=is_affiliate,
            is_discover=is_discover,
            brand_config=brand_config,
        )
        db.add(new_chan)
        db.commit()
        return {
            "id": new_chan.id,
            "name": new_chan.name,
            "nicho": new_chan.nicho,
            "lang": new_chan.lang,
            "subdomain": subdomain,
            "platform": new_chan.platform,
            "site_url": new_chan.site_url,
            "status": new_chan.status,
        }
    finally:
        db.close()

def get_db_blog_channels() -> list:
    db = SessionLocal()
    try:
        channels = db.query(BlogChannel).order_by(BlogChannel.created_at.desc()).all()
        return [
            {
                "id": c.id,
                "name": c.name,
                "nicho": c.nicho,
                "lang": c.lang,
                "subdomain": __get_subdomain_for_channel(c.id, c.name.lower().replace(" ", "-")[:50]),
                "platform": c.platform,
                "site_url": c.site_url,
                "status": c.status,
                "frequency": c.frequency,
                "created_at": c.created_at.isoformat() if c.created_at else None,
                "is_affiliate": c.is_affiliate,
                "is_discover": getattr(c, "is_discover", False),
                "brand_config": getattr(c, "brand_config", None),
                "affiliate_providers": c.affiliate_providers,
                "amazon_tag": c.amazon_tag,
                "amazon_key": c.amazon_key,
                "amazon_secret": c.amazon_secret,
                "shopee_app_id": c.shopee_app_id,
                "shopee_app_secret": c.shopee_app_secret,
                "mercadolivre_client_id": c.mercadolivre_client_id,
                "mercadolivre_client_secret": c.mercadolivre_client_secret,
                "mercadolivre_access_token": c.mercadolivre_access_token,
                "mercadolivre_refresh_token": c.mercadolivre_refresh_token,
                "mercadolivre_token_expires": c.mercadolivre_token_expires.isoformat() if c.mercadolivre_token_expires else None,
            } for c in channels
        ]

    finally:
        db.close()

def delete_db_blog_channel(channel_id: str) -> bool:
    db = SessionLocal()
    try:
        db.query(BlogPost).filter(BlogPost.channel_id == channel_id).delete(synchronize_session=False)
        chan = db.query(BlogChannel).filter(BlogChannel.id == channel_id).first()
        if chan:
            db.delete(chan)
            db.commit()
            return True
        return False
    except Exception as e:
        print(f"[Database] Erro ao deletar blog channel: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def create_db_blog_post(channel_id: str, title: str, slug: str, content: str,
                        excerpt: str = "", keywords: str = "", topic: str = "",
                        author: str = "Equipe Dezafira") -> dict:
    db = SessionLocal()
    try:
        new_post = BlogPost(
            id=f"post_{uuid.uuid4().hex[:8]}",
            channel_id=channel_id,
            title=title,
            slug=slug,
            content=content,
            excerpt=excerpt,
            keywords=keywords,
            topic=topic,
            author=author,
            status="draft",
            word_count=len(content.split()),
        )
        db.add(new_post)
        db.commit()
        return {
            "id": new_post.id,
            "title": new_post.title,
            "slug": new_post.slug,
            "status": new_post.status,
            "word_count": new_post.word_count,
            "created_at": new_post.created_at.isoformat() if new_post.created_at else None,
        }
    finally:
        db.close()

def get_db_blog_posts(channel_id: str = None, limit: int = 50) -> list:
    db = SessionLocal()
    try:
        q = db.query(BlogPost).order_by(BlogPost.created_at.desc())
        if channel_id:
            q = q.filter(BlogPost.channel_id == channel_id)
        posts = q.limit(limit).all()
        return [
            {
                "id": p.id,
                "channel_id": p.channel_id,
                "title": p.title,
                "slug": p.slug,
                "excerpt": p.excerpt,
                "keywords": p.keywords,
                "featured_image_url": p.featured_image_url,
                "image_provider": getattr(p, "image_provider", "pexels") or "pexels",
                "status": p.status,
                "platform_status": p.platform_status,
                "platform_url": p.platform_url,
                "word_count": p.word_count,
                "topic": p.topic,
                "author": getattr(p, "author", "Equipe Dezafira"),
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "published_at": p.published_at.isoformat() if p.published_at else None,
            } for p in posts
        ]
    finally:
        db.close()


def get_db_blog_post(post_id: str) -> dict:
    db = SessionLocal()
    try:
        p = db.query(BlogPost).filter(BlogPost.id == post_id).first()
        if p:
            return {
                "id": p.id,
                "channel_id": p.channel_id,
                "title": p.title,
                "slug": p.slug,
                "content": p.content,
                "excerpt": p.excerpt,
                "keywords": p.keywords,
                "featured_image_url": p.featured_image_url,
                "image_provider": getattr(p, "image_provider", "pexels") or "pexels",
                "status": p.status,
                "platform_status": p.platform_status,
                "platform_post_id": p.platform_post_id,
                "platform_url": p.platform_url,
                "word_count": p.word_count,
                "topic": p.topic,
                "author": getattr(p, "author", "Equipe Dezafira"),
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "published_at": p.published_at.isoformat() if p.published_at else None,
            }
        return None
    finally:
        db.close()

def update_db_blog_post(post_id: str, **kwargs) -> bool:
    db = SessionLocal()
    try:
        post = db.query(BlogPost).filter(BlogPost.id == post_id).first()
        if post:
            for key, value in kwargs.items():
                if hasattr(post, key):
                    setattr(post, key, value)
            db.commit()
            return True
        return False
    finally:
        db.close()


def delete_db_blog_post(post_id: str) -> bool:
    """Remove um post do blog pelo ID."""
    db = SessionLocal()
    try:
        post = db.query(BlogPost).filter(BlogPost.id == post_id).first()
        if post:
            db.delete(post)
            db.commit()
            return True
        return False
    except Exception as e:
        print(f"[Database] Erro ao deletar post {post_id}: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def update_db_blog_post_status(post_id: str, status: str) -> bool:
    """Atualiza o status de um post do blog."""
    from datetime import datetime
    kwargs = {"status": status}
    if status == "published":
        kwargs["published_at"] = datetime.utcnow()
    return update_db_blog_post(post_id, **kwargs)


def save_db_lili_score(post_id: str, score: int, approved: bool) -> bool:
    """Persiste o score LiLi de um artigo no banco (cache)."""
    return update_db_blog_post(
        post_id,
        lili_score=score,
        lili_approved=bool(approved),
        lili_reviewed_at=datetime.utcnow(),
    )


def get_db_all_posts_with_meta():
    """Lista todos os artigos com metadados para ranking global (sem content)."""
    db = SessionLocal()
    try:
        rows = db.query(
            BlogPost.id, BlogPost.channel_id, BlogPost.title, BlogPost.slug,
            BlogPost.status, BlogPost.word_count, BlogPost.topic,
            BlogPost.featured_image_url, BlogPost.image_provider,
            BlogPost.lili_score, BlogPost.lili_approved, BlogPost.lili_reviewed_at,
            BlogPost.created_at,
        ).all()
        return [{
            "id": r.id,
            "channel_id": r.channel_id,
            "title": r.title,
            "slug": r.slug,
            "status": r.status,
            "word_count": r.word_count or 0,
            "topic": r.topic,
            "featured_image_url": r.featured_image_url,
            "image_provider": r.image_provider,
            "lili_score": r.lili_score,
            "lili_approved": r.lili_approved,
            "lili_reviewed_at": r.lili_reviewed_at.isoformat() if r.lili_reviewed_at else None,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        } for r in rows]
    finally:
        db.close()


def get_db_blog_channel(channel_id: str) -> dict:
    db = SessionLocal()
    try:
        c = db.query(BlogChannel).filter(BlogChannel.id == channel_id).first()
        if c:
            return {
                "id": c.id,
                "name": c.name,
                "nicho": c.nicho,
                "lang": c.lang,
                "platform": c.platform,
                "site_url": c.site_url,
                "subdomain": __get_subdomain_for_channel(c.id, c.name.lower().replace(" ", "-")[:50]),
                "api_endpoint": c.api_endpoint,
                "api_token": c.api_token,
                "username": c.username,
                "app_password": c.app_password,
                "status": c.status,
                "frequency": c.frequency,
                "is_affiliate": getattr(c, "is_affiliate", False),
                "is_discover": getattr(c, "is_discover", False),
                "brand_config": getattr(c, "brand_config", None),
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
        return None
    finally:
        db.close()


def get_db_blog_info(slug: str) -> dict:
    """Retorna info completa de um blog pelo slug (name slug)."""
    db = SessionLocal()
    try:
        # Encontra o blog pelo slug do nome
        channels = db.query(BlogChannel).all()
        for c in channels:
            name_slug = c.name.lower().replace(" ", "-")[:50]
            if name_slug == slug:
                post_count = db.query(BlogPost).filter(
                    BlogPost.channel_id == c.id
                ).count()
                return {
                    "id": c.id,
                    "name": c.name,
                    "nicho": c.nicho,
                    "lang": c.lang,
                    "subdomain": __get_subdomain_for_channel(c.id, c.name.lower().replace(" ", "-")[:50]),
                    "slug": name_slug,
                    "platform": c.platform,
                    "site_url": c.site_url,
                    "status": c.status,
                    "frequency": c.frequency,
                    "banner_url": c.banner_url,
                    "post_count": post_count,
                    "created_at": c.created_at.isoformat() if c.created_at else None,
                    "is_affiliate": c.is_affiliate,
                    "is_discover": getattr(c, "is_discover", False),
                    "brand_config": getattr(c, "brand_config", None),
                    "affiliate_providers": c.affiliate_providers,
                    "amazon_tag": c.amazon_tag,
                    "amazon_key": c.amazon_key,
                    "amazon_secret": c.amazon_secret,
                    "shopee_app_id": c.shopee_app_id,
                    "shopee_app_secret": c.shopee_app_secret,
                    "mercadolivre_client_id": c.mercadolivre_client_id,
                    "mercadolivre_client_secret": c.mercadolivre_client_secret,
                    "mercadolivre_access_token": c.mercadolivre_access_token,
                    "mercadolivre_refresh_token": c.mercadolivre_refresh_token,
                    "mercadolivre_token_expires": c.mercadolivre_token_expires.isoformat() if c.mercadolivre_token_expires else None,
                }
        return None
    finally:
        db.close()


def update_db_blog_channel(channel_id: str, **kwargs) -> bool:
    db = SessionLocal()
    try:
        chan = db.query(BlogChannel).filter(BlogChannel.id == channel_id).first()
        if chan:
            for key, value in kwargs.items():
                if hasattr(chan, key):
                    setattr(chan, key, value)
            db.commit()
            return True
        return False
    finally:
        db.close()



def __get_subdomain_for_channel(channel_id, slug_fallback=""):
    """Retorna subdominio de um canal (fallback para slug)."""
    db = SessionLocal()
    try:
        sd = db.query(BlogSubdomain).filter(BlogSubdomain.channel_id == channel_id).first()
        if sd:
            return sd.subdomain
    except Exception:
        pass
    finally:
        db.close()
    if slug_fallback:
        import unicodedata as _ud, re as _re
        sub = slug_fallback.replace("-", "").lower()[:50]
        sub = _ud.normalize("NFKD", sub).encode("ascii", "ignore").decode("ascii")
        sub = _re.sub(r"[^a-z0-9-]", "", sub)
        return sub
    return ""

def get_db_blog_by_subdomain(subdomain: str) -> dict:
    """Retorna dados de um blog pelo subdominio (tabela blog_subdomains)."""
    db = SessionLocal()
    try:
        sd = db.query(BlogSubdomain).filter(BlogSubdomain.subdomain == subdomain).first()
        if sd:
            c = db.query(BlogChannel).filter(BlogChannel.id == sd.channel_id).first()
            if c:
                post_count = db.query(BlogPost).filter(
                    BlogPost.channel_id == c.id
                ).count()
                return {
                    "id": c.id,
                    "name": c.name,
                    "nicho": c.nicho,
                    "lang": c.lang,
                    "subdomain": sd.subdomain,
                    "slug": c.name.lower().replace(" ", "-")[:50],
                    "platform": c.platform,
                    "site_url": c.site_url,
                    "status": c.status,
                    "frequency": c.frequency,
                    "banner_url": c.banner_url,
                    "post_count": post_count,
                    "created_at": c.created_at.isoformat() if c.created_at else None,
                }
        return None
    finally:
        db.close()


def create_db_blog_section(channel_id: str, name: str, slug: str = "",
                           description: str = "", keywords: str = "",
                           target_articles: int = 5, sort_order: int = 0) -> dict:
    db = SessionLocal()
    try:
        section = BlogSection(
            id=f"sec_{uuid.uuid4().hex[:6]}",
            channel_id=channel_id,
            name=name,
            slug=slug or name.lower().replace(" ", "-")[:50],
            description=description,
            keywords=keywords,
            target_articles=target_articles,
            sort_order=sort_order,
            status="active",
        )
        db.add(section)
        db.commit()
        return {"id": section.id, "name": section.name, "slug": section.slug,
                "target_articles": section.target_articles, "sort_order": section.sort_order}
    finally:
        db.close()


def get_db_blog_sections(channel_id: str) -> list:
    db = SessionLocal()
    try:
        sections = db.query(BlogSection).filter(
            BlogSection.channel_id == channel_id
        ).order_by(BlogSection.sort_order).all()
        return [{
            "id": s.id, "name": s.name, "slug": s.slug,
            "description": s.description, "keywords": s.keywords,
            "target_articles": s.target_articles, "sort_order": s.sort_order,
            "status": s.status,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        } for s in sections]
    finally:
        db.close()


def delete_db_blog_section(section_id: str) -> bool:
    db = SessionLocal()
    try:
        section = db.query(BlogSection).filter(BlogSection.id == section_id).first()
        if section:
            db.delete(section)
            db.commit()
            return True
        return False
    finally:
        db.close()


# ─── BlogPipelineRun CRUD ────────────────────────────────────────────

def create_db_blog_pipeline_run(channel_id: str, total_articles_target: int = 3,
                                 blog_name: str = "", niche: str = "",
                                 language: str = "pt",
                                 pipeline_data: dict = None) -> dict:
    db = SessionLocal()
    try:
        run = BlogPipelineRun(
            id=f"bpr_{uuid.uuid4().hex[:8]}",
            channel_id=channel_id,
            blog_name=blog_name,
            niche=niche,
            language=language,
            phase="fundacao",
            status="running",
            total_articles_target=total_articles_target,
            articles_generated=0,
            current_round=0,
            pipeline_data=pipeline_data or {},
        )
        db.add(run)
        db.commit()
        return {"id": run.id, "phase": run.phase, "status": run.status}
    finally:
        db.close()


def update_db_blog_pipeline_run(run_id: str, **kwargs) -> bool:
    db = SessionLocal()
    try:
        run = db.query(BlogPipelineRun).filter(BlogPipelineRun.id == run_id).first()
        if run:
            for key, value in kwargs.items():
                if hasattr(run, key):
                    setattr(run, key, value)
            db.commit()
            return True
        return False
    finally:
        db.close()


def get_db_blog_pipeline_run(run_id: str) -> dict:
    """Retorna um pipeline run completo."""
    db = SessionLocal()
    try:
        r = db.query(BlogPipelineRun).filter(BlogPipelineRun.id == run_id).first()
        if r:
            return {
                "id": r.id, "channel_id": r.channel_id,
                "blog_name": r.blog_name, "niche": r.niche,
                "language": r.language, "phase": r.phase,
                "status": r.status,
                "total_articles_target": r.total_articles_target,
                "articles_generated": r.articles_generated,
                "current_round": r.current_round,
                "pipeline_data": r.pipeline_data,
                "started_at": r.started_at.isoformat() if r.started_at else None,
                "completed_at": r.completed_at.isoformat() if r.completed_at else None,
                "error": r.error,
            }
        return None
    finally:
        db.close()


def get_db_blog_pipeline_runs(limit: int = 10) -> list:
    """Retorna uma lista dos pipeline runs mais recentes."""
    db = SessionLocal()
    try:
        runs = db.query(BlogPipelineRun).order_by(BlogPipelineRun.started_at.desc()).limit(limit).all()
        return [
            {
                "id": r.id,
                "channel_id": r.channel_id,
                "blog_name": r.blog_name,
                "niche": r.niche,
                "language": r.language,
                "phase": r.phase,
                "status": r.status,
                "total_articles_target": r.total_articles_target,
                "articles_generated": r.articles_generated,
                "current_round": r.current_round,
                "started_at": r.started_at.isoformat() if r.started_at else None,
                "completed_at": r.completed_at.isoformat() if r.completed_at else None,
                "error": r.error,
            } for r in runs
        ]
    except Exception as e:
        print(f"[Database] Erro ao listar pipeline runs: {e}")
        return []
    finally:
        db.close()



def get_stuck_pipeline_runs() -> list:
    """Retorna pipelines que estão como 'running' (interrompidas)."""
    db = SessionLocal()
    try:
        runs = db.query(BlogPipelineRun).filter(
            BlogPipelineRun.status == "running"
        ).order_by(BlogPipelineRun.started_at.desc()).all()
        return [{
            "id": r.id, "channel_id": r.channel_id,
            "blog_name": r.blog_name,
            "phase": r.phase, "status": r.status,
            "articles_generated": r.articles_generated,
            "total_articles_target": r.total_articles_target,
            "pipeline_data": r.pipeline_data,
            "started_at": r.started_at.isoformat() if r.started_at else None,
        } for r in runs]
    finally:
        db.close()


def update_db_blog_pipeline_run_checkpoint(run_id: str, phase: str,
                                            articles_generated: int,
                                            current_round: int,
                                            pipeline_data: dict) -> bool:
    """Atualiza checkpoint de uma pipeline run."""
    return update_db_blog_pipeline_run(
        run_id,
        phase=phase,
        articles_generated=articles_generated,
        current_round=current_round,
        pipeline_data=pipeline_data,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# CRUD — FABRICA DE LIVROS
# ═══════════════════════════════════════════════════════════════════════════════

def create_db_book(title: str, topic: str, description: str = "", author: str = "Dezafira Editorial",
                   keywords: str = "", price_cents: int = 0) -> dict:
    db = SessionLocal()
    try:
        book = Book(
            id=f"book_{uuid.uuid4().hex[:8]}",
            title=title, topic=topic,
            description=description, author=author, keywords=keywords,
            price_cents=price_cents, status="draft",
        )
        db.add(book)
        db.commit()
        return {
            "id": book.id, "title": book.title, "topic": book.topic,
            "status": book.status, "author": book.author,
            "created_at": book.created_at.isoformat() if book.created_at else None,
        }
    finally:
        db.close()


def get_db_books(limit: int = 50) -> list:
    db = SessionLocal()
    try:
        books = db.query(Book).order_by(Book.created_at.desc()).limit(limit).all()
        result = []
        for b in books:
            chapters_count = db.query(BookChapter).filter(BookChapter.book_id == b.id).count()
            result.append({
                "id": b.id, "title": b.title, "subtitle": b.subtitle,
                "author": b.author, "description": b.description,
                "cover_url": b.cover_url, "topic": b.topic,
                "keywords": b.keywords, "status": b.status,
                "total_chapters": chapters_count,
                "total_words": b.total_words,
                "price_cents": b.price_cents,
                "created_at": b.created_at.isoformat() if b.created_at else None,
            })
        return result
    finally:
        db.close()


def get_db_book(book_id: str) -> dict:
    db = SessionLocal()
    try:
        b = db.query(Book).filter(Book.id == book_id).first()
        if not b:
            return None
        chapters = db.query(BookChapter).filter(BookChapter.book_id == book_id).order_by(
            BookChapter.chapter_number
        ).all()
        formats = db.query(BookFormat).filter(BookFormat.book_id == book_id).all()
        return {
            "id": b.id, "title": b.title, "subtitle": b.subtitle,
            "author": b.author, "description": b.description,
            "cover_url": b.cover_url, "topic": b.topic,
            "keywords": b.keywords, "status": b.status,
            "total_chapters": len(chapters), "total_words": b.total_words,
            "price_cents": b.price_cents,
            "chapters": [{
                "id": ch.id, "chapter_number": ch.chapter_number,
                "title": ch.title, "content": ch.content,
                "word_count": ch.word_count, "status": ch.status,
            } for ch in chapters],
            "formats": [{
                "format_type": f.format_type, "file_url": f.file_url,
                "file_size_bytes": f.file_size_bytes,
                "generated_at": f.generated_at.isoformat() if f.generated_at else None,
            } for f in formats],
            "created_at": b.created_at.isoformat() if b.created_at else None,
            "published_at": b.published_at.isoformat() if b.published_at else None,
        }
    finally:
        db.close()


def create_db_book_chapter(book_id: str, chapter_number: int, title: str,
                           content: str = "") -> dict:
    db = SessionLocal()
    try:
        ch = BookChapter(
            id=f"bch_{uuid.uuid4().hex[:8]}", book_id=book_id,
            chapter_number=chapter_number, title=title,
            content=content, word_count=len(content.split()),
            status="draft",
        )
        db.add(ch)
        book = db.query(Book).filter(Book.id == book_id).first()
        if book:
            book.total_chapters = db.query(BookChapter).filter(
                BookChapter.book_id == book_id
            ).count()
            total = db.query(BookChapter.word_count).filter(
                BookChapter.book_id == book_id
            ).all()
            book.total_words = sum(wc[0] or 0 for wc in total)
        db.commit()
        return {
            "id": ch.id, "chapter_number": ch.chapter_number,
            "title": ch.title, "word_count": ch.word_count,
            "status": ch.status,
        }
    except Exception as e:
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()


def update_db_book(book_id: str, **kwargs) -> bool:
    db = SessionLocal()
    try:
        book = db.query(Book).filter(Book.id == book_id).first()
        if book:
            for key, value in kwargs.items():
                if hasattr(book, key):
                    setattr(book, key, value)
            db.commit()
            return True
        return False
    finally:
        db.close()


def delete_db_book(book_id: str) -> bool:
    db = SessionLocal()
    try:
        db.query(BookChapter).filter(BookChapter.book_id == book_id).delete()
        db.query(BookFormat).filter(BookFormat.book_id == book_id).delete()
        book = db.query(Book).filter(Book.id == book_id).first()
        if book:
            db.delete(book)
            db.commit()
            return True
        return False
    except Exception as e:
        print(f"[Database] Erro ao deletar livro: {e}")
        db.rollback()
        return False
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════════════════════
# CRUD — FABRICA DE CURSOS
# ═══════════════════════════════════════════════════════════════════════════════

def create_db_course(title: str, topic: str, description: str = "",
                     difficulty: str = "iniciante", price_cents: int = 0) -> dict:
    db = SessionLocal()
    try:
        course = Course(
            id=f"crs_{uuid.uuid4().hex[:8]}", title=title, topic=topic,
            description=description, difficulty=difficulty,
            price_cents=price_cents, status="draft",
        )
        db.add(course)
        db.commit()
        return {"id": course.id, "title": course.title, "topic": course.topic,
                "status": course.status, "difficulty": course.difficulty,
                "created_at": course.created_at.isoformat() if course.created_at else None}
    finally:
        db.close()


def get_db_courses(limit: int = 50) -> list:
    db = SessionLocal()
    try:
        courses = db.query(Course).order_by(Course.created_at.desc()).limit(limit).all()
        result = []
        for c in courses:
            modules_count = db.query(CourseModule).filter(CourseModule.course_id == c.id).count()
            lessons_count = db.query(CourseLesson).join(CourseModule).filter(
                CourseModule.course_id == c.id
            ).count() if modules_count > 0 else 0
            result.append({
                "id": c.id, "title": c.title, "subtitle": c.subtitle,
                "description": c.description, "topic": c.topic,
                "keywords": c.keywords, "status": c.status,
                "total_modules": modules_count,
                "total_lessons": lessons_count,
                "difficulty": c.difficulty,
                "price_cents": c.price_cents,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            })
        return result
    finally:
        db.close()


def get_db_course(course_id: str) -> dict:
    db = SessionLocal()
    try:
        c = db.query(Course).filter(Course.id == course_id).first()
        if not c:
            return None
        modules = db.query(CourseModule).filter(
            CourseModule.course_id == course_id
        ).order_by(CourseModule.module_number).all()
        result = {
            "id": c.id, "title": c.title, "subtitle": c.subtitle,
            "description": c.description, "topic": c.topic,
            "keywords": c.keywords, "status": c.status,
            "total_modules": len(modules),
            "difficulty": c.difficulty, "price_cents": c.price_cents,
            "estimated_hours": c.estimated_hours,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "published_at": c.published_at.isoformat() if c.published_at else None,
            "modules": [],
        }
        for mod in modules:
            lessons = db.query(CourseLesson).filter(
                CourseLesson.module_id == mod.id
            ).order_by(CourseLesson.lesson_number).all()
            module_data = {
                "id": mod.id, "module_number": mod.module_number,
                "title": mod.title, "description": mod.description,
                "lessons": [{
                    "id": l.id, "lesson_number": l.lesson_number,
                    "title": l.title, "content": l.content,
                    "content_type": l.content_type,
                    "word_count": l.word_count,
                    "estimated_minutes": l.estimated_minutes,
                } for l in lessons],
            }
            result["modules"].append(module_data)
        return result
    finally:
        db.close()


def create_db_course_module(course_id: str, module_number: int, title: str,
                            description: str = "") -> dict:
    db = SessionLocal()
    try:
        mod = CourseModule(
            id=f"crm_{uuid.uuid4().hex[:6]}", course_id=course_id,
            module_number=module_number, title=title, description=description,
        )
        db.add(mod)
        course = db.query(Course).filter(Course.id == course_id).first()
        if course:
            course.total_modules = db.query(CourseModule).filter(
                CourseModule.course_id == course_id
            ).count()
        db.commit()
        return {"id": mod.id, "module_number": mod.module_number, "title": mod.title}
    except Exception as e:
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()


def create_db_course_lesson(module_id: str, lesson_number: int, title: str,
                            content: str = "", content_type: str = "texto",
                            estimated_minutes: int = 10) -> dict:
    db = SessionLocal()
    try:
        lesson = CourseLesson(
            id=f"crl_{uuid.uuid4().hex[:6]}", module_id=module_id,
            lesson_number=lesson_number, title=title,
            content=content, content_type=content_type,
            word_count=len(content.split()),
            estimated_minutes=estimated_minutes,
        )
        db.add(lesson)
        db.commit()
        return {"id": lesson.id, "lesson_number": lesson.lesson_number,
                "title": lesson.title, "word_count": lesson.word_count}
    except Exception as e:
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()


def update_db_course(course_id: str, **kwargs) -> bool:
    db = SessionLocal()
    try:
        course = db.query(Course).filter(Course.id == course_id).first()
        if course:
            for key, value in kwargs.items():
                if hasattr(course, key):
                    setattr(course, key, value)
            db.commit()
            return True
        return False
    finally:
        db.close()


def delete_db_course(course_id: str) -> bool:
    db = SessionLocal()
    try:
        modules = db.query(CourseModule).filter(CourseModule.course_id == course_id).all()
        for mod in modules:
            lessons = db.query(CourseLesson).filter(CourseLesson.module_id == mod.id).all()
            for les in lessons:
                db.query(CourseQuiz).filter(CourseQuiz.lesson_id == les.id).delete()
                db.query(CourseMaterial).filter(CourseMaterial.lesson_id == les.id).delete()
            db.query(CourseLesson).filter(CourseLesson.module_id == mod.id).delete()
        db.query(CourseModule).filter(CourseModule.course_id == course_id).delete()
        c = db.query(Course).filter(Course.id == course_id).first()
        if c:
            db.delete(c)
            db.commit()
            return True
        return False
    except Exception as e:
        db.rollback()
        return False
    finally:
        db.close()



# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS — JOBS DE REGENERACAO EM LOTE (LiLi)
# ═══════════════════════════════════════════════════════════════════════════════

def create_db_regeneration_job(total: int = 0):
    """Cria um job persistido e retorna o dict com id."""
    job_id = "job_" + uuid.uuid4().hex[:10]
    db = SessionLocal()
    try:
        job = RegenerationJob(id=job_id, status="running", total=total)
        db.add(job)
        db.commit()
        return {"id": job_id, "status": "running", "total": total}
    except Exception as e:
        db.rollback()
        print(f"[Database] Falha ao criar job: {e}")
        return None
    finally:
        db.close()


def add_db_regeneration_job_item(job_id: str, post_id: str, post_title: str = ""):
    """Adiciona um item (artigo) ao job."""
    db = SessionLocal()
    try:
        item = RegenerationJobItem(
            id="itm_" + uuid.uuid4().hex[:10],
            job_id=job_id,
            post_id=post_id,
            post_title=post_title,
            status="pending",
        )
        db.add(item)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"[Database] Falha ao criar item do job: {e}")
        return False
    finally:
        db.close()


def get_db_regeneration_job(job_id: str):
    """Retorna o job com lista de itens."""
    db = SessionLocal()
    try:
        job = db.query(RegenerationJob).filter(RegenerationJob.id == job_id).first()
        if not job:
            return None
        items = db.query(RegenerationJobItem).filter(
            RegenerationJobItem.job_id == job_id
        ).order_by(RegenerationJobItem.created_at.asc()).all()
        return {
            "id": job.id,
            "status": job.status,
            "total": job.total,
            "processed": job.processed,
            "succeeded": job.succeeded,
            "failed": job.failed,
            "created_at": job.created_at.strftime("%d/%m %H:%M") if job.created_at else "",
            "updated_at": job.updated_at.strftime("%d/%m %H:%M") if job.updated_at else "",
            "error": job.error,
            "items": [
                {
                    "id": i.id,
                    "post_id": i.post_id,
                    "post_title": i.post_title,
                    "status": i.status,
                    "error": i.error,
                }
                for i in items
            ],
        }
    finally:
        db.close()


def update_db_regeneration_job(job_id: str, **kwargs):
    """Atualiza campos do job (status, contadores, erro)."""
    db = SessionLocal()
    try:
        job = db.query(RegenerationJob).filter(RegenerationJob.id == job_id).first()
        if not job:
            return False
        for key, value in kwargs.items():
            if hasattr(job, key):
                setattr(job, key, value)
        job.updated_at = datetime.utcnow()
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"[Database] Falha ao atualizar job {job_id}: {e}")
        return False
    finally:
        db.close()


def update_db_regeneration_job_item(item_id: str, **kwargs):
    """Atualiza um item do job (status, erro)."""
    db = SessionLocal()
    try:
        item = db.query(RegenerationJobItem).filter(
            RegenerationJobItem.id == item_id
        ).first()
        if not item:
            return False
        for key, value in kwargs.items():
            if hasattr(item, key):
                setattr(item, key, value)
        item.updated_at = datetime.utcnow()
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"[Database] Falha ao atualizar item {item_id}: {e}")
        return False
    finally:
        db.close()


def get_db_recent_regeneration_jobs(limit: int = 10):
    """Jobs recentes (qualquer status) para listagem na UI."""
    db = SessionLocal()
    try:
        jobs = db.query(RegenerationJob).order_by(
            RegenerationJob.created_at.desc()
        ).limit(limit).all()
        return [
            {
                "id": j.id,
                "status": j.status,
                "total": j.total,
                "processed": j.processed,
                "succeeded": j.succeeded,
                "failed": j.failed,
                "created_at": j.created_at.strftime("%d/%m %H:%M") if j.created_at else "",
                "updated_at": j.updated_at.strftime("%d/%m %H:%M") if j.updated_at else "",
                "error": j.error,
            }
            for j in jobs
        ]
    finally:
        db.close()


def get_db_running_regeneration_jobs(limit: int = 5):
    """Jobs com status running (para retomar apos restart)."""
    db = SessionLocal()
    try:
        jobs = db.query(RegenerationJob).filter(
            RegenerationJob.status == "running"
        ).order_by(RegenerationJob.created_at.desc()).limit(limit).all()
        return [{"id": j.id, "total": j.total, "processed": j.processed} for j in jobs]
    finally:
        db.close()


def reset_db_stuck_job_items(job_id: str):
    """Reabre itens que ficaram em 'processing' (crash no meio do item)."""
    db = SessionLocal()
    try:
        items = db.query(RegenerationJobItem).filter(
            RegenerationJobItem.job_id == job_id,
            RegenerationJobItem.status == "processing",
        ).all()
        for item in items:
            item.status = "pending"
            item.updated_at = datetime.utcnow()
        db.commit()
        return len(items)
    except Exception as e:
        db.rollback()
        print(f"[Database] Falha ao resetar itens do job {job_id}: {e}")
        return 0
    finally:
        db.close()

