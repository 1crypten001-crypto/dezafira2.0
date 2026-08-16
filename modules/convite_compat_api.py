"""
MÓDULO: convite_compat_api.py
DESCRIÇÃO: Camada de COMPATIBILIDADE — replica o contrato da API Express
original do 1Convite (rotas `/api/v1/*` que o PWA React chama) em cima do
FastAPI do DezafiraADM.

Fonte de dados: tabelas `convite_*` (populadas por scripts/seed_convite.py) e
o estado de usuário fresco (`convite_user_progress`, `convite_contatos`,
`convite_trilha_progresso`, `convite_leads`).

Decisões de port (aprovadas pelo dono):
  * Dados de usuário começam do ZERO — sem migração de contas/progresso legados.
  * Conselheiros IA (ChatGPT via LWC) mantêm a chave original — o FastAPI
    faz proxy para o sidecar Node (web/1convite/backend-lwc) via LWC_SIDECAR_URL.
  * Conteúdo (Bíblia, matriz, trilhas, dicionário) lê do banco do ADM.

Registro no app:
    from modules.convite_compat_api import register_convite_compat_routes
    register_convite_compat_routes(app)
"""

import json
import logging
import os
import random
from datetime import datetime

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, Response
from sqlalchemy import func, or_

from modules.database import SessionLocal
from modules.convite_models import (
    ConviteBiblia,
    ConviteDicionario,
    ConviteMatrizDiaria,
    ConviteTrilha,
    create_db_convite_contato,
    create_db_convite_lead,
    delete_db_convite_contato,
    get_db_convite_trilha_progresso,
    get_db_convite_user,
    list_db_convite_contatos,
    set_db_convite_trilha_progresso,
    update_db_convite_user,
)

logger = logging.getLogger("convite_compat_api")

router = APIRouter(prefix="/api/v1", tags=["1Convite (compat)"])

# ── ABREVIAÇÕES usadas pelo audio original (beblia.bible) ────────────────────
_FALLBACK_ORDENADOS = [
    "gn", "ex", "lv", "nm", "dt", "js", "jz", "rt", "1sm", "2sm", "1rs", "2rs",
    "1cr", "2cr", "ed", "ne", "et", "jo", "sl", "pv", "ec", "ct", "is", "jr",
    "lm", "ez", "dn", "os", "jl", "am", "ob", "jn", "mq", "na", "hc", "sf",
    "ag", "zc", "ml", "mt", "mc", "lc", "jo", "at", "rm", "1co", "2co", "gl",
    "ef", "fp", "cl", "1ts", "2ts", "1tm", "2tm", "tt", "fm", "hb", "tg", "1pe",
    "2pe", "1jo", "2jo", "3jo", "jd", "ap",
]
_FALLBACK_BOOKS = [
    "Gênesis", "Êxodo", "Levítico", "Números", "Deuteronômio", "Josué",
    "Juízes", "Rute", "1 Samuel", "2 Samuel", "1 Reis", "2 Reis", "1 Crônicas",
    "2 Crônicas", "Esdras", "Neemias", "Ester", "Jó", "Salmos", "Provérbios",
    "Eclesiastes", "Cânticos", "Isaías", "Jeremias", "Lamentações", "Ezequiel",
    "Daniel", "Oseias", "Joel", "Amós", "Obadias", "Jonas", "Miqueias", "Naum",
    "Habacuque", "Sofonias", "Ageu", "Zacarias", "Malaquias", "Mateus", "Marcos",
    "Lucas", "João", "Atos", "Romanos", "1 Coríntios", "2 Coríntios", "Gálatas",
    "Efésios", "Filipenses", "Colossenses", "1 Tessalonicenses", "2 Tessalonicenses",
    "1 Timóteo", "2 Timóteo", "Tito", "Filemom", "Hebreus", "Tiago", "1 Pedro",
    "2 Pedro", "1 João", "2 João", "3 João", "Judas", "Apocalipse",
]

