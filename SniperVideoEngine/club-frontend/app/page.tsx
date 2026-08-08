"use client";

import { useAuth } from "../lib/auth-context";
import Link from "next/link";
import React from "react";

export default function HomePage() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#0a0a0f]">
        <div className="animate-pulse text-[var(--text-dim)] text-lg">Carregando...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0a0a0f]">
      {/* Navbar */}
      <nav className="fixed top-0 w-full z-50 bg-[#0a0a0f]/80 backdrop-blur-xl border-b border-white/5">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white font-bold text-sm">D</div>
            <span className="text-lg font-bold text-white">Dezafira Club</span>
          </div>
          <div className="flex items-center gap-4">
            {user ? (
              <Link href="/painel" className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm font-medium transition-colors">
                Meu Painel
              </Link>
            ) : (
              <>
                <Link href="/auth/login" className="text-sm text-gray-400 hover:text-white transition-colors">Entrar</Link>
                <Link href="/auth/register" className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm font-medium transition-colors">
                  Comece Grátis
                </Link>
              </>
            )}
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative pt-32 pb-24 overflow-hidden">
        {/* Background */}
        <div className="absolute inset-0">
          <div className="absolute inset-0 bg-gradient-to-b from-indigo-600/10 via-transparent to-transparent" />
          <div className="absolute top-20 left-1/2 -translate-x-1/2 w-[800px] h-[400px] bg-indigo-500/10 rounded-full blur-[120px]" />
          <div className="absolute inset-0" style={{backgroundImage: "url('/images/hero-bg.svg')", backgroundSize: "cover", opacity: 0.4}} />
        </div>
        <div className="relative max-w-4xl mx-auto px-4 text-center">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs font-medium mb-6">
            <span className="w-2 h-2 rounded-full bg-indigo-400 animate-pulse" />
            Plataforma de cursos e ebooks
          </div>
          <h1 className="text-5xl md:text-7xl font-bold mb-6 leading-tight">
            <span className="bg-gradient-to-r from-white via-white to-gray-400 bg-clip-text text-transparent">Transforme</span>{" "}
            <span className="bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">conhecimento</span>
            <br />
            <span className="bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent">em resultados</span>
          </h1>
          <p className="text-xl text-gray-400 mb-10 max-w-2xl mx-auto leading-relaxed">
            Cursos, ebooks e ferramentas práticas para você evoluir e alcançar seus objetivos.
          </p>
          {!user ? (
            <div className="flex gap-4 justify-center">
              <Link href="/auth/register" className="px-8 py-4 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-lg font-semibold transition-all hover:shadow-lg hover:shadow-indigo-500/25">
                Comece Agora
              </Link>
              <Link href="/auth/login" className="px-8 py-4 bg-white/5 hover:bg-white/10 border border-white/10 text-white rounded-xl text-lg font-medium transition-all">
                Já tenho conta
              </Link>
            </div>
          ) : (
            <Link href="/painel" className="inline-flex px-8 py-4 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-lg font-semibold transition-all hover:shadow-lg hover:shadow-indigo-500/25">
              Ir para o Painel →
            </Link>
          )}
        </div>
      </section>

      {/* Features */}
      <section className="max-w-6xl mx-auto px-4 py-24">
        <div className="text-center mb-16">
          <h2 className="text-3xl font-bold text-white mb-4">Tudo que você precisa</h2>
          <p className="text-gray-400 max-w-lg mx-auto">Um ecossistema completo para aprender, evoluir e crescer.</p>
        </div>
        <div className="grid md:grid-cols-3 gap-6">
          {[
            { icon: "📚", title: "Ebooks", desc: "Conteúdo aprofundado sobre temas que importam para sua jornada.", color: "from-blue-500/20 to-indigo-500/20", border: "border-blue-500/20" },
            { icon: "🎓", title: "Cursos", desc: "Aprenda no seu ritmo com módulos, aulas e quizzes interativos.", color: "from-purple-500/20 to-pink-500/20", border: "border-purple-500/20" },
            { icon: "🏆", title: "Gamificação", desc: "Ganhe pontos, conquiste badges e suba no ranking da comunidade.", color: "from-amber-500/20 to-orange-500/20", border: "border-amber-500/20" },
          ].map((f) => (
            <div key={f.title} className={`relative group rounded-2xl border ${f.border} bg-gradient-to-br ${f.color} p-8 hover:scale-[1.02] transition-all duration-300`}>
              <div className="text-4xl mb-4">{f.icon}</div>
              <h3 className="text-xl font-semibold text-white mb-2">{f.title}</h3>
              <p className="text-gray-400 leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Combos */}
      <section className="max-w-6xl mx-auto px-4 py-24">
        <div className="text-center mb-16">
          <h2 className="text-3xl font-bold text-white mb-4">Ofertas Exclusivas</h2>
          <p className="text-gray-400 max-w-lg mx-auto">Combos com desconto para acelerar seu progresso.</p>
        </div>
        <CombosSection />
      </section>

      {/* Ranking */}
      <section className="max-w-6xl mx-auto px-4 py-24">
        <div className="text-center mb-16">
          <h2 className="text-3xl font-bold text-white mb-4">Ranking da Comunidade</h2>
          <p className="text-gray-400 max-w-lg mx-auto">Veja quem está liderando em pontos e dedicação.</p>
        </div>
        <RankingSection />
      </section>

      {/* CTA */}
      <section className="max-w-6xl mx-auto px-4 py-24">
        <div className="relative rounded-3xl bg-gradient-to-br from-indigo-600/20 via-purple-600/10 to-indigo-600/20 border border-indigo-500/20 p-12 text-center overflow-hidden">
          <div className="absolute inset-0 bg-[url('/images/hero-bg.svg')] bg-cover opacity-20" />
          <div className="relative">
            <h2 className="text-3xl font-bold text-white mb-4">Pronto para começar?</h2>
            <p className="text-gray-400 mb-8 max-w-lg mx-auto">Junte-se à comunidade e comece sua jornada agora.</p>
            <Link href={user ? "/painel" : "/auth/register"} className="inline-flex px-8 py-4 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-lg font-semibold transition-all hover:shadow-lg hover:shadow-indigo-500/25">
              {user ? "Ir para o Painel" : "Criar Conta Grátis"}
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/5 py-8">
        <div className="max-w-6xl mx-auto px-4 flex items-center justify-between text-sm text-gray-500">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white font-bold text-xs">D</div>
            <span>Dezafira Club</span>
          </div>
          <span>&copy; 2026 Dezafira</span>
        </div>
      </footer>
    </div>
  );
}

function CombosSection() {
  const [combos, setCombos] = React.useState<any[]>([]);
  React.useEffect(() => {
    fetch(`${process.env.NEXT_PUBLIC_API_URL || ""}/api/v1/combos`)
      .then((r) => r.json())
      .then((d) => setCombos(d.combos || []))
      .catch(() => {});
  }, []);

  if (combos.length === 0) {
    return (
      <div className="rounded-2xl border border-white/5 bg-white/[0.02] p-12 text-center">
        <div className="text-4xl mb-4">🎁</div>
        <p className="text-gray-400">Em breve novos combos disponíveis!</p>
      </div>
    );
  }

  return (
    <div className="grid md:grid-cols-2 gap-6">
      {combos.map((c) => (
        <div key={c.id} className="rounded-2xl border border-white/5 bg-white/[0.02] p-6 hover:border-indigo-500/30 transition-all group">
          <div className="flex justify-between items-start mb-4">
            <h3 className="text-xl font-semibold text-white">{c.name}</h3>
            <span className="px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 text-xs font-medium">-{c.discount_pct}%</span>
          </div>
          <p className="text-gray-400 mb-6">{c.description}</p>
          <div className="flex items-baseline gap-3">
            <span className="text-2xl font-bold text-indigo-400">R$ {(c.combo_price_cents / 100).toFixed(2)}</span>
            <span className="text-sm line-through text-gray-500">R$ {(c.original_price_cents / 100).toFixed(2)}</span>
          </div>
        </div>
      ))}
    </div>
  );
}

function RankingSection() {
  const [ranking, setRanking] = React.useState<any[]>([]);
  React.useEffect(() => {
    fetch(`${process.env.NEXT_PUBLIC_API_URL || ""}/api/v1/ranking`)
      .then((r) => r.json())
      .then((d) => setRanking(d.ranking || []))
      .catch(() => {});
  }, []);

  if (ranking.length === 0) {
    return (
      <div className="rounded-2xl border border-white/5 bg-white/[0.02] p-12 text-center">
        <div className="text-4xl mb-4">🏆</div>
        <p className="text-gray-400">Seja o primeiro no ranking!</p>
      </div>
    );
  }

  const medals = ["🥇", "🥈", "🥉"];

  return (
    <div className="rounded-2xl border border-white/5 bg-white/[0.02] overflow-hidden">
      <div className="divide-y divide-white/5">
        {ranking.slice(0, 10).map((r) => (
          <div key={r.user_id} className="flex items-center gap-4 px-6 py-4 hover:bg-white/[0.02] transition-colors">
            <span className={`text-lg font-bold w-10 text-center ${r.position <= 3 ? "" : "text-gray-500"}`}>
              {r.position <= 3 ? medals[r.position - 1] : `#${r.position}`}
            </span>
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white text-sm font-bold">
              {r.name?.charAt(0) || "?"}
            </div>
            <span className="flex-1 font-medium text-white">{r.name}</span>
            <span className="text-indigo-400 font-semibold">{r.total_points} pts</span>
          </div>
        ))}
      </div>
    </div>
  );
}
