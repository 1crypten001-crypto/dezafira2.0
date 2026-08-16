type CacheEntry<T = unknown> = { value: T; expiresAt: number };

class MemoryCache {
  private entries = new Map<string, CacheEntry>();

  set<T>(key: string, value: T, ttl = CACHE_TTL.POSTS): void {
    this.entries.set(key, { value, expiresAt: Date.now() + ttl });
  }

  get<T>(key: string): T | undefined {
    const entry = this.entries.get(key);
    if (!entry) return undefined;
    if (Date.now() >= entry.expiresAt) {
      this.entries.delete(key);
      return undefined;
    }
    return entry.value as T;
  }

  has(key: string): boolean {
    return this.get(key) !== undefined;
  }

  delete(key: string): void {
    this.entries.delete(key);
  }

  deletePattern(pattern: string): void {
    const regex = new RegExp(pattern);
    for (const key of this.entries.keys()) {
      if (regex.test(key)) this.entries.delete(key);
    }
  }

  clear(): void {
    this.entries.clear();
  }

  getStats() {
    for (const key of this.entries.keys()) this.get(key);
    return { size: this.entries.size, keys: [...this.entries.keys()] };
  }
}

export const CACHE_TTL = {
  POSTS: 60 * 1000,
  CATEGORIES: 5 * 60 * 1000,
  SETTINGS: 10 * 60 * 1000
} as const;

export const cache = new MemoryCache();

export function cacheKey(...parts: Array<string | number>): string {
  return parts.join(':');
}

export function invalidatePostsCache(): void {
  cache.deletePattern('^posts');
}
