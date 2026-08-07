/**
 * Test Setup - Configuração global para testes
 */

import { beforeAll, afterAll, vi } from 'vitest';

// Mock environment variables
beforeAll(() => {
  process.env.NODE_ENV = 'test';
  process.env.DATABASE_PATH = ':memory:';
  process.env.ADMIN_USERNAME = 'testadmin';
  process.env.ADMIN_PASSWORD = 'TestPassword123!';
});

// Cleanup after all tests
afterAll(() => {
  // Limpar cache
  vi.clearAllMocks();
});

// Global test utilities
export const testUtils = {
  // Gerar slug único para testes
  generateSlug: (prefix: string) => `test-${prefix}-${Date.now()}`,
  
  // Dados mock para posts
  mockPost: (overrides = {}) => ({
    title: 'Test Post',
    slug: `test-post-${Date.now()}`,
    content: '<p>Test content</p>',
    excerpt: 'Test excerpt',
    author: 'Test Author',
    categoryId: 1,
    status: 'published',
    featured: 0,
    viewCount: 0,
    isPremium: 0,
    publishedAt: new Date().toISOString(),
    ...overrides
  }),
  
  // Dados mock para categorias
  mockCategory: (overrides = {}) => ({
    name: 'Test Category',
    slug: `test-category-${Date.now()}`,
    description: 'Test description',
    color: '#000000',
    ...overrides
  })
};