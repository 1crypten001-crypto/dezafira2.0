"use client";

import { useEffect, useState } from "react";
import { useAuth } from "../../../lib/auth-context";
import { useRouter } from "next/navigation";
import { api } from "../../../lib/api";

interface Offer {
  id: string;
  slug: string;
  niche: string;
  keyword: string;
  angle: string;
  mechanism: string;
  status: string;
  conversion_score: number;
  seo_score: number;
  created_at: string;
}

interface Investigation {
  facebook_ads: any[];
  facebook_patterns: any;
  google_keywords: any[];
  google_backlinks: any[];
  status: string;
}

interface Keyword {
  id: string;
  keyword: string;
  search_volume: number;
  difficulty: number;
  intent: string;
}

interface Backlink {
  id: string;
  domain: string;
  url: string;
  relevance: string;
  type: string;
}

interface Asset {
  id: string;
  slot: string;
  url: string | null;
  prompt: string;
  provider: string;
}

interface OfferDetail extends Offer {
  investigation?: Investigation;
  keywords?: Keyword[];
  backlinks?: Backlink[];
  assets?: Asset[];
  avatar_1_prompt?: string;
  avatar_2_prompt?: string;
  mascot_prompt?: string;
  avatar_1_url?: string;
  avatar_2_url?: string;
  mascot_url?: string;
  headlines?: string[];
  body_long?: string;
  body_short?: string;
  ctas?: string[];
  price_cents?: number;
  validation?: {
    conversion_score: number;
    seo_score: number;
    overall_score: number;
    recommendations: string[];
    strengths: string[];
    weaknesses: string[];
  };
}

