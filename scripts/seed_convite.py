#!/usr/bin/env python3
"""
Seed do conteúdo do produto "1Convite" no banco do DezafiraADM.

Lê os JSON canônicos de data/convite/ (gerados por scripts/convert_convite_data.py)
e popula as tabelas convite_* de forma idempotente (só insere o que falta):

  - convite_dicionario           (dicionário teológico — 16 termos, dedup)
  - convite_trilhas              (4 temas × 30 dias — Ansiedade/Família/Finanças/Propósito)
  - convite_matriz_diaria        (365 dias — 7 reais do 1Convite + 358 gerados)
  - convite_jogos_quiz/charadas/forca/caca_palavras   (arcade bíblico)
  - convite_trilha_reino(*)      (plano 18m/12m + marcos + ações)

Uso:
    python scripts/seed_convite.py                # conteúdo (rápido)
    python scripts/seed_convite.py --with-bible   # + Bíblia ACF (~31k versículos, download)

Var de ambiente opcional: DATABASE_URL (default: banco local/do projeto).
"""

import argparse
import json
import logging
import os
import sys
import urllib.request
import uuid

# Garante que a raiz do repo esteja no sys.path (roda de qualquer lugar)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("seed_convite")

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "convite")
BIBLE_URL = "https://raw.githubusercontent.com/thiagobodruk/bible/master/json/pt_acf.json"
BATCH = 1000


def _load(name: str):
    with open(os.path.join(DATA_DIR, name), "r", encoding="utf-8") as f:
        return json.load(f)


# ─────────────────────────────────────────────────────────────────────────────
# 1) Dicionário teológico — as DUAS listas originais do 1Convite (dedup)
# ─────────────────────────────────────────────────────────────────────────────

TERMOS_INDEX_JS = [
    ("graça", "Favor imerecido concedido por Deus ao homem. O amor ativo que resgata sem exigir méritos."),
    ("fé", "Firme fundamento das coisas que se esperam, e a prova das coisas que se não veem (Hebreus 11:1)."),
    ("reino", "O governo e a soberania de Deus estabelecidos no coração do homem e manifestados na sociedade."),
    ("propósito", "A intenção divina para a qual cada ser foi criado; o alinhamento com a vontade do Criador."),
    ("amor", "Do grego \"Agape\", o amor incondicional, sacrificial e baseado em decisão, não em sentimentos."),
    ("sabático", "Repouso ordenado por Deus, não apenas físico, mas espiritual, descansando na suficiência divina."),
    ("evangelho", "As \"Boas Novas\" da salvação, restauração e reconciliação da criação com Deus através de Cristo."),
    ("justiça", "Retidão moral e conformidade com a vontade de Deus. Estar em posição correta perante o Criador."),
]
TERMOS_SEED_JS = [
    ("Graça", "Favor imerecido de Deus. É o que recebemos pela fé, não pelas obras."),
    ("Justificação", "Ato de Deus que nos declara justos diante dEle, por meio da fé em Jesus."),
    ("Santificação", "Processo contínuo de transformação espiritual depois da justificação."),
    ("Propiciação", "Satisfação dada à justiça de Deus pelo sacrifício de Jesus na cruz."),
    ("Redenção", "Ato de resgatar da escravidão do pecado por meio do sangue de Cristo."),
    ("Conversão (Metanoia)", "Mudança profunda de mente e coração que leva a uma nova vida."),
    ("Avivamento", "Renovação espiritual coletiva que fortalece a fé e atrai perdidos."),
    ("Discipulado", "Processo de seguir a Jesus, aprender com Ele e reproduzir Seus ensinamentos."),
]


def seed_dicionario(session):
    from modules.convite_models import ConviteDicionario
    count = session.query(ConviteDicionario).count()
    if count:
        log.info(f"[dicionario] já tem {count} termos — pulando")
        return 0
    termos = dict(TERMOS_INDEX_JS)
    termos.update(dict(TERMOS_SEED_JS))  # seed.js sobrescreve só termos repetidos
    session.add_all([ConviteDicionario(termo=k, significado=v) for k, v in termos.items()])
    session.commit()
    log.info(f"[dicionario] inseridos {len(termos)} termos")
    return len(termos)


