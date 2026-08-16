const isCapacitor = Boolean(
  window.Capacitor || 
  window.location.protocol === 'capacitor:' || 
  window.location.protocol === 'file:' ||
  (typeof navigator !== 'undefined' && navigator.userAgent && navigator.userAgent.includes('Capacitor'))
);
const isLocalhost = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';

const API_BASE = (isLocalhost && !isCapacitor)
  ? 'http://localhost:3001/api/v1'
  : 'https://invigorating-expression-production-d4df.up.railway.app/api/v1';

export async function sendLeadWebhook(data) {
  const res = await fetch(`${API_BASE}/leads`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error('Erro ao enviar lead');
  return res.json();
}
