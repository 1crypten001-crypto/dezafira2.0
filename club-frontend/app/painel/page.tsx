"use client";

export const dynamic = 'force-dynamic';



import { useAuth } from "../../lib/auth-context";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "../../lib/api";
import Link from "next/link";

export default function PainelPage() {
  const { user, loading: authLoading, logout } = useAuth();
  const router = useRouter();
  const [dashboard, setDashboard] = useState<any>(null);
  const [tab, setTab] = useState<"offers" | "overview" | "courses" | "ebooks">("offers");
  const [selectedOffer, setSelectedOffer] = useState<any>(null);

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
    <div className="min-h-screen bg-[#060911] text-[#f8fafc]">
      {/* Header */}
      <header className="border-b border-[#1e293b] bg-[#090d16]">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <Link href="/" className="text-xl font-bold text-[#38bdf8]">Dezafira</Link>
          <div className="flex items-center gap-4">
            <span className="text-sm text-[var(--text-dim)]">{user.name}</span>
            {user.role === "admin" && (
              <Link href="/admin" className="text-sm text-[var(--warning)] font-bold hover:underline">Painel Admin →</Link>
            )}
            <button onClick={logout} className="text-sm text-[var(--text-dim)] hover:text-[var(--error)]">Sair</button>
          </div>
        </div>
      </header>

      {/* Tabs */}
      <div className="border-b border-[#1e293b] bg-[#090d16]">
        <div className="max-w-6xl mx-auto px-4 flex gap-1">
          {(["offers", "overview", "courses", "ebooks"] as const).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                tab === t
                  ? "border-[#38bdf8] text-[#38bdf8] font-bold bg-[#131c2e]"
                  : "border-transparent text-[var(--text-dim)] hover:text-[var(--text)]"
              }`}
            >
              {t === "offers" ? "🎯 Ofertas Criadas no Ecossistema" : t === "overview" ? "Visão Geral" : t === "courses" ? "Cursos" : "Ebooks"}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <main className="max-w-6xl mx-auto px-4 py-8">
        {tab === "offers" && <OffersTab onSelectOffer={setSelectedOffer} />}
        {tab === "overview" && <OverviewTab dashboard={dashboard} />}
        {tab === "courses" && <CoursesTab />}
        {tab === "ebooks" && <EbooksTab dashboard={dashboard} />}
      </main>

      {/* Modal de Detalhes da Oferta Completa */}
      {selectedOffer && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-[#090d16] border border-[#1e293b] rounded-2xl max-w-3xl w-full p-6 space-y-6 shadow-2xl">
            <div className="flex justify-between items-start border-b border-[#1e293b] pb-4">
              <div>
                <span className="badge text-[var(--success)] text-xs mb-1 inline-block">🟢 Oferta Ativa & Sincronizada</span>
                <h2 className="text-xl font-bold text-[#f1f5f9]">{selectedOffer.title}</h2>
                <p className="text-xs text-[#38bdf8] italic mt-1">"{selectedOffer.headline}"</p>
              </div>
              <button
                onClick={() => setSelectedOffer(null)}
                className="text-gray-400 hover:text-white text-xl font-bold p-1"
              >
                ✕
              </button>
            </div>

            {/* Grid dos Entregáveis Funcionais */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              
              {/* MiniApp Quiz (Produto Principal) */}
              <div className="bg-[#131c2e] border border-[#eab30855] rounded-xl p-4 space-y-2">
                <div className="flex items-center gap-2 text-[#eab308] font-bold text-sm">
                  <span>📱</span> MiniApp Quiz (Produto Recorrência)
                </div>
                <p className="text-xs text-gray-300">
                  Aplicativo PWA interativo funcional com diagnósticos dinâmicos e captura de leads.
                </p>
                <a
                  href={selectedOffer.miniapp_url || "https://dezafiraadm-production.up.railway.app/api/v1/hermes/preview/sess_oferta2026/miniapp"}
                  target="_blank"
                  className="block w-full text-center bg-[#eab30822] text-[#facc15] border border-[#eab30855] py-2 rounded-lg text-xs font-bold hover:bg-[#eab30844]"
                >
                  ▶️ Testar MiniApp Quiz PWA
                </a>
              </div>

              {/* Funil & Checkout Asaas */}
              <div className="bg-[#131c2e] border border-[#22c55e55] rounded-xl p-4 space-y-2">
                <div className="flex items-center gap-2 text-[#4ade80] font-bold text-sm">
                  <span>💻</span> Página VSL & Checkout Asaas PIX
                </div>
                <p className="text-xs text-gray-300">
                  Página de vendas VSL completa com gateway de pagamento Asaas PIX ativo.
                </p>
                <a
                  href={selectedOffer.sales_page_url}
                  target="_blank"
                  className="block w-full text-center bg-[#22c55e22] text-[#4ade80] border border-[#22c55e55] py-2 rounded-lg text-xs font-bold hover:bg-[#22c55e44]"
                >
                  🚀 Ver VSL & Checkout PIX
                </a>
              </div>

              {/* Ebook 3D & Curso HD */}
              <div className="bg-[#131c2e] border border-[#8b5cf655] rounded-xl p-4 space-y-2">
                <div className="flex items-center gap-2 text-[#c084fc] font-bold text-sm">
                  <span>📗</span> Ebook 3D & Curso HD (Agnes AI)
                </div>
                <p className="text-xs text-gray-300">
                  Visualizador com 8 capítulos do Ebook e 5 Módulos em vídeo do Curso.
                </p>
                <a
                  href={selectedOffer.products_url || "https://dezafiraadm-production.up.railway.app/api/v1/hermes/preview/sess_oferta2026/products"}
                  target="_blank"
                  className="block w-full text-center bg-[#8b5cf622] text-[#c084fc] border border-[#8b5cf655] py-2 rounded-lg text-xs font-bold hover:bg-[#8b5cf644]"
                >
                  📦 Ver Ebook & Curso HD
                </a>
              </div>

              {/* Blog SEO Vinculado */}
              <div className="bg-[#131c2e] border border-[#38bdf855] rounded-xl p-4 space-y-2">
                <div className="flex items-center gap-2 text-[#38bdf8] font-bold text-sm">
                  <span>📝</span> Blog SEO (Artigo Completo)
                </div>
                <p className="text-xs text-gray-300">
                  Artigo de autoridade completo com imagens Agnes AI gerando tráfego orgânico.
                </p>
                <a
                  href={selectedOffer.blog_url}
                  target="_blank"
                  className="block w-full text-center bg-[#38bdf822] text-[#38bdf8] border border-[#38bdf855] py-2 rounded-lg text-xs font-bold hover:bg-[#38bdf844]"
                >
                  📝 Ler Artigo do Blog
                </a>
              </div>

              {/* Canais Postiz */}
              <div className="bg-[#131c2e] border border-[#f472b655] rounded-xl p-4 space-y-2 md:col-span-2">
                <div className="flex items-center gap-2 text-[#f472b6] font-bold text-sm">
                  <span>📢</span> Distribuição Multicanal Postiz Ads
                </div>
                <p className="text-xs text-gray-300">
                  Anúncios visuais no Instagram, TikTok, Pinterest e X: {selectedOffer.postiz_channels.join(", ")}.
                </p>
                <a
                  href={selectedOffer.ads_url || "https://dezafiraadm-production.up.railway.app/api/v1/hermes/preview/sess_oferta2026/ads"}
                  target="_blank"
                  className="block w-full text-center bg-[#f472b622] text-[#f472b6] border border-[#f472b655] py-2 rounded-lg text-xs font-bold hover:bg-[#f472b644]"
                >
                  📢 Ver Anúncios em Todas as Redes
                </a>
              </div>

            </div>

            <div className="border-t border-[#1e293b] pt-4 flex justify-end">
              <button
                onClick={() => setSelectedOffer(null)}
                className="bg-[#1e293b] text-white px-6 py-2 rounded-lg text-xs font-bold hover:bg-[#334155]"
              >
                Fechar Hub
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function OffersTab({ onSelectOffer }: { onSelectOffer: (offer: any) => void }) {
  const offersList = [
    {
      id: "off_2026",
      title: "Escola de Negócios Digitais com IA & Automação 2026",
      headline: "A metodologia exata dos agentes autônomos para gerar funis, produtos e anúncios em minutos",
      price: "R$ 97,00",
      status: "active",
      blog_url: "https://dezafiraadm-production.up.railway.app/api/v1/hermes/preview/sess_oferta2026/blog",
      sales_page_url: "https://dezafiraadm-production.up.railway.app/api/v1/hermes/preview/sess_oferta2026/funnel",
      miniapp_url: "https://dezafiraadm-production.up.railway.app/api/v1/hermes/preview/sess_oferta2026/miniapp",
      products_url: "https://dezafiraadm-production.up.railway.app/api/v1/hermes/preview/sess_oferta2026/products",
      ads_url: "https://dezafiraadm-production.up.railway.app/api/v1/hermes/preview/sess_oferta2026/ads",
      checkout_url: "https://dezafiraadm-production.up.railway.app/api/v1/hermes/preview/sess_oferta2026/funnel",
      deliverables: ["Artigo de Blog SEO", "Ebook 3D (8 Capítulos)", "Curso HD (5 Módulos)", "MiniApp Quiz PWA", "Checkout Asaas PIX"],
      postiz_channels: ["Instagram", "TikTok", "Pinterest", "X (Twitter)", "YouTube Shorts"]
    },
    {
      id: "off_1",
      title: "Dominando IA e Automação de Infoprodutos",
      headline: "Como construir um negócio digital de alta escala sem precisar de agências ou gravar vídeos",
      price: "R$ 97,00",
      status: "active",
      blog_url: "https://dezafiraadm-production.up.railway.app/api/v1/hermes/preview/sess_admin/blog",
      sales_page_url: "https://dezafiraadm-production.up.railway.app/api/v1/hermes/preview/sess_admin/funnel",
      miniapp_url: "https://dezafiraadm-production.up.railway.app/api/v1/hermes/preview/sess_admin/miniapp",
      products_url: "https://dezafiraadm-production.up.railway.app/api/v1/hermes/preview/sess_admin/products",
      ads_url: "https://dezafiraadm-production.up.railway.app/api/v1/hermes/preview/sess_admin/ads",
      checkout_url: "https://dezafiraadm-production.up.railway.app/api/v1/hermes/preview/sess_admin/funnel",
      deliverables: ["Ebook Capa 3D", "Curso 5 Módulos HD", "MiniApp Quiz Interativo (Recorrência)"],
      postiz_channels: ["Instagram", "TikTok", "Pinterest", "X (Twitter)", "YouTube Shorts"]
    },
    {
      id: "off_2",
      title: "O Reino — Sabedoria e Vida Prática",
      headline: "Estudos bíblicos aprofundados, devocionais e ebooks práticos para o dia a dia",
      price: "R$ 47,00",
      status: "active",
      blog_url: "https://www.dezafira.com.br/blog/o-reino",
      sales_page_url: "https://www.dezafira.com.br/blog/o-reino",
      miniapp_url: "https://dezafiraadm-production.up.railway.app/api/v1/hermes/preview/sess_admin/products",
      checkout_url: "https://www.dezafira.com.br",
      deliverables: ["Ebook Devocional", "MiniApp Quiz Bíblico (Recorrência)"],
      postiz_channels: ["Instagram", "Pinterest", "YouTube Shorts"]
    }
  ];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-xl font-bold text-[#38bdf8]">🎯 Ofertas Criadas no Ecossistema</h2>
          <p className="text-sm text-[var(--text-dim)]">
            Gerencie todas as esteiras ativas. Clique no Hub para testar a Página de Vendas, o MiniApp e os entregáveis.
          </p>
        </div>
        <Link href="/admin" className="btn-primary text-xs px-4 py-2">
          + Criar Nova Oferta com Hermes
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {offersList.map((off) => (
          <div key={off.id} className="card bg-[#090d16] border border-[#1e293b] p-6 space-y-4 shadow-xl">
            <div className="flex justify-between items-start">
              <div>
                <span className="badge text-[var(--success)] mb-2 inline-block">🟢 Oferta Ativa</span>
                <h3 className="text-lg font-bold text-[#f1f5f9]">{off.title}</h3>
              </div>
              <span className="text-lg font-extrabold text-[#38bdf8]">{off.price}</span>
            </div>

            <p className="text-xs text-[var(--text-dim)] italic border-l-2 border-[#38bdf8] pl-3">
              "{off.headline}"
            </p>

            {/* Entregáveis Vinculados */}
            <div>
              <div className="text-xs font-bold text-[#c084fc] mb-1">🎁 Entregáveis na Oferta:</div>
              <div className="flex gap-2 flex-wrap text-xs">
                {off.deliverables.map((item, i) => (
                  <span key={i} className="bg-[#131c2e] text-[#f1f5f9] px-2 py-1 rounded border border-[#1e293b]">
                    {item}
                  </span>
                ))}
              </div>
            </div>

            {/* Redes Conectadas pelo Postiz */}
            <div>
              <div className="text-xs font-bold text-[#f472b6] mb-1">📢 Distribuição (Postiz Ads):</div>
              <div className="flex gap-1 flex-wrap text-[10px]">
                {off.postiz_channels.map((ch, i) => (
                  <span key={i} className="bg-[#1e293b] text-[#38bdf8] px-2 py-0.5 rounded">
                    {ch}
                  </span>
                ))}
              </div>
            </div>

            {/* Ações e Links Direct */}
            <div className="grid grid-cols-2 gap-2 pt-2 border-t border-[#1e293b]">
              <button
                onClick={() => onSelectOffer(off)}
                className="text-center text-xs bg-[#38bdf822] text-[#38bdf8] py-2 rounded font-semibold hover:bg-[#38bdf844] border border-[#38bdf855]"
              >
                🔍 Abrir Hub da Oferta
              </button>
              <a
                href={off.sales_page_url}
                target="_blank"
                className="text-center text-xs bg-[#22c55e22] text-[#4ade80] py-2 rounded font-semibold hover:bg-[#22c55e44] border border-[#22c55e44]"
              >
                🚀 Página & Checkout
              </a>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function OverviewTab({ dashboard }: { dashboard: any }) {
  if (!dashboard) return <div className="text-[var(--text-dim)]">Carregando...</div>;
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
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
    </div>
  );
}

function CoursesTab() {
  return (
    <div className="card text-center text-[var(--text-dim)]">
      Cursos disponíveis no catálogo da plataforma.
    </div>
  );
}

function EbooksTab({ dashboard }: { dashboard: any }) {
  return (
    <div className="card text-center text-[var(--text-dim)]">
      {dashboard?.ebooks_owned || 0} ebooks em sua coleção.
    </div>
  );
}
