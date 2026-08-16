import { describe, expect, it } from 'vitest';
import { acceptsLandingChildren, getLandingDropPosition } from '$lib/landing-dnd';

describe('landing builder drag and drop', () => {
  it('only lets real content containers receive blocks inside', () => {
    expect(acceptsLandingChildren('section')).toBe(true);
    expect(acceptsLandingChildren('container')).toBe(true);
    expect(acceptsLandingChildren('column')).toBe(true);
    expect(acceptsLandingChildren('columns')).toBe(false);
    expect(acceptsLandingChildren('hero')).toBe(false);
  });

  it('uses stable edge zones on tall containers', () => {
    expect(getLandingDropPosition('section', 800, 10)).toBe('before');
    expect(getLandingDropPosition('section', 800, 400)).toBe('inside');
    expect(getLandingDropPosition('section', 800, 790)).toBe('after');
  });

  it('uses before and after halves for leaf blocks and columns shells', () => {
    expect(getLandingDropPosition('text', 100, 20)).toBe('before');
    expect(getLandingDropPosition('text', 100, 80)).toBe('after');
    expect(getLandingDropPosition('columns', 100, 50)).toBe('after');
  });
});
