"use client";

export const dynamic = "force-dynamic";

import { useEffect, useState } from "react";
import Link from "next/link";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const FORMAT_OPTIONS = [
  { id: "ebook", icon: "📗", label: "Ebook" },
  { id: "curso", icon: "🎓", label: "Curso" },
  { id: "app", icon: "📱", label: "MiniApp / Mapa" },
  { id: "blog", icon: "✍️", label: "Blog" },
];

const NICHE_OPTIONS = [
  "Tecnologia & IA",
  "Fitness & Saúde",
  "Finanças & Negócios",
  "Espiritualidade",
  "Marketing Digital",
  "Direito Constitucional",
  "Estudo Bíblico",
];

const STATUS_LABEL: Record<string, { label: string; color: string }> = {
  draft: { label: "🟡 Rascunho", color: "#fbbf24" },
  generating: { label: "⚡ Gerando", color: "#60a5fa" },
  review: { label: "👀 Revisão", color: "#a78bfa" },
  publishing: { label: "🚚 Publicando", color: "#fb923c" },
  published: { label: "✅ Publicado", color: "#4ade80" },
  failed: { label: "❌ Falhou", color: "#f87171" },
};

function authHeaders(extra: Record<string, string> = {}): Record<string, string> {
  const token = typeof window !== "undefined" ? localStorage.getItem("dz_token") : "";
  return token ? { Authorization: `Bearer ${token}`, ...extra } : extra;
}

