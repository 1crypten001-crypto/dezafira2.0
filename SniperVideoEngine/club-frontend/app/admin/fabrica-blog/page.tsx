"use client";
import { useEffect, useState } from "react";
import { useAuth } from "../../../lib/auth-context";
import { useRouter } from "next/navigation";
import { api } from "../../../lib/api";

export default function FabricaBlogPage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  const [panelUrl, setPanelUrl] = useState("");

  useEffect(() => {
    if (!authLoading && (!user || user.role !== "admin")) {
      router.push("/painel");
    }
  }, [user, authLoading]);

  useEffect(() => {
    if (user?.role === "admin") {
      const token = api.getToken();
      const base = process.env.NEXT_PUBLIC_API_URL || "";
      const origin = base.replace(/\/api\/v1\/?$/, "");
      setPanelUrl(`${origin}/?token=${encodeURIComponent(token || "")}#blogs`);
    }
  }, [user]);

  if (authLoading || !user || !panelUrl) {
    return <div className="min-h-screen flex items-center justify-center text-[var(--text-dim)]">Carregando...</div>;
  }

  return (
    <div className="min-h-screen">
      <header className="border-b border-[var(--border)] bg-[var(--surface)]">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <span className="text-xl font-bold">Fabrica de Blogs</span>
            <span className="badge text-[var(--warning)]">Admin</span>
          </div>
          <a href="/admin" className="text-sm text-[var(--text-dim)] hover:text-[var(--text)]">← Voltar</a>
        </div>
      </header>
      <iframe
        src={panelUrl}
        className="w-full"
        style={{ height: "calc(100vh - 60px)", border: "none" }}
        title="Fabrica de Blogs"
      />
    </div>
  );
}
