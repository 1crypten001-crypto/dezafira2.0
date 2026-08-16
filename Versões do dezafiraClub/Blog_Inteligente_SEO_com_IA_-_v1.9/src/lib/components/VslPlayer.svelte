<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { env } from '$env/dynamic/public';

  // Component Props (Svelte 5 runes style)
  let { 
    vslId = '', 
    src = '', 
    thumbnail = '', 
    delaySeconds = 0, 
    headlineVariant = 'A',
    onCtaReveal = () => {} 
  } = $props();

  // API Admin endpoint (analytics) — sobrescreva com PUBLIC_ADM_API_URL no .env
  const API_URL = env.PUBLIC_ADM_API_URL || "https://dezafiraadm-production.up.railway.app";

  // Svelte 5 state variables
  let videoElement: HTMLVideoElement | null = $state(null);
  let isMuted = $state(true);
  let isPlaying = $state(false);
  let showUnmuteOverlay = $state(false);
  let showPauseOverlay = $state(false);
  let currentTime = $state(0);
  let duration = $state(0);
  let sessionId = $state('');
  let hasRevealedCta = $state(false);

  // Intersection observer & Visibility tracking
  let observer: IntersectionObserver | null = null;

  // Real vs Fake progress logic
  let progressPercent = $derived(duration > 0 ? (currentTime / duration) * 100 : 0);
  
  // Custom warped progress bar (neuromarketing trick)
  let fakeProgressPercent = $derived(() => {
    if (duration === 0) return 0;
    const ratio = currentTime / duration;
    // Carrega até 40% na primeira décima parte do vídeo
    if (ratio < 0.1) {
      return ratio * 10 * 40;
    } else {
      // Avança os 60% restantes no restante do vídeo
      return 40 + ((ratio - 0.1) / 0.9) * 60;
    }
  });

  // Track max percentage watched (25, 50, 75, 100)
  let maxPercentageWatched = $state(0);

  // Initialize session and listeners
  onMount(() => {
    // Session ID unique for tracking
    sessionId = 'sess_' + Math.random().toString(36).substring(2, 11);

    // Visibility Listener: Pause if tab is inactive
    const handleVisibilityChange = () => {
      if (document.hidden && isPlaying && videoElement) {
        videoElement.pause();
        isPlaying = false;
      }
    };
    document.addEventListener('visibilitychange', handleVisibilityChange);

    // Resume Watching check
    if (typeof localStorage !== 'undefined') {
      const savedTime = localStorage.getItem(`vsl_pos_${vslId}`);
      if (savedTime && videoElement) {
        const parsedTime = parseFloat(savedTime);
        // Só retoma se não estiver no final do vídeo
        if (parsedTime > 5 && parsedTime < (duration || 99999) - 10) {
          videoElement.currentTime = parsedTime;
        }
      }
    }

    // Try Autoplay on mount
    setTimeout(() => {
      attemptPlay();
    }, 500);

    // Setup Smart Pause Observer: pause if scrolled out of viewport
    if (videoElement) {
      observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting && isPlaying) {
            videoElement?.pause();
            isPlaying = false;
          }
        });
      }, { threshold: 0.2 });
      observer.observe(videoElement);
    }

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      if (observer && videoElement) {
        observer.unobserve(videoElement);
      }
    };
  });

  // Safe tracking function
  async function trackEvent(percentage: number, isCtaClicked: boolean = false) {
    if (!vslId || !sessionId) return;
    try {
      await fetch(`${API_URL}/api/v1/vsl/analytics`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          vsl_id: vslId,
          session_id: sessionId,
          seconds_watched: Math.floor(currentTime),
          max_percentage: percentage,
          converted: isCtaClicked,
          headline_variant: headlineVariant
        })
      });
    } catch (e) {
      console.error('[VSL Player] Error sending analytics:', e);
    }
  }

  // Attempt play with fallback to muted autoplay
  async function attemptPlay() {
    if (!videoElement) return;
    try {
      // Tenta reproduzir com som
      isMuted = false;
      videoElement.muted = false;
      await videoElement.play();
      isPlaying = true;
      showUnmuteOverlay = false;
      trackEvent(0);
    } catch (err) {
      // Se bloqueado, reproduz mutado com o overlay piscante
      try {
        isMuted = true;
        videoElement.muted = true;
        await videoElement.play();
        isPlaying = true;
        showUnmuteOverlay = true;
        trackEvent(0);
      } catch (mutedErr) {
        console.error('[VSL Player] Autoplay totalmente bloqueado:', mutedErr);
      }
    }
  }

  // Activates sound and restarts video (neuromarketing trick)
  function handleUnmuteClick() {
    if (!videoElement) return;
    isMuted = false;
    videoElement.muted = false;
    videoElement.currentTime = 0; // Recomeça com som do início
    showUnmuteOverlay = false;
  }

  // Custom play/pause toggle
  function togglePlay() {
    if (!videoElement) return;
    if (isPlaying) {
      videoElement.pause();
      isPlaying = false;
      showPauseOverlay = true; // Mostra banner de retenção
    } else {
      videoElement.play();
      isPlaying = true;
      showPauseOverlay = false;
    }
  }

  // Handles resume play on clicking "continue watching" popup
  function resumeFromPauseOverlay() {
    if (!videoElement) return;
    videoElement.play();
    isPlaying = true;
    showPauseOverlay = false;
  }

  // Keep track of current playback state
  function handleTimeUpdate() {
    if (!videoElement) return;
    currentTime = videoElement.currentTime;

    // Salva progresso no localStorage para retomar se sair
    if (typeof localStorage !== 'undefined' && currentTime % 5 < 1) {
      localStorage.setItem(`vsl_pos_${vslId}`, currentTime.toString());
    }

    // Calcula retenção em faixas
    if (duration > 0) {
      const pct = Math.floor((currentTime / duration) * 100);
      let eventPct = 0;
      if (pct >= 25 && maxPercentageWatched < 25) { maxPercentageWatched = 25; eventPct = 25; }
      if (pct >= 50 && maxPercentageWatched < 50) { maxPercentageWatched = 50; eventPct = 50; }
      if (pct >= 75 && maxPercentageWatched < 75) { maxPercentageWatched = 75; eventPct = 75; }
      if (pct >= 100 && maxPercentageWatched < 100) { maxPercentageWatched = 100; eventPct = 100; }
      
      if (eventPct > 0) {
        trackEvent(eventPct);
      }
    }

    // Gatilho de Delay do CTA
    if (delaySeconds > 0 && currentTime >= delaySeconds && !hasRevealedCta) {
      hasRevealedCta = true;
      onCtaReveal();
    }
  }

  function handleLoadedMetadata() {
    if (videoElement) {
      duration = videoElement.duration;
    }
  }

  // External function called when CTA is clicked to log conversion
  export function logConversion() {
    trackEvent(maxPercentageWatched, true);
  }