# ─────────────────────────────────────────────────────────────────────────────
# 2) Trilhas de crescimento — 4 temas × 30 dias (lógica idêntica ao seed.js)
# ─────────────────────────────────────────────────────────────────────────────

def _trilha_dados(tema: str, dia: int):
    if tema == "Ansiedade":
        return (f"Dia {dia}: Entregando o Controle",
                "Não andeis ansiosos por coisa alguma... - Filipenses 4:6",
                f"A ansiedade surge quando tentamos carregar um fardo de amanhã com a força de hoje. No dia {dia} dessa jornada de paz, lembre-se de que Deus governa o tempo e o agora.",
                "Pare o que está fazendo por 2 minutos, respire fundo e declare: Eu confio no Teu governo.")
    if tema == "Família":
        return (f"Dia {dia}: Fortalecendo Laços",
                "Eu e a minha casa serviremos ao Senhor. - Josué 24:15",
                f"A família é o primeiro laboratório do Reino de Deus na terra. No dia {dia}, veja o valor sagrado de cultivar relacionamentos saudáveis dentro do seu lar.",
                "Faça um elogio sincero para alguém da sua família hoje ou mande uma mensagem de carinho.")
    if tema == "Finanças":
        return (f"Dia {dia}: Princípio da Mordomia",
                "Ao Senhor pertence a terra e tudo o que nela há. - Salmo 24:1",
                f"Não somos donos, mas mordomos dos recursos que Deus confiou a nós. No dia {dia}, compreenda que a generosidade é a vacina contra a avareza e o medo da escassez.",
                "Separe um valor ou prepare algo para abençoar alguém que está passando por necessidade.")
    return (f"Dia {dia}: Descobrindo o Chamado",
            "Pois Dele, por Ele e para Ele são todas as coisas. - Romanos 11:36",
            f"Propósito não é o que você faz para Deus, mas o que Deus faz através de você. No dia {dia}, sintonize seu coração com os planos eternos do Pai.",
            "Escreva em um papel três talentos que você tem e como pode usá-los para servir ao próximo.")


def seed_trilhas(session):
    from modules.convite_models import ConviteTrilha
    count = session.query(ConviteTrilha).count()
    if count:
        log.info(f"[trilhas] já tem {count} dias — pulando")
        return 0
    rows = []
    for tema in ["Ansiedade", "Família", "Finanças", "Propósito"]:
        for dia in range(1, 31):
            titulo, versiculo, reflexao, acao = _trilha_dados(tema, dia)
            rows.append(ConviteTrilha(tema=tema, dia_trilha=dia, titulo=titulo,
                                      versiculo=versiculo, reflexao=reflexao, acao_pratica=acao))
    session.add_all(rows)
    session.commit()
    log.info(f"[trilhas] inseridos {len(rows)} dias (4 temas × 30)")
    return len(rows)


# ─────────────────────────────────────────────────────────────────────────────
# 3) Matriz diária — 7 dias reais + 358 gerados (lógica idêntica ao index.js)
# ─────────────────────────────────────────────────────────────────────────────

def _matriz_gerado(i: int):
    is_proposito = i % 2 != 0
    pilar = "PROPÓSITO_M2414" if is_proposito else "RECOMPENSA_AP321"
    codigo = (f"Código {i:02d}: Conexão intencional gera o fruto da eternidade." if is_proposito
              else f"Código {i:02d}: Seu valor não está na sua pressa, mas na sua herança.")
    versiculo = ("E disse-lhes: Ide por todo o mundo, pregai o evangelho a toda criatura. - Marcos 16:15" if is_proposito
                 else "Aquele que vencer herdará todas as coisas; e eu serei seu Deus, e ele será meu filho. - Apocalipse 21:7")
    reflexao = (f"O dia {i} convida você a ir além do seu círculo de conforto. Notar as pessoas e fazer convites de coração aberto é trazer o Reino de Deus à terra em gestos simples." if is_proposito
                else f"Hoje, no dia {i}, lembre-se de que sentar no trono significa reinar em paz. Pare, respire no silêncio e desfrute da abundância do amor que já preenche a sua identidade.")
    meditacao = (f"Respire fundo... e concentre-se na presença divina do Dia {i}. Deixe de lado os ruídos e conecte-se com o pilar de hoje. "
                 f"Faça uma pausa de respiração guiada, sintonize seu coração com as promessas eternas e peça a Deus força para colocar essa palavra em prática no seu caminhar diário.")
    audio = f"https://www.soundhelix.com/examples/mp3/SoundHelix-Song-{(i % 15) + 1}.mp3"
    return pilar, codigo, versiculo, reflexao, meditacao, audio


