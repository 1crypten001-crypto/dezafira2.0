/**
 * Performance - Otimizações de queries e compressão
 */

// Comprimir texto para armazenamento
export function compressText(text: string): string {
  // Para textos pequenos, não compensa comprimir
  if (text.length < 500) return text;
  
  try {
    // Usar simple compression (base64 encoded)
    // Em produção, usar algo como lz-string
    return text;
  } catch {
    return text;
  }
}

// Comprimir para responses
export function compressResponse(data: any): string {
  return JSON.stringify(data);
}

// Parsear com segurança
export function safeJsonParse<T>(text: string, fallback: T): T {
  try {
    return JSON.parse(text);
  } catch {
    return fallback;
  }
}

// Debounce para operações pesadas
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout | null = null;
  
  return (...args: Parameters<T>) => {
    if (timeout) clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
}

// Throttle para rate limiting
export function throttle<T extends (...args: any[]) => any>(
  func: T,
  limit: number
): (...args: Parameters<T>) => void {
  let lastCall = 0;
  
  return (...args: Parameters<T>) => {
    const now = Date.now();
    if (now - lastCall >= limit) {
      lastCall = now;
      func(...args);
    }
  };
}

// Lazy load de imagens
export function getLazyImageSrc(src: string, placeholder?: string): string {
  return `data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 9'%3E%3Crect fill='%23ddd' width='16' height='9'/%3E%3C/svg%3E`;
}

// Generate critical CSS inline (simplificado)
export function getCriticalCss(pageType: 'home' | 'post' | 'category' | 'admin'): string {
  // CSS crítico mínimo para cada tipo de página
  const criticalCSS = {
    home: 'body{font-family:system-ui;margin:0}.container{max-width:1200px;margin:0 auto}',
    post: 'body{font-family:system-ui;margin:0;line-height:1.6}',
    category: 'body{font-family:system-ui;margin:0}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:1rem}',
    admin: 'body{font-family:system-ui;margin:0;padding:1rem}'
  };
  
  return criticalCSS[pageType] || criticalCSS.home;
}

// Resource hints para prefetch
export function getResourceHints(urls: string[]): { preload: string[], prefetch: string[] } {
  const preload = urls.filter(u => u.includes('critical'));
  const prefetch = urls.filter(u => !u.includes('critical'));
  
  return { preload, prefetch };
}

// Batch de operações assíncronas
export async function batchAsync<T>(
  items: T[],
  processor: (item: T) => Promise<void>,
  batchSize: number = 10
): Promise<void> {
  for (let i = 0; i < items.length; i += batchSize) {
    const batch = items.slice(i, i + batchSize);
    await Promise.all(batch.map(processor));
  }
}

// Memoization simples
export function memoize<T extends (...args: any[]) => any>(fn: T): T {
  const cache = new Map<string, ReturnType<T>>();
  
  return ((...args: Parameters<T>): ReturnType<T> => {
    const key = JSON.stringify(args);
    if (cache.has(key)) {
      return cache.get(key)!;
    }
    const result = fn(...args);
    cache.set(key, result);
    return result;
  }) as T;
}

// Time-based cache
export function timeCache<T>(ttl: number, factory: () => T): () => T {
  let cached: { value: T; timestamp: number } | null = null;
  
  return () => {
    const now = Date.now();
    if (!cached || now - cached.timestamp > ttl) {
      cached = { value: factory(), timestamp: now };
    }
    return cached.value;
  };
}