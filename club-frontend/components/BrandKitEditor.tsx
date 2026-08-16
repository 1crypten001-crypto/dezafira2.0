"use client";

import { useEffect, useState } from "react";

/**
 * 🎨 BrandKitEditor — editor global do brand kit (cores/fontes) das capas
 * Agnes Studio nas fábricas. Persiste em localStorage (`dz_brand_kit`) e é
 * lido automaticamente pelo AgnesCoverButton (enviado no body das capas).
 */
const DEFAULT_KIT = { colors: {} };

const COLOR_FIELDS: [string, string][] = [
  ["bg", "Fundo"],
  ["bg2", "Fundo 2"],
  ["accent", "Destaque"],
  ["text", "Texto"],
  ["muted", "Texto suave"],
];

function readKit(): any {
  try {
    const raw = typeof window !== "undefined" ? localStorage.getItem("dz_brand_kit") : null;
    return raw ? JSON.parse(raw) : { ...DEFAULT_KIT };
  } catch {
    return { ...DEFAULT_KIT };
  }
}

export default function BrandKitEditor() {
  const [open, setOpen] = useState(false);
  const [kit, setKit] = useState<any>(readKit);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    const onStorage = () => setKit(readKit());
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, []);

  const setColor = (key: string, value: string) => {
    setKit((prev: any) => {
      const next = { ...prev, colors: { ...(prev.colors || {}), [key]: value } };
      localStorage.setItem("dz_brand_kit", JSON.stringify(next));
      setSaved(true);
      setTimeout(() => setSaved(false), 1500);
      return next;
    });
  };

  const setFont = (key: string, value: string) => {
    setKit((prev: any) => {
      const next = { ...prev, [key]: value };
      localStorage.setItem("dz_brand_kit", JSON.stringify(next));
      setSaved(true);
      setTimeout(() => setSaved(false), 1500);
      return next;
    });
  };

  const clear = () => {
    localStorage.removeItem("dz_brand_kit");
    setKit({ ...DEFAULT_KIT });
    setSaved(true);
    setTimeout(() => setSaved(false), 1500);
  };

  const colors = kit.colors || {};

  return (
    <div className="mb-4 rounded-xl p-4" style={{ background: "var(--surface)", border: "1px solid var(--border)" }}>
      <div className="flex items-center justify-between">
        <button
          type="button"
          onClick={() => setOpen(!open)}
          className="text-sm font-bold"
          style={{ color: "var(--text)" }}
        >
          🎨 Brand kit das capas Agnes {saved && <span style={{ color: "var(--success)" }}>✓ salvo</span>}
        </button>
        <div className="flex items-center gap-2">
          {open && (
            <button
              type="button"
              onClick={clear}
              className="text-[10px] px-2 py-1 rounded"
              style={{ background: "var(--surface2)", border: "1px solid var(--border)", color: "var(--text-dim)" }}
            >
              Limpar
            </button>
          )}
          <span className="text-[10px]" style={{ color: "var(--text-dim)" }}>{open ? "▲" : "▼"}</span>
        </div>
      </div>

      {open && (
        <div className="mt-3">
          <div className="grid grid-cols-3 md:grid-cols-5 gap-3">
            {COLOR_FIELDS.map(([key, label]) => (
              <div key={key}>
                <label className="block text-[10px] font-bold mb-1" style={{ color: "var(--text-dim)" }}>{label}</label>
                <input
                  type="color"
                  value={colors[key] || "#0f172a"}
                  onChange={(e) => setColor(key, e.target.value)}
                  className="w-full h-8 rounded border cursor-pointer"
                  style={{ background: "var(--surface2)", borderColor: "var(--border)" }}
                />
              </div>
            ))}
            {[
              ["font", "Fonte (títulos)"],
              ["font_sans", "Fonte (texto)"],
            ].map(([key, label]) => (
              <div key={key}>
                <label className="block text-[10px] font-bold mb-1" style={{ color: "var(--text-dim)" }}>{label}</label>
                <input
                  type="text"
                  value={kit[key] || ""}
                  placeholder="ex: Georgia, serif"
                  onChange={(e) => setFont(key, e.target.value)}
                  className="w-full p-2 rounded border text-[10px]"
                  style={{ background: "var(--surface2)", borderColor: "var(--border)", color: "var(--text)" }}
                />
              </div>
            ))}
          </div>
          <p className="text-[10px] mt-2" style={{ color: "var(--text-dim)" }}>
            Aplicado automaticamente nas capas geradas aqui (🖌️ Capa Agnes). Salvo neste navegador.
          </p>
        </div>
      )}
    </div>
  );
}
