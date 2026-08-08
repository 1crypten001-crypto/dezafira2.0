import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import crypto from 'crypto';
import { query, run } from '$lib/server/database';
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
 * Endpoint privado para sincronizar os posts de "O Reino" e configurar
 * banners e post_products de forma nativa na produção do Railway.
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

  try {
    const posts = postsData.posts;
    let insertedPostsCount = 0;
    let skippedPostsCount = 0;
    const postIds: number[] = [];

    // 1. Inserir posts no banco
    for (const p of posts) {
      const existing = await query("SELECT id FROM posts WHERE slug = ?", [p.slug]);
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
        const check = await query("SELECT id FROM posts WHERE slug = ?", [p.slug]);
        if (check.rows && check.rows.length > 0) {
          postIds.push(Number((check.rows[0] as any).id));
        }
      }
      insertedPostsCount++;
    }

    // 2. Vincular produto principal aos posts
    let linkedProductsCount = 0;
    const prodRes = await query("SELECT id FROM products WHERE slug = 'movimento-1convite'");
    if (prodRes.rows && prodRes.rows.length > 0) {
      const p1ConviteId = Number((prodRes.rows[0] as any).id);
      
      for (const pid of postIds) {
        const checkLink = await query(
          "SELECT 1 FROM post_products WHERE post_id = ? AND product_id = ?",
          [pid, p1ConviteId]
        );
        if (!checkLink.rows || checkLink.rows.length === 0) {
          await run(
            "INSERT INTO post_products (post_id, product_id) VALUES (?, ?)",
            [pid, p1ConviteId]
          );
          linkedProductsCount++;
        }
      }
    }

    // 3. Configurar Banners (ads)
    let adsCreated = 0;
    
    // Sidebar
    const sidebarAdName = "Banner 1Convite Sidebar";
    const checkSidebar = await query("SELECT id FROM ads WHERE name = ?", [sidebarAdName]);
    if (!checkSidebar.rows || checkSidebar.rows.length === 0) {
      await run(
        `INSERT INTO ads (name, placement, type, image_url, link_url, is_active, weight)
         VALUES (?, 'sidebar', 'image', ?, '/product/movimento-1convite', 1, 10)`,
        [
          sidebarAdName,
          "https://images.unsplash.com/photo-1511285560929-80b456fea0bc?w=500"
        ]
      );
      adsCreated++;
    }

    // Inline
    const inlineAdName = "Banner BibliaFlow Inline";
    const checkInline = await query("SELECT id FROM ads WHERE name = ?", [inlineAdName]);
    if (!checkInline.rows || checkInline.rows.length === 0) {
      await run(
        `INSERT INTO ads (name, placement, type, image_url, link_url, is_active, weight)
         VALUES (?, 'post_inline', 'image', ?, '/product/bibliaflow', 1, 5)`,
        [
          inlineAdName,
          "https://images.unsplash.com/photo-1481627834876-b7833e8f5570?w=800"
        ]
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
};
