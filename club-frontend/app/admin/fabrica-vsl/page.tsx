"use client";

export const dynamic = 'force-dynamic';

import { useState, useEffect, useRef } from "react";
import Link from "next/link";

const API_URL = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/$/, '');

const authH = () => {
  const t = typeof window !== 'undefined' ? localStorage.getItem('dz_token') : null;
  return t ? { 'Authorization': 'Bearer '+t, 'Content-Type': 'application/json' } : { 'Content-Type': 'application/json' };
}

export default function FabricaVslPage() {
  const [activeTab, setActiveTab] = useState("gerador"); // "gerador" | "catalogo"

  // Catalogo states
  const [loading, setLoading] = useState(false);
  const [loadingList, setLoadingList] = useState(true);
  const [existingVsls, setExistingVsls] = useState<any[]>([]);

  // Form states for creating VSL (legacy)
  const [title, setTitle] = useState("");
  const [videoUrl, setVideoUrl] = useState("");
  const [nicho, setNiche] = useState("Geral");
  const [delaySeconds, setDelaySeconds] = useState(0);
  const [thumbnailUrl, setThumbnailUrl] = useState("");

  // Selected VSL states for edit & analytics
  const [selectedVsl, setSelectedVsl] = useState<any>(null);
  const [editTitle, setEditTitle] = useState("");
  const [editVideoUrl, setEditVideoUrl] = useState("");
  const [editNicho, setEditNicho] = useState("Geral");
  const [editDelay, setEditDelay] = useState(0);
  const [editThumbnail, setEditThumbnail] = useState("");
  const [editHeadlineA, setEditHeadlineA] = useState("");
  const [editHeadlineB, setEditHeadlineB] = useState("");
  const [editHeadlineC, setEditHeadlineC] = useState("");
  const [analytics, setAnalytics] = useState<any>(null);
  const [renderResult, setRenderResult] = useState<any>(null);
  const [renderBusy, setRenderBusy] = useState(false);
  // Vídeo IA (Agnes agnes-video-v2.0)
  const [agnesTask, setAgnesTask] = useState<string>("");
  const [agnesStatus, setAgnesStatus] = useState<string>("");
  const [agnesProgress, setAgnesProgress] = useState<number>(0);
  const [agnesBusy, setAgnesBusy] = useState(false);
  const [agnesVideoUrl, setAgnesVideoUrl] = useState<string>("");
  const agnesPollRef = useRef<any>(null);

  // Gerador states
  const [genTitle, setGenTitle] = useState("");
  const [genNiche, setGenNiche] = useState("");
  const [genOffer, setGenOffer] = useState("");
  const [genAudience, setGenAudience] = useState("");
  const [genCtaUrl, setGenCtaUrl] = useState("");
  const [genStep, setGenStep] = useState(1);
  const [genProgress, setGenProgress] = useState(0);
  const [generatedVsl, setGeneratedVsl] = useState<any>(null);
  const [selectedHeadline, setSelectedHeadline] = useState("");

  const progressSteps = [
    '🧠 Analisando oferta...', 
    '✍️ Gerando 3 variações de headline...', 
    '📝 Escrevendo script completo...', 
    '🎯 Finalizando VSL...'
  ];

  useEffect(() => {
    // limpa polling de vídeo IA ao desmontar
    return () => {
      if (agnesPollRef.current) {
        clearInterval(agnesPollRef.current);
        agnesPollRef.current = null;
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (activeTab === "catalogo") {
      loadExistingVsls();
    }
  }, [activeTab]);

  const loadExistingVsls = async () => {
    setLoadingList(true);
    try {
      const res = await fetch(`${API_URL}/api/v1/vsl`, { headers: authH() });
      const data = await res.json();
      setExistingVsls(data.vsls || []);
    } catch (err) {
      console.error("Erro ao listar VSLs:", err);
    } finally {
      setLoadingList(false);
    }
  };

  const handleCreateLegacy = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !videoUrl.trim()) return;

    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/v1/vsl`, {
        method: "POST",
        headers: authH(),
        body: JSON.stringify({
          title,
          video_url: videoUrl,
          nicho,
          delay_seconds: delaySeconds,
          thumbnail_url: thumbnailUrl || null
        })
      });
      const data = await res.json();
      if (data.success) {
        alert("VSL e Headlines criadas com sucesso pela IA!");
        setTitle("");
        setVideoUrl("");
        setDelaySeconds(0);
        setThumbnailUrl("");
        loadExistingVsls();
      }
    } catch (err) {
      console.error("Erro ao criar VSL:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateAI = async (e: React.FormEvent) => {
    e.preventDefault();
    setGenStep(2);
    setGenProgress(0);

    // Simulate progress steps over ~3s each (12s total) while API runs in background
    let currentStep = 0;
    const interval = setInterval(() => {
      currentStep++;
      if (currentStep < progressSteps.length) {
        setGenProgress(currentStep);
      } else {
        clearInterval(interval);
      }
    }, 3000);

    try {
      const res = await fetch(`${API_URL}/api/v1/vsl`, {
        method: "POST",
        headers: authH(),
        body: JSON.stringify({
          title: genTitle,
          niche: genNiche,
          offer_description: genOffer,
          target_audience: genAudience,
          cta_url: genCtaUrl
        })
      });
      const data = await res.json();
      
      // Wait for animation if API was faster
      clearInterval(interval);
      setGenProgress(progressSteps.length - 1);
      setTimeout(() => {
        setGeneratedVsl(data.vsl || data.video || data);
        setGenStep(3);
      }, 1000);
    } catch (err) {
      console.error("Erro na geração:", err);
      alert("Erro ao gerar VSL. Tente novamente.");
      setGenStep(1);
    }
  };

  const handleRenderVideo = async () => {
    if (!selectedVsl) return;
    setRenderBusy(true);
    setRenderResult(null);
    try {
      const res = await fetch(`${API_URL}/api/v1/vsl/${selectedVsl.id}/render-video`, {
        method: "POST",
        headers: authH(),
        body: JSON.stringify({ style_id: "moderno" }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
      setRenderResult(data);
      if (data.video_url) setEditVideoUrl(data.video_url);
    } catch (err: any) {
      console.error("Erro ao renderizar vídeo:", err);
      alert("Erro ao renderizar vídeo: " + (err.message || err));
    } finally {
      setRenderBusy(false);
    }
  };

  const stopAgnesPoll = () => {
    if (agnesPollRef.current) {
      clearInterval(agnesPollRef.current);
      agnesPollRef.current = null;
    }
  };

  const handleRenderAgnesVideo = async () => {
    if (!selectedVsl) return;
    setAgnesBusy(true);
    setAgnesStatus("iniciando");
    setAgnesProgress(0);
    setAgnesVideoUrl("");
    stopAgnesPoll();
    try {
      const res = await fetch(`${API_URL}/api/v1/vsl/${selectedVsl.id}/render-agnes-video`, {
        method: "POST",
        headers: authH(),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
      setAgnesTask(data.task_id || "");
      const poll = async () => {
        try {
          const r2 = await fetch(`${API_URL}/api/v1/vsl/${selectedVsl.id}/agnes-video`, {
            headers: authH(),
          });
          const d2 = await r2.json();
          setAgnesStatus(d2.status || "");
          setAgnesProgress(typeof d2.progress === "number" ? d2.progress : 0);
          if (d2.local_url) {
            setAgnesVideoUrl(d2.local_url);
            setEditVideoUrl(d2.local_url);
            setAgnesBusy(false);
            stopAgnesPoll();
          } else if (["completed", "succeeded", "done", "success"].includes(d2.status)) {
            // concluído sem download local? usa a URL remota
            if (d2.url) setAgnesVideoUrl(d2.url);
            setAgnesBusy(false);
            stopAgnesPoll();
          } else if (["failed", "error", "cancelled", "no_task"].includes(d2.status)) {
            setAgnesBusy(false);
            stopAgnesPoll();
            if (d2.status !== "no_task") alert("Vídeo IA falhou: " + (d2.detail || d2.status));
          }
        } catch (e) {
          console.error("poll agnes video:", e);
        }
      };
      agnesPollRef.current = setInterval(poll, 6000);
      poll();
    } catch (err: any) {
      console.error("Erro ao gerar vídeo IA:", err);
      alert("Erro ao gerar vídeo IA: " + (err.message || err));
      setAgnesBusy(false);
    }
  };

  const handleSelectVsl = async (vslId: string) => {
    stopAgnesPoll();
    setAgnesBusy(false);
    setAgnesTask("");
    setAgnesStatus("");
    setAgnesVideoUrl("");
    try {
      const res = await fetch(`${API_URL}/api/v1/vsl/${vslId}`, { headers: authH() });
      const data = await res.json();
      if (data.video) {
        setSelectedVsl(data.video);
        setEditTitle(data.video.title || "");
        setEditVideoUrl(data.video.video_url || "");
        setEditNicho(data.video.nicho || "Geral");
        setEditDelay(data.video.delay_seconds || 0);
        setEditThumbnail(data.video.thumbnail_url || "");
        setEditHeadlineA(data.video.headline_a || "");
        setEditHeadlineB(data.video.headline_b || "");
        setEditHeadlineC(data.video.headline_c || "");
        setAnalytics(data.analytics || null);
      }
    } catch (err) {
      console.error("Erro ao carregar detalhes do VSL:", err);
    }
  };

  const handleSave = async () => {
    if (!selectedVsl) return;
    const payload = {
      title: editTitle,
      video_url: editVideoUrl,
      nicho: editNicho,
      delay_seconds: editDelay,
      thumbnail_url: editThumbnail || null,
      headline_a: editHeadlineA,
      headline_b: editHeadlineB,
      headline_c: editHeadlineC
    };
    try {
      const res = await fetch(`${API_URL}/api/v1/vsl/${selectedVsl.id}`, {
        method: "PUT",
        headers: authH(),
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (data.success || data.id) {
        alert("Configurações da VSL salvas com sucesso!");
        loadExistingVsls();
        handleSelectVsl(selectedVsl.id);
      }
    } catch (err) {
      console.error("Erro ao salvar alterações da VSL:", err);
    }
  };

  const handleDelete = async (vslId: string) => {
    if (!confirm("Tem certeza que deseja excluir esta VSL permanentemente?")) return;
    try {
      await fetch(`${API_URL}/api/v1/vsl/${vslId}`, { method: "DELETE", headers: authH() });
      loadExistingVsls();
      if (selectedVsl?.id === vslId) {
        setSelectedVsl(null);
        setAnalytics(null);
      }
    } catch (err) {
      console.error("Erro ao excluir VSL:", err);
    }
  };

  return (
    <div className="min-h-screen bg-[var(--ink)] text-[var(--text)]">
      <header className="border-b border-[var(--border)] bg-[var(--bg)]">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link href="/admin" className="text-sm text-[var(--text-dim)] hover:text-[var(--text)]">← Voltar ao Admin</Link>
            <span className="text-[var(--text-dim)]">/</span>
            <h1 className="text-lg font-bold text-[var(--brand)]">🎬 Fábrica de VSLs</h1>
          </div>
        </div>
        <div className="max-w-6xl mx-auto px-4 pt-4 flex gap-4">
          <button 
            onClick={() => setActiveTab("gerador")}
            className={`pb-3 font-bold text-sm border-b-2 transition-colors ${activeTab === 'gerador' ? 'border-[var(--brand)] text-[var(--brand)]' : 'border-transparent text-[var(--text-dim)] hover:text-[var(--text)]'}`}
          >
            ✨ Gerar Nova VSL
          </button>
          <button 
            onClick={() => setActiveTab("catalogo")}
            className={`pb-3 font-bold text-sm border-b-2 transition-colors ${activeTab === 'catalogo' ? 'border-[var(--brand)] text-[var(--brand)]' : 'border-transparent text-[var(--text-dim)] hover:text-[var(--text)]'}`}
          >
            📚 Catálogo e Analytics
          </button>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-8 space-y-8">
        
        {activeTab === "gerador" && (
          <div className="bg-[var(--bg)] border border-[var(--border)] rounded-2xl p-6 shadow-xl card">
            {genStep === 1 && (
              <form onSubmit={handleGenerateAI} className="space-y-6">
                <div>
                  <h2 className="text-xl font-bold text-[var(--text)]">Criar VSL com Inteligência Artificial</h2>
                  <p className="text-sm text-[var(--text-dim)]">Preencha o briefing abaixo e a IA fará o resto.</p>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-bold text-[var(--text-dim)] mb-1">TÍTULO DA VSL</label>
                    <input type="text" value={genTitle} onChange={e=>setGenTitle(e.target.value)} required placeholder="Ex: Método Seca Barriga" className="input w-full bg-[var(--surface)] border border-[var(--border)] rounded-xl px-4 py-2.5 text-sm text-[var(--text)] focus:outline-none focus:border-[var(--brand)]" />
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-[var(--text-dim)] mb-1">NICHO</label>
                    <input type="text" value={genNiche} onChange={e=>setGenNiche(e.target.value)} required placeholder="Ex: Emagrecimento" className="input w-full bg-[var(--surface)] border border-[var(--border)] rounded-xl px-4 py-2.5 text-sm text-[var(--text)] focus:outline-none focus:border-[var(--brand)]" />
                  </div>
                  <div className="md:col-span-2">
                    <label className="block text-xs font-bold text-[var(--text-dim)] mb-1">OFERTA (DESCRIÇÃO)</label>
                    <textarea value={genOffer} onChange={e=>setGenOffer(e.target.value)} required placeholder="Descreva sua oferta em detalhes..." rows={3} className="input w-full bg-[var(--surface)] border border-[var(--border)] rounded-xl px-4 py-2.5 text-sm text-[var(--text)] focus:outline-none focus:border-[var(--brand)]" />
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-[var(--text-dim)] mb-1">PÚBLICO-ALVO</label>
                    <input type="text" value={genAudience} onChange={e=>setGenAudience(e.target.value)} required placeholder="Ex: Mulheres de 30-50 anos" className="input w-full bg-[var(--surface)] border border-[var(--border)] rounded-xl px-4 py-2.5 text-sm text-[var(--text)] focus:outline-none focus:border-[var(--brand)]" />
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-[var(--text-dim)] mb-1">URL DO CTA (BOTÃO)</label>
                    <input type="url" value={genCtaUrl} onChange={e=>setGenCtaUrl(e.target.value)} placeholder="Ex: https://checkout.com/..." className="input w-full bg-[var(--surface)] border border-[var(--border)] rounded-xl px-4 py-2.5 text-sm text-[var(--text)] focus:outline-none focus:border-[var(--brand)]" />
                  </div>
                </div>

                <div className="flex justify-end pt-4">
                  <button type="submit" className="btn-primary bg-[var(--brand)] text-[var(--ink)] font-bold px-8 py-3 rounded-xl text-sm hover:brightness-110 transition-all">
                    Gerar VSL com IA
                  </button>
                </div>
              </form>
            )}

            {genStep === 2 && (
              <div className="flex flex-col items-center justify-center py-20 space-y-6">
                <div className="w-16 h-16 rounded-full border-4 border-[var(--surface)] border-t-[var(--brand)] animate-spin"></div>
                <div className="text-center">
                  <h3 className="text-lg font-bold text-[var(--text)] mb-4">Processando...</h3>
                  <div className="space-y-3 text-left w-80">
                    {progressSteps.map((step, idx) => (
                      <div key={idx} className={`flex items-center gap-3 text-sm transition-opacity duration-500 ${idx <= genProgress ? 'opacity-100 text-[var(--text)]' : 'opacity-30 text-[var(--text-dim)]'}`}>
                        <span>{idx < genProgress ? '✅' : (idx === genProgress ? '🔄' : '⏳')}</span>
                        {step}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {genStep === 3 && generatedVsl && (
              <div className="space-y-6">
                <h2 className="text-xl font-bold text-[var(--text)]">Escolha a Melhor Headline</h2>
                <p className="text-sm text-[var(--text-dim)]">Nossa IA criou 3 opções baseadas na sua oferta.</p>
                <div className="grid grid-cols-1 gap-4">
                  {[
                    { key: 'A', text: generatedVsl.headline_a || "Opção A não gerada" },
                    { key: 'B', text: generatedVsl.headline_b || "Opção B não gerada" },
                    { key: 'C', text: generatedVsl.headline_c || "Opção C não gerada" },
                  ].map(h => (
                    <div 
                      key={h.key} 
                      onClick={() => setSelectedHeadline(h.text)}
                      className={`p-4 rounded-xl border cursor-pointer transition-all ${selectedHeadline === h.text ? 'border-[var(--brand)] bg-[var(--brand)]/10' : 'border-[var(--border)] bg-[var(--surface)] hover:border-[var(--brand)]/50'}`}
                    >
                      <span className="text-[var(--brand)] font-bold mr-2">Opção {h.key}:</span>
                      <span className="text-sm">{h.text}</span>
                    </div>
                  ))}
                </div>
                <div className="flex justify-end pt-4">
                  <button 
                    onClick={() => setGenStep(4)}
                    disabled={!selectedHeadline}
                    className="btn-primary bg-[var(--brand)] text-[var(--ink)] font-bold px-8 py-3 rounded-xl text-sm disabled:opacity-50"
                  >
                    Avançar para o Script →
                  </button>
                </div>
              </div>
            )}

            {genStep === 4 && generatedVsl && (
              <div className="space-y-6">
                <h2 className="text-xl font-bold text-[var(--text)]">Seu Script de VSL</h2>
                <div className="bg-[var(--surface)] border border-[var(--border)] rounded-xl p-6 h-96 overflow-y-auto whitespace-pre-wrap text-sm leading-relaxed">
                  {generatedVsl.script || "Script completo será exibido aqui."}
                </div>
                <div className="flex justify-between pt-4">
                  <button onClick={() => setGenStep(3)} className="text-[var(--text-dim)] hover:text-[var(--text)]">← Voltar</button>
                  <button onClick={() => setGenStep(5)} className="btn-primary bg-[var(--brand)] text-[var(--ink)] font-bold px-8 py-3 rounded-xl text-sm">
                    Publicar VSL
                  </button>
                </div>
              </div>
            )}

            {genStep === 5 && (
              <div className="flex flex-col items-center justify-center py-12 text-center space-y-6">
                <div className="w-20 h-20 bg-green-500/20 text-green-400 rounded-full flex items-center justify-center text-4xl mb-4 border border-green-500/30">
                  🎉
                </div>
                <h2 className="text-2xl font-bold text-[var(--text)]">VSL Publicada com Sucesso!</h2>
                <p className="text-[var(--text-dim)] max-w-md">Sua VSL já está disponível no catálogo e pronta para rodar.</p>
                <div className="flex gap-4 pt-4">
                  <button onClick={() => {
                    setGenStep(1);
                    setGenTitle("");
                    setGenNiche("");
                    setGenOffer("");
                    setGenAudience("");
                    setGenCtaUrl("");
                    setGeneratedVsl(null);
                    setSelectedHeadline("");
                  }} className="btn-secondary border border-[var(--border)] text-[var(--text)] px-6 py-2 rounded-xl text-sm hover:bg-[var(--surface)]">
                    Criar Outra
                  </button>
                  <button onClick={() => setActiveTab("catalogo")} className="btn-primary bg-[var(--brand)] text-[var(--ink)] font-bold px-6 py-2 rounded-xl text-sm">
                    Ver no Catálogo →
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === "catalogo" && (
          <div className="space-y-8">
            <div className="bg-[var(--bg)] border border-[var(--border)] rounded-2xl p-6 shadow-xl card">
              <h2 className="text-lg font-bold text-[var(--text)] mb-4">🎬 Suas VSLs Cadastradas</h2>
              {loadingList ? (
                <p className="text-xs text-[var(--text-dim)]">Carregando lista...</p>
              ) : existingVsls.length === 0 ? (
                <p className="text-xs text-[var(--text-dim)]">Nenhuma VSL cadastrada.</p>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {existingVsls.map((vsl) => (
                    <div key={vsl.id} className="bg-[var(--surface)] border border-[var(--border)] rounded-xl p-4 hover:border-[var(--brand)] transition-all flex flex-col justify-between">
                      <div>
                        <h3 className="text-sm font-bold text-white line-clamp-1 mb-1">{vsl.title}</h3>
                        <p className="text-xs text-[var(--text-dim)] mb-1">Nicho: <span className="text-[var(--text)] font-semibold">{vsl.nicho}</span></p>
                        <p className="text-xs text-[var(--text-dim)] mb-2">Delay: <span className="text-[var(--brand)] font-mono">{vsl.delay_seconds}s</span></p>
                        <div className="text-[11px] text-gray-500 truncate font-mono bg-[var(--ink)] p-1.5 rounded border border-[var(--border)] mb-3">
                          {vsl.video_url}
                        </div>
                      </div>
                      <div className="flex items-center justify-between border-t border-[var(--border)] pt-2">
                        <span className="text-[9px] text-[var(--text-dim)] font-mono">{vsl.id}</span>
                        <div className="flex gap-2">
                          <button onClick={() => handleSelectVsl(vsl.id)} className="text-xs text-[var(--brand)] font-semibold hover:underline">Configurar & Métricas</button>
                          <button onClick={() => handleDelete(vsl.id)} className="text-xs text-red-400 hover:underline">Excluir</button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Cadastro de nova VSL (Legacy) */}
            <div className="bg-[var(--bg)] border border-[var(--border)] rounded-2xl p-6 shadow-xl space-y-4 card">
              <div>
                <h2 className="text-lg font-bold text-[var(--text)]">🚀 Cadastro Manual (Avançado)</h2>
                <p className="text-xs text-[var(--text-dim)]">Insira a URL do arquivo de vídeo (.mp4) se já tiver uma VSL pronta.</p>
              </div>
              <form onSubmit={handleCreateLegacy} className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-[var(--text-dim)] mb-1">TÍTULO</label>
                  <input type="text" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Título" className="w-full bg-[var(--surface)] border border-[var(--border)] rounded-xl px-4 py-2.5 text-sm text-[var(--text)] focus:outline-none focus:border-[var(--brand)]" required />
                </div>
                <div>
                  <label className="block text-xs font-bold text-[var(--text-dim)] mb-1">URL (.MP4)</label>
                  <input type="url" value={videoUrl} onChange={(e) => setVideoUrl(e.target.value)} placeholder="URL do vídeo" className="w-full bg-[var(--surface)] border border-[var(--border)] rounded-xl px-4 py-2.5 text-sm text-[var(--text)] focus:outline-none focus:border-[var(--brand)]" required />
                </div>
                <div>
                  <label className="block text-xs font-bold text-[var(--text-dim)] mb-1">NICHO</label>
                  <select value={nicho} onChange={(e) => setNiche(e.target.value)} className="w-full bg-[var(--surface)] border border-[var(--border)] rounded-xl px-4 py-2.5 text-sm text-[var(--text)] focus:outline-none focus:border-[var(--brand)]">
                    <option value="Geral">Geral</option>
                    <option value="Beleza & Estética">Beleza & Estética</option>
                    <option value="Gastronomia">Gastronomia / Restaurante</option>
                    <option value="Finanças">Finanças / Negócios</option>
                    <option value="Fitness & Saúde">Fitness & Saúde</option>
                    <option value="Espiritualidade">Espiritualidade</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-bold text-[var(--text-dim)] mb-1">DELAY (SEGUNDOS)</label>
                  <input type="number" value={delaySeconds} onChange={(e) => setDelaySeconds(parseInt(e.target.value) || 0)} className="w-full bg-[var(--surface)] border border-[var(--border)] rounded-xl px-4 py-2.5 text-sm text-[var(--text)] focus:outline-none focus:border-[var(--brand)]" min="0" />
                </div>
                <div className="md:col-span-2">
                  <label className="block text-xs font-bold text-[var(--text-dim)] mb-1">THUMBNAIL (OPCIONAL)</label>
                  <input type="text" value={thumbnailUrl} onChange={(e) => setThumbnailUrl(e.target.value)} className="w-full bg-[var(--surface)] border border-[var(--border)] rounded-xl px-4 py-2.5 text-sm text-[var(--text)] focus:outline-none focus:border-[var(--brand)]" />
                </div>
                <div className="md:col-span-2 flex justify-end">
                  <button type="submit" disabled={loading} className="btn-primary bg-[var(--brand)] text-[var(--ink)] font-bold px-8 py-3 rounded-xl text-sm disabled:opacity-50">
                    {loading ? "Processando..." : "Cadastrar Manualmente"}
                  </button>
                </div>
              </form>
            </div>

            {selectedVsl && (
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
                
                <div className="lg:col-span-7 bg-[var(--bg)] border border-[var(--border)] rounded-2xl p-6 shadow-xl space-y-6 card">
                  <div className="border-b border-[var(--border)] pb-3 flex justify-between items-center">
                    <h3 className="text-lg font-bold text-[var(--text)]">Configurações da VSL</h3>
                    <button onClick={handleSave} className="bg-green-600 hover:bg-green-700 text-white font-bold px-4 py-2 rounded-xl text-xs">
                      💾 Salvar Configurações
                    </button>
                  </div>
                  <div className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-xs text-[var(--text-dim)] mb-1">Título da VSL</label>
                        <input type="text" value={editTitle} onChange={(e) => setEditTitle(e.target.value)} className="w-full bg-[var(--surface)] border border-[var(--border)] rounded-lg px-3 py-2 text-sm text-[var(--text)] focus:outline-none focus:border-[var(--brand)]" />
                      </div>
                      <div>
                        <label className="block text-xs text-[var(--text-dim)] mb-1">Nicho</label>
                        <input type="text" value={editNicho} onChange={(e) => setEditNicho(e.target.value)} className="w-full bg-[var(--surface)] border border-[var(--border)] rounded-lg px-3 py-2 text-sm text-[var(--text)] focus:outline-none focus:border-[var(--brand)]" />
                      </div>
                    </div>
                    <div>
                      <label className="block text-xs text-[var(--text-dim)] mb-1">URL do Vídeo (.mp4)</label>
                      <input type="text" value={editVideoUrl} onChange={(e) => setEditVideoUrl(e.target.value)} className="w-full bg-[var(--surface)] border border-[var(--border)] rounded-lg px-3 py-2 text-sm text-[var(--text)] focus:outline-none focus:border-[var(--brand)]" />
                    </div>
                    <div>
                      <label className="block text-xs text-[var(--text-dim)] mb-1">🎬 Vídeo gerado (cenas Agnes + narração TTS)</label>
                      <div className="flex items-center gap-2 flex-wrap">
                        <button
                          onClick={handleRenderVideo}
                          disabled={renderBusy || !(selectedVsl.script)}
                          className="bg-purple-600 hover:bg-purple-700 disabled:opacity-40 text-white font-bold px-4 py-2 rounded-xl text-xs"
                        >
                          {renderBusy ? "⏳ Renderizando (cenas + áudio)…" : "🎬 Renderizar vídeo (TTS)"}
                        </button>
                        {!(selectedVsl.script) && (
                          <span className="text-[10px] text-[var(--text-dim)]">Sem script — gere a VSL pela IA primeiro</span>
                        )}
                      </div>
                      {renderResult?.video_url && (
                        <div className="mt-3">
                          {/* eslint-disable-next-line @next/next/no-img-element */}
                          <video src={`${API_URL}${renderResult.video_url}`} controls className="w-full rounded-xl border border-[var(--border)]" />
                          <p className="text-[10px] text-[var(--text-dim)] mt-1">
                            {renderResult.scenes?.length || 0} cenas geradas · áudio TTS pt-BR · salvo em {renderResult.video_url}
                          </p>
                        </div>
                      )}
                      {renderResult && !renderResult.success && (
                        <p className="text-[10px] text-red-400 mt-1">Erros: {(renderResult.errors || []).join("; ")}</p>
                      )}
                    </div>
                    <div>
                      <label className="block text-xs text-[var(--text-dim)] mb-1">🤖 Vídeo IA (Agnes agnes-video-v2.0)</label>
                      <div className="flex items-center gap-2 flex-wrap">
                        <button
                          onClick={handleRenderAgnesVideo}
                          disabled={agnesBusy || !(selectedVsl.thumbnail_url || selectedVsl.video_url)}
                          className="bg-[var(--brand)] hover:opacity-90 disabled:opacity-40 text-white font-bold px-4 py-2 rounded-xl text-xs"
                        >
                          {agnesBusy ? "⏳ Gerando vídeo IA…" : "🎬 Gerar vídeo IA (Agnes)"}
                        </button>
                        <span className="text-[10px] text-[var(--text-dim)]">image-to-video a partir da thumbnail · ~1-2 min</span>
                      </div>
                      {agnesBusy && (
                        <div className="mt-3">
                          <div className="w-full h-2 rounded-full bg-[var(--surface)] border border-[var(--border)] overflow-hidden">
                            <div
                              className="h-full bg-[var(--brand)] transition-all"
                              style={{ width: `${Math.max(agnesProgress, 4)}%` }}
                            />
                          </div>
                          <p className="text-[10px] text-[var(--text-dim)] mt-1">
                            {agnesStatus === "in_progress" ? `Renderizando… ${agnesProgress}%` : agnesStatus === "queued" ? "Na fila da Agnes…" : "Enviando para a Agnes…"}
                          </p>
                        </div>
                      )}
                      {agnesVideoUrl && (
                        <div className="mt-3">
                          <video src={agnesVideoUrl.startsWith("http") ? agnesVideoUrl : `${API_URL}${agnesVideoUrl}`} controls autoPlay muted loop className="w-full rounded-xl border border-[var(--border)]" />
                          <p className="text-[10px] text-[var(--text-dim)] mt-1">Vídeo IA Agnes gerado · salvo em {agnesVideoUrl}</p>
                        </div>
                      )}
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-xs text-[var(--text-dim)] mb-1">Delay (Segundos)</label>
                        <input type="number" value={editDelay} onChange={(e) => setEditDelay(parseInt(e.target.value) || 0)} className="w-full bg-[var(--surface)] border border-[var(--border)] rounded-lg px-3 py-2 text-sm text-[var(--text)] focus:outline-none focus:border-[var(--brand)]" />
                      </div>
                      <div>
                        <label className="block text-xs text-[var(--text-dim)] mb-1">Thumb</label>
                        <input type="text" value={editThumbnail} onChange={(e) => setEditThumbnail(e.target.value)} className="w-full bg-[var(--surface)] border border-[var(--border)] rounded-lg px-3 py-2 text-sm text-[var(--text)] focus:outline-none focus:border-[var(--brand)]" />
                      </div>
                    </div>
                  </div>
                  <div className="space-y-4 pt-4 border-t border-[var(--border)]">
                    <h4 className="text-xs font-bold text-[var(--brand)] uppercase tracking-wider">Variações de Headlines A/B/C</h4>
                    <div className="space-y-3">
                      <div>
                        <label className="block text-[11px] text-[var(--text-dim)] mb-1">Headline A</label>
                        <input type="text" value={editHeadlineA} onChange={(e) => setEditHeadlineA(e.target.value)} className="w-full bg-[var(--surface)] border border-[var(--border)] rounded-lg px-3 py-2 text-xs text-[var(--text)] focus:outline-none focus:border-[var(--brand)]" />
                      </div>
                      <div>
                        <label className="block text-[11px] text-[var(--text-dim)] mb-1">Headline B</label>
                        <input type="text" value={editHeadlineB} onChange={(e) => setEditHeadlineB(e.target.value)} className="w-full bg-[var(--surface)] border border-[var(--border)] rounded-lg px-3 py-2 text-xs text-[var(--text)] focus:outline-none focus:border-[var(--brand)]" />
                      </div>
                      <div>
                        <label className="block text-[11px] text-[var(--text-dim)] mb-1">Headline C</label>
                        <input type="text" value={editHeadlineC} onChange={(e) => setEditHeadlineC(e.target.value)} className="w-full bg-[var(--surface)] border border-[var(--border)] rounded-lg px-3 py-2 text-xs text-[var(--text)] focus:outline-none focus:border-[var(--brand)]" />
                      </div>
                    </div>
                  </div>
                </div>

                <div className="lg:col-span-5 bg-[var(--bg)] border border-[var(--border)] rounded-2xl p-6 shadow-xl space-y-6 card">
                  <h3 className="text-md font-bold text-[var(--text)] border-b border-[var(--border)] pb-3">📈 Métricas e Desempenho</h3>
                  
                  {analytics ? (
                    <div className="space-y-6">
                      <div className="grid grid-cols-3 gap-2 text-center">
                        <div className="bg-[var(--surface)] p-2.5 rounded-xl border border-[var(--border)]">
                          <span className="block text-[10px] text-[var(--text-dim)] uppercase">Plays</span>
                          <span className="text-md font-bold text-[var(--text)]">{analytics.total_plays}</span>
                        </div>
                        <div className="bg-[var(--surface)] p-2.5 rounded-xl border border-[var(--border)]">
                          <span className="block text-[10px] text-[var(--text-dim)] uppercase">Vendas</span>
                          <span className="text-md font-bold text-green-400">{analytics.conversions}</span>
                        </div>
                        <div className="bg-[var(--surface)] p-2.5 rounded-xl border border-[var(--border)]">
                          <span className="block text-[10px] text-[var(--text-dim)] uppercase">CTR</span>
                          <span className="text-md font-bold text-[var(--brand)]">{analytics.ctr}%</span>
                        </div>
                      </div>

                      <div className="space-y-2 pt-2 border-t border-[var(--border)]">
                        <h4 className="text-xs font-bold text-[var(--text-dim)] uppercase mb-2">Desempenho de Headlines (A/B/C)</h4>
                        <div className="space-y-2.5 text-xs">
                          {["A", "B", "C"].map((variant) => {
                            const hData = analytics.headline_performance ? analytics.headline_performance[variant] : null;
                            if (!hData) return null;
                            return (
                              <div key={variant} className="bg-[var(--surface)] border border-[var(--border)] rounded-lg p-2.5 flex items-center justify-between">
                                <div>
                                  <span className="font-bold text-[var(--brand)] mr-2">Variação {variant}</span>
                                  <span className="text-[var(--text-dim)]">({hData.plays} visitas)</span>
                                </div>
                                <div className="text-right">
                                  <span className="block font-bold text-[var(--text)]">{hData.conversions} vendas</span>
                                  <span className="text-[10px] text-[var(--text-dim)]">CTR: {hData.ctr}%</span>
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    </div>
                  ) : (
                    <p className="text-xs text-[var(--text-dim)]">Sem dados de acesso ainda para esta VSL.</p>
                  )}
                </div>

              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