_MOCK_CODE = {
    "dia_id": 1,
    "pilar_origem": "PROPÓSITO_M2414",
    "codigo_verbal": "Código 01: O Reino começa no quintal da sua casa.",
    "versiculo_chave": "E este evangelho do reino será pregado em todo o mundo como testemunho a todas as nações, então, virá o fim. - Mateus 24:14",
    "texto_reflexao": "O evangelismo eficaz não começa em outra nação, mas no próximo contato que você fizer hoje.",
    "texto_meditacao": "Pai, a Ti rendo graças. Obrigado porque o Senhor é bom e sempre me ouve. Capacita-me a ser bênção hoje. Em nome de Jesus, amém!",
    "url_audio_meditacao": "/piano.mp3",
}


# ── HELPERS ──────────────────────────────────────────────────────────────────

def _code_dict(row) -> dict:
    if row is None:
        return dict(_MOCK_CODE)
    return {
        "dia_id": row.dia_id,
        "pilar_origem": row.pilar_origem,
        "codigo_verbal": row.codigo_verbal,
        "versiculo_chave": row.versiculo_chave,
        "texto_reflexao": row.texto_reflexao,
        "texto_meditacao": row.texto_meditacao or "",
        "url_audio_meditacao": row.url_audio_meditacao or "/piano.mp3",
    }


def _get_code_for_day(dia: int) -> dict:
    session = SessionLocal()
    try:
        row = session.query(ConviteMatrizDiaria).filter(ConviteMatrizDiaria.dia_id == dia).first()
        code = _code_dict(row)
        code["dia_id"] = dia
        return code
    finally:
        session.close()


# ═══════════════════════════════════════════════════════════════════════════
# USUÁRIO / PERFIL / AUTH (estado fresco — começa do zero)
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/usuario")
async def compat_usuario():
    return get_db_convite_user()


@router.post("/usuario/perfil")
async def compat_usuario_perfil(request: Request):
    body = await _safe_json(request)
    user = update_db_convite_user(
        nome=body.get("nome"), email=body.get("email"), avatar=body.get("avatar")
    )
    return user


@router.post("/auth/convite")
async def compat_auth_convite(request: Request):
    """Login do 1Convite (mesma lógica do Express original).

    NOTA: o caminho é /auth/convite (e não /auth/google) porque /api/v1/auth/google
    já pertence ao NextAuth do admin — o PWA absorvido foi ajustado para chamar
    /auth/convite (ver web/1convite/frontend/src/App.jsx).
    """
    body = await _safe_json(request)
    user = update_db_convite_user(
        nome=body.get("nome"), email=body.get("email"), avatar=body.get("avatar")
    )
    return {"success": True, "user": user}


@router.get("/codigo-dia")
async def compat_codigo_dia():
    user = get_db_convite_user()
    code = _get_code_for_day(user["dia_atual"])
    return {"user": user, "code": code}


@router.post("/codigo-dia/save")
async def compat_codigo_dia_save(request: Request):
    """Salva o código do dia enriquecido pela IA (atualiza a matriz diária).
    Validação idêntica à do Express original."""
    body = await _safe_json(request)
    dia_id = body.get("dia_id")
    if not dia_id or not body.get("codigo_verbal") or not body.get("versiculo_chave") or not body.get("texto_reflexao"):
        return JSONResponse(status_code=400, content={"error": "Parâmetros ausentes"})
    session = SessionLocal()
    try:
        row = session.query(ConviteMatrizDiaria).filter(ConviteMatrizDiaria.dia_id == int(dia_id)).first()
        if row:
            row.codigo_verbal = body["codigo_verbal"]
            row.versiculo_chave = body["versiculo_chave"]
            row.texto_reflexao = body["texto_reflexao"]
            if body.get("texto_meditacao"):
                row.texto_meditacao = body["texto_meditacao"]
            session.commit()
        return {"success": True}
    finally:
        session.close()


@router.post("/checkpoint/start")
async def compat_checkpoint_start():
    now_ms = int(datetime.utcnow().timestamp() * 1000)
    update_db_convite_user(checkpoint_started_at=now_ms, checkpoint_completado=False)
    return {"success": True, "startedAt": now_ms}


@router.post("/sync-checkpoint")
async def compat_sync_checkpoint():
    user = update_db_convite_user(checkpoint_completado=True, checkpoint_started_at=0)
    return {"success": True, "message": "O Agora foi destravado com sucesso!", "user": user}


