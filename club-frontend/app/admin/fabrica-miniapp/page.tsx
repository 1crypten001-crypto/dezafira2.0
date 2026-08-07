"use client";

export const dynamic = 'force-dynamic';

import { useState, useEffect } from "react";
import Link from "next/link";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "https://dezafiraadm-production.up.railway.app";

export default function FabricaMiniAppPage() {
  const [prompt, setPrompt] = useState("");
  const [niche, setNiche] = useState("Tecnologia & IA");
  const [loading, setLoading] = useState(false);
  const [miniapp, setMiniapp] = useState<any>(null);
  const [agentLogs, setAgentLogs] = useState<any[]>([]);
  const [existingApps, setExistingApps] = useState<any[]>([]);
  const [loadingList, setLoadingList] = useState(true);

  useEffect(() => {
    loadExistingApps();
  }, []);

  const loadExistingApps = async () => {
    try {
      const res = await fetch(`${API_URL}/api/v1/miniapps`);
      const data = await res.json();
      setExistingApps(data.miniapps || []);
    } catch (err) {
      console.error("Erro ao listar miniapps:", err);
    } finally {
      setLoadingList(false);
    }
  };

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim()) return;

    setLoading(true);
    setMiniapp(null);
    setAgentLogs([
      { agent: "📐 Arquiteto PWA (Nexo)", message: "Mapeando requisitos e tela do aplicativo..." },
      { agent: "🎨 Diretor Visual (Agnes AI)", message: "Gerando Logo 3D 512x512 e Banner via Agnes AI..." },
      { agent: "💻 Desenvolvedor Frontend (Coder)", message: "Construindo componentes PWA instaláveis com HTML real..." },
      { agent: "🗄️ Gestor de Conteúdos (DB Chronicler)", message: "Gravando no banco PostgreSQL (sobrevive deploy)..." }
    ]);

    try {
      const res = await fetch(`${API_URL}/api/v1/miniapps/create`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt, niche })
      });
      const data = await res.json();
      if (data.success && data.miniapp) {
        setMiniapp(data.miniapp);
        if (data.miniapp.logs) {
          setAgentLogs(data.miniapp.logs);
        }
        loadExistingApps();
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (appId: string) => {
    if (!confirm("Tem certeza que deseja deletar este MiniApp?")) return;
    try {
      await fetch(`${API_URL}/api/v1/miniapps/${appId}`, { method: "DELETE" });
      loadExistingApps();
      if (miniapp?.app_id === appId) setMiniapp(null);
    } catch (err) {
      console.error("Erro ao deletar:", err);
    }
  };

  return (
    <div className="min-h-screen bg-[#060911] text-[#f8fafc]">
      <header className="border-b border-[#1e293b] bg-[#090d16]">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link href="/admin" className="text-sm text-[var(--text-dim)] hover:text-white">← Voltar ao Admin</Link>
            <span className="text-[#334155]">/</span>
            <h1 className="text-lg font-bold text-[#38bdf8]">📱 Fábrica de MiniApps (Sala de Agentes)</h1>
          </div>
          <span className="badge text-[var(--success)] text-xs font-bold">🟢 Agentes Especializados + PostgreSQL</span>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-8 space-y-8">

        {/* Lista de MiniApps Existentes */}
        {existingApps.length > 0 && (
          <div className="bg-[#090d16] border border-[#1e293b] rounded-2xl p-6 shadow-xl">
            <h2 className="text-lg font-bold text-[#f1f5f9] mb-4">📱 MiniApps Criados ({existingApps.length})</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {existingApps.map((app) => (
                <div key={app.id} className="bg-[#131c2e] border border-[#1e293b] rounded-xl p-4 hover:border-[#38bdf855] transition-all">
                  <div className="flex items-start justify-between mb-2">
                    <h3 className="text-sm font-bold text-white line-clamp-1">{app.app_name}</h3>
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${app.status === "active" ? "bg-green-500/20 text-green-400" : "bg-yellow-500/20 text-yellow-400"}`}>
                      {app.status === "active" ? "🟢 Ativo" : "🟡 Draft"}
                    </span>
                  </div>
                  <p className="text-xs text-[var(--text-dim)] mb-2">{app.niche} • {app.app_type}</p>
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] text-gray-500 font-mono">{app.id}</span>
                    <div className="flex gap-2">
                      <button onClick={() => setMiniapp(app)} className="text-[10px] text-[#38bdf8] hover:underline">Ver</button>
                      <button onClick={() => handleDelete(app.id)} className="text-[10px] text-red-400 hover:underline">Deletar</button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Painel de Criação */}
        <div className="bg-[#090d16] border border-[#1e293b] rounded-2xl p-6 shadow-xl space-y-4">
          <div>
            <h2 className="text-xl font-extrabold text-[#f1f5f9]">Criar Novo MiniApp PWA de Recorrência</h2>
            <p className="text-xs text-[var(--text-dim)]">
              Descreva a ideia do aplicativo. A Sala de Agentes criará a logo 3D com Agnes AI, a interface PWA instalável (HTML real) e o banco de dados temporizado no PostgreSQL.
            </p>
          </div>

          <form onSubmit={handleGenerate} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="md:col-span-2">
                <label className="block text-xs font-bold text-[var(--text-dim)] mb-1">PROMPT DO MINIAPP</label>
                <input
                  type="text"
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  placeholder="Ex: Calculadora de Macros e Treinos para Atletas ou Quiz Diagnóstico Financeiro 2026"
                  className="w-full bg-[#131c2e] border border-[#334155] rounded-xl px-4 py-3 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-[#38bdf8]"
                  required
                />
              </div>
              <div>
                <label className="block text-xs font-bold text-[var(--text-dim)] mb-1">NICHO DA OPERAÇÃO</label>
                <select
                  value={niche}
                  onChange={(e) => setNiche(e.target.value)}
                  className="w-full bg-[#131c2e] border border-[#334155] rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:border-[#38bdf8]"
                >
                  <option value="Tecnologia & IA">Tecnologia & IA</option>
                  <option value="Fitness & Saúde">Fitness & Saúde</option>
                  <option value="Finanças & Negócios">Finanças & Negócios</option>
                  <option value="Espiritualidade">Espiritualidade & Devocional</option>
                  <option value="Marketing Digital">Marketing Digital</option>
                </select>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-gradient-to-r from-[#38bdf8] to-[#0284c7] text-[#090d16] font-extrabold py-3 rounded-xl text-sm shadow-lg hover:brightness-110 disabled:opacity-50 transition-all"
            >
              {loading ? "⚡ Sala de Agentes Gerando o MiniApp PWA..." : "🚀 Disparar Sala de Agentes & Criar MiniApp PWA"}
            </button>
          </form>
        </div>

        {/* Sala de Agentes Trabalhando ao Vivo */}
        {agentLogs.length > 0 && (
          <div className="bg-[#090d16] border border-[#1e293b] rounded-2xl p-6 space-y-3">
            <h3 className="text-sm font-bold text-[#38bdf8] flex items-center gap-2">
              <span className="animate-pulse">🟢</span> Sala de Agentes Autônomos em Ação
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {agentLogs.map((log, idx) => (
                <div key={idx} className="bg-[#131c2e] border border-[#1e293b] p-3 rounded-xl text-xs space-y-1">
                  <strong className="text-[#f1f5f9] block">{log.agent}</strong>
                  <p className="text-[var(--text-dim)]">{log.message}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Visualização do MiniApp */}
        {miniapp && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

            {/* Moldura de Celular */}
            <div className="lg:col-span-1 flex justify-center">
              <div className="w-[320px] h-[640px] bg-[#000] border-[6px] border-[#334155] rounded-[40px] shadow-2xl p-4 flex flex-col justify-between relative overflow-hidden">
                <div className="absolute top-2 left-1/2 -translate-x-1/2 w-28 h-4 bg-[#1e293b] rounded-full z-20"></div>

                <div className="mt-4 border-b border-[#1e293b] pb-3 flex items-center gap-3">
                  {miniapp.logo_url && (
                    <img src={miniapp.logo_url} className="w-10 h-10 rounded-xl border border-[#38bdf8] object-cover shadow-md" alt="Logo" />
                  )}
                  <div>
                    <h4 className="text-xs font-bold text-white leading-tight">{miniapp.app_name}</h4>
                    <span className="text-[10px] text-[#22c55e] font-semibold">PWA Instalado</span>
                  </div>
                </div>

                {miniapp.banner_url && (
                  <div className="my-2 rounded-xl overflow-hidden border border-[#1e293b]">
                    <img src={miniapp.banner_url} className="w-full h-32 object-cover" alt="Banner" />
                  </div>
                )}

                {miniapp.pwa_html ? (
                  <div className="flex-1 bg-[#131c2e] rounded-xl overflow-hidden border border-[#1e293b]">
                    <iframe srcDoc={miniapp.pwa_html} className="w-full h-full border-0" title="Preview PWA" />
                  </div>
                ) : (
                  <div className="flex-1 bg-[#131c2e] rounded-xl p-3 space-y-2 border border-[#1e293b] overflow-y-auto text-xs">
                    <div className="bg-[#090d16] p-2.5 rounded-lg border border-[#334155]">
                      <span className="text-[10px] text-[#38bdf8] font-bold block mb-1">DIAGNÓSTICO ATIVO</span>
                      <p className="text-[11px] text-gray-200">Responda para liberar o plano personalizado.</p>
                    </div>
                    <button className="w-full text-left bg-[#090d16] hover:bg-[#1e293b] border border-[#334155] p-2 rounded-lg text-[11px] text-white font-medium">
                      ▶️ Iniciar Teste Diagnóstico
                    </button>
                  </div>
                )}

                <div className="pt-2 border-t border-[#1e293b] flex justify-around text-[10px] text-[var(--text-dim)]">
                  <span>Inicio</span>
                  <span className="text-[#38bdf8] font-bold">Ferramenta</span>
                  <span>Perfil</span>
                </div>
              </div>
            </div>

            {/* Drip Content */}
            <div className="lg:col-span-2 space-y-4">
              <div className="bg-[#090d16] border border-[#1e293b] rounded-2xl p-6 space-y-4 shadow-xl">
                <div className="flex justify-between items-center border-b border-[#1e293b] pb-3">
                  <div>
                    <span className="badge text-[var(--success)] text-xs">🗄️ Banco PostgreSQL Ativo</span>
                    <h3 className="text-lg font-bold text-[#f1f5f9] mt-1">Trilha de Liberação Recorrente (Drip Content)</h3>
                  </div>
                  <span className="text-xs text-[#38bdf8] font-bold">App ID: {miniapp.app_id || miniapp.id}</span>
                </div>

                <div className="space-y-3">
                  {miniapp.drip_contents?.map((item: any, idx: number) => (
                    <div key={idx} className="bg-[#131c2e] border border-[#1e293b] p-4 rounded-xl flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <span className="bg-[#38bdf822] text-[#38bdf8] border border-[#38bdf855] text-xs font-bold px-3 py-1.5 rounded-lg">
                          Dia {item.day}
                        </span>
                        <div>
                          <h4 className="text-sm font-bold text-white">{item.title}</h4>
                          <p className="text-xs text-[var(--text-dim)]">{item.payload?.desc || "Conteúdo liberado para o assinante."}</p>
                        </div>
                      </div>
                      <span className={`text-xs font-bold px-3 py-1 rounded-full ${item.payload?.status === "unlocked" ? "bg-green-500/20 text-green-400" : "bg-yellow-500/20 text-yellow-400"}`}>
                        {item.payload?.status === "unlocked" ? "🟢 Liberado" : "⏳ Programado"}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

          </div>
        )}

      </main>
    </div>
  );
}
