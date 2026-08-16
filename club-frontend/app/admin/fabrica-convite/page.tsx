"use client";

export const dynamic = "force-dynamic";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "https://dezafiraadm-production.up.railway.app";

type Blueprint = {
  id: string;
  name: string;
  price_cents: number;
  status: string;
  stage: string;
  created_at?: string;
};

export default function FabricaConvitePage() {
  const [nome, setNome] = useState("1Convite — Super App do Reino");
  const [tagline, setTagline] = useState("Um APP sobre o Reino: Bíblia narrada, matriz diária e arcade bíblico");
  const [descricao, setDescricao] = useState("Super app cristão com Bíblia ACF completa narrada, matriz diária de 365 dias, arcade bíblico, Trilha do Reino e conselheiros IA.");
  const [preco, setPreco] = useState("1990");
  const [dominio, setDominio] = useState("1convite.com.br");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ type: "ok" | "err"; text: string } | null>(null);
  const [asaas, setAsaas] = useState<any>(null);
  const [miniapp, setMiniapp] = useState<any>(null);
  const [blueprints, setBlueprints] = useState<Blueprint[]>([]);

  const loadStatus = useCallback(async () => {
    try {
      const [asaasRes, miniRes, bpRes] = await Promise.all([
        fetch(`${API_URL}/api/v1/asaas/status`),
        fetch(`${API_URL}/api/v1/miniapps`),
        fetch(`${API_URL}/api/v1/convite/factory/blueprints`).catch(() => null),
      ]);
      if (asaasRes.ok) setAsaas(await asaasRes.json());
      if (miniRes.ok) {
        const d = await miniRes.json();
        const apps = d.miniapps || [];
        setMiniapp(apps.find((a: any) => (a.slug || "").toLowerCase() === "1convite" || (a.app_name || "").toLowerCase().includes("convite")) || null);
      }
      if (bpRes && bpRes.ok) {
        const d = await bpRes.json();
        setBlueprints(d.blueprints || d.items || []);
      }
    } catch (err) {
      console.error("Erro ao carregar status:", err);
    }
  }, []);

  useEffect(() => {
    loadStatus();
  }, [loadStatus]);

  const show = (type: "ok" | "err", text: string) => setMessage({ type, text });

  const handleBlueprint = async () => {
    setLoading(true);
    setMessage(null);
    try {
      const res = await fetch(`${API_URL}/api/v1/convite/factory/blueprint`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          nome,
          tagline,
          descricao,
          preco_cents: parseInt(preco || "0", 10) || 0,
          dominio_dedicado: dominio,
        }),
      });
      const data = await res.json();
      if (data.success) {
        show("ok", `Blueprint criado: ${data.blueprint?.id} — app_url ${data.app_url}`);
        loadStatus();
      } else {
        show("err", data.error || "Falha ao criar blueprint");
      }
    } catch (e: any) {
      show("err", String(e?.message || e));
    } finally {
      setLoading(false);
    }
  };

  const handlePublish = async (bpId: string) => {
    if (!confirm(`Publicar o blueprint ${bpId} no DezafiraClube?`)) return;
    setLoading(true);
    setMessage(null);
    try {
      const res = await fetch(`${API_URL}/api/v1/convite/factory/publish/${bpId}`, { method: "POST" });
      const data = await res.json();
      show(data.status === "published" ? "ok" : "err", `Publish: ${data.status} — veja o log do blueprint`);
      loadStatus();
    } catch (e: any) {
      show("err", String(e?.message || e));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: 24, fontFamily: "Inter, system-ui, sans-serif" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
        <div>
          <h1 style={{ margin: 0, fontSize: 24, fontWeight: 800 }}>🏭 Fábrica de Convites</h1>
          <p style={{ margin: "4px 0 0", color: "#64748b", fontSize: 13 }}>
            1Convite — Super App do Reino → branding → blueprint → Clube (venda + checkout Asaas)
          </p>
        </div>
        <Link href="/admin" style={{ color: "#0f3460", fontSize: 13 }}>← Voltar</Link>
      </div>

      {/* Status cards */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px,1fr))", gap: 12, marginBottom: 20 }}>
        <StatusCard label="Miniapp 1Convite" value={miniapp ? "✅ registrado" : "—"} detail={miniapp ? `slug: ${miniapp.slug || miniapp.id}` : "não encontrado"} />
        <StatusCard label="Domínio dedicado" value={dominio} detail={miniapp ? "servido na raiz do domínio" : "aguardando registro"} />
        <StatusCard label="Asaas (venda)" value={asaas?.success ? "✅ conectado" : asaas?.configured ? "⚠️ erro" : "—"} detail={asaas?.account?.email ? `conta: ${asaas.account.email}` : asaas?.message || "sem ASAAS_API_KEY"} />
        <StatusCard label="Blueprints" value={String(blueprints.length)} detail="produtos da fábrica" />
      </div>

      {message && (
        <div style={{ padding: "10px 14px", borderRadius: 8, marginBottom: 16, fontSize: 13, background: message.type === "ok" ? "#dcfce7" : "#fee2e2", color: message.type === "ok" ? "#166534" : "#991b1b" }}>
          {message.text}
        </div>
      )}

      {/* Branding form */}
      <div style={{ background: "#fff", border: "1px solid #e2e8f0", borderRadius: 12, padding: 20, marginBottom: 20 }}>
        <h2 style={{ margin: "0 0 14px", fontSize: 16, fontWeight: 700 }}>🎨 Branding do produto</h2>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
          <Field label="Nome do produto"><input value={nome} onChange={(e) => setNome(e.target.value)} style={inp} /></Field>
          <Field label="Domínio dedicado"><input value={dominio} onChange={(e) => setDominio(e.target.value)} style={inp} /></Field>
          <Field label="Tagline" span={2}><input value={tagline} onChange={(e) => setTagline(e.target.value)} style={inp} /></Field>
          <Field label="Descrição (vendas)" span={2}><textarea value={descricao} onChange={(e) => setDescricao(e.target.value)} rows={3} style={inp} /></Field>
          <Field label="Preço (centavos — R$ 19,90 = 1990)"><input value={preco} onChange={(e) => setPreco(e.target.value)} style={inp} /></Field>
        </div>
        <button onClick={handleBlueprint} disabled={loading} style={btnPrimary}>
          {loading ? "Processando..." : "Criar Blueprint da Oferta"}
        </button>
      </div>

      {/* Blueprints */}
      <div style={{ background: "#fff", border: "1px solid #e2e8f0", borderRadius: 12, padding: 20 }}>
        <h2 style={{ margin: "0 0 14px", fontSize: 16, fontWeight: 700 }}>📦 Blueprints do 1Convite</h2>
        {blueprints.length === 0 && <p style={{ color: "#94a3b8", fontSize: 13 }}>Nenhum blueprint ainda — crie acima.</p>}
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
          <thead>
            <tr style={{ textAlign: "left", color: "#64748b" }}>
              <th style={{ padding: "6px 8px" }}>ID</th>
              <th>Nome</th>
              <th>Preço</th>
              <th>Status</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {blueprints.map((bp) => (
              <tr key={bp.id} style={{ borderTop: "1px solid #f1f5f9" }}>
                <td style={{ padding: "8px" }}>{bp.id}</td>
                <td>{bp.name}</td>
                <td>R$ {(bp.price_cents / 100).toFixed(2)}</td>
                <td>
                  <span style={{ background: bp.status === "published" ? "#dcfce7" : bp.status === "review" ? "#fef9c3" : "#fee2e2", padding: "2px 8px", borderRadius: 999, fontSize: 12 }}>
                    {bp.status}
                  </span>
                </td>
                <td>
                  {bp.status !== "published" && (
                    <button onClick={() => handlePublish(bp.id)} disabled={loading} style={btnSmall}>
                      Publicar no Clube
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function StatusCard({ label, value, detail }: { label: string; value: string; detail?: string }) {
  return (
    <div style={{ background: "#fff", border: "1px solid #e2e8f0", borderRadius: 12, padding: 14 }}>
      <div style={{ fontSize: 12, color: "#64748b", fontWeight: 600 }}>{label}</div>
      <div style={{ fontSize: 16, fontWeight: 800, margin: "4px 0 2px" }}>{value}</div>
      {detail && <div style={{ fontSize: 11, color: "#94a3b8" }}>{detail}</div>}
    </div>
  );
}

function Field({ label, span, children }: { label: string; span?: number; children: React.ReactNode }) {
  return (
    <label style={{ gridColumn: span ? `span ${span}` : undefined, display: "flex", flexDirection: "column", gap: 4, fontSize: 12, fontWeight: 600, color: "#334155" }}>
      {label}
      {children}
    </label>
  );
}

const inp: React.CSSProperties = {
  padding: "8px 10px", border: "1px solid #cbd5e1", borderRadius: 8, fontSize: 13,
  fontFamily: "inherit", outline: "none",
};
const btnPrimary: React.CSSProperties = {
  marginTop: 16, background: "#0f3460", color: "#fff", border: "none", borderRadius: 8,
  padding: "10px 18px", fontWeight: 700, fontSize: 14, cursor: "pointer",
};
const btnSmall: React.CSSProperties = {
  background: "#d4af37", color: "#14141f", border: "none", borderRadius: 6,
  padding: "5px 10px", fontWeight: 700, fontSize: 12, cursor: "pointer",
};