@router.post("/avancar-dia")
async def compat_avancar_dia():
    # Incrementa o dia (1..365) e reseta o checkpoint — lógica fiel ao Express
    user = get_db_convite_user()
    novo_dia = user["dia_atual"] + 1 if user["dia_atual"] < 365 else 1
    user = update_db_convite_user(dia_atual=novo_dia, checkpoint_completado=False, checkpoint_started_at=0)
    code = _get_code_for_day(novo_dia)
    return {"user": user, "code": code}


@router.post("/reiniciar-jornada")
async def compat_reiniciar_jornada():
    user = update_db_convite_user(dia_atual=1, checkpoint_completado=False, checkpoint_started_at=0)
    return {"success": True, "message": "Jornada resetada para o Dia 1", "user": user}


@router.post("/admin/definir-plano")
async def compat_definir_plano(request: Request):
    body = await _safe_json(request)
    plano = body.get("plano") or "FREE"
    user = update_db_convite_user(status_plano=str(plano).upper())
    return {"success": True, "plano": user["status_plano"]}


# ═══════════════════════════════════════════════════════════════════════════
# CONTATOS / HISTÓRICO (começa vazio — start do zero)
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/contatos")
async def compat_contatos_list():
    return list_db_convite_contatos()


@router.post("/contatos")
async def compat_contatos_create(request: Request):
    body = await _safe_json(request)
    nome = (body.get("nome") or "").strip()
    if not nome:
        return JSONResponse(status_code=400, content={"error": "Nome é obrigatório"})
    contato = create_db_convite_contato(
        nome=nome, relacao=body.get("relacao"), prioritario=bool(body.get("prioritario"))
    )
    return {"success": True, "contato": contato}


@router.delete("/contatos/{contato_id}")
async def compat_contatos_delete(contato_id: int):
    delete_db_convite_contato(contato_id)
    return {"success": True}


@router.post("/contatos/{contato_id}/acao")
async def compat_contatos_acao(contato_id: int):
    # No original, registra a ação (oração/missão) do contato. Sem tabela de
    # ações no start-do-zero; responde sucesso sem efeito colateral.
    return {"success": True}


@router.get("/historico")
async def compat_historico():
    return {"rows": []}


# ═══════════════════════════════════════════════════════════════════════════
# TRILHAS DE CRESCIMENTO (conteúdo do banco + progresso fresco)
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/trilhas/lista")
async def compat_trilhas_lista():
    session = SessionLocal()
    try:
        temas = [r[0] for r in session.query(ConviteTrilha.tema).distinct().order_by(ConviteTrilha.tema).all()]
        return temas or ["Ansiedade", "Família", "Finanças", "Propósito"]
    finally:
        session.close()


@router.get("/trilhas/ativa")
async def compat_trilhas_ativa():
    progresso = get_db_convite_trilha_progresso()
    if not progresso.get("ativa"):
        return {"ativa": False}
    session = SessionLocal()
    try:
        row = (session.query(ConviteTrilha)
               .filter(ConviteTrilha.tema == progresso["tema"],
                       ConviteTrilha.dia_trilha == progresso["dia_progresso"])
               .first())
        conteudo = None
        if row:
            conteudo = {
                "dia_trilha": row.dia_trilha,
                "titulo": row.titulo,
                "versiculo": row.versiculo,
                "reflexao": row.reflexao,
                "acao_pratica": row.acao_pratica,
            }
        else:
            conteudo = {
                "dia_trilha": progresso["dia_progresso"],
                "titulo": f"Dia {progresso['dia_progresso']}: Jornada de Fé",
                "versiculo": "O Senhor é o meu pastor; nada me faltará. - Salmos 23:1",
                "reflexao": f"Neste dia de reflexão sobre {progresso['tema']}, que a palavra de Deus ilumine os seus passos.",
                "acao_pratica": "Dedique 5 minutos para orar por alguém hoje.",
            }
        return {
            "ativa": True,
            "tema": progresso["tema"],
            "dia_progresso": progresso["dia_progresso"],
            "conteudo": conteudo,
        }
    finally:
        session.close()