def seed_matriz(session):
    from modules.convite_models import ConviteMatrizDiaria
    count = session.query(ConviteMatrizDiaria).count()
    if count:
        log.info(f"[matriz] já tem {count} dias — pulando")
        return 0
    real = {d["dia_id"]: d for d in _load("matriz_diaria_real.json")["dias"]}
    rows = []
    for i in range(1, 366):
        if i in real:
            d = real[i]
            rows.append(ConviteMatrizDiaria(
                dia_id=i, pilar_origem=d["pilar_origem"], codigo_verbal=d["codigo_verbal"],
                versiculo_chave=d["versiculo_chave"], texto_reflexao=d["texto_reflexao"],
                texto_meditacao=d.get("texto_meditacao"), url_audio_meditacao=d.get("url_audio_meditacao")))
        else:
            pilar, codigo, versiculo, reflexao, meditacao, audio = _matriz_gerado(i)
            rows.append(ConviteMatrizDiaria(dia_id=i, pilar_origem=pilar, codigo_verbal=codigo,
                                            versiculo_chave=versiculo, texto_reflexao=reflexao,
                                            texto_meditacao=meditacao, url_audio_meditacao=audio))
    session.add_all(rows)
    session.commit()
    log.info(f"[matriz] inseridos {len(rows)} dias (7 reais + 358 gerados)")
    return len(rows)


# ─────────────────────────────────────────────────────────────────────────────
# 4) Arcade bíblico (quiz / charadas / forca / caça-palavras)
# ─────────────────────────────────────────────────────────────────────────────

def seed_arcade(session):
    from modules.convite_models import (ConviteJogoCacaPalavras, ConviteJogoCharada,
                                        ConviteJogoForca, ConviteJogoQuiz)
    total = 0

    if not session.query(ConviteJogoQuiz).count():
        perguntas = _load("arcade_quiz.json")["perguntas"]
        session.add_all([ConviteJogoQuiz(pergunta=p["question"], opcoes=p["options"],
                                         resposta_idx=p["answer"], dificuldade=p["difficulty"])
                         for p in perguntas])
        session.commit()
        log.info(f"[arcade] quiz: {len(perguntas)}")
        total += len(perguntas)

    if not session.query(ConviteJogoCharada).count():
        charadas = _load("arcade_charadas.json")["perguntas"]
        session.add_all([ConviteJogoCharada(dicas=c["clues"], opcoes=c["options"],
                                            resposta_idx=c["answer"], dificuldade=c["difficulty"])
                         for c in charadas])
        session.commit()
        log.info(f"[arcade] charadas: {len(charadas)}")
        total += len(charadas)

    if not session.query(ConviteJogoForca).count():
        forca = _load("arcade_forca.json")["palavras"]
        session.add_all([ConviteJogoForca(palavra=f["word"], dica=f["tip"], dificuldade=f["difficulty"])
                         for f in forca])
        session.commit()
        log.info(f"[arcade] forca: {len(forca)}")
        total += len(forca)

    if not session.query(ConviteJogoCacaPalavras).count():
        caca = _load("arcade_caca_palavras.json")["palavras"]
        session.add_all([ConviteJogoCacaPalavras(palavra=p["word"], dificuldade=p["difficulty"])
                         for p in caca])
        session.commit()
        log.info(f"[arcade] caça-palavras: {len(caca)}")
        total += len(caca)

    return total


# ─────────────────────────────────────────────────────────────────────────────
# 5) Trilha do Reino — planos 18m/12m + marcos + ações
# ─────────────────────────────────────────────────────────────────────────────

def _generate_plan(entries, book_names, devotionais, acoes):
    days = []
    for i, e in enumerate(entries):
        book, ch_start, ch_end = e
        chapters = list(range(ch_start, ch_end + 1))
        chapter_str = f"{ch_start}" if ch_start == ch_end else f"{ch_start}-{ch_end}"
        days.append((book_names.get(book, book), book, chapter_str, chapters,
                     devotionais[i % len(devotionais)], acoes[i % len(acoes)]))
    return days


