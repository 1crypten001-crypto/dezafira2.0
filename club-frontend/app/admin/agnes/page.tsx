"use client";

export const dynamic = "force-dynamic";

import { useCallback, useEffect, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type GalleryImage = {
  filename: string;
  url: string;
  entity_type: string;
  entity_id: string;
  title: string;
  size: number;
  created_at: string;
};

function authHeaders(extra: Record<string, string> = {}): Record<string, string> {
  const token = typeof window !== "undefined" ? localStorage.getItem("dz_token") : "";
  return token ? { Authorization: `Bearer ${token}`, ...extra } : extra;
}

function fmtBytes(n: number): string {
  if (!n) return "";
  if (n > 1024 * 1024) return `${(n / 1024 / 1024).toFixed(1)} MB`;
  return `${Math.max(1, Math.round(n / 1024))} KB`;
}

const ENTITY_LABEL: Record<string, string> = {
  course: "🎓 Curso",
  ebook: "📗 Ebook",
  post: "✍️ Artigo",
};

export default function AgnesGalleryPage() {
  const [images, setImages] = useState<GalleryImage[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<{ ok: boolean; msg: string } | null>(null);
  const [busy, setBusy] = useState(false);
  const [zoom, setZoom] = useState<GalleryImage | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_URL}/api/v1/agnes/gallery`, { headers: authHeaders() });
      if (!res.ok) throw new Error("HTTP " + res.status);
      const data = await res.json();
      setImages(data.images || []);
    } catch (err: any) {
      setError(err.message || "Erro ao carregar galeria");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const apply = async (img: GalleryImage) => {
    if (!img.entity_type || !img.entity_id) {
      setNotice({ ok: false, msg: "Capa sem produto de origem resolvido — aplique via fábrica do produto." });
      return;
    }
    if (!confirm(`Aplicar "${img.title}" como capa do ${ENTITY_LABEL[img.entity_type] || img.entity_type}?`)) return;
    setBusy(true);
    setNotice(null);
    try {
      const res = await fetch(`${API_URL}/api/v1/agnes/use-cover`, {
        method: "POST",
        headers: authHeaders({ "Content-Type": "application/json" }),
        body: JSON.stringify({ entity_type: img.entity_type, entity_id: img.entity_id, filename: img.filename }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
      setNotice({ ok: true, msg: `✅ Aplicada em ${ENTITY_LABEL[img.entity_type]}: ${img.title}` });
    } catch (err: any) {
      setNotice({ ok: false, msg: err.message || "Erro" });
    } finally {
      setBusy(false);
    }
  };

  const remove = async (img: GalleryImage) => {
    if (!confirm(`Remover ${img.filename} da galeria?`)) return;
    setBusy(true);
    setNotice(null);
    try {
      const res = await fetch(`${API_URL}/api/v1/agnes/gallery/${encodeURIComponent(img.filename)}`, {
        method: "DELETE",
        headers: authHeaders(),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
      setNotice({ ok: true, msg: "🗑️ Capa removida" });
      setImages((prev) => prev.filter((i) => i.filename !== img.filename));
      setZoom(null);
    } catch (err: any) {
      setNotice({ ok: false, msg: err.message || "Erro" });
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="min-h-screen p-6" style={{ background: "var(--bg)", color: "var(--text)" }}>
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold">🖼️ Galeria Agnes Studio</h1>
            <p className="text-sm mt-1" style={{ color: "var(--text-dim)" }}>
              Capas com design editorial (tipografia + autor + créditos) geradas em outputs/agnes
            </p>
          </div>
          <button onClick={load} className="px-4 py-2 rounded-lg text-sm" style={{ background: "var(--surface)", border: "1px solid var(--border)" }}>
            🔄 Atualizar
          </button>
        </div>

        {notice && (
          <div className="mb-4 p-3 rounded-lg text-sm" style={{ background: notice.ok ? "var(--surface)" : "var(--error)", color: notice.ok ? "var(--success)" : "var(--ink)", border: "1px solid var(--border)" }}>
            {notice.msg}
          </div>
        )}

        {loading ? (
          <p style={{ color: "var(--text-dim)" }}>Carregando…</p>
        ) : error ? (
          <div className="p-6 rounded-xl" style={{ background: "var(--error)", color: "var(--ink)" }}>{error}</div>
        ) : images.length === 0 ? (
          <div className="p-10 rounded-2xl text-center" style={{ background: "var(--surface)", border: "1px dashed var(--border)" }}>
            <p className="text-lg mb-2">Nenhuma capa gerada ainda 🎨</p>
            <p className="text-sm" style={{ color: "var(--text-dim)" }}>
              Use o botão 🖌️ Capa Agnes nas fábricas de curso/ebook/blog ou no Blueprint.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {images.map((img) => (
              <div key={img.filename} className="rounded-xl overflow-hidden" style={{ background: "var(--surface)", border: "1px solid var(--border)" }}>
                <button
                  type="button"
                  onClick={() => setZoom(img)}
                  className="w-full block"
                  title="Clique para ampliar"
                  style={{ aspectRatio: "16/9", background: "#000" }}
                >
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={`${API_URL}${img.url}`} alt={img.title} className="w-full h-full object-cover" />
                </button>
                <div className="p-3">
                  <p className="text-xs font-bold line-clamp-1">{img.title}</p>
                  <p className="text-[9px] mt-1" style={{ color: "var(--text-dim)" }}>
                    {ENTITY_LABEL[img.entity_type] || "🖌️ Agnes Studio"} · {fmtBytes(img.size)}
                    {img.created_at ? ` · ${img.created_at}` : ""}
                  </p>
                  <div className="flex gap-2 mt-2">
                    <button
                      type="button"
                      onClick={() => apply(img)}
                      disabled={busy || !img.entity_type}
                      className="flex-1 text-[10px] font-bold px-2 py-1.5 rounded"
                      style={{ background: "var(--brand)", color: "var(--ink)" }}
                      title={img.entity_type ? `Aplicar em ${ENTITY_LABEL[img.entity_type]}` : "Sem produto de origem"}
                    >
                      Aplicar
                    </button>
                    <button
                      type="button"
                      onClick={() => remove(img)}
                      disabled={busy}
                      className="text-[10px] px-2 py-1.5 rounded"
                      style={{ background: "var(--surface2)", border: "1px solid var(--border)", color: "var(--text-dim)" }}
                    >
                      🗑
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Zoom modal */}
      {zoom && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
          style={{ background: "rgba(0,0,0,0.88)" }}
          onClick={() => setZoom(null)}
        >
          <div
            className="max-w-4xl w-full rounded-2xl p-5"
            style={{ background: "var(--surface)", border: "1px solid var(--border)" }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-3">
              <div>
                <h4 className="text-sm font-bold text-white">{zoom.title}</h4>
                <p className="text-[10px] font-mono" style={{ color: "var(--text-dim)" }}>{zoom.filename}</p>
              </div>
              <button
                type="button"
                onClick={() => setZoom(null)}
                className="text-sm px-2.5 py-1 rounded-lg"
                style={{ background: "var(--surface2)", color: "var(--text-dim)" }}
              >
                ✕ Fechar
              </button>
            </div>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={`${API_URL}${zoom.url}`}
              alt={zoom.title}
              className="w-full rounded-xl"
              style={{ maxHeight: "70vh", objectFit: "contain", background: "#000" }}
            />
            <div className="flex flex-wrap items-center gap-3 mt-3 text-[11px]" style={{ color: "var(--text-dim)" }}>
              <span className="font-mono font-bold" style={{ color: "var(--brand)" }}>{fmtBytes(zoom.size)}</span>
              <span>{ENTITY_LABEL[zoom.entity_type] || "🖌️ Agnes Studio"}</span>
              <span>{zoom.created_at}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
