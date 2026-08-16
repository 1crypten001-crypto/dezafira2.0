"""
MÓDULO: convite_models.py
DESCRIÇÃO: Modelos ORM do conteúdo do produto "1Convite" (super app cristão:
Bíblia, matriz diária, trilhas, arcade bíblico, trilha do reino) absorvido na
fábrica DezafiraADM — + tabela `miniapp_domains` (domínios dedicados de PWA).

Fluxo:
  scripts/convert_convite_data.py  →  data/convite/*.json  (conteúdo canônico)
  scripts/seed_convite.py          →  popula as tabelas convite_* (idempotente)
  server.py (middleware)           →  roteia domínio dedicado → /app/{slug}
"""

import logging
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, JSON, String, Text
from sqlalchemy.orm import sessionmaker

from modules.database import Base, SessionLocal

logger = logging.getLogger("convite_models")


# ═══════════════════════════════════════════════════════════════════════════
# CONTEÚDO — 1CONVITE (produto da fábrica)
# ═══════════════════════════════════════════════════════════════════════════

class ConviteMatrizDiaria(Base):
    """Matriz diária (365 dias): código verbal, versículo, reflexão, meditação."""
    __tablename__ = "convite_matriz_diaria"

    dia_id = Column(Integer, primary_key=True)
    pilar_origem = Column(String(50), nullable=False)          # PROPÓSITO_M2414 | RECOMPENSA_AP321
    codigo_verbal = Column(Text, nullable=False)
    versiculo_chave = Column(Text, nullable=False)
    texto_reflexao = Column(Text, nullable=False)
    texto_meditacao = Column(Text, nullable=True)
    url_audio_meditacao = Column(String(1000), nullable=True)


class ConviteDicionario(Base):
    """Dicionário teológico (termo → significado)."""
    __tablename__ = "convite_dicionario"

    termo = Column(String(100), primary_key=True)
    significado = Column(Text, nullable=False)


class ConviteTrilha(Base):
    """Trilhas de crescimento (4 temas × 30 dias)."""
    __tablename__ = "convite_trilhas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tema = Column(String(50), nullable=False, index=True)
    dia_trilha = Column(Integer, nullable=False)
    titulo = Column(Text, nullable=False)
    versiculo = Column(Text, nullable=False)
    reflexao = Column(Text, nullable=False)
    acao_pratica = Column(Text, nullable=False)


class ConviteBiblia(Base):
    """Bíblia Almeida Corrigida Fiel (ACF) — texto completo (~31k versículos)."""
    __tablename__ = "convite_biblia"

    id = Column(Integer, primary_key=True, autoincrement=True)
    livro_nome = Column(String(100), nullable=False)
    livro_abrev = Column(String(20), nullable=False, index=True)
    capitulo = Column(Integer, nullable=False)
    versiculo = Column(Integer, nullable=False)
    texto = Column(Text, nullable=False)


class ConviteJogoQuiz(Base):
    """Arcade bíblico — Quiz (30 perguntas)."""
    __tablename__ = "convite_jogos_quiz"

    id = Column(Integer, primary_key=True, autoincrement=True)
    pergunta = Column(Text, nullable=False)
    opcoes = Column(JSON, nullable=False)          # [str, str, str, str]
    resposta_idx = Column(Integer, nullable=False)  # índice da correta
    dificuldade = Column(String(20), default="facil", index=True)


class ConviteJogoCharada(Base):
    """Arcade bíblico — Quem Sou Eu? / Charadas (15 perguntas)."""
    __tablename__ = "convite_jogos_charadas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    dicas = Column(JSON, nullable=False)           # [str, ...] dicas progressivas
    opcoes = Column(JSON, nullable=False)
    resposta_idx = Column(Integer, nullable=False)
    dificuldade = Column(String(20), default="facil", index=True)


class ConviteJogoForca(Base):
    """Arcade bíblico — Forca (30 palavras)."""
    __tablename__ = "convite_jogos_forca"

    id = Column(Integer, primary_key=True, autoincrement=True)
    palavra = Column(String(100), nullable=False)
    dica = Column(Text, nullable=True)
    dificuldade = Column(String(20), default="facil", index=True)


