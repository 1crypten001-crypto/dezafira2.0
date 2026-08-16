import React, { useState } from 'react';


// Componente de vídeo local
function ChaminhaVideo({ size = 100 }) {
  const videoRef = React.useRef(null);
  const canvasRef = React.useRef(null);

  React.useEffect(() => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas) return;

    const ctx = canvas.getContext('2d', { willReadFrequently: true });
    let animationFrameId;

    const processFrame = () => {
      if (video.paused || video.ended) {
        animationFrameId = requestAnimationFrame(processFrame);
        return;
      }

      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      try {
        const frame = ctx.getImageData(0, 0, canvas.width, canvas.height);
        const data = frame.data;
        const length = data.length;

        for (let i = 0; i < length; i += 4) {
          const r = data[i + 0];
          const g = data[i + 1];
          const b = data[i + 2];

          // Detecção de tela verde
          if (g > 90 && g > r * 1.15 && g > b * 1.15) {
            data[i + 3] = 0;
          }
        }
        ctx.putImageData(frame, 0, 0);
      } catch (e) {}

      animationFrameId = requestAnimationFrame(processFrame);
    };

    const handlePlay = () => {
      processFrame();
    };

    video.addEventListener('play', handlePlay);
    video.addEventListener('playing', handlePlay);
    video.addEventListener('loadedmetadata', handlePlay);
    video.addEventListener('canplay', handlePlay);

    if (!video.paused) {
      processFrame();
    }

    return () => {
      cancelAnimationFrame(animationFrameId);
      video.removeEventListener('play', handlePlay);
      video.removeEventListener('playing', handlePlay);
    };
  }, []);

  return (
    <div style={{
      width: size,
      height: size,
      display: 'inline-flex',
      alignItems: 'center',
      justifyContent: 'center',
      position: 'relative',
      overflow: 'visible'
    }}>
      <video
        ref={videoRef}
        src="/Imagens/Chaminha.mp4"
        autoPlay
        loop
        muted
        playsInline
        style={{ position: 'absolute', opacity: 0, width: '1px', height: '1px', pointerEvents: 'none' }}
      />
      <canvas
        ref={canvasRef}
        width={160}
        height={160}
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'contain'
        }}
      />
    </div>
  );
}

