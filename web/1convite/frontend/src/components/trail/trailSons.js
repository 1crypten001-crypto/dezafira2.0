const AudioCtx = window.AudioContext || window.webkitAudioContext;
let ctx = null;

function getCtx() {
  if (!ctx) ctx = new AudioCtx();
  return ctx;
}

function playTone(freq, duration, type = 'sine', volume = 0.12) {
  const c = getCtx();
  const osc = c.createOscillator();
  const gain = c.createGain();
  osc.type = type;
  osc.frequency.value = freq;
  gain.gain.setValueAtTime(volume, c.currentTime);
  gain.gain.exponentialRampToValueAtTime(0.001, c.currentTime + duration);
  osc.connect(gain);
  gain.connect(c.destination);
  osc.start();
  osc.stop(c.currentTime + duration);
}

export function playTrailClick() {
  playTone(800, 0.05, 'sine', 0.1);
}

export function playTrailComplete() {
  const notes = [523, 659, 784, 1047];
  notes.forEach((f, i) => setTimeout(() => playTone(f, 0.12, 'sine', 0.12), i * 100));
}

export function playTrailStreak() {
  playTone(880, 0.1, 'sine', 0.1);
  setTimeout(() => playTone(1175, 0.1, 'sine', 0.1), 100);
  setTimeout(() => playTone(1568, 0.15, 'sine', 0.12), 200);
}

export function playTrailMilestone() {
  const notes = [523, 587, 659, 784, 880, 988, 1047];
  notes.forEach((f, i) => setTimeout(() => playTone(f, 0.15, 'sine', 0.1), i * 80));
}

export function playTrailCoin() {
  playTone(988, 0.08, 'square', 0.08);
  setTimeout(() => playTone(1318, 0.12, 'square', 0.08), 80);
}
