"use client";

export const dynamic = 'force-dynamic';

import { useState, useEffect } from "react";
import Link from "next/link";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Helper functions for HSL <-> Hex conversions
function hslToHex(hslStr: string): string {
  if (!hslStr) return "#38bdf8";
  try {
    const parts = hslStr.split(",");
    if (parts.length < 3) return "#38bdf8";
    let h = parseInt(parts[0]);
    let s = parseInt(parts[1].replace("%", "").trim());
    let l = parseInt(parts[2].replace("%", "").trim());
    s /= 100;
    l /= 100;

    const k = (n: number) => (n + h / 30) % 12;
    const a = s * Math.min(l, 1 - l);
    const f = (n: number) => {
      const kVal = k(n);
      const color = l - a * Math.max(Math.min(kVal - 3, 9 - kVal, 1), -1);
      return Math.round(255 * color).toString(16).padStart(2, "0");
    };
    return `#${f(0)}${f(8)}${f(4)}`;
  } catch (e) {
    return "#38bdf8";
  }
}

function hexToHsl(hex: string): string {
  try {
    let r = parseInt(hex.slice(1, 3), 16) / 255;
    let g = parseInt(hex.slice(3, 5), 16) / 255;
    let b = parseInt(hex.slice(5, 7), 16) / 255;

    let max = Math.max(r, g, b), min = Math.min(r, g, b);
    let h = 0, s = 0, l = (max + min) / 2;

    if (max !== min) {
      let d = max - min;
      s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
      switch (max) {
        case r: h = (g - b) / d + (g < b ? 6 : 0); break;
        case g: h = (b - r) / d + 2; break;
        case b: h = (r - g) / d + 4; break;
      }
      h /= 6;
    }
    return `${Math.round(h * 360)}, ${Math.round(s * 100)}%, ${Math.round(l * 100)}%`;
  } catch (e) {
    return "220, 80%, 50%";
  }
}

