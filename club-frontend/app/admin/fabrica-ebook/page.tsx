"use client";

export const dynamic = 'force-dynamic';

import { useState, useEffect, useRef } from "react";
import AgnesCoverButton from "../../../components/AgnesCoverButton";
import BrandKitEditor from "../../../components/BrandKitEditor";
import Link from "next/link";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "https://dezafiraadm-production.up.railway.app";
const authH = (): Record<string, string> => { const t = localStorage.getItem('dz_token'); return t ? { Authorization: 'Bearer '+t } : {}; };

export default function FabricaEbookPage() {
  const [title, setTitle] = useState("");
  const [niche, setNiche] = useState("Tecnologia & IA");
  const [loading, setLoading] = useState(false);
  const [packData, setPackData] = useState<any>(null);
  const [activeEbookIndex, setActiveEbookIndex] = useState(0);
  const [activeChapterIndex, setActiveChapterIndex] = useState(0);
  const [existingBooks, setExistingBooks] = useState<any[]>([]);
  const [loadingList, setLoadingList] = useState(true);
  const [taskId, setTaskId] = useState<string | null>(null);
  const [progress, setProgress] = useState<any>(null);
  const pollRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    loadExistingBooks();
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, []);

  const loadExistingBooks = async () => {
    try {
      const token = typeof window !== "undefined" ? localStorage.getItem("dz_token") : "";
      const res = await fetch(`${API_URL}/api/v1/ebooks`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      const data = await res.json();
      setExistingBooks(data.books || []);
    } catch (err) {
      console.error("Erro ao listar ebooks:", err);
    } finally {
      setLoadingList(false);
    }
  };

  const pollStatus = (tid: string) => {
    if (pollRef.current) clearInterval(pollRef.current);
    pollRef.current = setInterval(async () => {
      try {
        const res = await fetch(`${API_URL}/api/v1/ebooks/task/${tid}`);
        const data = await res.json();
        setProgress(data);

        if (data.status === "completed" || data.status === "failed") {
          if (pollRef.current) clearInterval(pollRef.current);
          setLoading(false);
          if (data.status === "completed" && data.pack_ready) {
            const resultRes = await fetch(`${API_URL}/api/v1/ebooks/task/${tid}/result`);
            const resultData = await resultRes.json();
            if (resultData.success) {
              setPackData(resultData.pack_data);
              setActiveEbookIndex(0);
              setActiveChapterIndex(0);
            }
          }
        }
      } catch (err) {
        console.error("Erro ao consultar status:", err);
      }
    }, 3000);
  };

  const handleGeneratePack = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;

    setLoading(true);
    setPackData(null);
    setProgress(null);

    try {
      const res = await fetch(`${API_URL}/api/v1/ebooks/generate-pack`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title, niche })
      });
      const data = await res.json();
      if (data.success && data.task_id) {
        setTaskId(data.task_id);
        pollStatus(data.task_id);
      }
    } catch (err) {
      console.error("Erro ao iniciar geracao:", err);
      setLoading(false);
    }
  };

  const currentEbook = packData?.pack ? packData.pack[activeEbookIndex] : null;
  const currentChapter = currentEbook?.chapters ? currentEbook.chapters[activeChapterIndex] : null;

  const phases = progress?.phases || {};
  const phaseOrder = ["names", "covers", "chapters_main", "chapters_bonus1", "chapters_bonus2", "done"];
  const phaseLabels: Record<string, string> = {
    names: "📝 Nomes",
    covers: "🎨 Capas",
    chapters_main: "📘 Capitulos Principal",
    chapters_bonus1: "🎁 Capitulos Bonus 1",
    chapters_bonus2: "🎁 Capitulos Bonus 2",
    done: "✅ Concluido",
  };

  return (
    <div className="min-h-screen" style={{ background: 'var(--ink)', color: 'var(--text)' }}>
      <header className="border-b" style={{ background: 'var(--ink)', borderColor: 'var(--border)' }}>
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link href="/admin" className="text-sm hover:brightness-110" style={{ color: 'var(--text-dim)' }}>← Voltar ao Admin</Link>
            <span style={{ color: 'var(--text-dim)' }}>/</span>
            <h1 className="text-lg font-bold" style={{ color: 'var(--brand)' }}>📗 Fábrica de Ebooks (Pacote Triplo)</h1>
          </div>
          <span className="badge text-xs font-bold" style={{ color: 'var(--success)' }}>🟢 Agentes Especializados</span>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-8 space-y-8">

        <BrandKitEditor />

        {/* Lista de Ebooks Existentes */}
        {existingBooks.length > 0 && (
          <div className="border rounded-2xl p-6 shadow-xl" style={{ background: 'var(--ink)', borderColor: 'var(--border)' }}>
            <h2 className="text-lg font-bold mb-4" style={{ color: 'var(--text)' }}>📚 Ebooks Criados ({existingBooks.length})</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {existingBooks.map((book) => (
                <div key={book.id} className="border rounded-xl p-4 transition-all hover:brightness-110" style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}>
                  <div className="flex items-start justify-between mb-2">
                    <h3 className="text-sm font-bold line-clamp-1" style={{ color: 'var(--text)' }}>{book.title}</h3>
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-full" style={{ background: book.status === "published" ? 'var(--success)' : 'var(--warning)', color: 'var(--ink)' }}>
                      {book.status === "published" ? "🟢 Publicado" : "🟡 Rascunho"}
                    </span>
                  </div>
                  <p className="text-xs mb-1" style={{ color: 'var(--text-dim)' }}>{book.topic}</p>
                  <p className="text-xs" style={{ color: 'var(--text-dim)' }}>{book.total_words || 0} palavras</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Painel de Disparo */}
        <div className="border rounded-2xl p-6 shadow-xl space-y-4" style={{ background: 'var(--ink)', borderColor: 'var(--border)' }}>
          <div>
            <h2 className="text-xl font-extrabold" style={{ color: 'var(--text)' }}>Gerar Pacote de 3 Ebooks</h2>
            <p className="text-xs" style={{ color: 'var(--text-dim)' }}>
              A geracao e <strong>assincrona</strong> — voce pode acompanhar o progresso abaixo. 
              Total: ~18 capitulos via LLM + 3 capas. Tempo estimado: 10-15 minutos.
            </p>
          </div>

          <form onSubmit={handleGeneratePack} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="md:col-span-2">
                <label className="block text-xs font-bold mb-1" style={{ color: 'var(--text-dim)' }}>TITULO OU TEMA</label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="Ex: Guia Definitivo de Negocios Digitais com IA"
                  className="w-full border rounded-xl px-4 py-3 text-sm focus:outline-none focus:brightness-110"
                  style={{ background: 'var(--surface)', borderColor: 'var(--border)', color: 'var(--text)' }}
                  required
                />
              </div>
              <div>
                <label className="block text-xs font-bold mb-1" style={{ color: 'var(--text-dim)' }}>NICHO</label>
                <select
                  value={niche}
                  onChange={(e) => setNiche(e.target.value)}
                  className="w-full border rounded-xl px-4 py-3 text-sm focus:outline-none focus:brightness-110"
                  style={{ background: 'var(--surface)', borderColor: 'var(--border)', color: 'var(--text)' }}
                >
                  <option value="Tecnologia & IA">Tecnologia & IA</option>
                  <option value="Fitness & Saude">Fitness & Saude</option>
                  <option value="Financas & Negocios">Financas & Negocios</option>
                  <option value="Espiritualidade">Espiritualidade</option>
                  <option value="Marketing Digital">Marketing Digital</option>
                </select>
              </div>
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full font-extrabold py-3.5 rounded-xl text-sm shadow-lg hover:brightness-110 disabled:opacity-50 transition-all"
              style={{ background: 'var(--brand)', color: 'var(--ink)' }}
            >
              {loading ? `⏳ Gerando... ${progress?.progress || 0}%` : "🚀 Gerar Pacote com 3 Ebooks"}
            </button>
          </form>
        </div>

        {/* Progresso em Tempo Real */}
        {progress && (
          <div className="border rounded-2xl p-6 shadow-xl space-y-4" style={{ background: 'var(--ink)', borderColor: 'var(--border)' }}>
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-bold" style={{ color: 'var(--text)' }}>
                {progress.status === "completed" ? "✅ Concluido!" : 
                 progress.status === "failed" ? "❌ Erro" : 
                 "⚡ Progresso da Geracao"}
              </h3>
              <span className="text-sm font-mono" style={{ color: 'var(--brand)' }}>{progress.progress || 0}%</span>
            </div>

            {/* Barra de progresso */}
            <div className="w-full rounded-full h-3" style={{ background: 'var(--surface)' }}>
              <div
                className="h-3 rounded-full transition-all duration-500"
                style={{ width: `${progress.progress || 0}%`, background: progress.status === "failed" ? 'var(--error)' : 'var(--brand)' }}
              />
            </div>

            {/* Mensagem atual */}
            <p className="text-sm" style={{ color: 'var(--text-dim)' }}>{progress.message}</p>

            {/* Fases */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {phaseOrder.map((phase) => {
                const p = phases[phase];
                if (!p) return null;
                return (
                  <div key={phase} className="p-3 rounded-xl border text-xs" style={{
                    background: p.status === "completed" ? 'var(--success)' : p.status === "running" ? 'var(--surface)' : 'var(--surface2)',
                    borderColor: 'var(--border)',
                    color: p.status === "completed" ? 'var(--ink)' : 'var(--text)'
                  }}>
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-bold">{phaseLabels[phase] || phase}</span>
                      <span className="font-mono">{p.progress}%</span>
                    </div>
                    <p style={{ color: p.status === "completed" ? 'var(--ink)' : 'var(--text-dim)' }}>{p.message}</p>
                  </div>
                );
              })}
            </div>

            {progress.status === "failed" && progress.error && (
              <div className="border rounded-xl p-4 text-sm" style={{ background: 'var(--error)', borderColor: 'var(--border)', color: 'var(--ink)' }}>
                {progress.error}
              </div>
            )}
          </div>
        )}

        {/* Visualizacao dos 3 Ebooks Gerados */}
        {packData && packData.pack && (
          <div className="space-y-8">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {packData.pack.map((item: any, idx: number) => (
                <div
                  key={item.id}
                  onClick={() => { setActiveEbookIndex(idx); setActiveChapterIndex(0); }}
                  className="border rounded-2xl p-5 cursor-pointer transition-all hover:scale-[1.02] shadow-xl"
                  style={{ background: 'var(--ink)', borderColor: activeEbookIndex === idx ? 'var(--brand)' : 'var(--border)' }}
                >
                  <span className="badge text-xs font-bold mb-3 inline-block border" style={{ background: 'var(--surface)', color: 'var(--brand)', borderColor: 'var(--border)' }}>
                    {item.badge}
                  </span>
                  <div className="text-center my-3">
                    <img src={item.cover_url} alt={item.title} className="w-[180px] h-[260px] object-cover rounded-xl mx-auto shadow-2xl border-2" style={{ borderColor: 'var(--border)' }} />
                  </div>
                  <h3 className="font-bold text-sm line-clamp-2 mt-2" style={{ color: 'var(--text)' }}>{item.title}</h3>
                  <p className="text-xs line-clamp-2 mt-1" style={{ color: 'var(--text-dim)' }}>{item.subtitle}</p>
                  <div className="mt-4 pt-3 border-t flex justify-between items-center text-xs" style={{ borderColor: 'var(--border)' }}>
                    <span className="font-bold" style={{ color: 'var(--brand)' }}>{item.chapters_count} Capitulos</span>
                    <span style={{ color: 'var(--text-dim)' }}>{activeEbookIndex === idx ? "📖 Lendo" : "Ler →"}</span>
                  </div>
                  <div className="mt-2 flex justify-center">
                    <AgnesCoverButton entityType="ebook" entityId={item.id} />
                  </div>
                </div>
              ))}
            </div>

            {currentEbook && (
              <div className="border rounded-2xl p-6 md:p-8 space-y-6 shadow-2xl" style={{ background: 'var(--ink)', borderColor: 'var(--border)' }}>
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center border-b pb-6 gap-4" style={{ borderColor: 'var(--border)' }}>
                  <div>
                    <span className="badge text-xs mb-1 inline-block" style={{ background: 'var(--surface)', color: 'var(--brand)' }}>{currentEbook.badge}</span>
                    <h2 className="text-2xl font-extrabold" style={{ color: 'var(--text)' }}>{currentEbook.title}</h2>
                    <p className="text-xs italic mt-0.5" style={{ color: 'var(--text-dim)' }}>"{currentEbook.subtitle}"</p>
                  </div>
                  <button 
                    onClick={() => {
                      fetch(`${API_URL}/api/v1/ebooks/${currentEbook.id}/publish`, { method: 'POST', headers: authH() })
                        .then(() => alert('Ebook enviado para o DezafiraClub!'))
                        .catch(() => alert('Erro ao enviar.'))
                    }}
                    className="px-4 py-2 text-sm font-bold rounded-lg transition-all"
                    style={{ background: 'var(--brand)', color: 'var(--ink)' }}
                  >
                    Enviar pro Clube →
                  </button>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
                  <div className="lg:col-span-1 border rounded-xl p-4" style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}>
                    <h4 className="text-xs font-extrabold uppercase tracking-wider mb-3" style={{ color: 'var(--brand)' }}>Sumario</h4>
                    <div className="space-y-1.5">
                      {currentEbook.chapters?.map((chap: any, cIdx: number) => (
                        <button
                          key={chap.num}
                          onClick={() => setActiveChapterIndex(cIdx)}
                          className="w-full text-left px-3 py-2.5 rounded-lg text-xs transition-all font-medium"
                          style={{
                            background: activeChapterIndex === cIdx ? 'var(--brand)' : 'transparent',
                            color: activeChapterIndex === cIdx ? 'var(--ink)' : 'var(--text)',
                            fontWeight: activeChapterIndex === cIdx ? 'bold' : 'normal'
                          }}
                        >
                          {chap.title}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="lg:col-span-3 border rounded-xl p-6" style={{ background: 'var(--surface2)', borderColor: 'var(--border)' }}>
                    {currentChapter && (
                      <div>
                        <div className="flex justify-between items-center border-b pb-3 mb-4" style={{ borderColor: 'var(--border)' }}>
                          <h3 className="text-lg font-bold" style={{ color: 'var(--brand)' }}>{currentChapter.title}</h3>
                          <span className="text-xs font-mono" style={{ color: 'var(--text-dim)' }}>{activeChapterIndex + 1} / {currentEbook.chapters.length}</span>
                        </div>
                        <div className="prose prose-invert text-sm leading-relaxed space-y-4 whitespace-pre-wrap" style={{ color: 'var(--text)' }}>
                          {currentChapter.content}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

      </main>
    </div>
  );
}
