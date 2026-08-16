"use client";

export const dynamic = 'force-dynamic';

import { useState, useEffect } from "react";
import Link from "next/link";
import { useAuth } from "../../../lib/auth-context";
import { useRouter } from "next/navigation";

const API_URL = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/$/, '');

const authH = () => {
  const t = typeof window !== 'undefined' ? localStorage.getItem('dz_token') : null;
  return t ? { 'Authorization': 'Bearer '+t, 'Content-Type': 'application/json' } : { 'Content-Type': 'application/json' };
}

export default function CanaisHubPage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();

  const [channels, setChannels] = useState<any[]>([]);
  const [loadingList, setLoadingList] = useState(true);

  // Create Form State
  const [showForm, setShowForm] = useState(false);
  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [niche, setNiche] = useState("");
  const [description, setDescription] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (!authLoading) {
      if (!user || user.role !== 'admin') {
        router.push('/painel');
      } else {
        loadChannels();
      }
    }
  }, [user, authLoading, router]);

  const loadChannels = async () => {
    setLoadingList(true);
    try {
      const res = await fetch(`${API_URL}/api/v1/channels`, { headers: authH() });
      if (res.ok) {
        const data = await res.json();
        setChannels(data.channels || []);
      }
    } catch (err) {
      console.error("Erro ao carregar canais:", err);
    } finally {
      setLoadingList(false);
    }
  };

  const handleNameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setName(val);
    setSlug(val.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, ''));
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !slug) return;
    setIsSubmitting(true);
    try {
      const res = await fetch(`${API_URL}/api/v1/channels`, {
        method: "POST",
        headers: authH(),
        body: JSON.stringify({ name, slug, niche, description })
      });
      if (res.ok) {
        setShowForm(false);
        setName("");
        setSlug("");
        setNiche("");
        setDescription("");
        loadChannels();
      } else {
        alert("Erro ao criar canal.");
      }
    } catch (err) {
      console.error("Erro no submit:", err);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (authLoading) return <div className="min-h-screen bg-[var(--ink)] text-[var(--text)] p-8">Carregando...</div>;

  return (
    <div className="min-h-screen bg-[var(--ink)] text-[var(--text)]">
      <header className="border-b border-[var(--border)] bg-[var(--bg)]">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link href="/admin" className="text-sm text-[var(--text-dim)] hover:text-[var(--text)]">← Voltar ao Admin</Link>
            <span className="text-[var(--text-dim)]">/</span>
            <h1 className="text-lg font-bold text-[var(--brand)]">Hub de Canais</h1>
          </div>
          {!showForm && (
            <button 
              onClick={() => setShowForm(true)}
              className="btn-primary bg-[var(--brand)] text-[var(--ink)] font-bold px-4 py-2 rounded-xl text-sm"
            >
              + Criar Novo Canal
            </button>
          )}
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-8 space-y-8">
        <div>
          <h2 className="text-2xl font-bold text-[var(--text)]">Hub de Canais</h2>
          <p className="text-[var(--text-dim)]">Gerencie seus blogs e canais de conteúdo</p>
        </div>

        {showForm && (
          <div className="bg-[var(--bg)] border border-[var(--border)] rounded-2xl p-6 shadow-xl card animate-fade-in">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-bold text-[var(--text)]">Novo Canal</h3>
              <button onClick={() => setShowForm(false)} className="text-[var(--text-dim)] hover:text-[var(--text)]">Cancelar</button>
            </div>
            <form onSubmit={handleCreate} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-[var(--text-dim)] mb-1">NOME DO CANAL</label>
                  <input type="text" value={name} onChange={handleNameChange} required className="input w-full bg-[var(--surface)] border border-[var(--border)] rounded-xl px-4 py-2 text-sm text-[var(--text)] focus:border-[var(--brand)] outline-none" />
                </div>
                <div>
                  <label className="block text-xs font-bold text-[var(--text-dim)] mb-1">SLUG (URL)</label>
                  <input type="text" value={slug} onChange={(e) => setSlug(e.target.value)} required className="input w-full bg-[var(--surface)] border border-[var(--border)] rounded-xl px-4 py-2 text-sm text-[var(--text)] focus:border-[var(--brand)] outline-none" />
                </div>
                <div>
                  <label className="block text-xs font-bold text-[var(--text-dim)] mb-1">NICHO</label>
                  <input type="text" value={niche} onChange={(e) => setNiche(e.target.value)} className="input w-full bg-[var(--surface)] border border-[var(--border)] rounded-xl px-4 py-2 text-sm text-[var(--text)] focus:border-[var(--brand)] outline-none" />
                </div>
                <div className="md:col-span-2">
                  <label className="block text-xs font-bold text-[var(--text-dim)] mb-1">DESCRIÇÃO</label>
                  <textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={3} className="input w-full bg-[var(--surface)] border border-[var(--border)] rounded-xl px-4 py-2 text-sm text-[var(--text)] focus:border-[var(--brand)] outline-none" />
                </div>
              </div>
              <div className="flex justify-end pt-2">
                <button type="submit" disabled={isSubmitting} className="btn-primary bg-[var(--brand)] text-[var(--ink)] font-bold px-6 py-2 rounded-xl text-sm disabled:opacity-50">
                  {isSubmitting ? "Criando..." : "Salvar Canal"}
                </button>
              </div>
            </form>
          </div>
        )}

        {loadingList ? (
          <p className="text-[var(--text-dim)]">Carregando canais...</p>
        ) : channels.length === 0 ? (
          <div className="text-center py-12 bg-[var(--surface)] border border-[var(--border)] rounded-2xl">
            <h3 className="text-lg font-bold text-[var(--text)] mb-2">Nenhum canal criado ainda.</h3>
            <p className="text-[var(--text-dim)] mb-4">Crie o primeiro canal para começar a publicar conteúdo!</p>
            {!showForm && (
              <button onClick={() => setShowForm(true)} className="btn-primary bg-[var(--brand)] text-[var(--ink)] font-bold px-4 py-2 rounded-xl text-sm">
                Criar Novo Canal
              </button>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {channels.map((ch) => (
              <div key={ch.id} className="bg-[var(--bg)] border border-[var(--border)] rounded-2xl p-5 shadow-lg flex flex-col justify-between card hover:border-[var(--brand)]/50 transition-colors">
                <div>
                  <div className="flex justify-between items-start mb-2">
                    <h3 className="text-lg font-bold text-[var(--text)] truncate mr-2">{ch.name || ch.title}</h3>
                    <span className="badge bg-[var(--surface)] text-[var(--brand)] text-xs px-2 py-1 rounded border border-[var(--border)]">
                      /{ch.slug}
                    </span>
                  </div>
                  <p className="text-xs text-[var(--text-dim)] mb-3 line-clamp-2 min-h-[2rem]">
                    {ch.description || "Sem descrição"}
                  </p>
                  <div className="flex items-center gap-4 text-xs text-[var(--text-dim)] mb-4">
                    <span>📝 {ch.post_count || 0} posts</span>
                    <span>📅 {new Date(ch.created_at).toLocaleDateString('pt-BR')}</span>
                  </div>
                </div>
                <div className="pt-4 border-t border-[var(--border)]">
                  <Link href="/admin/fabrica-blog" className="block text-center btn-secondary bg-[var(--surface)] border border-[var(--border)] text-[var(--text)] hover:text-[var(--brand)] hover:border-[var(--brand)] transition-colors py-2 rounded-xl text-sm font-semibold">
                    Ver Posts →
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
