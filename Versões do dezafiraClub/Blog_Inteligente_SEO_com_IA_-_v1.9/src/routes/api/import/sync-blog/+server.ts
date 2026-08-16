import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import crypto from 'crypto';
import {
  query, run, createPost, createAd, assignProductsToPost,
  createCategory, assignCategoriesToPost
} from '$lib/server/database';
import { env } from '$env/dynamic/private';
import postsData from '$lib/server/articles_export.json' assert { type: 'json' };

function safeEqual(a: string, b: string): boolean {
  const ba = Buffer.from(a);
  const bb = Buffer.from(b);
  if (ba.length !== bb.length) return false;
  return crypto.timingSafeEqual(ba, bb);
}

/**
 * POST /api/import/sync-blog
 *
 * Ponte DezafiraAdm → DezafiraClube. DOIS modos:
 *
 * 1) BLUEPRINT (novo, generalizado) — body:
 *    {
 *      product_slug: string,          // slug do produto do catálogo (vínculo post_products)
 *      posts: [{ title, slug, content, excerpt?, cover_image?, tags?, youtube_video_url?, published? }],
 *      ads:   [{ name, placement, type, image_url?, link_url?, weight?, youtube_video_url? }],
 *      category?: string              // cria/usa a categoria e atribui aos posts
 *    }
 *
 * 2) LEGADO (sem body) — sincroniza os posts de "O Reino" a partir de
 *    articles_export.json, vincula o produto 'movimento-1convite' e cria
 *    os banners fixos (compatibilidade com o comportamento original).
 */
export const POST: RequestHandler = async ({ request }) => {
  const importKey = env.IMPORT_API_KEY || '';
  const providedKey = request.headers.get('x-import-key') || '';

  if (!importKey) {
    return json({ success: false, error: 'IMPORT_API_KEY não configurado neste serviço.' }, { status: 503 });
  }
  if (!safeEqual(providedKey, importKey)) {
    return json({ success: false, error: 'Chave de importação inválida.' }, { status: 401 });
  }

  let body: any = null;
  try {
    body = await request.json();
  } catch {
    body = null;
  }

  if (body && Array.isArray(body.posts)) {
    return handleBlueprintSync(body);
  }
  return handleLegacySync();
};

// ── Modo 1 · BLUEPRINT ───────────────────────────────────────────────────────

async function handleBlueprintSync(body: any) {
  try {
    const posts = Array.isArray(body.posts) ? body.posts : [];
    const ads = Array.isArray(body.ads) ? body.ads : [];
    const productSlug = String(body.product_slug || '').trim();

    // Resolve o produto do catálogo pelo slug (para vínculo post_products)
    let productId: number | null = null;
    if (productSlug) {
      const prodRes = await query('SELECT id FROM products WHERE slug = ?', [productSlug]);
      if (prodRes.rows && prodRes.rows.length > 0) {
        productId = Number((prodRes.rows[0] as any).id);
      }
    }

    // 1. Posts (skip se o slug já existe — idempotente)
    let insertedPostsCount = 0;
    let skippedPostsCount = 0;
    let linkedProductsCount = 0;
    const postIds: number[] = [];

    for (const p of posts) {
      const slug = String(p.slug || '').trim();
      if (!slug) continue;
      const existing = await query('SELECT id FROM posts WHERE slug = ?', [slug]);
      if (existing.rows && existing.rows.length > 0) {
        postIds.push(Number((existing.rows[0] as any).id));
        skippedPostsCount++;
        continue;
      }
      const insertRes = await createPost({
        title: String(p.title || ''),
        slug,
        content: String(p.content || ''),
        excerpt: p.excerpt ? String(p.excerpt) : undefined,
        cover_image: p.cover_image ? String(p.cover_image) : undefined,
        tags: p.tags ? String(p.tags) : undefined,
        youtube_video_url: p.youtube_video_url ? String(p.youtube_video_url) : undefined,
        published: p.published !== undefined ? Number(p.published) : 1
      });
      const newId = (insertRes as any).lastInsertRowid || (insertRes as any).insertId;
      if (newId) {
        postIds.push(Number(newId));
        insertedPostsCount++;
      }
    }

    // 2. Vínculo produto ↔ posts
    if (productId && postIds.length > 0) {
      for (const pid of postIds) {
        const checkLink = await query(
          'SELECT 1 FROM post_products WHERE post_id = ? AND product_id = ?', [pid, productId]
        );
        if (!checkLink.rows || checkLink.rows.length === 0) {
          await run('INSERT INTO post_products (post_id, product_id) VALUES (?, ?)', [pid, productId]);
          linkedProductsCount++;
        }
      }
    }

    // 3. Categoria (opcional — cria se faltar e atribui aos posts)
    let categoryId: number | null = null;
    if (body.category) {
      const catSlug = String(body.category).toLowerCase().trim()
        .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
        .replace(/[^a-z0-9\s-]/g, '').replace(/[\s_]+/g, '-').replace(/-+/g, '-')
        .replace(/^-+|-+$/g, '').substring(0, 60);
      const catRes = await query('SELECT id FROM categories WHERE slug = ?', [catSlug]);
      if (catRes.rows && catRes.rows.length > 0) {
        categoryId = Number((catRes.rows[0] as any).id);
      } else {
        const catIns = await createCategory(String(body.category), catSlug);
        const catNewId = (catIns as any).lastInsertRowid;
        categoryId = catNewId ? Number(catNewId) : null;
      }
      if (categoryId && postIds.length > 0) {
        await assignCategoriesToPost(postIds[0], [categoryId]);
      }
    }

    // 4. Banners (ads) — idempotente por nome
    let adsCreated = 0;
    for (const ad of ads) {
      const name = String(ad.name || '').trim();
      if (!name) continue;
      const checkAd = await query('SELECT id FROM ads WHERE name = ?', [name]);
      if (checkAd.rows && checkAd.rows.length > 0) continue;
      await createAd({
        name,
        placement: String(ad.placement || 'sidebar'),
        type: String(ad.type || 'image'),
        image_url: ad.image_url ? String(ad.image_url) : undefined,
        link_url: ad.link_url ? String(ad.link_url) : undefined,
        weight: ad.weight ? Number(ad.weight) : 1,
        youtube_video_url: ad.youtube_video_url ? String(ad.youtube_video_url) : undefined
      });
      adsCreated++;
    }

    return json({
      success: true,
      summary: {
        posts_inserted: insertedPostsCount,
        posts_skipped: skippedPostsCount,
        posts_linked: linkedProductsCount,
        ads_created: adsCreated,
        product_id: productId
      },
      message: 'Sincronização blueprint concluída.'
    }, { status: 200 });
  } catch (error: any) {
    console.error('[SYNC-BLUEPRINT] Erro:', error);
    return json({ success: false, error: error.message || 'Erro na sincronização blueprint.' }, { status: 500 });
  }
}