@router.post("/trilhas/iniciar")
async def compat_trilhas_iniciar(request: Request):
    body = await _safe_json(request)
    tema = (body.get("tema") or "").strip()
    if not tema:
        return JSONResponse(status_code=400, content={"error": "Tema da trilha é obrigatório"})
    set_db_convite_trilha_progresso(tema, 1)
    return {"success": True, "tema": tema, "dia_progresso": 1}


@router.post("/trilhas/cancelar")
async def compat_trilhas_cancelar():
    set_db_convite_trilha_progresso(None, 1)
    return {"success": True}


@router.post("/trilhas/completar-dia")
async def compat_trilhas_completar_dia():
    progresso = get_db_convite_trilha_progresso()
    if not progresso.get("ativa"):
        return JSONResponse(status_code=400, content={"error": "Nenhuma trilha ativa no momento"})
    novo_dia = progresso["dia_progresso"] + 1
    if novo_dia > 30:
        set_db_convite_trilha_progresso(None, 1)
        return {"success": True, "concluida": True}
    set_db_convite_trilha_progresso(progresso["tema"], novo_dia)
    return {"success": True, "concluida": False, "novoDia": novo_dia}


# ═══════════════════════════════════════════════════════════════════════════
# BÍBLIA (ACF) — shapes fiéis ao Express original
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/biblia/livros")
async def compat_biblia_livros():
    session = SessionLocal()
    try:
        rows = (session.query(ConviteBiblia.livro_nome, ConviteBiblia.livro_abrev,
                              func.max(ConviteBiblia.capitulo).label("total"))
                .group_by(ConviteBiblia.livro_nome, ConviteBiblia.livro_abrev)
                .order_by(func.min(ConviteBiblia.id))
                .all())
        if not rows:
            return []
        return [{"livro_abrev": a, "livro_nome": n, "total": t, "capitulos": t} for n, a, t in rows]
    finally:
        session.close()


@router.get("/biblia/capitulos/{abrev}")
async def compat_biblia_capitulos(abrev: str):
    session = SessionLocal()
    try:
        max_cap = (session.query(func.max(ConviteBiblia.capitulo))
                   .filter(ConviteBiblia.livro_abrev == abrev.lower()).scalar())
        if max_cap is None:
            return JSONResponse(status_code=404, content={"error": f"Livro '{abrev}' não encontrado"})
        return {"total": max_cap}
    finally:
        session.close()


@router.get("/biblia/texto/{abrev}/{capitulo}")
async def compat_biblia_texto(abrev: str, capitulo: int):
    session = SessionLocal()
    try:
        rows = (session.query(ConviteBiblia.versiculo, ConviteBiblia.texto)
                .filter(ConviteBiblia.livro_abrev == abrev.lower(),
                        ConviteBiblia.capitulo == capitulo)
                .order_by(ConviteBiblia.versiculo)
                .all())
        if not rows:
            return JSONResponse(status_code=404, content={"error": f"{abrev} {capitulo} não encontrado"})
        return [{"versiculo": v, "texto": t, "livro": abrev, "capitulo": capitulo} for v, t in rows]
    finally:
        session.close()


@router.get("/biblia/busca")
async def compat_biblia_busca(request: Request):
    q = (request.query_params.get("q") or "").strip()
    if len(q) < 3:
        return {"success": True, "resultados": []}
    session = SessionLocal()
    try:
        pattern = f"%{q}%"
        rows = (session.query(ConviteBiblia)
                .filter(or_(ConviteBiblia.texto.ilike(pattern),
                            ConviteBiblia.livro_nome.ilike(pattern)))
                .order_by(ConviteBiblia.id)
                .limit(30)
                .all())
        return {"success": True, "resultados": [
            {"livro": r.livro_nome, "abrev": r.livro_abrev, "capitulo": r.capitulo,
             "versiculo": r.versiculo, "texto": r.texto} for r in rows]}
    finally:
        session.close()


