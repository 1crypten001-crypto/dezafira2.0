"""
RAG Biblico — Busca inteligente no conteudo biblico.
Indexa artigos, livros e cursos usando embeddings semanticos.
"""

from __future__ import annotations
from typing import List, Dict, Any

from agents.llm import query_llm


class BiblicalRAGAgent:
    """Agente RAG para buscar e responder sobre conteudo biblico."""

    def __init__(self):
        self.embeddings_model = None
        self.documents: List[Dict[str, Any]] = []
        self.embeddings: list = []
        self.index_loaded = False

    def _load_embedder(self):
        """Carrega modelo de embeddings (lazy)."""
        if self.embeddings_model is None:
            from sentence_transformers import SentenceTransformer
            self.embeddings_model = SentenceTransformer('all-MiniLM-L6-v2')

    def _embed(self, texts: List[str]) -> List[np.ndarray]:
        """Gera embeddings para uma lista de textos."""
        self._load_embedder()
        import numpy as np
        return self.embeddings_model.encode(texts)

    async def index_content(self, force: bool = False):
        """Indexa todo o conteudo do banco (artigos, livros, cursos)."""
        if self.index_loaded and not force:
            return
        
        from modules.database import SessionLocal, BlogPost, BookChapter, CourseLesson
        
        db = SessionLocal()
        try:
            docs = []
            
            posts = db.query(BlogPost).filter(BlogPost.status == "published").all()
            for p in posts:
                docs.append({
                    "id": f"post_{p.id}", "type": "artigo",
                    "title": p.title or "",
                    "content": p.content or "",
                    "source": "blog",
                    "url": f"/api/v1/blogs/view/{p.slug or p.id}",
                    "created_at": p.created_at.isoformat() if p.created_at else "",
                })
            
            chapters = db.query(BookChapter).filter(BookChapter.status == "published").all()
            for ch in chapters:
                docs.append({
                    "id": f"bch_{ch.id}", "type": "livro_capitulo",
                    "title": ch.title or "",
                    "content": ch.content or "",
                    "source": "livro",
                    "url": f"/api/v1/books/{ch.book_id}",
                    "created_at": ch.created_at.isoformat() if ch.created_at else "",
                })
            
            lessons = db.query(CourseLesson).all()
            for les in lessons:
                docs.append({
                    "id": f"crl_{les.id}", "type": "curso_aula",
                    "title": les.title or "",
                    "content": les.content or "",
                    "source": "curso", "url": "",
                    "created_at": les.created_at.isoformat() if les.created_at else "",
                })
            
            self.documents = docs
            
            if docs:
                texts = [f"{d['title']} {d['content'][:2000]}" for d in docs]
                self.embeddings = self._embed(texts)
                self.index_loaded = True
                print(f"[RAG] Indexado: {len(docs)} documentos")
            else:
                print("[RAG] Nenhum documento para indexar")
        except Exception as e:
            print(f"[RAG] Erro ao indexar: {e}")
        finally:
            db.close()

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Busca os documentos mais relevantes para a pergunta."""
        if not self.index_loaded or not self.documents or len(self.embeddings) == 0:
            return []
        
        query_emb = self._embed([query])[0]
        scores = []
        for i, doc_emb in enumerate(self.embeddings):
            cosine_sim = np.dot(query_emb, doc_emb) / (
                np.linalg.norm(query_emb) * np.linalg.norm(doc_emb) + 1e-10
            )
            scores.append((i, float(cosine_sim)))
        
        scores.sort(key=lambda x: x[1], reverse=True)
        results = []
        for i, score in scores[:top_k]:
            doc = self.documents[i].copy()
            doc["relevance"] = round(score, 4)
            results.append(doc)
        return results

    async def ask(self, question: str) -> Dict[str, Any]:
        """Responde uma pergunta com base no conteudo indexado."""
        await self.index_content()
        results = self.search(question, top_k=5)
        
        if not results:
            return {
                "answer": "Ainda nao tenho conteudo suficiente para responder. Publique mais artigos, livros ou cursos primeiro.",
                "sources": []
            }
        
        context = "\n\n---\n\n".join([
            f"Fonte ({r['type']}): {r['title']}\n{r['content'][:1500]}"
            for r in results
        ])
        
        prompt = (
            f"Voce e um assistente biblico e teorico especializado. Responda a pergunta abaixo com base SOMENTE no contexto fornecido.\n\n"
            f"Seja claro, cite as fontes biblicas quando aplicavel, e indique quando a resposta nao esta no contexto.\n\n"
            f"PERGUNTA: {question}\n\n"
            f"CONTEXTO:\n{context}\n\n"
            f"RESPOSTA:"
        )
        
        answer = await query_llm([
            {"role": "system", "content": "Voce e um teologo e educador cristao. Responda em portugues brasileiro de forma clara, profunda e biblica. Sempre cite as fontes."},
            {"role": "user", "content": prompt},
        ], max_tokens=2048)
        
        sources = [{"title": r["title"], "type": r["type"], "url": r["url"], "relevance": r["relevance"]} for r in results[:3]]
        
        return {"answer": answer, "sources": sources, "documents_found": len(results)}


rag_agent = BiblicalRAGAgent()