// ── Modo 2 · LEGADO (comportamento original) ─────────────────────────────────

async function handleLegacySync() {
  try {
    const posts = postsData.posts;
    let insertedPostsCount = 0;
    let skippedPostsCount = 0;
    const postIds: number[] = [];

    for (const p of posts) {
      const existing = await query('SELECT id FROM posts WHERE slug = ?', [p.slug]);
      if (existing.rows && existing.rows.length > 0) {
        postIds.push(Number((existing.rows[0] as any).id));
        skippedPostsCount++;
        continue;
      }

      const insertRes = await run(
        `INSERT INTO posts (title, slug, content, excerpt, cover_image, published, created_at, updated_at)
         VALUES (?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)`,
        [
          p.title,
          p.slug,
          p.content,
          p.excerpt || '',
          p.featured_image_url || 'https://images.unsplash.com/photo-1481627834876-b7833e8f5570?w=800'
        ]
      );

      const newId = (insertRes as any).lastInsertRowid || (insertRes as any).insertId;
      if (newId) {
        postIds.push(Number(newId));
      } else {
        const check = await query('SELECT id FROM posts WHERE slug = ?', [p.slug]);
        if (check.rows && check.rows.length > 0) {
          postIds.push(Number((check.rows[0] as any).id));
        }
      }
      insertedPostsCount++;
    }

    // Vincular produto principal aos posts
    let linkedProductsCount = 0;
    const prodRes = await query("SELECT id FROM products WHERE slug = 'movimento-1convite'");
    if (prodRes.rows && prodRes.rows.length > 0) {
      const p1ConviteId = Number((prodRes.rows[0] as any).id);

      for (const pid of postIds) {
        const checkLink = await query(
          'SELECT 1 FROM post_products WHERE post_id = ? AND product_id = ?', [pid, p1ConviteId]
        );
        if (!checkLink.rows || checkLink.rows.length === 0) {
          await run('INSERT INTO post_products (post_id, product_id) VALUES (?, ?)', [pid, p1ConviteId]);
          linkedProductsCount++;
        }
      }
    }

    // Banners (ads)
    let adsCreated = 0;
    const sidebarAdName = 'Banner 1Convite Sidebar';
    const checkSidebar = await query('SELECT id FROM ads WHERE name = ?', [sidebarAdName]);
    if (!checkSidebar.rows || checkSidebar.rows.length === 0) {
      await run(
        `INSERT INTO ads (name, placement, type, image_url, link_url, is_active, weight)
         VALUES (?, 'sidebar', 'image', ?, '/product/movimento-1convite', 1, 10)`,
        [sidebarAdName, 'https://images.unsplash.com/photo-1511285560929-80b456fea0bc?w=500']
      );
      adsCreated++;
    }

    const inlineAdName = 'Banner BibliaFlow Inline';
    const checkInline = await query('SELECT id FROM ads WHERE name = ?', [inlineAdName]);
    if (!checkInline.rows || checkInline.rows.length === 0) {
      await run(
        `INSERT INTO ads (name, placement, type, image_url, link_url, is_active, weight)
         VALUES (?, 'post_inline', 'image', ?, '/product/bibliaflow', 1, 5)`,
        [inlineAdName, 'https://images.unsplash.com/photo-1481627834876-b7833e8f5570?w=800']
      );
      adsCreated++;
    }

    return json({
      success: true,
      summary: {
        posts_inserted: insertedPostsCount,
        posts_skipped: skippedPostsCount,
        posts_linked: linkedProductsCount,
        ads_created: adsCreated
      },
      message: 'Sincronização do blog e ofertas concluída com sucesso em produção.'
    }, { status: 200 });
  } catch (error: any) {
    console.error('[SYNC] Erro na sincronização:', error);
    return json({ success: false, error: error.message || 'Erro interno na sincronização do blog.' }, { status: 500 });
  }
}
