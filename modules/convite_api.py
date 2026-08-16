"""
MÓDULO: convite_api.py
DESCRIÇÃO: Endpoints públicos de conteúdo do produto "1Convite" (super app
cristão absorvido na fábrica DezafiraADM).

Fonte de dados: tabelas `convite_*` (populadas por scripts/seed_convite.py).
Endpoints de LEITURA pública — o PWA do 1Convite consome direto (Bíblia,
matriz diária, trilhas, dicionário, jogos e trilha do reino).

Registro no app:
    from modules.convite_api import register_convite_routes
    register_convite_routes(app)
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func, or_

from modules.database import SessionLocal
from modules.convite_models import (
    ConviteBiblia,
    ConviteDicionario,
    ConviteJogoCacaPalavras,
    ConviteJogoCharada,
    ConviteJogoForca,
    ConviteJogoQuiz,
    ConviteMatrizDiaria,
    ConviteTrilha,
    ConviteTrilhaReino,
    ConviteTrilhaReinoAcao,
    ConviteTrilhaReinoMilestone,
)

logger = logging.getLogger("convite_api")

router = APIRouter(prefix="/api/v1/convite", tags=["1Convite"])

_DIFICULDADES = {"facil", "medio", "avancado"}


def _check_dificuldade(dificuldade: Optional[str]) -> Optional[str]:
    if dificuldade and dificuldade not in _DIFICULDADES:
        raise HTTPException(status_code=400, detail="dificuldade deve ser facil|medio|avancado")
    return dificuldade


# ═══════════════════════════════════════════════════════════════════════════
# STATUS
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/status", summary="Contagens de conteúdo disponível")
async def convite_status():
    session = SessionLocal()
    try:
        counts = {
            "biblia": session.query(func.count(ConviteBiblia.id)).scalar(),
            "matriz_diaria": session.query(func.count(ConviteMatrizDiaria.dia_id)).scalar(),
            "dicionario": session.query(func.count(ConviteDicionario.termo)).scalar(),
            "trilhas": session.query(func.count(ConviteTrilha.id)).scalar(),
            "trilha_reino": session.query(func.count(ConviteTrilhaReino.id)).scalar(),
            "trilha_reino_marcos": session.query(func.count(ConviteTrilhaReinoMilestone.id)).scalar(),
            "trilha_reino_acoes": session.query(func.count(ConviteTrilhaReinoAcao.id)).scalar(),
            "jogos_quiz": session.query(func.count(ConviteJogoQuiz.id)).scalar(),
            "jogos_charadas": session.query(func.count(ConviteJogoCharada.id)).scalar(),
            "jogos_forca": session.query(func.count(ConviteJogoForca.id)).scalar(),
            "jogos_caca_palavras": session.query(func.count(ConviteJogoCacaPalavras.id)).scalar(),
        }
        return {"success": True, "counts": counts}
    finally:
        session.close()


# ═══════════════════════════════════════════════════════════════════════════
# BÍBLIA (ACF)
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/biblia/livros", summary="Lista livros com contagem de capítulos/versículos")
async def biblia_livros():
    session = SessionLocal()
    try:
        rows = (session.query(ConviteBiblia.livro_nome, ConviteBiblia.livro_abrev,
                              func.count(func.distinct(ConviteBiblia.capitulo)).label("capitulos"),
                              func.count(ConviteBiblia.id).label("versiculos"))
                .group_by(ConviteBiblia.livro_nome, ConviteBiblia.livro_abrev)
                .order_by(ConviteBiblia.id)
                .all())
        return {"success": True, "livros": [
            {"nome": n, "abrev": a, "capitulos": c, "versiculos": v} for n, a, c, v in rows]}
    finally:
        session.close()


@router.get("/biblia/capitulos/{abrev}", summary="Número de capítulos de um livro")
async def biblia_capitulos(abrev: str):
    session = SessionLocal()
    try:
        max_cap = (session.query(func.max(ConviteBiblia.capitulo))
                   .filter(ConviteBiblia.livro_abrev == abrev.lower()).scalar())
        if max_cap is None:
            raise HTTPException(status_code=404, detail=f"Livro '{abrev}' não encontrado")
        return {"success": True, "abrev": abrev.lower(), "capitulos": max_cap}
    finally:
        session.close()


@router.get("/biblia/texto/{abrev}/{capitulo}", summary="Versículos de um capítulo")
async def biblia_texto(abrev: str, capitulo: int):
    session = SessionLocal()
    try:
        rows = (session.query(ConviteBiblia.versiculo, ConviteBiblia.texto)
                .filter(ConviteBiblia.livro_abrev == abrev.lower(),
                        ConviteBiblia.capitulo == capitulo)
                .order_by(ConviteBiblia.versiculo)
                .all())
        if not rows:
            raise HTTPException(status_code=404, detail=f"{abrev} {capitulo} não encontrado")
        return {"success": True, "abrev": abrev.lower(), "capitulo": capitulo,
                "versiculos": [{"versiculo": v, "texto": t} for v, t in rows]}
    finally:
        session.close()


@router.get("/biblia/busca", summary="Busca por texto na Bíblia")
async def biblia_busca(q: str = Query(..., min_length=3), limit: int = Query(20, ge=1, le=100)):
    session = SessionLocal()
    try:
        pattern = f"%{q}%"
        rows = (session.query(ConviteBiblia)
                .filter(or_(ConviteBiblia.texto.ilike(pattern),
                            ConviteBiblia.livro_nome.ilike(pattern)))
                .order_by(ConviteBiblia.id)
                .limit(limit)
                .all())
        return {"success": True, "q": q, "resultados": [
            {"livro": r.livro_nome, "abrev": r.livro_abrev, "capitulo": r.capitulo,
             "versiculo": r.versiculo, "texto": r.texto} for r in rows]}
    finally:
        session.close()


@router.get("/biblia/aleatorio", summary="Versículo aleatório")
async def biblia_aleatorio():
    session = SessionLocal()
    try:
        row = session.query(ConviteBiblia).order_by(func.random()).first()
        if not row:
            raise HTTPException(status_code=404, detail="Bíblia vazia (rode o seed --with-bible)")
        return {"success": True, "livro": row.livro_nome, "abrev": row.livro_abrev,
                "capitulo": row.capitulo, "versiculo": row.versiculo, "texto": row.texto}
    finally:
        session.close()


# ═══════════════════════════════════════════════════════════════════════════
# MATRIZ DIÁRIA (365 dias)
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/matriz/dia", summary="Dia da matriz diária (default: dia do ano)")
async def matriz_dia(dia: Optional[int] = Query(None, ge=1, le=365)):
    dia = dia or (datetime.now().timetuple().tm_yday)
    session = SessionLocal()
    try:
        row = session.query(ConviteMatrizDiaria).filter(ConviteMatrizDiaria.dia_id == dia).first()
        if not row:
            raise HTTPException(status_code=404, detail=f"Dia {dia} não encontrado")
        return {"success": True, "dia": {
            "dia_id": row.dia_id, "pilar_origem": row.pilar_origem,
            "codigo_verbal": row.codigo_verbal, "versiculo_chave": row.versiculo_chave,
            "texto_reflexao": row.texto_reflexao, "texto_meditacao": row.texto_meditacao,
            "url_audio_meditacao": row.url_audio_meditacao}}
    finally:
        session.close()


# ═══════════════════════════════════════════════════════════════════════════
# DICIONÁRIO
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/dicionario/termos", summary="Todos os termos do dicionário teológico")
async def dicionario_termos():
    session = SessionLocal()
    try:
        rows = session.query(ConviteDicionario).order_by(ConviteDicionario.termo).all()
        return {"success": True, "termos": [{"termo": r.termo, "significado": r.significado} for r in rows]}
    finally:
        session.close()


# ═══════════════════════════════════════════════════════════════════════════
# TRILHAS DE CRESCIMENTO (4 temas × 30 dias)
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/trilhas/lista", summary="Lista trilhas (filtra por tema opcional)")
async def trilhas_lista(tema: Optional[str] = Query(None)):
    session = SessionLocal()
    try:
        q = session.query(ConviteTrilha)
        if tema:
            q = q.filter(ConviteTrilha.tema == tema)
        rows = q.order_by(ConviteTrilha.tema, ConviteTrilha.dia_trilha).all()
        temas = sorted({r.tema for r in rows})
        return {"success": True, "temas": temas, "dias": [
            {"tema": r.tema, "dia": r.dia_trilha, "titulo": r.titulo, "versiculo": r.versiculo,
             "reflexao": r.reflexao, "acao_pratica": r.acao_pratica} for r in rows]}
    finally:
        session.close()


# ═══════════════════════════════════════════════════════════════════════════
# TRILHA DO REINO (plano cronológico 18m/12m + marcos + ações)
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/trilha-reino/plano/{plano}", summary="Plano de leitura (18m ou 12m)")
async def trilha_reino_plano(plano: str, dia: Optional[int] = Query(None, ge=1)):
    if plano not in ("18m", "12m"):
        raise HTTPException(status_code=400, detail="plano deve ser 18m ou 12m")
    session = SessionLocal()
    try:
        q = session.query(ConviteTrilhaReino).filter(ConviteTrilhaReino.plano == plano)
        if dia:
            q = q.filter(ConviteTrilhaReino.dia == dia)
        rows = q.order_by(ConviteTrilhaReino.dia).all()
        if not rows:
            raise HTTPException(status_code=404, detail=f"Plano {plano} vazio")
        return {"success": True, "plano": plano, "total_dias": len(rows), "dias": [
            {"dia": r.dia, "leitura": r.leitura, "livro_abbr": r.livro_abbr,
             "capitulos": r.capitulos, "devocional": r.devocional, "acao": r.acao} for r in rows]}
    finally:
        session.close()


@router.get("/trilha-reino/marcos", summary="Marcos de fé (mapa visual)")
async def trilha_reino_marcos():
    session = SessionLocal()
    try:
        rows = session.query(ConviteTrilhaReinoMilestone).order_by(ConviteTrilhaReinoMilestone.start_day_18m).all()
        return {"success": True, "marcos": [
            {"key": r.key, "nome": r.nome, "icone": r.icone,
             "start_day_18m": r.start_day_18m, "start_day_12m": r.start_day_12m} for r in rows]}
    finally:
        session.close()


@router.get("/trilha-reino/acoes", summary="Banco de ações práticas")
async def trilha_reino_acoes():
    session = SessionLocal()
    try:
        rows = session.query(ConviteTrilhaReinoAcao).order_by(ConviteTrilhaReinoAcao.id).all()
        return {"success": True, "acoes": [r.texto for r in rows]}
    finally:
        session.close()


# ═══════════════════════════════════════════════════════════════════════════
# ARCADE BÍBLICO (jogos)
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/jogos/quiz", summary="Perguntas do quiz (filtra por dificuldade)")
async def jogos_quiz(dificuldade: Optional[str] = Query(None)):
    _check_dificuldade(dificuldade)
    session = SessionLocal()
    try:
        q = session.query(ConviteJogoQuiz)
        if dificuldade:
            q = q.filter(ConviteJogoQuiz.dificuldade == dificuldade)
        rows = q.order_by(ConviteJogoQuiz.id).all()
        return {"success": True, "perguntas": [
            {"id": r.id, "pergunta": r.pergunta, "opcoes": r.opcoes,
             "resposta_idx": r.resposta_idx, "dificuldade": r.dificuldade} for r in rows]}
    finally:
        session.close()


@router.get("/jogos/charadas", summary="Charadas 'Quem Sou Eu?' (filtra por dificuldade)")
async def jogos_charadas(dificuldade: Optional[str] = Query(None)):
    _check_dificuldade(dificuldade)
    session = SessionLocal()
    try:
        q = session.query(ConviteJogoCharada)
        if dificuldade:
            q = q.filter(ConviteJogoCharada.dificuldade == dificuldade)
        rows = q.order_by(ConviteJogoCharada.id).all()
        return {"success": True, "perguntas": [
            {"id": r.id, "dicas": r.dicas, "opcoes": r.opcoes,
             "resposta_idx": r.resposta_idx, "dificuldade": r.dificuldade} for r in rows]}
    finally:
        session.close()


@router.get("/jogos/forca", summary="Palavras da forca (filtra por dificuldade)")
async def jogos_forca(dificuldade: Optional[str] = Query(None)):
    _check_dificuldade(dificuldade)
    session = SessionLocal()
    try:
        q = session.query(ConviteJogoForca)
        if dificuldade:
            q = q.filter(ConviteJogoForca.dificuldade == dificuldade)
        rows = q.order_by(ConviteJogoForca.id).all()
        return {"success": True, "palavras": [
            {"id": r.id, "palavra": r.palavra, "dica": r.dica, "dificuldade": r.dificuldade} for r in rows]}
    finally:
        session.close()


@router.get("/jogos/caca-palavras", summary="Lista de palavras do caça-palavras (filtra por dificuldade)")
async def jogos_caca_palavras(dificuldade: Optional[str] = Query(None)):
    _check_dificuldade(dificuldade)
    session = SessionLocal()
    try:
        q = session.query(ConviteJogoCacaPalavras)
        if dificuldade:
            q = q.filter(ConviteJogoCacaPalavras.dificuldade == dificuldade)
        rows = q.order_by(ConviteJogoCacaPalavras.id).all()
        return {"success": True, "palavras": [
            {"id": r.id, "palavra": r.palavra, "dificuldade": r.dificuldade} for r in rows]}
    finally:
        session.close()


# ═══════════════════════════════════════════════════════════════════════════
# REGISTRO DO ROUTER
# ═══════════════════════════════════════════════════════════════════════════

def register_convite_routes(app):
    """Registra as rotas de conteúdo do 1Convite no app FastAPI."""
    app.include_router(router)
    logger.info("[ConviteAPI] Rotas registradas com sucesso")
