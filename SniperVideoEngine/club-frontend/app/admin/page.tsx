"use client";

import { useAuth } from "../../lib/auth-context";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "../../lib/api";
import Link from "next/link";

export default function AdminPage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  const [stats, setStats] = useState<any>(null);
  const [users, setUsers] = useState<any[]>([]);
  const [tab, setTab] = useState<"stats" | "users" | "combos" | "fabrica-blog" | "fabrica-ebook" | "fabrica-curso" | "trilhas" | "analytics" | "marketing">("stats");

  useEffect(() => {
    if (!authLoading && (!user || user.role !== "admin")) {
      router.push("/painel");
    }
  }, [user, authLoading]);

  useEffect(() => {
    if (user?.role === "admin") {
      api.getAdminStats().then(setStats).catch(console.error);
      api.getAdminUsers().then((d) => setUsers(d.users || [])).catch(console.error);
    }
  }, [user]);

  if (authLoading || !user) {
    return <div className="min-h-screen flex items-center justify-center text-[var(--text-dim)]">Carregando...</div>;
  }

  return (
    <div className="min-h-screen">
      <header className="border-b border-[var(--border)] bg-[var(--surface)]">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/painel" className="text-xl font-bold">Dezafira Club</Link>
            <span className="badge text-[var(--warning)]">Admin</span>
          </div>
          <Link href="/painel" className="text-sm text-[var(--text-dim)] hover:text-[var(--text)]">← Voltar ao Painel</Link>
        </div>
      </header>

      <div className="border-b border-[var(--border)]">
        <div className="max-w-6xl mx-auto px-4 flex gap-1 overflow-x-auto">
          {([
            { id: "stats", label: "Estatisticas" },
            { id: "fabrica-blog", label: "Fabrica Blog" },
            { id: "fabrica-ebook", label: "Fabrica Ebook" },
            { id: "fabrica-curso", label: "Fabrica Curso" },
            { id: "marketing", label: "Fábrica Marketing" },
            { id: "trilhas", label: "Trilhas" },
            { id: "users", label: "Usuarios" },
            { id: "combos", label: "Combos" },
            { id: "analytics", label: "Analytics" },
          ] as const).map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
                tab === t.id
                  ? "border-[var(--brand)] text-[var(--brand)]"
                  : "border-transparent text-[var(--text-dim)] hover:text-[var(--text)]"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>

      <main className="max-w-6xl mx-auto px-4 py-8">
        {tab === "stats" && stats && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { label: "Usuários", value: stats.total_users, icon: "👥" },
              { label: "Blogs", value: stats.total_blogs, icon: "📝" },
              { label: "Livros", value: stats.total_books, icon: "📗" },
              { label: "Cursos", value: stats.total_courses, icon: "🎓" },
              { label: "Combos", value: stats.total_combos, icon: "🎁" },
              { label: "Vendas Combo", value: stats.total_combo_sales, icon: "💰" },
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

        {tab === "combos" && <CombosAdmin />}

        {tab === "fabrica-blog" && (
          <div className="text-center py-12">
            <h2 className="text-2xl font-bold mb-2">Fabrica de Blogs</h2>
            <p className="text-[var(--text-dim)] mb-4">Gerencie blogs e artigos do sistema</p>
            <a href="/admin/fabrica-blog" className="btn-primary inline-block">Acessar</a>
          </div>
        )}

        {tab === "fabrica-ebook" && (
          <div className="text-center py-12">
            <h2 className="text-2xl font-bold mb-2">Fabrica de Ebooks</h2>
            <p className="text-[var(--text-dim)] mb-4">Gerencie ebooks e checkout</p>
            <a href="/admin/fabrica-ebook" className="btn-primary inline-block">Acessar</a>
          </div>
        )}

        {tab === "fabrica-curso" && (
          <div className="text-center py-12">
            <h2 className="text-2xl font-bold mb-2">Fabrica de Cursos</h2>
            <p className="text-[var(--text-dim)] mb-4">Pipeline de cursos com IA + gestao de conteudo</p>
            <a href="/admin/fabrica-curso" className="btn-primary inline-block">Acessar</a>
          </div>
        )}

        {tab === "trilhas" && (
          <div className="text-center py-12">
            <h2 className="text-2xl font-bold mb-2">Trilhas de Aprendizado</h2>
            <p className="text-[var(--text-dim)] mb-4">Organize cursos em trilhas sequenciais</p>
            <a href="/admin/trilhas" className="btn-primary inline-block">Acessar</a>
          </div>
        )}

        {tab === "analytics" && (
          <div className="text-center py-12">
            <h2 className="text-2xl font-bold mb-2">Analytics</h2>
            <p className="text-[var(--text-dim)] mb-4">Metricas reais do sistema</p>
            <a href="/admin/analytics" className="btn-primary inline-block">Acessar</a>
          </div>
        )}

        {tab === "marketing" && (
          <div className="text-center py-12">
            <h2 className="text-2xl font-bold mb-2">Fábrica de Marketing Digital</h2>
            <p className="text-[var(--text-dim)] mb-4">Crie funis previsíveis baseados no framework de Sabri Suby</p>
            <a href="/admin/fabrica-blog#marketing" className="btn-primary inline-block">Acessar</a>
          </div>
        )}
      </main>
    </div>
  );
}

function CombosAdmin() {
  const [combos, setCombos] = useState<any[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ name: "", description: "", ebook_id: "", course_id: "", original_price_cents: 0, combo_price_cents: 0, slug: "" });

  useEffect(() => {
    api.getCombos().then((d) => setCombos(d.combos || [])).catch(console.error);
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.createCombo(form);
      setShowForm(false);
      setForm({ name: "", description: "", ebook_id: "", course_id: "", original_price_cents: 0, combo_price_cents: 0, slug: "" });
      api.getCombos().then((d) => setCombos(d.combos || []));
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Remover combo?")) return;
    try {
      await api.deleteCombo(id);
      setCombos(combos.filter((c) => c.id !== id));
    } catch (err: any) {
      alert(err.message);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-semibold">Combos</h2>
        <button onClick={() => setShowForm(!showForm)} className="btn-secondary text-sm">
          {showForm ? "Cancelar" : "+ Novo Combo"}
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleCreate} className="card space-y-4">
          <input className="input" placeholder="Nome" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
          <input className="input" placeholder="Descrição" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
          <div className="grid grid-cols-2 gap-4">
            <input className="input" placeholder="Ebook ID" value={form.ebook_id} onChange={(e) => setForm({ ...form, ebook_id: e.target.value })} />
            <input className="input" placeholder="Curso ID" value={form.course_id} onChange={(e) => setForm({ ...form, course_id: e.target.value })} />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <input className="input" type="number" placeholder="Preço Original (centavos)" value={form.original_price_cents} onChange={(e) => setForm({ ...form, original_price_cents: Number(e.target.value) })} />
            <input className="input" type="number" placeholder="Preço Combo (centavos)" value={form.combo_price_cents} onChange={(e) => setForm({ ...form, combo_price_cents: Number(e.target.value) })} />
          </div>
          <button type="submit" className="btn-primary">Criar Combo</button>
        </form>
      )}

      <div className="space-y-3">
        {combos.map((c) => (
          <div key={c.id} className="card flex items-center gap-4">
            <div className="flex-1">
              <h3 className="font-semibold">{c.name}</h3>
              <p className="text-sm text-[var(--text-dim)]">{c.description}</p>
              <div className="flex gap-3 mt-2 text-sm">
                <span className="text-[var(--success)]">-{c.discount_pct}%</span>
                <span>R$ {(c.combo_price_cents / 100).toFixed(2)}</span>
                <span className="line-through text-[var(--text-dim)]">R$ {(c.original_price_cents / 100).toFixed(2)}</span>
              </div>
            </div>
            <button onClick={() => handleDelete(c.id)} className="text-sm text-[var(--error)] hover:underline">Remover</button>
          </div>
        ))}
      </div>
    </div>
  );
}
