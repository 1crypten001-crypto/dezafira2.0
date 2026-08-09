"use client";

export const dynamic = 'force-dynamic';



import { useAuth } from "../../lib/auth-context";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "../../lib/api";
import Link from "next/link";

const apiBase = (typeof window !== "undefined" ? (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000") : "http://localhost:8000").replace(/\/$/, "");
const chatUrl = `${apiBase}/chat/`;
const previewUrl = `${apiBase}/api/v1/hermes/preview/sess_admin/funnel`;

export default function AdminPage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  const [stats, setStats] = useState<any>(null);
  const [users, setUsers] = useState<any[]>([]);
  const [postizStatus, setPostizStatus] = useState<any>(null);
  const [tab, setTab] = useState<
    | "stats"
    | "hermes"
    | "fabrica-blog"
    | "fabrica-ebook"
    | "fabrica-mapas"
    | "fabrica-curso"
    | "marketing"
    | "fabrica-miniapp"
    | "fabrica-postiz"
    | "trilhas"
    | "users"
    | "analytics"
  >("hermes");

  useEffect(() => {
    if (!authLoading && (!user || user.role !== "admin")) {
      router.push("/painel");
    }
  }, [user, authLoading]);

  useEffect(() => {
    if (user?.role === "admin") {
      api.getAdminStats().then(setStats).catch(console.error);
      api.getAdminUsers().then((d) => setUsers(d.users || [])).catch(console.error);
      api.getPostizStatus().then(setPostizStatus).catch(console.error);
    }
  }, [user]);

  if (authLoading || !user) {
    return <div className="min-h-screen flex items-center justify-center text-[var(--text-dim)]">Carregando...</div>;
  }

  return (
    <div className="min-h-screen">
      <header className="border-b border-[var(--border)] bg-[var(--surface)]">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/painel" className="text-xl font-bold text-[var(--brand)]">Dezafira</Link>
            <span className="badge text-[var(--warning)]">Admin</span>
          </div>
          <Link href="/painel" className="text-sm text-[var(--text-dim)] hover:text-[var(--text)]">← Voltar ao Painel</Link>
        </div>
      </header>

      {/* Bar de Abas Exclusivas por Fábrica */}
      <div className="border-b border-[var(--border)] bg-[#090d16]">
        <div className="max-w-7xl mx-auto px-4 flex gap-1 overflow-x-auto">
          {([
            { id: "hermes", label: "🤖 Hermes Agent" },
            { id: "stats", label: "📊 Estatísticas" },
            { id: "fabrica-blog", label: "📝 Fábrica Blog" },
            { id: "fabrica-mapas", label: "🧠 Fábrica Mapas" },
            { id: "fabrica-ebook", label: "📗 Fábrica Ebook" },
            { id: "fabrica-curso", label: "🎓 Fábrica Curso" },
            { id: "fabrica-miniapp", label: "📱 Fábrica MiniApp" },
            { id: "marketing", label: "📢 Fábrica Marketing" },
            { id: "fabrica-postiz", label: "🚀 Fábrica Postiz" },
            { id: "trilhas", label: "🎓 Trilhas" },
            { id: "users", label: "👥 Usuários" },
            { id: "analytics", label: "📈 Analytics" },
          ] as const).map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
                tab === t.id
                  ? "border-[var(--brand)] text-[var(--brand)] font-bold bg-[#131c2e]"
                  : "border-transparent text-[var(--text-dim)] hover:text-[var(--text)]"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>

      <main className="max-w-7xl mx-auto px-4 py-8">
        
        {/* HERMES AGENT & PIPELINE CENTRAL */}
        {tab === "hermes" && (
          <div className="space-y-4">
            <div className="bg-[#090d16] border border-[#1e293b] rounded-2xl p-4 shadow-xl">
              <div className="flex flex-col md:flex-row items-start md:items-center justify-between border-b border-[#1e293b] pb-4 mb-4 gap-3">
                <div>
                  <div className="flex items-center gap-2">
                    <h2 className="text-lg font-bold text-[#38bdf8]">
                      🤖 Hermes Agent — Orquestrador Central
                    </h2>
                    <span className="badge text-[var(--success)] text-[10px]">🟢 DeepSeek LLM Ativo</span>
                  </div>
                  <p className="text-xs text-[var(--text-dim)] mt-0.5">
                    Método <strong>TLC Spec-Driven</strong> • Clique em <strong>▶️ INICIAR PIPELINE GERAL</strong> no topo do chat para orquestrar todas as fábricas.
                  </p>
                </div>

                <div className="flex gap-2">
                  <a
                    href={chatUrl}
                    target="_blank"
                    rel="noreferrer"
                    className="text-xs bg-[#38bdf822] text-[#38bdf8] px-3 py-2 rounded-lg font-semibold border border-[#38bdf855] hover:bg-[#38bdf844]"
                  >
                    ↗️ Abrir Chat em Nova Janela
                  </a>
                  <a
                    href={previewUrl}
                    target="_blank"
                    rel="noreferrer"
                    className="btn-primary text-xs px-3 py-2"
                  >
                    🚀 Preview da Oferta
                  </a>
                </div>
              </div>

              {/* Chat e Pipeline Geral em Tela Cheia Responsiva */}
              <iframe
                src={chatUrl}
                className="w-full rounded-xl border border-[#1e293b] bg-[#060911]"
                style={{ height: "calc(100vh - 200px)", minHeight: "650px" }}
                title="Hermes Agent WebUI Chat"
              />
            </div>
          </div>
        )}

        {/* FÁBRICA MINIAPP (SALA DE AGENTES + AGNES AI LOGO + DRIP DB) */}
        {tab === "fabrica-miniapp" && (
          <div className="space-y-4">
            <div className="bg-[#090d16] border border-[#1e293b] rounded-2xl p-6 shadow-xl flex justify-between items-center">
              <div>
                <span className="badge text-[var(--success)] text-xs mb-1 inline-block">🟢 Sala de Agentes Autônomos Ativa</span>
                <h2 className="text-xl font-bold text-[#f1f5f9]">📱 Fábrica de MiniApps & PWAs (Recorrência)</h2>
                <p className="text-xs text-[var(--text-dim)] mt-1">
                  Geração autônoma de Aplicativos PWAs Instaláveis, Logos 3D por Agnes AI e entrega temporizada de conteúdos no banco de dados.
                </p>
              </div>
              <Link href="/admin/fabrica-miniapp" className="btn-primary text-xs px-4 py-2">
                🚀 Abrir Sala de Agentes em Tela Cheia
              </Link>
            </div>
            
            <iframe
              src="/admin/fabrica-miniapp"
              className="w-full rounded-2xl border border-[#1e293b] bg-[#060911]"
              style={{ height: "calc(100vh - 250px)", minHeight: "700px" }}
              title="Fábrica de MiniApps PWA"
            />
          </div>
        )}

        {/* FÁBRICA DE MAPAS MENTAIS (NOVO) */}
        {tab === "fabrica-mapas" && (
          <div className="space-y-4">
            <div className="bg-[#090d16] border border-[#1e293b] rounded-2xl p-6 shadow-xl flex justify-between items-center">
              <div>
                <span className="badge text-[var(--success)] text-xs mb-1 inline-block">🟢 Memorização Ativa & Spaced Repetition</span>
                <h2 className="text-xl font-bold text-[#f1f5f9]">🧠 Fábrica de Mapas Mentais (Esteira Recorrente)</h2>
                <p className="text-xs text-[var(--text-dim)] mt-1">
                  Gere mapas mentais dinâmicos em JSON com quizzes interativos e modo foco de 3 níveis.
                </p>
              </div>
              <Link href="/admin/fabrica-mapas" className="btn-primary text-xs px-4 py-2">
                🚀 Abrir Workspace de Mapas Mentais
              </Link>
            </div>
            
            <iframe
              src="/admin/fabrica-mapas"
              className="w-full rounded-2xl border border-[#1e293b] bg-[#060911]"
              style={{ height: "calc(100vh - 250px)", minHeight: "700px" }}
              title="Fábrica de Mapas Mentais"
            />
          </div>
        )}

        {/* FÁBRICA EBOOK (SALA TRIPLA DE EBOOKS: 1 PRINCIPAL + 2 BÔNUS) */}
        {tab === "fabrica-ebook" && (
          <div className="space-y-4">
            <div className="bg-[#090d16] border border-[#1e293b] rounded-2xl p-6 shadow-xl flex justify-between items-center">
              <div>
                <span className="badge text-[var(--success)] text-xs mb-1 inline-block">🟢 Pacote Triplo com Capas 3D Agnes AI</span>
                <h2 className="text-xl font-bold text-[#f1f5f9]">📗 Fábrica de Ebooks (1 Principal + 2 Bônus Exclusivos)</h2>
                <p className="text-xs text-[var(--text-dim)] mt-1">
                  Gere 3 Ebooks simultaneamente com capas 3D por Agnes AI e leitor digital de 8 capítulos integrado.
                </p>
              </div>
              <Link href="/admin/fabrica-ebook" className="btn-primary text-xs px-4 py-2">
                🚀 Abrir Leitor & Fábrica em Tela Cheia
              </Link>
            </div>
            
            <iframe
              src="/admin/fabrica-ebook"
              className="w-full rounded-2xl border border-[#1e293b] bg-[#060911]"
              style={{ height: "calc(100vh - 250px)", minHeight: "700px" }}
              title="Fábrica de Ebooks"
            />
          </div>
        )}

        {/* FÁBRICA POSTIZ (NOVA) */}
        {tab === "fabrica-postiz" && (
          <div className="card text-center py-12">
            <h2 className="text-2xl font-bold mb-2">🚀 Fábrica Postiz — Distribuição & Anúncios</h2>
            <p className="text-[var(--text-dim)] mb-6 max-w-lg mx-auto">
              Automação de anúncios pagos e postagens orgânicas em mais de 20 redes sociais (Instagram, TikTok, Pinterest, YouTube Shorts, X) via APIs oficiais e MCP.
            </p>
            <div className="inline-block bg-[#131c2e] p-4 rounded-xl border border-[#1e293b] mb-6 text-left text-xs">
              <div><strong>Status Conexão Postiz:</strong> <span className="text-[#22c55e] font-bold">Conectado (API/MCP OK)</span></div>
              <div className="mt-1"><strong>Canais Ativos:</strong> Instagram, TikTok, Pinterest, X, YouTube, LinkedIn</div>
            </div>
            <br />
            <a href="https://dezafiraadm-production.up.railway.app/api/v1/postiz/status" target="_blank" className="btn-primary inline-block">
              Verificar Conexão Postiz API
            </a>
          </div>
        )}

        {/* OUTRAS FÁBRICAS */}
        {tab === "stats" && stats && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { label: "Usuários", value: stats.total_users, icon: "👥" },
              { label: "Blogs", value: stats.total_blogs, icon: "📝" },
              { label: "Livros", value: stats.total_books, icon: "📗" },
              { label: "Cursos", value: stats.total_courses, icon: "🎓" },
            ].map((s) => (
              <div key={s.label} className="card text-center">
                <div className="text-2xl mb-1">{s.icon}</div>
                <div className="text-2xl font-bold">{s.value}</div>
                <div className="text-sm text-[var(--text-dim)]">{s.label}</div>
              </div>
            ))}
          </div>
        )}

        {tab === "users" && (
          <div className="card">
            <div className="space-y-2">
              {users.map((u) => (
                <div key={u.id} className="flex items-center gap-4 py-2 border-b border-[var(--border)] last:border-0">
                  <span className="w-6 text-center text-sm">{u.role === "admin" ? "👑" : "👤"}</span>
                  <div className="flex-1">
                    <span className="font-medium">{u.name}</span>
                    <span className="text-sm text-[var(--text-dim)] ml-2">{u.email}</span>
                  </div>
                  <span className={`badge ${u.is_active ? "text-[var(--success)]" : "text-[var(--error)]"}`}>
                    {u.is_active ? "Ativo" : "Inativo"}
                  </span>
                  <span className="text-sm text-[var(--text-dim)]">{u.created_at}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {tab === "fabrica-blog" && (
          <div className="text-center py-12">
            <h2 className="text-2xl font-bold mb-2">Fábrica de Blogs</h2>
            <p className="text-[var(--text-dim)] mb-4">Gerencie blogs e artigos do sistema com automação SEO</p>
            <a href="/admin/fabrica-blog" className="btn-primary inline-block">Acessar Fábrica de Blogs</a>
          </div>
        )}

        {tab === "fabrica-mapas" && (
          <div className="text-center py-12">
            <h2 className="text-2xl font-bold mb-2">Fábrica de Mapas Mentais</h2>
            <p className="text-[var(--text-dim)] mb-4">Gerencie mapas mentais estruturados, visualizadores PWA e quizzes de fixação</p>
            <a href="/admin/fabrica-mapas" className="btn-primary inline-block">Acessar Fábrica de Mapas Mentais</a>
          </div>
        )}

        {tab === "fabrica-ebook" && (
          <div className="text-center py-12">
            <h2 className="text-2xl font-bold mb-2">Fábrica de Ebooks</h2>
            <p className="text-[var(--text-dim)] mb-4">Gerencie livros digitais, capítulos e capas 3D geradas com IA</p>
            <a href="/admin/fabrica-ebook" className="btn-primary inline-block">Acessar Fábrica de Ebooks</a>
          </div>
        )}

        {tab === "fabrica-curso" && (
          <div className="text-center py-12">
            <h2 className="text-2xl font-bold mb-2">Fábrica de Cursos</h2>
            <p className="text-[var(--text-dim)] mb-4">Pipeline de criação de módulos, roteiros e videoaulas</p>
            <a href="/admin/fabrica-curso" className="btn-primary inline-block">Acessar Fábrica de Cursos</a>
          </div>
        )}

        {tab === "marketing" && (
          <div className="text-center py-12">
            <h2 className="text-2xl font-bold mb-2">Fábrica de Marketing</h2>
            <p className="text-[var(--text-dim)] mb-4">Gerencie Landing Pages, VSLs e Copies de alta conversão</p>
            <a href="/admin/marketing" className="btn-primary inline-block">Acessar Fábrica de Marketing</a>
          </div>
        )}

        {tab === "trilhas" && (
          <div className="text-center py-12">
            <h2 className="text-2xl font-bold mb-2">Trilhas de Aprendizado</h2>
            <p className="text-[var(--text-dim)] mb-4">Organize cursos em trilhas de conhecimento</p>
            <a href="/admin/trilhas" className="btn-primary inline-block">Gerenciar Trilhas</a>
          </div>
        )}

        {tab === "analytics" && (
          <div className="text-center py-12">
            <h2 className="text-2xl font-bold mb-2">Analytics & Métricas</h2>
            <p className="text-[var(--text-dim)] mb-4">Métricas consolidadas de visualização e engajamento</p>
            <a href="/admin/analytics" className="btn-primary inline-block">Acessar Analytics</a>
          </div>
        )}

      </main>
    </div>
  );
}
