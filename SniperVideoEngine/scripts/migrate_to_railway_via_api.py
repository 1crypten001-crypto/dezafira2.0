#!/usr/bin/env python3
"""
Migra os artigos exportados do SQLite local para o Railway via API REST.
Le o arquivo articles_export.json e envia para o endpoint /api/v1/blog/import-posts.
"""

import json
import os
import sys
import httpx
import time

# ============================================================================
# CONFIG
# ============================================================================
RAILWAY_BASE = "https://backend-production-f90d.up.railway.app"
EXPORT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "articles_export.json")

# ============================================================================
# 1. Ler export
# ============================================================================
if not os.path.exists(EXPORT_FILE):
    print(f"ERRO: Arquivo de exportacao nao encontrado: {EXPORT_FILE}")
    print("Execute primeiro: python scripts/export_articles.py")
    sys.exit(1)

with open(EXPORT_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

posts = data["posts"]
channel = data["channel"]
stats = data["stats"]

print("=" * 60)
print(f"MIGRACAO: {stats['total_posts']} artigos -> Railway")
print(f"Canal: {channel['name']} (ID: {channel['id']})")
print(f"Total palavras: {stats['total_words']}")
print(f"Com imagens: {stats['with_images']}")
print("=" * 60)

# ============================================================================
# 2. Verificar canal no Railway
# ============================================================================
print(f"\nVerificando canal no Railway...")
resp = httpx.get(f"{RAILWAY_BASE}/api/v1/blog/o-reino/info", timeout=15)
if resp.status_code == 200:
    info = resp.json()
    print(f"  Canal encontrado: {info['name']} (ID: {info['id']})")
    print(f"  Artigos atuais: {info.get('post_count', 0)}")
    channel_id = info["id"]
else:
    print(f"  Canal NAO encontrado no Railway. Verifique se o seed foi executado.")
    print(f"  Vou tentar criar via seed...")
    resp = httpx.post(f"{RAILWAY_BASE}/api/v1/blogs/seed", timeout=15)
    print(f"  Seed: {resp.json()}")
    resp = httpx.get(f"{RAILWAY_BASE}/api/v1/blog/o-reino/info", timeout=15)
    if resp.status_code == 200:
        info = resp.json()
        channel_id = info["id"]
        print(f"  Canal criado: {info['name']} (ID: {channel_id})")
    else:
        print(f"  ERRO: Nao foi possivel criar canal.")
        sys.exit(1)

# ============================================================================
# 3. Importar artigos em lote
# ============================================================================
print(f"\nImportando {len(posts)} artigos...")

# Postar em lotes de 5 para evitar timeout
BATCH_SIZE = 5
total_inserted = 0
total_skipped = 0
total_errors = 0

for i in range(0, len(posts), BATCH_SIZE):
    batch = posts[i:i+BATCH_SIZE]
    payload = {
        "posts": batch,
        "channel_id": channel_id,
    }

    try:
        resp = httpx.post(
            f"{RAILWAY_BASE}/api/v1/blog/import-posts",
            json=payload,
            timeout=60,
        )
        result = resp.json()
        inserted = result.get("inserted", 0)
        skipped = result.get("skipped", 0)
        err_count = result.get("errors", 0)

        total_inserted += inserted
        total_skipped += skipped
        total_errors += err_count

        print(f"  Lote {i//BATCH_SIZE + 1}/{(len(posts)-1)//BATCH_SIZE + 1}: "
              f"+{inserted} inseridos, {skipped} pulados, {err_count} erros")

        if result.get("error_details"):
            for err in result["error_details"][:2]:
                print(f"    X {err}")

    except Exception as e:
        print(f"  ERRO no lote {i//BATCH_SIZE + 1}: {e}")
        total_errors += len(batch)

# ============================================================================
# 4. Verificar resultado
# ============================================================================
print(f"\nVerificando resultado final...")
time.sleep(3)  # Aguarda o banco atualizar

resp = httpx.get(f"{RAILWAY_BASE}/api/v1/blog/o-reino/info", timeout=15)
if resp.status_code == 200:
    info = resp.json()
    print(f"\n--- RESULTADO FINAL ---")
    print(f"Blog: {info['name']}")
    print(f"Artigos agora no Railway: {info.get('post_count', '?')}")
    print(f"Inseridos: {total_inserted}")
    print(f"Pulados (ja existiam): {total_skipped}")
    print(f"Erros: {total_errors}")

# Verificar posts
resp = httpx.get(f"{RAILWAY_BASE}/api/v1/blog/o-reino/posts", timeout=15)
if resp.status_code == 200:
    posts_railway = resp.json().get("posts", [])
    total_wc = sum(p.get("word_count", 0) or 0 for p in posts_railway)
    with_img = sum(1 for p in posts_railway if p.get("featured_image_url"))
    print(f"\nTotal palavras: {total_wc}")
    print(f"Com imagens: {with_img} / {len(posts_railway)}")
    print(f"\nArtigos importados:")
    for p in posts_railway[:5]:
        img = " [IMG]" if p.get("featured_image_url") else ""
        print(f"  - {p['title'][:55]} ({p.get('word_count', 0)} pal){img}")
    if len(posts_railway) > 5:
        print(f"  ... e mais {len(posts_railway) - 5} artigos")

print(f"\nBlog publico: {RAILWAY_BASE}/blog/o-reino")
print("Concluido!")
