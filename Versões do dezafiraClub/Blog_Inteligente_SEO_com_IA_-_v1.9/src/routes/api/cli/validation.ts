import { z } from 'zod';

const optionalHttpUrl = z.string().trim().max(2048).refine((value) => {
  if (value === '') return true;
  try {
    const url = new URL(value);
    return url.protocol === 'http:' || url.protocol === 'https:';
  } catch {
    return false;
  }
}, 'Informe uma URL HTTP ou HTTPS válida.');

const categoryIds = z.array(z.number().int().positive()).max(50).transform((ids) => [...new Set(ids)]);

const postFields = {
  title: z.string().trim().min(3).max(200),
  content: z.string().min(1).max(2_000_000),
  excerpt: z.string().max(1000),
  cover_image: optionalHttpUrl,
  published: z.boolean(),
  pinterest_enabled: z.boolean(),
  pinterest_image: optionalHttpUrl,
  category_ids: categoryIds,
  is_premium: z.boolean(),
  is_18_plus: z.boolean(),
  youtube_video_url: optionalHttpUrl,
  tags: z.string().max(1000),
  slug: z.string().trim().min(1).max(200)
};

export const createPostSchema = z.object({
  ...postFields,
  title: postFields.title,
  content: postFields.content
}).partial().required({ title: true, content: true }).strict();

export const updatePostSchema = z.object(postFields).partial().strict().refine(
  (body) => Object.keys(body).length > 0,
  'Informe pelo menos um campo para atualizar.'
);

export const categoryPinterestSchema = z.object({ pinterest_enabled: z.boolean() }).strict();

export const listPostsQuerySchema = z.object({
  page: z.coerce.number().int().positive().default(1),
  limit: z.coerce.number().int().min(1).max(100).default(25),
  search: z.string().trim().max(200).default('')
});

const landingFields = {
  title: z.string().trim().min(3).max(200),
  slug: z.string().trim().min(1).max(100),
  status: z.enum(['draft', 'published']),
  blocks: z.array(z.unknown()).max(250),
  settings: z.record(z.string(), z.unknown())
};

export const createLandingPageSchema = z.object(landingFields)
  .partial()
  .required({ title: true, blocks: true })
  .strict();

export const updateLandingPageSchema = z.object(landingFields).partial().strict().refine(
  (body) => Object.keys(body).length > 0,
  'Informe pelo menos um campo para atualizar.'
);

export const listLandingPagesQuerySchema = z.object({
  page: z.coerce.number().int().positive().default(1),
  limit: z.coerce.number().int().min(1).max(100).default(25),
  search: z.string().trim().max(200).default('')
});

export function zodError(error: z.ZodError) {
  return {
    error: 'Dados inválidos.',
    issues: error.issues.map((issue) => ({
      field: issue.path.join('.') || 'body',
      message: issue.message
    }))
  };
}
