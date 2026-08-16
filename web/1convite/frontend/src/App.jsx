import React, { useState, useEffect, useRef } from 'react';
import Onboarding from './components/Onboarding';
import html2canvas from 'html2canvas';
import LandingPage from './components/LandingPage/LandingPage';
import { ARCADE_QUIZ_QUESTIONS, ARCADE_CHARADAS_QUESTIONS, ARCADE_FORCA_WORDS, ARCADE_CACA_PALAVRAS_LIST, generateCacaPalavrasGrid } from './data/arcadeData';
import TrailHome from './components/trail/TrailHome';




// ═══ COMPONENTE REWARD POPUP (CHAMINHA) ═══
function RewardPopup({ amount, title, message, onClose }) {
  return (
    <div style={{
      position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
      backgroundColor: 'rgba(0,0,0,0.75)', backdropFilter: 'blur(5px)',
      zIndex: 10000, display: 'flex', alignItems: 'center', justifyContent: 'center',
      padding: '20px', animation: 'fadeIn 0.2s ease-out'
    }}>
      <div className="glass-panel text-center" style={{
        maxWidth: '320px', width: '100%', padding: '32px 24px', borderRadius: '24px',
        border: '1px solid var(--slate-border)', display: 'flex', flexDirection: 'column',
        alignItems: 'center', gap: '16px', backgroundColor: 'var(--bg-app)',
        boxShadow: '0 20px 40px rgba(0,0,0,0.4)', animation: 'scaleUp 0.3s cubic-bezier(0.34, 1.56, 0.64, 1)'
      }}>
        {/* Estilo local para animações */}
        <style>{`
          @keyframes bounceChaminha {
            0% { transform: translateY(0); }
            100% { transform: translateY(-12px); }
          }
          @keyframes scaleUp {
            0% { transform: scale(0.9); opacity: 0; }
            100% { transform: scale(1); opacity: 1; }
          }
        `}</style>

        {/* Chaminha Animado */}
        <div style={{ animation: 'bounceChaminha 0.8s infinite alternate ease-in-out' }}>
          <ChaminhaVideo size={100} />
        </div>

        <h3 style={{ fontSize: '1.4rem', fontWeight: '800', margin: 0, color: 'var(--text-primary)' }}>{title}</h3>
        <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', margin: 0, lineHeight: '1.5' }}>{message}</p>
        
        <div style={{
          display: 'flex', alignItems: 'center', gap: '8px', background: 'rgba(245,158,11,0.1)',
          padding: '8px 18px', borderRadius: '30px', border: '1px solid var(--orange)', margin: '4px 0'
        }}>
          <span style={{ fontSize: '1.05rem', fontWeight: 'bold', color: 'var(--orange)' }}>+{amount}</span>
          <ChaminhaCoin size={22} />
        </div>

        <button className="btn-primary" style={{ width: '100%', marginTop: '8px' }} onClick={onClose}>
          Glória a Deus!
        </button>
      </div>
    </div>
  );
}

// ═══ COMPONENTE CHAMINHA COIN ═══

// ═══ COMPONENTE CHAMINHA VIDEO (MASCOTE 3D) ═══
function ChaminhaVideo({ size = 100, style = {} }) {
  const videoRef = React.useRef(null);
  const canvasRef = React.useRef(null);

  React.useEffect(() => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas) return;

    const ctx = canvas.getContext('2d');
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

          // Detecção de tela verde (Chroma Key)
          if (g > 90 && g > r * 1.15 && g > b * 1.15) {
            data[i + 3] = 0; // Torna o pixel transparente
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
      overflow: 'visible',
      ...style
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

function ChaminhaCoin({ size = 22, style = {} }) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120"
      width={size} height={size} style={{ display: 'inline-block', verticalAlign: 'middle', ...style }}>
      <defs>
        <radialGradient id="cgCoin" cx="40%" cy="35%" r="60%">
          <stop offset="0%" stopColor="#FFE566"/>
          <stop offset="40%" stopColor="#F5C842"/>
          <stop offset="100%" stopColor="#C8860A"/>
        </radialGradient>
        <linearGradient id="cgRim" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#FFD700"/>
          <stop offset="50%" stopColor="#B8860B"/>
          <stop offset="100%" stopColor="#FFD700"/>
        </linearGradient>
        <radialGradient id="cgFlame" cx="50%" cy="65%" r="55%">
          <stop offset="0%" stopColor="#FFF0A0"/>
          <stop offset="40%" stopColor="#FFB300"/>
          <stop offset="100%" stopColor="#E85500"/>
        </radialGradient>
        <linearGradient id="cgTip" x1="50%" y1="0%" x2="50%" y2="100%">
          <stop offset="0%" stopColor="#FF6000"/>
          <stop offset="100%" stopColor="#FFB300"/>
        </linearGradient>
      </defs>
      <ellipse cx="60" cy="114" rx="28" ry="5" fill="rgba(0,0,0,0.18)"/>
      <circle cx="60" cy="62" r="48" fill="url(#cgRim)"/>
      <circle cx="60" cy="62" r="42" fill="url(#cgCoin)"/>
      <ellipse cx="48" cy="45" rx="14" ry="8" fill="rgba(255,255,255,0.25)" transform="rotate(-20,48,45)"/>
      <circle cx="60" cy="62" r="46" fill="none" stroke="#C8860A" strokeWidth="1" strokeDasharray="3,3.7" opacity="0.5"/>
      <path d="M60 24 C56 30 50 33 50 40 C50 47 55 50 60 52 C65 50 70 47 70 40 C70 33 64 30 60 24Z" fill="url(#cgTip)"/>
      <path d="M54 35 C51 39 50 44 52 47 C54 44 55 41 57 39Z" fill="#FF8C00" opacity="0.7"/>
      <path d="M66 35 C69 39 70 44 68 47 C66 44 65 41 63 39Z" fill="#FF8C00" opacity="0.7"/>
      <ellipse cx="60" cy="72" rx="14" ry="18" fill="url(#cgFlame)"/>
      <ellipse cx="55" cy="65" rx="4" ry="5" fill="rgba(255,255,200,0.35)" transform="rotate(-10,55,65)"/>
      <ellipse cx="55.5" cy="70" rx="3.5" ry="3.8" fill="#3D1A00"/>
      <ellipse cx="64.5" cy="70" rx="3.5" ry="3.8" fill="#3D1A00"/>
      <circle cx="54.2" cy="68.5" r="1.2" fill="white" opacity="0.9"/>
      <circle cx="63.2" cy="68.5" r="1.2" fill="white" opacity="0.9"/>
      <ellipse cx="51" cy="73.5" rx="3" ry="1.8" fill="#FF7B00" opacity="0.45"/>
      <ellipse cx="69" cy="73.5" rx="3" ry="1.8" fill="#FF7B00" opacity="0.45"/>
      <path d="M56 75.5 Q60 79 64 75.5" fill="none" stroke="#3D1A00" strokeWidth="1.4" strokeLinecap="round"/>
      <ellipse cx="54" cy="88.5" rx="5" ry="3" fill="#E8720A"/>
      <ellipse cx="66" cy="88.5" rx="5" ry="3" fill="#E8720A"/>
      <text x="60" y="106" textAnchor="middle" fontFamily="'Arial Black', Arial, sans-serif"
        fontSize="8" fontWeight="900" letterSpacing="1.5" fill="#7A4500">CHAMINHA</text>
    </svg>
  );
}

const LOJINHA_ITEMS = [
  { id: 'font-premium-1', type: 'font', name: 'Fonte Cursiva Elegante', price: 200, icon: '🔤', desc: 'Desbloqueia uma linda fonte manuscrita no Studio de Cards.' },
  { id: 'font-premium-2', type: 'font', name: 'Fonte Papiro Antigo', price: 300, icon: '📜', desc: 'Desbloqueia uma fonte estilo épico medieval.' },
  { id: 'bg-premium-1', type: 'bg', name: 'Fundo Ouro Velho', price: 250, icon: '✨', desc: 'Textura premium dourada para fundos de cartões.' },
  { id: 'bg-premium-2', type: 'bg', name: 'Fundo Jardim do Éden', price: 350, icon: '🌿', desc: 'Background com folhas vibrantes e luz celestial.' },
  { id: 'sticker-1', type: 'sticker', name: 'Sticker: Pomba da Paz', price: 100, icon: '🕊️', desc: 'Adicione este selo aos seus convites.' },
  { id: 'sticker-2', type: 'sticker', name: 'Sticker: Cruz Minimalista', price: 100, icon: '✝️', desc: 'Um toque clássico e elegante de fé.' }
];

