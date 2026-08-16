import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import {
  createLandingPage, deleteLandingPage, getLandingPageBySlug, getLandingPagesPage, updateLandingPage
} from '$lib/server/database';
import { sanitizeLandingBlocks } from '$lib/server/landing-pages';
import { slugify } from '$lib/server/sanitize';
import { requireCLIToken } from '../auth';
import { createLandingPageSchema, listLandingPagesQuerySchema, zodError } from '../validation';

export const GET: RequestHandler = async ({ request, url, getClientAddress }) => {
  const authError = await requireCLIToken(request, getClientAddress());
  if (authError) return authError;
  const parsed = listLandingPagesQuerySchema.safeParse(Object.fromEntries(url.searchParams));
  if (!parsed.success) return json(zodError(parsed.error), { status: 400 });

  try {
    const result = await getLandingPagesPage(parsed.data);
    return json({
      landing_pages: result.pages.map(({ content, settings, ...page }: any) => ({
        ...page,
        block_count: JSON.parse(content || '[]').length
      })),
      pagination: { page: result.page, limit: result.limit, total: result.total, totalPages: result.totalPages }
    });
  } catch (error) {
    console.error('[CLI LANDINGS] Failed to list:', error);
    return json({ error: 'Falha ao listar landing pages.' }, { status: 500 });
  }
};

export const POST: RequestHandler = async ({ request, getClientAddress }) => {
  const authError = await requireCLIToken(request, getClientAddress());
  if (authError) return authError;
  let raw: unknown;
  try { raw = await request.json(); } catch { return json({ error: 'Body JSON inválido.' }, { status: 400 }); }
  const parsed = createLandingPageSchema.safeParse(raw);
  if (!parsed.success) return json(zodError(parsed.error), { status: 400 });

  const body = parsed.data;
  const slug = slugify(body.slug || body.title);
  if (!slug) return json({ error: 'Não foi possível gerar um slug válido.' }, { status: 400 });
  try {
    if (await getLandingPageBySlug(slug)) return json({ error: 'Este slug já está em uso.' }, { status: 409 });
    const blocks = sanitizeLandingBlocks(body.blocks);
    const id = await createLandingPage(body.title, slug);
    try {
      await updateLandingPage(
        id, body.title, slug, body.status || 'draft', JSON.stringify(blocks), JSON.stringify(body.settings || {})
      );
    } catch (error) {
      await deleteLandingPage(id).catch(() => undefined);
      throw error;
    }
    return json({ success: true, id, slug, status: body.status || 'draft', edit_url: `/admin/landing-pages/${id}`, public_url: `/p/${slug}` }, { status: 201 });
  } catch (error) {
    console.error('[CLI LANDINGS] Failed to create:', error);
    return json({ error: error instanceof Error ? error.message : 'Falha ao criar landing page.' }, { status: 500 });
  }
};
