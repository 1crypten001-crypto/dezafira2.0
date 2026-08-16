import { describe, expect, it } from 'vitest';
import {
  categoryPinterestSchema,
  createPostSchema,
  listPostsQuerySchema,
  updatePostSchema
} from '../routes/api/cli/validation';

describe('CLI post validation', () => {
  it('accepts all supported post fields', () => {
    const result = createPostSchema.safeParse({
      title: 'Post válido',
      content: '<p>Conteúdo</p>',
      published: false,
      is_premium: true,
      youtube_video_url: 'https://youtube.com/watch?v=abc',
      tags: 'svelte, seo',
      category_ids: [2, 2, 1]
    });
    expect(result.success).toBe(true);
    if (result.success) expect(result.data.category_ids).toEqual([2, 1]);
  });

  it('rejects string booleans and unknown fields', () => {
    expect(createPostSchema.safeParse({
      title: 'Post inválido',
      content: '<p>Conteúdo</p>',
      published: 'false'
    }).success).toBe(false);
    expect(updatePostSchema.safeParse({ admin: true }).success).toBe(false);
  });

  it('requires at least one update field', () => {
    expect(updatePostSchema.safeParse({}).success).toBe(false);
  });

  it('only accepts real booleans for category updates', () => {
    expect(categoryPinterestSchema.safeParse({ pinterest_enabled: false }).success).toBe(true);
    expect(categoryPinterestSchema.safeParse({ pinterest_enabled: 'false' }).success).toBe(false);
  });

  it('normalizes and limits pagination', () => {
    expect(listPostsQuerySchema.parse({ page: '2', limit: '50' })).toMatchObject({ page: 2, limit: 50 });
    expect(listPostsQuerySchema.safeParse({ limit: '101' }).success).toBe(false);
  });
});
