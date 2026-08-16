import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { deleteLandingPage, getLandingPageById, getLandingPageBySlug, updateLandingPage } from '$lib/server/database';
import { sanitizeLandingBlocks } from '$lib/server/landing-pages';
import { slugify } from '$lib/server/sanitize';
import { requireCLIToken } from '../../auth';
import { updateLandingPageSchema, zodError } from '../../validation';

function parseId(value: string): number | null {
  if (!/^\d+$/.test(value)) return null;
  const id = Number(value);
  return Number.isSafeInteger(id) && id > 0 ? id : null;
}

export const GET: RequestHandler = async ({ request, params, getClientAddress }) => {
  const authError = await requireCLIToken(request, getClientAddress());
  if (authError) return authError;
  const id = parseId(params.id);
  if (!id) return json({ error: 'ID inválido.' }, { status: 400 });
  const page = await getLandingPageById(id);
  if (!page) return json({ error: 'Landing page não encontrada.' }, { status: 404 });
  return json({ ...page, blocks: JSON.parse(page.content || '[]'), settings: JSON.parse(page.settings || '{}'), content: undefined });
};

export const PUT: RequestHandler = async ({ request, params, getClientAddress }) => {
  const authError = await requireCLIToken(request, getClientAddress());
  if (authError) return authError;
  const id = parseId(params.id);
  if (!id) return json({ error: 'ID inválido.' }, { status: 400 });
  let raw: unknown;
  try { raw = await request.json(); } catch { return json({ error: 'Body JSON inválido.' }, { status: 400 }); }
  const parsed = updateLandingPageSchema.safeParse(raw);
  if (!parsed.success) return json(zodError(parsed.error), { status: 400 });

  try {
    const current = await getLandingPageById(id);
    if (!current) return json({ error: 'Landing page não encontrada.' }, { status: 404 });
    const slug = parsed.data.slug ? slugify(parsed.data.slug) : current.slug;
    const collision = await getLandingPageBySlug(slug);
    if (collision && Number(collision.id) !== id) return json({ error: 'Este slug já está em uso.' }, { status: 409 });
    const blocks = parsed.data.blocks ? sanitizeLandingBlocks(parsed.data.blocks) : JSON.parse(current.content || '[]');
    const settings = parsed.data.settings || JSON.parse(current.settings || '{}');
    await updateLandingPage(
      id,
      parsed.data.title || current.title,
      slug,
      parsed.data.status || current.status,
      JSON.stringify(blocks),
      JSON.stringify(settings)
    );
    return json({ success: true, id, slug, status: parsed.data.status || current.status, public_url: `/p/${slug}` });
  } catch (error) {
    console.error(`[CLI LANDINGS] Failed to update ${id}:`, error);
    return json({ error: error instanceof Error ? error.message : 'Falha ao atualizar landing page.' }, { status: 500 });
  }
};

export const DELETE: RequestHandler = async ({ request, params, url, getClientAddress }) => {
  const authError = await requireCLIToken(request, getClientAddress());
  if (authError) return authError;
  const id = parseId(params.id);
  if (!id) return json({ error: 'ID inválido.' }, { status: 400 });
  if (url.searchParams.get('confirm') !== String(id)) {
    return json({ error: `Confirme a exclusão definitiva usando ?confirm=${id}.` }, { status: 400 });
  }
  const page = await getLandingPageById(id);
  if (!page) return json({ error: 'Landing page não encontrada.' }, { status: 404 });
  await deleteLandingPage(id);
  return json({ success: true, id, title: page.title });
};