const COUNSELORS = [
  { id: 'jesus', name: 'Mestre Jesus', title: 'Amor & Esperança', isPremium: false, price: 0, systemPrompt: 'Você é Jesus Cristo. Responda com amor, perdão e parábolas.' },
  { id: 'paulo', name: 'Apóstolo Paulo', title: 'Graça & Fé', isPremium: true, price: 300, systemPrompt: 'Você é o Apóstolo Paulo. Responda com teologia, graça e perseverança.' },
  { id: 'pedro', name: 'Apóstolo Pedro', title: 'Liderança & Coragem', isPremium: true, price: 200, systemPrompt: 'Você é o Apóstolo Pedro. Responda com impetuosidade, arrependimento e esperança.' },
  { id: 'davi', name: 'Rei Davi', title: 'Adoração & Conforto', isPremium: true, price: 250, systemPrompt: 'Você é o Rei Davi. Responda com foco em adoração, salmos e conforto na angústia.' },
  { id: 'salomao', name: 'Rei Salomão', title: 'Sabedoria Prática', isPremium: true, price: 400, systemPrompt: 'Você é o Rei Salomão. Responda com sabedoria prática e provérbios.' },
  { id: 'ester', name: 'Rainha Ester', title: 'Propósito & Coragem', isPremium: true, price: 300, systemPrompt: 'Você é a Rainha Ester. Responda com foco em coragem e propósito divino.' }
];

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [userCoins, setUserCoins] = useState(() => parseInt(localStorage.getItem('app-coins') || localStorage.getItem('arcade-coins')) || 0);
  const [unlockedItems, setUnlockedItems] = useState(() => JSON.parse(localStorage.getItem('unlocked-items') || '[]'));
  
  // --- RESTORED ARCADE STATES ---
  const [arcadeActiveGame, setArcadeActiveGame] = useState('lobby');

  const [arcadeSelectedGame, setArcadeSelectedGame] = useState(null);
  const [arcadeDifficulty, setArcadeDifficulty] = useState('facil');
  const [arcadeQuizList, setArcadeQuizList] = useState([]);
  const [arcadeQuizCurrentQuestion, setArcadeQuizCurrentQuestion] = useState(0);
  const [arcadeQuizFeedback, setArcadeQuizFeedback] = useState(null);
  const [arcadeQuizTimer, setArcadeQuizTimer] = useState(15);
  const [arcadeQuizGameOver, setArcadeQuizGameOver] = useState(false);
  const [arcadeQuizScore, setArcadeQuizScore] = useState(0);
  const [arcadeCharadasList, setArcadeCharadasList] = useState([]);
  const [arcadeCharadasCurrent, setArcadeCharadasCurrent] = useState(0);
  const [arcadeCharadasFeedback, setArcadeCharadasFeedback] = useState(null);
  const [arcadeCharadasTimer, setArcadeCharadasTimer] = useState(20);
  const [arcadeCharadasGameOver, setArcadeCharadasGameOver] = useState(false);
  const [arcadeCharadasScore, setArcadeCharadasScore] = useState(0);
  const [arcadeForcaList, setArcadeForcaList] = useState([]);
  const [arcadeForcaCurrent, setArcadeForcaCurrent] = useState(0);
  const [arcadeForcaGuesses, setArcadeForcaGuesses] = useState([]);
  const [arcadeForcaFeedback, setArcadeForcaFeedback] = useState(null);
  const [arcadeForcaMistakes, setArcadeForcaMistakes] = useState(0);
  const [arcadeForcaGameOver, setArcadeForcaGameOver] = useState(false);
  const [arcadeForcaScore, setArcadeForcaScore] = useState(0);
  const [arcadeCacaWords, setArcadeCacaWords] = useState([]);
  const [arcadeCacaGrade, setArcadeCacaGrade] = useState([]);
  const [arcadeCacaFound, setArcadeCacaFound] = useState([]);
  const [arcadeCacaSelected, setArcadeCacaSelected] = useState([]);
  const [arcadeCacaScore, setArcadeCacaScore] = useState(0);
  const [arcadeCacaGameOver, setArcadeCacaGameOver] = useState(false);
  // --- END RESTORED ARCADE STATES ---

  const [user, setUser] = useState(null);
  const [codigoDia, setCodigoDia] = useState(null);
  const [contatos, setContatos] = useState([]);
  const [historico, setHistorico] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');

  // Studio de Compartilhamento
  // Studio de Compartilhamento
  const [cardCategory, setCardCategory] = useState('bomdia');
  const [cardSelectedText, setCardSelectedText] = useState('');
  const [cardBg, setCardBg] = useState(0);
  const [cardBgCategory, setCardBgCategory] = useState('paisagem');
  const [cardFormat, setCardFormat] = useState('square');
  const [cardFont, setCardFont] = useState('Georgia, serif');
  const [cardFontSize, setCardFontSize] = useState('md');
  const [cardTextColor, setCardTextColor] = useState('#ffffff');
  const [cardTextStyle, setCardTextStyle] = useState('italic');
  const [cardOverlay, setCardOverlay] = useState(0.65);
  const [cardGenerating, setCardGenerating] = useState(false);
  const cardPreviewRef = useRef(null);

  // Carregar fontes do Google dinamicamente
  useEffect(() => {
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = 'https://fonts.googleapis.com/css2?family=Playfair+Display:ital@0;1&family=Cormorant+Garamond:ital@0;1&family=Lora:ital@0;1&family=Merriweather:ital@0;1&family=Cinzel&family=Dancing+Script&family=Satisfy&family=Great+Vibes&family=Pacifico&family=Raleway:wght@400;700&family=Montserrat:wght@400;700&family=Josefin+Sans:wght@400;700&family=Quicksand:wght@400;700&family=Nunito:wght@400;700&family=Oswald:wght@400;700&family=Lobster&family=EB+Garamond:ital@0;1&family=Libre+Baskerville:ital@0;1&family=Crimson+Text:ital@0;1&display=swap';
    if (!document.querySelector('link[href*="googleapis.com/css2?family=Playfair"]')) {
      document.head.appendChild(link);
    }
  }, []);

  const CARD_FONTS = [
    { label: 'Georgia', value: 'Georgia, serif' },
    { label: 'Playfair Display', value: 'Playfair Display, serif' },
    { label: 'Cormorant', value: 'Cormorant Garamond, serif' },
    { label: 'EB Garamond', value: 'EB Garamond, serif' },
    { label: 'Libre Baskerville', value: 'Libre Baskerville, serif' },
    { label: 'Crimson Text', value: 'Crimson Text, serif' },
    { label: 'Lora', value: 'Lora, serif' },
    { label: 'Merriweather', value: 'Merriweather, serif' },
    { label: 'Cinzel', value: 'Cinzel, serif' },
    { label: 'Dancing Script', value: 'Dancing Script, cursive' },
    { label: 'Satisfy', value: 'Satisfy, cursive' },
    { label: 'Great Vibes', value: 'Great Vibes, cursive' },
    { label: 'Lobster', value: 'Lobster, cursive' },
    { label: 'Pacifico', value: 'Pacifico, cursive' },
    { label: 'Raleway', value: 'Raleway, sans-serif' },
    { label: 'Montserrat', value: 'Montserrat, sans-serif' },
    { label: 'Josefin Sans', value: 'Josefin Sans, sans-serif' },
    { label: 'Quicksand', value: 'Quicksand, sans-serif' },
    { label: 'Nunito', value: 'Nunito, sans-serif' },
    { label: 'Oswald', value: 'Oswald, sans-serif' },
  ];

  const CARD_TEXT_COLORS = [
    { label: 'Branco', value: '#ffffff' },
    { label: 'Creme', value: '#fef9e7' },
    { label: 'Dourado', value: '#FFD700' },
    { label: 'Ouro Rosa', value: '#F4C2C2' },
    { label: 'Azul Claro', value: '#B3D9FF' },
    { label: 'Mint', value: '#B3FFD9' },
    { label: 'Lavanda', value: '#E0B3FF' },
    { label: 'Laranja', value: '#FFB347' },
  ];

  const CARD_FONT_SIZES = [
    { label: 'P', value: 'sm', size: '0.88rem' },
    { label: 'M', value: 'md', size: '1.1rem' },
    { label: 'G', value: 'lg', size: '1.35rem' },
    { label: 'GG', value: 'xl', size: '1.65rem' },
  ];

  const CARD_BG_CATEGORIES = [
    {
      id: 'paisagem', label: 'Paisagem',
      items: [
        { url: 'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800&q=80', label: 'Montanha' },
        { url: 'https://images.unsplash.com/photo-1501854140801-50d01698950b?w=800&q=80', label: 'Vale Verde' },
        { url: 'https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=800&q=80', label: 'Cume' },
        { url: 'https://images.unsplash.com/photo-1470770903676-69b98201ea1c?w=800&q=80', label: 'Lago' },
        { url: 'https://images.unsplash.com/photo-1476673160081-cf065607f449?w=800&q=80', label: 'Trigo' },
        { url: 'https://images.unsplash.com/photo-1490750967868-88df5691cc5e?w=800&q=80', label: 'Flores' },
        { url: 'https://images.unsplash.com/photo-1530281700549-e82e7bf110d6?w=800&q=80', label: 'Floresta' },
        { url: 'https://images.unsplash.com/photo-1519451241324-20b4ea2c4220?w=800&q=80', label: 'Oceano' },
        { url: 'https://images.unsplash.com/photo-1418065460487-3e41a6c84dc5?w=800&q=80', label: 'Luz na Mata' },
        { url: 'https://images.unsplash.com/photo-1500534314209-a25ddb2bd429?w=800&q=80', label: 'Colinas' },
        { url: 'https://images.unsplash.com/photo-1504701954957-2010ec3bcec1?w=800&q=80', label: 'Praia' },
        { url: 'https://images.unsplash.com/photo-1559827260-dc66d52bef19?w=800&q=80', label: 'Cachoeira' },
      ]
    },
    {
      id: 'universo', label: 'Universo',
      items: [
        { url: 'https://images.unsplash.com/photo-1462331940025-496dfbfc7564?w=800&q=80', label: 'Galáxia' },
        { url: 'https://images.unsplash.com/photo-1446776811953-b23d57bd21aa?w=800&q=80', label: 'Nebulosa' },
        { url: 'https://images.unsplash.com/photo-1614730321146-b6fa6a46bcb4?w=800&q=80', label: 'Lua' },
        { url: 'https://images.unsplash.com/photo-1419242902214-272b3f66ee7a?w=800&q=80', label: 'Estrelas' },
        { url: 'https://images.unsplash.com/photo-1534796636912-3b95b3ab5986?w=800&q=80', label: 'Via Láctea' },
        { url: 'https://images.unsplash.com/photo-1516339901601-2e1b62dc0c45?w=800&q=80', label: 'Cosmos' },
        { url: 'https://images.unsplash.com/photo-1537420327992-d6e192287183?w=800&q=80', label: 'Aurora Boreal' },
        { url: 'https://images.unsplash.com/photo-1605106702734-205df224ecce?w=800&q=80', label: 'Espaço Azul' },
      ]
    },
    {
      id: 'solar', label: 'Sol',
      items: [
        { url: 'https://images.unsplash.com/photo-1516912481808-3406841bd33c?w=800&q=80', label: 'Nascer' },
        { url: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=800&q=80', label: 'Aurora' },
        { url: 'https://images.unsplash.com/photo-1472120435266-53107fd0c44a?w=800&q=80', label: 'Pôr do Sol' },
        { url: 'https://images.unsplash.com/photo-1495616811223-4d98c6e9c869?w=800&q=80', label: 'Horizonte' },
        { url: 'https://images.unsplash.com/photo-1426604966848-d7adac402bff?w=800&q=80', label: 'Dourado' },
        { url: 'https://images.unsplash.com/photo-1502082553048-f009c37129b9?w=800&q=80', label: 'Raios de Sol' },
        { url: 'https://images.unsplash.com/photo-1498429152472-9a433d9ddf3b?w=800&q=80', label: 'Crepúsculo' },
        { url: 'https://images.unsplash.com/photo-1504805572947-34fad45aed93?w=800&q=80', label: 'Manhã' },
      ]
    },
    {
      id: 'cachorro', label: 'Cachorro',
      items: [
        { url: 'https://images.unsplash.com/photo-1587300003388-59208cc962cb?w=800&q=80', label: 'Golden' },
        { url: 'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=800&q=80', label: 'Fofo' },
        { url: 'https://images.unsplash.com/photo-1537151608828-ea2b11777ee8?w=800&q=80', label: 'Filhote' },
        { url: 'https://images.unsplash.com/photo-1548199973-03cce0bbc87b?w=800&q=80', label: 'Correndo' },
        { url: 'https://images.unsplash.com/photo-1593134257782-e89567b7718a?w=800&q=80', label: 'Labrador' },
        { url: 'https://images.unsplash.com/photo-1560743641-3914f2c45636?w=800&q=80', label: 'Sorrindo' },
      ]
    },
    {
      id: 'gato', label: 'Gato',
      items: [
        { url: 'https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=800&q=80', label: 'Olhos' },
        { url: 'https://images.unsplash.com/photo-1533743983669-94fa5c4338ec?w=800&q=80', label: 'Fofo' },
        { url: 'https://images.unsplash.com/photo-1495360010541-f48722b34f7d?w=800&q=80', label: 'Sentado' },
        { url: 'https://images.unsplash.com/photo-1543466835-00a7907e9de1?w=800&q=80', label: 'Curioso' },
        { url: 'https://images.unsplash.com/photo-1518791841217-8f162f1912da?w=800&q=80', label: 'Listrado' },
        { url: 'https://images.unsplash.com/photo-1573865526739-10659fec78a5?w=800&q=80', label: 'Filhote' },
      ]
    },
    {
      id: 'passaro', label: 'Pássaro',
      items: [
        { url: 'https://images.unsplash.com/photo-1444464666168-49d633b86797?w=800&q=80', label: 'Bando' },
        { url: 'https://images.unsplash.com/photo-1552728089-57bdde30beb3?w=800&q=80', label: 'Colorido' },
        { url: 'https://images.unsplash.com/photo-1548550023-2bdb3c5beed7?w=800&q=80', label: 'No Galho' },
        { url: 'https://images.unsplash.com/photo-1551085254-e96b210db58a?w=800&q=80', label: 'Águia' },
        { url: 'https://images.unsplash.com/photo-1547394765-185e1e68f34e?w=800&q=80', label: 'Papagaio' },
        { url: 'https://images.unsplash.com/photo-1522926193341-e9ffd686c60f?w=800&q=80', label: 'Beija-flor' },
      ]
    },
  ];

  const CARD_PHRASES = {
    bomdia: [
      { text: 'Que este novo dia seja cheio da paz que só Deus pode dar.', ref: 'Salmos 118:24' },
      { text: 'Cada manhã são renovadas as Suas misericórdias. Grande é a Tua fidelidade.', ref: 'Lamentações 3:23' },
      { text: 'Desperta, ó minha alma! O Senhor abriu mais um dia para que você floresça.', ref: null },
      { text: 'Bom dia! Que hoje você experimente o amor de Deus em cada detalhe.', ref: null },
      { text: 'Antes que o mundo te fale, deixe Deus falar primeiro. Bom dia!', ref: null },
    ],
    boatarde: [
      { text: 'No meio do dia, lembre-se: Deus cuida de você com cuidado e ternura.', ref: 'Mateus 6:26' },
      { text: 'Boa tarde! Que o seu descanso de hoje seja tão produtivo quanto o seu trabalho.', ref: null },
      { text: 'A metade do dia passou. Que a segunda parte seja guiada por Ele.', ref: null },
      { text: 'Seja forte e corajoso! O Senhor, seu Deus, está com você por onde quer que você vá.', ref: 'Josué 1:9' },
      { text: 'Boa tarde! Um sorriso pode ser o seu maior testemunho hoje.', ref: null },
    ],
    boanoite: [
      { text: 'Que o Senhor te guarde em teu repouso e que Seus anjos velem sobre você.', ref: 'Salmos 91:11' },
      { text: 'Em paz deitarei e logo dormirei, pois só Tu, Senhor, me fazes habitar em segurança.', ref: 'Salmos 4:8' },
      { text: 'Boa noite! Entregue ao Senhor o que ficou por fazer. Ele é fiel.', ref: null },
      { text: 'Descanse. Amanhã é uma nova chance de recomeçar com Deus.', ref: null },
      { text: 'Feche os olhos em paz. O mesmo Deus que cuidou hoje, cuidará amanhã.', ref: null },
    ],
    versiculo: [
      { text: 'Ninguém tem maior amor do que este: de dar alguém a própria vida pelos seus amigos.', ref: 'João 15:13' },
      { text: 'Não andeis ansiosos por coisa alguma, mas em tudo pela oração fazei os vossos pedidos.', ref: 'Filipenses 4:6' },
      { text: 'Tudo posso naquele que me fortalece.', ref: 'Filipenses 4:13' },
      { text: 'Porque Deus amou o mundo de tal maneira que deu o seu Filho unigênito.', ref: 'João 3:16' },
      { text: 'O Senhor é o meu pastor e nada me faltará.', ref: 'Salmos 23:1' },
      { text: 'Eu sou o caminho, a verdade e a vida; ninguém vem ao Pai senão por mim.', ref: 'João 14:6' },
    ],
    convite: [
      { text: 'Você tem um convite para fazer parte de algo maior. 1 convite pode mudar uma vida.', ref: 'Mateus 24:14' },
      { text: 'Compartilhe a boa notícia! O Evangelho foi feito para ser levado a todos.', ref: 'Marcos 16:15' },
      { text: 'Quem salva uma alma, salva o mundo. Faça o seu 1Convite hoje.', ref: null },
      { text: 'Seja o instrumento de Deus nas mãos de alguém que precisa de esperança.', ref: null },
      { text: 'Uma boa palavra no momento certo pode mudar uma eternidade.', ref: 'Provérbios 15:23' },
    ],
  };

  const triggerDownload = (blob) => {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `1convite-card-${Date.now()}.png`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleGenerateCard = async (mode) => {
    if (!cardPreviewRef.current) return;
    setCardGenerating(true);
    try {
      const width = 1080;
      const height = cardFormat === 'square' ? 1080 : 1920;

      // Container offscreen em resolução nativa 1080p sem borderRadius (elimina bordas brancas)
      const offscreenDiv = document.createElement('div');
      offscreenDiv.style.position = 'fixed';
      offscreenDiv.style.left = '-9999px';
      offscreenDiv.style.top = '0';
      offscreenDiv.style.width = `${width}px`;
      offscreenDiv.style.height = `${height}px`;
      offscreenDiv.style.borderRadius = '0px';
      offscreenDiv.style.overflow = 'hidden';
      offscreenDiv.style.boxSizing = 'border-box';
      offscreenDiv.style.margin = '0';
      offscreenDiv.style.padding = '0';

      const clone = cardPreviewRef.current.cloneNode(true);
      clone.style.width = `${width}px`;
      clone.style.height = `${height}px`;
      clone.style.paddingTop = '0';
      clone.style.borderRadius = '0px';
      clone.style.boxShadow = 'none';

      // Font size escalado para 1080px
      const baseFontSizeMap = { sm: 38, md: 52, lg: 66, xl: 82 };
      const targetFontSize = baseFontSizeMap[cardFontSize] || 52;

      const textP = clone.querySelector('p');
      if (textP) {
        textP.style.fontSize = `${targetFontSize}px`;
        textP.style.lineHeight = '1.6';
      }

      const refSpan = clone.querySelector('span');
      if (refSpan) {
        refSpan.style.fontSize = `${Math.round(targetFontSize * 0.42)}px`;
        refSpan.style.marginTop = '24px';
      }

      const textContainer = clone.children[1];
      if (textContainer) {
        textContainer.style.padding = '60px 50px';
      }

      const footerDiv = textContainer ? textContainer.children[textContainer.children.length - 1] : null;
      if (footerDiv) {
        footerDiv.style.marginTop = '32px';
        const footerSvg = footerDiv.querySelector('svg');
        if (footerSvg) {
          footerSvg.setAttribute('width', '24');
          footerSvg.setAttribute('height', '24');
        }
        const footerSpan = footerDiv.querySelector('span');
        if (footerSpan) {
          footerSpan.style.fontSize = '20px';
        }
      }

      offscreenDiv.appendChild(clone);
      document.body.appendChild(offscreenDiv);

      const canvas = await html2canvas(offscreenDiv, {
        useCORS: true,
        allowTaint: true,
        scale: 1,
        width: width,
        height: height,
        windowWidth: width,
        windowHeight: height,
        backgroundColor: '#000000',
        logging: false
      });

      document.body.removeChild(offscreenDiv);

      canvas.toBlob(async (blob) => {
        if (!blob) {
          setCardGenerating(false);
          return;
        }
        const file = new File([blob], '1convite-card.png', { type: 'image/png' });

        if (mode === 'share' && navigator.canShare && navigator.canShare({ files: [file] })) {
          try {
            await navigator.share({
              title: '1Convite Card',
              text: 'Confira este cartão do 1Convite!',
              files: [file]
            });
          } catch (shareErr) {
            triggerDownload(blob);
          }
        } else {
          triggerDownload(blob);
        }
        setCardGenerating(false);
      }, 'image/png');
    } catch (e) {
      console.error('Erro ao gerar card:', e);
      setCardGenerating(false);
    }
  };


  // Customização de Temas & Cores
  const [rewardPopup, setRewardPopup] = useState(null);
  const [theme, setTheme] = useState(() => localStorage.getItem('app-theme') || 'theme-green');
  const [fontSizeScale, setFontSizeScale] = useState(() => parseInt(localStorage.getItem('app-font-size') || '16'));
  const [enableCustomFontSize, setEnableCustomFontSize] = useState(() => localStorage.getItem('app-enable-font-size') === 'true');
  const [voiceGender, setVoiceGender] = useState(() => localStorage.getItem('app-voice-gender') || 'feminino');
  const [voiceSpeed, setVoiceSpeed] = useState(() => parseFloat(localStorage.getItem('app-voice-speed') || '1.0'));
  const [currentPath, setCurrentPath] = useState(() => window.location.pathname);

  // CONFIGURAÇÃO DO WHATSAPP COMERCIAL (FUNIL DE VENDAS)
  const COMMERCIAL_WHATSAPP_NUMBER = '5511999999999'; // Modifique aqui com o seu número de WhatsApp comercial

  // Checkout real via Asaas (PIX/cartão) — cria a cobrança e abre a fatura.
  const iniciarCheckoutPremium = async (valorCents, descricao, plano) => {
    try {
      setIsPaying(true);
      const res = await fetch(`${API_BASE}/pagamentos/criar-preferencia`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          nome: profileName,
          email: profileEmail,
          valor_cents: valorCents,
          descricao: descricao,
          referencia: `1convite_${plano.toLowerCase().replace(/\s+/g, '-')}`,
        }),
      });
      const d = await res.json();
      if (res.ok && d.success) {
        if (d.checkoutUrl && String(d.checkoutUrl).startsWith('http')) {
          window.open(d.checkoutUrl, '_blank');
          alert(`Cobrança ${plano} gerada! Complete o pagamento na janela aberta (PIX ou cartão). Após a confirmação, seu Premium é liberado na hora.`);
        } else {
          setPaymentPreferenceId(d.preferenceId);
          setActiveTab('simular-pagamento');
        }
      } else {
        alert('Não foi possível gerar a cobrança. Tente novamente ou fale conosco pelo WhatsApp.');
      }
    } catch (e) {
      console.error(e);
      alert('Falha ao conectar. Verifique sua internet e tente de novo.');
    } finally {
      setIsPaying(false);
    }
  };

  const iniciarCheckoutWhatsApp = () => {
    const text = `Olá! Quero assinar o Plano Premium do 1Convite para o e-mail: ${profileEmail}`;
    const url = `https://wa.me/${COMMERCIAL_WHATSAPP_NUMBER}?text=${encodeURIComponent(text)}`;
    window.open(url, '_blank');
  };

  const getBestVoiceForGender = (gender) => {
    if (typeof window === 'undefined' || !('speechSynthesis' in window)) return null;
    const voices = window.speechSynthesis.getVoices();
    const ptVoices = voices.filter(v => v.lang.startsWith('pt'));
    if (ptVoices.length === 0) return null;

    const maleKeywords = ['daniel', 'antonio', 'felipe', 'antónio', 'ricardo', 'helio', 'thiago', 'antônio'];
    const femaleKeywords = ['maria', 'francisca', 'luciana', 'joana', 'helena', 'zira', 'google', 'lecia', 'solene'];

    if (gender === 'masculino') {
      const maleVoice = ptVoices.find(v => maleKeywords.some(keyword => v.name.toLowerCase().includes(keyword)));
      if (maleVoice) return maleVoice;
    } else {
      const femaleVoice = ptVoices.find(v => femaleKeywords.some(keyword => v.name.toLowerCase().includes(keyword)));
      if (femaleVoice) return femaleVoice;
    }

    return ptVoices.find(v => v.name.includes('Natural')) || ptVoices.find(v => v.name.includes('Google')) || ptVoices[0];
  };
  const [showOnboarding, setShowOnboarding] = useState(() => !localStorage.getItem('onboarding-completed'));

  useEffect(() => {
    document.body.classList.remove('theme-orange', 'theme-blue', 'theme-green', 'theme-purple', 'theme-sepia');
    document.body.classList.add(theme);
    localStorage.setItem('app-theme', theme);
  }, [theme]);

  useEffect(() => {
    if (enableCustomFontSize) {
      document.documentElement.style.fontSize = `${fontSizeScale}px`;
    } else {
      document.documentElement.style.fontSize = '16px';
    }
  }, [enableCustomFontSize, fontSizeScale]);

  // Login com ChatGPT
  const [chatFontSize, setChatFontSize] = useState('md');
  const [chatGptUser, setChatGptUser] = useState(null);
  const [activeCounselor, setActiveCounselor] = useState(null);
  const [unlockedCounselors, setUnlockedCounselors] = useState(() => JSON.parse(localStorage.getItem('unlocked-counselors') || '["jesus"]'));
  const [lwcState, setLwcState] = useState('unauthenticated');
  const [lwcDeviceCode, setLwcDeviceCode] = useState(null);
  const [lwcPollingActive, setLwcPollingActive] = useState(false);

  // Chat IA
  const [chatMessages, setChatMessages] = useState([
    { role: 'assistant', content: 'Olá! Sou o Conselheiro Inteligente do 1Convite. Como posso te apoiar hoje em suas reflexões, relacionamentos ou espiritualidade?' }
  ]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const [countdown, setCountdown] = useState(12);
  const [isCountdownActive, setIsCountdownActive] = useState(false);
  const [pedagioErro, setPedagioErro] = useState('');
  const [pedagioIniciado, setPedagioIniciado] = useState(false);

  const [showAddContato, setShowAddContato] = useState(false);
  const [newNome, setNewNome] = useState('');
  const [newRelacao, setNewRelacao] = useState('');
  const [newPrioritario, setNewPrioritario] = useState(false);
  const [contatoErro, setContatoErro] = useState('');

  const [audioPlaying, setAudioPlaying] = useState(false);
  const [audioDuration, setAudioDuration] = useState(0);
  const [audioCurrentTime, setAudioCurrentTime] = useState(0);
  const audioRef = useRef(null);

  const [breathState, setBreathState] = useState('Toque para iniciar');
  const [breathTimer, setBreathTimer] = useState(0);
  const [isBreathing, setIsBreathing] = useState(false);
  const [breathClass, setBreathClass] = useState('');
  const [breathTechnique, setBreathTechnique] = useState('simple');
  const [breathRounds, setBreathRounds] = useState(5);
  const [currentRound, setCurrentRound] = useState(1);
  const breathIntervalRef = useRef(null);
  const isBreathingActiveRef = useRef(false);

  const [paymentPreferenceId, setPaymentPreferenceId] = useState('');
  const [isPaying, setIsPaying] = useState(false);

  const [carouselIndex, setCarouselIndex] = useState(0);
  const carouselImages = ['/Imagens/1.png', '/Imagens/2.png', '/Imagens/3.png'];

  // Bíblia
  const [bibleViewMode, setBibleViewMode] = useState('reading');
  const [bibleBooks, setBibleBooks] = useState([]);
  const [bibleSelectedBook, setBibleSelectedBook] = useState({ livro_abrev: 'gn', livro_nome: 'Gênesis' });
  const [bibleChaptersCount, setBibleChaptersCount] = useState(50);
  const [bibleSelectedChapter, setBibleSelectedChapter] = useState(1);
  const [bibleVerses, setBibleVerses] = useState([]);
  const [bibleSelectedVerse, setBibleSelectedVerse] = useState(null);
  const [bibleSearchQuery, setBibleSearchQuery] = useState('');
  const [bibleResults, setBibleResults] = useState([]);
  const [bibleLoading, setBibleLoading] = useState(false);
  const [bibleError, setBibleError] = useState('');

  // Dicionário Teológico
  const [dicionario, setDicionario] = useState({});
  const [selectedDicionarioTermo, setSelectedDicionarioTermo] = useState(null);

  // Áudio da Bíblia
  const [bibleAudioUrl, setBibleAudioUrl] = useState('');
  const [bibleAudioPlaying, setBibleAudioPlaying] = useState(false);
  const [bibleAudioDuration, setBibleAudioDuration] = useState(0);
  const [bibleAudioCurrentTime, setBibleAudioCurrentTime] = useState(0);
  const bibleAudioRef = useRef(null);

  // Destaques, Comentários e Progresso da Bíblia
  const [bibleHighlights, setBibleHighlights] = useState(() => JSON.parse(localStorage.getItem('bible-highlights')) || {});
  const [bibleComments, setBibleComments] = useState(() => JSON.parse(localStorage.getItem('bible-comments')) || {});
  const [bibleProgress, setBibleProgress] = useState(() => JSON.parse(localStorage.getItem('bible-progress')) || {});

  // Calcula progresso de um livro: { percent, readChapters, totalChapters }
  const calcBookProgress = (bookAbrev, totalChapters) => {
    const read = bibleProgress[bookAbrev];
    if (!read || !totalChapters) return { percent: 0, readCount: 0, totalChapters };
    const readCount = Object.keys(read).filter(k => read[k]).length;
    return { percent: Math.round((readCount / totalChapters) * 100), readCount, totalChapters };
  };

  // Marca um capítulo como lido/não lido
  const markChapterAsRead = (bookAbrev, chapter, value = true) => {
    setBibleProgress(prev => {
      const updated = {
        ...prev,
        [bookAbrev]: { ...(prev[bookAbrev] || {}), [chapter]: value }
      };
      localStorage.setItem('bible-progress', JSON.stringify(updated));
      return updated;
    });
  };

  // Verifica se um capítulo está marcado como lido
  const isChapterRead = (bookAbrev, chapter) => !!(bibleProgress[bookAbrev]?.[chapter]);
  const [commentModalOpen, setCommentModalOpen] = useState(false);
  const [commentText, setCommentText] = useState('');
  const [bibleShowAudioPlayer, setBibleShowAudioPlayer] = useState(true);
  const [activeSabadoBlock, setActiveSabadoBlock] = useState('menu');
  const [isNarrating, setIsNarrating] = useState(false);
  const [aiGenerating, setAiGenerating] = useState(false);

  // Estados específicos para o player de Meditação Guiada TTS
  const [meditationPlaying, setMeditationPlaying] = useState(false);
  const [meditationCurrentTime, setMeditationCurrentTime] = useState(0);
  const [meditationDuration, setMeditationDuration] = useState(120);
  const [showMeditationLyrics, setShowMeditationLyrics] = useState(false);
  const meditationIntervalRef = useRef(null);
  const [meditationCompleted, setMeditationCompleted] = useState(false);
  
  // Som ambiente de fundo e velocidade para Meditação
  const [activeAmbient, setActiveAmbient] = useState('none');
  const [ambientVolume, setAmbientVolume] = useState(0.15);
  const [narrationRate, setNarrationRate] = useState(0.82);
  const ambientAudioRef = useRef(null);
  const meditationTimeoutRef = useRef(null);
  const currentSegmentIndexRef = useRef(0);
  const meditationVideoRef = useRef(null);

  useEffect(() => {
    if (meditationVideoRef.current) {
      if (meditationPlaying) {
        meditationVideoRef.current.play().catch(() => {});
      } else {
        meditationVideoRef.current.pause();
      }
    }
  }, [meditationPlaying]);

  const [availableVoices, setAvailableVoices] = useState([]);
  const [selectedVoiceName, setSelectedVoiceName] = useState(localStorage.getItem('preferred_voice') || '');

  useEffect(() => {
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      const loadVoices = () => {
        const voices = window.speechSynthesis.getVoices();
        const ptVoices = voices.filter(v => v.lang.startsWith('pt'));
        setAvailableVoices(ptVoices);
        if (!localStorage.getItem('preferred_voice') && ptVoices.length > 0) {
          const best = ptVoices.find(v => v.name.includes('Natural')) || 
                       ptVoices.find(v => v.name.includes('Google')) || 
                       ptVoices[0];
          setSelectedVoiceName(best.name);
        }
      };
      loadVoices();
      window.speechSynthesis.onvoiceschanged = loadVoices;
    }
  }, []);

  // Trilhas de Crescimento
  const [trilhaAtiva, setTrilhaAtiva] = useState(null);
  const [listaTrilhas, setListaTrilhas] = useState([]);
  const [trilhaLoading, setTrilhaLoading] = useState(false);

  // Modo Escuro & Perfil
  const [darkMode, setDarkMode] = useState(() => {
    const saved = localStorage.getItem('1convite_dark_mode');
    if (saved !== null) return saved === 'true';
    return true;
  });

  useEffect(() => {
    document.body.style.cssText = '';
    document.body.classList.remove('dark-mode');
    const rootEl = document.getElementById('root');
    if (rootEl) rootEl.style.cssText = '';
  }, []);

  const [profileName, setProfileName] = useState('Membro Convidado');
  const [profileEmail, setProfileEmail] = useState('membro@1convite.com');
  const [profileAvatar, setProfileAvatar] = useState('https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=250&q=80');
  const [profileSavedMsg, setProfileSavedMsg] = useState('');

  // Login Dedicado
  const [loginEmail, setLoginEmail] = useState('');
  const [loginNome, setLoginNome] = useState('');
  const [loginMethod, setLoginMethod] = useState('google'); // 'google' ou 'email'
  const [loginError, setLoginError] = useState('');

  // Estados do Motor de Animação do Canvas por Scroll
  const [scrollPercent, setScrollPercent] = useState(0);
  const [framesLoaded, setFramesLoaded] = useState(false);
  const [loadProgress, setLoadProgress] = useState(0);
  const canvasRef = useRef(null);
  const imagesRef = useRef([]);

  const handleEmailLogin = async (e) => {
    e.preventDefault();
    if (!loginEmail || !loginNome) {
      setLoginError('Por favor, preencha todos os campos.');
      return;
    }
    const avatar = `https://api.dicebear.com/7.x/initials/svg?seed=${encodeURIComponent(loginNome)}`;

    try {
      const res = await fetch(`${API_BASE}/auth/convite`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ nome: loginNome, email: loginEmail, avatar })
      });
      if (res.ok) {
        const data = await res.json();
        setUser(data.user);
        setProfileName(data.user.nome);
        setProfileEmail(data.user.email);
        setProfileAvatar(data.user.avatar);
        setLoginEmail('');
        setLoginNome('');
        setLoginError('');
      } else {
        setLoginError('Erro ao fazer o login.');
      }
    } catch {
      setLoginError('Erro de conexão ao servidor.');
    }
  };

  // Auxiliar para decodificar JWT do Google no Frontend
  const parseJwt = (token) => {
    try {
      const base64Url = token.split('.')[1];
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
      const jsonPayload = decodeURIComponent(window.atob(base64).split('').map(function(c) {
          return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
      }).join(''));
      return JSON.parse(jsonPayload);
    } catch (e) {
      console.error('Erro ao fazer parse do JWT', e);
      return null;
    }
  };

  useEffect(() => {
    // DESABILITADO: só deve rodar para a LandingPage da Techla
    // if (profileEmail !== 'membro@1convite.com') return;
    return;
    
    // Forçar fundo preto no body e transparente no root para o vídeo de background aparecer
    const originalBodyBg = document.body.style.backgroundColor;
    document.body.style.backgroundColor = '#030303';
    
    const rootEl = document.getElementById('root');
    let originalRootBg = '';
    if (rootEl) {
      originalRootBg = rootEl.style.backgroundColor;
      rootEl.style.backgroundColor = 'transparent';
    }

    const video = document.getElementById("lp-bg-video");
    if (video) {
      video.load();
      video.currentTime = 0.01;
      
      const initScrollTrigger = () => {
        if (window.gsap && window.ScrollTrigger) {
          const gsap = window.gsap;
          const ScrollTrigger = window.ScrollTrigger;
          
          gsap.registerPlugin(ScrollTrigger);
          
          ScrollTrigger.create({
            trigger: ".lp-container",
            start: "top top",
            end: "bottom bottom",
            scrub: 1.5,
            onUpdate: (self) => {
              if (video.duration) {
                const targetTime = self.progress * video.duration;
                gsap.to(video, {
                  currentTime: targetTime,
                  duration: 0.1,
                  overwrite: "auto",
                  ease: "none"
                });
              }
            }
          });
        }
      };

      if (video.readyState >= 1) {
        initScrollTrigger();
      } else {
        video.addEventListener('loadedmetadata', initScrollTrigger);
      }

      return () => {
        document.body.style.backgroundColor = originalBodyBg;
        if (rootEl) rootEl.style.backgroundColor = originalRootBg;
        video.removeEventListener('loadedmetadata', initScrollTrigger);
      };
    }
  }, [profileEmail]);

  useEffect(() => {
    document.body.style.removeProperty('background-color');
    document.body.style.removeProperty('backgroundColor');
    const rootEl = document.getElementById('root');
    if (rootEl) {
      rootEl.style.removeProperty('background-color');
      rootEl.style.removeProperty('backgroundColor');
    }
    localStorage.setItem('1convite_dark_mode', darkMode);
    if (darkMode) {
      document.body.classList.add('dark-mode');
    } else {
      document.body.classList.remove('dark-mode');
    }
  }, [darkMode]);

  const handleAvatarUpload = async (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = async () => {
        const base64Avatar = reader.result;
        setProfileAvatar(base64Avatar);
        
        // Sincroniza com o servidor
        try {
          const res = await fetch(`${API_BASE}/usuario/perfil`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nome: profileName, email: profileEmail, avatar: base64Avatar })
          });
          if (res.ok) {
            const data = await res.json();
            setUser(data);
          }
        } catch (err) {
          console.error(err);
        }
      };
      reader.readAsDataURL(file);
    }
  };

  const handleSaveProfile = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch(`${API_BASE}/usuario/perfil`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ nome: profileName, email: profileEmail, avatar: profileAvatar })
      });
      if (res.ok) {
        const data = await res.json();
        setUser(data);
        setProfileSavedMsg('Dados atualizados com sucesso!');
        setTimeout(() => setProfileSavedMsg(''), 3000);
      }
    } catch (err) {
      alert('Erro ao salvar no banco de dados.');
    }
  };

  // Google Login Callback
  const handleGoogleLoginResponse = async (response) => {
    const payload = parseJwt(response.credential);
    if (!payload) return;
    
    const googleUser = {
      nome: payload.name,
      email: payload.email,
      avatar: payload.picture
    };

    try {
      const res = await fetch(`${API_BASE}/auth/convite`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(googleUser)
      });
      if (res.ok) {
        const data = await res.json();
        setUser(data.user);
        setProfileName(data.user.nome);
        setProfileEmail(data.user.email);
        setProfileAvatar(data.user.avatar);
      }
    } catch (err) {
      console.error('Erro de rede ao logar com o Google:', err);
    }
  };

  // Simular Login Google para desenvolvimento/testes locais imediatos
  const handleSimularLoginGoogle = async () => {
    const nome = prompt("Digite seu nome completo do Google:", "Jônatas Oliveira");
    if (!nome) return;
    const email = prompt("Digite seu e-mail do Google:", "jonatas.oliveira@gmail.com");
    if (!email) return;
    
    // Avatar default dinâmico
    const avatar = `https://api.dicebear.com/7.x/adventurer/svg?seed=${encodeURIComponent(nome)}`;

    try {
      const res = await fetch(`${API_BASE}/auth/convite`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ nome, email, avatar })
      });
      if (res.ok) {
        const data = await res.json();
        setUser(data.user);
        setProfileName(data.user.nome);
        setProfileEmail(data.user.email);
        setProfileAvatar(data.user.avatar);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleGuestLogin = async () => {
    try {
      const res = await fetch(`${API_BASE}/auth/convite`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          nome: "Convidado Visitante",
          email: "visitante@1convite.com",
          avatar: "https://api.dicebear.com/7.x/initials/svg?seed=Visitante"
        })
      });
      if (res.ok) {
        const data = await res.json();
        setUser(data.user);
        setProfileName(data.user.nome);
        setProfileEmail(data.user.email);
        setProfileAvatar(data.user.avatar);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleLogout = async () => {
    if (!confirm('Deseja realmente sair da conta?')) return;
    try {
      const res = await fetch(`${API_BASE}/usuario/perfil`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          nome: "Membro Convidado",
          email: "membro@1convite.com",
          avatar: "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=250&q=80"
        })
      });
      if (res.ok) {
        const updatedUser = await res.json();
        setUser(updatedUser);
        setProfileName(updatedUser.nome);
        setProfileEmail(updatedUser.email);
        setProfileAvatar(updatedUser.avatar);
      }
    } catch (e) {
      console.error(e);
    }
  };

  // Efeito para inicializar o botão do Google Identity Services
  useEffect(() => {
    // Desativado botão oficial para evitar erros de 403 no console local com ID dummy.
    // Usamos o botão customizado abaixo que simula o login com 100% de sucesso local.
    /*
    if (window.google) {
      setTimeout(() => {
        const container = document.getElementById("google-signin-btn-container") || document.getElementById("google-login-screen-container");
        if (container) {
          try {
            window.google.accounts.id.initialize({
              client_id: "777777777777-dummygoogleclientid.apps.googleusercontent.com",
              callback: handleGoogleLoginResponse
            });
            window.google.accounts.id.renderButton(
              container,
              { theme: "outline", size: "large", width: 320 }
            );
          } catch (err) {
            console.warn('Erro ao inicializar botão do Google:', err);
          }
        }
      }, 400);
    }
    */
  }, [activeTab, profileEmail, loginMethod]);

  const isCapacitor = Boolean(
    window.Capacitor || 
    window.location.protocol === 'capacitor:' || 
    window.location.protocol === 'file:' ||
    (typeof navigator !== 'undefined' && navigator.userAgent && navigator.userAgent.includes('Capacitor'))
  );
  const isLocalhost = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';

  const API_BASE = (isLocalhost && !isCapacitor)
    ? 'http://localhost:3001/api/v1'
    : '/api/v1';

  // ── TIMERS DOS JOGOS ──────────────────────────────────────
  // Timer do Quiz
  useEffect(() => {
    if (arcadeActiveGame !== 'quiz' || arcadeQuizGameOver || arcadeQuizFeedback || arcadeQuizTimer <= 0) return;
    const interval = setInterval(() => {
      setArcadeQuizTimer(prev => {
        if (prev <= 1) {
          // Tempo esgotado - avança para próxima pergunta ou game over
          clearInterval(interval);
          setArcadeQuizFeedback('wrong');
          setTimeout(() => {
            setArcadeQuizFeedback(null);
            const resetTime = arcadeDifficulty === 'facil' ? 30 : (arcadeDifficulty === 'avancado' ? 7 : 15);
            setArcadeQuizTimer(resetTime);
            if (arcadeQuizCurrentQuestion + 1 < arcadeQuizList.length) {
              setArcadeQuizCurrentQuestion(prev => prev + 1);
            } else {
              setArcadeQuizGameOver(true);
            }
          }, 1500);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(interval);
  }, [arcadeActiveGame, arcadeQuizGameOver, arcadeQuizFeedback, arcadeQuizTimer, arcadeQuizCurrentQuestion, arcadeQuizList.length, arcadeDifficulty]);

  // Timer das Charadas
  useEffect(() => {
    if (arcadeActiveGame !== 'charadas' || arcadeCharadasGameOver || arcadeCharadasFeedback || arcadeCharadasTimer === null || arcadeCharadasTimer <= 0) return;
    const interval = setInterval(() => {
      setArcadeCharadasTimer(prev => {
        if (prev <= 1) {
          // Tempo esgotado - avança ou game over
          clearInterval(interval);
          setArcadeCharadasFeedback('wrong');
          setTimeout(() => {
            setArcadeCharadasFeedback(null);
            if (arcadeCharadasCurrent + 1 < arcadeCharadasList.length) {
              setArcadeCharadasCurrent(prev => prev + 1);
              const resetTime = arcadeDifficulty === 'facil' ? null : (arcadeDifficulty === 'avancado' ? 7 : 15);
              setArcadeCharadasTimer(resetTime);
            } else {
              setArcadeCharadasGameOver(true);
            }
          }, 1500);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(interval);
  }, [arcadeActiveGame, arcadeCharadasGameOver, arcadeCharadasFeedback, arcadeCharadasTimer, arcadeCharadasCurrent, arcadeCharadasList.length, arcadeDifficulty]);

  // ── ChatGPT Integration & Chat IA ──────────────────────────
  useEffect(() => {
    fetch(`${API_BASE}/chatgpt/session`, { credentials: 'include' })
      .then(res => res.json())
      .then(data => {
        if (data && data.status === 'authenticated') {
          setLwcState('authenticated');
          setChatGptUser(data.user);
        }
      })
      .catch(err => console.error('Erro ao verificar sessão do ChatGPT:', err));
  }, [API_BASE]);

  const startLwcPolling = (intervalSeconds) => {
    setLwcPollingActive(true);
    const intervalMs = intervalSeconds * 1000;
    
    const poll = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE}/chatgpt/status`, { credentials: 'include' });
        if (res.ok) {
          const data = await res.json();
          if (data.status === 'authenticated') {
            clearInterval(poll);
            setLwcPollingActive(false);
            setLwcState('authenticated');
            setChatGptUser(data.user);
            setLwcDeviceCode(null);
          } else if (data.status === 'expired' || data.status === 'error') {
            clearInterval(poll);
            setLwcPollingActive(false);
            setLwcState('unauthenticated');
            setLwcDeviceCode(null);
          }
        }
      } catch (err) {
        console.error('Erro ao obter status do ChatGPT:', err);
      }
    }, intervalMs);

    return () => clearInterval(poll);
  };

  const handleConnectChatGPT = async () => {
    try {
      setLwcState('pending');
      const res = await fetch(`${API_BASE}/chatgpt/login`, { method: 'POST', credentials: 'include' });
      if (res.ok) {
        const data = await res.json();
        setLwcDeviceCode(data);
        startLwcPolling(data.interval || 5);
      } else {
        setLwcState('unauthenticated');
        alert('Erro ao iniciar conexão com ChatGPT.');
      }
    } catch (err) {
      setLwcState('unauthenticated');
      console.error(err);
    }
  };

  const handleDisconnectChatGPT = async () => {
    try {
      const res = await fetch(`${API_BASE}/chatgpt/logout`, { method: 'POST', credentials: 'include' });
      if (res.ok) {
        setLwcState('unauthenticated');
        setChatGptUser(null);
        setLwcDeviceCode(null);
      }
    } catch (err) {
      console.error('Erro ao desconectar ChatGPT:', err);
    }
  };

  const parseStreamChunk = (chunk) => {
    let text = '';
    const lines = chunk.split('\n');
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const dataStr = line.slice(6).trim();
        if (dataStr === '[DONE]') continue;
        try {
          const data = JSON.parse(dataStr);
          if (data.type === 'response.output_text.delta' && typeof data.delta === 'string') {
            text += data.delta;
          } else if (data.type === 'response.content_part.updated' || data.type === 'response.content_part.delta') {
            if (data.part?.text) text += data.part.text;
            else if (data.delta?.text) text += data.delta.text;
          } else if (data.type === 'text_delta') {
            text += data.text;
          } else if (data.delta?.content) {
            text += data.delta.content;
          } else if (data.part?.type === 'text' && data.part.text) {
            text += data.part.text;
          } else if (data.choices?.[0]?.delta?.content) {
            text += data.choices[0].delta.content;
          }
        } catch {
          // Ignore
        }
      }
    }
    return text;
  };

  const handleSendChatMessage = async (e, customText = null) => {
    if (e) e.preventDefault();
    const textToSend = customText || chatInput;
    if (!textToSend.trim() || chatLoading) return;

    if (lwcState !== 'authenticated') {
      alert('Conecte sua conta do ChatGPT na aba "Conta" para conversar com o Conselheiro IA.');
      return;
    }

    const newUserMessage = { role: 'user', content: textToSend };
    setChatMessages(prev => [...prev, newUserMessage]);
    setChatInput('');
    setChatLoading(true);

    try {
      const history = chatMessages.concat(newUserMessage);
      
      const payload = {
        stream: true,
        instructions: 'Você é o Conselheiro Inteligente do aplicativo 1Convite. Seu objetivo é ajudar o usuário com aconselhamento de relacionamentos, paz interior, espiritualidade e ideias de convites/conexões intencionais (café, reflexões, jantares, tempo de qualidade). Seja caloroso, empático, bíblico e focado no momento presente (o Agora). Responda sempre em português do Brasil.',
        input: history.map(msg => ({
          role: msg.role,
          content: [
            { 
              type: msg.role === 'user' ? 'input_text' : 'output_text', 
              text: msg.content 
            }
          ]
        }))
      };

      const res = await fetch(`${API_BASE}/chatgpt/responses`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        credentials: 'include'
      });

      if (!res.ok) {
        throw new Error('Falha ao obter resposta do ChatGPT.');
      }

      setChatMessages(prev => [...prev, { role: 'assistant', content: '' }]);

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let accumulatedText = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const newText = parseStreamChunk(chunk);
        if (newText) {
          accumulatedText += newText;
          setChatMessages(prev => {
            const updated = [...prev];
            updated[updated.length - 1] = { role: 'assistant', content: accumulatedText };
            return updated;
          });
        }
      }
    } catch (err) {
      console.error(err);
      setChatMessages(prev => [...prev, { role: 'assistant', content: 'Desculpe, ocorreu um erro ao obter a resposta.' }]);
    } finally {
      setChatLoading(false);
    }
  };

  // ── Bíblia ──────────────────────────────────────────────────
  const searchBible = async (e) => {
    e.preventDefault();
    if (!bibleSearchQuery || bibleSearchQuery.length < 3) { setBibleError('Digite pelo menos 3 letras.'); return; }
    setBibleLoading(true); setBibleError('');
    try {
      const res = await fetch(`${API_BASE}/biblia/busca?q=${encodeURIComponent(bibleSearchQuery)}`);
      const data = await res.json();
      if (res.ok) { setBibleResults(data); if (!data.length) setBibleError('Nenhum versículo encontrado.'); }
      else setBibleError(data.error);
    } catch { setBibleError('Erro de conexão.'); }
    finally { setBibleLoading(false); }
  };

  const getRandomVerse = async () => {
    setBibleLoading(true); setBibleError('');
    try {
      const res = await fetch(`${API_BASE}/biblia/aleatorio`);
      const data = await res.json();
      if (res.ok) { setBibleResults([data]); setBibleSearchQuery(''); }
    } catch { setBibleError('Erro ao puxar versículo.'); }
    finally { setBibleLoading(false); }
  };

  const copyToClipboard = (text) => { navigator.clipboard.writeText(text); alert('Versículo copiado!'); };

  // ── Carrossel ───────────────────────────────────────────────
  useEffect(() => {
    const t = setInterval(() => setCarouselIndex(p => (p + 1) % carouselImages.length), 8000);
    return () => clearInterval(t);
  }, []);

  // ── Helper de Requisição Segura ──────────────────────────────────
  const fetchJson = async (url, options) => {
    try {
      const res = await fetch(url, options);
      if (!res.ok) return null;
      const ct = res.headers.get('content-type') || '';
      if (!ct.includes('application/json')) return null;
      return await res.json();
    } catch {
      return null;
    }
  };

  // ── Dados iniciais ──────────────────────────────────────────
  const loadAppData = async () => {
    try {
      const d = await fetchJson(`${API_BASE}/codigo-dia`);
      if (d) {
        setUser(d.user); 
        setCodigoDia(d.code);
        if (d.user) {
          setProfileName(d.user.nome || 'Membro Convidado');
          setProfileEmail(d.user.email || 'membro@1convite.com');
          setProfileAvatar(d.user.avatar || 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=250&q=80');
        }
        if (d.user && !d.user.checkpoint_completado) { setActiveTab('pedagio'); if (!pedagioIniciado) iniciarPedagio(); }
        else {
          if (activeTab === 'pedagio') setActiveTab('sabado');
        }
      }
      const contatosData = await fetchJson(`${API_BASE}/contatos`);
      if (contatosData) setContatos(contatosData);
      
      const historicoData = await fetchJson(`${API_BASE}/historico`);
      if (historicoData) setHistorico(historicoData.rows || []);
      
      await loadTrilhaStatus();
      await loadDicionario();
    } catch (e) { console.error(e); }
  };

  const loadDicionario = async () => {
    try {
      const data = await fetchJson(`${API_BASE}/dicionario/termos`);
      if (data) setDicionario(data);
    } catch (e) { console.error(e); }
  };

  const loadTrilhaStatus = async () => {
    try {
      const listData = await fetchJson(`${API_BASE}/trilhas/lista`);
      if (listData) setListaTrilhas(listData);
      
      const dataAtiva = await fetchJson(`${API_BASE}/trilhas/ativa`);
      if (dataAtiva) setTrilhaAtiva(dataAtiva.ativa ? dataAtiva : null);
    } catch (e) { console.error(e); }
  };

  const loadBibleBooks = async () => {
    try {
      const books = await fetchJson(`${API_BASE}/biblia/livros`);
      if (books) setBibleBooks(books);
    } catch (e) { console.error(e); }
  };

  useEffect(() => { loadAppData(); loadBibleBooks(); }, []);

  useEffect(() => {
    if (activeTab !== 'biblia') return;
    const load = async () => {
      try {
        setBibleLoading(true);
        setBibleAudioPlaying(false);
        setBibleAudioUrl('');
        
        const dc = await fetchJson(`${API_BASE}/biblia/capitulos/${bibleSelectedBook.livro_abrev}`);
        if (dc) setBibleChaptersCount(dc.total || 50);
        
        const verses = await fetchJson(`${API_BASE}/biblia/texto/${bibleSelectedBook.livro_abrev}/${bibleSelectedChapter}`);
        if (verses) setBibleVerses(verses);

        // Carrega o áudio com fallback
        const dataAudio = await fetchJson(`${API_BASE}/biblia/audio/${bibleSelectedBook.livro_abrev}/${bibleSelectedChapter}`);
        if (dataAudio) {
          setBibleAudioUrl(dataAudio.proxy || dataAudio.url || '/piano.mp3');
        } else {
          setBibleAudioUrl('/piano.mp3');
        }
      } catch (e) { console.error(e); } finally { setBibleLoading(false); }
    };
    load();
  }, [bibleSelectedBook, bibleSelectedChapter, activeTab]);

  // ── Pedágio ─────────────────────────────────────────────────
  const iniciarPedagio = async () => {
    try { setPedagioIniciado(true); setCountdown(12); setIsCountdownActive(true); await fetch(`${API_BASE}/checkpoint/start`, { method: 'POST' }); }
    catch (e) { console.error(e); }
  };

  useEffect(() => {
    let t;
    if (activeTab === 'pedagio' && isCountdownActive && countdown > 0) t = setTimeout(() => setCountdown(p => p - 1), 1000);
    else if (countdown === 0) setIsCountdownActive(false);
    return () => clearTimeout(t);
  }, [countdown, activeTab, isCountdownActive]);

  const destravarAgora = async () => {
    try {
      const res = await fetch(`${API_BASE}/sync-checkpoint`, { method: 'POST' });
      const data = await res.json();
      if (res.ok && data.success) {
        setPedagioIniciado(false);
        setPedagioErro('');
        setUser(prev => prev ? { ...prev, checkpoint_completado: true } : { ...data.user, checkpoint_completado: true });
        setActiveTab('sabado');
        loadAppData();
      } else {
        setPedagioErro(data.error || 'Erro ao destravar');
      }
    } catch {
      setPedagioErro('Erro de comunicação.');
    }
  };

  // ── Contatos ────────────────────────────────────────────────
  const handleAddContato = async (e) => {
    e.preventDefault(); setContatoErro('');
    if (!newNome || !newRelacao) { setContatoErro('Preencha todos os campos.'); return; }
    try {
      const res = await fetch(`${API_BASE}/contatos`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ nome: newNome, relacao: newRelacao, prioritario: newPrioritario }) });
      const data = await res.json();
      if (res.ok) { setNewNome(''); setNewRelacao(''); setNewPrioritario(false); setShowAddContato(false); loadAppData(); }
      else setContatoErro(data.error || 'Erro ao cadastrar.');
    } catch { setContatoErro('Falha de conexão.'); }
  };

  const deletarContato = async (id) => {
    if (!confirm('Remover este contato?')) return;
    try { await fetch(`${API_BASE}/contatos/${id}`, { method: 'DELETE' }); loadAppData(); } catch (e) { console.error(e); }
  };

  const registrarAcao = async (id, tipoAcao) => {
    try { await fetch(`${API_BASE}/contatos/${id}/acao`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ tipoAcao }) }); loadAppData(); }
    catch (e) { console.error(e); }
  };

  const verificarAlerta48h = (c) => {
    if (!c.prioritario) return false;
    if (c.ultimo_convite_timestamp === 0) return true;
    return (Date.now() - c.ultimo_convite_timestamp) / 3600000 >= 48;
  };

  // ── Respiração (Botão do Descanso Pró) ──────────────────────
  const playChime = (freq = 440, type = 'sine', duration = 1.2) => {
    try {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (!AudioCtx) return;
      const ctx = new AudioCtx();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = type;
      osc.frequency.setValueAtTime(freq, ctx.currentTime);
      gain.gain.setValueAtTime(0.12, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + duration);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start();
      osc.stop(ctx.currentTime + duration);
    } catch (e) {
      console.warn('AudioContext bloqueado:', e);
    }
  };

  const triggerHaptic = (ms = 50) => {
    if (typeof navigator !== 'undefined' && navigator.vibrate) {
      navigator.vibrate(ms);
    }
  };

  const pararRespiracao = () => {
    isBreathingActiveRef.current = false;
    setIsBreathing(false);
    setBreathState('Toque para iniciar');
    setBreathClass('');
    if (breathIntervalRef.current) {
      clearInterval(breathIntervalRef.current);
      breathIntervalRef.current = null;
    }
  };

  const iniciarRespiracao = () => {
    if (isBreathing) return;
    isBreathingActiveRef.current = true;
    setIsBreathing(true);
    setCurrentRound(1);
    
    let phases = [];
    if (breathTechnique === 'box') {
      phases = [
        { text: 'Inspire...', cls: 'inhaling', d: 4, freq: 528, osc: 'sine' },
        { text: 'Segure...', cls: 'holding', d: 4, freq: 639, osc: 'sine' },
        { text: 'Expire...', cls: 'exhaling', d: 4, freq: 396, osc: 'triangle' },
        { text: 'Aguarde...', cls: 'holding-empty', d: 4, freq: 432, osc: 'sine' }
      ];
    } else if (breathTechnique === 'relax') {
      phases = [
        { text: 'Inspire...', cls: 'inhaling', d: 4, freq: 528, osc: 'sine' },
        { text: 'Segure...', cls: 'holding', d: 7, freq: 639, osc: 'sine' },
        { text: 'Expire...', cls: 'exhaling', d: 8, freq: 396, osc: 'triangle' }
      ];
    } else {
      phases = [
        { text: 'Inspire...', cls: 'inhaling', d: 4, freq: 528, osc: 'sine' },
        { text: 'Segure...', cls: 'holding', d: 4, freq: 639, osc: 'sine' },
        { text: 'Expire...', cls: 'exhaling', d: 4, freq: 396, osc: 'triangle' }
      ];
    }

    let round = 1;
    let step = 0;

    const run = () => {
      if (!isBreathingActiveRef.current) return;
      
      if (round > breathRounds) {
        playChime(528, 'sine', 1.8);
        setTimeout(() => playChime(432, 'sine', 2.0), 100);
        triggerHaptic([80, 50, 80]);
        setBreathState('Desfrute Completo! ✨');
        setBreathClass('');
        setIsBreathing(false);
        isBreathingActiveRef.current = false;
        return;
      }

      if (step >= phases.length) {
        step = 0;
        round++;
        if (round <= breathRounds) {
          setCurrentRound(round);
          run();
        } else {
          // Finalização
          playChime(528, 'sine', 1.8);
          setTimeout(() => playChime(432, 'sine', 2.0), 100);
          triggerHaptic([80, 50, 80]);
          setBreathState('Desfrute Completo! ✨');
          setBreathClass('');
          setIsBreathing(false);
          isBreathingActiveRef.current = false;
        }
        return;
      }

      const ph = phases[step];
      setBreathState(ph.text);
      setBreathClass(ph.cls);
      setBreathTimer(ph.d);
      
      playChime(ph.freq, ph.osc, 1.2);
      triggerHaptic(50);

      let cv = ph.d;
      breathIntervalRef.current = setInterval(() => {
        if (!isBreathingActiveRef.current) {
          clearInterval(breathIntervalRef.current);
          return;
        }
        cv--;
        setBreathTimer(cv);
        if (cv <= 0) {
          clearInterval(breathIntervalRef.current);
          step++;
          run();
        }
      }, 1000);
    };

    run();
  };

  // ── Áudio Sabático ──────────────────────────────────────────
  useEffect(() => {
    if (!audioRef.current) return;
    if (audioPlaying) audioRef.current.play().catch(() => setAudioPlaying(false));
    else audioRef.current.pause();
  }, [audioPlaying]);

  const onAudioTimeUpdate = () => { if (audioRef.current) setAudioCurrentTime(audioRef.current.currentTime); };
  const onAudioLoadedMetadata = () => { if (audioRef.current) setAudioDuration(audioRef.current.duration); };
  const formatTime = (s) => { if (s === null || s === undefined || isNaN(s) || !isFinite(s)) return '0:00'; return `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, '0')}`; };
  const handleProgressBarClick = (e) => {
    const r = e.currentTarget.getBoundingClientRect();
    if (audioRef.current) { audioRef.current.currentTime = ((e.clientX - r.left) / r.width) * audioDuration; setAudioCurrentTime(audioRef.current.currentTime); }
  };

  const speakReflection = () => {
    if (!('speechSynthesis' in window)) {
      alert('Narração de voz não disponível no navegador.');
      return;
    }
    if (isNarrating) {
      window.speechSynthesis.cancel();
      setIsNarrating(false);
      return;
    }
    const texto = `${codigoDia.codigo_verbal}. Versículo chave: ${codigoDia.versiculo_chave}. Reflexão: ${codigoDia.texto_reflexao.replace(/\n/g, ' ')}`;
    const utterance = new SpeechSynthesisUtterance(texto);
    utterance.lang = 'pt-BR';
    utterance.rate = voiceSpeed * 1.05;

    if ('speechSynthesis' in window) {
      const voice = getBestVoiceForGender(voiceGender);
      if (voice) {
        utterance.voice = voice;
      }
    }

    utterance.onend = () => setIsNarrating(false);
    utterance.onerror = () => setIsNarrating(false);
    setIsNarrating(true);
    window.speechSynthesis.speak(utterance);
  };

  const generateDailyReflectionWithAI = async () => {
    if (!codigoDia) return;
    try {
      setAiGenerating(true);
      const prompt = `Você é o teólogo e historiador oficial do aplicativo 1Convite.
Gere um devocional cristão inspirador e um script de Oração Guiada no Estilo de Jesus (Ação de Graças, Certeza de que o Pai ouve e Alinhamento com o Propósito) para o Dia ${codigoDia.dia_id}.
O pilar bíblico deste dia é ${codigoDia.pilar_origem === 'PROPÓSITO_M2414' ? 'Mateus 24:14 (Propósito)' : 'Apocalipse 3:21 (Recompensa)'}.

Você deve responder EXCLUSIVAMENTE em formato JSON (sem formatação markdown fora do JSON ou explicações extras):
{
  "codigo_verbal": "Código ${codigoDia.dia_id}: [Escreva um título/código curto e impactante sobre relacionamento intencional, mesa, comunhão, desacelerar ou servir]",
  "versiculo_chave": "[Insira um versículo bíblico real e sua referência no formato Livro Capítulo:Versículo]",
  "texto_reflexao": "[Escreva a reflexão prática do dia inspirada no versículo. Após a reflexão, insira duas quebras de linha e conte uma história real e verídica da história do cristianismo que exemplifique perfeitamente este tema (ex: biographies de heróis da fé, missionários, momentos de avivamento). Insira a história sob o título '📖 HISTÓRIA CRISTÃ REAL:\\n[sua história aqui]']",
  "texto_meditacao": "[Escreva um Roteiro de Oração Guiada no Estilo de Jesus com cerca de 4 blocos. Use os seguintes títulos de blocos no roteiro: '🟢 1. O Ponto de Partida: Ação de Graças pelo Hoje' (Tom de voz: Calmo, grato, pausado), '🟡 2. O Alinhamento: Tudo o que Tenho é Suficiente', '🟠 3. O Propósito e o Mover no Agora' (Tom de voz: Firme, consciente, de governo), '🔴 4. A Selagem do Convite' (Tom de voz: Decidido, pronto para a ação). Insira marcadores de silêncio programados como '(Pausa de 3 segundos)' ou '(Pausa de 4 segundos)' de forma estratégica entre os parágrafos para simular pausas reais na leitura.]"
}

Importante: O JSON deve ser 100% válido.`;

      const res = await fetch(`${API_BASE}/chatgpt/responses`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: [
            { role: 'system', content: 'Você é um assistente teológico que responde estritamente no formato JSON puro especificado pelo usuário.' },
            { role: 'user', content: prompt }
          ]
        }),
        credentials: 'include'
      });

      if (res.ok) {
        const data = await res.json();
        const contentText = data.choices[0].message.content;
        const cleanJson = contentText.replace(/```json|```/g, '').trim();
        const generated = JSON.parse(cleanJson);

        const saveRes = await fetch(`${API_BASE}/codigo-dia/save`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            dia_id: codigoDia.dia_id,
            codigo_verbal: generated.codigo_verbal,
            versiculo_chave: generated.versiculo_chave,
            texto_reflexao: generated.texto_reflexao,
            texto_meditacao: generated.texto_meditacao
          })
        });

        if (saveRes.ok) {
          setCodigoDia({
            ...codigoDia,
            codigo_verbal: generated.codigo_verbal,
            versiculo_chave: generated.versiculo_chave,
            texto_reflexao: generated.texto_reflexao,
            texto_meditacao: generated.texto_meditacao
          });
        } else {
          alert('Erro ao salvar reflexão gerada.');
        }
      } else {
        alert('Erro ao solicitar resposta do ChatGPT.');
      }
    } catch (err) {
      console.error('Erro na geração com IA:', err);
      alert('Falha na geração: verifique sua conexão com o ChatGPT.');
    } finally {
      setAiGenerating(false);
    }
  };

  const ambientTracks = [
    { id: 'none', label: '🔕 Silêncio', url: '' },
    { id: 'chuva', label: '🌧️ Chuva', url: '/rain.mp3' },
    { id: 'mar', label: '🌊 Ondas', url: '/ocean.mp3' },
    { id: 'piano', label: '🎹 Piano', url: '/piano.mp3' }
  ];

  useEffect(() => {
    if (ambientAudioRef.current) {
      ambientAudioRef.current.volume = ambientVolume;
    }
  }, [ambientVolume]);

  useEffect(() => {
    if (!ambientAudioRef.current) return;
    ambientAudioRef.current.pause();
    
    const track = ambientTracks.find(t => t.id === activeAmbient);
    if (track && track.url) {
      ambientAudioRef.current.src = track.url;
      ambientAudioRef.current.loop = true;
      if (meditationPlaying) {
        ambientAudioRef.current.volume = ambientVolume;
        ambientAudioRef.current.play().catch(() => {});
      }
    }
  }, [activeAmbient]);

  const stopMeditation = () => {
    window.speechSynthesis.cancel();
    setMeditationPlaying(false);
    if (ambientAudioRef.current) {
      ambientAudioRef.current.pause();
    }
    if (meditationIntervalRef.current) {
      clearInterval(meditationIntervalRef.current);
      meditationIntervalRef.current = null;
    }
    if (meditationTimeoutRef.current) {
      clearTimeout(meditationTimeoutRef.current);
      meditationTimeoutRef.current = null;
    }
  };

  const toggleMeditationTTS = () => {
    if (!('speechSynthesis' in window)) {
      alert('Narração de voz não disponível no navegador.');
      return;
    }

    if (meditationPlaying) {
      stopMeditation();
      return;
    }

    const rawText = codigoDia.texto_meditacao || 'Respire fundo... e concentre-se.';
    
    // Parser profissional: extrai pausas programadas e tons de voz
    const lines = rawText.split('\n');
    const segments = [];
    let currentRate = narrationRate;
    
    for (let line of lines) {
      line = line.trim();
      if (!line) continue;
      
      // Ignorar metadados de guia
      if (line.startsWith('Roteiro de Meditação') || line.startsWith('Duração') || line.startsWith('Trilha de fundo') || line.startsWith('🟢') || line.startsWith('🟡') || line.startsWith('🟠') || line.startsWith('🔴')) {
        continue;
      }
      
      // Tom de voz
      if (line.startsWith('(Tom de voz:')) {
        if (line.includes('Suave') || line.includes('pausado')) {
          currentRate = narrationRate * 0.9;
        } else if (line.includes('Firme') || line.includes('ritmo')) {
          currentRate = narrationRate * 1.05;
        } else {
          currentRate = narrationRate;
        }
        continue;
      }
      
      // Pausa programada
      const pauseMatch = line.match(/\(Pausa de (\d+) segundos\)/i);
      if (pauseMatch) {
        const secs = parseInt(pauseMatch[1], 10);
        segments.push({ type: 'pause', duration: secs * 1000 });
        continue;
      }
      
      const cleanLine = line.replace(/^["']|["']$/g, '');
      if (cleanLine) {
        segments.push({ type: 'text', text: cleanLine, rate: currentRate });
      }
    }

    if (segments.length === 0) {
      segments.push({ type: 'text', text: rawText, rate: narrationRate });
    }

    // Calcular duração com precisão (considerando velocidade da fala e pausas de respiração)
    let totalSecs = 0;
    segments.forEach(seg => {
      if (seg.type === 'pause') {
        totalSecs += seg.duration / 1000;
      } else {
        const wc = seg.text.split(' ').length;
        totalSecs += Math.max(3.5, Math.round((wc * 0.65) / seg.rate));
      }
    });

    setMeditationDuration(totalSecs);
    setMeditationCurrentTime(0);
    setMeditationPlaying(true);
    setMeditationCompleted(false);

    if (activeAmbient !== 'none' && ambientAudioRef.current) {
      const track = ambientTracks.find(t => t.id === activeAmbient);
      if (track && track.url) {
        ambientAudioRef.current.src = track.url;
        ambientAudioRef.current.loop = true;
        ambientAudioRef.current.volume = ambientVolume;
        ambientAudioRef.current.play().catch(() => {});
      }
    }

    const startTime = Date.now();
    meditationIntervalRef.current = setInterval(() => {
      const elapsed = Math.round((Date.now() - startTime) / 1000);
      setMeditationCurrentTime(Math.min(elapsed, totalSecs));
    }, 1000);

    const playSegment = (index) => {
      if (index >= segments.length) {
        setMeditationCompleted(true);
        // Mantém som ambiente por mais 15s de contemplação antes de terminar
        meditationTimeoutRef.current = setTimeout(() => {
          stopMeditation();
          setMeditationCurrentTime(totalSecs);
        }, 15000);
        return;
      }

      currentSegmentIndexRef.current = index;
      const seg = segments[index];

      if (seg.type === 'pause') {
        meditationTimeoutRef.current = setTimeout(() => {
          playSegment(index + 1);
        }, seg.duration);
      } else {
        const utterance = new SpeechSynthesisUtterance(seg.text);
        utterance.lang = 'pt-BR';
        utterance.rate = seg.rate * voiceSpeed;
        utterance.pitch = 0.95;

        if ('speechSynthesis' in window) {
          const voice = getBestVoiceForGender(voiceGender);
          if (voice) {
            utterance.voice = voice;
          }
        }

        utterance.onend = () => {
          meditationTimeoutRef.current = setTimeout(() => {
            playSegment(index + 1);
          }, 800);
        };

        utterance.onerror = () => {
          stopMeditation();
        };

        window.speechSynthesis.speak(utterance);
      }
    };

    playSegment(0);
  };

  // ── Áudio da Bíblia ─────────────────────────────────────────
  useEffect(() => {
    if (!bibleAudioRef.current) return;
    if (bibleAudioPlaying) {
      setAudioPlaying(false);
      bibleAudioRef.current.play().catch(() => setBibleAudioPlaying(false));
    } else {
      bibleAudioRef.current.pause();
    }
  }, [bibleAudioPlaying]);

  const onBibleAudioTimeUpdate = () => { if (bibleAudioRef.current) setBibleAudioCurrentTime(bibleAudioRef.current.currentTime); };
  const onBibleAudioLoadedMetadata = () => { if (bibleAudioRef.current) setBibleAudioDuration(bibleAudioRef.current.duration); };
  const handleBibleAudioProgressBarClick = (e) => {
    const r = e.currentTarget.getBoundingClientRect();
    if (bibleAudioRef.current) {
      bibleAudioRef.current.currentTime = ((e.clientX - r.left) / r.width) * bibleAudioDuration;
      setBibleAudioCurrentTime(bibleAudioRef.current.currentTime);
    }
  };

  // ── Trilhas de Crescimento ──────────────────────────────────
  const iniciarTrilha = async (tema) => {
    try {
      setTrilhaLoading(true);
      const res = await fetch(`${API_BASE}/trilhas/iniciar`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tema })
      });
      if (res.ok) {
        alert(`Trilha de ${tema} iniciada com sucesso!`);
        await loadTrilhaStatus();
      }
    } catch (e) {
      console.error(e);
    } finally {
      setTrilhaLoading(false);
    }
  };

  const completarDiaTrilha = async () => {
    try {
      setTrilhaLoading(true);
      const res = await fetch(`${API_BASE}/trilhas/completar-dia`, { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        if (data.concluida) {
          alert('Parabéns! Você concluiu os 30 dias desta Trilha de Crescimento! 🏆');
        } else {
          alert('Devocional de hoje concluído! Avançando na trilha.');
        }
        await loadTrilhaStatus();
      }
    } catch (e) {
      console.error(e);
    } finally {
      setTrilhaLoading(false);
    }
  };

  const cancelarTrilha = async () => {
    if (!confirm('Deseja realmente cancelar a trilha ativa? Seu progresso será perdido.')) return;
    try {
      setTrilhaLoading(true);
      const res = await fetch(`${API_BASE}/trilhas/cancelar`, { method: 'POST' });
      if (res.ok) {
        await loadTrilhaStatus();
      }
    } catch (e) {
      console.error(e);
    } finally {
      setTrilhaLoading(false);
    }
  };

  // ── Dicionário Teológico ─────────────────────────────────────
  const formatVerseText = (text) => {
    if (!dicionario || Object.keys(dicionario).length === 0) return text;
    
    const termos = Object.keys(dicionario).sort((a, b) => b.length - a.length);
    const pattern = termos.map(t => t.replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&')).join('|');
    if (!pattern) return text;
    
    const regex = new RegExp(`\\b(${pattern})\\b`, 'gi');
    const parts = text.split(regex);
    
    return parts.map((part, i) => {
      const lowerPart = part.toLowerCase();
      if (dicionario[lowerPart]) {
        return (
          <span 
            key={i} 
            className="dict-term" 
            onClick={(e) => {
              e.stopPropagation();
              setSelectedDicionarioTermo({ termo: part, significado: dicionario[lowerPart] });
            }}
          >
            {part}
          </span>
        );
      }
      return part;
    });
  };

  // ── Pagamento ───────────────────────────────────────────────
  const iniciarCheckoutMercadoPago = async () => {
    try { setIsPaying(true); const res = await fetch(`${API_BASE}/pagamentos/criar-preferencia`, { method: 'POST' }); const d = await res.json(); if (res.ok) { setPaymentPreferenceId(d.preferenceId); setActiveTab('simular-pagamento'); } }
    catch (e) { console.error(e); } finally { setIsPaying(false); }
  };

  const finalizarPagamentoSimulado = async () => {
    try {
      const res = await fetch(`${API_BASE}/pagamentos/webhook`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ action: 'payment.created', pref_id: paymentPreferenceId }) });
      if (res.ok) { alert('Pagamento aprovado! Plano Premium ativado.'); loadAppData(); setActiveTab('sabado'); }
    } catch (e) { console.error(e); }
  };

  // ── Admin ───────────────────────────────────────────────────
  const avancarDia = async () => { try { const r = await fetch(`${API_BASE}/avancar-dia`, { method: 'POST' }); if (r.ok) { loadAppData(); alert('Dia avançado!'); } else alert('Erro ao avançar.'); } catch (e) { console.error(e); } };
  const reiniciarJornada = async () => { if (!confirm('Reiniciar ao Dia 1?')) return; try { await fetch(`${API_BASE}/reiniciar-jornada`, { method: 'POST' }); loadAppData(); } catch (e) { console.error(e); } };
  const alterarPlanoAdmin = async (p) => { try { await fetch(`${API_BASE}/admin/definir-plano`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ plano: p }) }); loadAppData(); } catch (e) { console.error(e); } };

  // ═══════════════════════════════════════════════════════════
  //  TELA PEDÁGIO
  // ═══════════════════════════════════════════════════════════
  if (activeTab === 'pedagio' && codigoDia) {
    const isProposito = codigoDia.pilar_origem === 'PROPÓSITO_M2414';
    return (
      <div className="pedagio-overlay">
        <div style={{ position: 'fixed', width: 300, height: 300, borderRadius: '50%', background: 'radial-gradient(circle, rgba(249,115,22,0.12) 0%, transparent 70%)', top: -80, right: -60, filter: 'blur(50px)', pointerEvents: 'none' }} />
        <div style={{ position: 'fixed', width: 250, height: 250, borderRadius: '50%', background: 'radial-gradient(circle, rgba(51,65,85,0.10) 0%, transparent 70%)', bottom: 80, left: -60, filter: 'blur(50px)', pointerEvents: 'none' }} />

        <div className="pedagio-container">
          <div style={{ textAlign: 'center' }}>
            <img src="/LOGOMARCA.png" alt="1Convite" style={{ height: '38px', objectFit: 'contain' }} />
          </div>

          <div style={{ textAlign: 'center' }}>
            <div className={`pedagio-badge ${isProposito ? 'badge-proposito' : 'badge-recompensa'}`}>
              {isProposito ? 'Mateus 24:14 — Propósito' : 'Apocalipse 3:21 — Recompensa'}
            </div>
            <h1 style={{ fontSize: '1.4rem', marginTop: '8px' }}>Dia {codigoDia.dia_id} da Jornada</h1>
            <p style={{ color: '#78716C', marginTop: '4px' }}>Alinhamento mental no Agora de Deus</p>
          </div>

          <div className="pedagio-card">
            <div className="pedagio-codigo">"{codigoDia.codigo_verbal}"</div>
            <div className="pedagio-versiculo">{codigoDia.versiculo_chave}</div>
            <div className="pedagio-reflexao">{codigoDia.texto_reflexao}</div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '14px' }}>
            {countdown > 0 && <div className="timer-circle"><span style={{ animation: 'none' }}>{countdown}</span></div>}
            {pedagioErro && <p style={{ color: '#ef4444', textAlign: 'center' }}>{pedagioErro}</p>}
            <button className="btn-primary" onClick={destravarAgora} disabled={countdown > 0} style={{ maxWidth: 360 }}>
              {countdown > 0 ? `⏳ Medite... (${countdown}s)` : '🔓 Destravar o Agora'}
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (currentPath === '/baixar' || currentPath === '/app') {
    return (
      <div style={{
        background: '#09090b',
        color: '#fafafa',
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        padding: '24px 16px',
        fontFamily: "'Inter', sans-serif"
      }}>
        {/* Header */}
        <div style={{ textAlign: 'center', marginTop: '40px', marginBottom: '32px' }}>
          <h1 style={{ fontSize: '2.2rem', color: 'var(--orange)', marginBottom: '8px', fontWeight: '900' }}>1Convite</h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '1rem' }}>Instale o aplicativo oficial no seu celular</p>
        </div>

        {/* Mascote Chaminha conversando com o usuário */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '32px', maxWidth: '480px', width: '100%', padding: '0 8px' }}>
          <ChaminhaVideo size={70} style={{ flexShrink: 0 }} />
          <div className="glass-panel" style={{
            padding: '12px 18px',
            borderRadius: '16px',
            fontSize: '0.9rem',
            color: 'var(--text-secondary)',
            border: '1px solid rgba(255, 255, 255, 0.08)',
            position: 'relative',
            background: 'rgba(255, 255, 255, 0.02)',
            flex: 1,
            textAlign: 'left'
          }}>
            <div style={{
              position: 'absolute', top: '50%', left: '-6px', transform: 'translateY(-50%) rotate(45deg)',
              width: '10px', height: '10px', background: '#09090b', borderLeft: '1px solid rgba(255, 255, 255, 0.08)',
              borderBottom: '1px solid rgba(255, 255, 255, 0.08)', zIndex: 1
            }} />
            🔥 <strong>Chaminha:</strong> "Leve o seu círculo de influência e devocionais diários para qualquer lugar instalando o app direto no celular!"
          </div>
        </div>

        {/* Card Principal de Download */}
        <div className="glass-panel" style={{ maxWidth: '480px', width: '100%', padding: '28px 20px', borderRadius: '20px', border: '1px solid rgba(255, 255, 255, 0.1)', background: 'rgba(255, 255, 255, 0.02)', marginBottom: '24px', boxSizing: 'border-box' }}>
          
          {/* Botão de Download */}
          <a href="/1convite.apk" download style={{ textDecoration: 'none' }}>
            <button className="btn-primary" style={{ width: '100%', padding: '16px', fontSize: '1.05rem', background: 'var(--grad-orange)', color: '#fff', fontWeight: 'bold', border: 'none', borderRadius: '12px', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '10px', boxShadow: 'var(--shadow-orange)' }}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
              Baixar Aplicativo Android (.APK)
            </button>
          </a>

          {/* Instruções Android */}
          <div style={{ marginTop: '28px', textAlign: 'left' }}>
            <h3 style={{ fontSize: '1.05rem', color: '#fff', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 'bold' }}>
              🤖 Como instalar no seu Android:
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div style={{ display: 'flex', gap: '12px' }}>
                <span style={{ background: 'var(--orange)', color: '#fff', width: '22px', height: '22px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold', fontSize: '0.8rem', flexShrink: 0 }}>1</span>
                <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: '1.45' }}>
                  Clique no botão acima para iniciar o download do arquivo <strong>1convite.apk</strong>.
                </p>
              </div>
              <div style={{ display: 'flex', gap: '12px' }}>
                <span style={{ background: 'var(--orange)', color: '#fff', width: '22px', height: '22px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold', fontSize: '0.8rem', flexShrink: 0 }}>2</span>
                <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: '1.45' }}>
                  Quando concluir, clique no arquivo para abrir. Se surgir um alerta do sistema, toque em <strong>Configurações</strong>.
                </p>
              </div>
              <div style={{ display: 'flex', gap: '12px' }}>
                <span style={{ background: 'var(--orange)', color: '#fff', width: '22px', height: '22px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold', fontSize: '0.8rem', flexShrink: 0 }}>3</span>
                <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: '1.45' }}>
                  Habilite a permissão **"Permitir desta fonte"** (ou "Fontes Desconhecidas") para o seu navegador.
                </p>
              </div>
              <div style={{ display: 'flex', gap: '12px' }}>
                <span style={{ background: 'var(--orange)', color: '#fff', width: '22px', height: '22px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold', fontSize: '0.8rem', flexShrink: 0 }}>4</span>
                <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: '1.45' }}>
                  Volte para a tela de instalação, clique em <strong>Instalar</strong> e depois em <strong>Abrir</strong>. Pronto!
                </p>
              </div>
            </div>
          </div>

          {/* Instruções iOS */}
          <div style={{ marginTop: '28px', paddingTop: '20px', borderTop: '1px solid rgba(255,255,255,0.08)', textAlign: 'left' }}>
            <h3 style={{ fontSize: '1.05rem', color: '#fff', marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 'bold' }}>
              🍎 Usuários de iPhone (iOS):
            </h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: '1.45', margin: '0 0 12px 0' }}>
              O iOS não aceita instalações fora da loja oficial. Mas você pode instalar o app instantaneamente como um <strong>Atalho na Tela de Início</strong>:
            </p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <div style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
                1. Abra <strong>1convite.com.br</strong> no navegador **Safari**.
              </div>
              <div style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
                2. Toque no ícone de <strong>Compartilhar</strong> (quadrado com seta para cima).
              </div>
              <div style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
                3. Role e selecione a opção <strong>"Adicionar à Tela de Início"</strong>.
              </div>
            </div>
          </div>

        </div>

        {/* Voltar para Web */}
        <button onClick={() => {
          window.location.href = '/';
        }} style={{ background: 'transparent', border: 'none', color: 'var(--orange)', cursor: 'pointer', fontSize: '0.88rem', fontWeight: '600', textDecoration: 'underline', marginBottom: '40px' }}>
          Acessar a Versão Web
        </button>
      </div>
    );
  }


  // if (profileEmail === 'membro@1convite.com') {
  //   return <LandingPage />;
  // }

  return (
    <div className="app-container">
      {showOnboarding && <Onboarding onComplete={() => setShowOnboarding(false)} />}
      <header className="app-header" style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '12px 16px',
        height: '60px',
        boxSizing: 'border-box'
      }}>
        {activeTab === 'dashboard' ? (
          <>
            {/* Esquerda: Perfil/Avatar */}
            <div 
              onClick={() => setActiveTab('conta')}
              style={{
                width: '36px',
                height: '36px',
                borderRadius: '50%',
                overflow: 'hidden',
                cursor: 'pointer',
                border: '2px solid var(--slate-border)',
                background: 'var(--slate-light)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            >
              {profileAvatar ? (
                <img src={profileAvatar} alt="Perfil" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
              ) : (
                <span style={{ fontSize: '1.1rem' }}>👤</span>
              )}
            </div>

            {/* Centro: Título do App */}
            <h1 style={{ fontSize: '1.25rem', fontWeight: '800', margin: 0, color: 'var(--text-primary)' }}>
              1Convite
            </h1>


{/* Direita: Diamante Premium */}
            <div 
              onClick={() => setActiveTab('conta')}
              style={{
                width: '36px',
                height: '36px',
                borderRadius: '50%',
                background: 'var(--orange-light)',
                border: '1px solid var(--orange)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                cursor: 'pointer',
                fontSize: '1.1rem'
              }}
              title="Assinatura Premium"
            >
              💎
            </div>
          </>
        ) : (
          <>
            {/* Esquerda: Botão Voltar */}
            <button 
              onClick={() => {
                if (window.speechSynthesis) window.speechSynthesis.cancel();
                setIsNarrating(false);
                setMeditationPlaying(false);
                if (meditationIntervalRef.current) clearInterval(meditationIntervalRef.current);
                if (activeTab === 'sabado' && activeSabadoBlock !== 'menu') {
                  setActiveSabadoBlock('menu');
                  // Parar meditação se estiver tocando
                  setAudioPlaying(false);
                  if (audioRef.current) audioRef.current.pause();
                } else {
                  setActiveTab('dashboard');
                  setBibleAudioPlaying(false);
                  if (bibleAudioRef.current) bibleAudioRef.current.pause();
                }
              }}
              style={{
                background: 'transparent',
                border: 'none',
                fontSize: '1.4rem',
                color: 'var(--text-primary)',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                width: '36px',
                height: '36px',
                borderRadius: '50%'
              }}
              className="back-btn"
            >
              ←
            </button>

            {/* Centro: Título ou Dropdown da Bíblia */}
            <div style={{ flex: 1, display: 'flex', justifyContent: 'center' }}>
              {activeTab === 'biblia' ? (
                <button
                  className="bible-select-btn"
                  onClick={() => setBibleViewMode(bibleViewMode === 'select-book' ? 'reading' : 'select-book')}
                  style={{ border: 'none', background: 'transparent', padding: 0, fontSize: '1.05rem', fontWeight: '700', color: 'var(--text-primary)', cursor: 'pointer' }}
                >
                  <span>{bibleSelectedBook.livro_nome} {bibleSelectedChapter} ▼</span>
                </button>
              ) : (
                <h2 style={{ fontSize: '1.1rem', fontWeight: '700', margin: 0, color: 'var(--text-primary)', textAlign: 'center' }}>
                  {activeTab === 'sabado' && (
                    activeSabadoBlock === 'menu' ? 'Desafio do Dia' :
                    activeSabadoBlock === 'reflexao' ? 'Reflexão do Dia' :
                    activeSabadoBlock === 'meditacao' ? 'Oração Guiada' :
                    activeSabadoBlock === 'descanso' ? 'O Botão do Descanso' :
                    'Trilha de Conhecimento'
                  )}
                  {activeTab === 'chat' && 'Conselheiro IA'}
                  {activeTab === 'contatos' && 'Conexões & Contatos'}
                  {activeTab === 'conta' && 'Minha Conta'}
                  {activeTab === 'criar-card' && 'Studio de Cards'}
                  {activeTab === 'arcade' && 'Jogos'}
                  {activeTab === 'trail' && 'Trilha do Reino'}
                </h2>
              )}
            </div>

            {/* Direita: Controles especiais da Bíblia */}
            {activeTab === 'biblia' ? (
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <button
                  onClick={() => setBibleShowAudioPlayer(!bibleShowAudioPlayer)}
                  style={{
                    background: bibleShowAudioPlayer ? 'var(--orange-light)' : 'transparent',
                    border: bibleShowAudioPlayer ? '1px solid var(--orange)' : 'none',
                    fontSize: '1.1rem',
                    color: bibleShowAudioPlayer ? 'var(--orange)' : 'var(--text-primary)',
                    cursor: 'pointer',
                    width: '32px',
                    height: '32px',
                    borderRadius: '50%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    transition: 'all 0.2s'
                  }}
                  title="Ouvir Áudio do Capítulo"
                >
                  🎵
                </button>
                <button
                  style={{
                    background: 'transparent',
                    border: 'none',
                    fontSize: '1.1rem',
                    color: 'var(--text-primary)',
                    cursor: 'pointer',
                    width: '32px',
                    height: '32px',
                    borderRadius: '50%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}
                  title="Opções"
                >
                  ⋮
                </button>
              </div>
            ) : (
              <div style={{ width: '36px' }}></div>
            )}
          </>
        )}
      </header>

      {/* ── MODAIS BÍBLIA ─────────────────────── */}
      {commentModalOpen && bibleSelectedVerse && (
        <div className="bible-modal-overlay" style={{ zIndex: 999 }}>
          <div className="bible-modal" style={{
            backgroundColor: darkMode ? '#1c1c1e' : '#ffffff',
            borderRadius: '24px',
            padding: '24px',
            width: '90%',
            maxWidth: '400px',
            boxShadow: '0 10px 25px rgba(0,0,0,0.2)',
            display: 'flex',
            flexDirection: 'column',
            gap: '16px',
            boxSizing: 'border-box'
          }}>
            <h3 style={{ margin: 0, fontSize: '1.1rem', color: 'var(--text-primary)' }}>
              📝 {bibleSelectedBook.livro_nome} {bibleSelectedChapter}:{bibleSelectedVerse.versiculo}
            </h3>
            
            <textarea
              className="input-field"
              rows="4"
              placeholder="Digite seu comentário ou anotação pessoal..."
              value={commentText}
              onChange={e => setCommentText(e.target.value)}
              style={{
                width: '100%',
                padding: '12px',
                borderRadius: '12px',
                border: '1px solid var(--slate-border)',
                backgroundColor: darkMode ? '#2c2c2e' : '#ffffff',
                color: 'var(--text-primary)',
                resize: 'none',
                boxSizing: 'border-box'
              }}
            />
            
            <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
              <button
                className="btn-secondary"
                style={{ padding: '10px 20px', borderRadius: '12px' }}
                onClick={() => setCommentModalOpen(false)}
              >
                FECHAR
              </button>
              <button
                className="btn-primary"
                style={{ padding: '10px 20px', borderRadius: '12px' }}
                onClick={() => {
                  const key = `${bibleSelectedBook.livro_abrev}-${bibleSelectedChapter}-${bibleSelectedVerse.versiculo}`;
                  const newComments = { ...bibleComments };
                  if (commentText.trim() === '') {
                    delete newComments[key];
                  } else {
                    newComments[key] = commentText;
                  }
                  setBibleComments(newComments);
                  localStorage.setItem('bible-comments', JSON.stringify(newComments));
                  setCommentModalOpen(false);
                }}
              >
                SALVAR
              </button>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'biblia' && bibleViewMode === 'select-book' && (() => {
        // Calcula progresso geral AT e NT
        const atBooks = bibleBooks.filter((_, i) => i < 39);
        const ntBooks = bibleBooks.filter((_, i) => i >= 39);
        const chaptersPerBook = { gn:50,ex:40,lv:27,nm:36,dt:34,js:24,jz:21,rt:4,'1sm':31,'2sm':24,'1rs':22,'2rs':25,'1cr':29,'2cr':36,ed:10,ne:13,et:10,jó:42,sl:150,pv:31,ec:12,ct:8,is:66,jr:52,lm:5,ez:48,dn:12,os:14,jl:3,am:9,ob:1,jn:4,mq:7,na:3,hc:3,sf:3,ag:2,zc:14,ml:4,mt:28,mc:16,lc:24,jo:21,at:28,rm:16,'1co':16,'2co':13,gl:6,ef:6,fp:4,cl:4,'1ts':5,'2ts':3,'1tm':6,'2tm':4,tt:3,fm:1,hb:13,tg:5,'1pe':5,'2pe':3,'1jo':5,'2jo':1,'3jo':1,jd:1,ap:22 };
        const calcTotal = (books) => books.reduce((acc, bk) => {
          const total = chaptersPerBook[bk.livro_abrev] || bk.capitulos || 0;
          const prog = calcBookProgress(bk.livro_abrev, total);
          return { read: acc.read + prog.readCount, total: acc.total + total };
        }, { read: 0, total: 0 });
        const atStats = calcTotal(atBooks);
        const ntStats = calcTotal(ntBooks);
        const atPercent = atStats.total > 0 ? Math.round((atStats.read / atStats.total) * 100) : 0;
        const ntPercent = ntStats.total > 0 ? Math.round((ntStats.read / ntStats.total) * 100) : 0;
        const totalPercent = (atStats.total + ntStats.total) > 0 ? Math.round(((atStats.read + ntStats.read) / (atStats.total + ntStats.total)) * 100) : 0;

        return (
          <div className="bible-modal-overlay">
            <div className="bible-modal-header">
              <h3 style={{ margin: 0, fontSize: '1.05rem' }}>Selecione o Livro</h3>
              <button className="btn-secondary" style={{ padding: '6px 14px', fontSize: '0.9rem' }} onClick={() => setBibleViewMode('reading')}>✕</button>
            </div>
            <div className="bible-modal-content">

              {/* Painel Resumo Global */}
              <div style={{ margin: '0 0 16px 0', padding: '14px 16px', background: 'rgba(255,255,255,0.04)', borderRadius: '14px', border: '1px solid rgba(255,255,255,0.08)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                  <span style={{ fontSize: '0.8rem', fontWeight: '700', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Progresso Total da Bíblia</span>
                  <span style={{ fontSize: '1.1rem', fontWeight: '800', color: 'var(--orange)' }}>{totalPercent}%</span>
                </div>
                <div style={{ height: '6px', background: 'rgba(255,255,255,0.08)', borderRadius: '99px', overflow: 'hidden', marginBottom: '12px' }}>
                  <div style={{ height: '100%', width: `${totalPercent}%`, background: 'linear-gradient(90deg, var(--orange), #f97316)', borderRadius: '99px', transition: 'width 0.5s ease' }} />
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                  <div style={{ textAlign: 'center', padding: '8px', background: 'rgba(255,255,255,0.03)', borderRadius: '10px' }}>
                    <div style={{ fontSize: '1rem', fontWeight: '700', color: '#f59e0b' }}>{atPercent}%</div>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>Antigo Testamento</div>
                    <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginTop: '2px' }}>{atStats.read}/{atStats.total} capítulos</div>
                  </div>
                  <div style={{ textAlign: 'center', padding: '8px', background: 'rgba(255,255,255,0.03)', borderRadius: '10px' }}>
                    <div style={{ fontSize: '1rem', fontWeight: '700', color: '#3b82f6' }}>{ntPercent}%</div>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>Novo Testamento</div>
                    <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginTop: '2px' }}>{ntStats.read}/{ntStats.total} capítulos</div>
                  </div>
                </div>
              </div>

              <div className="bible-testament-title">Antigo Testamento</div>
              {atBooks.map((bk, idx) => {
                const total = chaptersPerBook[bk.livro_abrev] || bk.capitulos || 0;
                const prog = calcBookProgress(bk.livro_abrev, total);
                const isDone = prog.percent === 100;
                return (
                  <div key={idx} style={{ padding: '10px 14px', marginBottom: '2px', cursor: 'pointer', borderRadius: '10px', background: isDone ? 'rgba(34,197,94,0.08)' : 'transparent', border: isDone ? '1px solid rgba(34,197,94,0.2)' : '1px solid transparent', transition: 'all 0.2s' }}
                    onClick={() => { setBibleSelectedBook(bk); setBibleViewMode('select-chapter'); }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '5px' }}>
                      <span style={{ fontSize: '0.92rem', fontWeight: isDone ? '700' : '500', color: isDone ? '#22c55e' : 'var(--text-primary)' }}>{bk.livro_nome}</span>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        {isDone && <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#22c55e" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>}
                        <span style={{ fontSize: '0.72rem', fontWeight: '700', color: isDone ? '#22c55e' : 'var(--text-muted)' }}>{prog.percent}%</span>
                      </div>
                    </div>
                    <div style={{ height: '3px', background: 'rgba(255,255,255,0.07)', borderRadius: '99px', overflow: 'hidden' }}>
                      <div style={{ height: '100%', width: `${prog.percent}%`, background: isDone ? '#22c55e' : 'var(--orange)', borderRadius: '99px', transition: 'width 0.4s ease' }} />
                    </div>
                  </div>
                );
              })}

              <div className="bible-testament-title" style={{ marginTop: '8px' }}>Novo Testamento</div>
              {ntBooks.map((bk, idx) => {
                const total = chaptersPerBook[bk.livro_abrev] || bk.capitulos || 0;
                const prog = calcBookProgress(bk.livro_abrev, total);
                const isDone = prog.percent === 100;
                return (
                  <div key={idx} style={{ padding: '10px 14px', marginBottom: '2px', cursor: 'pointer', borderRadius: '10px', background: isDone ? 'rgba(34,197,94,0.08)' : 'transparent', border: isDone ? '1px solid rgba(34,197,94,0.2)' : '1px solid transparent', transition: 'all 0.2s' }}
                    onClick={() => { setBibleSelectedBook(bk); setBibleViewMode('select-chapter'); }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '5px' }}>
                      <span style={{ fontSize: '0.92rem', fontWeight: isDone ? '700' : '500', color: isDone ? '#22c55e' : 'var(--text-primary)' }}>{bk.livro_nome}</span>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        {isDone && <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#22c55e" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>}
                        <span style={{ fontSize: '0.72rem', fontWeight: '700', color: isDone ? '#22c55e' : 'var(--text-muted)' }}>{prog.percent}%</span>
                      </div>
                    </div>
                    <div style={{ height: '3px', background: 'rgba(255,255,255,0.07)', borderRadius: '99px', overflow: 'hidden' }}>
                      <div style={{ height: '100%', width: `${prog.percent}%`, background: isDone ? '#22c55e' : '#3b82f6', borderRadius: '99px', transition: 'width 0.4s ease' }} />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        );
      })()}

      {activeTab === 'biblia' && bibleViewMode === 'select-chapter' && (() => {
        const chaptersPerBook = { gn:50,ex:40,lv:27,nm:36,dt:34,js:24,jz:21,rt:4,'1sm':31,'2sm':24,'1rs':22,'2rs':25,'1cr':29,'2cr':36,ed:10,ne:13,et:10,jó:42,sl:150,pv:31,ec:12,ct:8,is:66,jr:52,lm:5,ez:48,dn:12,os:14,jl:3,am:9,ob:1,jn:4,mq:7,na:3,hc:3,sf:3,ag:2,zc:14,ml:4,mt:28,mc:16,lc:24,jo:21,at:28,rm:16,'1co':16,'2co':13,gl:6,ef:6,fp:4,cl:4,'1ts':5,'2ts':3,'1tm':6,'2tm':4,tt:3,fm:1,hb:13,tg:5,'1pe':5,'2pe':3,'1jo':5,'2jo':1,'3jo':1,jd:1,ap:22 };
        const total = chaptersPerBook[bibleSelectedBook.livro_abrev] || bibleChaptersCount;
        const prog = calcBookProgress(bibleSelectedBook.livro_abrev, total);
        return (
          <div className="bible-modal-overlay">
            <div className="bible-modal-header">
              <button className="btn-secondary" style={{ padding: '6px 14px', fontSize: '0.85rem' }} onClick={() => setBibleViewMode('select-book')}>← Livros</button>
              <h3 style={{ margin: 0, fontSize: '1.05rem' }}>{bibleSelectedBook.livro_nome}</h3>
              <div style={{ width: '72px' }} />
            </div>
            <div className="bible-modal-content">
              {/* Barra de progresso do livro */}
              <div style={{ padding: '8px 4px 16px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                  <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>{prog.readCount} de {total} capítulos lidos</span>
                  <span style={{ fontSize: '0.78rem', fontWeight: '700', color: prog.percent === 100 ? '#22c55e' : 'var(--orange)' }}>{prog.percent}%</span>
                </div>
                <div style={{ height: '5px', background: 'rgba(255,255,255,0.07)', borderRadius: '99px', overflow: 'hidden' }}>
                  <div style={{ height: '100%', width: `${prog.percent}%`, background: prog.percent === 100 ? '#22c55e' : 'var(--orange)', borderRadius: '99px', transition: 'width 0.4s ease' }} />
                </div>
              </div>
              <div className="bible-chapter-grid">
                {Array.from({ length: bibleChaptersCount }).map((_, i) => {
                  const chNum = i + 1;
                  const read = isChapterRead(bibleSelectedBook.livro_abrev, chNum);
                  return (
                    <div key={i}
                      onClick={() => { setBibleSelectedChapter(chNum); setBibleViewMode('reading'); }}
                      style={{
                        position: 'relative',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        width: '44px', height: '44px', borderRadius: '10px',
                        cursor: 'pointer', fontSize: '0.9rem', fontWeight: '600',
                        background: read ? 'rgba(34,197,94,0.15)' : 'rgba(255,255,255,0.05)',
                        border: read ? '1.5px solid rgba(34,197,94,0.4)' : '1px solid rgba(255,255,255,0.06)',
                        color: read ? '#22c55e' : 'var(--text-primary)',
                        transition: 'all 0.2s'
                      }}
                    >
                      {chNum}
                      {read && (
                        <div style={{ position: 'absolute', top: '2px', right: '2px', width: '10px', height: '10px', borderRadius: '50%', background: '#22c55e', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                          <svg width="7" height="7" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        );
      })()}

      {/* ── MODAL DICIONÁRIO TEOLÓGICO ────────── */}
      {selectedDicionarioTermo && (
        <div className="dict-modal">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <h3 style={{ color: 'var(--orange)', fontSize: '1.1rem', textTransform: 'capitalize' }}>📚 {selectedDicionarioTermo.termo}</h3>
            <button className="btn-secondary" style={{ padding: '4px 10px', fontSize: '0.8rem' }} onClick={() => setSelectedDicionarioTermo(null)}>✕ Fechar</button>
          </div>
          <p style={{ fontSize: '0.92rem', lineHeight: '1.6', color: 'var(--text-primary)' }}>{selectedDicionarioTermo.significado}</p>
        </div>
      )}

      {/* ── MAIN ──────────────────────────────── */}
      <main className="main-content">

        {/* ════════════ TELA DASHBOARD PRINCIPAL ════════════ */}
        {activeTab === 'dashboard' && (
          <div className="page-enter animate-fade-in" style={{ padding: '16px', boxSizing: 'border-box' }}>
            
            {/* Carrossel no topo */}
            <div style={{ marginBottom: '20px' }}>
              <div className="carousel-container">
                <div className="carousel-wrapper" style={{ transform: `translateX(-${carouselIndex * 100}%)` }}>
                  {carouselImages.map((src, idx) => (
                    <img key={idx} src={src} alt={`Banner ${idx + 1}`} className="carousel-image" style={{ height: '140px' }} />
                  ))}
                </div>
                <div className="carousel-dots">
                  {carouselImages.map((_, idx) => (
                    <button key={idx} className={`carousel-dot${idx === carouselIndex ? ' active' : ''}`} onClick={() => setCarouselIndex(idx)} />
                  ))}
                </div>
              </div>
            </div>

            {/* Grid de 2 Colunas */}
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(2, 1fr)',
              gap: '16px',
              paddingBottom: '20px'
            }}>
              {[
                { 
                  id: 'biblia', 
                  label: 'Bíblia Sagrada', 
                  icon: (
                    <svg width="32" height="32" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                    </svg>
                  )
                },
                { 
                  id: 'sabado', 
                  label: 'Desafio do Dia', 
                  icon: (
                    <svg width="32" height="32" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364-6.364l-.707.707M6.343 17.657l-.707.707m12.728 0l-.707-.707M6.343 6.343l-.707-.707M12 8a4 4 0 100 8 4 4 0 000-8z" />
                    </svg>
                  )
                },
                { 
                  id: 'chat', 
                  label: 'Conselheiro IA', 
                  icon: (
                    <svg width="32" height="32" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                    </svg>
                  )
                },
                { 
                  id: 'contatos', 
                  label: 'Conexões & Contatos', 
                  icon: (
                    <svg width="32" height="32" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                  )
                },
                { 
                  id: 'conta', 
                  label: 'Aparência & Configs', 
                  icon: (
                    <svg width="32" height="32" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                      <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                  )
                },
                { 
                  id: 'criar-card', 
                  label: 'Criar Card', 
                  icon: (
                    <svg width="32" height="32" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
                      <rect x="3" y="3" width="18" height="18" rx="3" ry="3" strokeLinecap="round" strokeLinejoin="round" />
                      <circle cx="8.5" cy="8.5" r="1.5" />
                      <polyline points="21 15 16 10 5 21" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                  )
                },
                { 
                  id: 'arcade', 
                  label: 'Jogos', 
                  icon: (
                    <svg width="32" height="32" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                      <path strokeLinecap="round" strokeLinejoin="round" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  )
                },
                { 
                  id: 'lojinha', 
                  label: 'Lojinha 🛒', 
                  icon: (
                    <ChaminhaCoin size={36} />
                  )
                },
                { 
                  id: 'trail', 
                  label: 'Trilha do Reino', 
                  icon: (
                    <svg width="32" height="32" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M17.657 18.657A8 8 0 016.343 7.343S7 9 9 10c0-2 .5-5 2.986-7C14 5 16.09 5.777 17.656 7.343A7.975 7.975 0 0120 13a7.975 7.975 0 01-2.343 5.657z" />
                      <path strokeLinecap="round" strokeLinejoin="round" d="M9.879 16.121A3 3 0 1012.015 11L11 14H9c0 .768.293 1.536.879 2.121z" />
                    </svg>
                  )
                }
              ].map(card => (
                <div
                  key={card.id}
                  onClick={() => {
                    setActiveTab(card.id);
                    if (card.id === 'biblia') {
                      setBibleViewMode('reading');
                      setBibleSelectedVerse(null);
                    }
                    if (card.id === 'sabado') {
                      setActiveSabadoBlock('menu');
                    }
                    if (card.id === 'criar-card') {
                      setCardSelectedText('');
                      setCardCategory('bomdia');
                    }

                  }}
                  className="dashboard-card"
                >
                  <div className="dashboard-card-icon">
                    {card.icon}
                  </div>
                  <span className="dashboard-card-label">
                    {card.label}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ════════════ ABA DESAFIO DO DIA ════════════ */}
        {activeTab === 'sabado' && (
          <div className="page-enter" style={{ padding: '16px', boxSizing: 'border-box' }}>
            
            {/* MENU PRINCIPAL DO DESAFIO */}
            {activeSabadoBlock === 'menu' && (
              <div className="animate-fade-in" style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(2, 1fr)',
                gap: '16px',
                paddingBottom: '20px'
              }}>
                {[
                  {
                    id: 'reflexao',
                    title: 'Reflexão do Dia',
                    desc: 'Código verbal e reflexão.',
                    icon: (
                      <svg width="32" height="32" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364-6.364l-.707.707M6.343 17.657l-.707.707m12.728 0l-.707-.707M6.343 6.343l-.707-.707M12 8a4 4 0 100 8 4 4 0 000-8z" />
                      </svg>
                    )
                  },
                  {
                    id: 'meditacao',
                    title: 'Oração Guiada',
                    desc: 'Alinhamento e ação de graças.',
                    icon: (
                      <svg width="32" height="32" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3" />
                      </svg>
                    )
                  },
                  {
                    id: 'descanso',
                    title: 'Botão do Descanso',
                    desc: 'Pausa de respiração.',
                    icon: (
                      <svg width="32" height="32" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 10.5C7.8 10.5 10.5 7.8 10.5 4.5M19.5 10.5C16.2 10.5 13.5 7.8 13.5 4.5M4.5 13.5C7.8 13.5 10.5 16.2 10.5 19.5M19.5 13.5C16.2 13.5 13.5 16.2 13.5 19.5" />
                      </svg>
                    )
                  },
                  {
                    id: 'trilha',
                    title: 'Trilha Temática',
                    desc: 'Estudo ativo de 30 dias.',
                    icon: (
                      <svg width="32" height="32" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                      </svg>
                    )
                  }
                ].map(block => (
                  <div
                    key={block.id}
                    onClick={() => setActiveSabadoBlock(block.id)}
                    className="dashboard-card"
                    style={{
                      backgroundColor: 'var(--white)',
                      border: '1px solid var(--slate-border)',
                      borderRadius: '20px',
                      padding: '24px 16px',
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: '12px',
                      cursor: 'pointer',
                      transition: 'all 0.25s ease-in-out',
                      boxShadow: 'var(--shadow-sm)'
                    }}
                  >
                    <div className="dashboard-card-icon" style={{ color: 'var(--orange)' }}>
                      {block.icon}
                    </div>
                    <span className="dashboard-card-label" style={{ fontSize: '0.9rem', fontWeight: '700', color: 'var(--text-primary)', textAlign: 'center' }}>
                      {block.title}
                    </span>
                    <span style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', textAlign: 'center', opacity: 0.8 }}>
                      {block.desc}
                    </span>
                  </div>
                ))}
              </div>
            )}

            {/* 1. REFLEXÃO DO DIA */}
            {activeSabadoBlock === 'reflexao' && codigoDia && (
              <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                
                {codigoDia.dia_id > 7 && !codigoDia.texto_reflexao.includes('📖 HISTÓRIA CRISTÃ REAL') ? (
                  <div className="glass-panel" style={{ padding: '24px', borderRadius: '20px', textAlign: 'center' }}>
                    <div style={{ fontSize: '3rem', marginBottom: '12px' }}>🤖</div>
                    <h3 style={{ margin: '0 0 8px 0', fontSize: '1.15rem', color: 'var(--text-primary)', fontWeight: '700' }}>Personalização por Inteligência Artificial</h3>
                    <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', lineHeight: '1.5', marginBottom: '20px' }}>
                      Você chegou ao Dia {codigoDia.dia_id}! Para este dia em diante, o aplicativo pode criar uma reflexão exclusiva contendo uma história cristã real histórica personalizada a custo zero de API.
                    </p>

                    {chatGptUser ? (
                      aiGenerating ? (
                        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '12px', padding: '12px' }}>
                          <div className="spinner" style={{ width: '32px', height: '32px', border: '3px solid var(--orange-light)', borderTopColor: 'var(--orange)', borderRadius: '50%', animation: 'spin 1s linear infinite' }}></div>
                          <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Escrevendo devocional com IA e buscando histórias cristãs reais na história...</span>
                        </div>
                      ) : (
                        <button className="btn-primary" style={{ width: '100%', padding: '14px' }} onClick={generateDailyReflectionWithAI}>
                          ✨ Enriquecer Devocional com IA
                        </button>
                      )
                    ) : (
                      <div style={{ background: 'var(--slate-bg)', padding: '16px', borderRadius: '16px', border: '1px dashed var(--slate-border)' }}>
                        <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', margin: '0 0 12px 0' }}>
                          Conecte sua própria conta do ChatGPT gratuita nas Configurações para liberar o gerador inteligente.
                        </p>
                        <button className="btn-secondary" style={{ width: '100%', padding: '10px 16px', fontSize: '0.85rem' }} onClick={() => setActiveTab('conta')}>
                          ⚙️ Conectar ChatGPT nas Configurações
                        </button>
                      </div>
                    )}
                  </div>
                ) : (
                  <>
                    <div className="page-hero hero-sabado" style={{ borderRadius: '24px' }}>
                      <div className="hero-orb" style={{ width: 160, height: 160, top: -40, right: -40 }} />
                      <div className="hero-content">
                        <div className={`pedagio-badge ${codigoDia.pilar_origem === 'PROPÓSITO_M2414' ? 'badge-proposito' : 'badge-recompensa'}`} style={{ background: 'rgba(255,255,255,0.20)', color: '#fff', border: '1px solid rgba(255,255,255,0.35)', marginBottom: '12px' }}>
                          {codigoDia.pilar_origem === 'PROPÓSITO_M2414' ? 'Mateus 24:14' : 'Apocalipse 3:21'} — Código de Hoje
                        </div>
                        <div className="hero-title" style={{ fontSize: '1.25rem', lineHeight: '1.4' }}>"{codigoDia.codigo_verbal}"</div>
                        <div className="hero-sub">{codigoDia.versiculo_chave}</div>
                      </div>
                    </div>

                    <div className="glass-panel orange-card" style={{ padding: '24px 20px', borderRadius: '20px', position: 'relative' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                        <h3 style={{ margin: 0, color: '#C2550A', fontSize: '1rem' }}>💡 Reflexão & Inspiração</h3>
                        <button
                          onClick={speakReflection}
                          style={{
                            padding: '8px 16px',
                            borderRadius: '12px',
                            border: '1.5px solid var(--orange)',
                            background: isNarrating ? 'var(--orange)' : 'var(--orange-light)',
                            color: isNarrating ? '#ffffff' : 'var(--orange-dark)',
                            fontSize: '0.82rem',
                            fontWeight: 'bold',
                            cursor: 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '6px',
                            transition: 'all 0.2s',
                            boxShadow: 'var(--shadow-sm)'
                          }}
                        >
                          {isNarrating ? '⏹️ Parar' : '🔊 Ouvir'}
                        </button>
                      </div>
                      <p style={{ lineHeight: '1.8', fontSize: '1rem', color: 'var(--text-primary)', margin: 0, whiteSpace: 'pre-wrap', textAlign: 'left' }}>
                        {codigoDia.texto_reflexao}
                      </p>
                    </div>
                  </>
                )}
              </div>
            )}

            {/* 2. MEDITAÇÃO GUIADA */}
            {activeSabadoBlock === 'meditacao' && codigoDia && (
              <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <audio ref={ambientAudioRef} />
                
                <div style={{
                  background: 'linear-gradient(135deg, #0f0a1c 0%, #05030a 100%)',
                  padding: '24px',
                  borderRadius: '24px',
                  border: '1px solid rgba(139, 92, 246, 0.15)',
                  boxShadow: 'var(--shadow-lg)',
                  textAlign: 'center',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  position: 'relative',
                  overflow: 'hidden'
                }}>
                  {/* Fundo decorativo animado em Gradiente Líquido */}
                  <div style={{
                    position: 'absolute',
                    top: '-50%',
                    left: '-50%',
                    width: '200%',
                    height: '200%',
                    background: 'radial-gradient(circle, rgba(139, 92, 246, 0.08) 0%, transparent 60%)',
                    animation: meditationPlaying ? 'pulse 8s infinite ease-in-out' : 'none',
                    pointerEvents: 'none',
                    zIndex: 0
                  }} />

                  {/* Ilustração Personalizada Premium do Calm/Headspace */}
                  <div style={{
                    width: '100%',
                    maxWidth: '220px',
                    aspectRatio: '1',
                    borderRadius: '20px',
                    overflow: 'hidden',
                    marginBottom: '20px',
                    boxShadow: '0 8px 30px rgba(0,0,0,0.5)',
                    border: '1px solid rgba(255,255,255,0.08)',
                    position: 'relative',
                    zIndex: 1
                  }}>
                    <video 
                      ref={meditationVideoRef}
                      src="/Imagens/oraçãoguiada.mp4" 
                      loop 
                      muted 
                      playsInline
                      style={{
                        width: '100%',
                        height: '100%',
                        objectFit: 'cover',
                        filter: meditationPlaying ? 'none' : 'grayscale(30%) contrast(90%)',
                        transition: 'filter 0.5s ease'
                      }}
                    />
                  </div>

                  <h3 style={{ margin: '0 0 4px 0', fontSize: '1.25rem', fontWeight: '800', color: '#f8fafc', zIndex: 1 }}>
                    Oração do Dia {codigoDia.dia_id}
                  </h3>
                  <span style={{ fontSize: '0.8rem', color: '#a78bfa', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '20px', zIndex: 1 }}>
                    {codigoDia.pilar_origem === 'PROPÓSITO_M2414' ? 'Pilar Mateus 24:14' : 'Pilar Apocalipse 3:21'}
                  </span>

                  {/* Controle de Progresso */}
                  <div style={{ width: '100%', marginBottom: '20px', zIndex: 1 }}>
                    <div 
                      style={{ 
                        height: '6px', 
                        width: '100%', 
                        background: 'rgba(255, 255, 255, 0.1)', 
                        borderRadius: '3px',
                        position: 'relative'
                      }}
                    >
                      <div 
                        style={{ 
                          height: '100%', 
                          width: `${(meditationCurrentTime / (meditationDuration || 1)) * 100}%`, 
                          background: 'linear-gradient(90deg, #c084fc 0%, #8b5cf6 100%)', 
                          borderRadius: '3px',
                          transition: 'width 0.25s linear'
                        }} 
                      />
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem', color: '#9ca3af', marginTop: '6px' }}>
                      <span>{formatTime(meditationCurrentTime)}</span>
                      <span>{formatTime(meditationDuration)}</span>
                    </div>
                  </div>

                  {/* Painel de Controles Flexíveis */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: '20px', marginBottom: '24px', zIndex: 1 }}>
                    {/* Botão de Transcrição */}
                    <button 
                      onClick={() => setShowMeditationLyrics(!showMeditationLyrics)}
                      style={{
                        background: showMeditationLyrics ? 'rgba(139, 92, 246, 0.2)' : 'rgba(255,255,255,0.04)',
                        border: '1px solid rgba(255,255,255,0.08)',
                        padding: '8px 14px',
                        borderRadius: '20px',
                        color: showMeditationLyrics ? '#c084fc' : '#e2e8f0',
                        fontSize: '0.8rem',
                        fontWeight: 'bold',
                        cursor: 'pointer',
                        transition: 'all 0.2s'
                      }}
                    >
                      📖 Roteiro
                    </button>

                    {/* Botão Play/Pause Principal */}
                    <button 
                      onClick={toggleMeditationTTS} 
                      style={{
                        width: '54px',
                        height: '54px',
                        borderRadius: '50%',
                        background: '#8b5cf6',
                        border: 'none',
                        color: '#ffffff',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        cursor: 'pointer',
                        boxShadow: '0 4px 20px rgba(139, 92, 246, 0.4)',
                        transition: 'transform 0.2s',
                        transform: 'scale(1)',
                      }}
                      onMouseDown={(e) => e.currentTarget.style.transform = 'scale(0.95)'}
                      onMouseUp={(e) => e.currentTarget.style.transform = 'scale(1)'}
                    >
                      {meditationPlaying ? (
                        <svg width="22" height="22" fill="currentColor" viewBox="0 0 16 16">
                          <path d="M5.5 3.5A1.5 1.5 0 0 1 7 5v6a1.5 1.5 0 0 1-3 0V5a1.5 1.5 0 0 1 1.5-1.5zm5 0A1.5 1.5 0 0 1 12 5v6a1.5 1.5 0 0 1-3 0V5a1.5 1.5 0 0 1 1.5-1.5z" />
                        </svg>
                      ) : (
                        <svg width="22" height="22" fill="currentColor" viewBox="0 0 16 16" style={{ marginLeft: '3px' }}>
                          <path d="m11.596 8.697-6.363 3.692c-.54.313-1.233-.066-1.233-.697V4.308c0-.63.692-1.01 1.233-.696l6.363 3.692a.802.802 0 0 1 0 1.393z" />
                        </svg>
                      )}
                    </button>

                    {/* Velocidade da Narração */}
                    <button 
                      onClick={() => {
                        const rates = [0.75, 0.82, 0.95, 1.05];
                        const nextIndex = (rates.indexOf(narrationRate) + 1) % rates.length;
                        setNarrationRate(rates[nextIndex]);
                        if (meditationPlaying) {
                          // Reinicia com a nova velocidade
                          window.speechSynthesis.cancel();
                          setMeditationPlaying(false);
                          setTimeout(() => toggleMeditationTTS(), 100);
                        }
                      }}
                      style={{
                        background: 'rgba(255,255,255,0.04)',
                        border: '1px solid rgba(255,255,255,0.08)',
                        padding: '8px 12px',
                        borderRadius: '20px',
                        color: '#cbd5e1',
                        fontSize: '0.8rem',
                        fontWeight: 'bold',
                        cursor: 'pointer'
                      }}
                    >
                      ⏱️ {narrationRate === 0.75 ? 'Lento' : narrationRate === 0.82 ? 'Relax' : narrationRate === 0.95 ? 'Médio' : 'Rápido'}
                    </button>
                  </div>

                  {/* Som Ambiente de Fundo (Padrão Calm) */}
                  <div style={{
                    width: '100%',
                    background: 'rgba(255,255,255,0.03)',
                    border: '1px solid rgba(255,255,255,0.05)',
                    padding: '16px',
                    borderRadius: '16px',
                    boxSizing: 'border-box',
                    textAlign: 'left',
                    zIndex: 1,
                    marginBottom: '16px'
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                      <span style={{ fontSize: '0.82rem', color: '#9ca3af', fontWeight: 'bold' }}>🍃 Paisagem Sonora</span>
                      <span style={{ fontSize: '0.78rem', color: '#8b5cf6', fontWeight: 'bold' }}>
                        {activeAmbient === 'none' ? 'Silêncio' : activeAmbient === 'chuva' ? 'Chuva' : activeAmbient === 'mar' ? 'Ondas' : 'Piano'}
                      </span>
                    </div>

                    {/* Chips do Seletor */}
                    <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginBottom: '12px' }}>
                      {ambientTracks.map(track => (
                        <button
                          key={track.id}
                          onClick={() => setActiveAmbient(track.id)}
                          style={{
                            background: activeAmbient === track.id ? '#8b5cf6' : 'rgba(255,255,255,0.05)',
                            border: '1px solid rgba(255,255,255,0.1)',
                            borderRadius: '12px',
                            padding: '6px 12px',
                            color: activeAmbient === track.id ? '#ffffff' : '#9ca3af',
                            fontSize: '0.75rem',
                            fontWeight: '600',
                            cursor: 'pointer',
                            transition: 'all 0.2s'
                          }}
                        >
                          {track.label}
                        </button>
                      ))}
                    </div>

                    {/* Volume de Fundo */}
                    {activeAmbient !== 'none' && (
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
                        <span style={{ fontSize: '0.72rem', color: '#9ca3af' }}>🔊 Vol. Fundo:</span>
                        <input 
                          type="range" 
                          min="0.05" 
                          max="0.4" 
                          step="0.05"
                          value={ambientVolume}
                          onChange={(e) => setAmbientVolume(parseFloat(e.target.value))}
                          style={{ flex: 1, accentColor: '#8b5cf6', cursor: 'pointer' }}
                        />
                      </div>
                    )}


                  </div>

                  {/* Mensagem de Conclusão da Oração de Ação de Graças */}
                  {meditationCompleted && (
                    <div 
                      className="animate-fade-in" 
                      style={{
                        marginTop: '4px',
                        marginBottom: '16px',
                        background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.25), rgba(0, 240, 143, 0.15))',
                        border: '1px solid rgba(0, 240, 143, 0.3)',
                        padding: '18px',
                        borderRadius: '16px',
                        color: '#f8fafc',
                        zIndex: 1,
                        boxShadow: '0 4px 15px rgba(0, 240, 143, 0.1)',
                        textAlign: 'center',
                        width: '100%',
                        boxSizing: 'border-box'
                      }}
                    >
                      <div style={{ fontSize: '1.5rem', marginBottom: '8px' }}>🍞🕊️</div>
                      <p style={{ margin: 0, fontSize: '0.9rem', fontWeight: '700', lineHeight: '1.5', color: '#00f08f' }}>
                        Sua oração de ação de graças foi feita.
                      </p>
                      <p style={{ margin: '6px 0 0 0', fontSize: '0.85rem', color: '#cbd5e1', lineHeight: '1.4' }}>
                        Agora, qual é o seu pão a ser compartilhado hoje? Quem você vai abençoar com o seu "1Convite" agora?
                      </p>
                    </div>
                  )}

                  {/* Transcrição da Meditação */}
                  {showMeditationLyrics && (
                    <div className="animate-fade-in" style={{
                      padding: '16px',
                      background: 'rgba(255, 255, 255, 0.02)',
                      border: '1px solid rgba(255, 255, 255, 0.05)',
                      borderRadius: '16px',
                      width: '100%',
                      textAlign: 'left',
                      boxSizing: 'border-box',
                      zIndex: 1
                    }}>
                      <p style={{
                        fontSize: '0.9rem',
                        color: '#cbd5e1',
                        lineHeight: '1.75',
                        margin: 0,
                        whiteSpace: 'pre-wrap',
                        maxHeight: '150px',
                        overflowY: 'auto'
                      }}>
                        {codigoDia.texto_meditacao}
                      </p>
                    </div>
                  )}

                  {/* Fallback de IA no dia > 7 */}
                  {codigoDia.dia_id > 7 && !codigoDia.texto_reflexao.includes('📖 HISTÓRIA CRISTÃ REAL') && (
                    <div style={{
                      marginTop: '16px',
                      background: 'rgba(239, 68, 68, 0.1)',
                      border: '1px dashed rgba(239, 68, 68, 0.25)',
                      padding: '12px',
                      borderRadius: '14px',
                      fontSize: '0.8rem',
                      color: '#fca5a5',
                      lineHeight: '1.4',
                      zIndex: 1
                    }}>
                      ⚠️ Esta oração está usando um roteiro genérico. Vá na aba "Reflexão do Dia" e clique em "Enriquecer com IA" para gerar um roteiro de oração completo e personalizado com história real.
                    </div>
                  )}

                </div>
              </div>
            )}
            {/* 3. O BOTÃO DO DESCANSO */}
            {activeSabadoBlock === 'descanso' && (
              <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <div className="glass-panel" style={{ padding: '28px 24px', borderRadius: '24px', textAlign: 'center', background: 'linear-gradient(135deg, var(--white) 0%, var(--slate-bg) 100%)' }}>
                  
                  {!isBreathing ? (
                    <div className="animate-fade-in" style={{ marginBottom: '24px' }}>
                      <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', lineHeight: '1.6', margin: '0 0 20px 0' }}>
                        Desacelere os batimentos cardíacos, relaxe a mente e traga seu foco de volta para o Aqui e Agora.
                      </p>
                      
                      {/* Seleção de Técnica */}
                      <div style={{ textAlign: 'left', marginBottom: '20px' }}>
                        <label style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.5px', display: 'block', marginBottom: '8px' }}>
                          🧘 Técnica de Respiração
                        </label>
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '6px' }}>
                          {[
                            { id: 'simple', label: 'Micro-Pausa', desc: '4-4-4' },
                            { id: 'box', label: 'Box Breath', desc: '4-4-4-4' },
                            { id: 'relax', label: 'Relaxar', desc: '4-7-8' }
                          ].map(t => (
                            <button
                              key={t.id}
                              onClick={() => setBreathTechnique(t.id)}
                              style={{
                                padding: '10px 6px',
                                borderRadius: '12px',
                                border: '1.5px solid',
                                borderColor: breathTechnique === t.id ? 'var(--orange)' : 'var(--slate-border)',
                                background: breathTechnique === t.id ? 'var(--orange-light)' : 'var(--white)',
                                color: breathTechnique === t.id ? 'var(--orange-dark)' : 'var(--text-primary)',
                                cursor: 'pointer',
                                fontSize: '0.8rem',
                                fontWeight: '700',
                                display: 'flex',
                                flexDirection: 'column',
                                alignItems: 'center',
                                transition: 'all 0.2s'
                              }}
                            >
                              <span>{t.label}</span>
                              <span style={{ fontSize: '0.65rem', fontWeight: '600', opacity: 0.7, marginTop: '2px' }}>{t.desc}</span>
                            </button>
                          ))}
                        </div>
                      </div>

                      {/* Seleção de Ciclos */}
                      <div style={{ textAlign: 'left', marginBottom: '24px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                          <label style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                            🔄 Duração do Exercício
                          </label>
                          <span style={{ fontSize: '0.82rem', color: 'var(--orange-dark)', fontWeight: '700' }}>
                            {breathRounds} Ciclos
                          </span>
                        </div>
                        <input
                          type="range"
                          min="3"
                          max="15"
                          step="1"
                          value={breathRounds}
                          onChange={(e) => setBreathRounds(parseInt(e.target.value, 10))}
                          style={{ width: '100%', accentColor: 'var(--orange)', cursor: 'pointer' }}
                        />
                      </div>
                    </div>
                  ) : (
                    <div className="animate-fade-in" style={{ marginBottom: '20px' }}>
                      <span className="section-chip" style={{ background: 'var(--orange-light)', color: 'var(--orange-dark)', fontWeight: 'bold', padding: '6px 14px', borderRadius: '20px', fontSize: '0.8rem' }}>
                        Ciclo {currentRound} de {breathRounds}
                      </span>
                    </div>
                  )}

                  {/* Círculo Interativo com Animação */}
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', margin: '30px 0' }}>
                    <div
                      className={`breath-circle ${breathClass}`}
                      onClick={!isBreathing ? iniciarRespiracao : undefined}
                      style={{
                        border: '2px solid',
                        borderColor: isBreathing ? (breathClass === 'inhaling' ? '#2563EB' : breathClass === 'holding' ? 'var(--orange)' : breathClass === 'holding-empty' ? '#8b5cf6' : 'rgba(0, 240, 143, 0.4)') : 'var(--orange-light)',
                        boxShadow: isBreathing ? '0 10px 30px rgba(0,0,0,0.08)' : 'var(--shadow-md)',
                        background: !isBreathing ? 'var(--white)' : undefined,
                        cursor: isBreathing ? 'default' : 'pointer',
                        width: '160px',
                        height: '160px',
                        borderRadius: '50%',
                        display: 'flex',
                        flexDirection: 'column',
                        justifyContent: 'center',
                        alignItems: 'center',
                        transition: 'all 3s ease-in-out',
                        position: 'relative'
                      }}
                    >
                      {/* Pulse Ring Decorativo */}
                      {isBreathing && (
                        <div style={{
                          position: 'absolute',
                          top: 0, left: 0, right: 0, bottom: 0,
                          borderRadius: '50%',
                          border: '2px solid',
                          borderColor: breathClass === 'inhaling' ? 'rgba(37, 99, 235, 0.4)' : 'rgba(249, 115, 22, 0.4)',
                          animation: 'pulse 2s infinite ease-in-out',
                          pointerEvents: 'none'
                        }} />
                      )}

                      <span style={{ fontSize: '1rem', fontWeight: '800', color: 'var(--text-primary)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                        {breathState}
                      </span>
                      {isBreathing && (
                        <span style={{ fontSize: '1.8rem', fontWeight: '900', color: 'var(--orange-dark)', marginTop: '4px' }}>
                          {breathTimer}s
                        </span>
                      )}
                    </div>

                    {isBreathing && (
                      <button
                        onClick={pararRespiracao}
                        className="btn-secondary"
                        style={{
                          marginTop: '24px',
                          padding: '10px 24px',
                          borderRadius: '20px',
                          fontSize: '0.85rem',
                          fontWeight: '700',
                          border: '1.5px solid var(--slate-border)',
                          cursor: 'pointer',
                          background: 'var(--white)',
                          color: 'var(--text-secondary)',
                          boxShadow: 'var(--shadow-sm)'
                        }}
                      >
                        ⏹️ Parar Exercício
                      </button>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* 4. TRILHA DE CONHECIMENTO */}
            {activeSabadoBlock === 'trilha' && (
              <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                
                {/* Trilha Ativa */}
                {trilhaAtiva ? (
                  <div className="trilha-active-panel" style={{ margin: 0, padding: 0, borderRadius: '20px', overflow: 'hidden' }}>
                    {/* Imagem de Topo Temática da Trilha */}
                    <div style={{
                      width: '100%',
                      height: '140px',
                      position: 'relative'
                    }}>
                      <img 
                        src={
                          trilhaAtiva.tema === 'Ansiedade' ? 'https://images.unsplash.com/photo-1506126613408-eca07ce68773?auto=format&fit=crop&w=600&q=80' :
                          trilhaAtiva.tema === 'Família' ? 'https://images.unsplash.com/photo-1511895426328-dc8714191300?auto=format&fit=crop&w=600&q=80' :
                          trilhaAtiva.tema === 'Finanças' ? 'https://images.unsplash.com/photo-1559526324-4b87b5e36e44?auto=format&fit=crop&w=600&q=80' :
                          'https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=600&q=80'
                        } 
                        alt={trilhaAtiva.tema}
                        style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                      />
                      <div style={{
                        position: 'absolute',
                        bottom: 0, left: 0, right: 0,
                        background: 'linear-gradient(to top, rgba(15, 10, 28, 0.9), transparent)',
                        padding: '16px 20px',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'flex-end'
                      }}>
                        <div>
                          <span style={{ fontSize: '0.7rem', color: '#a78bfa', fontWeight: 'bold', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Jornada Ativa</span>
                          <h4 style={{ margin: '2px 0 0 0', fontSize: '1.2rem', fontWeight: '800', color: '#ffffff' }}>Trilha de {trilhaAtiva.tema}</h4>
                        </div>
                        <span style={{ fontSize: '0.8rem', fontWeight: '800', background: 'rgba(255,255,255,0.15)', padding: '4px 10px', borderRadius: '12px', color: '#fff', backdropFilter: 'blur(4px)' }}>
                          Dia {trilhaAtiva.dia_progresso}/30
                        </span>
                      </div>
                    </div>

                    <div style={{ padding: '20px' }}>
                      {trilhaAtiva.conteudo && (
                        <>
                          <h3 style={{ fontSize: '1.15rem', marginBottom: '8px', fontWeight: 'bold' }}>{trilhaAtiva.conteudo.titulo}</h3>
                          <p style={{ fontStyle: 'italic', marginBottom: '12px', fontSize: '0.9rem', color: 'var(--text-secondary)', lineHeight: '1.5' }}>
                            "{trilhaAtiva.conteudo.versiculo}"
                          </p>
                          <p style={{ marginBottom: '16px', fontSize: '0.95rem', lineHeight: '1.6' }}>
                            {trilhaAtiva.conteudo.reflexao}
                          </p>
                          <div className="glass-panel orange-card" style={{ padding: '14px', marginBottom: '18px', borderRadius: '14px' }}>
                            <strong style={{ fontSize: '0.85rem', color: 'var(--orange-dark)', display: 'block', marginBottom: '4px' }}>🎯 AÇÃO PRÁTICA DO DIA:</strong>
                            <p style={{ fontSize: '0.9rem', color: 'var(--text-primary)', margin: 0 }}>{trilhaAtiva.conteudo.acao_pratica}</p>
                          </div>
                        </>
                      )}
                      <div style={{ display: 'flex', gap: '10px' }}>
                        <button className="btn-primary" style={{ padding: '12px', borderRadius: '12px', flex: 2 }} onClick={completarDiaTrilha}>
                          ✓ Concluir Ação de Hoje
                        </button>
                        <button className="btn-secondary" style={{ padding: '12px', borderRadius: '12px', flex: 1, background: '#FEE2E2', color: '#EF4444', border: '1px solid #FCA5A5' }} onClick={cancelarTrilha}>
                          Abandonar
                        </button>
                      </div>
                    </div>
                  </div>
                ) : (
                  listaTrilhas.length > 0 && (
                    <div className="glass-panel" style={{ padding: '20px', borderRadius: '20px' }}>
                      <h3 style={{ marginBottom: '6px', fontSize: '1.15rem', fontWeight: '800' }}>🌱 Trilhas de Crescimento (30 Dias)</h3>
                      <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '20px', lineHeight: '1.4' }}>
                        Escolha uma trilha e receba uma porção diária de sabedoria teológica com ações práticas por 30 dias.
                      </p>
                      
                      <div style={{ 
                        display: 'grid', 
                        gridTemplateColumns: 'repeat(2, 1fr)', 
                        gap: '16px' 
                      }} className="lp-grid-mobile-single">
                        {listaTrilhas.map(tema => {
                          let detail = { desc: '', icon: null, color: 'rgba(255,255,255,0.05)', border: 'rgba(255,255,255,0.1)' };
                          
                          if (tema === 'Ansiedade') {
                            detail = { 
                              desc: 'Controle o estresse em uma jornada de paz.', 
                              icon: (
                                <svg width="24" height="24" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
                                  <path strokeLinecap="round" strokeLinejoin="round" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                                </svg>
                              ), 
                              color: 'rgba(14, 165, 233, 0.1)', 
                              border: 'rgba(14, 165, 233, 0.2)' 
                            };
                          } else if (tema === 'Família') {
                            detail = { 
                              desc: 'Harmonia, perdão e laços fortes no seu lar.', 
                              icon: (
                                <svg width="24" height="24" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
                                  <path strokeLinecap="round" strokeLinejoin="round" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
                                </svg>
                              ), 
                              color: 'rgba(244, 63, 94, 0.1)', 
                              border: 'rgba(244, 63, 94, 0.2)' 
                            };
                          } else if (tema === 'Finanças') {
                            detail = { 
                              desc: 'Princípios bíblicos de mordomia.', 
                              icon: (
                                <svg width="24" height="24" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
                                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                              ), 
                              color: 'rgba(16, 185, 129, 0.1)', 
                              border: 'rgba(16, 185, 129, 0.2)' 
                            };
                          } else if (tema === 'Propósito') {
                            detail = { 
                              desc: 'Descubra e ative seus dons para governar.', 
                              icon: (
                                <svg width="24" height="24" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
                                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                                </svg>
                              ), 
                              color: 'rgba(139, 92, 246, 0.1)', 
                              border: 'rgba(139, 92, 246, 0.2)' 
                            };
                          }
                          
                          return (
                            <div 
                              key={tema} 
                              className="dashboard-card animate-fade-in" 
                              onClick={() => iniciarTrilha(tema)} 
                              style={{ 
                                padding: '20px 16px', 
                                borderRadius: '18px', 
                                display: 'flex', 
                                flexDirection: 'column',
                                gap: '12px',
                                alignItems: 'flex-start', 
                                cursor: 'pointer', 
                                border: `1.5px solid ${detail.border}`,
                                backgroundColor: 'var(--white)',
                                transition: 'all 0.2s ease',
                                textAlign: 'left',
                                boxSizing: 'border-box'
                              }}
                            >
                              <div style={{ 
                                color: tema === 'Ansiedade' ? '#0ea5e9' : tema === 'Família' ? '#f43f5e' : tema === 'Finanças' ? '#10b981' : '#8b5cf6',
                                background: detail.color,
                                padding: '10px',
                                borderRadius: '12px',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center'
                              }}>
                                {detail.icon}
                              </div>
                              <div style={{ flex: 1 }}>
                                <strong style={{ fontSize: '0.95rem', color: 'var(--text-primary)', display: 'block' }}>
                                  Trilha de {tema}
                                </strong>
                                <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '4px', lineHeight: '1.4' }}>
                                  {detail.desc}
                                </div>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )
                )}

              </div>
            )}

          </div>
        )}

        {/* ════════════ ABA BÍBLIA ════════════ */}
        {activeTab === 'biblia' && bibleViewMode === 'reading' && (
          <div className="bible-reader page-enter">
            {/* Hero da Bíblia */}
            <div className="page-hero hero-biblia" style={{ paddingBottom: '44px' }}>
              <div className="hero-orb" style={{ width: 220, height: 220, top: -50, right: -60, background: 'rgba(249,115,22,0.20)' }} />
              <div className="hero-content">
                <div className="hero-label">📖 Bíblia Sagrada</div>
                <div className="hero-title">{bibleSelectedBook.livro_nome}</div>
                <div className="hero-sub">Capítulo {bibleSelectedChapter}</div>
              </div>
            </div>

            {/* Player de Áudio da Bíblia */}
            {bibleShowAudioPlayer && bibleAudioUrl && (
              <div style={{ padding: '0 20px 10px 20px', marginTop: '-18px', position: 'relative', zIndex: 5 }}>
                <div className="player-container" style={{ padding: '12px 16px', flexDirection: 'row', gap: '12px', background: darkMode ? 'rgba(24, 24, 27, 0.85)' : 'rgba(255, 255, 255, 0.7)', border: darkMode ? '1px solid rgba(255,255,255,0.06)' : 'none' }}>
                  <audio
                    ref={bibleAudioRef}
                    src={bibleAudioUrl}
                    onTimeUpdate={onBibleAudioTimeUpdate}
                    onLoadedMetadata={onBibleAudioLoadedMetadata}
                    onEnded={() => {
                      // Auto-marcar capítulo como lido ao terminar o áudio
                      markChapterAsRead(bibleSelectedBook.livro_abrev, bibleSelectedChapter);
                      setBibleAudioPlaying(false);
                    }}
                  />
                  <button className="play-btn" style={{ width: '40px', height: '40px', flexShrink: 0 }} onClick={() => setBibleAudioPlaying(!bibleAudioPlaying)}>
                    {bibleAudioPlaying
                      ? <svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M5.5 3.5A1.5 1.5 0 0 1 7 5v6a1.5 1.5 0 0 1-3 0V5a1.5 1.5 0 0 1 1.5-1.5zm5 0A1.5 1.5 0 0 1 12 5v6a1.5 1.5 0 0 1-3 0V5a1.5 1.5 0 0 1 1.5-1.5z" /></svg>
                      : <svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16" style={{ marginLeft: '2px' }}><path d="m11.596 8.697-6.363 3.692c-.54.313-1.233-.066-1.233-.697V4.308c0-.63.692-1.01 1.233-.696l6.363 3.692a.802.802 0 0 1 0 1.393z" /></svg>
                    }
                  </button>
                  <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    <div className="progress-bar-container" onClick={handleBibleAudioProgressBarClick} style={{ height: '4px' }}>
                      <div className="progress-bar-fill" style={{ width: `${(bibleAudioCurrentTime / (bibleAudioDuration || 1)) * 100}%` }} />
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: darkMode ? '#a1a1aa' : '#78716C' }}>
                      <span>{formatTime(bibleAudioCurrentTime)}</span>
                      <span>{formatTime(bibleAudioDuration)}</span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {bibleResults.length > 0 ? (
              <div style={{ padding: '16px 20px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                  <h3>Resultados ({bibleResults.length})</h3>
                  <button className="btn-secondary" style={{ padding: '5px 12px', fontSize: '0.82rem' }} onClick={() => { setBibleResults([]); setBibleSearchQuery(''); }}>Limpar</button>
                </div>
                {bibleResults.map((v, idx) => (
                  <div key={idx} className="glass-panel" style={{ position: 'relative', paddingTop: '42px' }}>
                    <span className="section-chip" style={{ position: 'absolute', top: '14px', right: '14px', fontSize: '0.62rem' }}>
                      {v.livro_nome} {v.capitulo}:{v.versiculo}
                    </span>
                    <p style={{ fontStyle: 'italic', lineHeight: '1.80', fontSize: '1rem' }}>"{formatVerseText(v.texto)}"</p>
                    <div style={{ display: 'flex', gap: '10px', marginTop: '14px' }}>
                      <button className="btn-secondary" style={{ flex: 1, padding: '10px', fontSize: '0.85rem' }} onClick={() => copyToClipboard(`"${v.texto}" - ${v.livro_nome} ${v.capitulo}:${v.versiculo}`)}>
                        📋 Copiar
                      </button>
                      <a
                        href={`https://wa.me/?text=${encodeURIComponent(`*"${v.texto}"*\n_${v.livro_nome} ${v.capitulo}:${v.versiculo}_\n\n👉 *1Convite:* https://1convite.com.br`)}`}
                        target="_blank" rel="noopener noreferrer"
                        className="btn-primary"
                        style={{ flex: 2, padding: '10px', textAlign: 'center', textDecoration: 'none' }}
                      >
                        📲 Enviar
                      </a>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <>
                {bibleLoading ? (
                  <div style={{ textAlign: 'center', padding: '60px 20px' }}>
                    <div style={{ fontSize: '2rem', marginBottom: '12px', animation: 'spin 1.5s linear infinite', display: 'inline-block' }}>📖</div>
                    <p style={{ color: '#A8A29E' }}>Carregando versículos...</p>
                  </div>
                ) : (
                  <div style={{ padding: '16px 20px 0' }}>
                    {bibleVerses.map(v => {
                      const key = `${bibleSelectedBook.livro_abrev}-${bibleSelectedChapter}-${v.versiculo}`;
                      const highlightColor = bibleHighlights[key];
                      const comment = bibleComments[key];
                      return (
                        <div
                          key={v.id || v.versiculo}
                          className={`bible-verse-row${(bibleSelectedVerse?.id === v.id || bibleSelectedVerse?.versiculo === v.versiculo) ? ' selected' : ''}`}
                          onClick={() => setBibleSelectedVerse((bibleSelectedVerse?.id === v.id || bibleSelectedVerse?.versiculo === v.versiculo) ? null : v)}
                          style={{
                            backgroundColor: highlightColor || undefined,
                            borderRadius: highlightColor ? '8px' : '0',
                            padding: highlightColor ? '8px 10px' : '6px 0',
                            margin: highlightColor ? '4px 0' : '0',
                            transition: 'all 0.2s',
                            display: 'flex',
                            gap: '10px',
                            alignItems: 'flex-start'
                          }}
                        >
                          <span className="bible-verse-num" style={{ flexShrink: 0, fontWeight: '700', fontSize: '0.85rem', color: 'var(--orange)' }}>
                            {v.versiculo}
                          </span>
                          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '4px' }}>
                            <span style={{ lineHeight: '1.75', fontSize: '1.02rem', color: 'var(--text-primary)' }}>
                              {formatVerseText(v.texto)}
                            </span>
                            {comment && (
                              <div style={{
                                padding: '6px 10px',
                                background: darkMode ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.03)',
                                borderRadius: '8px',
                                borderLeft: '3px solid var(--orange)',
                                fontSize: '0.82rem',
                                color: 'var(--text-secondary)',
                                marginTop: '4px',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '6px'
                              }}>
                                <span>💬</span>
                                <span>{comment}</span>
                              </div>
                            )}
                          </div>
                        </div>
                      );
                    })}
                    {/* Botão de Próximo Capítulo com Recompensa */}
                    {bibleVerses.length > 0 && (
                      <button
                        onClick={() => {
                          setUserCoins(prev => {
                            const val = prev + 10;
                            localStorage.setItem('app-coins', val);
                            return val;
                          });
                          setRewardPopup({ amount: 10, title: 'Capítulo Concluído!', message: 'Amém! Você meditou na Palavra e seu coração foi aquecido.' });
                          setBibleSelectedChapter(prev => prev + 1);
                        }}
                        style={{
                          width: '100%',
                          marginTop: '20px',
                          padding: '16px',
                          background: 'rgba(245,158,11,0.1)',
                          border: '1px dashed var(--orange)',
                          color: 'var(--orange)',
                          borderRadius: '16px',
                          fontSize: '1.1rem',
                          fontWeight: 'bold',
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          gap: '8px'
                        }}
                      >
                        Concluir Capítulo (+10 🔥)
                      </button>
                    )}
                  </div>
                )}
 
                {!bibleSelectedVerse && (
                  <div style={{ padding: '28px 20px', marginTop: '20px', borderTop: darkMode ? '1px solid rgba(255,255,255,0.08)' : '1px solid rgba(0,0,0,0.06)' }}>
                    <form onSubmit={searchBible} style={{ display: 'flex', gap: '10px', marginBottom: '12px' }}>
                      <input type="text" className="input-field" placeholder="Buscar versículo (ex: amor, fé)..." value={bibleSearchQuery} onChange={e => setBibleSearchQuery(e.target.value)} />
                      <button type="submit" className="btn-secondary" disabled={bibleLoading} style={{ flexShrink: 0, padding: '0 16px' }}>🔍</button>
                    </form>
                    {bibleError && <p style={{ color: '#ef4444', fontSize: '0.85rem', marginBottom: '12px' }}>{bibleError}</p>}
                    <button className="btn-orange-outline" onClick={getRandomVerse}>🎲 Versículo Aleatório</button>
                  </div>
                )}
              </>
            )}
 
            {/* Menu flutuante de versículo selecionado */}
            {bibleSelectedVerse && bibleResults.length === 0 && (
              <div 
                className="bible-action-menu-panel animate-slide-up"
                style={{
                  position: 'fixed',
                  bottom: 0,
                  left: 0,
                  right: 0,
                  backgroundColor: darkMode ? '#1c1c1e' : '#ffffff',
                  borderTop: '1px solid var(--slate-border)',
                  boxShadow: '0 -4px 20px rgba(0,0,0,0.15)',
                  padding: '16px 20px',
                  zIndex: 100,
                  borderTopLeftRadius: '24px',
                  borderTopRightRadius: '24px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '16px',
                  boxSizing: 'border-box'
                }}
              >
                {/* Fileira 1: Botões de Ação */}
                <div style={{ display: 'flex', gap: '8px', width: '100%' }}>
                  <button 
                    onClick={() => {
                      if (navigator.share) {
                        navigator.share({
                          title: 'Versículo Bíblico',
                          text: `"${bibleSelectedVerse.texto}" - ${bibleSelectedBook.livro_nome} ${bibleSelectedChapter}:${bibleSelectedVerse.versiculo}`
                        });
                      } else {
                        copyToClipboard(`"${bibleSelectedVerse.texto}" - ${bibleSelectedBook.livro_nome} ${bibleSelectedChapter}:${bibleSelectedVerse.versiculo}`);
                      }
                    }}
                    style={{ flex: 1, padding: '10px 4px', fontSize: '0.82rem', fontWeight: 'bold', borderRadius: '12px', border: '1px solid var(--slate-border)', background: 'transparent', color: 'var(--text-primary)', cursor: 'pointer' }}
                  >
                    Compartilhar
                  </button>
                  <button 
                    onClick={() => {
                      alert('Link de compartilhamento copiado!');
                      copyToClipboard(`"${bibleSelectedVerse.texto}" - ${bibleSelectedBook.livro_nome} ${bibleSelectedChapter}:${bibleSelectedVerse.versiculo}`);
                    }}
                    style={{ flex: 1, padding: '10px 4px', fontSize: '0.82rem', fontWeight: 'bold', borderRadius: '12px', border: '1px solid var(--slate-border)', background: 'transparent', color: 'var(--text-primary)', cursor: 'pointer' }}
                  >
                    Imagem
                  </button>
                  <button 
                    onClick={() => {
                      setCommentText(bibleComments[`${bibleSelectedBook.livro_abrev}-${bibleSelectedChapter}-${bibleSelectedVerse.versiculo}`] || '');
                      setCommentModalOpen(true);
                    }}
                    style={{ flex: 1, padding: '10px 4px', fontSize: '0.82rem', fontWeight: 'bold', borderRadius: '12px', border: '1px solid var(--slate-border)', background: 'transparent', color: 'var(--text-primary)', cursor: 'pointer' }}
                  >
                    Comentário
                  </button>
                  <button 
                    onClick={() => {
                      copyToClipboard(`"${bibleSelectedVerse.texto}" - ${bibleSelectedBook.livro_nome} ${bibleSelectedChapter}:${bibleSelectedVerse.versiculo}`);
                    }}
                    style={{ flex: 1, padding: '10px 4px', fontSize: '0.82rem', fontWeight: 'bold', borderRadius: '12px', border: '1px solid var(--slate-border)', background: 'transparent', color: 'var(--text-primary)', cursor: 'pointer' }}
                  >
                    Copiar
                  </button>
                </div>

                {/* Fileira 2: Círculos Coloridos de Destaque */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '8px', padding: '0 8px' }}>
                  {[
                    { id: 'clear', color: 'transparent', dotColor: '#2c2c2e', label: '✕', isClear: true },
                    { id: 'blue', color: 'rgba(59, 130, 246, 0.22)', dotColor: '#3b82f6' },
                    { id: 'purple', color: 'rgba(139, 92, 246, 0.22)', dotColor: '#8b5cf6' },
                    { id: 'gray', color: 'rgba(107, 114, 128, 0.22)', dotColor: '#6b7280' },
                    { id: 'teal', color: 'rgba(20, 184, 166, 0.22)', dotColor: '#14b8a6' },
                    { id: 'green', color: 'rgba(34, 197, 94, 0.22)', dotColor: '#22c55e' },
                    { id: 'orange', color: 'rgba(249, 115, 22, 0.22)', dotColor: '#f97316' }
                  ].map(colorOpt => {
                    const key = `${bibleSelectedBook.livro_abrev}-${bibleSelectedChapter}-${bibleSelectedVerse.versiculo}`;
                    const currentHighlight = bibleHighlights[key];
                    const isSelected = colorOpt.isClear ? !currentHighlight : currentHighlight === colorOpt.color;

                    return (
                      <button
                        key={colorOpt.id}
                        onClick={() => {
                          const newHighlights = { ...bibleHighlights };
                          if (colorOpt.isClear) {
                            delete newHighlights[key];
                          } else {
                            newHighlights[key] = colorOpt.color;
                          }
                          setBibleHighlights(newHighlights);
                          localStorage.setItem('bible-highlights', JSON.stringify(newHighlights));
                        }}
                        style={{
                          width: '36px',
                          height: '36px',
                          borderRadius: '50%',
                          backgroundColor: colorOpt.isClear ? (darkMode ? '#2c2c2e' : '#f4f4f5') : colorOpt.dotColor,
                          border: isSelected ? '3px solid var(--orange)' : '2px solid transparent',
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          color: colorOpt.isClear ? '#ef4444' : '#ffffff',
                          fontWeight: 'bold',
                          fontSize: '1rem',
                          padding: 0,
                          boxSizing: 'border-box'
                        }}
                      >
                        {colorOpt.isClear && '✕'}
                      </button>
                    );
                  })}
                </div>

                {/* Salvar */}
                <button
                  className="btn-primary"
                  style={{ width: '100%', padding: '12px', borderRadius: '12px', fontSize: '0.95rem' }}
                  onClick={() => setBibleSelectedVerse(null)}
                >
                  Salvar
                </button>
              </div>
            )}

            {/* Botão Flutuante Seletor de Livros (≡) */}
            <button
              onClick={() => setBibleViewMode(bibleViewMode === 'select-book' ? 'reading' : 'select-book')}
              style={{
                position: 'fixed',
                bottom: bibleSelectedVerse ? '215px' : '88px',
                right: '24px',
                width: '52px',
                height: '52px',
                borderRadius: '50%',
                backgroundColor: '#3b82f6',
                color: '#ffffff',
                border: 'none',
                boxShadow: '0 4px 12px rgba(59, 130, 246, 0.4)',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '1.4rem',
                zIndex: 90,
                transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)'
              }}
              title="Lista de Livros/Capítulos"
            >
              ☰
            </button>

            {/* Botão Flutuante: Marcar Capítulo como Lido */}
            {!bibleSelectedVerse && (() => {
              const alreadyRead = isChapterRead(bibleSelectedBook.livro_abrev, bibleSelectedChapter);
              return (
                <button
                  onClick={() => markChapterAsRead(bibleSelectedBook.livro_abrev, bibleSelectedChapter, !alreadyRead)}
                  style={{
                    position: 'fixed',
                    bottom: '24px',
                    right: '24px',
                    height: '52px',
                    padding: '0 18px',
                    borderRadius: '26px',
                    backgroundColor: alreadyRead ? 'rgba(34,197,94,0.15)' : '#22c55e',
                    color: alreadyRead ? '#22c55e' : '#fff',
                    border: alreadyRead ? '1.5px solid rgba(34,197,94,0.4)' : 'none',
                    boxShadow: alreadyRead ? 'none' : '0 4px 14px rgba(34,197,94,0.4)',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '7px',
                    fontSize: '0.85rem',
                    fontWeight: '700',
                    zIndex: 90,
                    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)'
                  }}
                  title={alreadyRead ? 'Capítulo já lido – clique para desmarcar' : 'Marcar capítulo como lido'}
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="20 6 9 17 4 12"></polyline>
                  </svg>
                  {alreadyRead ? 'Lido' : 'Marcar como Lido'}
                </button>
              );
            })()}
          </div>
        )}

        {/* ════════════ ABA CONTATOS ════════════ */}
        {activeTab === 'contatos' && (
          <div className="page-enter">
            {/* Hero */}
            <div className="page-hero hero-contatos">
              <div className="hero-orb" style={{ width: 200, height: 200, top: -40, left: -40, background: 'rgba(249,115,22,0.15)' }} />
              <div className="hero-content">
                <div className="hero-label">👥 Mateus 24:14</div>
                <div className="hero-title">Meus Próximos</div>
                <div className="hero-sub">{contatos.length} {contatos.length === 1 ? 'pessoa' : 'pessoas'} no seu círculo de influência</div>
              </div>
            </div>

            <div className="page-content" style={{ paddingTop: '4px' }}>
              {/* Alertas */}
              {contatos.filter(verificarAlerta48h).map(c => (
                <div key={`alert-${c.id}`} className="glass-panel" style={{ padding: '14px 18px', marginBottom: '12px', borderColor: 'rgba(239,68,68,0.25)', background: 'rgba(254,242,242,0.80)' }}>
                  <p style={{ color: '#dc2626', fontWeight: '600', fontSize: '0.9rem' }}>
                    ⚠️ Alerta: Você tem notado <strong>{c.nome}</strong> ({c.relacao})? Já se passaram 48h.
                  </p>
                </div>
              ))}

              {/* Botão adicionar */}
              <button
                className={showAddContato ? 'btn-secondary' : 'btn-primary'}
                style={{ marginBottom: '16px' }}
                onClick={() => setShowAddContato(!showAddContato)}
              >
                {showAddContato ? '✕ Fechar Formulário' : '+ Adicionar Próximo'}
              </button>

              {/* Form */}
              {showAddContato && (
                <form onSubmit={handleAddContato} className="glass-panel" style={{ marginBottom: '16px' }}>
                  <h3 style={{ marginBottom: '16px' }}>🆕 Novo Contato</h3>
                  {contatoErro && <p style={{ color: '#ef4444', fontSize: '0.85rem', marginBottom: '12px' }}>{contatoErro}</p>}
                  <div className="input-group">
                    <label>Nome Completo</label>
                    <input type="text" className="input-field" value={newNome} onChange={e => setNewNome(e.target.value)} placeholder="Ex: Maria da Silva" required />
                  </div>
                  <div className="input-group">
                    <label>Relação / Vínculo</label>
                    <input type="text" className="input-field" value={newRelacao} onChange={e => setNewRelacao(e.target.value)} placeholder="Ex: Família, Vizinho, Trabalho" required />
                  </div>
                  <div className="input-group">
                    <label className="checkbox-label">
                      <input type="checkbox" checked={newPrioritario} onChange={e => setNewPrioritario(e.target.checked)} />
                      <span>Contato Prioritário <span style={{ color: '#A8A29E', fontSize: '0.85rem' }}>(alerta a cada 48h)</span></span>
                    </label>
                  </div>
                  <button type="submit" className="btn-primary" style={{ marginTop: '4px' }}>✅ Salvar no Reino</button>
                </form>
              )}

              {/* Lista */}
              {contatos.length === 0 && !showAddContato ? (
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '16px', margin: '24px 0', padding: '0 12px' }}>
                  <ChaminhaVideo size={80} style={{ flexShrink: 0 }} />
                  <div className="glass-panel animate-fade-in" style={{
                    padding: '12px 18px',
                    borderRadius: '16px',
                    fontSize: '0.9rem',
                    color: 'var(--text-secondary)',
                    border: '1px solid rgba(255, 255, 255, 0.08)',
                    position: 'relative',
                    maxWidth: '360px',
                    background: 'rgba(255, 255, 255, 0.02)',
                    textAlign: 'left'
                  }}>
                    <div style={{
                      position: 'absolute', top: '50%', left: '-6px', transform: 'translateY(-50%) rotate(45deg)',
                      width: '10px', height: '10px', background: 'var(--bg-app)', borderLeft: '1px solid rgba(255, 255, 255, 0.08)',
                      borderBottom: '1px solid rgba(255, 255, 255, 0.08)', zIndex: 1
                    }} />
                    🔥 <strong>Chaminha:</strong> "Nenhum Próximo adicionado ainda! Adicione pessoas do seu convívio diário aqui para começar a notá-las e interagir com intenção!"
                  </div>
                </div>
              ) : (
                contatos.map(c => (
                  <div key={c.id} className="glass-panel" style={{ marginBottom: '12px', padding: '18px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                      <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                        <div style={{ width: 44, height: 44, borderRadius: '50%', background: 'linear-gradient(135deg, #F97316, #FB923C)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: '800', fontSize: '1.1rem', color: '#fff', flexShrink: 0 }}>
                          {c.nome.charAt(0).toUpperCase()}
                        </div>
                        <div>
                          <div style={{ fontWeight: '700', fontSize: '1rem', display: 'flex', alignItems: 'center', gap: '6px' }}>
                            {c.nome}
                            {c.prioritario && <span className="section-chip" style={{ fontSize: '0.60rem' }}>⭐ Prior.</span>}
                          </div>
                          <div style={{ fontSize: '0.82rem', color: '#78716C', marginTop: '2px' }}>{c.relacao}</div>
                        </div>
                      </div>
                      <button onClick={() => deletarContato(c.id)} style={{ background: 'none', border: 'none', color: '#EF4444', cursor: 'pointer', fontSize: '1.1rem', padding: '4px' }}>🗑</button>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '10px', borderTop: '1px solid rgba(0,0,0,0.05)' }}>
                      <span style={{ fontSize: '0.75rem', color: '#A8A29E' }}>
                        Último: {c.ultimo_convite_timestamp > 0 ? new Date(c.ultimo_convite_timestamp).toLocaleDateString('pt-BR') : 'Nunca'}
                      </span>
                      <div style={{ display: 'flex', gap: '6px' }}>
                        <button className="btn-secondary" style={{ padding: '6px 10px', fontSize: '0.78rem', borderRadius: '10px' }} onClick={() => registrarAcao(c.id, 'mensagem')}>💬</button>
                        <button className="btn-secondary" style={{ padding: '6px 10px', fontSize: '0.78rem', borderRadius: '10px' }} onClick={() => registrarAcao(c.id, 'cafe')}>☕</button>
                        <button className="btn-secondary" style={{ padding: '6px 10px', fontSize: '0.78rem', borderRadius: '10px' }} onClick={() => registrarAcao(c.id, 'casa_igreja')}>🏠</button>
                      </div>
                    </div>
                  </div>
                ))
              )}

              {user?.status_plano === 'FREE' && contatos.length >= 3 && (
                <div className="glass-panel orange-card" style={{ textAlign: 'center', marginTop: '8px' }}>
                  <p style={{ marginBottom: '14px', fontWeight: '500' }}>Limite de 3 contatos no plano gratuito.</p>
                  <button className="btn-primary" onClick={() => setActiveTab('upgrade')}>🔓 Desbloquear Ilimitados</button>
                </div>
              )}
            </div>
          </div>
        )}

        {/* ════════════ ABA HISTÓRICO ════════════ */}
        {activeTab === 'historico' && (
          <div className="page-enter">
            <div className="page-hero hero-contatos" style={{ background: 'linear-gradient(135deg, #475569 0%, #64748B 100%)' }}>
              <div className="hero-content">
                <div className="hero-label">📚 Jornada</div>
                <div className="hero-title">Histórico de Códigos</div>
                <div className="hero-sub">Mural de revelações da sua caminhada</div>
              </div>
            </div>

            <div className="page-content" style={{ paddingTop: '4px' }}>
              {user?.status_plano === 'FREE' ? (
                <div className="premium-lock-card" style={{ padding: '36px 24px' }}>
                  <div className="premium-lock-icon">🔒</div>
                  <h4 style={{ margin: '8px 0 4px 0', fontSize: '1.1rem', fontWeight: 'bold', color: 'var(--text-primary)' }}>Mural Completo de Códigos</h4>
                  <p style={{ fontSize: '0.88rem', color: 'var(--text-secondary)', marginBottom: '16px', lineHeight: '1.4' }}>Acesse a linha do tempo completa de todas as suas revelações e códigos diários destravados.</p>
                  <button className="btn-primary" style={{ padding: '10px 20px', fontSize: '0.9rem', width: 'auto' }} onClick={() => setActiveTab('upgrade')}>🔓 Destravar Histórico</button>
                </div>
              ) : (
                <>
                  <input type="text" className="input-field" placeholder="🔍 Pesquisar código, versículo..." value={searchQuery} onChange={e => setSearchQuery(e.target.value)} style={{ marginBottom: '16px' }} />
                  {historico
                    .filter(item => item.codigo_verbal.toLowerCase().includes(searchQuery.toLowerCase()) || item.versiculo_chave.toLowerCase().includes(searchQuery.toLowerCase()))
                    .map(item => (
                      <div key={item.dia_id} className="glass-panel">
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                          <span className="section-chip" style={{ fontSize: '0.68rem' }}>Dia {item.dia_id}</span>
                          <span style={{ fontSize: '0.72rem', color: '#A8A29E', fontWeight: '600' }}>{item.pilar_origem?.replace('_', ' ')}</span>
                        </div>
                        <h3 style={{ fontSize: '1rem', marginBottom: '6px' }}>{item.codigo_verbal}</h3>
                        <p style={{ fontStyle: 'italic', fontSize: '0.85rem', color: '#78716C' }}>{item.versiculo_chave}</p>
                      </div>
                    ))}
                  {historico.length === 0 && (
                    <div className="glass-panel" style={{ textAlign: 'center', padding: '40px 20px' }}>
                      <div style={{ fontSize: '2rem', marginBottom: '10px' }}>📅</div>
                      <p>Nenhum código registrado ainda. Complete mais dias!</p>
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        )}

        {/* ════════════ ABA CHAT IA ════════════ */}
        {activeTab === 'chat' && (
          <div className="page-enter flex-column" style={{ height: 'calc(100vh - 76px)', justifyContent: 'space-between' }}>
            {!activeCounselor ? (
                /* GRID DE CONSELHEIROS */
                <div style={{ flex: 1, overflowY: 'auto', padding: '24px', paddingBottom: '100px' }}>
                  <div style={{ textAlign: 'center', marginBottom: '32px' }}>
                    <h2 style={{ fontSize: '1.8rem', color: 'var(--orange)', marginBottom: '8px' }}>Escolha seu Conselheiro</h2>
                    <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem' }}>Converse com personalidades históricas para guiar sua jornada.</p>
                    <div style={{ marginTop: '16px', display: 'inline-flex', alignItems: 'center', gap: '8px', background: 'rgba(245,158,11,0.15)', padding: '8px 20px', borderRadius: '30px', border: '1px solid var(--orange)' }}>
                      <span style={{ fontSize: '1rem', color: 'var(--text-primary)' }}>Seu saldo:</span>
                      <span style={{ display:'inline-flex', alignItems:'center', gap:'6px', fontSize:'1.2rem', fontWeight:'bold', color:'var(--orange)' }}><ChaminhaCoin size={24}/> {userCoins}</span>
                    </div>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '16px' }}>
                    {COUNSELORS.map(counselor => {
                      const isUnlocked = unlockedCounselors.includes(counselor.id);
                      return (
                        <div key={counselor.id} className="dashboard-card" style={{ position: 'relative', opacity: isUnlocked ? 1 : 0.8 }} onClick={() => {
                          if (isUnlocked) {
                            setActiveCounselor(counselor.id);
                          } else {
                            if (userCoins >= counselor.price) {
                              if (confirm(`Deseja desbloquear ${counselor.name} por $<span style={{display:'inline-flex',alignItems:'center',gap:'4px'}}><ChaminhaCoin size={16}/> {counselor.price}</span>?`)) {
                                setUserCoins(prev => {
                                  const val = prev - counselor.price;
                                  localStorage.setItem('app-coins', val);
                                  return val;
                                });
                                setUnlockedCounselors(prev => {
                                  const arr = [...prev, counselor.id];
                                  localStorage.setItem('unlocked-counselors', JSON.stringify(arr));
                                  return arr;
                                });
                              }
                            } else {
                              alert('Moedas insuficientes!');
                            }
                          }
                        }}>
                          {!isUnlocked && (
                            <div style={{ position: 'absolute', top: 8, right: 8, background: 'var(--orange)', color: '#fff', padding: '2px 8px', borderRadius: '12px', fontSize: '0.7rem', fontWeight: 'bold' }}>
                              {counselor.price} ⭐
                            </div>
                          )}
                          <div className="dashboard-card-icon" style={{
                            width: '50px', height: '50px', borderRadius: '50%', background: isUnlocked ? 'rgba(16,185,129,0.1)' : 'rgba(255,255,255,0.05)',
                            display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.2rem', margin: '0 auto',
                            color: isUnlocked ? 'var(--orange)' : 'var(--text-secondary)', fontWeight: 'bold'
                          }}>
                            {counselor.name.substring(0,2).toUpperCase()}
                          </div>
                          
                          <span className="dashboard-card-label" style={{ marginTop: '8px' }}>{counselor.name}</span>
                          <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textAlign: 'center', lineHeight: '1.2' }}>{counselor.title}</span>
                        </div>
                      );
                    })}
                  </div>
                </div>
            ) : (
                lwcState !== 'authenticated' ? (
                  <div className="flex-column gap-md align-center justify-center text-center" style={{ flex: 1, padding: '2rem', position: 'relative' }}>
                    <button 
                      onClick={() => setActiveCounselor(null)}
                      style={{ position: 'absolute', top: '24px', left: '24px', background: 'transparent', border: 'none', color: 'var(--text-primary)', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '8px' }}
                    >
                      <svg width="24" height="24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M15 18l-6-6 6-6"/></svg>
                      Voltar
                    </button>
                    
                    <div style={{ fontSize: '4.5rem', filter: 'drop-shadow(0 0 10px rgba(16, 185, 129, 0.2))' }}>
                      <svg width="80" height="80" viewBox="0 0 24 24" fill="none" stroke="var(--orange)" strokeWidth="1.5">
                        <rect x="3" y="11" width="18" height="10" rx="2"></rect>
                        <circle cx="12" cy="5" r="2"></circle>
                        <path d="M12 7v4"></path>
                        <line x1="8" y1="16" x2="8" y2="16.01"></line>
                        <line x1="16" y1="16" x2="16" y2="16.01"></line>
                      </svg>
                    </div>
                    <h2 style={{ fontSize: '1.4rem', fontWeight: 'bold', color: 'var(--text-primary)' }}>Conselheiro Bloqueado</h2>
                    <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', lineHeight: '1.6', maxWidth: '300px' }}>
                      Você desbloqueou o conselheiro, mas para conversar com ele é necessário conectar sua conta do ChatGPT.
                    </p>
                    <button className="btn-primary" style={{ padding: '12px 24px', marginTop: '16px' }} onClick={() => setActiveTab('conta')}>
                      Conectar ChatGPT Agora
                    </button>
                  </div>
                ) : (
                  /* CHAT COM O CONSELHEIRO SELECIONADO */
                  <div className="chat-container" style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
                    <div className="chat-header" style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                        <button 
                          onClick={() => setActiveCounselor(null)}
                          style={{ background: 'transparent', border: 'none', color: 'var(--text-primary)', cursor: 'pointer', display: 'flex', alignItems: 'center', padding: '4px' }}
                        >
                          <svg width="24" height="24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M15 18l-6-6 6-6"/></svg>
                        </button>
                        <div style={{
                          width: '36px', height: '36px', borderRadius: '50%', background: 'rgba(255,255,255,0.1)',
                          display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.9rem',
                          color: 'var(--text-primary)', fontWeight: 'bold'
                        }}>
                          {COUNSELORS.find(c => c.id === activeCounselor)?.name.substring(0,2).toUpperCase()}
                        </div>
                        <div>
                          <strong style={{ display: 'block', fontSize: '0.95rem' }}>{COUNSELORS.find(c => c.id === activeCounselor)?.name}</strong>
                          <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                            ChatGPT ({chatGptUser?.plan?.toUpperCase() || 'SESSÃO'})
                          </span>
                        </div>
                      </div>
                      
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <button className="btn-secondary" style={{ padding: '4px 10px', fontSize: '0.75rem' }} onClick={() => {
                          if (confirm('Deseja limpar o histórico do chat?')) {
                            setChatMessages([{ role: 'assistant', content: `Olá! Sou ${COUNSELORS.find(c => c.id === activeCounselor)?.name}. Como posso te ajudar hoje?` }]);
                          }
                        }}>
                          Limpar
                        </button>
                      </div>
                    </div>

                    <div className="chat-messages">
                      {chatMessages.map((msg, index) => (
                        <div key={index} className={`chat-bubble ${msg.role}`}>
                          {msg.content}
                        </div>
                      ))}
                      {chatLoading && (
                        <div className="chat-bubble assistant">
                          <div className="typing-indicator">
                            <div className="typing-dot"></div><div className="typing-dot"></div><div className="typing-dot"></div>
                          </div>
                        </div>
                      )}
                      <div ref={messagesEndRef} />
                    </div>

                    <div className="chat-input-area">
                      <form onSubmit={handleSendChatMessage} className="chat-input-row">
                        <input
                          type="text"
                          className="chat-input-field"
                          placeholder="Fale com o Conselheiro..."
                          value={chatInput}
                          onChange={(e) => setChatInput(e.target.value)}
                          disabled={chatLoading}
                        />
                        <button type="submit" className="chat-send-btn" disabled={chatLoading || !chatInput.trim()}>
                          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <line x1="22" y1="2" x2="11" y2="13"></line>
                            <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                          </svg>
                        </button>
                      </form>
                    </div>
                  </div>
                )
            )}
          </div>
        )}

        {/* ════════════ ABA UPGRADE ════════════ */}
        {activeTab === 'upgrade' && (
          <div className="page-enter">
            <div className="page-hero hero-premium">
              <div className="hero-orb" style={{ width: 250, height: 250, top: -60, right: -50, background: 'rgba(249,115,22,0.25)' }} />
              <div className="hero-content">
                <div className="hero-label">⭐ Plano Premium</div>
                <div className="hero-title">Entre no Governo do Reino</div>
                <div className="hero-sub">Ferramentas completas de transformação espiritual</div>
              </div>
            </div>

            <div className="page-content" style={{ paddingTop: '4px' }}>
              <div className="glass-panel dark-card" style={{ marginBottom: '16px' }}>
                {[
                  { icon: '🎧', feat: 'Meditações Guiadas', val: '365 áudios', desc: 'Um áudio por dia de alinhamento' },
                  { icon: '👥', feat: 'Contatos Ilimitados', val: 'Sem limites', desc: 'Todo o seu círculo de influência' },
                  { icon: '⚠️', feat: 'Alertas de Conexão', val: 'Automáticos', desc: 'Notificação a cada 48h por prioritário' },
                  { icon: '📖', feat: 'Histórico Completo', val: 'Liberado', desc: 'Mural de todos os códigos' },
                ].map(({ icon, feat, val, desc }) => (
                  <div key={feat} style={{ display: 'flex', alignItems: 'center', gap: '14px', padding: '12px 0', borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
                    <span style={{ fontSize: '1.4rem', flexShrink: 0 }}>{icon}</span>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: '700', fontSize: '0.95rem', color: '#fff' }}>{feat}</div>
                      <div style={{ fontSize: '0.80rem', color: 'rgba(255,255,255,0.60)' }}>{desc}</div>
                    </div>
                    <span style={{ fontWeight: '700', color: '#FCD34D', fontSize: '0.85rem', flexShrink: 0 }}>{val}</span>
                  </div>
                ))}
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '14px' }}>
                <div className="glass-panel orange-card" style={{ textAlign: 'center', padding: '18px 14px', border: '1px solid rgba(212,175,55,.4)' }}>
                  <div style={{ fontSize: '0.8rem', color: '#78716C', marginBottom: '4px', fontWeight: '700', letterSpacing: '1px' }}>MENSAL</div>
                  <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'center', gap: '3px', marginBottom: '6px' }}>
                    <span style={{ fontSize: '0.95rem', color: '#78716C' }}>R$</span>
                    <span style={{ fontSize: '2.6rem', fontWeight: '900', color: '#C2550A', lineHeight: 1 }}>29</span>
                    <span style={{ fontSize: '1.3rem', fontWeight: '800', color: '#C2550A' }}>,90</span>
                    <span style={{ fontSize: '0.78rem', color: '#A8A29E' }}>/mês</span>
                  </div>
                  <div style={{ fontSize: '0.74rem', color: '#A8A29E', marginBottom: '12px' }}>Cancele quando quiser</div>
                  <button className="btn-primary" onClick={() => iniciarCheckoutPremium(2990, '1Convite Premium — Mensal (R$ 29,90/mês)', 'Mensal')} style={{ width: '100%', padding: '11px 8px', fontSize: '0.85rem' }}>
                    {isPaying ? 'Gerando…' : '⚡ Assinar Mensal'}
                  </button>
                </div>
                <div className="glass-panel orange-card" style={{ textAlign: 'center', padding: '18px 14px', border: '1px solid rgba(212,175,55,.4)', position: 'relative' }}>
                  <div style={{ position: 'absolute', top: -10, left: '50%', transform: 'translateX(-50%)', background: '#C2550A', color: '#fff', fontSize: '0.68rem', fontWeight: '800', padding: '3px 10px', borderRadius: '999px', letterSpacing: '0.5px' }}>2 MESES GRÁTIS</div>
                  <div style={{ fontSize: '0.8rem', color: '#78716C', marginBottom: '4px', fontWeight: '700', letterSpacing: '1px' }}>ANUAL</div>
                  <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'center', gap: '3px', marginBottom: '6px' }}>
                    <span style={{ fontSize: '0.95rem', color: '#78716C' }}>R$</span>
                    <span style={{ fontSize: '2.6rem', fontWeight: '900', color: '#C2550A', lineHeight: 1 }}>297</span>
                    <span style={{ fontSize: '1rem', fontWeight: '800', color: '#C2550A' }}>,00</span>
                  </div>
                  <div style={{ fontSize: '0.74rem', color: '#A8A29E', marginBottom: '12px' }}>12 meses por R$ 24,75/mês</div>
                  <button className="btn-primary" onClick={() => iniciarCheckoutPremium(29700, '1Convite Premium — Anual (R$ 297,00 à vista)', 'Anual')} style={{ width: '100%', padding: '11px 8px', fontSize: '0.85rem' }}>
                    {isPaying ? 'Gerando…' : '🔥 Assinar Anual'}
                  </button>
                </div>
              </div>
              <p style={{ fontSize: '0.78rem', color: '#A8A29E', marginTop: '4px' }}>Pagamento via Asaas (PIX ou cartão) • Acesso liberado na hora após confirmação</p>
              <button className="btn-secondary" style={{ marginTop: '8px', width: '100%', fontSize: '0.8rem' }} onClick={() => window.open('/instalar', '_blank')}>
                📲 Como instalar o app no celular
              </button>
            </div>
          </div>
        )}

        {/* ════════════ TELA PAGAMENTO ════════════ */}
        {activeTab === 'simular-pagamento' && (
          <div className="page-enter" style={{ padding: '20px', paddingBottom: '40px' }}>
            <div className="glass-panel" style={{ borderTop: '4px solid #009ee3', marginTop: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '16px' }}>
                <span style={{ color: '#009ee3', fontWeight: '800', fontSize: '1.2rem' }}>mercado pago</span>
                <span style={{ fontSize: '0.75rem', color: '#A8A29E', fontWeight: '700', border: '1px solid #E5E7EB', padding: '2px 8px', borderRadius: '4px' }}>SANDBOX</span>
              </div>
              <h3 style={{ marginBottom: '14px' }}>Resumo da Assinatura</h3>
              <div style={{ display: 'flex', justifyContent: 'space-between', background: '#F8FAFC', padding: '12px 16px', borderRadius: '10px', marginBottom: '18px', border: '1px solid #E2E8F0' }}>
                <span style={{ fontWeight: '500' }}>1Convite Premium — Mensal</span>
                <strong style={{ color: '#1C1917' }}>R$ 29,90</strong>
              </div>
              <p style={{ fontSize: '0.88rem', marginBottom: '20px', color: '#78716C', lineHeight: '1.65' }}>
                Ambiente de checkout seguro. Clique no botão abaixo para simular a aprovação instantânea do pagamento.
              </p>
              <button className="btn-primary" style={{ background: 'linear-gradient(135deg, #009ee3, #0088CC)' }} onClick={finalizarPagamentoSimulado}>
                ⚡ Confirmar e Simular Aprovação
              </button>
              <button className="btn-secondary" style={{ marginTop: '10px', width: '100%' }} onClick={() => setActiveTab('upgrade')}>Cancelar</button>
            </div>
          </div>
        )}

        {/* ── ABA MINHA CONTA & PERFIL ────────────────────────── */}
        {activeTab === 'conta' && (
          <div className="page-enter flex-column gap-md">
            <div className="page-hero hero-sabado" style={{ textAlign: 'center', padding: '30px 20px' }}>
              <div className="hero-content">
                <div className="profile-avatar-container">
                  <img src={profileAvatar} alt="Foto de Perfil" className="profile-avatar-img" />
                  <label className="profile-avatar-upload-btn" title="Alterar foto de perfil">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path><circle cx="12" cy="13" r="4"></circle></svg>
                    <input type="file" accept="image/*" onChange={handleAvatarUpload} style={{ display: 'none' }} />
                  </label>
                </div>
                <h2 className="hero-title" style={{ fontSize: '1.4rem', marginBottom: '4px' }}>{profileName}</h2>
                <span className={`pedagio-badge ${user?.status_plano === 'PREMIUM' ? 'badge-proposito' : 'badge-recompensa'}`}>
                  {user?.status_plano === 'PREMIUM' ? '⭐ Membro Premium' : '🌱 Plano Gratuito (FREE)'}
                </span>
              </div>
            </div>

            <div className="page-content" style={{ paddingTop: '10px' }}>
              {/* Tema & Aparência */}
              <div className="glass-panel" style={{ marginBottom: '16px', textAlign: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--text-primary)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"></circle><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"></path><path d="M2 12h20"></path></svg>
                  <h3 style={{ fontSize: '1.05rem', margin: 0, textAlign: 'left' }}>Tema & Aparência</h3>
                </div>
                <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginBottom: '14px', textAlign: 'left', lineHeight: '1.4' }}>
                  Escolha a cor de destaque do seu aplicativo para personalizar a sua experiência:
                </p>
                <div style={{ display: 'flex', gap: '16px', justifyContent: 'center', alignItems: 'center', margin: '10px 0' }}>
                  {[
                    { id: 'theme-orange', color: '#f97316', name: 'Laranja' },
                    { id: 'theme-blue', color: '#3b82f6', name: 'Azul' },
                    { id: 'theme-green', color: '#10B981', name: 'Verde' },
                    { id: 'theme-purple', color: '#8b5cf6', name: 'Roxo' },
                    { id: 'theme-sepia', color: '#b58900', name: 'Sépia' }
                  ].map(t => (
                    <button
                      key={t.id}
                      onClick={() => setTheme(t.id)}
                      title={t.name}
                      style={{
                        width: '36px',
                        height: '36px',
                        borderRadius: '50%',
                        backgroundColor: t.color,
                        border: theme === t.id ? '3px solid var(--text-primary)' : '2px solid rgba(0,0,0,0.1)',
                        cursor: 'pointer',
                        transform: theme === t.id ? 'scale(1.15)' : 'scale(1)',
                        transition: 'all 0.2s ease',
                        boxShadow: theme === t.id ? '0 4px 10px rgba(0,0,0,0.15)' : 'none'
                      }}
                    />
                  ))}
                </div>
              </div>

              {/* Ajuste de Tamanho da Fonte (Modelo da Imagem) */}
              <div className="glass-panel" style={{ marginBottom: '16px', textAlign: 'left' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontSize: '1.25rem', fontWeight: '800', color: 'var(--text-primary)' }}>Aa</span>
                    <h3 style={{ fontSize: '1.05rem', margin: 0 }}>Alterar tamanho da letra</h3>
                  </div>
                  {/* Toggle Switch */}
                  <label style={{ position: 'relative', display: 'inline-block', width: '42px', height: '22px', cursor: 'pointer' }}>
                    <input
                      type="checkbox"
                      checked={enableCustomFontSize}
                      onChange={(e) => {
                        const checked = e.target.checked;
                        setEnableCustomFontSize(checked);
                        localStorage.setItem('app-enable-font-size', checked);
                      }}
                      style={{ opacity: 0, width: 0, height: 0 }}
                    />
                    <span style={{
                      position: 'absolute', top: 0, left: 0, right: 0, bottom: 0,
                      backgroundColor: enableCustomFontSize ? 'var(--orange)' : 'rgba(255,255,255,0.1)',
                      border: enableCustomFontSize ? 'none' : '1px solid var(--slate-border)',
                      transition: 'all 0.3s ease', borderRadius: '22px'
                    }}>
                      <span style={{
                        position: 'absolute', content: '""', height: '16px', width: '16px', left: enableCustomFontSize ? '23px' : '2px', bottom: enableCustomFontSize ? '3px' : '2px',
                        backgroundColor: enableCustomFontSize ? 'white' : 'var(--text-secondary)', transition: 'all 0.3s ease', borderRadius: '50%'
                      }} />
                    </span>
                  </label>
                </div>

                {enableCustomFontSize && (
                  <div className="animate-fade-in" style={{ marginTop: '16px', padding: '0 4px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '14px', justifyContent: 'space-between', marginBottom: '10px' }}>
                      <span style={{ fontSize: '0.85rem', opacity: 0.6, fontWeight: '500' }}>Aa</span>
                      <input
                        type="range"
                        min="13"
                        max="22"
                        value={fontSizeScale}
                        onChange={(e) => {
                          const val = parseInt(e.target.value);
                          setFontSizeScale(val);
                          localStorage.setItem('app-font-size', val);
                        }}
                        style={{
                          flex: 1,
                          accentColor: 'var(--orange)',
                          height: '5px',
                          borderRadius: '3px',
                          cursor: 'pointer'
                        }}
                      />
                      <span style={{ fontSize: '1.25rem', fontWeight: 'bold' }}>Aa</span>
                    </div>
                    <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', margin: '12px 0 0', textAlign: 'center', opacity: 0.9 }}>
                      Clique e arraste a barra para alterar o tamanho da letra.
                    </p>
                  </div>
                )}
              </div>

              {/* Configurações de Voz (Modelo da Imagem) */}
              <div className="glass-panel" style={{ marginBottom: '16px', textAlign: 'left' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--text-primary)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path><path d="M19 10v2a7 7 0 0 1-14 0v-2"></path><line x1="12" y1="19" x2="12" y2="23"></line><line x1="8" y1="23" x2="16" y2="23"></line></svg>
                  <h3 style={{ fontSize: '1.05rem', margin: 0 }}>Voz</h3>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                  {/* Opção Masculina */}
                  <label style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', cursor: 'pointer' }}>
                    <span style={{ fontSize: '0.9rem', color: 'var(--text-primary)' }}>Masculina</span>
                    <input
                      type="radio"
                      name="voiceGender"
                      checked={voiceGender === 'masculino'}
                      onChange={() => {
                        setVoiceGender('masculino');
                        localStorage.setItem('app-voice-gender', 'masculino');
                      }}
                      style={{
                        width: '18px',
                        height: '18px',
                        accentColor: 'var(--orange)',
                        cursor: 'pointer'
                      }}
                    />
                  </label>

                  {/* Opção Feminina */}
                  <label style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', cursor: 'pointer' }}>
                    <span style={{ fontSize: '0.9rem', color: 'var(--text-primary)' }}>Feminina</span>
                    <input
                      type="radio"
                      name="voiceGender"
                      checked={voiceGender === 'feminino'}
                      onChange={() => {
                        setVoiceGender('feminino');
                        localStorage.setItem('app-voice-gender', 'feminino');
                      }}
                      style={{
                        width: '18px',
                        height: '18px',
                        accentColor: 'var(--orange)',
                        cursor: 'pointer'
                      }}
                    />
                  </label>

                  {/* Velocidade de Reprodução */}
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '4px', borderTop: '1px solid var(--slate-border)', paddingTop: '12px' }}>
                    <span style={{ fontSize: '0.9rem', color: 'var(--text-primary)' }}>Velocidade de reprodução</span>
                    <select
                      value={voiceSpeed}
                      onChange={(e) => {
                        const val = parseFloat(e.target.value);
                        setVoiceSpeed(val);
                        localStorage.setItem('app-voice-speed', val);
                      }}
                      style={{
                        padding: '6px 12px',
                        borderRadius: '8px',
                        border: '1px solid var(--slate-border)',
                        backgroundColor: 'var(--white)',
                        color: 'var(--text-primary)',
                        fontSize: '0.85rem',
                        fontWeight: '500',
                        outline: 'none',
                        cursor: 'pointer'
                      }}
                    >
                      <option value="0.8">0.8x</option>
                      <option value="1.0">1x</option>
                      <option value="1.2">1.2x</option>
                      <option value="1.5">1.5x</option>
                    </select>
                  </div>
                </div>
              </div>

              {/* Logout da Conta */}
              <div className="glass-panel" style={{ marginBottom: '16px', textAlign: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--text-primary)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path><polyline points="16 17 21 12 16 7"></polyline><line x1="21" y1="12" x2="9" y2="12"></line></svg>
                  <h3 style={{ fontSize: '1.05rem', margin: 0, textAlign: 'left' }}>Sessão Ativa</h3>
                </div>
                <div className="flex-column gap-sm">
                  <p style={{ fontSize: '0.88rem', color: 'var(--text-secondary)', marginBottom: '8px', textAlign: 'left' }}>
                    Conectado como <strong>{profileEmail || 'Visitante'}</strong>
                  </p>
                  <button className="btn-secondary" style={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }} onClick={handleLogout}>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path><polyline points="16 17 21 12 16 7"></polyline><line x1="21" y1="12" x2="9" y2="12"></line></svg>
                    Sair da Conta (Logout)
                  </button>
                </div>
              </div>

              {/* Integração com IA */}
              <div className="glass-panel" style={{ marginBottom: '16px', textAlign: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--text-primary)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path><polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline><line x1="12" y1="22.08" x2="12" y2="12"></line></svg>
                  <h3 style={{ fontSize: '1.05rem', margin: 0, textAlign: 'left' }}>Conexão com Conselheiro IA</h3>
                </div>
                
                {lwcState === 'authenticated' ? (
                  <div className="flex-column gap-sm">
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', color: 'var(--orange)', fontWeight: '600', fontSize: '0.95rem', margin: '4px 0' }}>
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><circle cx="12" cy="12" r="10"></circle></svg>
                      IA Ativa ({chatGptUser?.plan ? chatGptUser.plan.toUpperCase() : 'FREE/PLUS'})
                    </div>
                    <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginBottom: '8px', textAlign: 'left' }}>
                      Conta conectada: <strong>{chatGptUser?.email || 'Usuário ChatGPT'}</strong>. Você já pode conversar com o Conselheiro.
                    </p>
                    <button className="btn-secondary" style={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }} onClick={handleDisconnectChatGPT}>
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path><line x1="8" y1="12" x2="16" y2="12"></line></svg>
                      Desconectar Conta
                    </button>
                  </div>
                ) : lwcState === 'pending' && lwcDeviceCode ? (
                  <div className="flex-column gap-sm">
                    <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: '1.5', textAlign: 'left' }}>
                      Abra o link abaixo e insira o seguinte código para autorizar o acesso:
                    </p>
                    <div className="lwc-code-box">{lwcDeviceCode.userCode}</div>
                    <a 
                      href={lwcDeviceCode.verificationUrl} 
                      target="_blank" 
                      rel="noopener noreferrer" 
                      className="btn-primary" 
                      style={{ textDecoration: 'none', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', width: '100%', padding: '10px' }}
                    >
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>
                      Página de Verificação
                    </a>
                    <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px', textAlign: 'center' }}>
                      Aguardando autorização... (Expira em 5 minutos)
                    </p>
                  </div>
                ) : (
                  <div className="flex-column gap-sm">
                    <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginBottom: '10px', lineHeight: '1.5', textAlign: 'left' }}>
                      Conecte sua conta do ChatGPT para liberar o <strong>Conselheiro IA</strong> e <strong>Desafios Inteligentes</strong> customizados, sem custo extra para você ou para a plataforma.
                    </p>
                    <button className="btn-primary" style={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }} onClick={handleConnectChatGPT}>
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path></svg>
                      Conectar Conta IA
                    </button>
                  </div>
                )}
              </div>

              {/* Alternância de Tema */}
              <div className="glass-panel" style={{ marginBottom: '16px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--text-primary)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2v2"></path><path d="M12 20v2"></path><path d="M4.93 4.93l1.41 1.41"></path><path d="M17.66 17.66l1.41 1.41"></path><path d="M2 12h2"></path><path d="M20 12h2"></path><path d="M6.34 17.66l-1.41 1.41"></path><path d="M19.07 4.93l-1.41 1.41"></path></svg>
                  <h3 style={{ fontSize: '1.05rem', margin: 0, textAlign: 'left' }}>Aparência & Tema</h3>
                </div>
                <div className="toggle-switch-container">
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: '24px' }}>
                      {darkMode ? (
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--text-primary)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>
                      ) : (
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--text-primary)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>
                      )}
                    </div>
                    <div>
                      <strong style={{ display: 'block', fontSize: '0.92rem' }}>Modo Escuro (Dark Mode)</strong>
                      <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>Alternar tema de cores da interface</span>
                    </div>
                  </div>
                  <label className="toggle-switch">
                    <input type="checkbox" checked={darkMode} onChange={() => setDarkMode(!darkMode)} />
                    <span className="toggle-slider"></span>
                  </label>
                </div>
              </div>

              {/* Informações da Conta */}
              <div className="glass-panel" style={{ marginBottom: '16px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--text-primary)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
                  <h3 style={{ fontSize: '1.05rem', margin: 0, textAlign: 'left' }}>Informações Pessoais</h3>
                </div>
                <form onSubmit={handleSaveProfile} className="flex-column gap-sm">
                  <div className="input-group">
                    <label>Nome Completo</label>
                    <input type="text" className="input-field" value={profileName} onChange={(e) => setProfileName(e.target.value)} placeholder="Seu nome" />
                  </div>
                  <div className="input-group">
                    <label>E-mail da Conta</label>
                    <input type="email" className="input-field" value={profileEmail} onChange={(e) => setProfileEmail(e.target.value)} placeholder="seu.email@exemplo.com" />
                  </div>

                  {profileSavedMsg && (
                    <div style={{ color: '#16a34a', fontSize: '0.85rem', fontWeight: 'bold', margin: '4px 0' }}>
                      {profileSavedMsg}
                    </div>
                  )}

                  <button type="submit" className="btn-primary" style={{ marginTop: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path><polyline points="17 21 17 13 7 13 7 21"></polyline><polyline points="7 3 7 8 15 8"></polyline></svg>
                    Salvar Alterações
                  </button>
                </form>
              </div>

              {/* Plano & Assinatura */}
              <div className="glass-panel">
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--text-primary)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="2" y="5" width="20" height="14" rx="2" ry="2"></rect><line x1="2" y1="10" x2="22" y2="10"></line></svg>
                  <h3 style={{ fontSize: '1.05rem', margin: 0, textAlign: 'left' }}>Plano & Assinatura</h3>
                </div>
                <div className="flex-between" style={{ background: 'var(--slate-light)', padding: '14px', borderRadius: '12px', marginBottom: '14px' }}>
                  <div>
                    <strong style={{ display: 'block', fontSize: '0.95rem' }}>1Convite Premium</strong>
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                      {user?.status_plano === 'PREMIUM' ? 'Sua assinatura está ativa' : 'Acesso limitado ao plano gratuito'}
                    </span>
                  </div>
                  <span style={{ fontWeight: 'bold', color: 'var(--orange)' }}>
                    {user?.status_plano === 'PREMIUM' ? 'ATIVO' : 'R$ 29,90/mês'}
                  </span>
                </div>

                {user?.status_plano === 'FREE' ? (
                  <button className="btn-primary" style={{ width: '100%' }} onClick={() => setActiveTab('upgrade')}>
                    ⚡ Fazer Upgrade para Premium
                  </button>
                ) : (
                  <button className="btn-secondary" style={{ width: '100%' }} onClick={() => setActiveTab('sabado')}>
                    Acessar Conteúdo Exclusivo
                  </button>
                )}
              </div>
            </div>
          </div>
        )}

        {/* ════════════ ABA STUDIO DE CARDS ════════════ */}
        {activeTab === 'criar-card' && (() => {
          const phrases = CARD_PHRASES[cardCategory] || [];
          const activeBgCat = CARD_BG_CATEGORIES.find(c => c.id === cardBgCategory);
          const activeBgItems = activeBgCat?.items || [];
          const bg = activeBgItems[cardBg] || activeBgItems[0] || { url: '', label: '' };
          const selectedPhrase = cardSelectedText || (phrases[0] ? phrases[0].text : '');
          const selectedRef = phrases.find(p => p.text === selectedPhrase)?.ref;
          const fontSizeMap = { sm: '0.88rem', md: '1.1rem', lg: '1.35rem', xl: '1.65rem' };
          const fontStyleMap = {
            normal: { fontStyle: 'normal', fontWeight: '400' },
            italic: { fontStyle: 'italic', fontWeight: '400' },
            bold: { fontStyle: 'normal', fontWeight: '700' },
            bolditalic: { fontStyle: 'italic', fontWeight: '700' },
          };
          const MSG_CATS = [
            { id: 'bomdia', label: 'Bom Dia' },
            { id: 'boatarde', label: 'Boa Tarde' },
            { id: 'boanoite', label: 'Boa Noite' },
            { id: 'versiculo', label: 'Versículo' },
            { id: 'convite', label: '1Convite' },
          ];

          return (
            <div className="page-enter" style={{ paddingBottom: '40px' }}>
              <div className="page-content" style={{ paddingTop: '16px' }}>

                {/* ── PREVIEW STICKY ── */}
                <div style={{ padding: '0 20px 16px', position: 'sticky', top: 0, zIndex: 10, background: 'var(--bg-primary)' }}>
                  <div ref={cardPreviewRef} style={{
                    position: 'relative',
                    width: '100%',
                    paddingTop: cardFormat === 'square' ? '100%' : '177%',
                    borderRadius: '16px',
                    overflow: 'hidden',
                    backgroundImage: bg.url ? `url(${bg.url})` : 'linear-gradient(135deg,#1a1a2e,#16213e)',
                    backgroundSize: 'cover',
                    backgroundPosition: 'center',
                    boxShadow: '0 8px 32px rgba(0,0,0,0.40)',
                  }}>
                    <div style={{ position: 'absolute', inset: 0, background: `linear-gradient(to top, rgba(0,0,0,${cardOverlay}) 0%, rgba(0,0,0,${(cardOverlay*0.4).toFixed(2)}) 50%, rgba(0,0,0,${(cardOverlay*0.1).toFixed(2)}) 100%)` }} />
                    <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'flex-end', padding: '24px 20px', textAlign: 'center' }}>
                      <p style={{
                        fontFamily: cardFont,
                        fontSize: fontSizeMap[cardFontSize],
                        color: cardTextColor,
                        lineHeight: '1.65',
                        ...fontStyleMap[cardTextStyle],
                        textShadow: '0 2px 14px rgba(0,0,0,0.85)',
                        margin: 0,
                        letterSpacing: '0.01em',
                      }}>
                        &ldquo;{selectedPhrase}&rdquo;
                      </p>
                      {selectedRef && (
                        <span style={{ marginTop: '10px', fontSize: '0.75rem', color: cardTextColor, opacity: 0.8, fontWeight: '600', letterSpacing: '0.08em', textTransform: 'uppercase', textShadow: '0 1px 6px rgba(0,0,0,0.8)', fontFamily: cardFont }}>
                          — {selectedRef}
                        </span>
                      )}
                      <div style={{ marginTop: '14px', display: 'flex', alignItems: 'center', gap: '5px', opacity: 0.55 }}>
                        <svg width="10" height="10" viewBox="0 0 24 24" fill="#fff"><path d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z"/></svg>
                        <span style={{ fontSize: '0.6rem', color: '#fff', fontWeight: '700', letterSpacing: '0.1em' }}>1CONVITE.COM.BR</span>
                      </div>
                    </div>
                  </div>
                  {/* Formato */}
                  <div style={{ display: 'flex', gap: '8px', marginTop: '10px' }}>
                    {[{ id: 'square', label: 'Post (1:1)' }, { id: 'story', label: 'Story (9:16)' }].map(f => (
                      <button key={f.id} onClick={() => setCardFormat(f.id)} style={{
                        flex: 1, padding: '7px', fontSize: '0.8rem', fontWeight: '600', borderRadius: '10px', cursor: 'pointer', transition: 'all 0.2s',
                        background: cardFormat === f.id ? 'var(--orange)' : 'transparent',
                        color: cardFormat === f.id ? '#000' : 'var(--text-secondary)',
                        border: cardFormat === f.id ? 'none' : '1px solid rgba(255,255,255,0.12)',
                      }}>{f.label}</button>
                    ))}
                  </div>
                </div>

                {/* ── EDITOR DE TEXTO (Canva) ── */}
                <div className="glass-panel" style={{ margin: '0 20px 16px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--text-primary)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
                    <h3 style={{ margin: 0, fontSize: '1rem' }}>Estilo do Texto</h3>
                  </div>

                  {/* Fonte */}
                  <div style={{ marginBottom: '12px' }}>
                    <label style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', fontWeight: '600', display: 'block', marginBottom: '6px' }}>FONTE</label>
                    <div style={{ display: 'flex', gap: '6px', overflowX: 'auto', paddingBottom: '4px' }}>
                      {CARD_FONTS.map(f => (
                        <button key={f.value} onClick={() => setCardFont(f.value)}
                          style={{
                            flexShrink: 0, padding: '6px 12px', borderRadius: '20px', cursor: 'pointer', transition: 'all 0.2s', whiteSpace: 'nowrap', border: 'none',
                            background: cardFont === f.value ? 'var(--orange)' : 'rgba(255,255,255,0.06)',
                            color: cardFont === f.value ? '#000' : 'var(--text-secondary)',
                            fontFamily: f.value, fontSize: '0.82rem',
                          }}
                        >{f.label}</button>
                      ))}
                    </div>
                  </div>

                  {/* Tamanho, Estilo e Overlay na mesma linha */}
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '12px' }}>
                    {/* Tamanho */}
                    <div>
                      <label style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', fontWeight: '600', display: 'block', marginBottom: '6px' }}>TAMANHO</label>
                      <div style={{ display: 'flex', gap: '4px' }}>
                        {CARD_FONT_SIZES.map(s => (
                          <button key={s.value} onClick={() => setCardFontSize(s.value)}
                            style={{
                              flex: 1, padding: '7px 4px', borderRadius: '8px', cursor: 'pointer', border: 'none', transition: 'all 0.2s',
                              background: cardFontSize === s.value ? 'var(--orange)' : 'rgba(255,255,255,0.06)',
                              color: cardFontSize === s.value ? '#000' : 'var(--text-secondary)',
                              fontSize: s.value === 'xl' ? '0.9rem' : s.value === 'sm' ? '0.7rem' : '0.8rem', fontWeight: '700',
                            }}
                          >{s.label}</button>
                        ))}
                      </div>
                    </div>

                    {/* Estilo */}
                    <div>
                      <label style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', fontWeight: '600', display: 'block', marginBottom: '6px' }}>ESTILO</label>
                      <div style={{ display: 'flex', gap: '4px' }}>
                        {[{ id: 'normal', label: 'A', style: {} }, { id: 'italic', label: 'A', style: { fontStyle: 'italic' } }, { id: 'bold', label: 'A', style: { fontWeight: '700' } }, { id: 'bolditalic', label: 'A', style: { fontStyle: 'italic', fontWeight: '700' } }].map(s => (
                          <button key={s.id} onClick={() => setCardTextStyle(s.id)}
                            style={{
                              flex: 1, padding: '7px 4px', borderRadius: '8px', cursor: 'pointer', border: 'none', transition: 'all 0.2s',
                              background: cardTextStyle === s.id ? 'var(--orange)' : 'rgba(255,255,255,0.06)',
                              color: cardTextStyle === s.id ? '#000' : 'var(--text-secondary)',
                              fontSize: '0.88rem', ...s.style,
                            }}
                          >{s.label}</button>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Cores do texto */}
                  <div style={{ marginBottom: '12px' }}>
                    <label style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', fontWeight: '600', display: 'block', marginBottom: '8px' }}>COR DO TEXTO</label>
                    <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                      {CARD_TEXT_COLORS.map(c => (
                        <button key={c.value} onClick={() => setCardTextColor(c.value)} title={c.label}
                          style={{
                            width: '32px', height: '32px', borderRadius: '50%', cursor: 'pointer', padding: 0,
                            background: c.value,
                            border: cardTextColor === c.value ? '3px solid var(--orange)' : '2px solid rgba(255,255,255,0.15)',
                            transform: cardTextColor === c.value ? 'scale(1.2)' : 'scale(1)',
                            transition: 'all 0.2s', boxSizing: 'border-box',
                          }}
                        />
                      ))}
                    </div>
                  </div>

                  {/* Escuridão do overlay */}
                  <div>
                    <label style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', fontWeight: '600', display: 'block', marginBottom: '6px' }}>ESCURIDÃO DO FUNDO: {Math.round(cardOverlay * 100)}%</label>
                    <input type="range" min="0" max="100" value={Math.round(cardOverlay * 100)}
                      onChange={e => setCardOverlay(Number(e.target.value) / 100)}
                      style={{ width: '100%', accentColor: 'var(--orange)' }}
                    />
                  </div>
                </div>

                {/* ── GALERIA DE FUNDOS ── */}
                <div className="glass-panel" style={{ margin: '0 20px 16px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--text-primary)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>
                    <h3 style={{ margin: 0, fontSize: '1rem' }}>Escolha o Fundo</h3>
                  </div>
                  {/* Abas de categoria de fundo */}
                  <div style={{ display: 'flex', gap: '6px', overflowX: 'auto', paddingBottom: '6px', marginBottom: '12px' }}>
                    {CARD_BG_CATEGORIES.map(cat => (
                      <button key={cat.id} onClick={() => { setCardBgCategory(cat.id); setCardBg(0); }}
                        style={{
                          flexShrink: 0, padding: '5px 12px', fontSize: '0.78rem', fontWeight: '600',
                          borderRadius: '20px', cursor: 'pointer', transition: 'all 0.2s', whiteSpace: 'nowrap', border: 'none',
                          background: cardBgCategory === cat.id ? 'var(--orange)' : 'rgba(255,255,255,0.06)',
                          color: cardBgCategory === cat.id ? '#000' : 'var(--text-secondary)',
                        }}
                      >{cat.label}</button>
                    ))}
                  </div>
                  {/* Grid de imagens */}
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '8px' }}>
                    {activeBgItems.map((item, idx) => (
                      <div key={idx} onClick={() => setCardBg(idx)}
                        style={{
                          position: 'relative', paddingTop: '100%', borderRadius: '10px', overflow: 'hidden', cursor: 'pointer',
                          backgroundImage: `url(${item.url})`, backgroundSize: 'cover', backgroundPosition: 'center',
                          border: cardBg === idx ? '2.5px solid var(--orange)' : '2px solid transparent',
                          transition: 'all 0.2s',
                          transform: cardBg === idx ? 'scale(1.06)' : 'scale(1)',
                        }}
                      >
                        {cardBg === idx && (
                          <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'flex-end', justifyContent: 'center', background: 'rgba(0,0,0,0.25)', paddingBottom: '4px' }}>
                            <span style={{ fontSize: '0.6rem', color: '#fff', fontWeight: '700', background: 'rgba(0,0,0,0.5)', padding: '1px 5px', borderRadius: '4px' }}>{item.label}</span>
                          </div>
                        )}
                        {cardBg !== idx && (
                          <div style={{ position: 'absolute', bottom: 0, left: 0, right: 0, padding: '2px 4px', background: 'rgba(0,0,0,0.4)' }}>
                            <span style={{ fontSize: '0.55rem', color: '#fff', fontWeight: '600' }}>{item.label}</span>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>

                {/* ── MENSAGEM ── */}
                <div className="glass-panel" style={{ margin: '0 20px 16px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--text-primary)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
                    <h3 style={{ margin: 0, fontSize: '1rem' }}>Escolha a Mensagem</h3>
                  </div>
                  <div style={{ display: 'flex', gap: '6px', overflowX: 'auto', paddingBottom: '4px', marginBottom: '12px' }}>
                    {MSG_CATS.map(c => (
                      <button key={c.id} onClick={() => { setCardCategory(c.id); setCardSelectedText(''); }}
                        style={{
                          flexShrink: 0, padding: '6px 12px', fontSize: '0.78rem', fontWeight: '600',
                          borderRadius: '20px', cursor: 'pointer', transition: 'all 0.2s', whiteSpace: 'nowrap', border: 'none',
                          background: cardCategory === c.id ? 'var(--orange)' : 'rgba(255,255,255,0.06)',
                          color: cardCategory === c.id ? '#000' : 'var(--text-secondary)',
                        }}
                      >{c.label}</button>
                    ))}
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {phrases.map((p, idx) => (
                      <div key={idx} onClick={() => setCardSelectedText(p.text)}
                        style={{
                          padding: '12px 14px', borderRadius: '12px', cursor: 'pointer', transition: 'all 0.2s',
                          background: (cardSelectedText || phrases[0]?.text) === p.text ? 'rgba(249,115,22,0.12)' : 'rgba(255,255,255,0.04)',
                          border: (cardSelectedText || phrases[0]?.text) === p.text ? '1.5px solid var(--orange)' : '1px solid rgba(255,255,255,0.07)',
                        }}
                      >
                        <p style={{ margin: 0, fontSize: '0.88rem', lineHeight: '1.55', color: 'var(--text-primary)', fontStyle: 'italic' }}>&ldquo;{p.text}&rdquo;</p>
                        {p.ref && <span style={{ marginTop: '6px', display: 'block', fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: '600' }}>{p.ref}</span>}
                      </div>
                    ))}
                  </div>
                </div>

                {/* ── AÇÕES ── */}
                <div style={{ padding: '0 20px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  <button className="btn-primary" onClick={() => handleGenerateCard('share')} disabled={cardGenerating}
                    style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '10px', padding: '16px', fontSize: '1rem', fontWeight: '700', borderRadius: '14px' }}
                  >
                    {cardGenerating
                      ? <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ animation: 'spin 1s linear infinite' }}><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg>
                      : <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/></svg>
                    }
                    {cardGenerating ? 'Gerando...' : 'Compartilhar no WhatsApp / Redes'}
                  </button>
                  <button className="btn-secondary" onClick={() => handleGenerateCard('download')} disabled={cardGenerating}
                    style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '10px', padding: '14px', fontSize: '0.92rem', fontWeight: '600', borderRadius: '14px' }}
                  >
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                    Baixar Imagem PNG
                  </button>
                </div>

              </div>
            </div>
          );
        })()}

        {/* ════════════ ABA ARCADE BÍBLICO ════════════ */}
        {activeTab === 'arcade' && (
          <div className="page-enter" style={{ padding: '20px', paddingBottom: '40px' }}>
            {arcadeActiveGame === 'lobby' && (
              <>
                {/* Cabeçalho do Arcade com ChaminhaCoin */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px', background: 'rgba(255,255,255,0.03)', padding: '16px', borderRadius: '16px', border: '1px solid rgba(255,255,255,0.05)' }}>
                  <div>
                    <h2 style={{ margin: 0, fontSize: '1.2rem', color: 'var(--text-primary)' }}>Seu Progresso</h2>
                    <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Divirta-se e aprenda!</span>
                  </div>
                  <div style={{ display: 'flex', gap: '12px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', background: 'rgba(249,115,22,0.1)', padding: '6px 12px', borderRadius: '12px', border: '1px solid rgba(249,115,22,0.2)' }}>
                      <ChaminhaCoin size={20} />
                      <strong style={{ color: 'var(--orange)', fontSize: '1.1rem' }}>{userCoins}</strong>
                    </div>
                  </div>
                </div>

                {/* Chaminha no lobby de jogos com layout horizontal */}
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '16px', marginBottom: '32px', padding: '0 12px' }}>
                  <ChaminhaVideo size={80} style={{ flexShrink: 0 }} />
                  <div className="glass-panel animate-fade-in" style={{
                    padding: '12px 18px',
                    borderRadius: '16px',
                    fontSize: '0.9rem',
                    color: 'var(--text-secondary)',
                    border: '1px solid rgba(255, 255, 255, 0.08)',
                    position: 'relative',
                    maxWidth: '360px',
                    background: 'rgba(255, 255, 255, 0.02)'
                  }}>
                    <div style={{
                      position: 'absolute', top: '50%', left: '-6px', transform: 'translateY(-50%) rotate(45deg)',
                      width: '10px', height: '10px', background: 'var(--bg-app)', borderLeft: '1px solid rgba(255, 255, 255, 0.08)',
                      borderBottom: '1px solid rgba(255, 255, 255, 0.08)', zIndex: 1
                    }} />
                    🎮 <strong>Chaminha:</strong> "Vamos testar sua sabedoria? Escolha um jogo abaixo e ganhe muitas Chaminhas!"
                  </div>
                </div>

                {/* Lista de Jogos */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '16px' }}>
                  
                  <div className="glass-panel" onClick={() => { setArcadeSelectedGame('quiz'); setArcadeActiveGame('difficulty'); }} style={{ cursor: 'pointer', display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center', padding: '24px 16px', gap: '12px', transition: 'transform 0.2s' }} onMouseOver={e => e.currentTarget.style.transform = 'scale(1.05)'} onMouseOut={e => e.currentTarget.style.transform = 'scale(1)'}>
                    <div style={{ width: '64px', height: '64px', borderRadius: '20px', background: 'linear-gradient(135deg, #4f46e5, #7c3aed)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '8px', boxShadow: '0 8px 16px rgba(124, 58, 237, 0.3)' }}>
                      <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
                    </div>
                    <div>
                      <h3 style={{ margin: 0, fontSize: '1.1rem', color: 'var(--text-primary)' }}>Quiz Bíblico</h3>
                      <p style={{ margin: '6px 0 0', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Teste seus conhecimentos</p>
                    </div>
                    <div style={{ color: 'var(--orange)', fontWeight: 'bold', fontSize: '0.9rem', marginTop: '4px', background: 'rgba(249,115,22,0.1)', padding: '4px 12px', borderRadius: '12px' }}>JOGAR</div>
                  </div>

                  <div className="glass-panel" onClick={() => { setArcadeSelectedGame('cacapalavras'); setArcadeActiveGame('difficulty'); }} style={{ cursor: 'pointer', display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center', padding: '24px 16px', gap: '12px', transition: 'transform 0.2s' }} onMouseOver={e => e.currentTarget.style.transform = 'scale(1.05)'} onMouseOut={e => e.currentTarget.style.transform = 'scale(1)'}>
                    <div style={{ width: '64px', height: '64px', borderRadius: '20px', background: 'linear-gradient(135deg, #059669, #10b981)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '8px', boxShadow: '0 8px 16px rgba(5, 150, 105, 0.3)' }}>
                      <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/><line x1="11" y1="8" x2="11" y2="14"/><line x1="8" y1="11" x2="14" y2="11"/></svg>
                    </div>
                    <div>
                      <h3 style={{ margin: 0, fontSize: '1.1rem', color: 'var(--text-primary)' }}>Caça Palavras</h3>
                      <p style={{ margin: '6px 0 0', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Encontre os termos</p>
                    </div>
                    <div style={{ color: 'var(--orange)', fontWeight: 'bold', fontSize: '0.9rem', marginTop: '4px', background: 'rgba(249,115,22,0.1)', padding: '4px 12px', borderRadius: '12px' }}>JOGAR</div>
                  </div>

                  <div className="glass-panel" onClick={() => { setArcadeSelectedGame('charadas'); setArcadeActiveGame('difficulty'); }} style={{ cursor: 'pointer', display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center', padding: '24px 16px', gap: '12px', transition: 'transform 0.2s' }} onMouseOver={e => e.currentTarget.style.transform = 'scale(1.05)'} onMouseOut={e => e.currentTarget.style.transform = 'scale(1)'}>
                    <div style={{ width: '64px', height: '64px', borderRadius: '20px', background: 'linear-gradient(135deg, #db2777, #f43f5e)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '8px', boxShadow: '0 8px 16px rgba(219, 39, 119, 0.3)' }}>
                      <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
                    </div>
                    <div>
                      <h3 style={{ margin: 0, fontSize: '1.1rem', color: 'var(--text-primary)' }}>Quem Sou Eu?</h3>
                      <p style={{ margin: '6px 0 0', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Adivinhe o personagem</p>
                    </div>
                    <div style={{ color: 'var(--orange)', fontWeight: 'bold', fontSize: '0.9rem', marginTop: '4px', background: 'rgba(249,115,22,0.1)', padding: '4px 12px', borderRadius: '12px' }}>JOGAR</div>
                  </div>

                  <div className="glass-panel" onClick={() => { setArcadeSelectedGame('forca'); setArcadeActiveGame('difficulty'); }} style={{ cursor: 'pointer', display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center', padding: '24px 16px', gap: '12px', transition: 'transform 0.2s' }} onMouseOver={e => e.currentTarget.style.transform = 'scale(1.05)'} onMouseOut={e => e.currentTarget.style.transform = 'scale(1)'}>
                    <div style={{ width: '64px', height: '64px', borderRadius: '20px', background: 'linear-gradient(135deg, #d97706, #f59e0b)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '8px', boxShadow: '0 8px 16px rgba(217, 119, 6, 0.3)' }}>
                      <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M4 22h14"/><path d="M9 22V2"/><path d="M9 2h6"/><path d="M15 2v4"/><circle cx="15" cy="8" r="2"/></svg>
                    </div>
                    <div>
                      <h3 style={{ margin: 0, fontSize: '1.1rem', color: 'var(--text-primary)' }}>Forca Bíblica</h3>
                      <p style={{ margin: '6px 0 0', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Adivinhe a palavra</p>
                    </div>
                    <div style={{ color: 'var(--orange)', fontWeight: 'bold', fontSize: '0.9rem', marginTop: '4px', background: 'rgba(249,115,22,0.1)', padding: '4px 12px', borderRadius: '12px' }}>JOGAR</div>
                  </div>

                </div>
              </>
            )}

            {arcadeActiveGame === 'difficulty' && (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', gap: '24px', padding: '24px' }}>
                <h2 style={{ color: 'var(--orange)', fontSize: '1.5rem', marginBottom: '8px' }}>Selecione a Dificuldade</h2>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', width: '100%', maxWidth: '300px' }}>
                  
                  {/* FÁCIL */}
                  <button onClick={() => {
                    setArcadeDifficulty('facil');
                    if (arcadeSelectedGame === 'quiz') {
                      setArcadeQuizList(ARCADE_QUIZ_QUESTIONS.filter(q => q.difficulty === 'facil').sort(() => Math.random() - 0.5));
                      setArcadeQuizTimer(30);
                      setArcadeQuizCurrentQuestion(0); setArcadeQuizScore(0); setArcadeQuizGameOver(false); setArcadeQuizFeedback(null);
                    } else if (arcadeSelectedGame === 'cacapalavras') {
                      const filtered = ARCADE_CACA_PALAVRAS_LIST.filter(q => q.difficulty === 'facil');
                      const { grid, words } = generateCacaPalavrasGrid(filtered, 10, 5);
                      setArcadeCacaGrade(grid); setArcadeCacaWords(words); setArcadeCacaFound([]); setArcadeCacaSelected([]); setArcadeCacaScore(0); setArcadeCacaGameOver(false);
                    } else if (arcadeSelectedGame === 'charadas') {
                      setArcadeCharadasList(ARCADE_CHARADAS_QUESTIONS.filter(q => q.difficulty === 'facil').sort(() => Math.random() - 0.5));
                      setArcadeCharadasTimer(null);
                      setArcadeCharadasCurrent(0); setArcadeCharadasScore(0); setArcadeCharadasGameOver(false); setArcadeCharadasFeedback(null);
                    } else if (arcadeSelectedGame === 'forca') {
                      setArcadeForcaList(ARCADE_FORCA_WORDS.filter(q => q.difficulty === 'facil').sort(() => Math.random() - 0.5));
                      setArcadeForcaCurrent(0); setArcadeForcaScore(0); setArcadeForcaGameOver(false); setArcadeForcaGuesses([]); setArcadeForcaMistakes(0); setArcadeForcaFeedback(null);
                    }
                    setArcadeActiveGame(arcadeSelectedGame);
                  }} style={{ background: 'rgba(16,185,129,0.2)', border: '1px solid #10b981', color: '#fff', padding: '16px', borderRadius: '12px', fontSize: '1.1rem', cursor: 'pointer', transition: 'background 0.2s' }} onMouseOver={e => e.currentTarget.style.background = 'rgba(16,185,129,0.4)'} onMouseOut={e => e.currentTarget.style.background = 'rgba(16,185,129,0.2)'}>
                    🌟 Fácil
                  </button>

                  {/* MÉDIO */}
                  <button onClick={() => {
                    setArcadeDifficulty('medio');
                    if (arcadeSelectedGame === 'quiz') {
                      setArcadeQuizList(ARCADE_QUIZ_QUESTIONS.filter(q => q.difficulty === 'medio').sort(() => Math.random() - 0.5));
                      setArcadeQuizTimer(15);
                      setArcadeQuizCurrentQuestion(0); setArcadeQuizScore(0); setArcadeQuizGameOver(false); setArcadeQuizFeedback(null);
                    } else if (arcadeSelectedGame === 'cacapalavras') {
                      const filtered = ARCADE_CACA_PALAVRAS_LIST.filter(q => q.difficulty === 'medio');
                      const { grid, words } = generateCacaPalavrasGrid(filtered, 12, 6);
                      setArcadeCacaGrade(grid); setArcadeCacaWords(words); setArcadeCacaFound([]); setArcadeCacaSelected([]); setArcadeCacaScore(0); setArcadeCacaGameOver(false);
                    } else if (arcadeSelectedGame === 'charadas') {
                      setArcadeCharadasList(ARCADE_CHARADAS_QUESTIONS.filter(q => q.difficulty === 'medio').sort(() => Math.random() - 0.5));
                      setArcadeCharadasTimer(15);
                      setArcadeCharadasCurrent(0); setArcadeCharadasScore(0); setArcadeCharadasGameOver(false); setArcadeCharadasFeedback(null);
                    } else if (arcadeSelectedGame === 'forca') {
                      setArcadeForcaList(ARCADE_FORCA_WORDS.filter(q => q.difficulty === 'medio').sort(() => Math.random() - 0.5));
                      setArcadeForcaCurrent(0); setArcadeForcaScore(0); setArcadeForcaGameOver(false); setArcadeForcaGuesses([]); setArcadeForcaMistakes(0); setArcadeForcaFeedback(null);
                    }
                    setArcadeActiveGame(arcadeSelectedGame);
                  }} style={{ background: 'rgba(245,158,11,0.2)', border: '1px solid #f59e0b', color: '#fff', padding: '16px', borderRadius: '12px', fontSize: '1.1rem', cursor: 'pointer', transition: 'background 0.2s' }} onMouseOver={e => e.currentTarget.style.background = 'rgba(245,158,11,0.4)'} onMouseOut={e => e.currentTarget.style.background = 'rgba(245,158,11,0.2)'}>
                    ⭐ Médio
                  </button>

                  {/* AVANÇADO */}
                  <button onClick={() => {
                    setArcadeDifficulty('avancado');
                    if (arcadeSelectedGame === 'quiz') {
                      setArcadeQuizList(ARCADE_QUIZ_QUESTIONS.filter(q => q.difficulty === 'avancado').sort(() => Math.random() - 0.5));
                      setArcadeQuizTimer(7);
                      setArcadeQuizCurrentQuestion(0); setArcadeQuizScore(0); setArcadeQuizGameOver(false); setArcadeQuizFeedback(null);
                    } else if (arcadeSelectedGame === 'cacapalavras') {
                      const filtered = ARCADE_CACA_PALAVRAS_LIST.filter(q => q.difficulty === 'avancado');
                      const { grid, words } = generateCacaPalavrasGrid(filtered, 14, 8);
                      setArcadeCacaGrade(grid); setArcadeCacaWords(words); setArcadeCacaFound([]); setArcadeCacaSelected([]); setArcadeCacaScore(0); setArcadeCacaGameOver(false);
                    } else if (arcadeSelectedGame === 'charadas') {
                      setArcadeCharadasList(ARCADE_CHARADAS_QUESTIONS.filter(q => q.difficulty === 'avancado').sort(() => Math.random() - 0.5));
                      setArcadeCharadasTimer(7);
                      setArcadeCharadasCurrent(0); setArcadeCharadasScore(0); setArcadeCharadasGameOver(false); setArcadeCharadasFeedback(null);
                    } else if (arcadeSelectedGame === 'forca') {
                      setArcadeForcaList(ARCADE_FORCA_WORDS.filter(q => q.difficulty === 'avancado').sort(() => Math.random() - 0.5));
                      setArcadeForcaCurrent(0); setArcadeForcaScore(0); setArcadeForcaGameOver(false); setArcadeForcaGuesses([]); setArcadeForcaMistakes(0); setArcadeForcaFeedback(null);
                    }
                    setArcadeActiveGame(arcadeSelectedGame);
                  }} style={{ background: 'rgba(239,68,68,0.2)', border: '1px solid #ef4444', color: '#fff', padding: '16px', borderRadius: '12px', fontSize: '1.1rem', cursor: 'pointer', transition: 'background 0.2s' }} onMouseOver={e => e.currentTarget.style.background = 'rgba(239,68,68,0.4)'} onMouseOut={e => e.currentTarget.style.background = 'rgba(239,68,68,0.2)'}>
                    🔥 Avançado (2x Recompensas)
                  </button>
                </div>
                <button onClick={() => setArcadeActiveGame('lobby')} style={{ background: 'transparent', border: 'none', color: 'var(--text-secondary)', marginTop: '16px', cursor: 'pointer', textDecoration: 'underline' }}>
                  Voltar
                </button>
              </div>
            )}

            {arcadeActiveGame === 'quiz' && (() => {
              const q = arcadeQuizList[arcadeQuizCurrentQuestion];
              
              const handleAnswer = (index) => {
                if (arcadeQuizFeedback) return;
                
                if (index === q.answer) {
                  setArcadeQuizFeedback('correct');
                  setArcadeQuizScore(prev => prev + 10 + arcadeQuizTimer);
                  setUserCoins(prev => {
                    const multiplier = arcadeDifficulty === 'avancado' ? 2 : 1;
                    const newCoins = prev + (5 * multiplier);
                    localStorage.setItem('app-coins', newCoins);
                    return newCoins;
                  });
                } else {
                  setArcadeQuizFeedback('wrong');
                }
                
                setTimeout(() => {
                  setArcadeQuizFeedback(null);
                  const resetTime = arcadeDifficulty === 'facil' ? 30 : (arcadeDifficulty === 'avancado' ? 7 : 15);
                  setArcadeQuizTimer(resetTime);
                  if (arcadeQuizCurrentQuestion + 1 < arcadeQuizList.length) {
                    setArcadeQuizCurrentQuestion(prev => prev + 1);
                  } else {
                    setArcadeQuizGameOver(true);
                  }
                }, 2000);
              };

              if (arcadeQuizGameOver) {
                return (
                  <div style={{ textAlign: 'center', paddingTop: '40px' }}>
                    <div style={{ fontSize: '4rem', marginBottom: '16px' }}>🏆</div>
                    <h2 style={{ fontSize: '1.8rem', margin: '0 0 8px', color: 'var(--orange)' }}>Quiz Concluído!</h2>
                    <p style={{ color: 'var(--text-secondary)', fontSize: '1rem', marginBottom: '30px' }}>Sua pontuação: <strong style={{ color: '#fff' }}>{arcadeQuizScore}</strong></p>
                    
                    <button className="btn-primary" onClick={() => {
                      setArcadeActiveGame('lobby');
                      setArcadeQuizCurrentQuestion(0);
                      setArcadeQuizScore(0);
                      setArcadeQuizGameOver(false);
                      const resetTime = arcadeDifficulty === 'facil' ? 30 : (arcadeDifficulty === 'avancado' ? 7 : 15);
                      setArcadeQuizTimer(resetTime);
                    }} style={{ padding: '16px 32px', fontSize: '1.1rem', borderRadius: '12px', width: '100%' }}>
                      Voltar ao Lobby
                    </button>
                  </div>
                );
              }

              return (
                <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
                  {/* Header do Jogo */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
                    <button onClick={() => setArcadeActiveGame('lobby')} style={{ background: 'rgba(255,255,255,0.1)', border: 'none', color: '#fff', width: '40px', height: '40px', borderRadius: '50%', cursor: 'pointer', fontSize: '1.2rem', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>←</button>
                    <div style={{ display: 'flex', gap: '16px' }}>
                      <div style={{ fontWeight: 'bold', color: 'var(--orange)', background: 'rgba(249,115,22,0.1)', padding: '6px 12px', borderRadius: '20px' }}>⭐ {arcadeQuizScore}</div>
                      <div style={{ fontWeight: 'bold', color: '#10b981', background: 'rgba(16,185,129,0.1)', padding: '6px 12px', borderRadius: '20px' }}>⏱️ {arcadeQuizTimer}s</div>
                    </div>
                  </div>

                  {/* Pergunta */}
                  <div className="glass-panel" style={{ padding: '30px 20px', textAlign: 'center', marginBottom: '24px' }}>
                    <div style={{ fontSize: '0.85rem', color: 'var(--orange)', fontWeight: 'bold', marginBottom: '12px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Pergunta {arcadeQuizCurrentQuestion + 1} de {arcadeQuizList.length}</div>
                    <h3 style={{ margin: 0, fontSize: '1.3rem', lineHeight: '1.4', color: 'var(--text-primary)' }}>{q?.question}</h3>
                  </div>

                  {/* Alternativas */}
                  <div style={{ display: 'grid', gap: '12px' }}>
                    {q?.options.map((opt, idx) => {
                      let bgColor = 'rgba(255,255,255,0.05)';
                      let borderColor = 'rgba(255,255,255,0.1)';
                      
                      if (arcadeQuizFeedback) {
                        if (idx === q.answer) {
                          bgColor = 'rgba(16,185,129,0.2)'; // verde (correto)
                          borderColor = '#10b981';
                        } else if (arcadeQuizFeedback === 'wrong' && idx !== q.answer) {
                          bgColor = 'rgba(239,68,68,0.1)'; // vermelho (errado)
                        }
                      }

                      return (
                        <button key={idx} onClick={() => handleAnswer(idx)} disabled={!!arcadeQuizFeedback}
                          style={{
                            background: bgColor,
                            border: `2px solid ${borderColor}`,
                            padding: '18px 20px',
                            borderRadius: '16px',
                            color: 'var(--text-primary)',
                            fontSize: '1.05rem',
                            fontWeight: '600',
                            textAlign: 'left',
                            cursor: arcadeQuizFeedback ? 'default' : 'pointer',
                            transition: 'all 0.2s'
                          }}
                        >
                          {opt}
                        </button>
                      );
                    })}
                  </div>
                </div>
              );
            })()}

            {arcadeActiveGame === 'charadas' && (() => {
              const q = arcadeCharadasList[arcadeCharadasCurrent];
              
              const handleAnswer = (index) => {
                if (arcadeCharadasFeedback) return;
                
                if (index === q.answer) {
                  setArcadeCharadasFeedback('correct');
                  setArcadeCharadasScore(prev => prev + 15); // Mais pontos por ser mais difícil
                  setUserCoins(prev => {
                    const multiplier = arcadeDifficulty === 'avancado' ? 2 : 1;
                    const newCoins = prev + (10 * multiplier);
                    localStorage.setItem('app-coins', newCoins);
                    return newCoins;
                  });
                } else {
                  setArcadeCharadasFeedback('wrong');
                }
                
                setTimeout(() => {
                  setArcadeCharadasFeedback(null);
                  if (arcadeCharadasCurrent + 1 < arcadeCharadasList.length) {
                    setArcadeCharadasCurrent(prev => prev + 1);
                    const resetTime = arcadeDifficulty === 'facil' ? null : (arcadeDifficulty === 'avancado' ? 7 : 15);
                    setArcadeCharadasTimer(resetTime);
                  } else {
                    setArcadeCharadasGameOver(true);
                  }
                }, 2000);
              };

              if (arcadeCharadasGameOver) {
                return (
                  <div style={{ textAlign: 'center', paddingTop: '40px' }}>
                    <div style={{ fontSize: '4rem', marginBottom: '16px' }}>🎭</div>
                    <h2 style={{ fontSize: '1.8rem', margin: '0 0 8px', color: 'var(--orange)' }}>Fim do Jogo!</h2>
                    <p style={{ color: 'var(--text-secondary)', fontSize: '1rem', marginBottom: '30px' }}>Sua pontuação: <strong style={{ color: '#fff' }}>{arcadeCharadasScore}</strong></p>
                    
                    <button className="btn-primary" onClick={() => {
                      setArcadeActiveGame('lobby');
                      setArcadeCharadasCurrent(0);
                      setArcadeCharadasScore(0);
                      setArcadeCharadasGameOver(false);
                    }} style={{ padding: '16px 32px', fontSize: '1.1rem', borderRadius: '12px', width: '100%' }}>
                      Voltar ao Lobby
                    </button>
                  </div>
                );
              }

              return (
                <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
                  {/* Header do Jogo */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
                    <button onClick={() => setArcadeActiveGame('lobby')} style={{ background: 'rgba(255,255,255,0.1)', border: 'none', color: '#fff', width: '40px', height: '40px', borderRadius: '50%', cursor: 'pointer', fontSize: '1.2rem', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>←</button>
                    <div style={{ display: 'flex', gap: '16px' }}>
                      {arcadeCharadasTimer !== null && (
                        <div style={{ fontWeight: 'bold', color: arcadeCharadasTimer <= 3 ? '#ef4444' : '#fff', background: 'rgba(255,255,255,0.1)', padding: '6px 12px', borderRadius: '20px', transition: 'color 0.3s' }}>
                          ⏱ {arcadeCharadasTimer}s
                        </div>
                      )}
                      <div style={{ fontWeight: 'bold', color: 'var(--orange)', background: 'rgba(249,115,22,0.1)', padding: '6px 12px', borderRadius: '20px' }}>⭐ {arcadeCharadasScore}</div>
                    </div>
                  </div>

                  {/* Dicas */}
                  <div className="glass-panel" style={{ padding: '30px 20px', textAlign: 'left', marginBottom: '24px', position: 'relative', overflow: 'hidden' }}>
                    <div style={{ position: 'absolute', top: -20, right: -20, fontSize: '6rem', opacity: 0.05, transform: 'rotate(15deg)' }}>🤔</div>
                    <div style={{ fontSize: '0.85rem', color: 'var(--orange)', fontWeight: 'bold', marginBottom: '16px', textTransform: 'uppercase', letterSpacing: '0.05em', textAlign: 'center' }}>Quem Sou Eu? ({arcadeCharadasCurrent + 1}/{arcadeCharadasList.length})</div>
                    
                    <ul style={{ margin: 0, paddingLeft: '20px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                      {q?.clues.map((clue, idx) => (
                        <li key={idx} style={{ fontSize: '1.1rem', color: 'var(--text-primary)', lineHeight: '1.4' }}>{clue}</li>
                      ))}
                    </ul>
                  </div>

                  {/* Alternativas */}
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px' }}>
                    {q?.options.map((opt, idx) => {
                      let bgColor = 'rgba(255,255,255,0.05)';
                      let borderColor = 'rgba(255,255,255,0.1)';
                      
                      if (arcadeCharadasFeedback) {
                        if (idx === q.answer) {
                          bgColor = 'rgba(16,185,129,0.2)'; // verde
                          borderColor = '#10b981';
                        } else if (arcadeCharadasFeedback === 'wrong' && idx !== q.answer) {
                          bgColor = 'rgba(239,68,68,0.1)'; // vermelho
                        }
                      }

                      return (
                        <button key={idx} onClick={() => handleAnswer(idx)} disabled={!!arcadeCharadasFeedback}
                          style={{
                            background: bgColor,
                            border: `2px solid ${borderColor}`,
                            padding: '16px',
                            borderRadius: '16px',
                            color: 'var(--text-primary)',
                            fontSize: '1rem',
                            fontWeight: '600',
                            textAlign: 'center',
                            cursor: arcadeCharadasFeedback ? 'default' : 'pointer',
                            transition: 'all 0.2s'
                          }}
                        >
                          {opt}
                        </button>
                      );
                    })}
                  </div>
                </div>
              );
            })()}

            {arcadeActiveGame === 'forca' && (() => {
              const currentWordObj = arcadeForcaList[arcadeForcaCurrent];
              const word = currentWordObj ? currentWordObj.word.toUpperCase() : '';
              
              // Verifica se a palavra inteira já foi adivinhada
              const isWordGuessed = word && word.split('').every(char => char === ' ' || arcadeForcaGuesses.includes(char));
              const ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ".split('');
              
              const maxMistakes = arcadeDifficulty === 'facil' ? 8 : (arcadeDifficulty === 'avancado' ? 4 : 6);

              const handleGuess = (letter) => {
                if (arcadeForcaFeedback || arcadeForcaGuesses.includes(letter)) return;
                
                const newGuesses = [...arcadeForcaGuesses, letter];
                setArcadeForcaGuesses(newGuesses);
                
                if (!word.includes(letter)) {
                  setArcadeForcaMistakes(prev => {
                    const newMistakes = prev + 1;
                    // Verifica se perdeu após esta tentativa
                    if (newMistakes >= maxMistakes) {
                      setTimeout(() => setArcadeForcaFeedback('lost'), 600);
                    }
                    return newMistakes;
                  });
                } else {
                  // Verifica se ganhou após esta tentativa
                  const updatedWord = word.split('');
                  const willBeGuessed = updatedWord.every(char => char === ' ' || newGuesses.includes(char));
                  if (willBeGuessed) {
                    setTimeout(() => setArcadeForcaFeedback('won'), 600);
                  }
                }
              };

              const handleNextWord = () => {
                if (arcadeForcaFeedback === 'won') {
                  setArcadeForcaScore(prev => prev + 20); // 20 pontos por acertar a palavra
                  setUserCoins(prev => {
                    const multiplier = arcadeDifficulty === 'avancado' ? 2 : 1;
                    const newCoins = prev + (15 * multiplier);
                    localStorage.setItem('app-coins', newCoins);
                    return newCoins;
                  });
                }
                
                if (arcadeForcaCurrent + 1 < arcadeForcaList.length) {
                  setArcadeForcaCurrent(prev => prev + 1);
                  setArcadeForcaGuesses([]);
                  setArcadeForcaMistakes(0);
                  setArcadeForcaFeedback(null);
                } else {
                  setArcadeForcaGameOver(true);
                }
              };

              if (arcadeForcaGameOver) {
                return (
                  <div style={{ textAlign: 'center', paddingTop: '40px' }}>
                    <div style={{ fontSize: '4rem', marginBottom: '16px' }}>🏆</div>
                    <h2 style={{ fontSize: '1.8rem', margin: '0 0 8px', color: 'var(--orange)' }}>Fim do Jogo!</h2>
                    <p style={{ color: 'var(--text-secondary)', fontSize: '1rem', marginBottom: '30px' }}>Sua pontuação final: <strong style={{ color: '#fff' }}>{arcadeForcaScore}</strong></p>
                    
                    <button className="btn-primary" onClick={() => {
                      setArcadeActiveGame('lobby');
                      setArcadeForcaCurrent(0);
                      setArcadeForcaScore(0);
                      setArcadeForcaGameOver(false);
                      setArcadeForcaGuesses([]);
                      setArcadeForcaMistakes(0);
                      setArcadeForcaFeedback(null);
                    }} style={{ padding: '16px 32px', fontSize: '1.1rem', borderRadius: '12px', width: '100%' }}>
                      Voltar ao Lobby
                    </button>
                  </div>
                );
              }

              return (
                <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
                  {/* Header do Jogo */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
                    <button onClick={() => setArcadeActiveGame('lobby')} style={{ background: 'rgba(255,255,255,0.1)', border: 'none', color: '#fff', width: '40px', height: '40px', borderRadius: '50%', cursor: 'pointer', fontSize: '1.2rem', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>←</button>
                    <div style={{ display: 'flex', gap: '16px' }}>
                      <div style={{ fontWeight: 'bold', color: 'var(--orange)', background: 'rgba(249,115,22,0.1)', padding: '6px 12px', borderRadius: '20px' }}>⭐ {arcadeForcaScore}</div>
                      <div style={{ fontWeight: 'bold', color: '#ef4444', background: 'rgba(239,68,68,0.1)', padding: '6px 12px', borderRadius: '20px' }}>❤️ {maxMistakes - arcadeForcaMistakes}</div>
                    </div>
                  </div>

                  {/* Dica */}
                  <div className="glass-panel" style={{ padding: '20px', textAlign: 'center', marginBottom: '24px' }}>
                    <div style={{ fontSize: '0.85rem', color: 'var(--orange)', fontWeight: 'bold', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Dica da Palavra</div>
                    <h3 style={{ margin: 0, fontSize: '1.2rem', color: 'var(--text-primary)' }}>"{currentWordObj?.tip}"</h3>
                  </div>

                  {/* Palavra Oculta */}
                  <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'center', gap: '8px', marginBottom: '32px' }}>
                    {word.split('').map((char, idx) => {
                      if (char === ' ') return <div key={idx} style={{ width: '100%', height: '8px' }}></div>;
                      const isRevealed = arcadeForcaGuesses.includes(char) || arcadeForcaFeedback === 'lost';
                      const isMissed = arcadeForcaFeedback === 'lost' && !arcadeForcaGuesses.includes(char);
                      
                      return (
                        <div key={idx} style={{
                          width: '40px', height: '50px', borderBottom: '3px solid var(--text-primary)',
                          display: 'flex', alignItems: 'flex-end', justifyContent: 'center',
                          fontSize: '1.8rem', fontWeight: 'bold', paddingBottom: '4px',
                          color: isMissed ? '#ef4444' : 'var(--text-primary)'
                        }}>
                          {isRevealed ? char : ''}
                        </div>
                      );
                    })}
                  </div>

                  {/* Feedback Modal / Overlay */}
                  {arcadeForcaFeedback && (
                    <div style={{ background: arcadeForcaFeedback === 'won' ? 'rgba(16,185,129,0.15)' : 'rgba(239,68,68,0.15)', border: `2px solid ${arcadeForcaFeedback === 'won' ? '#10b981' : '#ef4444'}`, borderRadius: '16px', padding: '20px', textAlign: 'center', marginBottom: '24px' }}>
                      <h3 style={{ margin: '0 0 12px', color: arcadeForcaFeedback === 'won' ? '#10b981' : '#ef4444', fontSize: '1.4rem' }}>
                        {arcadeForcaFeedback === 'won' ? 'Você Acertou! 🎉' : 'Você Perdeu! 😢'}
                      </h3>
                      <button className="btn-primary" onClick={handleNextWord} style={{ padding: '12px 24px', fontSize: '1rem', borderRadius: '12px' }}>
                        Próxima Palavra ➔
                      </button>
                    </div>
                  )}

                  {/* Teclado Virtual */}
                  {!arcadeForcaFeedback && (
                    <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'center', gap: '6px' }}>
                      {ALPHABET.map((letter) => {
                        const isGuessed = arcadeForcaGuesses.includes(letter);
                        const isCorrect = isGuessed && word.includes(letter);
                        const isWrong = isGuessed && !word.includes(letter);
                        
                        let bgColor = 'rgba(255,255,255,0.08)';
                        let borderColor = 'rgba(255,255,255,0.1)';
                        let opacity = 1;
                        
                        if (isCorrect) {
                          bgColor = 'rgba(16,185,129,0.2)';
                          borderColor = '#10b981';
                        } else if (isWrong) {
                          bgColor = 'rgba(239,68,68,0.1)';
                          borderColor = '#ef4444';
                          opacity = 0.5;
                        }

                        return (
                          <button key={letter} onClick={() => handleGuess(letter)} disabled={isGuessed}
                            style={{
                              width: '42px', height: '48px', borderRadius: '10px',
                              background: bgColor, border: `1px solid ${borderColor}`,
                              color: '#fff', fontSize: '1.1rem', fontWeight: 'bold',
                              cursor: isGuessed ? 'default' : 'pointer', opacity,
                              display: 'flex', alignItems: 'center', justifyContent: 'center'
                            }}
                          >
                            {letter}
                          </button>
                        );
                      })}
                    </div>
                  )}
                </div>
              );
            })()}

            {arcadeActiveGame === 'cacapalavras' && (() => {
              const size = Math.sqrt(arcadeCacaGrade.length) || 10;
              
              const handleLetterClick = (id, r, c, char) => {
                if (arcadeCacaGameOver) return;
                
                let newSelected = [...arcadeCacaSelected];
                
                // Se já tem duas selecionadas, reseta e começa nova seleção
                if (newSelected.length === 2) {
                  newSelected = [{ id, r, c, char }];
                } else if (newSelected.length === 1) {
                  // Segundo clique - tenta fechar a palavra
                  newSelected.push({ id, r, c, char });
                  
                  // Verifica se forma reta
                  const first = newSelected[0];
                  const second = newSelected[1];
                  
                  const rDiff = second.r - first.r;
                  const cDiff = second.c - first.c;
                  
                  // Deve ser horizontal, vertical ou diagonal
                  const absR = Math.abs(rDiff);
                  const absC = Math.abs(cDiff);
                  if (first.r === second.r || first.c === second.c || absR === absC) {
                    const stepR = rDiff === 0 ? 0 : rDiff / Math.abs(rDiff);
                    const stepC = cDiff === 0 ? 0 : cDiff / Math.abs(cDiff);
                    
                    const length = Math.max(Math.abs(rDiff), Math.abs(cDiff)) + 1;
                    
                    let formedWord = "";
                    const formedIndices = [];
                    
                    for (let i = 0; i < length; i++) {
                      const currR = first.r + (i * stepR);
                      const currC = first.c + (i * stepC);
                      const cell = arcadeCacaGrade.find(c => c.r === currR && c.c === currC);
                      if (cell) {
                        formedWord += cell.char;
                        formedIndices.push(cell.id);
                      }
                    }
                    
                    // Checa se a palavra (ou o reverso dela) está na lista
                    const normalize = s => s.toUpperCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
                    const wordObj = arcadeCacaWords.find(w => normalize(w.word) === formedWord || normalize(w.word) === formedWord.split('').reverse().join(''));
                    
                    if (wordObj && !wordObj.found) {
                      // Achou!
                      const newFound = [...arcadeCacaFound, ...formedIndices];
                      setArcadeCacaFound(newFound);
                      
                      const newWords = arcadeCacaWords.map(w => normalize(w.word) === normalize(wordObj.word) ? { ...w, found: true } : w);
                      setArcadeCacaWords(newWords);
                      
                      const allFound = newWords.every(w => w.found);
                      if (allFound) {
                        setArcadeCacaScore(prev => prev + 50); // 50 pontos bônus
                        setUserCoins(prev => {
                          const multiplier = arcadeDifficulty === 'avancado' ? 2 : 1;
                          const newCoins = prev + (50 * multiplier);
                          localStorage.setItem('app-coins', newCoins);
                          return newCoins;
                        });
                        setTimeout(() => setArcadeCacaGameOver(true), 1000);
                      }
                    }
                  }
                  
                  // Reseta seleção após tentar formar (com pequeno delay visual)
                  setTimeout(() => setArcadeCacaSelected([]), 400);
                } else {
                  // Primeiro clique
                  newSelected = [{ id, r, c, char }];
                }
                
                setArcadeCacaSelected(newSelected);
              };

              if (arcadeCacaGameOver) {
                return (
                  <div style={{ textAlign: 'center', paddingTop: '40px' }}>
                    <div style={{ fontSize: '4rem', marginBottom: '16px' }}>🏆</div>
                    <h2 style={{ fontSize: '1.8rem', margin: '0 0 8px', color: 'var(--orange)' }}>Parabéns!</h2>
                    <p style={{ color: 'var(--text-secondary)', fontSize: '1rem', marginBottom: '30px' }}>Você encontrou todas as palavras e ganhou <strong style={{ color: '#fff' }}>50 moedas</strong> bônus!</p>
                    
                    <button className="btn-primary" onClick={() => {
                      setArcadeActiveGame('lobby');
                      setArcadeCacaGrade([]);
                      setArcadeCacaWords([]);
                      setArcadeCacaFound([]);
                      setArcadeCacaSelected([]);
                      setArcadeCacaGameOver(false);
                    }} style={{ padding: '16px 32px', fontSize: '1.1rem', borderRadius: '12px', width: '100%' }}>
                      Voltar ao Lobby
                    </button>
                  </div>
                );
              }

              return (
                <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
                  {/* Header do Jogo */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
                    <button onClick={() => setArcadeActiveGame('lobby')} style={{ background: 'rgba(255,255,255,0.1)', border: 'none', color: '#fff', width: '40px', height: '40px', borderRadius: '50%', cursor: 'pointer', fontSize: '1.2rem', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>←</button>
                    <div style={{ display: 'flex', gap: '16px' }}>
                      <div style={{ fontWeight: 'bold', color: 'var(--orange)', background: 'rgba(249,115,22,0.1)', padding: '6px 12px', borderRadius: '20px' }}>⭐ {arcadeCacaWords.filter(w => w.found).length}/{arcadeCacaWords.length}</div>
                    </div>
                  </div>

                  {/* Instrução */}
                  <div style={{ textAlign: 'center', marginBottom: '16px', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                    Clique na primeira e depois na última letra de uma palavra para selecioná-la.
                  </div>

                  {/* Grade */}
                  <div style={{ 
                    display: 'grid', 
                    gridTemplateColumns: `repeat(${size}, 1fr)`, 
                    gap: '4px', 
                    background: 'rgba(0,0,0,0.2)', 
                    padding: '8px', 
                    borderRadius: '16px',
                    marginBottom: '24px'
                  }}>
                    {arcadeCacaGrade.map((cell) => {
                      const isFound = arcadeCacaFound.includes(cell.id);
                      const isSelected = arcadeCacaSelected.some(s => s.id === cell.id);
                      
                      let bgColor = 'rgba(255,255,255,0.05)';
                      let color = 'var(--text-secondary)';
                      let fontWeight = 'normal';
                      
                      if (isFound) {
                        bgColor = 'var(--orange)';
                        color = '#fff';
                        fontWeight = 'bold';
                      } else if (isSelected) {
                        bgColor = 'rgba(16,185,129,0.5)';
                        color = '#fff';
                      }

                      return (
                        <div 
                          key={cell.id} 
                          onClick={() => handleLetterClick(cell.id, cell.r, cell.c, cell.char)}
                          style={{
                            aspectRatio: '1',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            background: bgColor,
                            color,
                            fontWeight,
                            borderRadius: '8px',
                            cursor: 'pointer',
                            fontSize: '1.2rem',
                            userSelect: 'none'
                          }}
                        >
                          {cell.char}
                        </div>
                      );
                    })}
                  </div>

                  {/* Lista de Palavras */}
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '12px', justifyContent: 'center' }}>
                    {arcadeCacaWords.map((w, idx) => (
                      <div key={idx} style={{ 
                        padding: '6px 16px', 
                        borderRadius: '20px', 
                        background: w.found ? 'rgba(249,115,22,0.2)' : 'rgba(255,255,255,0.05)',
                        color: w.found ? 'var(--orange)' : 'var(--text-secondary)',
                        textDecoration: w.found ? 'line-through' : 'none',
                        fontWeight: w.found ? 'bold' : 'normal'
                      }}>
                        {w.word}
                      </div>
                    ))}
                  </div>
                </div>
              );
            })()}
          </div>
        )}

        {activeTab === 'trail' && (
          <div className="page-enter animate-fade-in" style={{ paddingBottom: '100px' }}>
            <TrailHome
              onBack={() => setActiveTab('dashboard')}
              userCoins={userCoins}
              setUserCoins={setUserCoins}
            />
          </div>
        )}

        {activeTab === 'lojinha' && (
          <div className="lojinha-container" style={{ padding: '24px', maxWidth: '800px', margin: '0 auto', paddingBottom: '100px' }}>
            
            {/* Chaminha no topo da lojinha com layout horizontal */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '16px', marginBottom: '32px', padding: '0 12px' }}>
              <ChaminhaVideo size={80} style={{ flexShrink: 0 }} />
              <div className="glass-panel animate-fade-in" style={{
                padding: '12px 18px',
                borderRadius: '16px',
                fontSize: '0.9rem',
                color: 'var(--text-secondary)',
                border: '1px solid rgba(255, 255, 255, 0.08)',
                position: 'relative',
                maxWidth: '360px',
                background: 'rgba(255, 255, 255, 0.02)'
              }}>
                <div style={{
                  position: 'absolute', top: '50%', left: '-6px', transform: 'translateY(-50%) rotate(45deg)',
                  width: '10px', height: '10px', background: 'var(--bg-app)', borderLeft: '1px solid rgba(255, 255, 255, 0.08)',
                  borderBottom: '1px solid rgba(255, 255, 255, 0.08)', zIndex: 1
                }} />
                🔥 <strong>Chaminha:</strong> "Bem-vindo à minha Lojinha! Use suas Chaminhas para liberar fundos lindos e fontes incríveis!"
              </div>
            </div>
            <div style={{ textAlign: 'center', marginBottom: '32px' }}>
              <h2 style={{ fontSize: '2rem', color: 'var(--orange)', marginBottom: '8px' }}>Lojinha 1Convite 🛒</h2>
              <p style={{ color: 'var(--text-secondary)' }}>Use suas moedas ganhas para desbloquear itens exclusivos para o Studio de Cards!</p>
              <div style={{ marginTop: '16px', display: 'inline-flex', alignItems: 'center', gap: '8px', background: 'rgba(245,158,11,0.15)', padding: '12px 24px', borderRadius: '30px', border: '1px solid var(--orange)' }}>
                <span style={{ fontSize: '1.2rem', color: 'var(--text-primary)' }}>Seu saldo:</span>
                <span style={{ display:'inline-flex', alignItems:'center', gap:'6px', fontSize:'1.5rem', fontWeight:'bold', color:'var(--orange)' }}><ChaminhaCoin size={28}/> {userCoins}</span>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))', gap: '12px' }}>
              {LOJINHA_ITEMS.map(item => {
                const isUnlocked = unlockedItems.includes(item.id);
                return (
                  <div key={item.id} style={{
                    background: 'rgba(255,255,255,0.03)',
                    border: isUnlocked ? '1px solid var(--orange)' : '1px solid rgba(255,255,255,0.1)',
                    borderRadius: '12px',
                    padding: '16px 10px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '8px',
                    transition: 'transform 0.2s',
                    position: 'relative',
                    overflow: 'hidden'
                  }}>
                    {isUnlocked && (
                      <div style={{ position: 'absolute', top: 6, right: 6, background: 'var(--orange)', color: '#fff', padding: '2px 8px', borderRadius: '8px', fontSize: '0.65rem', fontWeight: 'bold' }}>
                        ADQUIRIDO
                      </div>
                    )}
                    <div style={{ fontSize: '2.2rem', textAlign: 'center', marginTop: isUnlocked ? '10px' : '0' }}>{item.icon}</div>
                    <h3 style={{ fontSize: '0.95rem', margin: 0, textAlign: 'center', color: 'var(--text-primary)', fontWeight: 'bold' }}>{item.name}</h3>
                    <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', textAlign: 'center', flex: 1, margin: 0, lineHeight: '1.3' }}>{item.desc}</p>
                    
                    <button
                      onClick={() => {
                        if (isUnlocked) return;
                        if (userCoins >= item.price) {
                          setUserCoins(prev => {
                            const val = prev - item.price;
                            localStorage.setItem('app-coins', val);
                            return val;
                          });
                          setUnlockedItems(prev => {
                            const arr = [...prev, item.id];
                            localStorage.setItem('unlocked-items', JSON.stringify(arr));
                            return arr;
                          });
                          alert('Compra realizada com sucesso! O item já está disponível no Studio de Cards.');
                        } else {
                          alert('Moedas insuficientes! Jogue mais Arcade ou complete o Desafio do Dia para ganhar mais moedas.');
                        }
                      }}
                      disabled={isUnlocked}
                      style={{
                        marginTop: '8px',
                        width: '100%',
                        padding: '10px 6px',
                        borderRadius: '10px',
                        border: 'none',
                        background: isUnlocked ? 'rgba(255,255,255,0.1)' : (userCoins >= item.price ? 'var(--orange)' : 'rgba(255,255,255,0.05)'),
                        color: isUnlocked ? 'var(--text-secondary)' : (userCoins >= item.price ? '#fff' : 'var(--text-secondary)'),
                        fontWeight: 'bold',
                        fontSize: '0.8rem',
                        cursor: isUnlocked ? 'default' : (userCoins >= item.price ? 'pointer' : 'not-allowed'),
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '6px'
                      }}
                    >
                      {isUnlocked ? 'Já Possui' : <span style={{display:'inline-flex',alignItems:'center',gap:'4px'}}><ChaminhaCoin size={14}/> {item.price}</span>}
                    </button>
                  </div>
                );
              })}
            </div>
          </div>
        )}

      </main>
    </div>
  );
}

export default App;
