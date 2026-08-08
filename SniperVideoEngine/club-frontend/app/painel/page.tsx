"use client";

import { useAuth } from "../../lib/auth-context";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "../../lib/api";
import Link from "next/link";

export default function PainelPage() {
  const { user, loading: authLoading, logout } = useAuth();
  const router = useRouter();
  const [dashboard, setDashboard] = useState<any>(null);
  const [tab, setTab] = useState<"overview" | "courses" | "ebooks" | "ranking">("overview");

  useEffect(() => {
    if (!authLoading && !user) {
      router.push("/auth/login");
    }
  }, [user, authLoading]);

  useEffect(() => {
    if (user) {
      api.getDashboard().then(setDashboard).catch(console.error);
    }
  }, [user]);

  if (authLoading || !user) {
    return <div className="min-h-screen flex items-center justify-center text-[var(--text-dim)]">Carregando...</div>;
  }

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="border-b border-[var(--border)] bg-[var(--surface)]">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <Link href="/" className="text-xl font-bold">Dezafira Club</Link>
          <div className="flex items-center gap-4">
            <span className="text-sm text-[var(--text-dim)]">{user.name}</span>
            <span className="badge text-[var(--brand)]">{user.total_points} pts</span>
            {user.role === "admin" && (
              <Link href="/admin" className="text-sm text-[var(--warning)] hover:underline">Admin</Link>
            )}
            <button onClick={logout} className="text-sm text-[var(--text-dim)] hover:text-[var(--error)]">Sair</button>
          </div>
        </div>
      </header>

      {/* Tabs */}
      <div className="border-b border-[var(--border)]">
        <div className="max-w-6xl mx-auto px-4 flex gap-1">
          {(["overview", "courses", "ebooks", "ranking"] as const).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                tab === t
                  ? "border-[var(--brand)] text-[var(--brand)]"
                  : "border-transparent text-[var(--text-dim)] hover:text-[var(--text)]"
              }`}
            >
              {t === "overview" ? "Visão Geral" : t === "courses" ? "Cursos" : t === "ebooks" ? "Ebooks" : "Ranking"}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <main className="max-w-6xl mx-auto px-4 py-8">
        {tab === "overview" && <OverviewTab dashboard={dashboard} />}
        {tab === "courses" && <CoursesTab />}
        {tab === "ebooks" && <EbooksTab dashboard={dashboard} />}
        {tab === "ranking" && <RankingTab />}
      </main>
    </div>
  );
}

function OverviewTab({ dashboard }: { dashboard: any }) {
  if (!dashboard) return <div className="text-[var(--text-dim)]">Carregando...</div>;
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: "Pontos", value: dashboard.total_points, icon: "⭐" },
          { label: "Streak", value: `${dashboard.streak?.current_streak || 0} dias`, icon: "🔥" },
          { label: "Cursos", value: dashboard.courses_in_progress || 0, icon: "🎓" },
          { label: "Ebooks", value: dashboard.ebooks_owned || 0, icon: "📚" },
        ].map((s) => (
          <div key={s.label} className="card text-center">
            <div className="text-2xl mb-1">{s.icon}</div>
            <div className="text-2xl font-bold">{s.value}</div>
            <div className="text-sm text-[var(--text-dim)]">{s.label}</div>
          </div>
        ))}
      </div>

      {/* Badges */}
      {dashboard.badges?.length > 0 && (
        <div className="card">
          <h3 className="font-semibold mb-3">Badges</h3>
          <div className="flex flex-wrap gap-2">
            {dashboard.badges.map((b: any, i: number) => (
              <span key={i} className="badge">
                {b.badge_icon} {b.badge_name}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Ranking Preview */}
      {dashboard.ranking?.length > 0 && (
        <div className="card">
          <h3 className="font-semibold mb-3">Ranking</h3>
          <div className="space-y-2">
            {dashboard.ranking.slice(0, 5).map((r: any) => (
              <div key={r.user_id} className="flex items-center gap-3 py-1">
                <span className="w-6 text-center text-sm font-bold text-[var(--text-dim)]">#{r.position}</span>
                <span className="flex-1">{r.name}</span>
                <span className="text-[var(--brand)] text-sm">{r.total_points} pts</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function CoursesTab() {
  const [courses, setCourses] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getMemberCourses().then((d) => setCourses(d.courses || [])).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="text-[var(--text-dim)]">Carregando...</div>;

  return (
    <div className="space-y-4">
      {courses.length === 0 ? (
        <div className="card text-center text-[var(--text-dim)]">
          Você ainda não está inscrito em nenhum curso.
        </div>
      ) : (
        courses.map((c) => (
          <div key={c.id} className="card flex items-center gap-4">
            <div className="w-16 h-16 rounded-lg bg-[var(--surface2)] flex items-center justify-center text-2xl">🎓</div>
            <div className="flex-1">
              <h3 className="font-semibold">{c.course_title || "Curso"}</h3>
              <p className="text-sm text-[var(--text-dim)]">Progresso: {Math.round(c.progress_pct || 0)}%</p>
              <div className="w-full bg-[var(--surface2)] rounded-full h-2 mt-2">
                <div
                  className="bg-[var(--brand)] h-2 rounded-full transition-all"
                  style={{ width: `${c.progress_pct || 0}%` }}
                />
              </div>
            </div>
            {c.completed && <span className="badge text-[var(--success)]">✓ Concluído</span>}
          </div>
        ))
      )}
    </div>
  );
}

function EbooksTab({ dashboard }: { dashboard: any }) {
  return (
    <div className="card text-center text-[var(--text-dim)]">
      {dashboard?.ebooks_owned || 0} ebooks na sua coleção.
      <br />
      <span className="text-sm">Em breve: leitor integrado.</span>
    </div>
  );
}

function RankingTab() {
  const [ranking, setRanking] = useState<any[]>([]);
  useEffect(() => {
    api.getRanking().then((d) => setRanking(d.ranking || [])).catch(console.error);
  }, []);

  return (
    <div className="card">
      {ranking.length === 0 ? (
        <div className="text-center text-[var(--text-dim)]">Nenhum dado ainda.</div>
      ) : (
        <div className="space-y-3">
          {ranking.map((r) => (
            <div key={r.user_id} className="flex items-center gap-4 py-3 border-b border-[var(--border)] last:border-0">
              <span className={`text-xl font-bold w-10 text-center ${r.position <= 3 ? "" : "text-[var(--text-dim)]"}`}>
                {r.position <= 3 ? ["🥇", "🥈", "🥉"][r.position - 1] : `#${r.position}`}
              </span>
              <div className="flex-1">
                <div className="font-medium">{r.name}</div>
              </div>
              <div className="text-[var(--brand)] font-semibold">{r.total_points} pts</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
