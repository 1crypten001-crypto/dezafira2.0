"use client";

import { useState, useEffect, useRef } from "react";
import Link from "next/link";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "https://dezafiraadm-production.up.railway.app";

export default function FabricaMapasPage() {
  const [title, setTitle] = useState("");
  const [niche, setNiche] = useState("Direito Constitucional");
  const [styleId, setStyleId] = useState("moderno");
  const [priceCents, setPriceCents] = useState(1990);
  const [loading, setLoading] = useState(false);
  const [mindmaps, setMindmaps] = useState<any[]>([]);
  const [loadingList, setLoadingList] = useState(true);
  const [taskId, setTaskId] = useState<string | null>(null);
  const [progress, setProgress] = useState<any>(null);
  const [selectedMap, setSelectedMap] = useState<any>(null);
  const pollRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    loadMindMaps();
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, []);

  const loadMindMaps = async () => {
    try {
      const token = typeof window !== "undefined" ? localStorage.getItem("dz_token") : "";
      const res = await fetch(`${API_URL}/api/v1/mindmaps`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      const data = await res.json();
      setMindmaps(data.mindmaps || []);
    } catch (err) {
      console.error("Erro ao listar mapas mentais:", err);
    } finally {
      setLoadingList(false);
    }
  };

  const pollStatus = (tid: string) => {
    if (pollRef.current) clearInterval(pollRef.current);
    pollRef.current = setInterval(async () => {
      try {
        const token = typeof window !== "undefined" ? localStorage.getItem("dz_token") : "";
        const res = await fetch(`${API_URL}/api/v1/pipeline/mindmap-factory/status/${tid}`, {
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        });
        const data = await res.json();
        setProgress(data);

        if (data.status === "completed" || data.status === "failed") {
          if (pollRef.current) clearInterval(pollRef.current);
          setLoading(false);
          loadMindMaps();
        }
      } catch (err) {
        console.error("Erro ao consultar status:", err);
      }
    }, 3000);
  };

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!niche.trim()) return;

    setLoading(true);
    setProgress(null);

    try {
      const token = typeof window !== "undefined" ? localStorage.getItem("dz_token") : "";
      const res = await fetch(`${API_URL}/api/v1/pipeline/run-mindmap-factory`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          title,
          niche,
          style_id: styleId,
          price_cents: priceCents,
        })
      });
      const data = await res.json();
      if (data.task_id) {
        setTaskId(data.task_id);
        pollStatus(data.task_id);
      }
    } catch (err) {
      console.error("Erro ao iniciar geracao:", err);
      setLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Tem certeza que deseja deletar este mapa mental?")) return;
    try {
      const token = typeof window !== "undefined" ? localStorage.getItem("dz_token") : "";
      await fetch(`${API_URL}/api/v1/mindmaps/${id}`, {
        method: "DELETE",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      loadMindMaps();
      if (selectedMap?.id === id) setSelectedMap(null);
    } catch (err) {
      console.error("Erro ao deletar mapa:", err);
    }
  };

  return (
    <div className="min-h-screen bg-[#060911] text-[#f8fafc]">
      <header className="border-b border-[#1e293b] bg-[#090d16] px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link href="/admin" className="text-sm text-gray-400 hover:text-white">← Voltar ao Admin</Link>
          <span className="text-[#334155]">/</span>
          <h1 className="text-lg font-bold text-[#8b5cf6]">🧠 Fábrica de Mapas Mentais</h1>
        </div>
        <span className="badge text-[var(--success)] bg-green-500/10 border border-green-500/20 px-3 py-1 rounded-full text-xs font-bold">
          🟢 Esteira Recorrente Ativa
        </span>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-8 space-y-8">
        
        {/* Painel de Criação */}
        <div className="bg-[#090d16] border border-[#1e293b] rounded-2xl p-6 shadow-xl space-y-6">
          <div>
            <h2 className="text-xl font-extrabold text-[#f1f5f9]">Criar Novo Mapa Mental Recorrente</h2>
            <p className="text-xs text-gray-400 mt-1">
              Gere mapas mentais dinâmicos com memorização guiada e quizzes de fixação para alimentar seu app de recorrência.
            </p>
          </div>

          <form onSubmit={handleGenerate} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="md:col-span-2">
                <label className="block text-xs font-bold text-gray-400 mb-1">NICHO OU TEMA PRINCIPAL</label>
                <input
                  type="text"
                  value={niche}
                  onChange={(e) => setNiche(e.target.value)}
                  placeholder="Ex: Direito Constitucional ou Estudo Bíblico"
                  className="w-full bg-[#131c2e] border border-[#334155] rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:border-[#8b5cf6]"
                  required
                />
              </div>
              <div>
                <label className="block text-xs font-bold text-gray-400 mb-1">TÍTULO (OPCIONAL)</label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="Ex: Atos Administrativos"
                  className="w-full bg-[#131c2e] border border-[#334155] rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:border-[#8b5cf6]"
                />
              </div>
              <div>
                <label className="block text-xs font-bold text-gray-400 mb-1">PREÇO DA ASSINATURA (CENTAVOS)</label>
                <input
                  type="number"
                  value={priceCents}
                  onChange={(e) => setPriceCents(Number(e.target.value))}
                  className="w-full bg-[#131c2e] border border-[#334155] rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:border-[#8b5cf6]"
                />
              </div>
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-gradient-to-r from-[#8b5cf6] to-[#6d28d9] text-white font-extrabold py-3.5 rounded-xl text-sm shadow-lg hover:brightness-110 disabled:opacity-50 transition-all"
            >
              {loading ? "⏳ Orquestrando Agentes..." : "🚀 Disparar Esteira de Criação"}
            </button>
          </form>
        </div>

        {/* Progresso de Geração */}
        {progress && (
          <div className="bg-[#090d16] border border-[#1e293b] rounded-2xl p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-md font-bold text-[#f1f5f9]">Status da Pipeline</h3>
              <span className="text-sm font-mono text-[#8b5cf6]">{progress.status === "completed" ? "100%" : progress.current_macro_stage || "Iniciando"}</span>
            </div>
            <div className="w-full bg-[#131c2e] rounded-full h-2">
              <div
                className="h-2 rounded-full bg-gradient-to-r from-[#8b5cf6] to-[#38bdf8] transition-all duration-500"
                style={{ width: progress.status === "completed" ? "100%" : "50%" }}
              />
            </div>
            <p className="text-xs text-gray-400">{progress.error || "Aguardando conclusão de escrita do grafo..."}</p>
          </div>
        )}

        {/* Lista de Mapas Mentais Criados */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="md:col-span-1 bg-[#090d16] border border-[#1e293b] rounded-2xl p-6 shadow-xl h-[600px] flex flex-col">
            <h2 className="text-lg font-bold text-[#f1f5f9] mb-4">Mapas Disponíveis ({mindmaps.length})</h2>
            <div className="flex-1 overflow-y-auto space-y-3 pr-1">
              {loadingList ? (
                <div className="text-sm text-gray-400">Carregando mapas...</div>
              ) : mindmaps.length === 0 ? (
                <div className="text-sm text-gray-400">Nenhum mapa criado ainda.</div>
              ) : (
                mindmaps.map((m) => (
                  <div
                    key={m.id}
                    onClick={() => setSelectedMap(m)}
                    className={`p-4 rounded-xl border cursor-pointer transition-all ${
                      selectedMap?.id === m.id ? "bg-[#131c2e] border-[#8b5cf6]" : "bg-[#0b0f19] border-[#1e293b] hover:border-gray-700"
                    }`}
                  >
                    <div className="flex justify-between items-start">
                      <h4 className="text-sm font-bold text-white line-clamp-1">{m.title}</h4>
                      <button
                        onClick={(e) => { e.stopPropagation(); handleDelete(m.id); }}
                        className="text-gray-500 hover:text-red-500 text-xs"
                      >
                        Deletar
                      </button>
                    </div>
                    <p className="text-xs text-[#38bdf8] mt-1">{m.niche}</p>
                    <div className="flex justify-between items-center mt-3">
                      <span className="text-[10px] px-2 py-0.5 rounded bg-green-500/10 text-green-400 border border-green-500/20 font-mono">
                        {m.status}
                      </span>
                      <a
                        href={`${API_URL}/mindmap/${m.id}`}
                        target="_blank"
                        className="text-[10px] text-gray-400 hover:underline"
                        onClick={(e) => e.stopPropagation()}
                      >
                        Abrir PWA ↗
                      </a>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Visualizador de Tópicos */}
          <div className="md:col-span-2 bg-[#090d16] border border-[#1e293b] rounded-2xl p-6 shadow-xl h-[600px] flex flex-col">
            {selectedMap ? (
              <div className="flex flex-col h-full space-y-4">
                <div className="border-b border-[#1e293b] pb-4">
                  <h2 className="text-xl font-extrabold text-[#f1f5f9]">{selectedMap.title}</h2>
                  <p className="text-xs text-gray-400 mt-1">Nicho: {selectedMap.niche} | Estilo: {selectedMap.style_id}</p>
                </div>
                <div className="flex-1 overflow-y-auto space-y-4 pr-1">
                  <h3 className="text-sm font-bold text-[#8b5cf6]">Hierarquia e Quizzes (Visualização Rápida)</h3>
                  {selectedMap.map_json ? (
                    <div className="bg-[#0b0f19] border border-[#1e293b] p-4 rounded-xl font-mono text-xs overflow-x-auto text-gray-300">
                      <pre>{JSON.stringify(JSON.parse(selectedMap.map_json), null, 2)}</pre>
                    </div>
                  ) : (
                    <div className="text-sm text-gray-400 italic">Estrutura JSON não gerada ou corrompida.</div>
                  )}
                </div>
              </div>
            ) : (
              <div className="flex-1 flex flex-col items-center justify-center text-gray-500">
                <span>🧠</span>
                <span className="text-sm mt-2">Selecione um mapa mental ao lado para ver seus ramos e estrutura.</span>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