class ConviteJogoCacaPalavras(Base):
    """Arcade bíblico — Caça-Palavras (37 palavras)."""
    __tablename__ = "convite_jogos_caca_palavras"

    id = Column(Integer, primary_key=True, autoincrement=True)
    palavra = Column(String(100), nullable=False)
    dificuldade = Column(String(20), default="facil", index=True)


class ConviteTrilhaReino(Base):
    """Trilha do Reino — plano de leitura cronológico (18m/540 e 12m/365)."""
    __tablename__ = "convite_trilha_reino"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plano = Column(String(10), nullable=False, index=True)   # '18m' | '12m'
    dia = Column(Integer, nullable=False, index=True)
    leitura = Column(Text, nullable=False)                   # ex: "Gênesis 1-3"
    livro_abbr = Column(String(20), nullable=True)
    capitulos = Column(JSON, nullable=True)                  # [1, 2, 3]
    devocional = Column(Text, nullable=True)
    acao = Column(Text, nullable=True)


class ConviteTrilhaReinoMilestone(Base):
    """Marcos de fé da Trilha do Reino (mapa visual 9 marcos)."""
    __tablename__ = "convite_trilha_reino_milestones"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(50), nullable=False)
    nome = Column(String(100), nullable=False)
    icone = Column(String(20), nullable=True)
    start_day_18m = Column(Integer, nullable=False)
    start_day_12m = Column(Integer, nullable=False)


class ConviteTrilhaReinoAcao(Base):
    """Banco de ações práticas da Trilha do Reino."""
    __tablename__ = "convite_trilha_reino_acoes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    texto = Column(Text, nullable=False)


# ═══════════════════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════════════════
# ESTADO DE USUÁRIO — 1CONVITE (começa do ZERO: sem migração de dados legados)
#
# O PWA React original persistia progresso num Postgres próprio (tb_usuario_*).
# No ADM, o estado do usuário é fresco: as tabelas abaixo começam vazias e são
# criadas sob demanda. Contatos/histórico começam vazios; trilha ativa inicia
# sem tema. O conteúdo (Bíblia/matriz/jogos) é o que importa — está nas tabelas
# convite_* acima, já populadas pelo seed.
# ═══════════════════════════════════════════════════════════════════════════

class ConviteUserProgress(Base):
    """Progresso do usuário do 1Convite (linha única, espelha tb_usuario_progresso)."""
    __tablename__ = "convite_user_progress"

    id = Column(Integer, primary_key=True, autoincrement=True)
    dia_atual = Column(Integer, nullable=False, default=1)
    checkpoint_completado = Column(Integer, nullable=False, default=0)   # 0/1 (SQLite não tem BOOLEAN)
    checkpoint_started_at = Column(Integer, nullable=False, default=0)   # epoch ms
    status_plano = Column(String(20), nullable=False, default="FREE")
    nome = Column(String(200), nullable=False, default="Membro Convidado")
    email = Column(String(300), nullable=False, default="membro@1convite.com")
    avatar = Column(String(1000), nullable=True)
    moedas = Column(Integer, nullable=False, default=100)
    streak = Column(Integer, nullable=False, default=1)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ConviteTrilhaProgresso(Base):
    """Trilha de crescimento ativa do usuário (linha única)."""
    __tablename__ = "convite_trilha_progresso"

    id = Column(Integer, primary_key=True, autoincrement=True)
    trilha_ativa = Column(String(50), nullable=True)
    dia_progresso = Column(Integer, nullable=False, default=1)
    atualizado_em = Column(Integer, nullable=False, default=0)            # epoch ms


class ConviteContato(Base):
    """Contatos de oração/missão do usuário (começa vazio — start do zero)."""
    __tablename__ = "convite_contatos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(200), nullable=False)
    relacao = Column(String(100), nullable=True)
    prioritario = Column(Integer, nullable=False, default=0)              # 0/1
    criado_em = Column(DateTime, default=datetime.utcnow)