</script>

<div class="vsl-player-container">
  <!-- Tag de Vídeo Customizada sem controles nativos -->
  <video
    bind:this={videoElement}
    src={src}
    poster={thumbnail || undefined}
    preload="auto"
    playsinline
    muted={isMuted}
    ontimeupdate={handleTimeUpdate}
    onloadedmetadata={handleLoadedMetadata}
    onclick={togglePlay}
    class="vsl-video"
  >
    <track kind="captions" />
  </video>

  <!-- Overlay Piscante de Som Muted Autoplay (Smart Play) -->
  {#if showUnmuteOverlay}
    <button class="vsl-unmute-overlay" onclick={handleUnmuteClick}>
      <div class="unmute-box">
        <span class="unmute-icon">🔊</span>
        <div class="unmute-text">
          <p class="unmute-title">SEU VÍDEO JÁ COMEÇOU!</p>
          <p class="unmute-subtitle">Clique aqui para ativar o som</p>
        </div>
      </div>
      <div class="pulse-ring"></div>
    </button>
  {/if}

  <!-- Overlay de Recuperação na Pausa (Pause Recovery) -->
  {#if showPauseOverlay}
    <div class="vsl-pause-overlay">
      <div class="pause-box">
        <span class="warning-icon">⚠️</span>
        <h3>Não vá embora ainda!</h3>
        <p>Temos revelações incríveis e uma oferta imperdível te esperando no final deste vídeo.</p>
        <button class="resume-btn" onclick={resumeFromPauseOverlay}>
          ▶️ Continuar Assistindo
        </button>
      </div>
    </div>
  {/if}

  <!-- Controles Customizados (Não interativos / Sem Seek) -->
  <div class="vsl-custom-controls">
    <div class="vsl-top-controls">
      <!-- Botão Play/Pause visual -->
      <button class="control-btn" onclick={togglePlay}>
        {isPlaying ? '⏸️' : '▶️'}
      </button>
      <span class="live-tag">LIVE</span>
    </div>

    <!-- Barra de Progresso Inteligente (Não clicável) -->
    <div class="vsl-progress-container">
      <div 
        class="vsl-progress-bar" 
        style:width="{fakeProgressPercent()}%"
      ></div>
    </div>
  </div>
</div>

<style>
  .vsl-player-container {
    position: relative;
    width: 100%;
    max-width: 800px;
    margin: 0 auto;
    background-color: #000;
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
    aspect-ratio: 16/9;
  }

  .vsl-video {
    width: 100%;
    height: 100%;
    display: block;
    cursor: pointer;
  }

  /* Overlay de Smart Play Muted */
  .vsl-unmute-overlay {
    position: absolute;
    inset: 0;
    background: rgba(0, 0, 0, 0.45);
    backdrop-filter: blur(2px);
    display: flex;
    justify-content: center;
    align-items: center;
    border: none;
    cursor: pointer;
    width: 100%;
    z-index: 100;
  }

  .unmute-box {
    background: #ea580c;
    color: #fff;
    padding: 16px 28px;
    border-radius: 50px;
    display: flex;
    align-items: center;
    gap: 16px;
    box-shadow: 0 10px 25px rgba(234, 88, 12, 0.5);
    animation: pulse-box 1.5s infinite ease-in-out;
  }

  .unmute-icon {
    font-size: 32px;
  }

  .unmute-title {
    font-weight: 800;
    font-size: 16px;
    letter-spacing: 0.5px;
    text-align: left;
    margin: 0;
  }

  .unmute-subtitle {
    font-size: 12px;
    opacity: 0.9;
    text-align: left;
    margin: 0;
  }

  @keyframes pulse-box {
    0% { transform: scale(1); }
    50% { transform: scale(1.05); }
    100% { transform: scale(1); }
  }

  /* Overlay de Recuperação na Pausa */
  .vsl-pause-overlay {
    position: absolute;
    inset: 0;
    background: rgba(15, 23, 42, 0.95);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 110;
    padding: 20px;
  }

  .pause-box {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 16px;
    padding: 24px;
    max-width: 380px;
    text-align: center;
    color: #fff;
    box-shadow: 0 15px 35px rgba(0, 0, 0, 0.4);
  }

  .warning-icon {
    font-size: 40px;
    display: block;
    margin-bottom: 12px;
  }

  .pause-box h3 {
    font-size: 18px;
    margin-bottom: 8px;
    font-weight: 700;
  }

  .pause-box p {
    font-size: 13px;
    line-height: 1.5;
    color: #94a3b8;
    margin-bottom: 18px;
  }

  .resume-btn {
    background: #22c55e;
    color: #fff;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-weight: 700;
    font-size: 14px;
    cursor: pointer;
    transition: background 0.2s;
  }

  .resume-btn:hover {
    background: #16a34a;
  }

  /* Custom Controls UI (sem controle de Seek) */
  .vsl-custom-controls {
    position: absolute;
    bottom: 0;
    left: 0;
    width: 100%;
    padding: 12px 20px;
    background: linear-gradient(transparent, rgba(0, 0, 0, 0.85));
    display: flex;
    flex-direction: column;
    gap: 8px;
    z-index: 50;
    pointer-events: none; /* Deixa cliques passarem para o vídeo */
  }

  .vsl-top-controls {
    display: flex;
    justify-content: space-between;
    align-items: center;
    pointer-events: auto; /* Permite clicar no play/pause */
  }

  .control-btn {
    background: none;
    border: none;
    font-size: 18px;
    cursor: pointer;
    color: #fff;
    padding: 4px;
  }

  .live-tag {
    background: #ef4444;
    color: #fff;
    font-size: 9px;
    font-weight: 800;
    padding: 2px 6px;
    border-radius: 4px;
    letter-spacing: 0.5px;
    animation: blink 2s infinite;
  }

  @keyframes blink {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
  }

  /* Barra de progresso somente-leitura */
  .vsl-progress-container {
    width: 100%;
    height: 5px;
    background: rgba(255, 255, 255, 0.2);
    border-radius: 10px;
    overflow: hidden;
  }

  .vsl-progress-bar {
    height: 100%;
    background: #38bdf8;
    border-radius: 10px;
    transition: width 0.2s linear;
  }
</style>
