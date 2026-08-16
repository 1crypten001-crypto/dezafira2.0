"use client";

export const dynamic = 'force-dynamic';

import { useAuth } from "../../lib/auth-context";
import { useRouter } from "next/navigation";
import { useEffect, useState, useCallback } from "react";
import { api } from "../../lib/api";
import Link from "next/link";

const API_URL = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/$/, "");

function authH(): Record<string, string> {
  const token = typeof window !== "undefined" ? localStorage.getItem("dz_token") : null;
  return token
    ? { Authorization: `Bearer ${token}`, "Content-Type": "application/json" }
    : { "Content-Type": "application/json" };
}

async function safeFetch<T>(url: string, fallback: T): Promise<T> {
  try {
    const res = await fetch(url, { headers: authH() });
    if (!res.ok) return fallback;
    return await res.json();
  } catch {
    return fallback;
  }
}

type SystemStatus = { api: "ok" | "error" | "loading"; obscura: boolean; version: string; build: string };
type FactoryData = {
  blogs: number; lastBlog: string;
  ebooks: number; lastEbook: string;
  courses: number; lastCourse: string;
  vsls: number; lastVsl: string;
  biosites: number; lastBiosite: string;
  miniapps: number; lastMiniapp: string;
  mindmaps: number; lastMindmap: string;
};
type ActivityItem = { icon: string; label: string; name: string; time: string; href: string };
type GlobalStats = { total_users: number; total_blogs: number; total_books: number; total_courses: number };

function StatusPill({ ok, label }: { ok: boolean | "loading"; label: string }) {
  if (ok === "loading") return (
    <div className="flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-mono font-semibold"
      style={{ background: "rgba(248,88,8,0.08)", color: "var(--dim)" }}>
      <span className="w-1.5 h-1.5 rounded-full bg-[var(--dim)] animate-pulse" />{label}
    </div>
  );
  return (
    <div className="flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-mono font-semibold"
      style={{
        background: ok ? "rgba(34,197,94,0.1)" : "rgba(239,68,68,0.1)",
        color: ok ? "#4ade80" : "#f87171"
      }}>
      <span className={`w-1.5 h-1.5 rounded-full ${ok ? "bg-green-400 animate-pulse" : "bg-red-400"}`} />{label}
    </div>
  );
}

function MetricCard({ icon, value, label, href }: { icon: string; value: number | string; label: string; href?: string }) {
  const inner = (
    <div className="flex items-center gap-3 p-3 rounded-xl border transition-all hover:border-[var(--brand)]/40"
      style={{ background: "rgba(255,255,255,0.025)", borderColor: "rgba(255,255,255,0.06)" }}>
      <span className="text-lg shrink-0">{icon}</span>
      <div className="min-w-0 flex-1">
        <div className="text-lg font-black tabular-nums leading-none" style={{ color: "var(--paper)" }}>{value ?? "—"}</div>
        <div className="text-[10px] mt-0.5 truncate" style={{ color: "var(--dim)" }}>{label}</div>
      </div>
    </div>
  );
  return href ? <Link href={href}>{inner}</Link> : inner;
}

function FactoryCard({ icon, name, count, last, href, color }: {
  icon: string; name: string; count: number; last: string; href: string; color: string
}) {
  return (
    <Link href={href}>
      <div className="flex flex-col gap-2.5 p-4 rounded-xl border cursor-pointer transition-all hover:scale-[1.01] hover:border-[var(--brand)]/40"
        style={{ background: "rgba(255,255,255,0.025)", borderColor: "rgba(255,255,255,0.06)" }}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-lg">{icon}</span>
            <span className="text-[12px] font-bold" style={{ color: "var(--paper)" }}>{name}</span>
          </div>
          <span className="text-[11px] font-black tabular-nums px-2 py-0.5 rounded-lg"
            style={{ background: `${color}18`, color }}>{count}</span>
        </div>
        <div className="text-[10px] truncate" style={{ color: "var(--dim)" }}>
          {last ? `↳ ${last}` : "Nenhum item ainda"}
        </div>
        <div className="flex justify-end">
          <span className="text-[10px] font-semibold" style={{ color: "var(--brand)" }}>Abrir →</span>
        </div>
      </div>
    </Link>
  );
}

