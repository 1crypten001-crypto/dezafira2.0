import {
  CalculateMetadataFunction,
  staticFile,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import React from "react";
import { loadFont } from "@remotion/google-fonts/PlusJakartaSans";

// Carrega a fonte geométrica premium Plus Jakarta Sans
const { fontFamily: loadedFontFamily } = loadFont();

export type CinematicPromoProps = {
  bgImages: string[];
  logoPath: string;
  colors: {
    bg: string;
    primary: string;
    secondary: string;
    accent?: string;
  };
  durationInSeconds: number;
};

export const calculateCinematicPromoMetadata: CalculateMetadataFunction<CinematicPromoProps> = ({
  props,
}) => {
  const fps = 24;
  const durationInFrames = Math.round((props.durationInSeconds || 15) * fps);
  return {
    durationInFrames,
    fps,
  };
};

export const CinematicPromo: React.FC<CinematicPromoProps> = ({
  bgImages = [],
  logoPath,
  colors,
}) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();

  const img1 = bgImages[0] || "";
  const img2 = bgImages[1] || "";
  const img3 = bgImages[2] || "";

  // ─── TIMELINE (15s = 360 frames @ 24fps) ───
  // Cena 1: Frames 0 - 120 (Transição suave 110 - 120)
  // Cena 2: Frames 110 - 240 (Transição suave 230 - 240)
  // Cena 3: Frames 230 - 360

  // ── Opacidades e Blurs das Cenas (Crossfade com Blur)
  let img1Opacity = 1;
  let img1Blur = 0;
  if (frame >= 110) {
    img1Opacity = interpolate(frame, [110, 120], [1, 0], { extrapolateRight: "clamp" });
    img1Blur = interpolate(frame, [110, 120], [0, 20], { extrapolateRight: "clamp" });
  }

  let img2Opacity = 0;
  let img2Blur = 0;
  if (frame >= 110 && frame <= 120) {
    img2Opacity = interpolate(frame, [110, 120], [0, 1], { extrapolateRight: "clamp" });
  } else if (frame > 120 && frame < 230) {
    img2Opacity = 1;
  } else if (frame >= 230 && frame <= 240) {
    img2Opacity = interpolate(frame, [230, 240], [1, 0], { extrapolateRight: "clamp" });
    img2Blur = interpolate(frame, [230, 240], [0, 20], { extrapolateRight: "clamp" });
  }

  let img3Opacity = 0;
  if (frame >= 230) {
    img3Opacity = interpolate(frame, [230, 240], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  }

  // ── Movimento de Câmera Ken Burns Cinema (Pan & Zoom Ultra-Suave)
  // Cena 1: Avatar — Slow Push-in dramático
  const s1Scale = interpolate(frame, [0, 130], [1.0, 1.08], { extrapolateRight: "clamp" });
  const s1TranslateY = interpolate(frame, [0, 130], [0, -10], { extrapolateRight: "clamp" });

  // Cena 2: Tecnologia — Slow Glide diagonal
  const s2Frame = frame - 110;
  const s2Scale = interpolate(s2Frame, [0, 130], [1.02, 1.1], { extrapolateRight: "clamp" });
  const s2TranslateX = interpolate(s2Frame, [0, 130], [0, -18], { extrapolateRight: "clamp" });
  const s2TranslateY = interpolate(s2Frame, [0, 130], [0, -8], { extrapolateRight: "clamp" });

  // Cena 3: Clímax — Smooth Zoom-out revelador
  const s3Frame = frame - 230;
  const s3Scale = interpolate(s3Frame, [0, 130], [1.09, 1.0], { extrapolateRight: "clamp" });
  const s3TranslateY = interpolate(s3Frame, [0, 130], [8, 0], { extrapolateRight: "clamp" });

  // Fade-in inicial do vídeo
  const introFade = interpolate(frame, [0, 16], [0, 1], { extrapolateRight: "clamp" });

  // Identifica a cena ativa (0, 1 ou 2)
  const activeSceneIndex = frame < 115 ? 0 : (frame < 235 ? 1 : 2);
  const sceneFrame = activeSceneIndex === 0 
    ? frame 
    : (activeSceneIndex === 1 ? frame - 115 : frame - 235);

  // Mola de entrada de tipografia para a cena ativa (Estilo Apple)
  const textSpring = spring({
    frame: sceneFrame - 4,
    fps,
    config: { damping: 16, mass: 0.8 },
  });

  const textY = interpolate(textSpring, [0, 1], [35, 0]);
  const textOpacity = interpolate(textSpring, [0, 1], [0, 1]);
  const textBlur = interpolate(textSpring, [0, 1], [16, 0]);

  // Transição de saída do texto antes da troca de cena
  let textExit = 1;
  if (activeSceneIndex === 0 && frame >= 108) {
    textExit = interpolate(frame, [108, 114], [1, 0], { clamp: true });
  } else if (activeSceneIndex === 1 && frame >= 228) {
    textExit = interpolate(frame, [228, 234], [1, 0], { clamp: true });
  }

  return (
    <div
      style={{
        flex: 1,
        backgroundColor: colors.bg || "#0a0a0c",
        fontFamily: loadedFontFamily,
        width,
        height,
        position: "relative",
        overflow: "hidden",
      }}
    >
      {/* ── CAMADA 1: BACKGROUNDS ULTRA-LIMPOS COM KEN BURNS ── */}
      <div style={{ position: "absolute", inset: 0, opacity: introFade, zIndex: 0 }}>
        {/* Cena 1: Avatar Feminino */}
        {img1 && frame < 120 && (
          <div
            style={{
              position: "absolute",
              inset: 0,
              opacity: img1Opacity,
              filter: `blur(${img1Blur}px)`,
              transform: `scale(${s1Scale}) translateY(${s1TranslateY}px)`,
              zIndex: 3,
            }}
          >
            <img
              src={staticFile(img1)}
              alt="Scene 1"
              style={{ width: "100%", height: "100%", objectFit: "cover" }}
            />
          </div>
        )}

        {/* Cena 2: Conceito Tecnológico */}
        {img2 && frame >= 110 && frame < 240 && (
          <div
            style={{
              position: "absolute",
              inset: 0,
              opacity: img2Opacity,
              filter: `blur(${img2Blur}px)`,
              transform: `scale(${s2Scale}) translate(${s2TranslateX}px, ${s2TranslateY}px)`,
              zIndex: 2,
            }}
          >
            <img
              src={staticFile(img2)}
              alt="Scene 2"
              style={{ width: "100%", height: "100%", objectFit: "cover" }}
            />
          </div>
        )}

        {/* Cena 3: Horizonte Épico */}
        {img3 && frame >= 230 && (
          <div
            style={{
              position: "absolute",
              inset: 0,
              opacity: img3Opacity,
              transform: `scale(${s3Scale}) translateY(${s3TranslateY}px)`,
              zIndex: 1,
            }}
          >
            <img
              src={staticFile(img3)}
              alt="Scene 3"
              style={{ width: "100%", height: "100%", objectFit: "cover" }}
            />
          </div>
        )}
      </div>

      {/* Gradiente Vignette Cinematográfico Estilo Apple TV+ */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: "radial-gradient(ellipse at center, rgba(0,0,0,0) 30%, rgba(5,5,8,0.7) 75%, rgba(0,0,0,0.92) 100%)",
          zIndex: 4,
        }}
      />

      {/* Gradiente de Base para Legibilidade */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: "linear-gradient(to top, rgba(5, 5, 8, 0.95) 0%, rgba(5, 5, 8, 0.5) 45%, rgba(5, 5, 8, 0) 100%)",
          zIndex: 5,
        }}
      />

      {/* ── HEADER SUPERIOR: BRANDING APPLE TV+ STYLE ── */}
      <div
        style={{
          position: "absolute",
          top: 48,
          left: 56,
          display: "flex",
          alignItems: "center",
          gap: 16,
          zIndex: 10,
        }}
      >
        {logoPath && (
          <img
            src={staticFile(logoPath)}
            alt="Logo"
            style={{
              height: 44,
              width: "auto",
              filter: "drop-shadow(0 4px 12px rgba(0, 207, 255, 0.3))",
            }}
          />
        )}
        <div style={{ display: "flex", flexDirection: "column" }}>
          <span
            style={{
              fontSize: 16,
              fontWeight: 800,
              letterSpacing: "5px",
              color: "#ffffff",
              textTransform: "uppercase",
            }}
          >
            DEZAFIRA
          </span>
          <span
            style={{
              fontSize: 10,
              fontWeight: 600,
              letterSpacing: "3px",
              color: colors.primary || "#00CFFF",
              textTransform: "uppercase",
            }}
          >
            ORIGINAL
          </span>
        </div>
      </div>

      {/* ── CAMADA 2: TIPOGRAFIA DE ALTA COSTURA APPLE ── */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          display: "flex",
          flexDirection: "column",
          justifyContent: "flex-end",
          padding: "0 64px 84px 64px",
          opacity: textOpacity * textExit,
          transform: `translateY(${textY}px)`,
          filter: `blur(${textBlur}px)`,
          zIndex: 6,
        }}
      >
        {/* ── CENA 1: AVATAR / APRESENTAÇÃO HERO ── */}
        {activeSceneIndex === 0 && (
          <div style={{ maxWidth: 880, display: "flex", flexDirection: "column", alignItems: "flex-start" }}>
            {/* Frosted Glass Badge */}
            <div
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: 8,
                background: "rgba(255, 255, 255, 0.08)",
                backdropFilter: "blur(20px)",
                border: "1px solid rgba(255, 255, 255, 0.16)",
                borderRadius: 999,
                padding: "6px 18px",
                marginBottom: 20,
              }}
            >
              <div
                style={{
                  width: 6,
                  height: 6,
                  borderRadius: "50%",
                  backgroundColor: colors.primary || "#00CFFF",
                  boxShadow: `0 0 10px ${colors.primary || "#00CFFF"}`,
                }}
              />
              <span
                style={{
                  fontSize: 12,
                  fontWeight: 700,
                  letterSpacing: "4px",
                  color: "#ffffff",
                  textTransform: "uppercase",
                }}
              >
                INFOPRODUTOS & IA
              </span>
            </div>

            {/* Título Principal Apple */}
            <h1
              style={{
                margin: 0,
                fontSize: 82,
                fontWeight: 800,
                color: "#ffffff",
                letterSpacing: "-2.5px",
                lineHeight: 1.05,
                textShadow: "0 10px 40px rgba(0, 0, 0, 0.9)",
              }}
            >
              Dezafira Club
            </h1>

            {/* Subtítulo Sofisticado */}
            <p
              style={{
                margin: "16px 0 0 0",
                fontSize: 26,
                fontWeight: 500,
                color: "rgba(255, 255, 255, 0.85)",
                letterSpacing: "0.5px",
                lineHeight: 1.3,
                textShadow: "0 4px 16px rgba(0, 0, 0, 0.8)",
              }}
            >
              A Nova Era dos Criadores de Infoprodutos no Piloto Automático.
            </p>
          </div>
        )}

        {/* ── CENA 2: PROPOSIÇÃO DE VALOR HERO CENTER ── */}
        {activeSceneIndex === 1 && (
          <div
            style={{
              width: "100%",
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              textAlign: "center",
            }}
          >
            {/* Tag Central */}
            <span
              style={{
                fontSize: 13,
                fontWeight: 700,
                letterSpacing: "6px",
                color: colors.primary || "#00CFFF",
                textTransform: "uppercase",
                marginBottom: 16,
              }}
            >
              O PODER DA AUTOMAÇÃO
            </span>

            {/* Título Centralizado com Destaque */}
            <h2
              style={{
                margin: 0,
                fontSize: 68,
                fontWeight: 800,
                color: "#ffffff",
                letterSpacing: "-2px",
                lineHeight: 1.15,
                maxWidth: 960,
                textShadow: "0 10px 40px rgba(0, 0, 0, 0.9)",
              }}
            >
              Crie. Automatize.{" "}
              <span
                style={{
                  color: colors.primary || "#00CFFF",
                  textShadow: `0 0 30px rgba(0, 207, 255, 0.4)`,
                }}
              >
                Escale.
              </span>
            </h2>

            <p
              style={{
                margin: "18px 0 0 0",
                fontSize: 24,
                fontWeight: 400,
                color: "rgba(255, 255, 255, 0.8)",
                letterSpacing: "1px",
                maxWidth: 800,
              }}
            >
              Infoprodutos completos criados e comercializados com Inteligência Artificial de ponta.
            </p>
          </div>
        )}

        {/* ── CENA 3: CLÍMAX & CALL TO ACTION ── */}
        {activeSceneIndex === 2 && (
          <div
            style={{
              width: "100%",
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              textAlign: "center",
            }}
          >
            <h2
              style={{
                margin: 0,
                fontSize: 70,
                fontWeight: 800,
                color: "#ffffff",
                letterSpacing: "-2px",
                lineHeight: 1.1,
                textShadow: "0 10px 40px rgba(0, 0, 0, 0.9)",
              }}
            >
              Sua Jornada Começa Agora.
            </h2>

            {/* Apple Style Glassmorphic Button */}
            <div
              style={{
                marginTop: 28,
                background: "linear-gradient(135deg, rgba(0, 207, 255, 0.25) 0%, rgba(123, 79, 214, 0.25) 100%)",
                backdropFilter: "blur(24px)",
                border: "1px solid rgba(0, 207, 255, 0.5)",
                borderRadius: 999,
                padding: "16px 42px",
                boxShadow: "0 12px 32px rgba(0, 207, 255, 0.25)",
                display: "inline-flex",
                alignItems: "center",
                gap: 12,
              }}
            >
              <span
                style={{
                  fontSize: 26,
                  fontWeight: 700,
                  color: "#ffffff",
                  letterSpacing: "0.5px",
                }}
              >
                Acesse <span style={{ color: colors.primary || "#00CFFF" }}>dezafira.com.br</span>
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Footer Tag Minimalista */}
      <div
        style={{
          position: "absolute",
          bottom: 32,
          right: 56,
          fontSize: 12,
          fontWeight: 600,
          letterSpacing: "2px",
          color: "rgba(255, 255, 255, 0.4)",
          textTransform: "uppercase",
          zIndex: 10,
        }}
      >
        dezafira studio · 2026
      </div>
    </div>
  );
};
