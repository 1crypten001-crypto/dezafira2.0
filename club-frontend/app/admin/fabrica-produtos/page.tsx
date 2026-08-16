"use client";

export const dynamic = "force-dynamic";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

/**
 * Fábrica de Produtos foi substituída pelo 🎯 Blueprint de Produto
 * (/admin/blueprint), que gera o produto completo (blog, banners, landing,
 * funil, área de membros) a partir de tema + nicho.
 */
export default function FabricaProdutosRedirectPage() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/admin/blueprint");
  }, [router]);

  return (
    <div className="min-h-screen flex items-center justify-center" style={{ background: "var(--bg)", color: "var(--text)" }}>
      <div className="text-center">
        <div className="text-3xl mb-3">🎯</div>
        <p className="text-sm" style={{ color: "var(--text-dim)" }}>
          Redirecionando para o Blueprint de Produto…
        </p>
      </div>
    </div>
  );
}