class ConviteLead(Base):
    """Leads capturados pela landing do 1Convite (formulário de contato)."""
    __tablename__ = "convite_leads"

    id = Column(Integer, primary_key=True, autoincrement=True)
    telefone = Column(String(50), nullable=True)
    nome = Column(String(200), nullable=True)
    email = Column(String(300), nullable=True)
    origem = Column(String(100), nullable=True)
    pagina = Column(String(200), nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow)


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS — estado de usuário (linha única, criada sob demanda)
# ─────────────────────────────────────────────────────────────────────────────

def _ensure_user_row(session) -> ConviteUserProgress:
    """Garante a linha única do usuário (começa do zero com defaults)."""
    row = session.query(ConviteUserProgress).order_by(ConviteUserProgress.id.asc()).first()
    if row is None:
        row = ConviteUserProgress()
        session.add(row)
        session.commit()
        session.refresh(row)
    return row


def get_db_convite_user() -> dict:
    """Usuário do 1Convite (objeto JSON pronto pro PWA)."""
    session = SessionLocal()
    try:
        row = _ensure_user_row(session)
        return {
            "id": row.id,
            "dia_atual": row.dia_atual,
            "checkpoint_completado": bool(row.checkpoint_completado),
            "checkpoint_started_at": row.checkpoint_started_at,
            "status_plano": row.status_plano,
            "nome": row.nome,
            "email": row.email,
            "avatar": row.avatar or "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=250&q=80",
            "moedas": row.moedas,
            "streak": row.streak,
        }
    finally:
        session.close()


def update_db_convite_user(**fields) -> dict:
    """Atualiza campos do usuário do 1Convite e devolve o objeto atualizado."""
    session = SessionLocal()
    try:
        row = _ensure_user_row(session)
        if "nome" in fields and fields["nome"]:
            row.nome = fields["nome"]
        if "email" in fields and fields["email"]:
            row.email = fields["email"]
        if "avatar" in fields and fields["avatar"]:
            row.avatar = fields["avatar"]
        if "status_plano" in fields:
            row.status_plano = fields["status_plano"]
        if "dia_atual" in fields:
            row.dia_atual = fields["dia_atual"]
        if "checkpoint_completado" in fields:
            row.checkpoint_completado = 1 if fields["checkpoint_completado"] else 0
        if "checkpoint_started_at" in fields:
            row.checkpoint_started_at = int(fields["checkpoint_started_at"] or 0)
        session.commit()
        return get_db_convite_user()
    finally:
        session.close()


def get_db_convite_trilha_progresso() -> dict:
    """Progresso da trilha ativa do 1Convite (ou vazio)."""
    session = SessionLocal()
    try:
        row = session.query(ConviteTrilhaProgresso).order_by(ConviteTrilhaProgresso.id.asc()).first()
        if not row or not row.trilha_ativa:
            return {"ativa": False}
        return {
            "ativa": True,
            "tema": row.trilha_ativa,
            "dia_progresso": row.dia_progresso,
        }
    finally:
        session.close()


def set_db_convite_trilha_progresso(tema: str | None, dia: int = 1) -> dict:
    """Inicia/cancela a trilha ativa (linha única)."""
    session = SessionLocal()
    try:
        row = session.query(ConviteTrilhaProgresso).order_by(ConviteTrilhaProgresso.id.asc()).first()
        if row is None:
            row = ConviteTrilhaProgresso()
            session.add(row)
        row.trilha_ativa = tema
        row.dia_progresso = dia
        row.atualizado_em = int(datetime.utcnow().timestamp() * 1000)
        session.commit()
        return get_db_convite_trilha_progresso()
    finally:
        session.close()


def list_db_convite_contatos() -> list:
    session = SessionLocal()
    try:
        rows = session.query(ConviteContato).order_by(ConviteContato.id.asc()).all()
        return [
            {"id": r.id, "nome": r.nome, "relacao": r.relacao, "prioritario": bool(r.prioritario), "criado_em": r.criado_em.isoformat() if r.criado_em else None}
            for r in rows
        ]
    finally:
        session.close()