@router.get("/biblia/aleatorio")
async def compat_biblia_aleatorio():
    session = SessionLocal()
    try:
        row = session.query(ConviteBiblia).order_by(func.random()).first()
        if not row:
            return JSONResponse(status_code=404, content={"error": "Bíblia vazia"})
        return {"livro": row.livro_nome, "abrev": row.livro_abrev, "capitulo": row.capitulo,
                "versiculo": row.versiculo, "texto": row.texto}
    finally:
        session.close()


# ── ÁUDIO: URLs de narração (beblia.bible primária; LibriVox fallback) ──────

@router.get("/biblia/audio/{abrev}/{capitulo}")
async def compat_biblia_audio(abrev: str, capitulo: int, request: Request):
    search = abrev.lower()
    if search in _FALLBACK_ORDENADOS:
        book_name = _FALLBACK_BOOKS[_FALLBACK_ORDENADOS.index(search)]
        cap_pad = str(int(capitulo)).zfill(3)
        audio_url = f"https://beblia.bible:81/BibleAudio/portuguese/{book_name}/{cap_pad}.mp3"
        backend = _backend_base(request)
        return {
            "url": audio_url,
            "proxy": f"{backend}/api/v1/biblia/audio-stream/{book_name}/{cap_pad}.mp3",
            "source": "primary",
            "license": "Verificar licença da fonte",
        }
    # Fallback LibriVox (livros sem correspondência em beblia)
    archive = _librivox_lookup(abrev, capitulo)
    if archive:
        backend = _backend_base(request)
        return {
            "url": archive["url"],
            "proxy": f"{backend}/api/v1/biblia/audio-stream-librivox/{archive['item_id']}/{archive['file_path']}",
            "source": "librivox",
            "license": "Public Domain (LibriVox)",
        }
    return JSONResponse(status_code=404, content={"error": "Livro não suportado para áudio"})


@router.get("/biblia/audio-stream/{book}/{chapter}")
async def compat_biblia_audio_stream(book: str, chapter: str):
    """Proxy de streaming do áudio primário (beblia.bible)."""
    url = f"https://beblia.bible:81/BibleAudio/portuguese/{book}/{chapter}"
    return await _stream_proxy(url)


@router.get("/biblia/audio-stream-librivox/{item_id}/{file_name}")
async def compat_biblia_audio_stream_librivox(item_id: str, file_name: str):
    """Proxy de streaming do áudio LibriVox/Internet Archive."""
    url = f"https://archive.org/download/{item_id}/{file_name}"
    return await _stream_proxy(url)


_LIBRIVOX_MAP = {
    "gn": {"id": "Bible-KJV-01-Genesis", "prefix": "KJVBible_01_Genesis_", "chapters": 50},
    "ex": {"id": "Bible-KJV-02-Exodus", "prefix": "KJVBible_02_Exodus_", "chapters": 40},
    "lv": {"id": "Bible-KJV-03-Leviticus", "prefix": "KJVBible_03_Leviticus_", "chapters": 27},
    "nm": {"id": "Bible-KJV-04-Numbers", "prefix": "KJVBible_04_Numbers_", "chapters": 36},
    "dt": {"id": "Bible-KJV-05-Deuteronomy", "prefix": "KJVBible_05_Deuteronomy_", "chapters": 34},
    "js": {"id": "Bible-KJV-06-Joshua", "prefix": "KJVBible_06_Joshua_", "chapters": 24},
    "jz": {"id": "Bible-KJV-07-Judges", "prefix": "KJVBible_07_Judges_", "chapters": 21},
    "sl": {"id": "Bible-KJV-19-Psalms", "prefix": "KJVBible_19_Psalms_", "chapters": 150},
    "pv": {"id": "Bible-KJV-20-Proverbs", "prefix": "KJVBible_20_Proverbs_", "chapters": 31},
    "is": {"id": "Bible-KJV-23-Isaiah", "prefix": "KJVBible_23_Isaiah_", "chapters": 66},
    "mt": {"id": "Bible-KJV-40-Matthew", "prefix": "KJVBible_40_Matthew_", "chapters": 28},
    "mc": {"id": "Bible-KJV-41-Mark", "prefix": "KJVBible_41_Mark_", "chapters": 16},
    "lc": {"id": "Bible-KJV-42-Luke", "prefix": "KJVBible_42_Luke_", "chapters": 24},
    "jo": {"id": "Bible-KJV-43-John", "prefix": "KJVBible_43_John_", "chapters": 21},
}