export default function FabricaOfertasPage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  
  const [offers, setOffers] = useState<Offer[]>([]);
  const [selectedOffer, setSelectedOffer] = useState<OfferDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<"list" | "investigation" | "model" | "copy" | "assets" | "publish">("list");
  
  // Form state
  const [niche, setNiche] = useState("");
  const [keyword, setKeyword] = useState("");
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    if (!authLoading && (!user || user.role !== "admin")) {
      router.push("/painel");
    }
  }, [user, authLoading, router]);

  useEffect(() => {
    if (user?.role === "admin") {
      loadOffers();
    }
  }, [user]);

  const loadOffers = async () => {
    try {
      const data = await api.request("/api/v1/offers/");
      setOffers(data.offers || []);
    } catch (err) {
      console.error("Erro ao carregar ofertas:", err);
    }
  };

  const createOffer = async () => {
    if (!niche || !keyword) {
      alert("Preencha nicho e keyword");
      return;
    }

    setCreating(true);
    try {
      const data = await api.request("/api/v1/offers/create", {
        method: "POST",
        body: JSON.stringify({ niche, keyword }),
      });
      
      setSelectedOffer(data.offer as OfferDetail);
      setActiveTab("investigation");
      setNiche("");
      setKeyword("");
      await loadOffers();
    } catch (err) {
      alert("Erro ao criar oferta: " + err);
    } finally {
      setCreating(false);
    }
  };

  const runPipeline = async (offerId: string) => {
    setLoading(true);
    try {
      await api.request(`/api/v1/offers/${offerId}/run`, {
        method: "POST",
      });
      await loadOffer(offerId);
      alert("Pipeline concluída com sucesso!");
    } catch (err) {
      alert("Erro ao executar pipeline: " + err);
    } finally {
      setLoading(false);
    }
  };

  const loadOffer = async (offerId: string) => {
    try {
      const data = await api.request(`/api/v1/offers/${offerId}`);
      setSelectedOffer(data.offer as OfferDetail);
    } catch (err) {
      console.error("Erro ao carregar oferta:", err);
    }
  };

  const regenerateAsset = async (offerId: string, slot: string) => {
    try {
      await api.request(`/api/v1/offers/${offerId}/regenerate-assets`, {
        method: "POST",
        body: JSON.stringify({ slot, style_id: "moderno" }),
      });
      await loadOffer(offerId);
      alert(`Asset ${slot} regenerado!`);
    } catch (err) {
      alert("Erro ao regenerar asset: " + err);
    }
  };

  const publishOffer = async (offerId: string) => {
    try {
      await api.request(`/api/v1/offers/${offerId}/publish`, {
        method: "POST",
      });
      alert("Oferta publicada no Blueprint!");
      await loadOffer(offerId);
    } catch (err) {
      alert("Erro ao publicar: " + err);
    }
  };

  const deleteOffer = async (offerId: string) => {
    if (!confirm("Tem certeza que deseja remover esta oferta?")) return;
    
    try {
      await api.request(`/api/v1/offers/${offerId}`, {
        method: "DELETE",
      });
      await loadOffers();
      if (selectedOffer?.id === offerId) {
        setSelectedOffer(null);
        setActiveTab("list");
      }
    } catch (err) {
      alert("Erro ao remover: " + err);
    }
  };

  if (authLoading || !user) {
    return (
      <div className="min-h-screen bg-[#0a0e1a] flex items-center justify-center">
        <div className="text-white text-lg">Carregando...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0a0e1a] text-white">
      {/* Header */}
      <div className="bg-[#111827] border-b border-[#1e293b] px-6 py-4">
        <div className="flex items-center justify-between max-w-7xl mx-auto">
          <div>
            <h1 className="text-2xl font-bold bg-gradient-to-r from-[#8b5cf6] to-[#ec4899] bg-clip-text text-transparent">
              🏭 Fábrica de Ofertas
            </h1>
            <p className="text-gray-400 text-sm mt-1">
              Dário + Team — Investigação, Modelagem, Copy e Personagens
            </p>
          </div>
          <button
            onClick={() => router.push("/admin")}
            className="px-4 py-2 bg-[#1e293b] hover:bg-[#334155] rounded-xl text-sm transition-colors"
          >
            ← Voltar
          </button>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Sidebar - Lista de Ofertas */}
          <div className="lg:col-span-1">
            <div className="bg-[#111827] rounded-2xl border border-[#1e293b] p-5">
              <h2 className="text-lg font-semibold mb-4">Criar Nova Oferta</h2>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-2">Nicho</label>
                  <select
                    value={niche}
                    onChange={(e) => setNiche(e.target.value)}
                    className="w-full bg-[#0a0e1a] border border-[#334155] rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:border-[#8b5cf6]"
                  >
                    <option value="">Selecione o nicho</option>
                    <option value="emagrecimento">Emagrecimento</option>
                    <option value="financas">Finanças</option>
                    <option value="relacionamentos">Relacionamentos</option>
                    <option value="receitas">Receitas</option>
                    <option value="marketing">Marketing Digital</option>
                    <option value="desenvolvimento_pessoal">Desenvolvimento Pessoal</option>
                    <option value="saude">Saúde</option>
                    <option value="diy">DIY & Maker</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm text-gray-400 mb-2">Keyword Principal</label>
                  <input
                    type="text"
                    value={keyword}
                    onChange={(e) => setKeyword(e.target.value)}
                    placeholder="Ex: como emagrecer"
                    className="w-full bg-[#0a0e1a] border border-[#334155] rounded-xl px-4 py-3 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-[#8b5cf6]"
                    required
                  />
                </div>

                <button
                  onClick={createOffer}
                  disabled={creating || !niche || !keyword}
                  className="w-full bg-gradient-to-r from-[#8b5cf6] to-[#ec4899] hover:from-[#7c3aed] hover:to-[#db2777] disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold py-3 rounded-xl transition-all"
                >
                  {creating ? "⏳ Criando..." : "🚀 Criar Oferta"}
                </button>
              </div>

              {/* Lista de Ofertas */}
              <div className="mt-6">
                <h3 className="text-sm font-semibold text-gray-400 mb-3">Ofertas Existentes ({offers.length})</h3>
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {offers.map((offer) => (
                    <button
                      key={offer.id}
                      onClick={() => {
                        setSelectedOffer(offer as OfferDetail);
                        setActiveTab("investigation");
                      }}
                      className={`w-full text-left p-3 rounded-xl border transition-all ${
                        selectedOffer?.id === offer.id
                          ? "border-[#8b5cf6] bg-[#8b5cf611]"
                          : "border-[#1e293b] bg-[#0a0e1a] hover:border-[#334155]"
                      }`}
                    >
                      <div className="flex items-start justify-between">
                        <div>
                          <p className="font-medium text-sm">{offer.keyword}</p>
                          <p className="text-xs text-gray-500">{offer.niche}</p>
                        </div>
                        <span className={`px-2 py-1 rounded-lg text-xs ${
                          offer.status === "completed" ? "bg-green-500/20 text-green-400" :
                          offer.status === "running" ? "bg-yellow-500/20 text-yellow-400" :
                          "bg-gray-500/20 text-gray-400"
                        }`}>
                          {offer.status === "completed" ? "✅" :
                           offer.status === "running" ? "⏳" : "📝"}
                        </span>
                      </div>
                      {offer.conversion_score && (
                        <div className="mt-2 flex gap-2 text-xs">
                          <span className="text-purple-400">Conversão: {offer.conversion_score}%</span>
                          <span className="text-blue-400">SEO: {offer.seo_score}%</span>
                        </div>
                      )}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Main Content */}
          <div className="lg:col-span-2">
            {!selectedOffer ? (
              <div className="bg-[#111827] rounded-2xl border border-[#1e293b] p-12 text-center">
                <div className="text-6xl mb-4">🎯</div>
                <h2 className="text-xl font-semibold mb-2">Crie sua primeira oferta</h2>
                <p className="text-gray-400">
                  Selecione um nicho e keyword no painel lateral para começar
                </p>
              </div>
            ) : (
              <div className="bg-[#111827] rounded-2xl border border-[#1e293b] overflow-hidden">
                {/* Tabs */}
                <div className="flex border-b border-[#1e293b] overflow-x-auto">
                  {[
                    { id: "investigation", label: "🔍 Investigação", icon: "🔍" },
                    { id: "model", label: "📋 Modelo", icon: "📋" },
                    { id: "copy", label: "✍️ Copy", icon: "✍️" },
                    { id: "assets", label: "🎨 Assets", icon: "🎨" },
                    { id: "publish", label: "🚀 Publicar", icon: "🚀" },
                  ].map((tab) => (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id as any)}
                      className={`flex-shrink-0 px-4 py-3 text-sm font-medium transition-colors ${
                        activeTab === tab.id
                          ? "bg-[#8b5cf6] text-white"
                          : "text-gray-400 hover:text-white hover:bg-[#1e293b]"
                      }`}
                    >
                      {tab.label}
                    </button>
                  ))}
                </div>

                {/* Tab Content */}
                <div className="p-6">
                  {/* INVESTIGAÇÃO TAB */}
                  {activeTab === "investigation" && (
                    <div className="space-y-6">
                      <div className="flex items-center justify-between">
                        <h3 className="text-lg font-semibold">Investigação do Dário</h3>
                        <button
                          onClick={() => runPipeline(selectedOffer.id)}
                          disabled={loading}
                          className="px-4 py-2 bg-[#8b5cf6] hover:bg-[#7c3aed] disabled:opacity-50 text-white rounded-xl text-sm font-medium transition-colors"
                        >
                          {loading ? "⏳ Executando..." : "▶️ Executar Pipeline"}
                        </button>
                      </div>

                      {/* Status */}
                      <div className={`p-4 rounded-xl ${
                        selectedOffer.status === "completed" ? "bg-green-500/10 border border-green-500/30" :
                        selectedOffer.status === "running" ? "bg-yellow-500/10 border border-yellow-500/30" :
                        "bg-gray-500/10 border border-gray-500/30"
                      }`}>
                        <p className="font-medium">
                          Status: {selectedOffer.status === "completed" ? "✅ Concluída" :
                                   selectedOffer.status === "running" ? "⏳ Em execução" :
                                   "📝 Rascunho"}
                        </p>
                      </div>

                      {/* Facebook Ads */}
                      {(selectedOffer.investigation?.facebook_ads?.length ?? 0) > 0 && (
                        <div>
                          <h4 className="font-semibold mb-3 flex items-center gap-2">
                            <span className="text-blue-400">📘</span>
                            Anúncios Facebook ({selectedOffer.investigation?.facebook_ads?.length})
                          </h4>
                          <div className="space-y-3 max-h-96 overflow-y-auto">
                            {selectedOffer.investigation?.facebook_ads?.map((ad, idx) => (
                              <div key={idx} className="bg-[#0a0e1a] border border-[#1e293b] rounded-xl p-4">
                                <p className="font-medium text-sm text-blue-300">{ad.page_name}</p>
                                <p className="text-xs text-gray-400 mt-1 line-clamp-2">{ad.ad_copy}</p>
                                <div className="mt-2 flex gap-2 text-xs">
                                  <span className="px-2 py-1 bg-[#1e293b] rounded-lg">{ad.headline}</span>
                                  <span className="px-2 py-1 bg-[#1e293b] rounded-lg">{ad.cta}</span>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Keywords SEO */}
                      {(selectedOffer.keywords?.length ?? 0) > 0 && (
                        <div>
                          <h4 className="font-semibold mb-3 flex items-center gap-2">
                            <span className="text-green-400">🔑</span>
                            Keywords SEO ({selectedOffer.keywords?.length})
                          </h4>
                          <div className="grid grid-cols-2 gap-3">
                            {selectedOffer.keywords?.map((kw) => (
                              <div key={kw.id} className="bg-[#0a0e1a] border border-[#1e293b] rounded-xl p-3">
                                <p className="font-medium text-sm">{kw.keyword}</p>
                                <div className="mt-2 flex gap-2 text-xs text-gray-400">
                                  <span>👁️ {kw.search_volume}</span>
                                  <span className={kw.difficulty < 40 ? "text-green-400" : kw.difficulty < 60 ? "text-yellow-400" : "text-red-400"}>
                                    🔥 {kw.difficulty}
                                  </span>
                                  <span className="px-2 py-0.5 bg-[#1e293b] rounded">{kw.intent}</span>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Backlinks */}
                      {(selectedOffer.backlinks?.length ?? 0) > 0 && (
                        <div>
                          <h4 className="font-semibold mb-3 flex items-center gap-2">
                            <span className="text-purple-400">🔗</span>
                            Backlinks Potenciais ({selectedOffer.backlinks?.length})
                          </h4>
                          <div className="space-y-2">
                            {selectedOffer.backlinks?.map((bl) => (
                              <div key={bl.id} className="bg-[#0a0e1a] border border-[#1e293b] rounded-xl p-3 flex items-center justify-between">
                                <div>
                                  <p className="font-medium text-sm">{bl.domain}</p>
                                  <p className="text-xs text-gray-500">{bl.url}</p>
                                </div>
                                <span className={`px-2 py-1 rounded-lg text-xs ${
                                  bl.relevance === "alta" ? "bg-green-500/20 text-green-400" :
                                  bl.relevance === "media" ? "bg-yellow-500/20 text-yellow-400" :
                                  "bg-gray-500/20 text-gray-400"
                                }`}>
                                  {bl.relevance}
                                </span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {/* MODELO TAB */}
                  {activeTab === "model" && (
                    <div className="space-y-6">
                      <h3 className="text-lg font-semibold">Modelo da Oferta</h3>
                      
                      <div className="grid grid-cols-2 gap-4">
                        <div className="bg-[#0a0e1a] border border-[#1e293b] rounded-xl p-4">
                          <p className="text-xs text-gray-400 mb-1">Angle</p>
                          <p className="font-medium">{selectedOffer.angle || "Não definido"}</p>
                        </div>
                        <div className="bg-[#0a0e1a] border border-[#1e293b] rounded-xl p-4">
                          <p className="text-xs text-gray-400 mb-1">Mecanismo</p>
                          <p className="font-medium text-sm">{selectedOffer.mechanism || "Não definido"}</p>
                        </div>
                        <div className="bg-[#0a0e1a] border border-[#1e293b] rounded-xl p-4">
                          <p className="text-xs text-gray-400 mb-1">Preço Sugerido</p>
                          <p className="font-medium text-green-400">
                            R$ {(selectedOffer.price_cents || 0) / 100}
                          </p>
                        </div>
                      </div>

                      {/* Avatares */}
                      <div>
                        <h4 className="font-semibold mb-3">Avatares & Personagens</h4>
                        <div className="grid grid-cols-3 gap-4">
                          <div className="bg-[#0a0e1a] border border-[#1e293b] rounded-xl p-4">
                            <p className="text-xs text-gray-400 mb-2">Avatar #1 (Homem)</p>
                            <div className="aspect-square bg-[#111827] rounded-lg flex items-center justify-center mb-2">
                              {selectedOffer.avatar_1_url ? (
                                <img src={selectedOffer.avatar_1_url} alt="Avatar 1" className="w-full h-full object-cover rounded-lg" />
                              ) : (
                                <span className="text-4xl">👤</span>
                              )}
                            </div>
                            <p className="text-xs text-gray-500 line-clamp-2">{selectedOffer.avatar_1_prompt}</p>
                            <button
                              onClick={() => regenerateAsset(selectedOffer.id, "avatar_1")}
                              className="mt-2 w-full px-3 py-2 bg-[#1e293b] hover:bg-[#334155] rounded-lg text-xs transition-colors"
                            >
                              🔄 Regenerar
                            </button>
                          </div>

                          <div className="bg-[#0a0e1a] border border-[#1e293b] rounded-xl p-4">
                            <p className="text-xs text-gray-400 mb-2">Avatar #2 (Mulher)</p>
                            <div className="aspect-square bg-[#111827] rounded-lg flex items-center justify-center mb-2">
                              {selectedOffer.avatar_2_url ? (
                                <img src={selectedOffer.avatar_2_url} alt="Avatar 2" className="w-full h-full object-cover rounded-lg" />
                              ) : (
                                <span className="text-4xl">👩</span>
                              )}
                            </div>
                            <p className="text-xs text-gray-500 line-clamp-2">{selectedOffer.avatar_2_prompt}</p>
                            <button
                              onClick={() => regenerateAsset(selectedOffer.id, "avatar_2")}
                              className="mt-2 w-full px-3 py-2 bg-[#1e293b] hover:bg-[#334155] rounded-lg text-xs transition-colors"
                            >
                              🔄 Regenerar
                            </button>
                          </div>

                          <div className="bg-[#0a0e1a] border border-[#1e293b] rounded-xl p-4">
                            <p className="text-xs text-gray-400 mb-2">Mascote</p>
                            <div className="aspect-square bg-[#111827] rounded-lg flex items-center justify-center mb-2">
                              {selectedOffer.mascot_url ? (
                                <img src={selectedOffer.mascot_url} alt="Mascote" className="w-full h-full object-cover rounded-lg" />
                              ) : (
                                <span className="text-4xl">🎭</span>
                              )}
                            </div>
                            <p className="text-xs text-gray-500 line-clamp-2">{selectedOffer.mascot_prompt}</p>
                            <button
                              onClick={() => regenerateAsset(selectedOffer.id, "mascot")}
                              className="mt-2 w-full px-3 py-2 bg-[#1e293b] hover:bg-[#334155] rounded-lg text-xs transition-colors"
                            >
                              🔄 Regenerar
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* COPY TAB */}
                  {activeTab === "copy" && (
                    <div className="space-y-6">
                      <h3 className="text-lg font-semibold">Copy da Oferta</h3>
                      
                      {/* Headlines */}
                      {(selectedOffer.headlines?.length ?? 0) > 0 && (
                        <div>
                          <h4 className="font-medium mb-3">Headlines ({selectedOffer.headlines?.length})</h4>
                          <div className="space-y-2">
                            {selectedOffer.headlines?.map((h, idx) => (
                              <div key={idx} className="bg-[#0a0e1a] border border-[#1e293b] rounded-xl p-3 flex items-center gap-3">
                                <span className="px-2 py-1 bg-[#8b5cf6] rounded-lg text-xs font-bold">
                                  {String.fromCharCode(65 + idx)}
                                </span>
                                <p className="text-sm">{h}</p>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Body Copy */}
                      {selectedOffer.body_long && (
                        <div>
                          <h4 className="font-medium mb-3">Body Copy</h4>
                          <div className="bg-[#0a0e1a] border border-[#1e293b] rounded-xl p-4">
                            <pre className="whitespace-pre-wrap text-sm text-gray-300 font-sans">
                              {selectedOffer.body_long}
                            </pre>
                          </div>
                        </div>
                      )}

                      {/* CTAs */}
                      {(selectedOffer.ctas?.length ?? 0) > 0 && (
                        <div>
                          <h4 className="font-medium mb-3">CTAs ({selectedOffer.ctas?.length})</h4>
                          <div className="flex flex-wrap gap-2">
                            {selectedOffer.ctas?.map((cta, idx) => (
                              <span
                                key={idx}
                                className="px-4 py-2 bg-gradient-to-r from-[#8b5cf6] to-[#ec4899] rounded-xl text-sm font-medium"
                              >
                                {cta}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {/* ASSETS TAB */}
                  {activeTab === "assets" && (
                    <div className="space-y-6">
                      <h3 className="text-lg font-semibold">Assets Visuais</h3>
                      
                      <div className="grid grid-cols-2 gap-4">
                        {selectedOffer.assets?.map((asset) => (
                          <div key={asset.id} className="bg-[#0a0e1a] border border-[#1e293b] rounded-xl p-4">
                            <p className="text-xs text-gray-400 mb-2 capitalize">{asset.slot}</p>
                            {asset.url ? (
                              <img src={asset.url} alt={asset.slot} className="w-full h-48 object-cover rounded-lg mb-2" />
                            ) : (
                              <div className="w-full h-48 bg-[#111827] rounded-lg flex items-center justify-center mb-2">
                                <span className="text-4xl">🖼️</span>
                              </div>
                            )}
                            <p className="text-xs text-gray-500 line-clamp-2">{asset.prompt}</p>
                            <p className="text-xs text-gray-600 mt-1">Provider: {asset.provider}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* PUBLISH TAB */}
                  {activeTab === "publish" && (
                    <div className="space-y-6">
                      <h3 className="text-lg font-semibold">Publicar no Blueprint</h3>
                      
                      {/* Validation */}
                      {selectedOffer.validation && (
                        <div className="bg-[#0a0e1a] border border-[#1e293b] rounded-xl p-5">
                          <h4 className="font-medium mb-4">Validação da Dona Benta</h4>
                          
                          <div className="grid grid-cols-3 gap-4 mb-4">
                            <div className="text-center">
                              <p className="text-3xl font-bold text-purple-400">
                                {selectedOffer.validation.conversion_score}%
                              </p>
                              <p className="text-xs text-gray-400">Conversão</p>
                            </div>
                            <div className="text-center">
                              <p className="text-3xl font-bold text-blue-400">
                                {selectedOffer.validation.seo_score}%
                              </p>
                              <p className="text-xs text-gray-400">SEO</p>
                            </div>
                            <div className="text-center">
                              <p className="text-3xl font-bold text-green-400">
                                {selectedOffer.validation.overall_score}%
                              </p>
                              <p className="text-xs text-gray-400">Overall</p>
                            </div>
                          </div>

                          {selectedOffer.validation.recommendations?.length > 0 && (
                            <div className="mb-4">
                              <p className="text-sm font-medium text-yellow-400 mb-2">Recomendações:</p>
                              <ul className="space-y-1">
                                {selectedOffer.validation.recommendations.map((rec, idx) => (
                                  <li key={idx} className="text-xs text-gray-400">• {rec}</li>
                                ))}
                              </ul>
                            </div>
                          )}

                          <div className="flex gap-4">
                            {selectedOffer.validation.strengths?.length > 0 && (
                              <div>
                                <p className="text-sm font-medium text-green-400 mb-2">Pontos Fortes:</p>
                                <ul className="space-y-1">
                                  {selectedOffer.validation.strengths.map((s, idx) => (
                                    <li key={idx} className="text-xs text-gray-400">✓ {s}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                            {selectedOffer.validation.weaknesses?.length > 0 && (
                              <div>
                                <p className="text-sm font-medium text-red-400 mb-2">Pontos Fracos:</p>
                                <ul className="space-y-1">
                                  {selectedOffer.validation.weaknesses.map((w, idx) => (
                                    <li key={idx} className="text-xs text-gray-400">✗ {w}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </div>
                        </div>
                      )}

                      {/* Publish Button */}
                      <div className="bg-[#0a0e1a] border border-[#1e293b] rounded-xl p-5">
                        <h4 className="font-medium mb-2">Publicar no Blueprint Engine</h4>
                        <p className="text-sm text-gray-400 mb-4">
                          Todas as informações da oferta serão enviadas para o Blueprint Engine,
                          que gerará o produto completo (curso/ebook), blog com SEO otimizado,
                          landing page e funil de vendas.
                        </p>
                        <button
                          onClick={() => publishOffer(selectedOffer.id)}
                          className="w-full bg-gradient-to-r from-[#10b981] to-[#059669] hover:from-[#059669] hover:to-[#047857] text-white font-semibold py-3 rounded-xl transition-all"
                        >
                          🚀 Publicar no Blueprint
                        </button>
                      </div>
                    </div>
                  )}

                  {/* Actions */}
                  <div className="mt-6 pt-6 border-t border-[#1e293b] flex gap-3">
                    <button
                      onClick={() => deleteOffer(selectedOffer.id)}
                      className="px-4 py-2 bg-red-500/10 hover:bg-red-500/20 text-red-400 rounded-xl text-sm transition-colors"
                    >
                      🗑️ Remover
                    </button>
                    <button
                      onClick={() => loadOffer(selectedOffer.id)}
                      className="px-4 py-2 bg-[#1e293b] hover:bg-[#334155] text-white rounded-xl text-sm transition-colors"
                    >
                      🔄 Atualizar
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
