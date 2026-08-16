import React, { useState, useEffect } from 'react';
import './LandingPage.css';
import { sendLeadWebhook } from '../../services/webhookService';

export default function LandingPage() {
  // Calculator State
  const [leads, setLeads] = useState(150);
  const [ticket, setTicket] = useState(1200);
  const [noshow, setNoshow] = useState(25);
  const [base, setBase] = useState(1500);

  // FAQ State
  const [openFaq, setOpenFaq] = useState(null);

  // Final Form State
  const [formData, setFormData] = useState({
    nome: '', email: '', whatsapp: '', clinica: '', faturamento: '', dor_principal: ''
  });
  const [formStatus, setFormStatus] = useState('idle'); // idle, loading, success

  // Calculator logic
  const leadsPerdidos = 0.30 * leads * 0.15 * ticket;
  const conversaoExtra = (leads * 0.70) * 0.15 * ticket;
  const noshowEvitavel = (leads * 0.30) * (noshow / 100 / 2) * ticket;
  const reativacao = base * 0.03 * ticket / 3;
  const perdaTotal = leadsPerdidos + conversaoExtra + noshowEvitavel + reativacao;
  const ganho30 = perdaTotal * 0.30 - 897;

  const fmtBRL = (n) => 'R$ ' + Math.round(n).toLocaleString('pt-BR');
  const fmtInt = (n) => (+n).toLocaleString('pt-BR');

  const handleHeroSubmit = (e) => {
    e.preventDefault();
    const whats = e.target.elements['hero-whatsapp'].value;
    const finalFormEl = document.getElementById('aplicar');
    if (finalFormEl) {
      finalFormEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
    if (whats) {
      setFormData(prev => ({ ...prev, whatsapp: whats }));
    }
    setTimeout(() => {
      document.getElementById('f-name')?.focus();
    }, 600);
  };

  const handleFinalSubmit = async (e) => {
    e.preventDefault();
    setFormStatus('loading');
    try {
      await sendLeadWebhook({ ...formData, origem: 'techla-landing', pagina: window.location.href });
      setFormStatus('success');
      setTimeout(() => {
        const successEl = document.getElementById('form-success');
        if(successEl) successEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }, 100);
    } catch (err) {
      console.error(err);
      setFormStatus('idle');
      alert('Não conseguimos enviar agora. Tente novamente em alguns segundos.');
    }
  };

  const handleChange = (e) => setFormData({ ...formData, [e.target.name]: e.target.value });

  return (
    <div className="landing-page-root">
      <a href="#main" className="skip-link">Pular para o conteúdo</a>

      <nav className="topnav" aria-label="Navegação principal">
        <div className="container nav-inner">
          <a href="#" className="brand" aria-label="Techla, página inicial">Techla<span className="brand-dot">.</span></a>
          <div className="nav-links">
            <a className="nav-link" href="#solucao">Como funciona</a>
            <a className="nav-link" href="#garantia">Garantia</a>
            <a className="nav-link" href="#faq">FAQ</a>
            <a className="nav-link nav-cta" href="#aplicar">Aplicar</a>
          </div>
        </div>
      </nav>

      <main id="main">
        {/* HERO */}
        <section className="hero" aria-labelledby="hero-title">
          <div className="hero-bg" aria-hidden="true"></div>
          <div className="container hero-inner">
            <div>
              <span className="eyebrow dotted">Para clínicas de estética com 2-3 funcionários</span>
              <h1 id="hero-title" className="headline">
                A IA que sua clínica precisa para nunca mais perder uma cliente <em>enquanto você dorme</em>.
              </h1>
              <p className="sub">
                Agente SDR no WhatsApp 24/7, CRM, recuperação de no-show e reativação de base — entregues prontos em 14 dias. Garantia de 30 dias money-back.
              </p>
              <form id="hero-form" className="hero-form" onSubmit={handleHeroSubmit} aria-label="Aplicar para diagnóstico">
                <div className="input-inline">
                  <input id="hero-whatsapp" type="tel" placeholder="WhatsApp da clínica (com DDD)" autoComplete="tel" inputMode="tel" required aria-label="WhatsApp da clínica" />
                  <button type="submit">
                    Quero meu diagnóstico <span className="arrow" aria-hidden="true">→</span>
                  </button>
                </div>
                <div className="form-hint">
                  Sem custo. Sem compromisso. Apenas se fizer sentido pra sua clínica.
                </div>
              </form>
              <div className="hero-trust" aria-label="Garantias">
                <div className="trust-item">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><polyline points="20 6 9 17 4 12"/></svg>
                  14 dias para go-live
                </div>
                <div className="trust-item">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><polyline points="20 6 9 17 4 12"/></svg>
                  30 dias money-back
                </div>
                <div className="trust-item">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><polyline points="20 6 9 17 4 12"/></svg>
                  Atende em pt-BR natural
                </div>
              </div>
            </div>

            <div className="mockup" aria-hidden="true">
              <div className="mockup-inner">
                <div className="mockup-chrome">
                  <div className="mockup-dot"></div>
                  <div className="mockup-dot"></div>
                  <div className="mockup-dot"></div>
                </div>
                <div className="mockup-tabs">
                  <div className="mockup-tab active">WhatsApp · Camila S.</div>
                  <div className="mockup-tab">CRM</div>
                  <div className="mockup-tab">Métricas</div>
                </div>
                <div className="chat">
                  <div className="chat-msg them">Oi! Vocês fazem harmonização orofacial?</div>
                  <div className="chat-time">23:47</div>
                  <div className="chat-msg us">Olá, Camila 💛 Faço, sim. A gente trabalha com bichectomia, preenchimento labial, mandibular e bioestimulador. Posso te explicar como funciona a avaliação?</div>
                  <div className="chat-time">23:47 · IA Techla</div>
                  <div className="chat-msg them">Pode! E o valor de uma avaliação?</div>
                  <div className="chat-msg us">A avaliação é gratuita — 30 minutos pra entender o que você quer e desenhar um protocolo. Tenho terça às 14h ou quinta às 10h dessa semana. Qual fica melhor?</div>
                  <div className="chat-typing">
                    <div className="typing-dot"></div>
                    <div className="typing-dot"></div>
                    <div className="typing-dot"></div>
                  </div>
                </div>
                <div className="mockup-meta">
                  <div className="meta-item"><span className="meta-label">Hoje</span><span className="meta-value">12 leads</span></div>
                  <div className="meta-item"><span className="meta-label">Qualificados</span><span className="meta-value">8</span></div>
                  <div className="meta-item"><span className="meta-label">Agendados</span><span className="meta-value win">5</span></div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* AGITATION */}
        <section className="agit" aria-labelledby="agit-title">
          <div className="container">
            <header className="agit-head">
              <span className="eyebrow">O ralo invisível</span>
              <h2 id="agit-title" className="agit-title">Todo dia, sua clínica perde dinheiro <em>invisível</em>.</h2>
              <p className="agit-lead">Não é sobre vender mais. É sobre parar de perder o que já é seu.</p>
            </header>

            <div className="agit-grid">
              <div className="loss-block">
                <div className="loss-value">R$ 8.000</div>
                <div className="loss-cap">por mês somem em leads que chegam às 22h e nunca são respondidos.</div>
                <div className="loss-quote">
                  "Se a clínica leva horas para responder, o paciente esfria."
                  <span className="loss-source">Valentins Digital, 2024</span>
                </div>
              </div>
              <div className="loss-block">
                <div className="loss-value">R$ 12.000</div>
                <div className="loss-cap">evaporam em no-show. <em>Falta dói no caixa e na agenda.</em></div>
                <div className="loss-quote">
                  1 em cada 3 clínicas brasileiras perde mais de 10% das consultas marcadas.
                  <span className="loss-source">Panorama Clínicas 2026 · n=639</span>
                </div>
              </div>
              <div className="loss-block">
                <div className="loss-value">R$ 6.000</div>
                <div className="loss-cap">estão parados na sua base de WhatsApp inativa.</div>
                <div className="loss-quote">
                  Cliente que sumiu não é destino — é retorno que ninguém marcou.
                  <span className="loss-source">Vocabulário do nicho, adaptado</span>
                </div>
              </div>
            </div>

            <div className="agit-anchor">
              <div className="anchor-inner">
                <div className="anchor-num">21<small>×</small></div>
                <div>
                  <div className="anchor-text">
                    Responder um lead em 5 minutos te dá <em>21x mais chance</em> de fechar venda do que responder em 30.
                  </div>
                  <div className="anchor-source">MIT Lead Response Study · Harvard Business Review</div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* CALCULATOR */}
        <section className="calc-section" aria-labelledby="calc-title">
          <div className="container">
            <header className="section-head">
              <span className="eyebrow">A conta</span>
              <h2 id="calc-title" className="section-title">Faça a conta. Quanto sua clínica perde <em>agora</em>?</h2>
              <p className="section-lead">Use os sliders abaixo com os números reais da sua clínica. O cálculo é conservador.</p>
            </header>

            <div className="calc">
              <div className="calc-inputs">
                <div className="calc-input">
                  <div className="calc-input-head">
                    <span className="calc-input-label">Leads por mês</span>
                    <span className="calc-input-value">{fmtInt(leads)}</span>
                  </div>
                  <input type="range" className="slider" min="50" max="500" step="10" value={leads} onChange={e => setLeads(+e.target.value)} aria-label="Leads recebidos por mês" />
                </div>
                <div className="calc-input">
                  <div className="calc-input-head">
                    <span className="calc-input-label">Ticket médio</span>
                    <span className="calc-input-value">{fmtBRL(ticket)}</span>
                  </div>
                  <input type="range" className="slider" min="300" max="3000" step="50" value={ticket} onChange={e => setTicket(+e.target.value)} aria-label="Ticket médio por procedimento" />
                </div>
                <div className="calc-input">
                  <div className="calc-input-head">
                    <span className="calc-input-label">No-show atual</span>
                    <span className="calc-input-value">{noshow}%</span>
                  </div>
                  <input type="range" className="slider" min="10" max="40" step="1" value={noshow} onChange={e => setNoshow(+e.target.value)} aria-label="Taxa de no-show" />
                </div>
                <div className="calc-input">
                  <div className="calc-input-head">
                    <span className="calc-input-label">Base inativa</span>
                    <span className="calc-input-value">{fmtInt(base)}</span>
                  </div>
                  <input type="range" className="slider" min="200" max="3000" step="50" value={base} onChange={e => setBase(+e.target.value)} aria-label="Tamanho da base inativa" />
                </div>
              </div>
              <div className="calc-output">
                <div className="calc-output-inner">
                  <div className="calc-output-label">Sua clínica perde, por mês:</div>
                  <div className="calc-output-loss">{fmtBRL(perdaTotal)}</div>
                  <div className="calc-output-label">Recuperando 30% com Techla:</div>
                  <div className="calc-output-win">+{fmtBRL(Math.max(0, ganho30))} / mês</div>
                  <div className="calc-output-fineprint">Cenário conservador. Cálculo já desconta a mensalidade de R$ 897.</div>
                </div>
              </div>
            </div>

            <div className="calc-cta-wrap">
              <a href="#aplicar" className="btn btn-primary">
                Quero parar de perder esse dinheiro <span className="arrow" aria-hidden="true">→</span>
              </a>
            </div>

            <p className="calc-transition">Você acabou de calcular o tamanho do ralo. Agora vamos mostrar como fechá-lo.</p>
          </div>
        </section>

        {/* SOLUTION */}
        <section className="solution" id="solucao" aria-labelledby="sol-title">
          <div className="container">
            <header className="section-head">
              <span className="eyebrow">A operação</span>
              <h2 id="sol-title" className="section-title">Não é chatbot. É <em>operação</em>.</h2>
              <p className="section-lead">A Techla monta toda a estrutura comercial da sua clínica com IA. Em 14 dias.</p>
            </header>

            <div className="bento">
              {/* Cards ommitted for brevity, adding a few */}
              <div className="bento-card">
                <svg className="bento-card-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/></svg>
                <div className="bento-card-title">Agente SDR no WhatsApp 24/7</div>
                <div className="bento-card-body">Atende, qualifica e agenda em português natural — treinado com o vocabulário da sua clínica. Não parece robô: acolhe.</div>
              </div>
              <div className="bento-card">
                <svg className="bento-card-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
                <div className="bento-card-title">Agendamento integrado</div>
                <div className="bento-card-body">A agenda fecha sozinha. Lembrete automático 24h antes e 2h antes — no-show despenca.</div>
              </div>
              <div className="bento-card">
                <svg className="bento-card-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><rect x="3" y="3" width="6" height="18" rx="1"/><rect x="11" y="3" width="6" height="11" rx="1"/><rect x="19" y="3" width="2" height="7" rx="1" opacity="0.6"/></svg>
                <div className="bento-card-title">CRM com pipeline visual</div>
                <div className="bento-card-body">Cada lead no funil: novo → qualificado → agendado → fechado. Sem planilha, sem WhatsApp Business bagunçado.</div>
              </div>
            </div>

            <div className="calc-cta-wrap" style={{ marginTop: "64px" }}>
              <a href="#aplicar" className="btn btn-primary">
                Ver como tudo isso funciona junto <span className="arrow" aria-hidden="true">→</span>
              </a>
            </div>
          </div>
        </section>

        {/* COMPARE */}
        <section className="compare-section" aria-labelledby="comp-title">
          <div className="container">
            <header className="section-head">
              <span className="eyebrow">A matemática</span>
              <h2 id="comp-title" className="section-title">Pelo preço de <em>meia secretária</em>, sua clínica ganha uma operação inteira.</h2>
              <p className="section-lead">Comparado a contratar mais uma secretária CLT no interior de MG.</p>
            </header>

            <div className="compare" role="table" aria-label="Comparativo Techla versus secretária CLT">
              <div className="compare-row head" role="row">
                <div role="columnheader">Critério</div>
                <div role="columnheader">Secretária CLT</div>
                <div role="columnheader" className="compare-head-techla">Techla</div>
              </div>
              <div className="compare-row" role="row">
                <div className="compare-criterion" role="cell">Custo mensal real</div>
                <div className="compare-secretaria" role="cell">R$ 2.400 – R$ 2.800</div>
                <div className="compare-techla" role="cell">R$ 897</div>
              </div>
              <div className="compare-row" role="row">
                <div className="compare-criterion" role="cell">Horário de trabalho</div>
                <div className="compare-secretaria" role="cell">8h/dia, seg–sex</div>
                <div className="compare-techla" role="cell">24/7, todos os dias</div>
              </div>
            </div>

            <div className="compare-closing">
              <div className="compare-closing-text">A conta não fecha pro outro lado.</div>
              <a href="#aplicar" className="btn btn-primary">
                Faz mais sentido contratar a Techla <span className="arrow" aria-hidden="true">→</span>
              </a>
            </div>
          </div>
        </section>

        {/* FINAL CTA + FAQ */}
        <section className="final" id="aplicar" aria-labelledby="final-title">
          <div className="container">
            <header className="section-head left">
              <span className="eyebrow">Próximo passo</span>
              <h2 id="final-title" className="section-title">Sua clínica pode atender melhor <em>hoje</em>. Decida agora.</h2>
              <p className="section-lead">Preencha abaixo. Em até 24h, a gente entra em contato pelo WhatsApp para agendar seu diagnóstico gratuito.</p>
            </header>

            <div className="final-grid">
              <div className="form-block" id="form-block">
                {formStatus === 'success' ? (
                  <div id="form-success" className="form-success">
                    <div className="form-success-title">Recebemos <em>sua aplicação</em>.</div>
                    <p className="form-success-body">Em até 24h, a gente entra em contato pelo WhatsApp pra agendar seu diagnóstico — 30 minutos, gratuitos, sem compromisso.</p>
                  </div>
                ) : (
                  <form id="apply-form" aria-label="Aplicar para diagnóstico gratuito" onSubmit={handleFinalSubmit}>
                    <div className="form-row">
                      <label className="label" htmlFor="f-name">Nome <span className="req">*</span></label>
                      <input id="f-name" name="nome" type="text" className="input" placeholder="Seu nome completo" required autoComplete="name" value={formData.nome} onChange={handleChange} disabled={formStatus === 'loading'} />
                    </div>
                    <div className="form-row">
                      <label className="label" htmlFor="f-email">E-mail <span className="req">*</span></label>
                      <input id="f-email" name="email" type="email" className="input" placeholder="voce@suaclinica.com.br" required autoComplete="email" value={formData.email} onChange={handleChange} disabled={formStatus === 'loading'} />
                    </div>
                    <div className="form-row">
                      <label className="label" htmlFor="f-whats">WhatsApp da clínica <span className="req">*</span></label>
                      <input id="f-whats" name="whatsapp" type="tel" className="input" placeholder="(37) 9 9999-9999" required autoComplete="tel" inputMode="tel" value={formData.whatsapp} onChange={handleChange} disabled={formStatus === 'loading'} />
                    </div>
                    <div className="form-row">
                      <label className="label" htmlFor="f-clinic">Nome da clínica <span className="req">*</span></label>
                      <input id="f-clinic" name="clinica" type="text" className="input" placeholder="Nome da sua clínica" required value={formData.clinica} onChange={handleChange} disabled={formStatus === 'loading'} />
                    </div>
                    <div className="form-row">
                      <label className="label" htmlFor="f-fat">Faturamento aproximado <span className="req">*</span></label>
                      <select id="f-fat" name="faturamento" className="select" required value={formData.faturamento} onChange={handleChange} disabled={formStatus === 'loading'}>
                        <option value="">Selecione uma faixa</option>
                        <option value="Até R$ 30 mil/mês">Até R$ 30 mil/mês</option>
                        <option value="R$ 30 a 50 mil/mês">R$ 30 a 50 mil/mês</option>
                        <option value="R$ 50 a 100 mil/mês">R$ 50 a 100 mil/mês</option>
                        <option value="Acima de R$ 100 mil/mês">Acima de R$ 100 mil/mês</option>
                      </select>
                    </div>
                    <div className="form-row">
                      <label className="label" htmlFor="f-pain">Principal dor hoje <span className="req">*</span></label>
                      <select id="f-pain" name="dor_principal" className="select" required value={formData.dor_principal} onChange={handleChange} disabled={formStatus === 'loading'}>
                        <option value="">Selecione</option>
                        <option>Perco lead à noite e fim de semana</option>
                        <option>Tenho muito no-show</option>
                        <option>Secretária sobrecarregada, não vende</option>
                        <option>Base de WhatsApp parada</option>
                        <option>Não consigo crescer sem contratar mais</option>
                        <option>Outra</option>
                      </select>
                    </div>
                    <button type="submit" className="btn btn-primary" disabled={formStatus === 'loading'}>
                      {formStatus === 'loading' ? 'Enviando...' : 'Quero meu diagnóstico gratuito'} <span className="arrow" aria-hidden="true">→</span>
                    </button>
                    <div className="form-commit">
                      Sem custo. Sem compromisso. Se a Techla não fizer sentido pra sua clínica, a gente fala isso na call.
                    </div>
                  </form>
                )}
              </div>

              <div className="faq-block" id="faq">
                <h3>Antes de aplicar, talvez você esteja se <em>perguntando</em>:</h3>
                {[
                  { q: "Vai parecer robô?", a: "Não. O agente é treinado com o vocabulário e o tom da sua clínica..." },
                  { q: "Funciona com o WhatsApp que eu já uso?", a: "Sim. A gente conecta no número que sua clínica já tem via WhatsApp Business API." },
                ].map((faq, i) => (
                  <div key={i} className={`faq-item ${openFaq === i ? 'open' : ''}`}>
                    <button className="faq-q" aria-expanded={openFaq === i} onClick={() => setOpenFaq(openFaq === i ? null : i)}>
                      {faq.q}
                    </button>
                    <div className="faq-a"><div className="faq-a-inner"><p>{faq.a}</p></div></div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>
      </main>

      <footer>
        <div className="container">
          <div className="footer-bottom">
            <div>© 2026 Techla. Operação comercial com IA.</div>
          </div>
        </div>
      </footer>
    </div>
  );
}