export default function FabricaBioSitesPage() {
  const [prompt, setPrompt] = useState("");
  const [niche, setNiche] = useState("Geral");
  const [loading, setLoading] = useState(false);
  const [existingSites, setExistingSites] = useState<any[]>([]);
  const [loadingList, setLoadingList] = useState(true);
  
  // Selected site for editing & preview
  const [selectedSite, setSelectedSite] = useState<any>(null);
  const [previewKey, setPreviewKey] = useState(0);

  // Pipeline visual feedback state
  const [pipelineStep, setPipelineStep] = useState(0);
  const [pipelineVisible, setPipelineVisible] = useState(false);

  // Edit form state
  const [editName, setEditName] = useState("");
  const [editDescription, setEditDescription] = useState("");
  const [editProfilePic, setEditProfilePic] = useState("");
  const [editPixelFb, setEditPixelFb] = useState("");
  const [editGoogleGa, setEditGoogleGa] = useState("");
  const [editTemplate, setEditTemplate] = useState("minimalist_glass");
  const [editAsaasId, setEditAsaasId] = useState("");
  const [editSubStatus, setEditSubStatus] = useState("paid");
  
  const [editPrimary, setEditPrimary] = useState("#38bdf8");
  const [editAccent, setEditAccent] = useState("#ea580c");
  const [editBg, setEditBg] = useState("#060911");
  const [editText, setEditText] = useState("#f8fafc");

  const [editLinks, setEditLinks] = useState<any[]>([]);

  useEffect(() => {
    loadExistingSites();
  }, []);

  const loadExistingSites = async () => {
    try {
      const res = await fetch(`${API_URL}/api/v1/biosites`);
      const data = await res.json();
      setExistingSites(data.biosites || []);
    } catch (err) {
      console.error("Erro ao listar bio sites:", err);
    } finally {
      setLoadingList(false);
    }
  };

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim()) return;

    setLoading(true);
    setPipelineVisible(true);
    setPipelineStep(1);

    try {
      const res = await fetch(`${API_URL}/api/v1/biosites/create`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt, niche })
      });
      const data = await res.json();
      if (data.success) {
        // Animate the pipeline simulation steps
        setTimeout(() => setPipelineStep(2), 850);
        setTimeout(() => setPipelineStep(3), 1700);
        setTimeout(() => setPipelineStep(4), 2550);
        setTimeout(() => {
          setPipelineStep(5);
          setTimeout(() => {
            setPipelineVisible(false);
            loadExistingSites();
          }, 850);
        }, 3400);
      } else {
        setPipelineVisible(false);
        alert("Erro ao iniciar a geração: " + (data.message || "Erro desconhecido"));
      }
    } catch (err) {
      console.error(err);
      setPipelineVisible(false);
      alert("Erro ao conectar com o servidor local.");
    } finally {
      setLoading(false);
    }
  };

  const handleSelectSite = async (siteId: string) => {
    try {
      const res = await fetch(`${API_URL}/api/v1/biosites/${siteId}`);
      const data = await res.json();
      if (data.id) {
        setSelectedSite(data);
        setEditName(data.name || "");
        setEditDescription(data.description || "");
        setEditProfilePic(data.profile_image_url || "");
        setEditPixelFb(data.pixel_facebook || "");
        setEditGoogleGa(data.google_analytics || "");
        setEditAsaasId(data.asaas_subscription_id || "");
        setEditSubStatus(data.subscription_status || "paid");

        const theme = data.theme_config ? (typeof data.theme_config === "string" ? JSON.parse(data.theme_config) : data.theme_config) : {};
        setEditTemplate(theme.template || "minimalist_glass");
        
        setEditPrimary(hslToHex(theme.primary_color || "220, 80%, 50%"));
        setEditAccent(hslToHex(theme.accent_color || "35, 90%, 50%"));
        setEditBg(hslToHex(theme.bg_color || "222, 47%, 11%"));
        setEditText(hslToHex(theme.text_color || "0, 0%, 100%"));

        setEditLinks(data.links || []);
        setPreviewKey(prev => prev + 1);
      }
    } catch (err) {
      console.error("Erro ao carregar detalhes do bio site:", err);
    }
  };

  const handleSave = async () => {
    if (!selectedSite) return;

    const themeConfig = {
      template: editTemplate,
      primary_color: hexToHsl(editPrimary),
      accent_color: hexToHsl(editAccent),
      bg_color: hexToHsl(editBg),
      text_color: hexToHsl(editText),
      font_family: editTemplate === "neo_brutalist" ? "Space Grotesk" : "Inter"
    };

    const payload = {
      name: editName,
      nicho: selectedSite.nicho,
      slug: selectedSite.slug, // Mantém o slug atual
      profile_image_url: editProfilePic,
      description: editDescription,
      theme_config: themeConfig,
      pixel_facebook: editPixelFb,
      google_analytics: editGoogleGa,
      subscription_status: editSubStatus,
      asaas_subscription_id: editAsaasId,
      links: editLinks
    };

    try {
      const res = await fetch(`${API_URL}/api/v1/biosites/${selectedSite.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (data.success) {
        alert("Bio Site atualizado com sucesso!");
        loadExistingSites();
        setPreviewKey(prev => prev + 1);
      }
    } catch (err) {
      console.error("Erro ao salvar alterações:", err);
    }
  };

  const handleDelete = async (siteId: string) => {
    if (!confirm("Tem certeza que deseja excluir este Bio Site permanentemente?")) return;
    try {
      await fetch(`${API_URL}/api/v1/biosites/${siteId}`, { method: "DELETE" });
      loadExistingSites();
      if (selectedSite?.id === siteId) {
        setSelectedSite(null);
      }
    } catch (err) {
      console.error("Erro ao excluir:", err);
    }
  };

  // Link helper list management
  const handleLinkChange = (index: number, field: string, value: string) => {
    const updated = [...editLinks];
    updated[index] = { ...updated[index], [field]: value };
    setEditLinks(updated);
  };

  const handleAddLink = () => {
    setEditLinks([...editLinks, { title: "Novo Link", url: "https://", icon: "🔗", animation: "none" }]);
  };

  const handleRemoveLink = (index: number) => {
    setEditLinks(editLinks.filter((_, i) => i !== index));
  };

  return (
    <div className="min-h-screen bg-[var(--ink)] text-[#f8fafc]">
      <header className="border-b border-[var(--surface)] bg-[var(--ink)]">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link href="/admin" className="text-sm text-[var(--text-dim)] hover:text-white">← Voltar ao Admin</Link>
            <span className="text-[#334155]">/</span>
            <h1 className="text-lg font-bold text-[var(--brand)]">🔗 Fábrica de Bio Sites (Link na Bio)</h1>
          </div>
          <span className="badge bg-purple-500/20 text-purple-400 text-xs font-bold px-3 py-1 rounded-full border border-purple-500/30">
            Premium Impeccable.style + Asaas
          </span>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-8 space-y-8">
        
        {/* Existentes */}
        <div className="bg-[var(--ink)] border border-[var(--surface)] rounded-2xl p-6 shadow-xl">
          <h2 className="text-lg font-bold text-[#f1f5f9] mb-4">🔗 Seus Bio Sites Ativos</h2>
          {loadingList ? (
            <p className="text-xs text-[var(--text-dim)]">Carregando lista...</p>
          ) : existingSites.length === 0 ? (
            <p className="text-xs text-[var(--text-dim)]">Nenhum Bio Site criado ainda. Use o gerador abaixo!</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {existingSites.map((site) => (
                <div key={site.id} className="bg-[var(--surface)] border border-[var(--surface)] rounded-xl p-4 hover:border-[var(--brand)] transition-all flex flex-col justify-between">
                  <div>
                    <div className="flex items-start justify-between mb-2">
                      <h3 className="text-sm font-bold text-white line-clamp-1">{site.name}</h3>
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${site.subscription_status === "paid" ? "bg-green-500/20 text-green-400" : "bg-red-500/20 text-red-400"}`}>
                        {site.subscription_status === "paid" ? "🟢 Ativo" : "🔴 Suspenso Asaas"}
                      </span>
                    </div>
                    <p className="text-xs text-[var(--text-dim)] mb-2">Nicho: {site.nicho}</p>
                    <a href={`${API_URL}/bio/${site.slug}`} target="_blank" rel="noopener noreferrer" className="text-xs text-[var(--brand)] font-mono hover:underline block mb-3 break-all">
                      /bio/{site.slug} ↗
                    </a>
                  </div>
                  <div className="flex items-center justify-between border-t border-[var(--border)] pt-2">
                    <span className="text-[9px] text-gray-500 font-mono">{site.id}</span>
                    <div className="flex gap-2">
                      <button onClick={() => handleSelectSite(site.id)} className="text-xs text-[var(--brand)] font-semibold hover:underline">Editar & Preview</button>
                      <button onClick={() => handleDelete(site.id)} className="text-xs text-red-400 hover:underline">Excluir</button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Gerador por IA */}
        <div className="bg-[var(--ink)] border border-[var(--surface)] rounded-2xl p-6 shadow-xl space-y-4">
          <div>
            <h2 className="text-lg font-bold text-[#f1f5f9]">🚀 Gerar Novo Bio Site com IA</h2>
            <p className="text-xs text-[var(--text-dim)]">Insira a descrição e nicho do seu cliente local. A Sala de Agentes criará a identidade e sugestão de links de conversão instantaneamente.</p>
          </div>
          <form onSubmit={handleGenerate} className="grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
            <div className="md:col-span-2">
              <label className="block text-xs font-bold text-[var(--text-dim)] mb-1">PROMPT / NOME DA EMPRESA</label>
              <input
                type="text"
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Ex: Barbearia do Carlão - cortes modernos e barba na toalha quente"
                className="w-full bg-[var(--surface)] border border-[#334155] rounded-xl px-4 py-3 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-[var(--brand)]"
                required
              />
            </div>
            <div className="flex gap-2">
              <div className="flex-1">
                <label className="block text-xs font-bold text-[var(--text-dim)] mb-1">NICHO</label>
                <select
                  value={niche}
                  onChange={(e) => setNiche(e.target.value)}
                  className="w-full bg-[var(--surface)] border border-[#334155] rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:border-[var(--brand)]"
                >
                  <option value="Geral">Geral</option>
                  <option value="Beleza & Estética">Beleza & Estética</option>
                  <option value="Gastronomia">Gastronomia / Restaurante</option>
                  <option value="Finanças">Finanças</option>
                  <option value="Fitness & Saúde">Fitness & Saúde</option>
                  <option value="Espiritualidade">Espiritualidade</option>
                </select>
              </div>
              <button
                type="submit"
                disabled={loading}
                className="bg-[var(--brand)] text-[#090d16] font-bold px-6 py-3 rounded-xl text-sm hover:brightness-110 disabled:opacity-50 transition-all"
              >
                {loading ? "Criando..." : "Gerar"}
              </button>
            </div>
          </form>
        </div>

        {/* Pipeline de IA - Stepper de Progresso */}
        {pipelineVisible && (
          <div className="bg-[var(--ink)] border border-[var(--brand)]/30 rounded-2xl p-6 shadow-xl space-y-4">
            <div className="flex items-center gap-3">
              <div className="animate-spin w-5 h-5 rounded-full border-2 border-t-transparent border-[var(--brand)]"></div>
              <h3 className="text-sm font-bold text-[var(--brand)] uppercase tracking-wider">
                Pipeline de IA: Estruturando Bio Site
              </h3>
            </div>
            
            <div className="space-y-3 font-mono text-xs">
              <div className={`flex items-center gap-2 ${pipelineStep >= 1 ? "text-[var(--brand)] font-bold animate-pulse" : "text-gray-600"}`}>
                <span>{pipelineStep >= 1 ? "🔵" : "⚪"}</span>
                <span>[Agente Seu Link] Analisando o nicho "{niche}" e escrevendo copy de alta conversão...</span>
              </div>
              <div className={`flex items-center gap-2 ${pipelineStep >= 2 ? "text-[var(--brand)] font-bold animate-pulse" : "text-gray-600"}`}>
                <span>{pipelineStep >= 2 ? "🔵" : "⚪"}</span>
                <span>[Agente Seu Design] Definindo paleta de cores HSL e selecionando o template Impeccable.style...</span>
              </div>
              <div className={`flex items-center gap-2 ${pipelineStep >= 3 ? "text-[var(--brand)] font-bold animate-pulse" : "text-gray-600"}`}>
                <span>{pipelineStep >= 3 ? "🔵" : "⚪"}</span>
                <span>[Agente Seu Link] Sugerindo links essenciais de agendamento e redes sociais...</span>
              </div>
              <div className={`flex items-center gap-2 ${pipelineStep >= 4 ? "text-[var(--brand)] font-bold animate-pulse" : "text-gray-600"}`}>
                <span>{pipelineStep >= 4 ? "🔵" : "⚪"}</span>
                <span>[Database] Gravando os dados do Bio Site no banco local (dezafira.db)...</span>
              </div>
              <div className={`flex items-center gap-2 ${pipelineStep >= 5 ? "text-green-400 font-bold" : "text-gray-600"}`}>
                <span>{pipelineStep >= 5 ? "✨" : "⚪"}</span>
                <span>[Sucesso] Bio Site criado! Atualizando painel...</span>
              </div>
            </div>
          </div>
        )}

        {/* Painel Lateral - Edição e Preview */}
        {selectedSite && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
            
            {/* Esquerda: Formulário de Configuração */}
            <div className="lg:col-span-7 bg-[var(--ink)] border border-[var(--surface)] rounded-2xl p-6 shadow-xl space-y-6">
              <div className="border-b border-[var(--surface)] pb-3 flex justify-between items-center">
                <h3 className="text-lg font-bold text-[#f1f5f9]">Configurações do Bio Site</h3>
                <button onClick={handleSave} className="bg-green-600 hover:bg-green-700 text-white font-bold px-4 py-2 rounded-xl text-xs transition-all">
                  💾 Salvar Alterações
                </button>
              </div>

              {/* Informações Gerais */}
              <div className="space-y-4">
                <h4 className="text-xs font-bold text-[var(--brand)] uppercase tracking-wider">Informações Gerais</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs text-[var(--text-dim)] mb-1">Nome Comercial</label>
                    <input
                      type="text"
                      value={editName}
                      onChange={(e) => setEditName(e.target.value)}
                      className="w-full bg-[var(--surface)] border border-[#334155] rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-[var(--brand)]"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-[var(--text-dim)] mb-1">Foto de Perfil URL</label>
                    <input
                      type="text"
                      value={editProfilePic}
                      onChange={(e) => setEditProfilePic(e.target.value)}
                      placeholder="https://sua-foto.png (ou vazio para avatar de letras)"
                      className="w-full bg-[var(--surface)] border border-[#334155] rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-[var(--brand)]"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-xs text-[var(--text-dim)] mb-1">Biografia / Descrição Curta</label>
                  <textarea
                    value={editDescription}
                    onChange={(e) => setEditDescription(e.target.value)}
                    rows={2}
                    className="w-full bg-[var(--surface)] border border-[#334155] rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-[var(--brand)]"
                  />
                </div>
              </div>

              {/* Design & Cores */}
              <div className="space-y-4 pt-4 border-t border-[var(--surface)]">
                <h4 className="text-xs font-bold text-[var(--brand)] uppercase tracking-wider">Design & Cores (Impeccable.style)</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs text-[var(--text-dim)] mb-1">Template Base</label>
                    <select
                      value={editTemplate}
                      onChange={(e) => setEditTemplate(e.target.value)}
                      className="w-full bg-[var(--surface)] border border-[#334155] rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-[var(--brand)]"
                    >
                      <option value="midnight_aura">Midnight Aura (Roxo / Escuro Neon)</option>
                      <option value="minimalist_glass">Minimalist Glass (Translúcido / Vidro)</option>
                      <option value="neo_brutalist">Neo-Brutalist (Alto Contraste Retro)</option>
                    </select>
                  </div>
                  <div className="grid grid-cols-4 gap-2">
                    <div>
                      <label className="block text-[10px] text-[var(--text-dim)] mb-1 text-center">Primária</label>
                      <input type="color" value={editPrimary} onChange={(e) => setEditPrimary(e.target.value)} className="w-full h-8 rounded border-0 cursor-pointer" />
                    </div>
                    <div>
                      <label className="block text-[10px] text-[var(--text-dim)] mb-1 text-center">Destaque</label>
                      <input type="color" value={editAccent} onChange={(e) => setEditAccent(e.target.value)} className="w-full h-8 rounded border-0 cursor-pointer" />
                    </div>
                    <div>
                      <label className="block text-[10px] text-[var(--text-dim)] mb-1 text-center">Fundo</label>
                      <input type="color" value={editBg} onChange={(e) => setEditBg(e.target.value)} className="w-full h-8 rounded border-0 cursor-pointer" />
                    </div>
                    <div>
                      <label className="block text-[10px] text-[var(--text-dim)] mb-1 text-center">Texto</label>
                      <input type="color" value={editText} onChange={(e) => setEditText(e.target.value)} className="w-full h-8 rounded border-0 cursor-pointer" />
                    </div>
                  </div>
                </div>
              </div>

              {/* Rastreamento e Cobrança */}
              <div className="space-y-4 pt-4 border-t border-[var(--surface)]">
                <h4 className="text-xs font-bold text-[var(--brand)] uppercase tracking-wider">Integrações, Pixels & Asaas</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs text-[var(--text-dim)] mb-1">Facebook Pixel ID</label>
                    <input
                      type="text"
                      value={editPixelFb}
                      onChange={(e) => setEditPixelFb(e.target.value)}
                      placeholder="Ex: 1234567890"
                      className="w-full bg-[var(--surface)] border border-[#334155] rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-[var(--brand)]"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-[var(--text-dim)] mb-1">Google Analytics ID (G-XXXX)</label>
                    <input
                      type="text"
                      value={editGoogleGa}
                      onChange={(e) => setEditGoogleGa(e.target.value)}
                      placeholder="Ex: G-XXXXXXXXXX"
                      className="w-full bg-[var(--surface)] border border-[#334155] rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-[var(--brand)]"
                    />
                  </div>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs text-[var(--text-dim)] mb-1">ID Assinatura Asaas</label>
                    <input
                      type="text"
                      value={editAsaasId}
                      onChange={(e) => setEditAsaasId(e.target.value)}
                      placeholder="Ex: sub_xxxxxx"
                      className="w-full bg-[var(--surface)] border border-[#334155] rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-[var(--brand)]"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-[var(--text-dim)] mb-1">Status da Assinatura</label>
                    <select
                      value={editSubStatus}
                      onChange={(e) => setEditSubStatus(e.target.value)}
                      className="w-full bg-[var(--surface)] border border-[#334155] rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-[var(--brand)]"
                    >
                      <option value="paid">🟢 Pago / Ativo</option>
                      <option value="unpaid">🔴 Inadimplente / Suspenso</option>
                    </select>
                  </div>
                </div>
              </div>

              {/* Gerenciador de Links */}
              <div className="space-y-4 pt-4 border-t border-[var(--surface)]">
                <div className="flex justify-between items-center">
                  <h4 className="text-xs font-bold text-[var(--brand)] uppercase tracking-wider">Gerenciador de Links</h4>
                  <button onClick={handleAddLink} className="text-xs text-[var(--brand)] border border-[var(--brand)] px-3 py-1 rounded-lg hover:bg-[#38bdf811]">
                    ➕ Adicionar Link
                  </button>
                </div>
                <div className="space-y-3">
                  {editLinks.map((link, idx) => (
                    <div key={idx} className="bg-[var(--surface)] border border-[var(--surface)] p-4 rounded-xl space-y-3">
                      <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
                        <div className="md:col-span-2">
                          <label className="block text-[10px] text-[var(--text-dim)] mb-1">Título do Botão</label>
                          <input
                            type="text"
                            value={link.title}
                            onChange={(e) => handleLinkChange(idx, "title", e.target.value)}
                            className="w-full bg-[var(--ink)] border border-[#334155] rounded-lg px-3 py-1.5 text-xs text-white"
                          />
                        </div>
                        <div>
                          <label className="block text-[10px] text-[var(--text-dim)] mb-1">Ícone (Emoji)</label>
                          <input
                            type="text"
                            value={link.icon || ""}
                            onChange={(e) => handleLinkChange(idx, "icon", e.target.value)}
                            className="w-full bg-[var(--ink)] border border-[#334155] rounded-lg px-3 py-1.5 text-xs text-white text-center"
                          />
                        </div>
                        <div>
                          <label className="block text-[10px] text-[var(--text-dim)] mb-1">Efeito</label>
                          <select
                            value={link.animation || "none"}
                            onChange={(e) => handleLinkChange(idx, "animation", e.target.value)}
                            className="w-full bg-[var(--ink)] border border-[#334155] rounded-lg px-3 py-1.5 text-xs text-white"
                          >
                            <option value="none">Nenhum</option>
                            <option value="pulse">Pulso 💓</option>
                            <option value="shake">Tremor 📳</option>
                            <option value="bounce">Salto 🦘</option>
                          </select>
                        </div>
                      </div>
                      <div className="flex gap-2 items-center">
                        <div className="flex-1">
                          <label className="block text-[10px] text-[var(--text-dim)] mb-1">URL de Destino</label>
                          <input
                            type="text"
                            value={link.url}
                            onChange={(e) => handleLinkChange(idx, "url", e.target.value)}
                            className="w-full bg-[var(--ink)] border border-[#334155] rounded-lg px-3 py-1.5 text-xs text-white"
                          />
                        </div>
                        <button onClick={() => handleRemoveLink(idx)} className="text-xs text-red-400 hover:underline self-end pb-1.5">
                          Remover
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Direita: Preview Mobile */}
            <div className="lg:col-span-5 flex flex-col items-center">
              <div className="sticky top-6 w-[320px] h-[640px] bg-[#000] border-[6px] border-[#334155] rounded-[40px] shadow-2xl p-4 flex flex-col justify-between relative overflow-hidden">
                <div className="absolute top-2 left-1/2 -translate-x-1/2 w-28 h-4 bg-[#1e293b] rounded-full z-20"></div>
                
                {/* Mobile Preview Frame */}
                <div className="flex-1 mt-4 bg-[var(--surface)] rounded-2xl overflow-hidden border border-[var(--surface)] relative">
                  <iframe
                    key={previewKey}
                    src={`${API_URL}/bio/${selectedSite.slug}?preview=true`}
                    className="w-full h-full border-0"
                    title="Real-Time Bio Site Preview"
                  />
                </div>
                
                <div className="pt-2 flex justify-center text-[10px] text-gray-500 font-semibold uppercase tracking-wider">
                  Visualização Mobile Real-Time
                </div>
              </div>
            </div>

          </div>
        )}

      </main>
    </div>
  );
}