export default function BlueprintPage() {
  const [theme, setTheme] = useState("");
  const [niche, setNiche] = useState("Tecnologia & IA");
  const [priceCents, setPriceCents] = useState(1990);
  const [formats, setFormats] = useState<string[]>(["ebook"]);
  const [artigos, setArtigos] = useState(3);
  const [funil, setFunil] = useState<{ enabled: boolean; upsell: string; downsell: string }>({
    enabled: false,
    upsell: "",
    downsell: "",
  });
  const [creating, setCreating] = useState(false);
  const [notice, setNotice] = useState<{ ok: boolean; msg: string } | null>(null);
  const [blueprints, setBlueprints] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const loadList = async () => {
    try {
      const res = await fetch(`${API_URL}/api/v1/blueprints`, { headers: authHeaders() });
      const data = await res.json();
      setBlueprints(data.blueprints || []);
    } catch (err) {
      console.error("Erro ao listar blueprints:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadList();
    const t = setInterval(loadList, 5000);
    return () => clearInterval(t);
  }, []);

  const toggleFormat = (id: string) => {
    setFormats((prev) => (prev.includes(id) ? prev.filter((f) => f !== id) : [...prev, id]));
  };

  const createBlueprint = async (e: React.FormEvent) => {
    e.preventDefault();
    if (formats.length === 0) {
      setNotice({ ok: false, msg: "Selecione pelo menos um formato." });
      return;
    }
    setCreating(true);
    setNotice(null);
    try {
      const config: Record<string, any> = {
        artigos: Number(artigos) || 3,
        template_landing: "dezafira",
      };
      if (funil.enabled) {
        config.funil = {
          order_bump: null,
          upsell: funil.upsell.trim()
            ? { name: funil.upsell.trim(), price_cents: Math.round((Number(priceCents) || 0) * 0.6), slug: "" }
            : null,
          downsell: funil.downsell.trim()
            ? { name: funil.downsell.trim(), price_cents: Math.round((Number(priceCents) || 0) * 0.4), slug: "" }
            : null,
        };
      }
      const res = await fetch(`${API_URL}/api/v1/blueprints`, {
        method: "POST",
        headers: authHeaders({ "Content-Type": "application/json" }),
        body: JSON.stringify({
          name: theme,
          theme,
          niche,
          price_cents: Number(priceCents) || 0,
          formats,
          config,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Erro ao criar blueprint");
      setNotice({ ok: true, msg: `✅ Blueprint criado: ${data.id}` });
      setTheme("");
      loadList();
    } catch (err: any) {
      setNotice({ ok: false, msg: err.message || "Erro ao criar" });
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="min-h-screen" style={{ background: "var(--bg)", color: "var(--text)" }}>
      <header className="border-b" style={{ borderColor: "var(--border)", background: "var(--bg-deep)" }}>
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link href="/admin" className="text-sm" style={{ color: "var(--text-dim)" }}>← Voltar ao Admin</Link>
            <span style={{ color: "var(--border)" }}>/</span>
            <h1 className="text-lg font-bold" style={{ color: "var(--brand)" }}>🎯 Blueprint de Produto</h1>
          </div>
          <span className="badge" style={{ color: "var(--success)" }}>🟢 Tema + nicho → produto completo</span>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-8 space-y-8">
        {notice && (
          <div
            className="rounded-2xl p-4 text-sm"
            style={{
              background: notice.ok ? "rgba(34,197,94,0.1)" : "rgba(239,68,68,0.1)",
              border: `1px solid ${notice.ok ? "rgba(34,197,94,0.4)" : "rgba(239,68,68,0.4)"}`,
              color: notice.ok ? "#4ade80" : "#f87171",
            }}
          >
            {notice.msg}
          </div>
        )}

        {/* Criar receita */}
        <div className="rounded-2xl p-6 shadow-xl space-y-5" style={{ background: "var(--surface)", border: "1px solid var(--border)" }}>
          <div>
            <h2 className="text-xl font-extrabold text-white">🧪 Criar nova receita</h2>
            <p className="text-xs mt-1" style={{ color: "var(--text-dim)" }}>
              A IA gera tudo: produto, blog, banners, landing, funil e área de membros. Você revisa as imagens antes de publicar.
            </p>
          </div>

          <form onSubmit={createBlueprint} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="md:col-span-2">
                <label className="block text-xs font-bold mb-1" style={{ color: "var(--text-dim)" }}>TEMA / PRODUTO</label>
                <input
                  type="text"
                  value={theme}
                  onChange={(e) => setTheme(e.target.value)}
                  placeholder="Ex: Guia Definitivo de Emagrecimento com IA"
                  className="w-full input"
                  required
                />
              </div>
              <div>
                <label className="block text-xs font-bold mb-1" style={{ color: "var(--text-dim)" }}>NICHO</label>
                <select value={niche} onChange={(e) => setNiche(e.target.value)} className="w-full input">
                  {NICHE_OPTIONS.map((n) => (
                    <option key={n} value={n}>{n}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-bold mb-1" style={{ color: "var(--text-dim)" }}>PREÇO (CENTAVOS)</label>
                <input
                  type="number"
                  value={priceCents}
                  onChange={(e) => setPriceCents(Number(e.target.value))}
                  className="w-full input"
                />
              </div>
              <div>
                <label className="block text-xs font-bold mb-1" style={{ color: "var(--text-dim)" }}>Nº DE ARTIGOS (BLOG)</label>
                <input
                  type="number"
                  min={0}
                  max={10}
                  value={artigos}
                  onChange={(e) => setArtigos(Number(e.target.value))}
                  className="w-full input"
                />
              </div>
              <div>
                <label className="block text-xs font-bold mb-1" style={{ color: "var(--text-dim)" }}>TEMPLATE DE LANDING</label>
                <select className="w-full input" defaultValue="dezafira">
                  <option value="dezafira">Dezafira (padrão)</option>
                </select>
              </div>
            </div>

            {/* Formatos */}
            <div>
              <label className="block text-xs font-bold mb-2" style={{ color: "var(--text-dim)" }}>FORMATOS DA RECEITA</label>
              <div className="flex flex-wrap gap-2">
                {FORMAT_OPTIONS.map((f) => {
                  const active = formats.includes(f.id);
                  return (
                    <button
                      key={f.id}
                      type="button"
                      onClick={() => toggleFormat(f.id)}
                      className="px-4 py-2 rounded-xl text-sm font-bold transition-all"
                      style={{
                        background: active ? "var(--brand)" : "var(--surface2)",
                        color: active ? "#fff" : "var(--text-dim)",
                        border: `1px solid ${active ? "var(--brand)" : "var(--border)"}`,
                      }}
                    >
                      {f.icon} {f.label}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Funil (MVP: bump/upsell/downsell) */}
            <div className="rounded-xl p-4" style={{ background: "var(--surface2)", border: "1px solid var(--border)" }}>
              <label className="flex items-center gap-2 text-sm font-bold text-white">
                <input
                  type="checkbox"
                  checked={funil.enabled}
                  onChange={(e) => setFunil((p) => ({ ...p, enabled: e.target.checked }))}
                />
                🎯 Criar esteira de ofertas (upsell + downsell pós-compra)
              </label>
              {funil.enabled && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-3">
                  <input
                    type="text"
                    value={funil.upsell}
                    onChange={(e) => setFunil((p) => ({ ...p, upsell: e.target.value }))}
                    placeholder="Produto de upsell (ex: Mentoria de 30 dias)"
                    className="w-full input"
                  />
                  <input
                    type="text"
                    value={funil.downsell}
                    onChange={(e) => setFunil((p) => ({ ...p, downsell: e.target.value }))}
                    placeholder="Produto de downsell (ex: Guia Rápido)"
                    className="w-full input"
                  />
                </div>
              )}
            </div>

            <button
              type="submit"
              disabled={creating}
              className="w-full text-white font-extrabold py-3.5 rounded-xl text-sm shadow-lg hover:brightness-110 disabled:opacity-50 transition-all"
              style={{ background: "linear-gradient(90deg, var(--brand), #c2410c)" }}
            >
              {creating ? "Criando…" : "🧪 Criar Blueprint e Gerar Tudo"}
            </button>
          </form>
        </div>

        {/* Lista */}
        <div className="rounded-2xl p-6 shadow-xl" style={{ background: "var(--surface)", border: "1px solid var(--border)" }}>
          <div className="flex items-center justify-between mb-5">
            <h2 className="text-lg font-bold text-white">📦 Blueprints ({blueprints.length})</h2>
            <button onClick={loadList} className="btn-secondary text-xs">🔄 Atualizar</button>
          </div>

          {loading ? (
            <p className="text-sm" style={{ color: "var(--text-dim)" }}>Carregando…</p>
          ) : blueprints.length === 0 ? (
            <p className="text-sm" style={{ color: "var(--text-dim)" }}>
              Nenhum blueprint ainda. Crie a primeira receita acima. 🚀
            </p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {blueprints.map((bp) => {
                const st = STATUS_LABEL[bp.status] || { label: bp.status, color: "var(--text-dim)" };
                const stageLabel = (bp.stage || "").replace("_", " ");
                return (
                  <Link
                    key={bp.id}
                    href={`/admin/blueprint/${bp.id}`}
                    className="rounded-xl p-4 transition-all hover:scale-[1.01] block"
                    style={{ background: "var(--surface2)", border: "1px solid var(--border)" }}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <h3 className="text-sm font-bold text-white line-clamp-1">{bp.theme}</h3>
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded-full whitespace-nowrap ml-2" style={{ background: "rgba(245,158,11,0.15)", color: st.color }}>
                        {st.label}
                      </span>
                    </div>
                    <p className="text-xs mb-2" style={{ color: "var(--text-dim)" }}>
                      {bp.niche} · {(bp.formats || []).join(" + ")}
                    </p>
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-mono" style={{ color: "var(--brand)" }}>
                        {(Number(bp.price_cents) || 0) > 0 ? `R$ ${(Number(bp.price_cents) / 100).toFixed(2)}` : "Grátis"}
                      </span>
                      <span className="text-[10px]" style={{ color: "var(--text-dim)" }}>
                        {stageLabel || "—"}
                      </span>
                    </div>
                  </Link>
                );
              })}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