def _compress_to_12m(plan18m, book_names, devotionais, acoes):
    result = []
    i = 0
    while i < len(plan18m) and len(result) < 365:
        book, ch_start, ch_end = plan18m[i]
        end_ch = ch_end
        while i + 1 < len(plan18m) and len(result) < 365:
            n_book, n_start, n_end = plan18m[i + 1]
            if n_book == book and (end_ch - ch_start + 1) + (n_end - n_start + 1) <= 5:
                end_ch = n_end
                i += 1
            else:
                break
        result.append([book, ch_start, end_ch])
        i += 1
    return _generate_plan(result, book_names, devotionais, acoes)


def seed_trilha_reino(session):
    from modules.convite_models import (ConviteTrilhaReino, ConviteTrilhaReinoAcao,
                                        ConviteTrilhaReinoMilestone)
    data = _load("trilha_reino.json")
    total = 0

    if not session.query(ConviteTrilhaReino).count():
        plan = data["plan_18m"]
        book_names = data["book_names"]
        devotionais = data["devocionais"]
        acoes = data["acoes"]

        rows = []
        for plano, dias in (("18m", _generate_plan(plan, book_names, devotionais, acoes)),
                            ("12m", _compress_to_12m(plan, book_names, devotionais, acoes))):
            for dia, (leitura, abbr, chap_str, chapters, devocional, acao) in enumerate(dias, start=1):
                rows.append(ConviteTrilhaReino(plano=plano, dia=dia, leitura=f"{leitura} {chap_str}",
                                               livro_abbr=abbr, capitulos=chapters,
                                               devocional=devocional, acao=acao))
        session.add_all(rows)
        session.commit()
        log.info(f"[trilha_reino] {len(rows)} dias (18m={sum(1 for r in rows if r.plano=='18m')}, 12m={sum(1 for r in rows if r.plano=='12m')})")
        total += len(rows)

    if not session.query(ConviteTrilhaReinoMilestone).count():
        milestones = data["config"]["milestones"]
        session.add_all([ConviteTrilhaReinoMilestone(key=m["id"], nome=m["name"], icone=m.get("icon"),
                                                     start_day_18m=m["startDay18"], start_day_12m=m["startDay12"])
                         for m in milestones])
        session.commit()
        log.info(f"[trilha_reino] marcos: {len(milestones)}")
        total += len(milestones)

    if not session.query(ConviteTrilhaReinoAcao).count():
        acoes = data["acoes"]
        session.add_all([ConviteTrilhaReinoAcao(texto=a) for a in acoes])
        session.commit()
        log.info(f"[trilha_reino] ações: {len(acoes)}")
        total += len(acoes)

    return total


# ─────────────────────────────────────────────────────────────────────────────
# 6) Bíblia ACF (opcional) — download do JSON público + inserção em lotes
# ─────────────────────────────────────────────────────────────────────────────

def seed_biblia(session, engine):
    from modules.convite_models import ConviteBiblia
    count = session.query(ConviteBiblia).count()
    if count:
        log.info(f"[biblia] já tem {count} versículos — pulando")
        return 0

    log.info(f"[biblia] baixando ACF de {BIBLE_URL} ...")
    with urllib.request.urlopen(BIBLE_URL, timeout=60) as r:
        raw = r.read()
    if raw[:3] == b"\xef\xbb\xbf":
        raw = raw[3:]
    bible = json.loads(raw.decode("utf-8"))

    inserted = 0
    batch = []
    with engine.begin() as conn:
        for book in bible:
            for ci, chapter in enumerate(book["chapters"], start=1):
                for vi, verse in enumerate(chapter, start=1):
                    batch.append({"livro_nome": book["name"], "livro_abrev": book["abbrev"],
                                  "capitulo": ci, "versiculo": vi, "texto": verse})
                    if len(batch) >= BATCH:
                        conn.execute(ConviteBiblia.__table__.insert(), batch)
                        inserted += len(batch)
                        log.info(f"  [biblia] {inserted} versículos...")
                        batch = []
        if batch:
            conn.execute(ConviteBiblia.__table__.insert(), batch)
            inserted += len(batch)
    log.info(f"[biblia] importados {inserted} versículos")
    return inserted


