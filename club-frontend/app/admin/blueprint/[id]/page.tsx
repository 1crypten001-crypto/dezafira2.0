"use client";

export const dynamic = "force-dynamic";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import AssetSlot from "../../../../components/AssetSlot";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const STAGES = [
  { id: "fundacao", label: "🧠 Fundação" },
  { id: "conteudo", label: "📦 Conteúdo" },
  { id: "assets", label: "🎨 Assets" },
  { id: "landing", label: "🚀 Landing" },
  { id: "funil", label: "🎯 Funil" },
  { id: "revisao", label: "👀 Revisão" },
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

export default function BlueprintDetailPage() {
  const params = useParams<{ id: string }>();
  const bpId = params.id;
  const [bp, setBp] = useState<any>(null);
  const [notice, setNotice] = useState<{ ok: boolean; msg: string } | null>(null);
  const [busy, setBusy] = useState(false);
  const firstLoad = useRef(true);
  const [brandKit, setBrandKit] = useState<any>(null);
  const [brandKitSaved, setBrandKitSaved] = useState(false);
  const [cfgDraft, setCfgDraft] = useState<any>(null);
  const [cfgSaved, setCfgSaved] = useState(false);

  const load = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/api/v1/blueprints/${bpId}`, { headers: authHeaders() });
      if (!res.ok) throw new Error("HTTP " + res.status);
      setBp(await res.json());
    } catch (err) {
      console.error("Erro ao carregar blueprint:", err);
    }
  }, [bpId]);

  useEffect(() => {
    load();
    const t = setInterval(() => {
      load();
    }, 3000);
    return () => clearInterval(t);
  }, [load]);

  // Dispara a geração automaticamente na primeira abertura (se draft)
  // Só marca o firstLoad quando bp já carregou (senão o run nunca dispara).
  useEffect(() => {
    if (!bp || !firstLoad.current) return;
    firstLoad.current = false;
    if (bp.status === "draft") {
      run(`/api/v1/blueprints/${bpId}/run`);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [bp]);

  const run = async (path: string, body?: any) => {
    setBusy(true);
    setNotice(null);
    try {
      const res = await fetch(path, {
        method: "POST",
        headers: authHeaders({ "Content-Type": "application/json" }),
        body: body ? JSON.stringify(body) : undefined,
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
      setNotice({ ok: true, msg: "✅ OK" });
      load();
    } catch (err: any) {
      setNotice({ ok: false, msg: err.message || "Erro" });
    } finally {
      setBusy(false);
    }
  };

  const publish = () => {
    if (!confirm("Publicar este blueprint no DezafiraClube? (cria produto, blog, landing e funil)")) return;
    run(`/api/v1/blueprints/${bpId}/publish`);
  };

  const saveConfig = async () => {
    setBusy(true);
    setNotice(null);
    try {
      const cur = bp.config || {};
      const d = cfgDraft || {};
      const res = await fetch(`${API_URL}/api/v1/blueprints/${bpId}`, {
        method: "PATCH",
        headers: authHeaders({ "Content-Type": "application/json" }),
        body: JSON.stringify({
          config: {
            template_landing: d.template_landing ?? cur.template_landing ?? "dezafira",
            funil: {
              ...(cur.funil || {}),
              bundle: d.bundle ?? cur.funil?.bundle ?? { enabled: false, discount_pct: 30 },
            },
            vsl: d.vsl ?? cur.vsl ?? { enabled: false, video_url: "" },
          },
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
      setCfgSaved(true);
      setNotice({ ok: true, msg: "✅ Configuração salva — landing, combo e VSL usam esses valores" });
      load();
    } catch (err: any) {
      setNotice({ ok: false, msg: err.message || "Erro ao salvar configuração" });
    } finally {
      setBusy(false);
    }
  };

  const saveBrandKit = async () => {
    setBusy(true);
    setNotice(null);
    try {
      const res = await fetch(`${API_URL}/api/v1/blueprints/${bpId}`, {
        method: "PATCH",
        headers: authHeaders({ "Content-Type": "application/json" }),
        // Salva no formato canônico { colors: {bg, bg2, accent, text, muted}, font, font_sans }
        // (o motor/Agnes Studio lê brand_kit.colors.*)
        body: JSON.stringify({ config: { brand_kit: { ...bk, colors: { ...bk.colors } } } }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
      setBrandKitSaved(true);
      setNotice({ ok: true, msg: "✅ Brand kit salvo — as capas Agnes Studio usam essas cores/fontes" });
    } catch (err: any) {
      setNotice({ ok: false, msg: err.message || "Erro ao salvar brand kit" });
    } finally {
      setBusy(false);
    }
  };

  if (!bp) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: "var(--bg)", color: "var(--text)" }}>
        Carregando…
      </div>
    );
  }

  const st = STATUS_LABEL[bp.status] || { label: bp.status, color: "var(--text-dim)" };
  const stageIdx = Math.max(0, STAGES.findIndex((s) => s.id === bp.stage));
  const fund = bp.content?.fundacao || {};
  const funil = bp.content?.funil || {};
  const publishLog = bp.publish_log || {};
  const assets = bp.assets || {};
  const slots = (bp.content?.assets?.slots) || [];
  const artifacts = bp.content?.conteudo?.artifacts || [];
  // Normaliza o brand kit: aceita tanto o formato aninhado { colors: {bg, bg2, accent, text, muted} }
  // quanto o formato plano { primary_color, accent_color } (usado pela API/seed).
  const rawBk: any = brandKit || bp.config?.brand_kit || {};
  const flatColors = rawBk.colors || {};
  const bk = {
    colors: {
      bg: flatColors.bg || rawBk.accent_color || rawBk.primary_color || "#0f1a21",
      bg2: flatColors.bg2 || rawBk.accent_color || "#0f1a21",
      accent: flatColors.accent || rawBk.primary_color || "#FF5B06",
      text: flatColors.text || "#ffffff",
      muted: flatColors.muted || "#94a3b8",
    },
    font: rawBk.font || "",
    font_sans: rawBk.font_sans || "",
  };
  const canPublish = bp.status === "review" || bp.status === "published" || bp.status === "failed";

  return (
    <div className="min-h-screen" style={{ background: "var(--bg)", color: "var(--text)" }}>
      <header className="border-b" style={{ borderColor: "var(--border)", background: "var(--bg-deep)" }}>
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link href="/admin/blueprint" className="text-sm" style={{ color: "var(--text-dim)" }}>← Blueprints</Link>
            <span style={{ color: "var(--border)" }}>/</span>
            <h1 className="text-lg font-bold text-white line-clamp-1">{bp.theme}</h1>
          </div>
          <span className="badge" style={{ color: st.color }}>{st.label}</span>
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

        {/* Estágios */}
        <div className="rounded-2xl p-6 shadow-xl" style={{ background: "var(--surface)", border: "1px solid var(--border)" }}>
          <h2 className="text-lg font-bold text-white mb-4">🛠️ Estágios do motor</h2>
          <div className="flex flex-wrap gap-2">
            {STAGES.map((s, i) => {
              const done = i < stageIdx || (i === stageIdx && (bp.status === "review" || bp.status === "publishing" || bp.status === "published"));
              const active = i === stageIdx && bp.status === "generating";
              return (
                <div
                  key={s.id}
                  className="px-3 py-2 rounded-xl text-xs font-bold"
                  style={{
                    background: done ? "rgba(34,197,94,0.12)" : active ? "rgba(96,165,250,0.15)" : "var(--surface2)",
                    border: `1px solid ${done ? "rgba(34,197,94,0.4)" : active ? "rgba(96,165,250,0.4)" : "var(--border)"}`,
                    color: done ? "#4ade80" : active ? "#60a5fa" : "var(--text-dim)",
                  }}
                >
                  {s.label} {done ? "✓" : active ? "…" : ""}
                </div>
              );
            })}
          </div>
        </div>

        {/* Fundação */}
        <div className="rounded-2xl p-6 shadow-xl" style={{ background: "var(--surface)", border: "1px solid var(--border)" }}>
          <h2 className="text-lg font-bold text-white mb-3">🧠 Fundação gerada</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
            <div><span style={{ color: "var(--text-dim)" }}>Nome:</span> <b className="text-white">{fund.name || "—"}</b></div>
            <div><span style={{ color: "var(--text-dim)" }}>Slug:</span> <b className="text-white">{fund.slug || "—"}</b></div>
            <div className="md:col-span-2"><span style={{ color: "var(--text-dim)" }}>Descrição:</span> <span className="text-white">{fund.description || "—"}</span></div>
            <div className="md:col-span-2"><span style={{ color: "var(--text-dim)" }}>Pitch:</span> <span className="text-white">{fund.pitch || "—"}</span></div>
            <div><span style={{ color: "var(--text-dim)" }}>CTA:</span> <span className="text-white">{fund.cta_primary || "—"}</span></div>
            <div><span style={{ color: "var(--text-dim)" }}>Preço:</span> <span className="text-white font-mono">{(Number(bp.price_cents) || 0) > 0 ? `R$ ${(Number(bp.price_cents) / 100).toFixed(2)}` : "Grátis"}</span></div>
          </div>
          {funil?.upsell && (
            <p className="text-xs mt-3" style={{ color: "var(--text-dim)" }}>
              🎯 Upsell: <b className="text-white">{funil.upsell.name}</b>
              {funil?.downsell ? ` · Downsell: ${funil.downsell.name}` : ""}
            </p>
          )}
          {artifacts.length > 0 && (
            <div className="mt-4 space-y-1">
              {artifacts.map((a: any, i: number) => (
                <div key={i} className="text-xs flex items-center justify-between rounded-lg px-3 py-2" style={{ background: "var(--surface2)", border: "1px solid var(--border)" }}>
                  <span className="text-white">{a.title || a.format}</span>
                  <span style={{ color: a.status === "completed" ? "#4ade80" : "#f87171" }}>
                    {a.status === "completed" ? "✅ pronto" : a.status === "failed" ? `❌ ${a.error || "falhou"}` : a.status}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Brand kit (cores/fontes das capas Agnes Studio) */}
        <div className="rounded-2xl p-6 shadow-xl" style={{ background: "var(--surface)", border: "1px solid var(--border)" }}>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-bold text-white">🎨 Brand kit (capas Agnes Studio)</h2>
            <button
              onClick={saveBrandKit}
              disabled={busy}
              className="btn-primary text-xs px-4 py-2 rounded-lg"
              style={{ background: brandKitSaved ? "rgba(34,197,94,0.2)" : "var(--brand)", color: brandKitSaved ? "#4ade80" : "var(--ink)" }}
            >
              {brandKitSaved ? "✓ Salvo" : "💾 Salvar brand kit"}
            </button>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
            {[
              ["bg", "Fundo"], ["bg2", "Fundo 2"], ["accent", "Destaque"], ["text", "Texto"], ["muted", "Texto suave"],
            ].map(([key, label]) => (
              <div key={key}>
                <label className="block text-[10px] font-bold mb-1" style={{ color: "var(--text-dim)" }}>{label}</label>
                <input
                  type="color"
                  value={(bk.colors as any)[key] || "#0f172a"}
                  onChange={(e) =>
                    setBrandKit((prev: any) => {
                      const cur = prev || { colors: {} };
                      return { ...cur, colors: { ...(cur.colors || {}), [key]: e.target.value } };
                    })
                  }
                  className="w-full h-9 rounded border cursor-pointer"
                  style={{ background: "var(--surface2)", borderColor: "var(--border)" }}
                />
              </div>
            ))}
            {[
              ["font", "Fonte (títulos)"], ["font_sans", "Fonte (texto)"],
            ].map(([key, label]) => (
              <div key={key}>
                <label className="block text-[10px] font-bold mb-1" style={{ color: "var(--text-dim)" }}>{label}</label>
                <input
                  type="text"
                  value={(bk as any)[key] || ""}
                  placeholder="ex: Georgia, serif"
                  onChange={(e) => setBrandKit((prev: any) => ({ ...(prev || { colors: {} }), [key]: e.target.value }))}
                  className="w-full p-2 rounded border text-xs"
                  style={{ background: "var(--surface2)", borderColor: "var(--border)", color: "var(--text)" }}
                />
              </div>
            ))}
          </div>
          <p className="text-[10px] mt-3" style={{ color: "var(--text-dim)" }}>
            🖌️ Usado pelo Agnes Studio nas capas editoriais (🖌️ Capa Agnes). Deixe vazio para usar o estilo padrão.
          </p>
        </div>

        {/* Configuração: template de landing + combo/pacote + VSL */}
        <div className="rounded-2xl p-6 shadow-xl" style={{ background: "var(--surface)", border: "1px solid var(--border)" }}>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-bold text-white">⚙️ Configuração (landing · combo · VSL)</h2>
            <button
              onClick={saveConfig}
              disabled={busy}
              className="btn-primary text-xs px-4 py-2 rounded-lg"
              style={{ background: cfgSaved ? "rgba(34,197,94,0.2)" : "var(--brand)", color: cfgSaved ? "#4ade80" : "var(--ink)" }}
            >
              {cfgSaved ? "✓ Salvo" : "💾 Salvar configuração"}
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {/* Template de landing */}
            <div>
              <label className="block text-[10px] font-bold mb-1" style={{ color: "var(--text-dim)" }}>🚀 Template de landing</label>
              <select
                value={(cfgDraft?.template_landing ?? bp.config?.template_landing) || "dezafira"}
                onChange={(e) => setCfgDraft((p: any) => ({ ...(p || {}), template_landing: e.target.value }))}
                className="w-full p-2 rounded border text-xs"
                style={{ background: "var(--surface2)", borderColor: "var(--border)", color: "var(--text)" }}
              >
                <option value="dezafira">Dezafira (padrão)</option>
                <option value="dark-sales">Dark Sales (urgência)</option>
                <option value="clean-soft">Clean Soft (claro)</option>
              </select>
              <p className="text-[9px] mt-1" style={{ color: "var(--text-dim)" }}>
                Usa os blocos do Clube (hero → oferta → prova → FAQ → CTA) com o brand kit já injetado.
              </p>
            </div>

            {/* Combo/pacote */}
            <div>
              <label className="block text-[10px] font-bold mb-1" style={{ color: "var(--text-dim)" }}>📦 Combo/pacote nativo (fase 2)</label>
              <label className="flex items-center gap-2 text-xs mb-2" style={{ color: "var(--text)" }}>
                <input
                  type="checkbox"
                  checked={Boolean(cfgDraft?.bundle?.enabled ?? bp.config?.funil?.bundle?.enabled)}
                  onChange={(e) =>
                    setCfgDraft((p: any) => {
                      const cur = p?.bundle ?? bp.config?.funil?.bundle ?? { enabled: false, discount_pct: 30, include_upsell: true, include_downsell: true };
                      return { ...(p || {}), bundle: { ...cur, enabled: e.target.checked } };
                    })
                  }
                />
                Criar produto "Pacote" (soma dos preços com desconto)
              </label>
              <div className="flex items-center gap-2 mb-2">
                <span className="text-[10px]" style={{ color: "var(--text-dim)" }}>Desconto %</span>
                <input
                  type="number"
                  min={0}
                  max={90}
                  value={cfgDraft?.bundle?.discount_pct ?? bp.config?.funil?.bundle?.discount_pct ?? 30}
                  onChange={(e) =>
                    setCfgDraft((p: any) => {
                      const cur = p?.bundle ?? bp.config?.funil?.bundle ?? { enabled: false, include_upsell: true, include_downsell: true };
                      return { ...(p || {}), bundle: { ...cur, discount_pct: Number(e.target.value) || 0 } };
                    })
                  }
                  className="w-20 p-1.5 rounded border text-xs"
                  style={{ background: "var(--surface2)", borderColor: "var(--border)", color: "var(--text)" }}
                />
              </div>
              <label className="flex items-center gap-2 text-[11px] mb-1" style={{ color: "var(--text-dim)" }}>
                <input
                  type="checkbox"
                  checked={Boolean(cfgDraft?.bundle?.include_upsell ?? bp.config?.funil?.bundle?.include_upsell ?? true)}
                  onChange={(e) =>
                    setCfgDraft((p: any) => {
                      const cur = p?.bundle ?? bp.config?.funil?.bundle ?? { enabled: false, discount_pct: 30, include_downsell: true };
                      return { ...(p || {}), bundle: { ...cur, include_upsell: e.target.checked } };
                    })
                  }
                />
                Incluir upsell
              </label>
              <label className="flex items-center gap-2 text-[11px]" style={{ color: "var(--text-dim)" }}>
                <input
                  type="checkbox"
                  checked={Boolean(cfgDraft?.bundle?.include_downsell ?? bp.config?.funil?.bundle?.include_downsell ?? true)}
                  onChange={(e) =>
                    setCfgDraft((p: any) => {
                      const cur = p?.bundle ?? bp.config?.funil?.bundle ?? { enabled: false, discount_pct: 30, include_upsell: true };
                      return { ...(p || {}), bundle: { ...cur, include_downsell: e.target.checked } };
                    })
                  }
                />
                Incluir downsell
              </label>
              {bp.publish_log?.bundle?.status === "ok" && (
                <p className="text-[9px] mt-2" style={{ color: "var(--success)" }}>
                  ✅ Combo publicado: {bp.publish_log.bundle.detail}
                </p>
              )}
            </div>

            {/* VSL */}
            <div>
              <label className="block text-[10px] font-bold mb-1" style={{ color: "var(--text-dim)" }}>🎬 VSL (roteiro + headlines)</label>
              <label className="flex items-center gap-2 text-xs mb-2" style={{ color: "var(--text)" }}>
                <input
                  type="checkbox"
                  checked={Boolean(cfgDraft?.vsl?.enabled ?? bp.config?.vsl?.enabled)}
                  onChange={(e) =>
                    setCfgDraft((p: any) => {
                      const cur = p?.vsl ?? bp.config?.vsl ?? { enabled: false, video_url: "" };
                      return { ...(p || {}), vsl: { ...cur, enabled: e.target.checked } };
                    })
                  }
                />
                Gerar VSL no motor (script completo + headlines A/B/C)
              </label>
              <input
                type="text"
                placeholder="URL do vídeo (opcional — ex: YouTube)"
                value={cfgDraft?.vsl?.video_url ?? bp.config?.vsl?.video_url ?? ""}
                onChange={(e) =>
                  setCfgDraft((p: any) => {
                    const cur = p?.vsl ?? bp.config?.vsl ?? { enabled: false };
                    return { ...(p || {}), vsl: { ...cur, video_url: e.target.value } };
                  })
                }
                className="w-full p-2 rounded border text-xs mb-1"
                style={{ background: "var(--surface2)", borderColor: "var(--border)", color: "var(--text)" }}
              />
              {bp.content?.vsl?.generated && (
                <div className="text-[9px] mt-1 space-y-0.5" style={{ color: "var(--text-dim)" }}>
                  <p style={{ color: "var(--success)" }}>✅ VSL gerada (id {bp.content.vsl.vsl_id})</p>
                  <p className="line-clamp-2">📝 {bp.content.vsl.script?.slice(0, 140)}…</p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Assets com AssetSlot */}
        <div className="rounded-2xl p-6 shadow-xl" style={{ background: "var(--surface)", border: "1px solid var(--border)" }}>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-bold text-white">🖼️ Assets de imagem ({slots.length})</h2>
            <span className="text-[10px]" style={{ color: "var(--text-dim)" }}>
              Clique na imagem para ver em tamanho real com dimensões
            </span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {slots.map((slot: any) => (
              <AssetSlot
                key={slot.key}
                apiBase={API_URL}
                bpId={bpId}
                slotKey={slot.key}
                label={slot.label}
                asset={assets[slot.key]}
                onChanged={load}
              />
            ))}
          </div>
        </div>

        {/* Publicação */}
        <div className="rounded-2xl p-6 shadow-xl" style={{ background: "var(--surface)", border: "1px solid var(--border)" }}>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-bold text-white">🚀 Publicação no DezafiraClube</h2>
            <button
              onClick={publish}
              disabled={busy || !canPublish}
              className="btn-primary text-sm px-5 py-2.5"
              style={busy || !canPublish ? { opacity: 0.5 } : undefined}
            >
              {busy ? "Processando…" : bp.status === "published" ? "↻ Republicar" : "🚀 Publicar no Clube"}
            </button>
          </div>
          {bp.status === "draft" && (
            <p className="text-xs mb-3" style={{ color: "var(--text-dim)" }}>
              ⚡ A geração é disparada automaticamente ao abrir o blueprint. Aguarde o estágio "Revisão".
            </p>
          )}
          {Object.keys(publishLog).length > 0 && (
            <div className="space-y-1.5">
              {Object.entries(publishLog).map(([step, entry]: [string, any]) => (
                <div
                  key={step}
                  className="flex items-center justify-between rounded-lg px-3 py-2 text-xs"
                  style={{
                    background: "var(--surface2)",
                    border: "1px solid var(--border)",
                    color: entry.status === "ok" ? "#4ade80" : entry.status === "failed" ? "#f87171" : "var(--text-dim)",
                  }}
                >
                  <span className="font-bold capitalize">{step}</span>
                  <span className="ml-3 text-right" style={{ color: "var(--text-dim)" }}>{entry.detail}</span>
                </div>
              ))}
            </div>
          )}
          {bp.status === "published" && bp.publish_log?.produto?.slug && (
            <p className="text-xs mt-3">
              🔗 <a className="underline" style={{ color: "var(--brand)" }} href={`https://www.dezafira.com.br/product/${bp.publish_log.produto.slug}`} target="_blank" rel="noreferrer">
                Ver produto no Clube
              </a>
              {bp.publish_log?.landing?.public_url && (
                <>
                  {" · "}
                  <a className="underline" style={{ color: "var(--brand)" }} href={`https://www.dezafira.com.br${bp.publish_log.landing.public_url}`} target="_blank" rel="noreferrer">
                    Ver landing
                  </a>
                </>
              )}
            </p>
          )}
        </div>
      </main>
    </div>
  );
}
