"use client";

import { useRef, useState } from "react";

type Asset = {
  url?: string;
  super_prompt?: string;
  provider?: string;
  source?: string;
  width?: number;
  height?: number;
  agnes_style?: string;
  error?: string;
  video?: boolean; // true → renderiza <video> em vez de <img>
  duration?: string;
  history?: any[]; // versões anteriores (diff/restaurar)
};

const PROVIDER_LABEL: Record<string, string> = {
  agnes: "🎨 Agnes AI",
  "agnes-studio": "🖌️ Agnes Studio",
  gemini: "🎨 Gemini",
  openrouter: "🔥 FLUX OpenRouter",
  flux: "🤖 FLUX Pollinations",
  pexels: "🖼️ Pexels",
  unsplash: "🖼️ Unsplash",
  placeholder: "🎭 Placeholder",
  upload: "📤 Upload manual",
  error: "❌ Erro",
};

const AGNES_STYLES = ["moderno", "elegante", "tech", "minimal", "dark-gold"];

function authHeaders(extra: Record<string, string> = {}): Record<string, string> {
  const token = typeof window !== "undefined" ? localStorage.getItem("dz_token") : "";
  return token ? { Authorization: `Bearer ${token}`, ...extra } : extra;
}

export default function AssetSlot({
  apiBase,
  bpId,
  slotKey,
  label,
  asset,
  onChanged,
}: {
  apiBase: string;
  bpId: string;
  slotKey: string;
  label: string;
  asset?: Asset;
  onChanged?: () => void;
}) {
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState<{ ok: boolean; msg: string } | null>(null);
  const [zoom, setZoom] = useState(false);
  const [agnesStyle, setAgnesStyle] = useState("moderno");
  const [variants, setVariants] = useState<any[] | null>(null);
  const [showVariants, setShowVariants] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [compareIdx, setCompareIdx] = useState<number | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const hasImage = !!asset?.url;
  const history = asset?.history || [];

  // URLs locais (/outputs/...) são servidas pelo backend — resolve contra o apiBase
  const src = (u?: string) => (u && u.startsWith("/outputs/") ? `${apiBase}${u}` : u || "");

  const run = async (path: string, body: any) => {
    setBusy(true);
    setNotice(null);
    try {
      const res = await fetch(`${apiBase}${path}`, {
        method: "POST",
        headers: authHeaders({ "Content-Type": "application/json" }),
        body: JSON.stringify(body),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
      setNotice({ ok: true, msg: "✅ Atualizado" });
      onChanged?.();
    } catch (err: any) {
      setNotice({ ok: false, msg: err.message || "Erro" });
    } finally {
      setBusy(false);
    }
  };

  const regenerate = () => run(`/api/v1/blueprints/${bpId}/assets/regenerate`, { slot: slotKey });

  const agnesCover = () =>
    run(`/api/v1/blueprints/${bpId}/assets/agnes-cover`, { slot: slotKey, style_id: agnesStyle });

  const loadVariants = async () => {
    setBusy(true);
    setNotice(null);
    try {
      const res = await fetch(`${apiBase}/api/v1/blueprints/${bpId}/assets/agnes-variants`, {
        method: "POST",
        headers: authHeaders({ "Content-Type": "application/json" }),
        body: JSON.stringify({ slot: slotKey, styles: AGNES_STYLES }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
      setVariants(data.variants || []);
      setShowVariants(true);
    } catch (err: any) {
      setNotice({ ok: false, msg: err.message || "Erro ao gerar variantes" });
    } finally {
      setBusy(false);
    }
  };

  const applyVariant = async (v: any) => {
    setBusy(true);
    setNotice(null);
    try {
      const res = await fetch(`${apiBase}/api/v1/blueprints/${bpId}/assets/agnes-apply-variant`, {
        method: "POST",
        headers: authHeaders({ "Content-Type": "application/json" }),
        body: JSON.stringify({ slot: slotKey, filename: v.filename, style_id: v.style_id }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
      setNotice({ ok: true, msg: `✅ Variante ${v.style_id} aplicada` });
      setShowVariants(false);
      setVariants(null);
      onChanged?.();
    } catch (err: any) {
      setNotice({ ok: false, msg: err.message || "Erro" });
    } finally {
      setBusy(false);
    }
  };

  const onFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      const dataUrl = String(reader.result || "");
      run(`/api/v1/blueprints/${bpId}/assets/upload`, { slot: slotKey, data_url: dataUrl });
    };
    reader.readAsDataURL(file);
    e.target.value = "";
  };

  const copyPrompt = async () => {
    try {
      await navigator.clipboard.writeText(asset?.super_prompt || "");
      setNotice({ ok: true, msg: "📋 Prompt copiado!" });
    } catch {
      setNotice({ ok: false, msg: "Não foi possível copiar" });
    }
  };

  const provider = asset?.provider || "";
  const dims =
    asset?.width && asset?.height ? `${asset.width} × ${asset.height}px` : null;

  return (
    <div
      className="rounded-xl p-4 transition-all"
      style={{ background: "var(--surface2)", border: "1px solid var(--border)" }}
    >
      <div className="flex items-start justify-between mb-2 gap-2">
        <h4 className="text-xs font-bold text-white">{label}</h4>
        {provider && (
          <span
            className="text-[9px] font-bold px-2 py-0.5 rounded-full whitespace-nowrap"
            style={{ background: "rgba(139,92,246,0.15)", color: "var(--brand)" }}
          >
            {PROVIDER_LABEL[provider] || provider}
          </span>
        )}
      </div>

      {/* Miniatura (clique → zoom em imagens; vídeo é player direto) */}
      <button
        type="button"
        onClick={() => hasImage && !asset?.video && setZoom(true)}
        disabled={!hasImage || busy}
        className="w-full rounded-lg overflow-hidden mb-2 group"
        style={{
          background: "var(--surface)",
          border: "1px solid var(--border)",
          aspectRatio: "16/9",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          cursor: hasImage && !asset?.video ? "zoom-in" : "default",
        }}
        title={hasImage ? "Clique para ampliar" : "Sem imagem ainda"}
      >
        {hasImage ? (
          asset?.video ? (
            <video
              src={src(asset.url)}
              muted
              loop
              playsInline
              className="w-full h-full object-cover"
            />
          ) : (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={src(asset.url)}
              alt={label}
              className="w-full h-full object-cover group-hover:opacity-90 transition-opacity"
            />
          )
        ) : (
          <span className="text-[10px]" style={{ color: "var(--text-dim)" }}>
            {asset?.error ? "❌ falha ao gerar" : "⏳ aguardando…"}
          </span>
        )}
      </button>

      {/* Ações */}
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={regenerate}
          disabled={busy || asset?.source === "upload"}
          className="btn-secondary text-[10px] px-2.5 py-1.5 flex-1"
          title={asset?.source === "upload" ? "Imagem enviada por upload" : "Gerar nova (seed)"}
        >
          {busy ? "…" : "🔄 Regenerar"}
        </button>
        <button
          type="button"
          onClick={() => fileRef.current?.click()}
          disabled={busy}
          className="btn-primary text-[10px] px-2.5 py-1.5 flex-1"
        >
          📤 Upload
        </button>
        <input ref={fileRef} type="file" accept="image/*" className="hidden" onChange={onFile} />
      </div>

      {/* Capa editorial Agnes Studio (alternativa à imagem por prompt) */}
      <div className="mt-2 flex items-center gap-2">
        <select
          value={agnesStyle}
          onChange={(e) => setAgnesStyle(e.target.value)}
          disabled={busy || asset?.source === "upload"}
          className="text-[10px] px-2 py-1.5 rounded"
          style={{ background: "var(--surface)", border: "1px solid var(--border)", color: "var(--text)" }}
        >
          {AGNES_STYLES.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
        <button
          type="button"
          onClick={agnesCover}
          disabled={busy || asset?.source === "upload"}
          className="btn-secondary text-[10px] px-2.5 py-1.5 flex-1"
          title="Capa editorial com tipografia + autor + créditos (Agnes Studio)"
        >
          🖌️ Capa Agnes
        </button>
        <button
          type="button"
          onClick={loadVariants}
          disabled={busy || asset?.source === "upload"}
          className="btn-secondary text-[10px] px-2.5 py-1.5"
          title="Comparar variantes de estilo lado a lado antes de aplicar"
        >
          🎛️ Variantes
        </button>
      </div>

      {/* Histórico de versões (diff antes/depois) */}
      <div className="mt-2 flex items-center justify-between gap-2">
        <button
          type="button"
          onClick={() => { setCompareIdx(null); setShowHistory(true); }}
          disabled={busy || history.length === 0}
          className="btn-secondary text-[10px] px-2.5 py-1.5 flex-1"
          title={history.length ? `Histórico com ${history.length} versão(ões) anterior(es)` : "Sem versões anteriores ainda"}
        >
          🕘 Histórico {history.length > 0 ? `(${history.length})` : ""}
        </button>
        {hasImage && history.length > 0 && (
          <span className="text-[9px]" style={{ color: "var(--text-dim)" }}>
            clique numa versão p/ comparar
          </span>
        )}
      </div>

      {/* Super prompt (sempre visível) */}
      <div
        className="mt-2 rounded-lg p-2 text-[9px] leading-relaxed"
        style={{ background: "var(--surface)", border: "1px dashed var(--border)", color: "var(--text-dim)" }}
      >
        <div className="flex items-center justify-between mb-1">
          <span className="font-bold" style={{ color: "var(--brand)" }}>✨ Super prompt</span>
          <button type="button" onClick={copyPrompt} className="text-[9px] underline">
            📋 copiar
          </button>
        </div>
        <p className="line-clamp-3">{asset?.super_prompt || "—"}</p>
      </div>

      {notice && (
        <p className="text-[10px] mt-1" style={{ color: notice.ok ? "var(--success)" : "#f87171" }}>
          {notice.msg}
        </p>
      )}

      {/* Modal de variantes (comparador lado a lado) */}
      {showVariants && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
          style={{ background: "rgba(0,0,0,0.85)" }}
          onClick={() => setShowVariants(false)}
        >
          <div
            className="max-w-5xl w-full rounded-2xl p-5"
            style={{ background: "var(--surface)", border: "1px solid var(--border)" }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-4">
              <h4 className="text-sm font-bold text-white">🎨 Variantes de {label}</h4>
              <button
                type="button"
                onClick={() => setShowVariants(false)}
                className="text-sm px-2.5 py-1 rounded-lg"
                style={{ background: "var(--surface2)", color: "var(--text-dim)" }}
              >
                ✕ Fechar
              </button>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
              {variants?.map((v: any) => (
                <button
                  key={v.style_id}
                  type="button"
                  onClick={() => applyVariant(v)}
                  disabled={busy}
                  className="rounded-xl overflow-hidden group text-left"
                  style={{ background: "var(--surface2)", border: "1px solid var(--border)" }}
                  title={`Aplicar estilo ${v.style_id}`}
                >
                  <div style={{ aspectRatio: "16/9", background: "#000" }}>
                    {v.error ? (
                      <div className="w-full h-full flex items-center justify-center text-[9px] p-2" style={{ color: "#f87171" }}>
                        ❌ {v.error}
                      </div>
                    ) : (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img
                        src={`${apiBase}${v.cover_url}`}
                        alt={v.style_id}
                        className="w-full h-full object-cover group-hover:opacity-80 transition-opacity"
                      />
                    )}
                  </div>
                  <div className="px-2 py-1.5 text-[10px] font-bold" style={{ color: "var(--brand)" }}>
                    {v.style_id} {v.width ? `· ${v.width}×${v.height}` : ""}
                  </div>
                </button>
              ))}
            </div>
            <p className="text-[10px] mt-3" style={{ color: "var(--text-dim)" }}>
              Clique numa variante para aplicá-la ao slot (não regenera — usa o arquivo já gerado).
            </p>
          </div>
        </div>
      )}

      {/* Modal de histórico: grid de versões + comparador antes/depois + restaurar */}
      {showHistory && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
          style={{ background: "rgba(0,0,0,0.85)" }}
          onClick={() => setShowHistory(false)}
        >
          <div
            className="max-w-5xl w-full rounded-2xl p-5"
            style={{ background: "var(--surface)", border: "1px solid var(--border)" }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-4">
              <h4 className="text-sm font-bold text-white">🕘 Histórico de {label}</h4>
              <button
                type="button"
                onClick={() => setShowHistory(false)}
                className="text-sm px-2.5 py-1 rounded-lg"
                style={{ background: "var(--surface2)", color: "var(--text-dim)" }}
              >
                ✕ Fechar
              </button>
            </div>

            {compareIdx === null ? (
              <>
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                  {history.map((v: any, i: number) => (
                    <button
                      key={i}
                      type="button"
                      onClick={() => setCompareIdx(i)}
                      className="rounded-xl overflow-hidden group text-left"
                      style={{ background: "var(--surface2)", border: "1px solid var(--border)" }}
                      title="Clique para comparar com a versão atual"
                    >
                      <div style={{ aspectRatio: "16/9", background: "#000" }}>
                        {/* eslint-disable-next-line @next/next/no-img-element */}
                        <img
                          src={src(v.url)}
                          alt={`versão ${i + 1}`}
                          className="w-full h-full object-cover group-hover:opacity-80 transition-opacity"
                        />
                      </div>
                      <div className="px-2 py-1.5 text-[9px]" style={{ color: "var(--text-dim)" }}>
                        <span className="font-bold" style={{ color: "var(--brand)" }}>
                          #{i + 1}
                        </span>{" "}
                        {v.width && v.height ? `${v.width}×${v.height} · ` : ""}
                        {v.agnes_style || v.provider || ""}{" "}
                        {v.ts ? `· ${new Date(v.ts).toLocaleString("pt-BR")}` : ""}
                      </div>
                    </button>
                  ))}
                </div>
                <p className="text-[10px] mt-3" style={{ color: "var(--text-dim)" }}>
                  Clique numa versão para comparar lado a lado com a atual e restaurar.
                </p>
              </>
            ) : (
              <>
                <div className="grid grid-cols-2 gap-4">
                  {/* Versão atual */}
                  <div className="rounded-xl overflow-hidden" style={{ background: "var(--surface2)", border: "1px solid var(--border)" }}>
                    <div className="px-3 py-2 text-[10px] font-bold flex items-center justify-between" style={{ color: "var(--brand)" }}>
                      <span>📌 Versão atual</span>
                      <span className="text-[9px]" style={{ color: "var(--text-dim)" }}>
                        {asset?.width && asset?.height ? `${asset.width}×${asset.height}` : ""}{" "}
                        {asset?.agnes_style || asset?.provider || ""}
                      </span>
                    </div>
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src={src(asset?.url)} alt="atual" className="w-full object-contain" style={{ maxHeight: "40vh", background: "#000" }} />
                  </div>
                  {/* Versão selecionada */}
                  <div className="rounded-xl overflow-hidden" style={{ background: "var(--surface2)", border: "1px solid var(--border)" }}>
                    <div className="px-3 py-2 text-[10px] font-bold flex items-center justify-between" style={{ color: "var(--text-dim)" }}>
                      <span>🕘 Versão #{compareIdx + 1}</span>
                      <span className="text-[9px]">
                        {history[compareIdx]?.width && history[compareIdx]?.height ? `${history[compareIdx].width}×${history[compareIdx].height}` : ""}{" "}
                        {history[compareIdx]?.agnes_style || history[compareIdx]?.provider || ""}
                      </span>
                    </div>
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src={src(history[compareIdx]?.url)} alt={`versão ${compareIdx + 1}`} className="w-full object-contain" style={{ maxHeight: "40vh", background: "#000" }} />
                  </div>
                </div>
                <div className="flex items-center justify-between mt-4 gap-3">
                  <button
                    type="button"
                    onClick={() => setCompareIdx(null)}
                    className="btn-secondary text-[10px] px-3 py-1.5"
                  >
                    ← Voltar à lista
                  </button>
                  <button
                    type="button"
                    disabled={busy}
                    onClick={() =>
                      run(`/api/v1/blueprints/${bpId}/assets/restore`, { slot: slotKey, index: compareIdx })
                    }
                    className="btn-primary text-[10px] px-3 py-1.5"
                  >
                    {busy ? "…" : "↩️ Restaurar esta versão"}
                  </button>
                </div>
                <p className="text-[10px] mt-3" style={{ color: "var(--text-dim)" }}>
                  Ao restaurar, a versão atual volta para o histórico (nada é perdido).
                </p>
              </>
            )}
          </div>
        </div>
      )}

      {/* Modal de zoom: imagem em tamanho real + dimensões */}
      {zoom && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
          style={{ background: "rgba(0,0,0,0.85)" }}
          onClick={() => setZoom(false)}
        >
          <div
            className="max-w-4xl w-full rounded-2xl p-5"
            style={{ background: "var(--surface)", border: "1px solid var(--border)" }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-3">
              <h4 className="text-sm font-bold text-white">{label}</h4>
              <button
                type="button"
                onClick={() => setZoom(false)}
                className="text-sm px-2.5 py-1 rounded-lg"
                style={{ background: "var(--surface2)", color: "var(--text-dim)" }}
              >
                ✕ Fechar
              </button>
            </div>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={src(asset?.url)}
              alt={label}
              className="w-full rounded-xl"
              style={{ maxHeight: "70vh", objectFit: "contain", background: "#000" }}
            />
            <div className="flex flex-wrap items-center gap-3 mt-3 text-[11px]" style={{ color: "var(--text-dim)" }}>
              <span className="font-mono font-bold" style={{ color: "var(--brand)" }}>
                {dims || "dimensões desconhecidas"}
              </span>
              {provider && <span>{PROVIDER_LABEL[provider] || provider}</span>}
              {asset?.source === "upload" ? (
                <span>🖼️ Fonte: upload manual</span>
              ) : (
                <span>🤖 Fonte: gerada por IA</span>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
