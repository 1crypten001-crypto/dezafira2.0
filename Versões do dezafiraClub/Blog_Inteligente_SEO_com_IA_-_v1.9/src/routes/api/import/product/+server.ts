import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import crypto from 'crypto';
import { createProduct, generateUniqueProductSlug, getProductById, getProductCategories } from '$lib/server/database';
import { env } from '$env/dynamic/private';

function safeEqual(a: string, b: string): boolean {
  const ba = Buffer.from(a);
  const bb = Buffer.from(b);
  if (ba.length !== bb.length) return false;
  return crypto.timingSafeEqual(ba, bb);
}

/**
 * POST /api/import/product
 *
 * Ponte DezafiraAdm → DezafiraClube. Permite que as fábricas do Adm
 * (curso/ebook/miniapp) criem produtos no catálogo do Clube para venda
 * via Asaas (order bump + esteira upsell/downsell).
 *
 * Autenticação: header `x-import-key` deve bater com IMPORT_API_KEY (env).
 * Sem a chave configurada, o endpoint retorna 503 (protegido por padrão).
 */
export const POST: RequestHandler = async ({ request }) => {
  const importKey = env.IMPORT_API_KEY || '';
  const providedKey = request.headers.get('x-import-key') || '';

  if (!importKey) {
    return json(
      { success: false, error: 'IMPORT_API_KEY não configurado neste serviço.' },
      { status: 503 }
    );
  }
  if (!safeEqual(providedKey, importKey)) {
    return json({ success: false, error: 'Chave de importação inválida.' }, { status: 401 });
  }

  let body: any;
  try {
    body = await request.json();
  } catch (e) {
    return json({ success: false, error: 'JSON inválido.' }, { status: 400 });
  }

  const name = String(body.name || '').trim();
  const price_cents = Math.max(0, parseInt(body.price_cents) || 0);

  // Combo/pacote nativo: ids dos produtos incluídos no bundle (validados abaixo)
  let bundle_items: number[] | null = null;
  if (body.bundle_items !== undefined && body.bundle_items !== null) {
    const raw = Array.isArray(body.bundle_items) ? body.bundle_items : [body.bundle_items];
    bundle_items = raw.map((n: any) => parseInt(n) || 0).filter((n: number) => n > 0);
    for (const itemId of bundle_items) {
      const item = await getProductById(itemId);
      if (!item) {
        return json(
          { success: false, error: `Produto incluído no bundle não existe: id ${itemId}` },
          { status: 400 }
        );
      }
    }
    if (bundle_items.length < 2) {
      return json(
        { success: false, error: 'Um combo/pacote precisa incluir pelo menos 2 produtos.' },
        { status: 400 }
      );
    }
  }
  const resource_type = String(body.resource_type || 'link').trim();
  const external_link = String(body.external_link || '').trim();
  const description = body.description ? String(body.description).trim() : undefined;
  const image_url = body.image_url ? String(body.image_url).trim() : undefined;
  const youtube_video_url = body.youtube_video_url ? String(body.youtube_video_url).trim() : undefined;

  if (!name) {
    return json({ success: false, error: 'O campo name é obrigatório.' }, { status: 400 });
  }
  if (price_cents > 0 && price_cents < 500) {
    return json(
      { success: false, error: 'O Asaas exige valor mínimo de R$ 5,00 (ou R$ 0 para grátis).' },
      { status: 400 }
    );
  }
  // Ponte Adm→Clube entrega por link (URL pública do entregável) ou manual (Drive/GitHub).
  // 'file'/'cloudinary' exigiriam upload de arquivo — não fazem sentido aqui e criariam
  // um produto quebrado sem arquivo.
  if (resource_type !== 'link' && resource_type !== 'manual') {
    return json(
      { success: false, error: 'resource_type deve ser link ou manual (entrega por URL).' },
      { status: 400 }
    );
  }
  if (!external_link) {
    return json({ success: false, error: 'external_link é obrigatório para link/manual.' }, { status: 400 });
  }

  try {
    const categories = await getProductCategories();
    let category_id: number | null = null;
    if (body.category) {
      const catName = String(body.category).toLowerCase().trim();
      const found = categories.find((c: any) => c.name.toLowerCase() === catName);
      category_id = found ? found.id : null;
    }

    const slug = await generateUniqueProductSlug(String(body.slug || name));

    const product = await createProduct({
      name,
      slug,
      description,
      price_cents,
      external_link: (resource_type === 'link' || resource_type === 'manual') ? external_link : undefined,
      image_url,
      category_id,
      youtube_video_url,
      resource_type,
      is_premium_included: body.is_premium_included ? 1 : 0,
      has_extra_service: body.has_extra_service ? 1 : 0,
      extra_service_title: body.extra_service_title || null,
      extra_service_price_cents: Math.max(0, parseInt(body.extra_service_price_cents) || 0),
      extra_service_description: body.extra_service_description || null,
      upsell_product_id: body.upsell_product_id ? parseInt(body.upsell_product_id) || null : null,
      downsell_product_id: body.downsell_product_id ? parseInt(body.downsell_product_id) || null : null,
      bundle_items
    });

    const productId = (product && (product as any).lastInsertRowid) ? Number((product as any).lastInsertRowid) : null;
    return json({
      success: true,
      product_id: productId,
      slug,
      message: 'Produto importado com sucesso.'
    }, { status: 201 });
  } catch (e) {
    console.error('[IMPORT] Erro ao criar produto:', e);
    return json({ success: false, error: 'Erro ao criar o produto no banco.' }, { status: 500 });
  }
};