def create_db_convite_contato(nome: str, relacao: str | None = None, prioritario: bool = False) -> dict:
    session = SessionLocal()
    try:
        row = ConviteContato(nome=nome, relacao=relacao, prioritario=1 if prioritario else 0)
        session.add(row)
        session.commit()
        session.refresh(row)
        return {"id": row.id, "nome": row.nome, "relacao": row.relacao, "prioritario": bool(row.prioritario)}
    finally:
        session.close()


def delete_db_convite_contato(contato_id: int) -> bool:
    session = SessionLocal()
    try:
        row = session.query(ConviteContato).filter(ConviteContato.id == contato_id).first()
        if row:
            session.delete(row)
            session.commit()
            return True
        return False
    finally:
        session.close()


def create_db_convite_lead(telefone=None, nome=None, email=None, origem=None, pagina=None) -> dict:
    session = SessionLocal()
    try:
        row = ConviteLead(telefone=telefone, nome=nome, email=email, origem=origem, pagina=pagina)
        session.add(row)
        session.commit()
        session.refresh(row)
        return {"id": row.id, "success": True}
    finally:
        session.close()


# ═══════════════════════════════════════════════════════════════════════════
# INFRA — DOMÍNIOS DEDICADOS DE PWA (rota por Host)
# ═══════════════════════════════════════════════════════════════════════════

class MiniappDomain(Base):
    """Domínio dedicado de um PWA da fábrica (ex: 1convite.com.br → miniapp).

    O middleware de Host-routing no server.py usa esta tabela: quando o Host da
    requisição está aqui, o request é roteado para /app/{slug} na raiz do
    domínio. Os outros PWAs continuam em /app/{slug} sem domínio próprio.
    """
    __tablename__ = "miniapp_domains"

    domain = Column(String(255), primary_key=True)   # hostname minúsculo, sem porta
    miniapp_id = Column(String(50), nullable=False, index=True)
    slug = Column(String(100), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# ─────────────────────────────────────────────────────────────────────────────
# CRUD — domínios dedicados
# ─────────────────────────────────────────────────────────────────────────────

def create_all_tables() -> None:
    """Cria as tabelas deste módulo (usado pelo seed e por quem precisar)."""
    from modules.database import engine
    Base.metadata.create_all(bind=engine)


def get_db_miniapp_domains() -> list:
    """Lista {domain → slug} de todos os domínios dedicados."""
    session: sessionmaker = SessionLocal()
    try:
        rows = session.query(MiniappDomain).all()
        return [{"domain": r.domain, "miniapp_id": r.miniapp_id, "slug": r.slug} for r in rows]
    finally:
        session.close()


def get_db_domain_slug(domain: str):
    """Devolve o slug do miniapp para um hostname (ou None)."""
    session = SessionLocal()
    try:
        row = session.query(MiniappDomain).filter(MiniappDomain.domain == domain.lower()).first()
        return row.slug if row else None
    finally:
        session.close()


def create_db_miniapp_domain(domain: str, miniapp_id: str, slug: str) -> dict:
    """Registra um domínio dedicado para um PWA (idempotente)."""
    session = SessionLocal()
    try:
        row = session.query(MiniappDomain).filter(MiniappDomain.domain == domain.lower()).first()
        if row:
            row.miniapp_id = miniapp_id
            row.slug = slug
        else:
            row = MiniappDomain(domain=domain.lower(), miniapp_id=miniapp_id, slug=slug)
            session.add(row)
        session.commit()
        session.refresh(row)
        return {"domain": row.domain, "miniapp_id": row.miniapp_id, "slug": row.slug}
    finally:
        session.close()


def delete_db_miniapp_domain(domain: str) -> bool:
    """Remove um domínio dedicado. Devolve True se existia."""
    session = SessionLocal()
    try:
        row = session.query(MiniappDomain).filter(MiniappDomain.domain == domain.lower()).first()
        if row:
            session.delete(row)
            session.commit()
            return True
        return False
    finally:
        session.close()
