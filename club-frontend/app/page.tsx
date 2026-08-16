"use client";

import { useAuth } from "../lib/auth-context";
import Link from "next/link";

export default function HomePage() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#182828]">
        <div className="animate-pulse text-indigo-400 text-lg font-medium">Carregando...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#182828] text-white selection:bg-[#f85808]/30 selection:text-white">
      {/* Navbar */}
      <nav className="fixed top-0 w-full z-50 bg-[#182828]/80 backdrop-blur-xl border-b border-white/5">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#f85808] to-[#c2410c] flex items-center justify-center text-white font-bold text-sm">D</div>
            <span className="text-lg font-bold text-white tracking-wide">Dezafira</span>
          </div>
          <div className="flex items-center gap-4">
            {user ? (
              <Link href="/painel" className="px-4 py-2 bg-[var(--brand)] hover:bg-[var(--brand-hover)] text-white rounded-lg text-sm font-medium transition-all duration-200 shadow-md">
                Painel
              </Link>
            ) : (
              <Link href="/auth/login" className="px-4 py-2 bg-[var(--brand)] hover:bg-[var(--brand-hover)] text-white rounded-lg text-sm font-medium transition-all duration-200 shadow-md">
                Entrar
              </Link>
            )}
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative pt-36 pb-24 overflow-hidden">
        <div className="absolute inset-0 z-0">
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[900px] h-[400px] bg-gradient-to-br from-[#f85808]/15 via-[#c2410c]/5 to-transparent rounded-full blur-[140px]" />
          <div className="absolute top-1/3 right-1/4 w-[300px] h-[300px] bg-[#f85808]/10 rounded-full blur-[100px]" />
        </div>

        <div className="relative z-10 max-w-4xl mx-auto px-4 text-center">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[var(--brand-soft)] border border-[var(--brand)] text-[var(--brand)] text-xs font-medium mb-6 animate-fade-in">
            <span className="w-1.5 h-1.5 rounded-full bg-[var(--brand)] animate-ping" />
            Painel de Administração
          </div>
          <h1 className="text-5xl md:text-7xl font-extrabold mb-6 leading-tight tracking-tight">
            <span className="bg-gradient-to-r from-white via-white to-gray-400 bg-clip-text text-transparent">Suas Fábricas</span>{" "}
            <span className="bg-gradient-to-r from-[#ff7a2a] via-[#f85808] to-[#c2410c] bg-clip-text text-transparent">Sob Controle</span>
            <br />
            <span className="bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent">e em Escala</span>
          </h1>
          <p className="text-xl text-gray-400 mb-10 max-w-2xl mx-auto leading-relaxed font-light">
            Gerencie blogs inteligentes, ebooks profissionais, cursos e trilhas de aprendizado — tudo integrado com analytics.
          </p>
          {!user ? (
            <div className="flex gap-4 justify-center">
              <Link href="/auth/login" className="px-8 py-4 bg-[var(--brand)] hover:bg-[var(--brand-hover)] text-white rounded-xl text-lg font-semibold transition-all hover:shadow-lg">
                Entrar no Painel
              </Link>
            </div>
          ) : (
            <Link href="/painel" className="inline-flex px-8 py-4 bg-purple-600 hover:bg-purple-500 text-white rounded-xl text-lg font-semibold transition-all hover:shadow-lg hover:shadow-purple-500/25">
              Ir para o Painel
            </Link>
          )}
        </div>
      </section>

      {/* Features Section */}
      <section className="max-w-6xl mx-auto px-4 py-20 relative z-10">
        <div className="text-center mb-16">
          <h2 className="text-3xl font-bold mb-4">Tudo que suas fábricas precisam</h2>
          <p className="text-gray-400 max-w-lg mx-auto">Gerencie conteúdo e engajamento em um único painel.</p>
        </div>
        <div className="grid md:grid-cols-3 gap-6">
          {[
            { icon: "📝", title: "Fábrica Blog", desc: "Crie e publique posts inteligentes com SEO otimizado automaticamente.", color: "from-[#f85808]/10 to-[#c2410c]/5", border: "border-[#f85808]/10" },
            { icon: "📚", title: "Fábrica de Produtos", desc: "Gere ebooks, apps de recorrência e cursos — tudo numa fábrica só.", color: "from-[#ff7a2a]/10 to-[#f85808]/5", border: "border-[#ff7a2a]/10" },
            { icon: "🎓", title: "Fábrica Curso", desc: "Monte trilhas de aprendizado com módulos, aulas e acompanhamento.", color: "from-amber-500/10 to-orange-500/5", border: "border-amber-500/10" },
            { icon: "📊", title: "Analytics", desc: "Acompanhe métricas de engajamento, conversões e crescimento.", color: "from-emerald-500/10 to-teal-500/5", border: "border-emerald-500/10" },
            { icon: "🎯", title: "Entregáveis", desc: "Gerencie e entregue ebooks, cursos e conteúdo exclusivo para seus membros.", color: "from-pink-500/10 to-rose-500/5", border: "border-pink-500/10" },
            { icon: "🚀", title: "Automação", desc: "Automatize processos de criação e publicação com IA.", color: "from-orange-500/10 to-yellow-500/5", border: "border-orange-500/10" },
          ].map((f) => (
            <div key={f.title} className={`relative group rounded-2xl border ${f.border} bg-gradient-to-br ${f.color} p-8 hover:scale-[1.02] hover:border-[var(--brand)] transition-all duration-300`}>
              <div className="text-4xl mb-4">{f.icon}</div>
              <h3 className="text-xl font-semibold text-white mb-2">{f.title}</h3>
              <p className="text-gray-400 leading-relaxed font-light">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* CTA Section */}
      <section className="max-w-6xl mx-auto px-4 py-20 relative z-10">
        <div className="relative rounded-3xl bg-gradient-to-br from-[#f85808]/20 via-[#c2410c]/10 to-[#f85808]/20 border border-[#f85808]/25 p-12 text-center overflow-hidden">
          <div className="relative">
            <h2 className="text-3xl font-bold mb-4">Pronto para escalar suas fábricas?</h2>
            <p className="text-gray-400 mb-8 max-w-lg mx-auto">Junte-se à Dezafira e tenha controle total sobre seus conteúdos.</p>
            <Link href={user ? "/painel" : "/auth/login"} className="inline-flex px-8 py-4 bg-purple-600 hover:bg-purple-500 text-white rounded-xl text-lg font-semibold transition-all hover:shadow-lg hover:shadow-purple-500/25">
              {user ? "Ir para o Painel" : "Comece Agora"}
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/5 py-8 relative z-10">
        <div className="max-w-6xl mx-auto px-4 flex items-center justify-between text-sm text-gray-500">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded bg-gradient-to-br from-[#f85808] to-[#c2410c] flex items-center justify-center text-white font-bold text-xs">D</div>
            <span>Dezafira</span>
          </div>
          <span>&copy; 2026 Dezafira</span>
        </div>
      </footer>
    </div>
  );
}