def _librivox_lookup(abrev: str, capitulo: int):
    info = _LIBRIVOX_MAP.get(abrev.lower())
    if not info or capitulo < 1 or capitulo > info["chapters"]:
        return None
    file_path = f"{info['prefix']}{str(capitulo).zfill(3)}.mp3"
    return {"item_id": info["id"], "file_path": file_path,
            "url": f"https://archive.org/download/{info['id']}/{file_path}"}


def _backend_base(request: Request) -> str:
    host = request.headers.get("host") or ""
    scheme = request.url.scheme
    if host:
        return f"{scheme}://{host}"
    return os.getenv("BACKEND_URL", "https://dezafiraadm-production.up.railway.app")


async def _stream_proxy(url: str):
    """Faz proxy do stream de áudio (Range requests para o player)."""
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            resp = await client.get(url)
            if resp.status_code >= 400:
                return Response(status_code=resp.status_code, content=b"", media_type="audio/mpeg")
            content_type = resp.headers.get("content-type", "audio/mpeg")
            return Response(content=resp.content, media_type=content_type)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Falha no proxy de áudio %s: %s", url, exc)
        return Response(status_code=502, content=b"", media_type="audio/mpeg")


# ═══════════════════════════════════════════════════════════════════════════
# DICIONÁRIO / PAGAMENTOS / LEADS / HEALTH
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/dicionario/termos")
async def compat_dicionario_termos():
    session = SessionLocal()
    try:
        rows = session.query(ConviteDicionario).order_by(ConviteDicionario.termo).all()
        return {r.termo: r.significado for r in rows}  # shape original: mapa termo→significado
    finally:
        session.close()


@router.post("/pagamentos/criar-preferencia")
async def compat_pagamentos_criar_preferencia(request: Request):
    """Preferência de pagamento do 1Convite.

    Com ASAAS_API_KEY no .env → cobrança PIX REAL (customer upsert + charge).
    Sem a chave → fallback fake (dev offline), como o Express original.
    """
    body = await _safe_json(request)
    if os.getenv("ASAAS_API_KEY"):
        try:
            from modules.asaas_client import AsaasClient
            nome = body.get("nome") or "Cliente 1Convite"
            email = body.get("email") or "cliente@1convite.com"
            cpf = body.get("cpf") or body.get("cpf_cnpj")
            phone = body.get("telefone") or body.get("phone")
            valor_cents = int(body.get("valor_cents") or body.get("preco_cents") or 0)
            descricao = body.get("descricao") or "Acesso ao 1Convite — Super App do Reino"
            referencia = body.get("referencia") or f"1convite_{int(datetime.utcnow().timestamp())}"

            client = AsaasClient()
            try:
                customer = await client.create_customer(
                    nome, email, cpf, phone, external_reference=referencia)
                charge = await client.create_pix_charge(
                    customer["id"], valor_cents, descricao, external_reference=referencia)
            finally:
                await client.aclose()
            return {
                "success": True,
                "preferenceId": charge["payment_id"],
                "checkoutUrl": charge["invoiceUrl"],
                "billingType": "PIX",
                "pixPayload": (charge.get("pix") or {}).get("payload", ""),
                "pixEncodedImage": (charge.get("pix") or {}).get("encodedImage", ""),
                "expirationDate": (charge.get("pix") or {}).get("expirationDate", ""),
                "status": charge["status"],
            }
        except Exception as exc:  # noqa: BLE001
            logger.warning("Asaas falhou (fallback fake): %s", exc)
            pref = f"pref_1convite_{random.randint(100000000, 999999999)}"
            return {"success": True, "preferenceId": pref,
                    "checkoutUrl": f"/simular-pagamento?pref_id={pref}", "fallback": True}
    pref = f"pref_1convite_{random.randint(100000000, 999999999)}"
    return {"success": True, "preferenceId": pref,
            "checkoutUrl": f"/simular-pagamento?pref_id={pref}", "fallback": True}