# ─────────────────────────────────────────────────────────────────────────────
# 7) Registro do miniapp 1Convite + domínio dedicado (Host-routing)
# ─────────────────────────────────────────────────────────────────────────────

CONVITE_MINIPP = {
    "app_name": "1Convite",
    "slug": "1convite",
    "niche": "espiritual",
    "app_type": "Interactive PWA",
    "status": "active",
    "brand_name": "1Convite",
    "headline": "Um app sobre o Reino: Bíblia, devocional e jogos",
    "subheadline": "Bíblia ACF, matriz diária, trilhas de crescimento, arcade bíblico e a Trilha do Reino.",
    "description": "Super app cristão que integra a Palavra de Deus, interatividade, ferramentas de IA e criatividade em um só lugar.",
    "pain": "Crescer espiritualmente exige constância; o 1Convite torna a Bíblia, a oração e o estudo parte da rotina.",
    "cta_text": "Começar agora",
    "theme": {
        "primary": "#A78BFA", "accent": "#C4B5FD",
        "gradient": "135deg, #2E1065, #7C3AED",
        "bg": "#090D16", "surface": "#161320",
        "emoji": "✨", "tagline": "Um app sobre o Reino"
    },
    "brand_voice": "Acollhedor, esperançoso e bíblico — tom de um mentor espiritual.",
    "dedicated_domain": "1convite.com.br",
}


def register_miniapp(session):
    """Cria (idempotente) o miniapp 1Convite e associa o domínio dedicado."""
    from modules.database import MiniApp
    from modules.convite_models import MiniappDomain, create_db_miniapp_domain

    cfg = CONVITE_MINIPP
    existing = session.query(MiniApp).filter(MiniApp.slug == cfg["slug"]).first()
    if existing:
        app_id = existing.id
        log.info(f"[miniapp] 1Convite já existe (id={app_id}) — atualizando branding")
        for k, v in cfg.items():
            if k in ("dedicated_domain",):
                continue
            if hasattr(existing, k):
                setattr(existing, k, v)
        session.commit()
    else:
        app_id = str(uuid.uuid4())
        session.add(MiniApp(id=app_id, app_name=cfg["app_name"], niche=cfg["niche"],
                            app_type=cfg["app_type"], status=cfg["status"], slug=cfg["slug"],
                            pain=cfg["pain"], description=cfg["description"],
                            headline=cfg["headline"], subheadline=cfg["subheadline"],
                            cta_text=cfg["cta_text"], brand_name=cfg["brand_name"],
                            brand_voice=cfg["brand_voice"],
                            theme=json.dumps(cfg["theme"], ensure_ascii=False)))
        session.commit()
        log.info(f"[miniapp] 1Convite criado (id={app_id}, slug={cfg['slug']})")

    domain = cfg["dedicated_domain"]
    existing_domain = session.query(MiniappDomain).filter(MiniappDomain.domain == domain).first()
    if existing_domain:
        log.info(f"[miniapp] domínio {domain} já associado a {existing_domain.slug}")
    else:
        create_db_miniapp_domain(domain, app_id, cfg["slug"])
        log.info(f"[miniapp] domínio dedicado {domain} → /app/{cfg['slug']}")
    return app_id


# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Seed do conteúdo 1Convite no banco do DezafiraADM")
    parser.add_argument("--with-bible", action="store_true", help="também importa a Bíblia ACF (~31k versículos)")
    parser.add_argument("--register-miniapp", action="store_true",
                        help="cria o miniapp 1Convite + domínio dedicado 1convite.com.br")
    parser.add_argument("--db", default=None, help="DATABASE_URL override (ex: sqlite:///convite_test.db)")
    args = parser.parse_args()

    if args.db:
        os.environ["DATABASE_URL"] = args.db

    from modules.database import engine, SessionLocal
    import modules.convite_models  # noqa: F401 — registra modelos no Base
    from modules.convite_models import create_all_tables
    create_all_tables()

    session = SessionLocal()
    try:
        seed_dicionario(session)
        seed_trilhas(session)
        seed_matriz(session)
        seed_arcade(session)
        seed_trilha_reino(session)
        if args.with_bible:
            seed_biblia(session, engine)
        if args.register_miniapp:
            register_miniapp(session)
        log.info("\n✅ Seed 1Convite concluído!")
    finally:
        session.close()


if __name__ == "__main__":
    main()
