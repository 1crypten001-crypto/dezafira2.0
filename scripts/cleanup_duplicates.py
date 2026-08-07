"""
Cleanup — Remove artigos duplicados do blog.
Mantém o post com maior word_count de cada grupo de títulos similares.

Uso: python scripts/cleanup_duplicates.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.database import (
    SessionLocal, BlogPost, BlogChannel,
    get_db_blog_posts,
)


def find_similar_groups(posts: list, threshold: float = 0.85) -> list:
    """
    Agrupa posts por similaridade de título.
    Usa sobreposição de palavras como métrica simples (sem dependências externas).
    Retorna lista de grupos: [(canonical_title, [(post, score), ...]), ...]
    """
    import re
    
    def normalize(t: str) -> str:
        t = t.lower().strip()
        t = re.sub(r'[^a-zà-ÿ0-9\s]', '', t)
        t = re.sub(r'\s+', ' ', t)
        return t.strip()
    
    def word_overlap(a: str, b: str) -> float:
        words_a = set(normalize(a).split())
        words_b = set(normalize(b).split())
        if not words_a or not words_b:
            return 0.0
        intersection = words_a & words_b
        union = words_a | words_b
        return len(intersection) / max(len(union), 1)
    
    # Marcar todos como não agrupados
    grouped = [False] * len(posts)
    groups = []
    
    for i in range(len(posts)):
        if grouped[i]:
            continue
        group = [posts[i]]
        grouped[i] = True
        
        for j in range(i + 1, len(posts)):
            if grouped[j]:
                continue
            sim = word_overlap(posts[i].title or "", posts[j].title or "")
            if sim >= threshold:
                group.append(posts[j])
                grouped[j] = True
        
        if len(group) > 1:
            groups.append(group)
    
    return groups


def main():
    print("=" * 60)
    print("  LIMPEZA DE ARTIGOS DUPLICADOS")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        # Buscar todos os posts
        posts = db.query(BlogPost).order_by(BlogPost.created_at.desc()).all()
        print(f"\nTotal de posts no banco: {len(posts)}")
        
        # Listar todos
        print("\n--- TODOS OS POSTS ---")
        for p in posts:
            ch = db.query(BlogChannel).filter(BlogChannel.id == p.channel_id).first()
            ch_name = ch.name if ch else "?"
            print(f"  [{p.id[:16]}] {p.title[:55]:55s} | {p.word_count:5d}w | {p.status:12s} | canal: {ch_name[:20]}")
        
        # Encontrar duplicatas
        groups = find_similar_groups(posts)
        
        if not groups:
            print("\n✅ Nenhuma duplicata encontrada!")
            return
        
        print(f"\n⚠️  {len(groups)} grupo(s) de duplicatas encontrados:")
        
        total_removed = 0
        for group in groups:
            # Ordenar por word_count DESC (maior primeiro)
            sorted_group = sorted(group, key=lambda p: p.word_count or 0, reverse=True)
            best = sorted_group[0]  # Mantém o maior
            
            print(f"\n  Grupo: '{best.title[:50]}'")
            print(f"    🏆 Manter: [{best.id[:16]}] {best.word_count}w (mais completo)")
            
            for p in sorted_group[1:]:
                print(f"    🗑️  Remover: [{p.id[:16]}] {p.word_count}w")
                db.delete(p)
                total_removed += 1
        
        db.commit()
        print(f"\n✅ {total_removed} duplicata(s) removida(s) com sucesso!")
        
        # Mostrar resultado final
        remaining = db.query(BlogPost).order_by(BlogPost.created_at.desc()).all()
        print(f"\n--- RESULTADO FINAL: {len(remaining)} posts ---")
        for p in remaining:
            print(f"  [{p.id[:16]}] {p.title[:55]:55s} | {p.word_count:5d}w | {p.status:12s}")
        
    finally:
        db.close()


if __name__ == "__main__":
    main()