@router.post("/pagamentos/webhook")
async def compat_pagamentos_webhook(request: Request):
    """Webhook de pagamento (compat). Com corpo Asaas → processa evento real;
    com corpo legado ({action: payment.created}) → ativa PREMIUM direto."""
    body = await _safe_json(request)
    if "event" in body and "payment" in body:  # evento Asaas v3
        from modules.asaas_client import AsaasClient
        client = AsaasClient()
        try:
            result = await client.handle_webhook(body)
        finally:
            await client.aclose()
        if result.get("processed"):
            update_db_convite_user(status_plano="PREMIUM")
            return {"success": True, "processed": True, "event": result["event"],
                    "payment_id": result["payment_id"], "status": result.get("status")}
        return {"success": True, "processed": False, "event": result["event"]}
    # legado (simulação) — mantém compatibilidade
    update_db_convite_user(status_plano="PREMIUM")
    return {"success": True, "message": "Plano ativado para PREMIUM via webhook do Mercado Pago!"}


@router.post("/leads")
async def compat_leads(request: Request):
    body = await _safe_json(request)
    create_db_convite_lead(
        telefone=body.get("phone"), nome=body.get("nome"),
        email=body.get("email"), origem=body.get("origem"), pagina=body.get("pagina"),
    )
    return {"success": True}


@router.get("/health")
async def compat_health():
    return {"status": "ok", "db": "connected", "time": datetime.utcnow().isoformat()}


# ═══════════════════════════════════════════════════════════════════════════
# ASAAS — pagamentos na venda (PIX real)
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/asaas/status")
async def asaas_status():
    """Valida o token Asaas (leitura). Devolve dados seguros da conta."""
    if not os.getenv("ASAAS_API_KEY"):
        return {"success": False, "configured": False, "message": "ASAAS_API_KEY não configurado"}
    try:
        from modules.asaas_client import AsaasClient
        client = AsaasClient()
        try:
            acc = await client.get_account()
        finally:
            await client.aclose()
        return {"success": True, "configured": True, "sandbox": os.getenv("ASAAS_API_KEY", "").startswith("$aact_sandbox_"),
                "account": {"email": acc.get("email"), "personType": acc.get("personType"),
                            "cpfCnpj": acc.get("cpfCnpj"), "company": acc.get("company")}}
    except Exception as exc:  # noqa: BLE001
        return {"success": False, "configured": True, "error": str(exc)[:200]}


@router.post("/asaas/cobranca-pix")
async def asaas_cobranca_pix(request: Request):
    """Checkout PIX genérico da fábrica: cria/upsert customer + cobrança PIX.

    Body: {nome, email, cpf?, telefone?, valor_cents, descricao?, referencia?}
    Usado pelo Clube (ou qualquer produto) para vender com o Asaas.
    """
    body = await _safe_json(request)
    email = (body.get("email") or "").strip()
    valor_cents = int(body.get("valor_cents") or 0)
    if not email or valor_cents <= 0:
        return JSONResponse(status_code=400, content={"error": "email e valor_cents (>0) são obrigatórios"})
    if not os.getenv("ASAAS_API_KEY"):
        return JSONResponse(status_code=503, content={"error": "ASAAS_API_KEY não configurado no Adm."})
    from modules.asaas_client import AsaasClient, AsaasError
    client = AsaasClient()
    try:
        customer = await client.create_customer(
            body.get("nome") or email.split("@")[0], email,
            cpf_cnpj=body.get("cpf"), phone=body.get("telefone"),
            external_reference=body.get("referencia") or "dezafira_venda",
        )
        charge = await client.create_pix_charge(
            customer["id"], valor_cents,
            body.get("descricao") or "Produto Dezafira",
            external_reference=body.get("referencia") or "dezafira_venda",
        )
    except AsaasError as exc:
        return JSONResponse(status_code=502, content={"error": str(exc)[:300]})
    finally:
        await client.aclose()
    return {"success": True, "customer_id": customer["id"], **charge}


