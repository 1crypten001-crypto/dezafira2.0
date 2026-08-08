import fs from 'fs';
import path from 'path';
import dotenv from 'dotenv';

dotenv.config();

const DATABASE_URL = process.env.DATABASE_URL;
const DATABASE_AUTH_TOKEN = process.env.DATABASE_AUTH_TOKEN;
const USE_TURSO = !!DATABASE_URL;

console.log(`Conectando ao banco do Clube: ${USE_TURSO ? 'PRODUCAO (LibSQL)' : 'LOCAL (SQLite)'}`);

let db;
if (USE_TURSO) {
  const { createClient } = await import('@libsql/client');
  db = createClient({ url: DATABASE_URL, authToken: DATABASE_AUTH_TOKEN });
} else {
  const Database = (await import('better-sqlite3')).default;
  const dbPath = process.env.DATABASE_PATH || './blog.db';
  const sqliteDb = new Database(dbPath);
  db = {
    execute: async (sql, params = []) => {
      const stmt = sqliteDb.prepare(sql);
      if (sql.trim().toUpperCase().startsWith('SELECT')) {
        return { rows: stmt.all(...params) };
      }
      return stmt.run(...params);
    }
  };
}

async function run() {
  try {
    const jsonPath = path.resolve('../scripts/articles_export.json');
    if (!fs.existsSync(jsonPath)) {
      console.error(`Erro: Arquivo ${jsonPath} nao encontrado!`);
      process.exit(1);
    }

    const data = JSON.parse(fs.readFileSync(jsonPath, 'utf8'));
    const postsData = data.posts;

    console.log(`Carregados ${postsData.length} posts para importacao.`);

    let insertedPostsCount = 0;
    let skippedPostsCount = 0;
    const postIds = [];

    for (const p of postsData) {
      const res = await db.execute("SELECT id FROM posts WHERE slug = ?", [p.slug]);
      if (res.rows && res.rows.length > 0) {
        postIds.push(res.rows[0].id);
        skippedPostsCount++;
        continue;
      }

      console.log(`Inserindo post no Clube: ${p.title.substring(0, 40)}...`);
      const insertRes = await db.execute(
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
      
      const newId = insertRes.lastInsertRowid || insertRes.insertId;
      if (newId) {
        postIds.push(Number(newId));
      } else {
        const check = await db.execute("SELECT id FROM posts WHERE slug = ?", [p.slug]);
        if (check.rows && check.rows.length > 0) {
          postIds.push(check.rows[0].id);
        }
      }
      insertedPostsCount++;
    }

    console.log(`Posts importados: ${insertedPostsCount} | Ja existiam: ${skippedPostsCount}`);

    const prodRes = await db.execute("SELECT id, name FROM products WHERE slug = 'movimento-1convite'");
    if (prodRes.rows && prodRes.rows.length > 0) {
      const p1ConviteId = prodRes.rows[0].id;
      console.log(`Produto 'Movimento 1Convite' localizado (ID: ${p1ConviteId}). Vinculando aos posts...`);

      let linkedCount = 0;
      for (const pid of postIds) {
        const checkLink = await db.execute(
          "SELECT 1 FROM post_products WHERE post_id = ? AND product_id = ?",
          [pid, p1ConviteId]
        );
        if (!checkLink.rows || checkLink.rows.length === 0) {
          await db.execute(
            "INSERT INTO post_products (post_id, product_id) VALUES (?, ?)",
            [pid, p1ConviteId]
          );
          linkedCount++;
        }
      }
      console.log(`Vinculos de produto criados na tabela post_products: ${linkedCount}`);
    } else {
      console.log("Aviso: Produto principal 'movimento-1convite' nao encontrado no banco do Clube para vinculacao.");
    }

    console.log("\nConfigurando banners de anuncios (ads)...");
    
    const sidebarAdName = "Banner 1Convite Sidebar";
    const checkSidebar = await db.execute("SELECT id FROM ads WHERE name = ?", [sidebarAdName]);
    if (!checkSidebar.rows || checkSidebar.rows.length === 0) {
      console.log("Criando banner de sidebar para 1Convite...");
      await db.execute(
        `INSERT INTO ads (name, placement, type, image_url, link_url, is_active, weight)
         VALUES (?, 'sidebar', 'image', ?, '/product/movimento-1convite', 1, 10)`,
        [
          sidebarAdName,
          "https://images.unsplash.com/photo-1511285560929-80b456fea0bc?w=500"
        ]
      );
    } else {
      console.log("Banner de sidebar ja existe.");
    }

    const inlineAdName = "Banner BibliaFlow Inline";
    const checkInline = await db.execute("SELECT id FROM ads WHERE name = ?", [inlineAdName]);
    if (!checkInline.rows || checkInline.rows.length === 0) {
      console.log("Criando banner inline no texto para BibliaFlow...");
      await db.execute(
        `INSERT INTO ads (name, placement, type, image_url, link_url, is_active, weight)
         VALUES (?, 'post_inline', 'image', ?, '/product/bibliaflow', 1, 5)`,
        [
          inlineAdName,
          "https://images.unsplash.com/photo-1481627834876-b7833e8f5570?w=800"
        ]
      );
    } else {
      console.log("Banner inline ja existe.");
    }

    console.log("\n--- SINCRONIZACAO DO CLUBE CONCLUIDA COM SUCESSO ---");
  } catch (error) {
    console.error("Erro na execucao do script:", error);
    process.exit(1);
  }
}

run();
