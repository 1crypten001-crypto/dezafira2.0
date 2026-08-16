/**
 * Bundle Analyzer - Analisa tamanho do bundle
 * Run: npm run analyze
 */

import { visualizer } from 'rollup-plugin-visualizer';
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vitest/config';

export default defineConfig({
  plugins: [
    sveltekit() as any,
    // Visualizer só roda com ANALYZE=true
    process.env.ANALYZE === 'true' && visualizer({
      filename: 'dist/bundle-stats.html',
      open: true,
      gzipSize: true,
      manifest: './.svelte-kit/output/client/manifest.json'
    })
  ].filter(Boolean),
  test: {
    include: ['src/**/*.{test,spec}.{js,ts}'],
    environment: 'node',
    globals: true,
    setupFiles: ['./src/tests/setup.ts'],
    testTimeout: 30000,
    hookTimeout: 30000
  },
  // Build optimizations
  build: {
    target: 'esnext',
    minify: 'terser',
    cssMinify: true,
    rollupOptions: {
      output: {
        manualChunks: {
          // Separar vendor chunks
          'vendor-svelte': ['svelte'],
          'vendor-kit': ['@sveltejs/kit'],
        }
      }
    }
  }
});