#!/usr/bin/env python3
"""Export articles from local SQLite as JSON for import to Railway."""

import json, sqlite3, os, sys

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dezafira.db")
OUTPUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "articles_export.json")

sq = sqlite3.connect(DB_PATH)
sq.row_factory = sqlite3.Row
cur = sq.cursor()

# Get blog channel
cur.execute("SELECT * FROM blog_channels")
channels = [dict(r) for r in cur.fetchall()]
channel = channels[0] if channels else None

# Get all posts
cur.execute("SELECT * FROM blog_posts ORDER BY created_at")
posts = []
for row in cur.fetchall():
    p = dict(row)
    # Convert datetime objects to strings
    for k, v in p.items():
        if hasattr(v, 'isoformat'):
            p[k] = v.isoformat()
    posts.append(p)

# Build export
export = {
    "channel": dict(channel) if channel else None,
    "posts": posts,
    "stats": {
        "total_posts": len(posts),
        "total_words": sum(p.get("word_count", 0) or 0 for p in posts),
        "with_images": sum(1 for p in posts if p.get("featured_image_url")),
        "without_images": sum(1 for p in posts if not p.get("featured_image_url")),
    }
}

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(export, f, ensure_ascii=False, indent=2)

print(f"Exportado: {OUTPUT}")
print(f"Artigos: {export['stats']['total_posts']}")
print(f"Palavras: {export['stats']['total_words']}")
print(f"Canal: {channel['name'] if channel else 'N/A'} (ID: {channel['id'] if channel else 'N/A'})")

sq.close()
