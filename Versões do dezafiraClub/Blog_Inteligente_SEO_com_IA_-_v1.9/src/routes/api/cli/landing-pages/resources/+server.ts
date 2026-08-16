import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { getAllProducts, getLandingBuilderPosts } from '$lib/server/database';
import { requireCLIToken } from '../../auth';

export const GET: RequestHandler = async ({ request, getClientAddress }) => {
  const authError = await requireCLIToken(request, getClientAddress());
  if (authError) return authError;
  try {
    const [products, posts] = await Promise.all([getAllProducts(), getLandingBuilderPosts()]);
    return json({
      products: products.map((p: any) => ({
        id: p.id, name: p.name, slug: p.slug, description: p.description || '',
        price_cents: p.price_cents, image_url: p.image_url || '', href: `/product/${p.slug}`
      })),
      posts: posts.map((p: any) => ({ ...p, href: `/post/${p.slug}` }))
    });
  } catch (error) {
    console.error('[CLI LANDINGS] Failed to load resources:', error);
    return json({ error: 'Falha ao carregar produtos e posts.' }, { status: 500 });
  }
};
