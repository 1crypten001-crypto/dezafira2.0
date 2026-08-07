"use client";
import { useState, useEffect } from "react";
import { api } from "../../../lib/api";

export default function AnalyticsPage() {
  const [overview, setOverview] = useState<any>(null);
  const [courses, setCourses] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadData(); }, []);

  async function loadData() {
    setLoading(true);
    try {
      const [o, c] = await Promise.all([api.adminAnalyticsOverview(), api.adminAnalyticsCourses()]);
      setOverview(o);
      setCourses(c.courses || []);
    } catch (e) { console.error(e); }
    setLoading(false);
  }

  if (loading) return <div className="min-h-screen bg-gray-950 text-white p-6"><p>Carregando...</p></div>;

  return (
    <div className="min-h-screen bg-gray-950 text-white p-6">
      <h1 className="text-3xl font-bold mb-6">Analytics</h1>

      {overview && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <StatCard title="Usuarios" value={overview.users?.total} subtitle={`${overview.users?.admins} admins`} color="indigo" />
          <StatCard title="Cursos" value={overview.courses?.total} subtitle={`${overview.courses?.published} publicados`} color="amber" />
          <StatCard title="Ebooks" value={overview.books?.total} subtitle="livros" color="purple" />
          <StatCard title="Entregaveis" value={overview.deliverables?.total || 0} subtitle="apps criados" color="green" />
        </div>
      )}

      <div className="grid md:grid-cols-2 gap-6">
        <div className="bg-gray-900 p-4 rounded-lg">
          <h2 className="text-xl font-bold mb-3">Cursos por Status</h2>
          {courses.length === 0 ? <p className="text-gray-400">Nenhum curso encontrado</p> : (
            <div className="space-y-2">
              {courses.map(c => (
                <div key={c.id} className="flex justify-between items-center bg-gray-800 p-2 rounded">
                  <span>{c.title}</span>
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-gray-400">{c.total_modules}M {c.total_lessons}A</span>
                    <span className={`text-xs px-2 py-1 rounded ${c.status === "published" ? "bg-green-800" : "bg-yellow-800"}`}>{c.status}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="bg-gray-900 p-4 rounded-lg">
          <h2 className="text-xl font-bold mb-3">Resumo do Sistema</h2>
          <div className="space-y-3 text-sm">
            <div className="flex justify-between"><span className="text-gray-400">Blogs</span><span>{overview?.blogs?.total || 0}</span></div>
            <div className="flex justify-between"><span className="text-gray-400">Artigos</span><span>{overview?.blogs?.posts || 0}</span></div>
            <div className="flex justify-between"><span className="text-gray-400">Cursos Publicados</span><span>{overview?.courses?.published || 0}</span></div>
            <div className="flex justify-between"><span className="text-gray-400">Entregaveis</span><span>{overview?.deliverables?.total || 0}</span></div>
          </div>
        </div>
      </div>
    </div>
  );
}

function StatCard({ title, value, subtitle, color }: { title: string; value: any; subtitle: string; color: string }) {
  const colors: Record<string, string> = {
    indigo: "border-indigo-500",
    amber: "border-amber-500",
    purple: "border-purple-500",
    green: "border-green-500",
  };
  return (
    <div className={`bg-gray-900 p-4 rounded-lg border-l-4 ${colors[color] || "border-gray-500"}`}>
      <p className="text-sm text-gray-400">{title}</p>
      <p className="text-2xl font-bold">{value ?? 0}</p>
      <p className="text-xs text-gray-500">{subtitle}</p>
    </div>
  );
}
