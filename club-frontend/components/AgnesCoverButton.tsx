"use client";

import { useState } from "react";

/**
 * 🎨 AgnesCoverButton — gera/regenera a capa de um produto (curso/ebook/post)
 * via Agnes Studio (design editorial: tipografia + autor + créditos), com
 * seletor de estilo visual e preview da capa gerada.
 *
 * Uso nas fábricas (fabrica-curso / fabrica-ebook / fabrica-blog):
 *   <AgnesCoverButton entityType="course" entityId={c.id} onDone={loadData} />
 */

const AGNES_STYLES = [
  { id: "moderno", label: "Moderno" },
  { id: "elegante", label: "Elegante" },
  { id: "tech", label: "Tech" },
  { id: "minimal", label: "Minimal" },
  { id: "dark-gold", label: "Dark Gold" },
];

const ENDPOINTS: Record<string, string> = {
  course: "/api/v1/courses",
  ebook: "/api/v1/ebooks",
  post: "/api/v1/blog/post",
};

function authHeaders(extra: Record<string, string> = {}): Record<string, string> {
  const token = typeof window !== "undefined" ? localStorage.getItem("dz_token") : "";
  return token ? { Authorization: `Bearer ${token}`, ...extra } : extra;
}

/** Brand kit global (localStorage) — enviado junto com o style_id nas capas. */
function readBrandKit(): any {
  try {
    const raw = typeof window !== "undefined" ? localStorage.getItem("dz_brand_kit") : null;
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export default function AgnesCoverButton({
  entityType,
  entityId,
  onDone,
}: {
  entityType: "course" | "ebook" | "post";
  entityId: string;
  onDone?: () => void;
}) {
  const [style, setStyle] = useState("moderno");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [preview, setPreview] = useState<{
    url: string;
    width?: number;
    height?: number;
  } | null>(null);

  const generate = async () => {
    setBusy(true);
    setError(null);
    try {
      const body: any = { style_id: style };
      const brandKit = readBrandKit();
      if (brandKit) body.brand_kit = brandKit;
      const res = await fetch(`${ENDPOINTS[entityType]}/${entityId}/agnes-cover`, {
        method: "POST",
        headers: authHeaders({ "Content-Type": "application/json" }),
        body: JSON.stringify(body),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
      setPreview({ url: data.cover_url, width: data.width, height: data.height });
      onDone?.();
    } catch (err: any) {
      setError(err.message || "Erro ao gerar capa");
    } finally {
      setBusy(false);
    }
  };

  const dims =
    preview?.width && preview?.height ? `${preview.width} × ${preview.height}px` : null;

  return (
    <div className="flex items-center gap-2 flex-wrap">
      <select
        value={style}
        onChange={(e) => setStyle(e.target.value)}
        disabled={busy}
        className="text-[10px] px-2 py-1.5 rounded"
        style={{ background: "var(--surface2)", border: "1px solid var(--border)", color: "var(--text)" }}
        title="Estilo visual da capa (Agnes Studio)"
      >
        {AGNES_STYLES.map((s) => (
          <option key={s.id} value={s.id}>
            {s.label}
          </option>
        ))}
      </select>
      <button
        type="button"
        onClick={generate}
        disabled={busy}
        className="text-[11px] font-bold px-3 py-1.5 rounded"
        style={{ background: "var(--brand)", color: "var(--ink)" }}
        title="Capa editorial com tipografia + autor + créditos"
      >
        {busy ? "…" : "🖌️ Capa Agnes"}
      </button>

      {preview && (
        <div className="flex items-center gap-2">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={preview.url}
            alt="Capa Agnes gerada"
            className="h-10 w-auto rounded border"
            style={{ borderColor: "var(--border)", objectFit: "contain" }}
          />
          {dims && (
            <span className="text-[9px] font-mono" style={{ color: "var(--text-dim)" }}>
              {dims}
            </span>
          )}
        </div>
      )}

      {error && (
        <span className="text-[10px]" style={{ color: "#f87171" }}>
          ❌ {error}
        </span>
      )}
    </div>
  );
}