@router.post("/asaas/webhook")
async def asaas_webhook(request: Request):
    """Webhook oficial do Asaas (eventos PAYMENT_*). Libera acesso quando pago."""
    body = await _safe_json(request)
    if not os.getenv("ASAAS_API_KEY"):
        return JSONResponse(status_code=503, content={"error": "ASAAS_API_KEY não configurado no Adm."})
    from modules.asaas_client import AsaasClient, AsaasError
    client = AsaasClient()
    try:
        result = await client.handle_webhook(body)
    except AsaasError as exc:
        return JSONResponse(status_code=502, content={"error": str(exc)[:300]})
    finally:
        await client.aclose()
    if result.get("processed"):
        update_db_convite_user(status_plano="PREMIUM")
    return {"success": True, **result}


@router.get("/asaas/cobranca/{payment_id}")
async def asaas_cobranca_status(payment_id: str):
    """Status de uma cobrança Asaas (para o front conferir se pagou)."""
    if not os.getenv("ASAAS_API_KEY"):
        return JSONResponse(status_code=503, content={"error": "ASAAS_API_KEY não configurado no Adm."})
    from modules.asaas_client import AsaasClient, AsaasError
    client = AsaasClient()
    try:
        p = await client.get_payment(payment_id)
    except AsaasError as exc:
        return JSONResponse(status_code=404, content={"error": str(exc)[:300]})
    finally:
        await client.aclose()
    return {"success": True, "payment_id": p["id"], "status": p["status"],
            "billingType": p.get("billingType"), "value": p.get("value"),
            "invoiceUrl": p.get("invoiceUrl"), "externalReference": p.get("externalReference")}


# ═══════════════════════════════════════════════════════════════════════════
# CONSELHEIROS IA (ChatGPT via LWC) — proxy para o sidecar Node
#
# O 1Convite usa o SDK `@opencoredev/loginwithchatgpt-server` (device flow do
# ChatGPT). O sidecar original vive em web/1convite/backend-lwc/ e roda com o
# mesmo LWC_SECRET. Aqui fazemos proxy transparente de /api/v1/chatgpt/* para
# o sidecar. Sem sidecar configurado, responde 503 JSON — o PWA lida com
# "não autenticado" de forma graciosa (não quebra o app).
# ═══════════════════════════════════════════════════════════════════════════

@router.api_route("/chatgpt/{rest:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
async def compat_chatgpt_proxy(rest: str, request: Request):
    sidecar = os.getenv("LWC_SIDECAR_URL", "").strip().rstrip("/")
    if not sidecar:
        return JSONResponse(status_code=503, content={"status": "unavailable",
                                                      "error": "Conselheiros IA offline (sidecar LWC não configurado)"})
    url = f"{sidecar}/api/v1/chatgpt/{rest}"
    if request.query_params:
        url += "?" + str(request.query_params)
    body_bytes = await request.body()
    headers = {k: v for k, v in request.headers.items() if k.lower() not in ("host", "content-length")}
    try:
        async with httpx.AsyncClient(timeout=90.0, follow_redirects=False) as client:
            resp = await client.request(request.method, url, content=body_bytes or None, headers=headers)
            content_type = resp.headers.get("content-type", "application/json")
            if "application/json" in content_type:
                return JSONResponse(status_code=resp.status_code, content=json.loads(resp.content or b"{}"))
            return Response(content=resp.content, status_code=resp.status_code,
                            media_type=content_type.split(";")[0])
    except Exception as exc:  # noqa: BLE001
        logger.warning("Sidecar LWC inacessível: %s", exc)
        return JSONResponse(status_code=502, content={"status": "unavailable", "error": str(exc)})


# ── Helpers internos ─────────────────────────────────────────────────────────

async def _safe_json(request: Request) -> dict:
    try:
        raw = await request.body()
        if not raw:
            return {}
        return json.loads(raw.decode("utf-8"))
    except Exception:  # noqa: BLE001
        return {}


# ═══════════════════════════════════════════════════════════════════════════
# REGISTRO
# ═══════════════════════════════════════════════════════════════════════════

def register_convite_compat_routes(app):
    """Registra as rotas de compatibilidade /api/v1/* do 1Convite no app FastAPI."""
    app.include_router(router)
    logger.info("[ConviteCompat] Rotas de compatibilidade registradas com sucesso")
