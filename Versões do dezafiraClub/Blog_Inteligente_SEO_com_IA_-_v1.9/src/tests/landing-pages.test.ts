import { describe, expect, it } from 'vitest';
import { sanitizeHtml } from '$lib/server/sanitize';
import { sanitizeLandingBlocks } from '$lib/server/landing-pages';
import { createLandingPageSchema, updateLandingPageSchema } from '../routes/api/cli/validation';

describe('landing page security and CLI validation', () => {
  it('keeps safe custom HTML and removes executable markup', () => {
    const html = sanitizeHtml('<section style="padding:20px" onclick="alert(1)"><h2>Oferta</h2><script>alert(1)</script><a href="javascript:alert(1)">Comprar</a></section>');
    expect(html).toContain('<section style="padding:20px">');
    expect(html).toContain('<h2>Oferta</h2>');
    expect(html).not.toContain('onclick');
    expect(html).not.toContain('script');
    expect(html).not.toContain('javascript:');
  });

  it('accepts premium blocks and sanitizes nested snapshots', () => {
    const blocks = sanitizeLandingBlocks([{ id: 'hero-1', type: 'hero', properties: { title: '<Oferta>', image: 'https://example.com/a.jpg' } }]);
    expect(blocks[0].type).toBe('hero');
    expect(blocks[0].properties.title).toBe('Oferta');
  });

  it('rejects unknown blocks', () => {
    expect(() => sanitizeLandingBlocks([{ id: 'x', type: 'script-widget' }])).toThrow(/não permitido/);
  });

  it('requires title and blocks when creating', () => {
    expect(createLandingPageSchema.safeParse({ title: 'Oferta', blocks: [] }).success).toBe(true);
    expect(createLandingPageSchema.safeParse({ title: 'Oferta' }).success).toBe(false);
  });

  it('allows partial updates but rejects an empty body', () => {
    expect(updateLandingPageSchema.safeParse({ status: 'published' }).success).toBe(true);
    expect(updateLandingPageSchema.safeParse({}).success).toBe(false);
  });
});