function ActivityRow({ item }: { item: ActivityItem }) {
  return (
    <div className="flex items-start gap-2.5 py-2.5 border-b last:border-0"
      style={{ borderColor: "rgba(255,255,255,0.05)" }}>
      <span className="text-sm mt-0.5 shrink-0">{item.icon}</span>
      <div className="flex-1 min-w-0">
        <div className="text-[11px] font-medium truncate" style={{ color: "var(--paper)" }}>{item.name}</div>
        <div className="text-[10px]" style={{ color: "var(--dim)" }}>{item.label} · {item.time}</div>
      </div>
    </div>
  );
}

function UserRow({ u }: { u: any }) {
  return (
    <div className="flex items-center gap-2 py-2 border-b last:border-0"
      style={{ borderColor: "rgba(255,255,255,0.05)" }}>
      <div className="w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-black shrink-0"
        style={{ background: "rgba(248,88,8,0.15)", color: "var(--brand)" }}>
        {(u.name || "?").charAt(0).toUpperCase()}
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-[11px] font-semibold truncate" style={{ color: "var(--paper)" }}>{u.name}</div>
        <div className="text-[10px] truncate" style={{ color: "var(--dim)" }}>{u.email}</div>
      </div>
      <span className="text-[9px] font-mono px-1.5 py-0.5 rounded"
        style={{
          background: u.role === "admin" ? "rgba(248,88,8,0.15)" : "rgba(255,255,255,0.05)",
          color: u.role === "admin" ? "var(--brand)" : "var(--dim)"
        }}>{u.role}</span>
    </div>
  );
}

function SectionLabel({ label }: { label: string }) {
  return (
    <div className="flex items-center gap-2 mb-1">
      <span className="text-[10px] font-mono font-bold uppercase tracking-[0.14em]" style={{ color: "var(--dim)" }}>{label}</span>
      <div className="flex-1 h-px" style={{ background: "rgba(255,255,255,0.05)" }} />
    </div>
  );
}

