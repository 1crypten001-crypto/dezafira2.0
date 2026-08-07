/**
 * Cache Tests
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { cache, CACHE_TTL, cacheKey, invalidatePostsCache } from '$lib/server/cache';

describe('MemoryCache', () => {
  beforeEach(() => {
    cache.clear();
  });

  describe('set/get', () => {
    it('should store and retrieve data', () => {
      cache.set('test', { value: 123 });
      expect(cache.get('test')).toEqual({ value: 123 });
    });

    it('should return undefined for non-existent keys', () => {
      expect(cache.get('nonexistent')).toBeUndefined();
    });

    it('should respect custom TTL', async () => {
      cache.set('short', 'data', 10); // 10ms
      expect(cache.get('short')).toBe('data');
      
      await new Promise(r => setTimeout(r, 20));
      expect(cache.get('short')).toBeUndefined();
    });
  });

  describe('has', () => {
    it('should return true for existing keys', () => {
      cache.set('exists', 'data');
      expect(cache.has('exists')).toBe(true);
    });

    it('should return false for non-existent keys', () => {
      expect(cache.has('notexists')).toBe(false);
    });
  });

  describe('delete', () => {
    it('should remove a key', () => {
      cache.set('delete-me', 'data');
      cache.delete('delete-me');
      expect(cache.has('delete-me')).toBe(false);
    });
  });

  describe('deletePattern', () => {
    it('should delete all keys matching pattern', () => {
      cache.set('posts:1', 'post1');
      cache.set('posts:2', 'post2');
      cache.set('category:1', 'cat1');
      
      cache.deletePattern('^posts');
      
      expect(cache.has('posts:1')).toBe(false);
      expect(cache.has('posts:2')).toBe(false);
      expect(cache.has('category:1')).toBe(true);
    });
  });

  describe('clear', () => {
    it('should clear all entries', () => {
      cache.set('a', '1');
      cache.set('b', '2');
      cache.clear();
      expect(cache.getStats().size).toBe(0);
    });
  });

  describe('getStats', () => {
    it('should return cache statistics', () => {
      cache.set('key1', 'value1');
      cache.set('key2', 'value2');
      
      const stats = cache.getStats();
      expect(stats.size).toBe(2);
      expect(stats.keys).toContain('key1');
      expect(stats.keys).toContain('key2');
    });
  });
});

describe('Cache TTL constants', () => {
  it('should have reasonable TTL values', () => {
    expect(CACHE_TTL.POSTS).toBe(60 * 1000); // 1 min
    expect(CACHE_TTL.CATEGORIES).toBe(5 * 60 * 1000); // 5 min
    expect(CACHE_TTL.SETTINGS).toBe(10 * 60 * 1000); // 10 min
  });
});

describe('cacheKey helper', () => {
  it('should generate cache keys correctly', () => {
    expect(cacheKey('posts', '1')).toBe('posts:1');
    expect(cacheKey('posts', '1', '10')).toBe('posts:1:10');
    expect(cacheKey('category', 'news')).toBe('category:news');
  });
});
