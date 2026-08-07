"use client";

export const dynamic = 'force-dynamic';

import { useState, useEffect, useRef } from "react";
import Link from "next/link";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "https://dezafiraadm-production.up.railway.app";

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
      const token = typeof window !== "undefined" ? localStorage.getItem("token") : "";
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
    <div className="min-h-screen bg-[#060911] text-[#f8fafc]">
      <header className="border-b border-[#1e293b] bg-[#090d16]">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link href="/admin" className="text-sm text-[var(--text-dim)] hover:text-white">← Voltar ao Admin</Link>
            <span className="text-[#334155]">/</span>
            <h1 className="text-lg font-bold text-[#8b5cf6]">📗 Fábrica de Ebooks (Pacote Triplo)</h1>
          </div>
          <span className="badge text-[var(--success)] text-xs font-bold">🟢 Agentes Especializados</span>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-8 space-y-8">

        {/* Lista de Ebooks Existentes */}
        {existingBooks.length > 0 && (
          <div className="bg-[#090d16] border border-[#1e293b] rounded-2xl p-6 shadow-xl">
            <h2 className="text-lg font-bold text-[#f1f5f9] mb-4">📚 Ebooks Criados ({existingBooks.length})</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {existingBooks.map((book) => (
                <div key={book.id} className="bg-[#131c2e] border border-[#1e293b] rounded-xl p-4 hover:border-[#8b5cf655] transition-all">
                  <div className="flex items-start justify-between mb-2">
                    <h3 className="text-sm font-bold text-white line-clamp-1">{book.title}</h3>
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${book.status === "published" ? "bg-green-500/20 text-green-400" : "bg-yellow-500/20 text-yellow-400"}`}>
                      {book.status === "published" ? "🟢 Publicado" : "🟡 Rascunho"}
                    </span>
                  </div>
                  <p className="text-xs text-[var(--text-dim)] mb-1">{book.topic}</p>
                  <p className="text-xs text-gray-400">{book.total_words || 0} palavras</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Painel de Disparo */}
        <div className="bg-[#090d16] border border-[#1e293b] rounded-2xl p-6 shadow-xl space-y-4">
          <div>
            <h2 className="text-xl font-extrabold text-[#f1f5f9]">Gerar Pacote de 3 Ebooks</h2>
            <p className="text-xs text-[var(--text-dim)]">
              A geracao e <strong>assincrona</strong> — voce pode acompanhar o progresso abaixo. 
              Total: ~18 capitulos via LLM + 3 capas. Tempo estimado: 10-15 minutos.
            </p>
          </div>

          <form onSubmit={handleGeneratePack} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="md:col-span-2">
                <label className="block text-xs font-bold text-[var(--text-dim)] mb-1">TITULO OU TEMA</label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="Ex: Guia Definitivo de Negocios Digitais com IA"
                  className="w-full bg-[#131c2e] border border-[#334155] rounded-xl px-4 py-3 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-[#8b5cf6]"
                  required
                />
              </div>
              <div>
                <label className="block text-xs font-bold text-[var(--text-dim)] mb-1">NICHO</label>
                <select
                  value={niche}
                  onChange={(e) => setNiche(e.target.value)}
                  className="w-full bg-[#131c2e] border border-[#334155] rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:border-[#8b5cf6]"
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
              className="w-full bg-gradient-to-r from-[#8b5cf6] to-[#6d28d9] text-white font-extrabold py-3.5 rounded-xl text-sm shadow-lg hover:brightness-110 disabled:opacity-50 transition-all"
            >
              {loading ? `⏳ Gerando... ${progress?.progress || 0}%` : "🚀 Gerar Pacote com 3 Ebooks"}
            </button>
          </form>
        </div>

        {/* Progresso em Tempo Real */}
        {progress && (
          <div className="bg-[#090d16] border border-[#1e293b] rounded-2xl p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-bold text-[#f1f5f9]">
                {progress.status === "completed" ? "✅ Concluido!" : 
                 progress.status === "failed" ? "❌ Erro" : 
                 "⚡ Progresso da Geracao"}
              </h3>
              <span className="text-sm font-mono text-[#8b5cf6]">{progress.progress || 0}%</span>
            </div>

            {/* Barra de progresso */}
            <div className="w-full bg-[#131c2e] rounded-full h-3">
              <div
                className={`h-3 rounded-full transition-all duration-500 ${
                  progress.status === "failed" ? "bg-red-500" : "bg-gradient-to-r from-[#8b5cf6] to-[#38bdf8]"
                }`}
                style={{ width: `${progress.progress || 0}%` }}
              />
            </div>

            {/* Mensagem atual */}
            <p className="text-sm text-[var(--text-dim)]">{progress.message}</p>

            {/* Fases */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {phaseOrder.map((phase) => {
                const p = phases[phase];
                if (!p) return null;
                return (
                  <div key={phase} className={`p-3 rounded-xl border text-xs ${
                    p.status === "completed" ? "bg-green-500/10 border-green-500/30" :
                    p.status === "running" ? "bg-[#38bdf8]/10 border-[#38bdf8]/30" :
                    "bg-[#131c2e] border-[#1e293b]"
                  }`}>
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-bold text-white">{phaseLabels[phase] || phase}</span>
                      <span className={`font-mono ${
                        p.status === "completed" ? "text-green-400" :
                        p.status === "running" ? "text-[#38bdf8]" : "text-gray-500"
                      }`}>{p.progress}%</span>
                    </div>
                    <p className="text-[var(--text-dim)]">{p.message}</p>
                  </div>
                );
              })}
            </div>

            {progress.status === "failed" && progress.error && (
              <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 text-sm text-red-400">
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
                  className={`bg-[#090d16] border rounded-2xl p-5 cursor-pointer transition-all hover:scale-[1.02] shadow-xl ${
                    activeEbookIndex === idx ? "border-[#8b5cf6] ring-2 ring-[#8b5cf644]" : "border-[#1e293b]"
                  }`}
                >
                  <span className="badge text-xs font-bold mb-3 inline-block bg-[#8b5cf622] text-[#c084fc] border border-[#8b5cf655]">
                    {item.badge}
                  </span>
                  <div className="text-center my-3">
                    <img src={item.cover_url} alt={item.title} className="w-[180px] h-[260px] object-cover rounded-xl mx-auto shadow-2xl border-2 border-[#8b5cf655]" />
                  </div>
                  <h3 className="font-bold text-sm text-[#f1f5f9] line-clamp-2 mt-2">{item.title}</h3>
                  <p className="text-xs text-[var(--text-dim)] line-clamp-2 mt-1">{item.subtitle}</p>
                  <div className="mt-4 pt-3 border-t border-[#1e293b] flex justify-between items-center text-xs">
                    <span className="text-[#8b5cf6] font-bold">{item.chapters_count} Capitulos</span>
                    <span className="text-gray-400">{activeEbookIndex === idx ? "📖 Lendo" : "Ler →"}</span>
                  </div>
                </div>
              ))}
            </div>

            {currentEbook && (
              <div className="bg-[#090d16] border border-[#8b5cf655] rounded-2xl p-6 md:p-8 space-y-6 shadow-2xl">
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center border-b border-[#1e293b] pb-6 gap-4">
                  <div>
                    <span className="badge text-xs bg-[#8b5cf622] text-[#c084fc] mb-1 inline-block">{currentEbook.badge}</span>
                    <h2 className="text-2xl font-extrabold text-[#f1f5f9]">{currentEbook.title}</h2>
                    <p className="text-xs text-gray-400 italic mt-0.5">"{currentEbook.subtitle}"</p>
                  </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
                  <div className="lg:col-span-1 bg-[#131c2e] border border-[#1e293b] rounded-xl p-4">
                    <h4 className="text-xs font-extrabold text-[#c084fc] uppercase tracking-wider mb-3">Sumario</h4>
                    <div className="space-y-1.5">
                      {currentEbook.chapters?.map((chap: any, cIdx: number) => (
                        <button
                          key={chap.num}
                          onClick={() => setActiveChapterIndex(cIdx)}
                          className={`w-full text-left px-3 py-2.5 rounded-lg text-xs transition-all font-medium ${
                            activeChapterIndex === cIdx ? "bg-[#8b5cf6] text-white font-bold shadow-md" : "text-gray-300 hover:bg-[#1e293b] hover:text-white"
                          }`}
                        >
                          {chap.title}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="lg:col-span-3 bg-[#0b1120] border border-[#1e293b] rounded-xl p-6">
                    {currentChapter && (
                      <div>
                        <div className="flex justify-between items-center border-b border-[#1e293b] pb-3 mb-4">
                          <h3 className="text-lg font-bold text-[#38bdf8]">{currentChapter.title}</h3>
                          <span className="text-xs text-gray-400 font-mono">{activeChapterIndex + 1} / {currentEbook.chapters.length}</span>
                        </div>
                        <div className="prose prose-invert text-sm leading-relaxed text-gray-200 space-y-4 whitespace-pre-wrap">
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
