#!/usr/bin/env python3
"""
Migração dos artigos do SQLite local para o PostgreSQL do Railway.
Lê do arquivo local SniperVideoEngine/dezafira.db e insere no banco Railway.

USO:
  set DATABASE_URL=postgresql://... && python scripts/migrate_to_railway.py

Ou setar DATABASE_URL como variável de ambiente do sistema.
"""

import os
import sys
import sqlite3
import uuid
from datetime import datetime

# ============================================================================
# CONFIG — APENAS via variável de ambiente (NUNCA hardcoded!)
# ============================================================================
RAILWAY_DATABASE_URL = os.getenv("DATABASE_URL")
if not RAILWAY_DATABASE_URL:
    print("=" * 60)
    print("❌ DATABASE_URL não configurada!")
    print("=" * 60)
    print("Defina a variável de ambiente DATABASE_URL com a string de conexão do PostgreSQL.")
    print("Exemplo:")
    print("  set DATABASE_URL=postgresql://usuario:senha@host:porta/banco")
    print("  python scripts/migrate_to_railway.py")
    print()
    sys.exit(1)

LOCAL_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "dezafira.db"
)

# ============================================================================
# 1. Conectar ao SQLite local
# ============================================================================
print("=" * 60)
print("MIGRACAO: SQLite Local -> Railway PostgreSQL")
print("=" * 60)

if not os.path.exists(LOCAL_DB_PATH):
    print(f"❌ Banco local não encontrado em: {LOCAL_DB_PATH}")
    sys.exit(1)

sqlite_conn = sqlite3.connect(LOCAL_DB_PATH)
sqlite_conn.row_factory = sqlite3.Row
sqlite_cursor = sqlite_conn.cursor()
print(f"[OK] SQLite local conectado: {LOCAL_DB_PATH}")

# ============================================================================
# 2. Conectar ao PostgreSQL Railway
# ============================================================================
try:
    from sqlalchemy import create_engine, text

    # Ajusta postgres:// -> postgresql://
    db_url = RAILWAY_DATABASE_URL
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    pg_engine = create_engine(db_url, pool_pre_ping=True)
    pg_conn = pg_engine.connect()
    print(f"[OK] PostgreSQL Railway conectado!")
except Exception as e:
    print(f"❌ Falha ao conectar no Railway PostgreSQL: {e}")
    sys.exit(1)

# ============================================================================
# 3. Ler dados do SQLite
# ============================================================================

# Blog channels
sqlite_cursor.execute("SELECT * FROM blog_channels")
local_channels = [dict(row) for row in sqlite_cursor.fetchall()]
print(f"\n[STATS] Canais locais: {len(local_channels)}")

# Blog posts (todos os artigos, incluindo os com channel_id='default' que serão associados ao canal)
sqlite_cursor.execute("""
    SELECT * FROM blog_posts 
    ORDER BY created_at
""")
local_posts = [dict(row) for row in sqlite_cursor.fetchall()]
print(f"[STATS] Artigos locais (total): {len(local_posts)}")

# Conta quantos têm channel_id=default (artigos antigos que serão vinculados ao canal)
default_posts = [p for p in local_posts if p.get("channel_id") == "default"]
channel_posts = [p for p in local_posts if p.get("channel_id") != "default"]
print(f"   - Com channel_id do blog: {len(channel_posts)}")
print(f"   - Com channel_id=default (serao vinculados): {len(default_posts)}")

# Total de palavras
total_words = sum(p.get("word_count", 0) or 0 for p in local_posts)
print(f"[STATS] Total de palavras: {total_words}")

# ============================================================================
# 4. Verificar se o blog channel já existe no Railway
# ============================================================================

channel = None
for ch in local_channels:
    result = pg_conn.execute(
        text("SELECT id FROM blog_channels WHERE name = :name"),
        {"name": ch["name"]}
    )
    existing = result.fetchone()
    if existing:
        channel_id = existing[0]
        print(f"[INFO] Blog '{ch['name']}' ja existe no Railway (ID: {channel_id})")
        channel = ch
    else:
        # Criar o channel
        new_id = ch["id"] if ch["id"] else f"blg_{uuid.uuid4().hex[:6]}"
        pg_conn.execute(
            text("""
                INSERT INTO blog_channels 
                (id, name, nicho, lang, platform, site_url, status, frequency, created_at)
                VALUES (:id, :name, :nicho, :lang, :platform, :site_url, :status, :frequency, :created_at)
            """),
            {
                "id": new_id,
                "name": ch["name"],
                "nicho": ch["nicho"],
                "lang": ch["lang"],
                "platform": ch.get("platform", "dezafira"),
                "site_url": ch.get("site_url", ""),
                "status": ch.get("status", "active"),
                "frequency": ch.get("frequency", "daily"),
                "created_at": ch.get("created_at", datetime.utcnow()),
            }
        )
        channel_id = new_id
        channel = ch
        print(f"[OK] Blog '{ch['name']}' CRIADO no Railway (ID: {channel_id})")

pg_conn.commit()

# ============================================================================
# 5. Migrar os artigos
# ============================================================================

inserted = 0
skipped = 0
errors = 0

for post in local_posts:
    try:
        # Verifica se já existe pelo slug
        existing = pg_conn.execute(
            text("SELECT id FROM blog_posts WHERE slug = :slug"),
            {"slug": post.get("slug", "")}
        ).fetchone()

        if existing:
            print(f"  [SKIP] Ja existe: {post['title'][:50]}")
            skipped += 1
            continue

        # Insere o artigo
        pg_conn.execute(
            text("""
                INSERT INTO blog_posts 
                (id, channel_id, title, slug, content, excerpt, keywords, 
                 featured_image_url, status, word_count, topic, created_at, published_at)
                VALUES 
                (:id, :channel_id, :title, :slug, :content, :excerpt, :keywords,
                 :featured_image_url, :status, :word_count, :topic, :created_at, :published_at)
            """),
            {
                "id": post.get("id") or f"post_{uuid.uuid4().hex[:8]}",
                "channel_id": channel_id,
                "title": post.get("title", ""),
                "slug": post.get("slug", ""),
                "content": post.get("content", ""),
                "excerpt": post.get("excerpt", ""),
                "keywords": post.get("keywords", ""),
                "featured_image_url": post.get("featured_image_url"),
                "status": post.get("status", "draft"),
                "word_count": post.get("word_count", 0),
                "topic": post.get("topic", ""),
                "created_at": post.get("created_at", datetime.utcnow()),
                "published_at": post.get("published_at"),
            }
        )
        inserted += 1
        print(f"  [OK] {post['title'][:60]} ({post.get('word_count', 0)} palavras)")

    except Exception as e:
        errors += 1
        print(f"  [ERRO] {post.get('title', '?')[:40]}: {e}")

# Commit final
pg_conn.commit()

# ============================================================================
# 6. Resumo
# ============================================================================
print("\n" + "=" * 60)
print("RESUMO DA MIGRAÇÃO")
print("=" * 60)
print(f"  [STATS] Canal: {channel['name'] if channel else 'N/A'}")
print(f"  [STATS] Total artigos no SQLite: {len(local_posts)}")
print(f"  [STATS] Inseridos no Railway: {inserted}")
print(f"  [STATS] Ja existiam (pulados): {skipped}")
print(f"  [STATS] Erros: {errors}")
print(f"  [STATS] Total palavras: {total_words}")
print("=" * 60)

# Fechar conexões
sqlite_conn.close()
pg_conn.close()
