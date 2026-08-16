"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useAuth } from "../../lib/auth-context";

const NAV_SECTIONS: { title: string; items: { label: string; href: string; icon: string }[] }[] = [
  {
    title: "Visão Geral",
    items: [{ label: "Dashboard", href: "/admin", icon: "▦" }],
  },
  {
    title: "Canais & Nichos",
    items: [{ label: "Hub de Canais", href: "/admin/canais", icon: "◉" }],
  },
  {
    title: "Fábricas",
    items: [
      { label: "Blog", href: "/admin/fabrica-blog", icon: "✎" },
      { label: "Ebook", href: "/admin/fabrica-ebook", icon: "❐" },
      { label: "Curso", href: "/admin/fabrica-curso", icon: "▣" },
      { label: "Blueprint", href: "/admin/blueprint", icon: "🎯" },
      { label: "Ofertas", href: "/admin/fabrica-ofertas", icon: "🏷️" },
      { label: "Capas Agnes", href: "/admin/agnes", icon: "🖼️" },
      { label: "VSL", href: "/admin/fabrica-vsl", icon: "🎬" },
      { label: "Bio Sites", href: "/admin/fabrica-biosites", icon: "🔗" },
    ],
  },
  {
    title: "Serviços de PWA",
    items: [
      { label: "Mapas Mentais", href: "/admin/fabrica-mapas", icon: "⌘" },
      { label: "MiniApps", href: "/admin/fabrica-miniapp", icon: "▤" },
      { label: "1Convite", href: "/admin/fabrica-convite", icon: "👑" },
    ],
  },
  {
    title: "Distribuição",
    items: [{ label: "Postiz", href: "/admin", icon: "⇶" }],
  },
  {
    title: "Inteligência",
    items: [
      { label: "Hermes", href: "/admin#hermes", icon: "✦" },
      { label: "AionUi", href: "http://127.0.0.1:25809", icon: "⊕" },
    ],
  },
  {
    title: "Público",
    items: [
      { label: "Usuários", href: "/admin/analytics", icon: "♟" },
      { label: "Trilhas", href: "/admin/trilhas", icon: "≡" },
      { label: "Analytics", href: "/admin/analytics", icon: "≋" },
    ],
  },
];

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, loading, logout } = useAuth();
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (!loading && (!user || user.role !== "admin")) {
      router.push("/painel");
    }
  }, [user, loading, router]);

  useEffect(() => {
    setOpen(false);
  }, [pathname]);

  const isActive = (href: string) => {
    if (href === "/admin") return pathname === "/admin";
    if (href.includes("#")) {
      // Âncora: ativo só se o path bate E a hash atual coincide
      const [base, hash] = href.split("#");
      return pathname === base && typeof window !== "undefined" && window.location.hash === `#${hash}`;
    }
    return pathname.startsWith(href);
  };

  if (loading || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[var(--ink)] text-[var(--dim)]">
        Carregando…
      </div>
    );
  }

  const apiBase = (
    typeof window !== "undefined"
      ? process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
      : "http://localhost:8000"
  ).replace(/\/$/, "");
  const chatUrl = `${apiBase}/chat`;

  return (
    <div className="min-h-screen bg-[var(--ink)] text-[var(--paper)] flex">
      {/* Mobile overlay */}
      {open && (
        <div
          className="fixed inset-0 bg-black/60 z-30 lg:hidden"
          onClick={() => setOpen(false)}
        />
      )}

      {/* ── Sidebar (COMBO 05) ─────────────────────────────── */}
      <aside
        className={`fixed lg:sticky top-0 z-40 h-screen w-64 shrink-0 bg-[var(--mirage)] border-r border-[var(--line)] flex flex-col transition-transform lg:translate-x-0 ${
          open ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        {/* Brand */}
        <div className="px-5 py-5 border-b border-[var(--line)]">
          <Link href="/admin" className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-lg bg-[var(--blaze)] flex items-center justify-center text-[#05080a] font-black text-lg font-display">
              D
            </div>
            <div className="leading-tight">
              <div className="font-display font-bold text-[15px] tracking-tight">
                DEZAFIRA<span className="text-[var(--blaze)]">ADM</span>
              </div>
              <div className="font-mono text-[10px] text-[var(--dim)] tracking-widest uppercase">
                Combo 05 · Operate
              </div>
            </div>
          </Link>
        </div>

        {/* Nav */}
        <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-5">
          {NAV_SECTIONS.map((sec) => (
            <div key={sec.title}>
              <div className="px-2 mb-1.5 font-mono text-[10px] uppercase tracking-[0.14em] text-[var(--dim)]">
                {sec.title}
              </div>
              <div className="space-y-0.5">
                {sec.items.map((item) => {
                  const isHermes = item.label === "Hermes";
                  const isExternal = item.href.startsWith("http");
                  const resolvedHref = isHermes ? chatUrl : item.href;
                  const active = isActive(item.href);

                  if (isExternal) {
                    return (
                      <a
                        key={item.label + item.href}
                        href={resolvedHref}
                        target="_blank"
                        rel="noreferrer"
                        className="flex items-center gap-3 px-2.5 py-2 rounded-lg text-[13px] font-medium text-[var(--dim)] hover:text-[var(--paper)] hover:bg-[var(--mirage-2)] transition-colors"
                      >
                        <span className="w-5 text-center text-[15px]">{item.icon}</span>
                        {item.label}
                        <span className="ml-auto text-[9px] opacity-40">↗</span>
                      </a>
                    );
                  }

                  return (
                    <Link
                      key={item.label + item.href}
                      href={resolvedHref}
                      className={`flex items-center gap-3 px-2.5 py-2 rounded-lg text-[13px] font-medium transition-colors ${
                        active
                          ? "bg-[var(--blaze)]/15 text-[var(--blaze)] font-bold"
                          : "text-[var(--dim)] hover:text-[var(--paper)] hover:bg-[var(--mirage-2)]"
                      }`}
                    >
                      <span className="w-5 text-center text-[15px]">{item.icon}</span>
                      {item.label}
                      {active && <span className="ml-auto w-1.5 h-1.5 rounded-full bg-[var(--blaze)]" />}
                    </Link>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>

        {/* Footer user */}
        <div className="px-4 py-4 border-t border-[var(--line)] flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-full bg-[var(--mirage-2)] border border-[var(--line)] flex items-center justify-center text-[12px] font-bold text-[var(--blaze)]">
            {(user.name || "A").charAt(0).toUpperCase()}
          </div>
          <div className="flex-1 min-w-0">
            <div className="text-[12px] font-semibold truncate">{user.name}</div>
            <div className="font-mono text-[10px] text-[var(--dim)] uppercase">Admin</div>
          </div>
          <button
            onClick={async () => {
              await logout();
              router.push("/auth/login");
            }}
            title="Sair"
            className="text-[var(--dim)] hover:text-[var(--blaze)] transition-colors px-1"
          >
            ⎋
          </button>
        </div>
      </aside>

      {/* ── Content ─────────────────────────────────────────── */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Mobile top bar */}
        <div className="lg:hidden sticky top-0 z-20 bg-[var(--mirage)] border-b border-[var(--line)] px-4 py-3 flex items-center gap-3">
          <button
            onClick={() => setOpen(true)}
            className="text-[var(--paper)] text-xl leading-none"
            aria-label="Abrir menu"
          >
            ☰
          </button>
          <span className="font-display font-bold text-sm">
            DEZAFIRA<span className="text-[var(--blaze)]">ADM</span>
          </span>
        </div>
        <main className="flex-1 min-w-0">{children}</main>
      </div>
    </div>
  );
}