function fmtTime(iso?: string | null): string {
  if (!iso) return "—";
  try {
    const diff = Date.now() - new Date(iso).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return "agora";
    if (mins < 60) return `${mins}m atrás`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs}h atrás`;
    return new Date(iso).toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit" });
  } catch { return "—"; }
}

export default function AdminDashboard() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();

  const [sysStatus, setSysStatus] = useState<SystemStatus>({ api: "loading", obscura: false, version: "—", build: "—" });
  const [globalStats, setGlobalStats] = useState<GlobalStats | null>(null);
  const [factoryData, setFactoryData] = useState<FactoryData>({
    blogs: 0, lastBlog: "", ebooks: 0, lastEbook: "", courses: 0, lastCourse: "",
    vsls: 0, lastVsl: "", biosites: 0, lastBiosite: "", miniapps: 0, lastMiniapp: "",
    mindmaps: 0, lastMindmap: "",
  });
  const [activity, setActivity] = useState<ActivityItem[]>([]);
  const [users, setUsers] = useState<any[]>([]);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    if (!authLoading && (!user || user.role !== "admin")) router.push("/painel");
  }, [user, authLoading, router]);

  const loadAll = useCallback(async () => {
    if (!user || user.role !== "admin") return;
    setRefreshing(true);
    const [health, stats, vslRes, bioRes, miniRes, mindRes, ebookRes, courseRes, channelsRes, usersRes] =
      await Promise.all([
        safeFetch(`${API_URL}/healthz`, null as any),
        safeFetch(`${API_URL}/api/v1/admin/stats`, null as any),
        safeFetch(`${API_URL}/api/v1/vsl`, { videos: [] as any[] }),
        safeFetch(`${API_URL}/api/v1/biosites`, { biosites: [] as any[] }),
        safeFetch(`${API_URL}/api/v1/miniapps`, { miniapps: [] as any[] }),
        safeFetch(`${API_URL}/api/v1/mindmaps`, { mindmaps: [] as any[] }),
        safeFetch(`${API_URL}/api/v1/ebooks`, { books: [] as any[] }),
        safeFetch(`${API_URL}/api/v1/courses`, { courses: [] as any[] }),
        safeFetch(`${API_URL}/api/v1/channels`, { channels: [] as any[] }),
        api.getAdminUsers().catch(() => ({ users: [] })),
      ]);

    setSysStatus({
      api: health ? "ok" : "error",
      obscura: health?.obscura_enabled ?? false,
      version: health?.version ?? "—",
      build: health?.build ?? "—",
    });
    if (stats) setGlobalStats(stats);

    const vsls = vslRes?.videos ?? [];
    const bios = bioRes?.biosites ?? [];
    const minis = miniRes?.miniapps ?? [];
    const minds = mindRes?.mindmaps ?? [];
    const ebooks = ebookRes?.books ?? [];
    const courses = courseRes?.courses ?? [];
    const channels = channelsRes?.channels ?? [];

    setFactoryData({
      blogs: channels.reduce((s: number, c: any) => s + (c.post_count ?? 0), 0),
      lastBlog: channels[0]?.title ?? channels[0]?.name ?? "",
      ebooks: ebooks.length, lastEbook: ebooks[0]?.title ?? "",
      courses: courses.length, lastCourse: courses[0]?.title ?? "",
      vsls: vsls.length, lastVsl: vsls[0]?.title ?? "",
      biosites: bios.length, lastBiosite: bios[0]?.name ?? "",
      miniapps: minis.length, lastMiniapp: minis[0]?.title ?? minis[0]?.name ?? "",
      mindmaps: minds.length, lastMindmap: minds[0]?.title ?? "",
    });

    const allItems: ActivityItem[] = [
      ...vsls.slice(0, 3).map((v: any) => ({ icon: "🎬", label: "VSL", name: v.title ?? v.id, time: fmtTime(v.created_at), href: "/admin/fabrica-vsl" })),
      ...bios.slice(0, 3).map((b: any) => ({ icon: "🔗", label: "Bio Site", name: b.name ?? b.id, time: fmtTime(b.created_at), href: "/admin/fabrica-biosites" })),
      ...ebooks.slice(0, 3).map((e: any) => ({ icon: "📗", label: "Ebook", name: e.title ?? e.id, time: fmtTime(e.created_at), href: "/admin/fabrica-ebook" })),
      ...courses.slice(0, 3).map((c: any) => ({ icon: "🎓", label: "Curso", name: c.title ?? c.id, time: fmtTime(c.created_at), href: "/admin/fabrica-curso" })),
      ...minis.slice(0, 2).map((m: any) => ({ icon: "📱", label: "MiniApp", name: m.title ?? m.name ?? m.id, time: fmtTime(m.created_at), href: "/admin/fabrica-miniapp" })),
      ...minds.slice(0, 2).map((m: any) => ({ icon: "⌘", label: "Mapa", name: m.title ?? m.id, time: fmtTime(m.created_at), href: "/admin/fabrica-mapas" })),
    ];
    setActivity(allItems.slice(0, 10));
    setUsers((usersRes?.users ?? []).slice(0, 5));
    setLastRefresh(new Date());
    setRefreshing(false);
  }, [user]);

  useEffect(() => { loadAll(); }, [loadAll]);

  if (authLoading || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: "var(--ink)", color: "var(--dim)" }}>
        <div className="animate-pulse text-sm font-mono">Carregando...</div>
      </div>
    );
  }

  const totalContent = factoryData.blogs + factoryData.ebooks + factoryData.courses +
    factoryData.vsls + factoryData.biosites + factoryData.miniapps + factoryData.mindmaps;

  return (
    <div className="min-h-screen" style={{ background: "var(--ink)", color: "var(--paper)" }}>

      {/* Status Bar */}
      <div className="border-b px-6 py-2.5 flex items-center justify-between gap-4 flex-wrap"
        style={{ borderColor: "rgba(255,255,255,0.06)", background: "rgba(0,0,0,0.25)" }}>
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-[10px] font-mono uppercase tracking-widest mr-1" style={{ color: "var(--dim)" }}>Sistema</span>
          <StatusPill ok={sysStatus.api === "loading" ? "loading" : sysStatus.api === "ok"} label="API" />
          <StatusPill ok={sysStatus.api === "ok"} label="Banco" />
          <StatusPill ok={sysStatus.obscura} label="Obscura" />
          {sysStatus.version !== "—" && (
            <span className="text-[10px] font-mono px-2 py-0.5 rounded ml-1"
              style={{ background: "rgba(255,255,255,0.04)", color: "var(--dim)" }}>v{sysStatus.version}</span>
          )}
        </div>
        <div className="flex items-center gap-3">
          {lastRefresh && (
            <span className="text-[10px] font-mono hidden sm:block" style={{ color: "var(--dim)" }}>
              {lastRefresh.toLocaleTimeString("pt-BR")}
            </span>
          )}
          <button onClick={loadAll} disabled={refreshing}
            className="flex items-center gap-1.5 text-[11px] font-semibold px-3 py-1 rounded-lg transition-all hover:opacity-80 disabled:opacity-40"
            style={{ background: "rgba(248,88,8,0.1)", color: "var(--brand)", border: "1px solid rgba(248,88,8,0.2)" }}>
            <span className={refreshing ? "animate-spin inline-block" : ""}>⟳</span> Atualizar
          </button>
        </div>
      </div>

      {/* Page Title */}
      <div className="px-6 pt-5 pb-4 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-black tracking-tight" style={{ color: "var(--paper)" }}>Painel de Controle</h1>
          <p className="text-[11px] mt-0.5" style={{ color: "var(--dim)" }}>Visão geral de todas as fábricas e métricas do sistema</p>
        </div>
        <div className="text-[11px] font-mono px-3 py-1.5 rounded-lg"
          style={{ background: "rgba(248,88,8,0.08)", color: "var(--brand)", border: "1px solid rgba(248,88,8,0.15)" }}>
          👋 {user.name}
        </div>
      </div>

      {/* 3-Column Grid */}
      <div className="px-6 pb-10 grid gap-5"
        style={{ gridTemplateColumns: "clamp(200px,21%,268px) 1fr clamp(240px,25%,320px)" }}>

        {/* COL 1 — Global Metrics */}
        <div className="flex flex-col gap-2.5">
          <SectionLabel label="Métricas Globais" />
          <MetricCard icon="👥" value={globalStats?.total_users ?? "—"} label="Usuários cadastrados" href="/admin/analytics" />
          <MetricCard icon="📦" value={totalContent} label="Total de itens criados" />
          <div className="h-px my-1" style={{ background: "rgba(255,255,255,0.05)" }} />
          <SectionLabel label="Por Fábrica" />
          <MetricCard icon="📝" value={factoryData.blogs} label="Posts de Blog" href="/admin/fabrica-blog" />
          <MetricCard icon="📗" value={factoryData.ebooks} label="Ebooks" href="/admin/fabrica-ebook" />
          <MetricCard icon="🎓" value={factoryData.courses} label="Cursos" href="/admin/fabrica-curso" />
          <MetricCard icon="🎬" value={factoryData.vsls} label="VSLs" href="/admin/fabrica-vsl" />
          <MetricCard icon="🔗" value={factoryData.biosites} label="Bio Sites" href="/admin/fabrica-biosites" />
          <MetricCard icon="📱" value={factoryData.miniapps} label="MiniApps" href="/admin/fabrica-miniapp" />
          <MetricCard icon="⌘" value={factoryData.mindmaps} label="Mapas Mentais" href="/admin/fabrica-mapas" />
        </div>

        {/* COL 2 — Factory Cards */}
        <div className="flex flex-col gap-4 min-w-0">
          <SectionLabel label="Fábricas de Conteúdo" />
          <div className="grid grid-cols-2 gap-3">
            <FactoryCard icon="🎯" name="Ofertas" count={0} last="" href="/admin/fabrica-ofertas" color="#8b5cf6" />
            <FactoryCard icon="✎" name="Blog" count={factoryData.blogs} last={factoryData.lastBlog} href="/admin/fabrica-blog" color="#38bdf8" />
            <FactoryCard icon="📗" name="Ebook" count={factoryData.ebooks} last={factoryData.lastEbook} href="/admin/fabrica-ebook" color="#a78bfa" />
            <FactoryCard icon="🎓" name="Curso" count={factoryData.courses} last={factoryData.lastCourse} href="/admin/fabrica-curso" color="#f59e0b" />
            <FactoryCard icon="🎬" name="VSL" count={factoryData.vsls} last={factoryData.lastVsl} href="/admin/fabrica-vsl" color="#f85808" />
            <FactoryCard icon="🔗" name="Bio Sites" count={factoryData.biosites} last={factoryData.lastBiosite} href="/admin/fabrica-biosites" color="#4ade80" />
            <FactoryCard icon="◈" name="Produtos" count={0} last="" href="/admin/fabrica-produtos" color="#fb7185" />
          </div>

          <SectionLabel label="Serviços de PWA" />
          <div className="grid grid-cols-2 gap-3">
            <FactoryCard icon="📱" name="MiniApps" count={factoryData.miniapps} last={factoryData.lastMiniapp} href="/admin/fabrica-miniapp" color="#22d3ee" />
            <FactoryCard icon="⌘" name="Mapas Mentais" count={factoryData.mindmaps} last={factoryData.lastMindmap} href="/admin/fabrica-mapas" color="#a3e635" />
          </div>

          <SectionLabel label="Distribuição & Inteligência" />
          <div className="grid grid-cols-2 gap-3">
            {/* Postiz */}
            <a href={`${API_URL}/api/v1/postiz/status`} target="_blank" rel="noreferrer">
              <div className="flex flex-col gap-2.5 p-4 rounded-xl border transition-all hover:scale-[1.01] hover:border-[var(--brand)]/40"
                style={{ background: "rgba(255,255,255,0.025)", borderColor: "rgba(255,255,255,0.06)" }}>
                <div className="flex items-center gap-2"><span className="text-lg">⇶</span>
                  <span className="text-[12px] font-bold" style={{ color: "var(--paper)" }}>Postiz</span></div>
                <div className="text-[10px]" style={{ color: "var(--dim)" }}>Distribuição multicanal automática</div>
                <div className="flex justify-end"><span className="text-[10px] font-semibold" style={{ color: "var(--brand)" }}>Status ↗</span></div>
              </div>
            </a>
            {/* Hermes */}
            <a href={`${API_URL}/chat/`} target="_blank" rel="noreferrer">
              <div className="flex flex-col gap-2.5 p-4 rounded-xl border transition-all hover:scale-[1.01] hover:border-[var(--brand)]/40"
                style={{ background: "rgba(248,88,8,0.04)", borderColor: "rgba(248,88,8,0.15)" }}>
                <div className="flex items-center gap-2"><span className="text-lg">✦</span>
                  <span className="text-[12px] font-bold" style={{ color: "var(--paper)" }}>Hermes</span></div>
                <div className="text-[10px]" style={{ color: "var(--dim)" }}>Agente orquestrador central</div>
                <div className="flex justify-end"><span className="text-[10px] font-semibold" style={{ color: "var(--brand)" }}>Abrir ↗</span></div>
              </div>
            </a>
          </div>

          <SectionLabel label="Acesso Rápido" />
          <div className="grid grid-cols-4 gap-2">
            {[
              { label: "Canais", icon: "◉", href: "/admin/canais" },
              { label: "Trilhas", icon: "≡", href: "/admin/trilhas" },
              { label: "Analytics", icon: "≋", href: "/admin/analytics" },
              { label: "AionUi", icon: "⊕", href: "http://127.0.0.1:25809", ext: true },
            ].map(l => (
              l.ext
                ? <a key={l.href} href={l.href} target="_blank" rel="noreferrer">
                  <div className="flex flex-col items-center gap-1 py-3 px-1 rounded-xl border text-center transition-all hover:border-[var(--brand)]/40"
                    style={{ background: "rgba(255,255,255,0.025)", borderColor: "rgba(255,255,255,0.06)" }}>
                    <span className="text-sm">{l.icon}</span>
                    <span className="text-[9px] font-semibold" style={{ color: "var(--dim)" }}>{l.label}</span>
                  </div>
                </a>
                : <Link key={l.href} href={l.href}>
                  <div className="flex flex-col items-center gap-1 py-3 px-1 rounded-xl border text-center transition-all hover:border-[var(--brand)]/40"
                    style={{ background: "rgba(255,255,255,0.025)", borderColor: "rgba(255,255,255,0.06)" }}>
                    <span className="text-sm">{l.icon}</span>
                    <span className="text-[9px] font-semibold" style={{ color: "var(--dim)" }}>{l.label}</span>
                  </div>
                </Link>
            ))}
          </div>
        </div>

        {/* COL 3 — Activity + Users */}
        <div className="flex flex-col gap-4">

          {/* Activity Feed */}
          <div className="rounded-xl border overflow-hidden"
            style={{ background: "rgba(255,255,255,0.025)", borderColor: "rgba(255,255,255,0.06)" }}>
            <div className="px-4 py-3 border-b flex items-center justify-between"
              style={{ borderColor: "rgba(255,255,255,0.06)" }}>
              <span className="text-[11px] font-bold uppercase tracking-wide" style={{ color: "var(--dim)" }}>Atividade Recente</span>
              <span className="text-[10px] font-mono" style={{ color: "var(--dim)" }}>últimas criações</span>
            </div>
            <div className="px-4 py-1">
              {activity.length === 0
                ? <div className="py-8 text-center text-[11px]" style={{ color: "var(--dim)" }}>
                  Nenhuma atividade ainda.<br />
                  <span style={{ color: "var(--brand)" }}>Crie conteúdo nas fábricas!</span>
                </div>
                : activity.map((item, i) => <ActivityRow key={i} item={item} />)
              }
            </div>
          </div>

          {/* Users Widget */}
          <div className="rounded-xl border overflow-hidden"
            style={{ background: "rgba(255,255,255,0.025)", borderColor: "rgba(255,255,255,0.06)" }}>
            <div className="px-4 py-3 border-b flex items-center justify-between"
              style={{ borderColor: "rgba(255,255,255,0.06)" }}>
              <span className="text-[11px] font-bold uppercase tracking-wide" style={{ color: "var(--dim)" }}>👥 Usuários</span>
              <Link href="/admin/analytics" className="text-[10px] font-semibold hover:underline"
                style={{ color: "var(--brand)" }}>Ver todos →</Link>
            </div>
            <div className="px-4 py-1">
              {users.length === 0
                ? <div className="py-6 text-center text-[11px]" style={{ color: "var(--dim)" }}>Nenhum usuário.</div>
                : users.map((u, i) => <UserRow key={i} u={u} />)
              }
            </div>
            <div className="px-4 py-2.5 border-t" style={{ borderColor: "rgba(255,255,255,0.06)" }}>
              <span className="text-[10px]" style={{ color: "var(--dim)" }}>
                Total: <strong style={{ color: "var(--paper)" }}>{globalStats?.total_users ?? "—"}</strong> usuários cadastrados
              </span>
            </div>
          </div>

        </div>

      </div>
    </div>
  );
}