export default function Onboarding({ onComplete }) {
  const [step, setStep] = useState(0);
  const [respostas, setRespostas] = useState({
    objetivo: '',
    conexao: '',
    horario: '08:00',
    versaoBiblia: 'NVI'
  });

  const objetivos = [
    { key: 'relacionamento', text: '💑 Fortalecer meu relacionamento / casamento' },
    { key: 'paz', text: '🕊️ Reduzir ansiedade e cultivar paz interior' },
    { key: 'espiritual', text: '📖 Crescimento espiritual e leitura bíblica' },
    { key: 'conexoes', text: '🤝 Conectar intencionalmente com amigos e família' }
  ];

  const conexoes = [
    { key: 'oracao', text: '🙏 Momentos diários de oração silenciosa' },
    { key: 'leitura', text: '📖 Leitura e meditação em versículos' },
    { key: 'conselheiro', text: '🤖 Conversas e reflexões com o Conselheiro IA' },
    { key: 'pratica', text: '🚶 Praticar atitudes ativas de carinho e caridade' }
  ];

  const handleNext = () => {
    setStep(prev => prev + 1);
  };

  const handleBack = () => {
    setStep(prev => Math.max(0, prev - 1));
  };

  const selectObjetivo = (val) => {
    setRespostas(prev => ({ ...prev, objetivo: val }));
    handleNext();
  };

  const selectConexao = (val) => {
    setRespostas(prev => ({ ...prev, conexao: val }));
    handleNext();
  };

  const handleFinish = () => {
    localStorage.setItem('onboarding-completed', 'true');
    localStorage.setItem('onboarding-data', JSON.stringify(respostas));
    onComplete(respostas);
  };

  return (
    <div className="onboarding-overlay" style={{
      position: 'fixed',
      top: 0, left: 0, right: 0, bottom: 0,
      backgroundColor: 'var(--bg-app)',
      zIndex: 9999,
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'center',
      alignItems: 'center',
      padding: '24px',
      boxSizing: 'border-box'
    }}>
      <div className="onboarding-card glass-panel" style={{
        width: '100%',
        maxWidth: '400px',
        padding: '30px 24px',
        borderRadius: '24px',
        boxShadow: 'var(--shadow-lg)',
        border: '1px solid var(--slate-border)',
        boxSizing: 'border-box',
        display: 'flex',
        flexDirection: 'column',
        gap: '20px',
        animation: 'fadeIn 0.3s ease-out'
      }}>
        {/* Progresso */}
        {step > 0 && step < 5 && (
          <div style={{ display: 'flex', gap: '4px', width: '100%' }}>
            {[1, 2, 3, 4].map(i => (
              <div key={i} style={{
                flex: 1,
                height: '4px',
                borderRadius: '2px',
                backgroundColor: i <= step ? 'var(--orange)' : 'var(--slate-light)',
                transition: 'background-color 0.2s'
              }} />
            ))}
          </div>
        )}

        {/* Passo 0: Boas-vindas */}
        {step === 0 && (
          <div className="flex-column gap-md text-center" style={{ animation: 'fadeIn 0.2s' }}>
            <div style={{ margin: '15px 0', display: 'flex', justifyContent: 'center' }}>
              <ChaminhaVideo size={100} />
            </div>
            <h1 style={{ fontSize: '1.6rem', fontWeight: '800', color: 'var(--text-primary)' }}>Bem-vindo ao 1Convite</h1>
            <p style={{ fontSize: '0.925rem', color: 'var(--text-secondary)', lineHeight: '1.6' }}>
              Uma jornada intencional de 365 dias para trazer conexões profundas, paz espiritual e amor no seu dia a dia.
            </p>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              Vamos responder 3 perguntas rápidas para personalizar sua jornada.
            </p>
            <button className="btn-primary" onClick={handleNext} style={{ marginTop: '10px', width: '100%' }}>
              Começar Personalização
            </button>
          </div>
        )}

        {/* Passo 1: Objetivo Principal */}
        {step === 1 && (
          <div className="flex-column gap-md" style={{ animation: 'fadeIn 0.2s' }}>
            <h2 style={{ fontSize: '1.25rem', fontWeight: '700', color: 'var(--text-primary)' }}>
              Qual o seu foco principal ao usar o app?
            </h2>
            <div className="flex-column gap-sm" style={{ marginTop: '10px' }}>
              {objetivos.map(obj => (
                <button
                  key={obj.key}
                  onClick={() => selectObjetivo(obj.key)}
                  className="chat-suggest-chip"
                  style={{
                    padding: '14px 18px',
                    textAlign: 'left',
                    borderRadius: '16px',
                    fontSize: '0.925rem',
                    border: '1px solid var(--slate-border)',
                    background: 'var(--white)',
                    color: 'var(--text-primary)',
                    width: '100%',
                    whiteSpace: 'normal',
                    cursor: 'pointer',
                    transition: 'all 0.2s'
                  }}
                  onMouseOver={(e) => {
                    e.currentTarget.style.borderColor = 'var(--orange)';
                    e.currentTarget.style.background = 'var(--orange-light)';
                  }}
                  onMouseOut={(e) => {
                    e.currentTarget.style.borderColor = 'var(--slate-border)';
                    e.currentTarget.style.background = 'var(--white)';
                  }}
                >
                  {obj.text}
                </button>
              ))}
            </div>
            <button className="btn-secondary" onClick={handleBack} style={{ alignSelf: 'flex-start', marginTop: '10px' }}>
              Voltar
            </button>
          </div>
        )}

        {/* Passo 2: Modo de Conexão */}
        {step === 2 && (
          <div className="flex-column gap-md" style={{ animation: 'fadeIn 0.2s' }}>
            <h2 style={{ fontSize: '1.25rem', fontWeight: '700', color: 'var(--text-primary)' }}>
              Como você prefere se conectar com Deus e com o próximo?
            </h2>
            <div className="flex-column gap-sm" style={{ marginTop: '10px' }}>
              {conexoes.map(con => (
                <button
                  key={con.key}
                  onClick={() => selectConexao(con.key)}
                  className="chat-suggest-chip"
                  style={{
                    padding: '14px 18px',
                    textAlign: 'left',
                    borderRadius: '16px',
                    fontSize: '0.925rem',
                    border: '1px solid var(--slate-border)',
                    background: 'var(--white)',
                    color: 'var(--text-primary)',
                    width: '100%',
                    whiteSpace: 'normal',
                    cursor: 'pointer',
                    transition: 'all 0.2s'
                  }}
                  onMouseOver={(e) => {
                    e.currentTarget.style.borderColor = 'var(--orange)';
                    e.currentTarget.style.background = 'var(--orange-light)';
                  }}
                  onMouseOut={(e) => {
                    e.currentTarget.style.borderColor = 'var(--slate-border)';
                    e.currentTarget.style.background = 'var(--white)';
                  }}
                >
                  {con.text}
                </button>
              ))}
            </div>
            <button className="btn-secondary" onClick={handleBack} style={{ alignSelf: 'flex-start', marginTop: '10px' }}>
              Voltar
            </button>
          </div>
        )}

        {/* Passo 3: Versão da Bíblia */}
        {step === 3 && (
          <div className="flex-column gap-md" style={{ animation: 'fadeIn 0.2s', textAlign: 'center' }}>
            <h2 style={{ fontSize: '1.25rem', fontWeight: '700', color: 'var(--text-primary)', marginBottom: '8px' }}>
              Qual versão da Bíblia você usa?
            </h2>
            <div className="flex-column gap-sm" style={{ marginTop: '10px', width: '100%' }}>
              {['NVI', 'ARA', 'NVT', 'ACF', 'OUTRAS'].map(v => (
                <button
                  key={v}
                  onClick={() => {
                    setRespostas(prev => ({ ...prev, versaoBiblia: v }));
                  }}
                  style={{
                    padding: '14px 18px',
                    borderRadius: '16px',
                    fontSize: '0.95rem',
                    fontWeight: 'bold',
                    border: respostas.versaoBiblia === v ? '2.5px solid var(--orange)' : '1px solid var(--slate-border)',
                    background: respostas.versaoBiblia === v ? 'var(--orange-light)' : 'var(--white)',
                    color: 'var(--text-primary)',
                    width: '100%',
                    cursor: 'pointer',
                    transition: 'all 0.2s',
                    boxSizing: 'border-box'
                  }}
                >
                  {v}
                </button>
              ))}
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '15px' }}>
              <button className="btn-secondary" onClick={handleBack}>
                Voltar
              </button>
              <button className="btn-primary" onClick={handleNext}>
                Continuar
              </button>
            </div>
          </div>
        )}

        {/* Passo 4: Horário de Lembretes */}
        {step === 4 && (
          <div className="flex-column gap-md" style={{ animation: 'fadeIn 0.2s' }}>
            <h2 style={{ fontSize: '1.25rem', fontWeight: '700', color: 'var(--text-primary)' }}>
              Que horas deseja receber seu convite/desafio diário?
            </h2>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              Recomendamos o início da manhã para inspirar todo o seu dia.
            </p>
            <div style={{ display: 'flex', justifyContent: 'center', margin: '20px 0' }}>
              <input
                type="time"
                value={respostas.horario}
                onChange={(e) => setRespostas(prev => ({ ...prev, horario: e.target.value }))}
                style={{
                  fontSize: '2rem',
                  padding: '10px 20px',
                  borderRadius: '16px',
                  border: '2px solid var(--orange)',
                  background: 'var(--white)',
                  color: 'var(--text-primary)',
                  fontFamily: 'inherit',
                  textAlign: 'center',
                  outline: 'none'
                }}
              />
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '10px' }}>
              <button className="btn-secondary" onClick={handleBack}>
                Voltar
              </button>
              <button className="btn-primary" onClick={handleNext}>
                Avançar
              </button>
            </div>
          </div>
        )}
        
        {/* Passo 5: Conclusão */}
        {step === 5 && (
          <div className="flex-column gap-md text-center" style={{ animation: 'fadeIn 0.2s' }}>
            <div style={{ margin: '15px 0', display: 'flex', justifyContent: 'center', position: 'relative' }}>
              <ChaminhaVideo size={100} />
              {/* Adicionar chapéu de festa por cima do vídeo */}
              <div style={{ position: 'absolute', top: '-10px', fontSize: '2rem', transform: 'rotate(15deg)' }}>🎉</div>
            </div>
            <h2 style={{ fontSize: '1.5rem', fontWeight: '800', color: 'var(--text-primary)' }}>Tudo Pronto!</h2>
            <p style={{ fontSize: '0.925rem', color: 'var(--text-secondary)', lineHeight: '1.6' }}>
              Seu perfil de jornada foi configurado com sucesso. Prepare-se para momentos incríveis de conexão.
            </p>
            <div className="glass-panel" style={{
              background: 'rgba(255,255,255,0.03)',
              border: '1px solid var(--slate-border)',
              padding: '12px 16px',
              borderRadius: '16px',
              textAlign: 'left',
              fontSize: '0.85rem',
              color: 'var(--text-secondary)'
            }}>
              💡 <strong>Dica:</strong> Se precisar mudar seus objetivos ou desativar lembretes, acesse o painel principal a qualquer momento.
            </div>
            <button className="btn-primary" onClick={handleFinish} style={{ marginTop: '10px', width: '100%' }}>
              Entrar no Aplicativo
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
