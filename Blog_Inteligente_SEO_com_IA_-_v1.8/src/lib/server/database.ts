import { env } from '$env/dynamic/private';

const DATABASE_URL = env.DATABASE_URL;
const DATABASE_AUTH_TOKEN = env.DATABASE_AUTH_TOKEN;
const USE_TURSO = !!DATABASE_URL;

let client: any = null;
let clientPromise: Promise<any> | null = null;

async function getClient() {
  if (clientPromise) return clientPromise;

  clientPromise = (async () => {
    let localClient: any = null;
    if (USE_TURSO) {
      const { createClient } = await import('@libsql/client');
      localClient = createClient({ url: DATABASE_URL, authToken: DATABASE_AUTH_TOKEN });
    } else {
      const Database = (await import('better-sqlite3')).default;
      const dbPath = env.DATABASE_PATH || './blog.db';
      const sqliteDb = new Database(dbPath);
      sqliteDb.pragma('journal_mode = WAL');
      sqliteDb.pragma('busy_timeout = 5000');
      
      localClient = {
        execute: async (sql: string, params: any[] = []) => {
          const stmt = sqliteDb.prepare(sql);
          if (sql.trim().toUpperCase().startsWith('SELECT')) {
            return { rows: stmt.all(...params) };
          }
          return stmt.run(...params);
        }
      };
    }
    
    client = localClient;
    // Garantir que a estrutura do banco esteja atualizada
    await initDatabase();
    
    return localClient;
  })();

  return clientPromise;
}

export interface Post {
  id: number;
  title: string;
  slug: string;
  content: string;
  excerpt: string | null;
  cover_image: string | null;
  published: number;
  pinterest_enabled: number;
  pinterest_image: string | null;
  is_premium?: number;
  is_18_plus?: number;
  view_count?: number;
  created_at: string;
  updated_at: string;
  categories?: string;
  category_ids?: string;
  category_name?: string;
  is_featured?: number;
  youtube_video_url?: string | null;
  tags?: string | null;
}


export interface Category {
  id: number;
  name: string;
  slug: string;
  description?: string | null;
  pinterest_enabled?: number;
  updated_at?: string;
  post_count?: number;
}

export interface User {
  id: number;
  username: string;
  password: string;
  role?: string;
  name?: string;
  cpf?: string;
  phone?: string;
  created_at: string;
}

export interface Setting {
  key: string;
  value: string;
}

export interface PremiumPlan {
  id: number;
  name: string;
  slug: string;
  description: string | null;
  price_cents: number;
  interval_days: number;
  mp_plan_id: string | null;
  asaas_plan_id: string | null;
  features: any;
  is_active: number;
  created_at: string;
}

export async function initDatabase() {
  // 1. Criar Tabelas Base se não existirem
  try {
    await exec(`
      CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT DEFAULT 'member',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
      )
    `);
  } catch (e) {
    console.error('Error creating users table:', e);
  }

  try {
    await exec(`
      CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
      )
    `);
  } catch (e) {
    console.error('Error creating settings table:', e);
  }

  try {
    await exec(`
      CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        slug TEXT UNIQUE NOT NULL,
        content TEXT NOT NULL,
        excerpt TEXT,
        cover_image TEXT,
        published INTEGER DEFAULT 0,
        pinterest_enabled INTEGER DEFAULT 0,
        pinterest_image TEXT,
        is_premium INTEGER DEFAULT 0,
        is_18_plus INTEGER DEFAULT 0,
        youtube_video_url TEXT,
        tags TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
      )
    `);
  } catch (e) {
    console.error('Error creating posts table:', e);
  }

  try {
    await exec(`
      CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        slug TEXT UNIQUE NOT NULL,
        description TEXT,
        pinterest_enabled INTEGER DEFAULT 0,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
      )
    `);
  } catch (e) {
    console.error('Error creating categories table:', e);
  }

  try {
    await exec(`
      CREATE TABLE IF NOT EXISTS sessions (
        id TEXT PRIMARY KEY,
        username TEXT NOT NULL,
        expires_at INTEGER NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
      )
    `);
  } catch (e) {
    console.error('Error creating sessions table:', e);
  }

  try {
    await exec(`
      CREATE TABLE IF NOT EXISTS post_categories (
        post_id INTEGER NOT NULL,
        category_id INTEGER NOT NULL,
        PRIMARY KEY (post_id, category_id),
        FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
        FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
      )
    `);
  } catch (e) {
    console.error('Error creating post_categories table:', e);
  }

  try {
    await exec(`
      CREATE TABLE IF NOT EXISTS ads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        placement TEXT NOT NULL,
        type TEXT NOT NULL,
        content TEXT,
        image_url TEXT,
        link_url TEXT,
        is_active INTEGER DEFAULT 1,
        weight INTEGER DEFAULT 1,
        style TEXT,
        youtube_video_url TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
      )
    `);
  } catch (e) {
    console.error('Error creating ads table:', e);
  }

  try {
    await exec(`
      CREATE TABLE IF NOT EXISTS premium_plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        slug TEXT UNIQUE NOT NULL,
        description TEXT,
        price_cents INTEGER NOT NULL,
        interval_days INTEGER NOT NULL DEFAULT 30,
        mp_plan_id TEXT,
        asaas_plan_id TEXT,
        features TEXT,
        is_active INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
      )
    `);
  } catch (e) {
    console.error('Error creating premium_plans table:', e);
  }

  try {
    await exec(`
      CREATE TABLE IF NOT EXISTS user_interests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        interest_type TEXT NOT NULL,
        name TEXT NOT NULL,
        score INTEGER DEFAULT 0,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        UNIQUE(user_id, interest_type, name)
      )
    `);
  } catch (e) {
    console.error('Error creating user_interests table:', e);
  }

  try {
    await exec(`
      CREATE TABLE IF NOT EXISTS premium_subscriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        plan_id INTEGER NOT NULL,
        mp_subscription_id TEXT,
        mp_payment_id TEXT,
        asaas_subscription_id TEXT,
        asaas_customer_id TEXT,
        status TEXT NOT NULL DEFAULT 'pending',
        started_at DATETIME,
        expires_at DATETIME,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (plan_id) REFERENCES premium_plans(id)
      )
    `);
  } catch (e) {
    console.error('Error creating premium_subscriptions table:', e);
  }

  try {
    await exec(`
      CREATE TABLE IF NOT EXISTS premium_payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subscription_id INTEGER,
        mp_payment_id TEXT UNIQUE,
        asaas_payment_id TEXT,
        amount_cents INTEGER NOT NULL,
        status TEXT NOT NULL,
        payment_method TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (subscription_id) REFERENCES premium_subscriptions(id)
      )
    `);
  } catch (e) {
    console.error('Error creating premium_payments table:', e);
  }

  try {
    await exec(`
      CREATE TABLE IF NOT EXISTS collaborative_recommendations (
        from_post_id INTEGER NOT NULL,
        to_post_id INTEGER NOT NULL,
        score INTEGER DEFAULT 0,
        PRIMARY KEY (from_post_id, to_post_id),
        FOREIGN KEY (from_post_id) REFERENCES posts(id) ON DELETE CASCADE,
        FOREIGN KEY (to_post_id) REFERENCES posts(id) ON DELETE CASCADE
      )
    `);
  } catch (e) {
    console.error('Error creating collaborative_recommendations table:', e);
  }

  // Recently-seen posts (YouTube-style temporary feed suppression)
  try {
    await exec(`
      CREATE TABLE IF NOT EXISTS user_seen_posts (
        user_id INTEGER NOT NULL,
        post_id INTEGER NOT NULL,
        seen_at INTEGER NOT NULL,
        PRIMARY KEY (user_id, post_id),
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE
      )
    `);
  } catch (e) {
    console.error('Error creating user_seen_posts table:', e);
  }
  try {
    await exec('CREATE INDEX IF NOT EXISTS idx_user_seen_posts_user_seen ON user_seen_posts(user_id, seen_at)');
  } catch (e) {
    // index may already exist
  }

  // 2. Criar tabelas adicionais e migrações
  try {
    await exec('ALTER TABLE posts ADD COLUMN is_18_plus INTEGER DEFAULT 0');
  } catch (e) {

    // Column likely already exists
  }

  try {
    await exec('ALTER TABLE posts ADD COLUMN youtube_video_url TEXT');
  } catch (e) {
    // Column likely already exists
  }

  try {
    await exec('ALTER TABLE posts ADD COLUMN tags TEXT');
  } catch (e) {
    // Column likely already exists
  }

  try {
    await exec('ALTER TABLE ads ADD COLUMN youtube_video_url TEXT');
  } catch (e) {
    // Column likely already exists
  }

  try {
    await exec(`
      CREATE TABLE IF NOT EXISTS newsletter_subscribers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        name TEXT,
        status TEXT DEFAULT 'active',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
      )
    `);
  } catch (e) {
    console.error('Error creating newsletter_subscribers table:', e);
  }

  try {
    await exec(`
      CREATE TABLE IF NOT EXISTS newsletter_campaigns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject TEXT NOT NULL,
        content TEXT NOT NULL,
        youtube_video_url TEXT,
        recipients_count INTEGER NOT NULL,
        sent_at DATETIME DEFAULT CURRENT_TIMESTAMP
      )
    `);
  } catch (e) {
    console.error('Error creating newsletter_campaigns table:', e);
  }


  try {
    await exec(`
      CREATE TABLE IF NOT EXISTS page_views (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        page_type TEXT NOT NULL,
        slug TEXT,
        ip_address TEXT,
        user_agent TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
      )
    `);
    // Add user_agent column to existing tables that don't have it yet
    await exec(`ALTER TABLE page_views ADD COLUMN user_agent TEXT`).catch(() => {});
    // Performance index for dedup queries
    await exec(`CREATE INDEX IF NOT EXISTS idx_pv_dedup ON page_views (ip_address, slug, created_at)`).catch(() => {});
  } catch (e) {
    console.error('Error creating page_views table:', e);
  }

  // Migrações do Asaas e Área de Membros
  try {
    await exec('ALTER TABLE users ADD COLUMN role TEXT DEFAULT "member"');
  } catch (e) {}

  try {
    await exec('ALTER TABLE users ADD COLUMN name TEXT');
  } catch (e) {}

  try {
    await exec('ALTER TABLE users ADD COLUMN cpf TEXT');
  } catch (e) {}

  try {
    await exec('ALTER TABLE users ADD COLUMN phone TEXT');
  } catch (e) {}

  try {
    await exec('ALTER TABLE premium_plans ADD COLUMN asaas_plan_id TEXT');
  } catch (e) {}

  try {
    await exec('ALTER TABLE premium_subscriptions ADD COLUMN asaas_subscription_id TEXT');
  } catch (e) {}

  try {
    await exec('ALTER TABLE premium_subscriptions ADD COLUMN asaas_customer_id TEXT');
  } catch (e) {}

  try {
    await exec('ALTER TABLE premium_payments ADD COLUMN asaas_payment_id TEXT');
  } catch (e) {}

  // Stripe columns (optional gateway; Asaas remains default)
  try {
    await exec('ALTER TABLE premium_subscriptions ADD COLUMN stripe_subscription_id TEXT');
  } catch (e) {}
  try {
    await exec('ALTER TABLE premium_subscriptions ADD COLUMN stripe_customer_id TEXT');
  } catch (e) {}
  try {
    await exec('ALTER TABLE premium_payments ADD COLUMN stripe_payment_id TEXT');
  } catch (e) {}
  try {
    await exec('ALTER TABLE product_purchases ADD COLUMN stripe_session_id TEXT');
  } catch (e) {}
  try {
    await exec('ALTER TABLE course_purchases ADD COLUMN stripe_session_id TEXT');
  } catch (e) {}

  try {
    await exec('ALTER TABLE products ADD COLUMN image_url TEXT');
  } catch (e) {}

  try {
    await exec('ALTER TABLE products ADD COLUMN slug TEXT');
    // Backfill any products without a slug
    const productsWithoutSlug = await query('SELECT id, name FROM products WHERE slug IS NULL OR slug = ""');
    if (productsWithoutSlug && productsWithoutSlug.length > 0) {
      for (const prod of productsWithoutSlug) {
        let baseSlug = prod.name
          .toLowerCase()
          .trim()
          .normalize('NFD')
          .replace(/[\u0300-\u036f]/g, '')
          .replace(/[^a-z0-9\s-]/g, '')
          .replace(/[\s_]+/g, '-')
          .replace(/-+/g, '-')
          .replace(/^-+|-+$/g, '')
          .substring(0, 60);
        if (!baseSlug) baseSlug = `produto-${prod.id}`;
        
        let slug = baseSlug;
        let counter = 2;
        while (true) {
          const check = await queryOne('SELECT id FROM products WHERE slug = ? AND id != ?', [slug, prod.id]);
          if (!check) break;
          slug = `${baseSlug}-${counter}`;
          counter++;
        }
        await run('UPDATE products SET slug = ? WHERE id = ?', [slug, prod.id]);
      }
    }
  } catch (e) {}

  // Criar products ANTES das migrations ALTER TABLE
  try {
    await exec(`
      CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        slug TEXT UNIQUE,
        description TEXT,
        price_cents INTEGER NOT NULL DEFAULT 0,
        file_url TEXT,
        external_link TEXT,
        image_url TEXT,
        youtube_video_url TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
      )
    `);
  } catch (e) {}

  try {
    await exec('ALTER TABLE products ADD COLUMN category TEXT');
  } catch (e) {}

  try {
    await exec(`
      CREATE TABLE IF NOT EXISTS product_categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        slug TEXT UNIQUE NOT NULL,
        description TEXT
      )
    `);
  } catch (e) {
    console.error('Error creating product_categories table:', e);
  }

  try {
    await exec('ALTER TABLE products ADD COLUMN category_id INTEGER REFERENCES product_categories(id) ON DELETE SET NULL');
  } catch (e) {}

  // Migrate existing text categories in `category` column to `category_id`
  try {
    const productsToMigrate = await query("SELECT id, category FROM products WHERE category IS NOT NULL AND category != '' AND category_id IS NULL");
    if (productsToMigrate && productsToMigrate.length > 0) {
      for (const prod of productsToMigrate) {
        const catName = prod.category.trim();
        // Check if category already exists in product_categories
        let cat = await queryOne('SELECT id FROM product_categories WHERE name = ?', [catName]);
        if (!cat) {
          // Create it
          let baseSlug = catName
            .toLowerCase()
            .trim()
            .normalize('NFD')
            .replace(/[\u0300-\u036f]/g, '')
            .replace(/[^a-z0-9\s-]/g, '')
            .replace(/[\s_]+/g, '-')
            .replace(/-+/g, '-')
            .replace(/^-+|-+$/g, '')
            .substring(0, 60);
          if (!baseSlug) baseSlug = `categoria-${Date.now()}`;
          
          let slug = baseSlug;
          let counter = 2;
          while (true) {
            const check = await queryOne('SELECT id FROM product_categories WHERE slug = ?', [slug]);
            if (!check) break;
            slug = `${baseSlug}-${counter}`;
            counter++;
          }
          await run('INSERT INTO product_categories (name, slug) VALUES (?, ?)', [catName, slug]);
          cat = await queryOne('SELECT id FROM product_categories WHERE name = ?', [catName]);
        }
        if (cat) {
          await run('UPDATE products SET category_id = ? WHERE id = ?', [cat.id, prod.id]);
        }
      }
    }
  } catch (e) {
    console.error('Error migrating product categories:', e);
  }

  try {
    await exec(`
      CREATE TABLE IF NOT EXISTS member_otps (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT NOT NULL,
        code TEXT NOT NULL,
        expires_at DATETIME NOT NULL,
        used INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
      )
    `);
  } catch (e) {
    console.error('Error creating member_otps table:', e);
  }

  try {
    await exec(`
      CREATE TABLE IF NOT EXISTS shortlinks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        slug TEXT UNIQUE NOT NULL,
        destination_url TEXT NOT NULL,
        use_ad_interstitial INTEGER DEFAULT 0,
        ad_duration_seconds INTEGER DEFAULT 5,
        clicks_count INTEGER DEFAULT 0,
        is_indexed INTEGER DEFAULT 0,
        meta_title TEXT,
        meta_description TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
      )
    `);
  } catch (e) {
    console.error('Error creating shortlinks table:', e);
  }

  try {
    await exec(`ALTER TABLE shortlinks ADD COLUMN is_indexed INTEGER DEFAULT 0`);
  } catch (e) {
    // Ignore error if column already exists
  }

  try {
    await exec(`ALTER TABLE shortlinks ADD COLUMN meta_title TEXT`);
  } catch (e) {
    // Ignore error if column already exists
  }

  try {
    await exec(`ALTER TABLE shortlinks ADD COLUMN meta_description TEXT`);
  } catch (e) {
    // Ignore error if column already exists
  }

  try {
    await exec(`ALTER TABLE shortlinks ADD COLUMN fixed_ad_id INTEGER DEFAULT NULL`);
  } catch (e) {
    // Ignore error if column already exists
  }

  // Web Stories (AMP) — Ferramentas
  try {
    await exec(`
      CREATE TABLE IF NOT EXISTS web_stories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        slug TEXT UNIQUE NOT NULL,
        cover_image TEXT,
        poster_portrait TEXT,
        source_type TEXT DEFAULT 'manual',
        source_post_id INTEGER,
        cta_url TEXT,
        cta_text TEXT,
        published INTEGER DEFAULT 0,
        sort_order INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
      )
    `);
  } catch (e) {
    console.error('Error creating web_stories table:', e);
  }

  try {
    await exec(`
      CREATE TABLE IF NOT EXISTS web_story_slides (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        story_id INTEGER NOT NULL,
        sort_order INTEGER DEFAULT 0,
        background_image TEXT,
        title TEXT,
        body TEXT,
        cta_url TEXT,
        cta_text TEXT,
        FOREIGN KEY (story_id) REFERENCES web_stories(id) ON DELETE CASCADE
      )
    `);
  } catch (e) {
    console.error('Error creating web_story_slides table:', e);
  }

  try {
    await exec(`
      CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        slug TEXT UNIQUE,
        description TEXT,
        price_cents INTEGER NOT NULL DEFAULT 0,
        file_url TEXT,
        external_link TEXT,
        image_url TEXT,
        youtube_video_url TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
      )
    `);
  } catch (e) {
    console.error('Error creating products table:', e);
  }

  try {
    await exec(`
      CREATE TABLE IF NOT EXISTS post_products (
        post_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        PRIMARY KEY (post_id, product_id),
        FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
        FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
      )
    `);
  } catch (e) {
    console.error('Error creating post_products table:', e);
  }

  try {
    await exec(`
      CREATE TABLE IF NOT EXISTS product_purchases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        product_id INTEGER,
        product_name_snapshot TEXT,
        price_cents INTEGER,
        status TEXT DEFAULT 'pending',
        asaas_payment_id TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL
      )
    `);
  } catch (e) {
    console.error('Error creating product_purchases table:', e);
  }

  // Migration: preservar nome do produto mesmo se for excluído
  try {
    await exec(`ALTER TABLE product_purchases ADD COLUMN product_name_snapshot TEXT`);
  } catch (_) { /* column already exists */ }

  // Migration: preservar preço pago pelo produto no momento da compra
  try {
    await exec(`ALTER TABLE product_purchases ADD COLUMN price_cents INTEGER`);
  } catch (_) { /* column already exists */ }

  // Migration: adicionar url do video do youtube nos produtos
  try {
    await exec(`ALTER TABLE products ADD COLUMN youtube_video_url TEXT`);
  } catch (_) { /* column already exists */ }

  // Migration: tipo de recurso do produto (file, cloudinary, link, manual)
  try {
    await exec(`ALTER TABLE products ADD COLUMN resource_type TEXT DEFAULT 'file'`);
  } catch (_) { /* column already exists */ }

  // Migration: label do campo de identificação do comprador (ex: "Seu Gmail", "Seu usuário GitHub")
  try {
    await exec(`ALTER TABLE products ADD COLUMN access_label TEXT`);
  } catch (_) { /* column already exists */ }

  // Migration: instruções pós-compra para produtos com entrega manual
  try {
    await exec(`ALTER TABLE products ADD COLUMN drive_instructions TEXT`);
  } catch (_) { /* column already exists */ }

  // Migration: prazo de entrega estimado para produtos com entrega manual
  try {
    await exec(`ALTER TABLE products ADD COLUMN delivery_deadline TEXT`);
  } catch (_) { /* column already exists */ }

  // Migration: indicar se o produto está incluso na assinatura Premium
  try {
    await exec(`ALTER TABLE products ADD COLUMN is_premium_included INTEGER DEFAULT 0`);
  } catch (_) { /* column already exists */ }

  // Migration: identificador do comprador (Gmail, GitHub, etc.) para produtos com entrega manual
  try {
    await exec(`ALTER TABLE product_purchases ADD COLUMN buyer_access_id TEXT`);
  } catch (_) { /* column already exists */ }

  // Migration: oferta de serviço extra / order bump nos produtos
  try {
    await exec(`ALTER TABLE products ADD COLUMN has_extra_service INTEGER DEFAULT 0`);
  } catch (_) { /* column already exists */ }
  try {
    await exec(`ALTER TABLE products ADD COLUMN extra_service_title TEXT`);
  } catch (_) { /* column already exists */ }
  try {
    await exec(`ALTER TABLE products ADD COLUMN extra_service_price_cents INTEGER DEFAULT 0`);
  } catch (_) { /* column already exists */ }
  try {
    await exec(`ALTER TABLE products ADD COLUMN extra_service_description TEXT`);
  } catch (_) { /* column already exists */ }

  // Migration: registro de contratação do serviço extra na compra
  try {
    // Migration: esteira de produtos (upsell/downsell pós-compra)
    try {
      await exec(`ALTER TABLE products ADD COLUMN upsell_product_id INTEGER`);
    } catch (_) { /* column already exists */ }
    try {
      await exec(`ALTER TABLE products ADD COLUMN downsell_product_id INTEGER`);
    } catch (_) { /* column already exists */ }

    await exec(`ALTER TABLE product_purchases ADD COLUMN has_extra_service INTEGER DEFAULT 0`);
  } catch (_) { /* column already exists */ }
  try {
    await exec(`ALTER TABLE product_purchases ADD COLUMN extra_service_title_snapshot TEXT`);
  } catch (_) { /* column already exists */ }
  try {
    await exec(`ALTER TABLE product_purchases ADD COLUMN extra_service_price_cents INTEGER DEFAULT 0`);
  } catch (_) { /* column already exists */ }

  // Migration: Criar tabela de avaliações de produtos (product_reviews)
  try {
    await exec(`
      CREATE TABLE IF NOT EXISTS product_reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        rating INTEGER NOT NULL CHECK(rating >= 1 AND rating <= 5),
        comment TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
        UNIQUE(product_id, user_id)
      )
    `);
  } catch (e) {
    console.error('Error creating product_reviews table:', e);
  }

  // ── Área de Membros: Cursos ──────────────────────────────────────────────
  try {
    await exec(`
      CREATE TABLE IF NOT EXISTS member_courses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        slug TEXT UNIQUE NOT NULL,
        description TEXT,
        cover_image TEXT,
        access_type TEXT DEFAULT 'premium',
        price_cents INTEGER DEFAULT 0,
        asaas_product_id TEXT,
        published INTEGER DEFAULT 0,
        sort_order INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
      )
    `);
  } catch (e) {
    console.error('Error creating member_courses table:', e);
  }

  try {
    await exec(`
      CREATE TABLE IF NOT EXISTS member_lessons (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        content TEXT,
        video_url TEXT,
        video_type TEXT DEFAULT 'youtube',
        topic TEXT,
        sort_order INTEGER DEFAULT 0,
        published INTEGER DEFAULT 1,
        is_preview INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (course_id) REFERENCES member_courses(id) ON DELETE CASCADE
      )
    `);
  } catch (e) {
    console.error('Error creating member_lessons table:', e);
  }

  // Migration: add topic column if missing
  try {
    await exec(`ALTER TABLE member_lessons ADD COLUMN topic TEXT`);
  } catch (_) { /* column already exists */ }

  try {
    await exec(`
      CREATE TABLE IF NOT EXISTS member_materials (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_id INTEGER,
        title TEXT NOT NULL,
        description TEXT,
        file_url TEXT NOT NULL,
        file_type TEXT,
        sort_order INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (course_id) REFERENCES member_courses(id) ON DELETE SET NULL
      )
    `);
  } catch (e) {
    console.error('Error creating member_materials table:', e);
  }

  try {
    await exec(`
      CREATE TABLE IF NOT EXISTS course_purchases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        course_id INTEGER NOT NULL,
        status TEXT DEFAULT 'pending',
        asaas_payment_id TEXT,
        amount_cents INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (course_id) REFERENCES member_courses(id) ON DELETE CASCADE
      )
    `);
  } catch (e) {
    console.error('Error creating course_purchases table:', e);
  }

  try {
    await exec(`
      CREATE TABLE IF NOT EXISTS product_downloads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        downloaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
      )
    `);
  } catch (e) {
    console.error('Error creating product_downloads table:', e);
  }

  try {
    await exec(`
      CREATE TABLE IF NOT EXISTS landing_pages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        slug TEXT UNIQUE NOT NULL,
        status TEXT DEFAULT 'draft',
        content TEXT NOT NULL DEFAULT '[]',
        settings TEXT NOT NULL DEFAULT '{}',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
      )
    `);
  } catch (e) {
    console.error('Error creating landing_pages table:', e);
  }

  // 3. Semear configurações padrões se o banco estiver vazio
  try {
    const siteTitleSetting = await queryOne("SELECT key FROM settings WHERE key = 'site_title'");
    if (!siteTitleSetting) {
      console.log('Seeding default settings...');
      const defaultSettings = [
        { key: 'site_title', value: 'Meu Blog Svelte' },
        { key: 'site_description', value: 'Um blog moderno feito com SvelteKit e SQLite' },
        { key: 'feed_loading_mode', value: 'pagination' },
        { key: 'site_logo', value: '/favicon.svg' },
        { key: 'site_favicon', value: '/favicon.svg' }
      ];
      for (const setting of defaultSettings) {
        await run('INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)', [setting.key, setting.value]);
      }
    }
  } catch (e) {
    console.error('Error seeding default settings:', e);
  }

  // 4. Semear usuário admin padrão se não existir (apenas na primeira montagem)
  try {
    const adminUser = env.ADMIN_USERNAME || 'admin';
    const adminPass = env.ADMIN_PASSWORD || 'Xk9mP2vL7qR4StrongPass!';
    
    const userExists = await queryOne('SELECT id FROM users WHERE username = ?', [adminUser]);
    
    if (!userExists) {
      console.log('Seeding default admin user (first run)...');
      const bcrypt = await import('bcryptjs');
      const hasher = bcrypt.default ? bcrypt.default : bcrypt;
      const hashedPassword = await hasher.hash(adminPass, 10);
      await run('INSERT INTO users (username, password, role) VALUES (?, ?, ?)', [adminUser, hashedPassword, 'admin']);
      console.log('Admin user created successfully.');
    }
  } catch (e) {
    console.error('Error seeding admin user:', e);
  }

  // 5. Autotaguear posts antigos
  try {
    await autoTagExistingPosts();
  } catch (e) {
    console.error('Error in autoTagExistingPosts during init:', e);
  }

  return true;
}


function toSnake(row: any): any {
  if (!row) return row;
  const out: any = {};
  for (const [k, v] of Object.entries(row)) {
    out[k.replace(/_([a-z])/g, (_, c) => c.toUpperCase())] = v;
  }
  return out;
}

export async function query(sql: string, params: any[] = []) {
  const db = client || await getClient();
  const r = await db.execute(sql, params);
  return r.rows || [];
}

export async function queryOne(sql: string, params: any[] = []) {
  const rows = await query(sql, params);
  return rows[0] ?? null;
}

export async function run(sql: string, params: any[] = []) {
  const db = client || await getClient();
  return db.execute(sql, params);
}

async function exec(sql: string) {
  const db = client || await getClient();
  return db.execute(sql);
}

export async function generateUniqueSlug(title: string, excludeSlug?: string, excludeId?: number): Promise<string> {
  let slug = title
    .toLowerCase()
    .trim()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9\s-]/g, '')
    .replace(/[\s_]+/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-+|-+$/g, '')
    .substring(0, 60);

  let exists = await queryOne('SELECT slug FROM posts WHERE slug = ?', [slug]);
  if (excludeSlug && exists?.slug === excludeSlug) exists = null;

  let counter = 2;
  while (exists) {
    const candidate = `${slug}-${counter}`;
    const check = await queryOne('SELECT slug FROM posts WHERE slug = ?', [candidate]);
    if (!check) { slug = candidate; break; }
    counter++;
  }
  return slug;
}

export async function slugExists(slug: string, excludeId?: number): Promise<boolean> {
  const sql = excludeId
    ? 'SELECT id FROM posts WHERE slug = ? AND id != ?'
    : 'SELECT id FROM posts WHERE slug = ?';
  const params = excludeId ? [slug, excludeId] : [slug];
  const row = await queryOne(sql, params);
  return !!row;
}

/**
 * Chronological listing (search, category, sidebars).
 * Personalized home ranking lives in interest-engine.getHomeFeed — do not reintroduce
 * SQL random()/raw affinity ORDER BY here (it caused duplicates + buried new posts).
 */
export async function getAllPosts(options?: { page?: number; limit?: number; search?: string; categorySlug?: string; userInterests?: { categories: Record<string, number>; tags: Record<string, number> } }, _tenantId?: string): Promise<Post[]> {
  const page = options?.page || 1;
  const limit = options?.limit || 7;
  const offset = (page - 1) * limit;
  const search = options?.search;
  const categorySlug = options?.categorySlug;

  // Always stable newest-first. Personalization is handled by getHomeFeed.
  const orderClause = 'p.created_at DESC';

  if (categorySlug) {
    const sql = `
      SELECT p.*, GROUP_CONCAT(c.name) as categories
      FROM posts p
      JOIN post_categories pc ON p.id = pc.post_id
      JOIN categories cat ON pc.category_id = cat.id
      LEFT JOIN post_categories pc2 ON p.id = pc2.post_id
      LEFT JOIN categories c ON pc2.category_id = c.id
      WHERE p.published = 1 AND cat.slug = ?
      GROUP BY p.id
      ORDER BY ${orderClause}
      LIMIT ? OFFSET ?`;
    return (await query(sql, [categorySlug, limit, offset])) as Post[];
  }

  if (search) {
    const like = `%${search}%`;
    const sql = `
      SELECT p.*, GROUP_CONCAT(c.name) as categories
      FROM posts p
      LEFT JOIN post_categories pc ON p.id = pc.post_id
      LEFT JOIN categories c ON pc.category_id = c.id
      WHERE p.published = 1 AND (p.title LIKE ? OR p.excerpt LIKE ? OR p.content LIKE ?)
      GROUP BY p.id
      ORDER BY ${orderClause}
      LIMIT ? OFFSET ?`;
    return (await query(sql, [like, like, like, limit, offset])) as Post[];
  }

  const sql = `
    SELECT p.*, GROUP_CONCAT(c.name) as categories
    FROM posts p
    LEFT JOIN post_categories pc ON p.id = pc.post_id
    LEFT JOIN categories c ON pc.category_id = c.id
    WHERE p.published = 1
    GROUP BY p.id
    ORDER BY ${orderClause}
    LIMIT ? OFFSET ?`;
  return (await query(sql, [limit, offset])) as Post[];
}

/**
 * Lightweight candidate window for the mixed home feed (no OFFSET — mixer paginates in memory).
 * Caps content size in SELECT for ranking; feed cards still get cover/excerpt/title.
 */
export async function getPublishedFeedCandidates(limit: number = 250): Promise<Post[]> {
  const safeLimit = Math.max(1, Math.min(limit, 500));
  const sql = `
    SELECT p.id, p.title, p.slug, p.excerpt, p.cover_image, p.published,
           p.pinterest_enabled, p.pinterest_image, p.is_premium, p.is_18_plus,
           p.youtube_video_url, p.tags, p.created_at, p.updated_at,
           substr(p.content, 1, 2000) as content,
           GROUP_CONCAT(c.name) as categories
    FROM posts p
    LEFT JOIN post_categories pc ON p.id = pc.post_id
    LEFT JOIN categories c ON pc.category_id = c.id
    WHERE p.published = 1
    GROUP BY p.id
    ORDER BY p.created_at DESC
    LIMIT ?`;
  return (await query(sql, [safeLimit])) as Post[];
}


export async function countPosts(options?: { search?: string; categorySlug?: string }, _tenantId?: string): Promise<number> {
  const search = options?.search;
  const categorySlug = options?.categorySlug;

  if (categorySlug) {
    const sql = `SELECT COUNT(*) as count FROM posts p JOIN post_categories pc ON p.id = pc.post_id JOIN categories c ON pc.category_id = c.id WHERE p.published = 1 AND c.slug = ?`;
    const r = await queryOne(sql, [categorySlug]);
    return r?.count ?? 0;
  }

  if (search) {
    const like = `%${search}%`;
    const sql = `SELECT COUNT(*) as count FROM posts WHERE published = 1 AND (title LIKE ? OR excerpt LIKE ? OR content LIKE ?)`;
    const r = await queryOne(sql, [like, like, like]);
    return r?.count ?? 0;
  }

  const r = await queryOne('SELECT COUNT(*) as count FROM posts WHERE published = 1');
  return r?.count ?? 0;
}

export async function getAllPostsAdmin(_tenantId?: string): Promise<Post[]> {
  const sql = `SELECT p.*, GROUP_CONCAT(c.name) as categories FROM posts p LEFT JOIN post_categories pc ON p.id = pc.post_id LEFT JOIN categories c ON pc.category_id = c.id GROUP BY p.id ORDER BY p.created_at DESC`;
  return (await query(sql)) as Post[];
}

export async function getPostBySlug(slug: string, _tenantId?: string): Promise<Post | undefined> {
  const sql = `SELECT p.*, GROUP_CONCAT(c.id) as category_ids, GROUP_CONCAT(c.name) as categories FROM posts p LEFT JOIN post_categories pc ON p.id = pc.post_id LEFT JOIN categories c ON pc.category_id = c.id WHERE p.slug = ? GROUP BY p.id`;
  return (await queryOne(sql, [slug])) as Post | undefined;
}

export async function getPostById(id: number, _tenantId?: string): Promise<Post | undefined> {
  const sql = `SELECT * FROM posts WHERE id = ?`;
  return (await queryOne(sql, [id])) as Post | undefined;
}

export async function createPost(postData: {
  title: string; slug: string; content: string; excerpt?: string; cover_image?: string;
  published?: number; pinterest_enabled?: number; pinterest_image?: string; is_premium?: number;
  is_18_plus?: number; youtube_video_url?: string; tags?: string;
}): Promise<any> {
  const sql = `INSERT INTO posts (title, slug, content, excerpt, cover_image, published, pinterest_enabled, pinterest_image, is_premium, is_18_plus, youtube_video_url, tags) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`;
  return run(sql, [
    postData.title, postData.slug, postData.content,
    postData.excerpt || '', postData.cover_image || '',
    postData.published ? 1 : 0, postData.pinterest_enabled ? 1 : 0,
    postData.pinterest_image || null, postData.is_premium ? 1 : 0,
    postData.is_18_plus ? 1 : 0, postData.youtube_video_url || null, postData.tags || null
  ]);
}


export async function updatePost(id: number, postData: {
  title?: string; slug?: string; content?: string; excerpt?: string;
  cover_image?: string; published?: number; pinterest_enabled?: number;
  pinterest_image?: string; is_premium?: number; is_18_plus?: number;
  youtube_video_url?: string; tags?: string;
}): Promise<any> {
  const sql = `UPDATE posts SET title = COALESCE(?, title), slug = COALESCE(?, slug), content = COALESCE(?, content), excerpt = COALESCE(?, excerpt), cover_image = COALESCE(?, cover_image), published = COALESCE(?, published), pinterest_enabled = COALESCE(?, pinterest_enabled), pinterest_image = COALESCE(?, pinterest_image), is_premium = COALESCE(?, is_premium), is_18_plus = COALESCE(?, is_18_plus), youtube_video_url = COALESCE(?, youtube_video_url), tags = COALESCE(?, tags), updated_at = CURRENT_TIMESTAMP WHERE id = ?`;
  return run(sql, [
    postData.title ?? null, postData.slug ?? null, postData.content ?? null,
    postData.excerpt ?? null, postData.cover_image ?? null,
    postData.published !== undefined ? (postData.published ? 1 : 0) : null,
    postData.pinterest_enabled !== undefined ? (postData.pinterest_enabled ? 1 : 0) : null,
    postData.pinterest_image ?? null, 
    postData.is_premium !== undefined ? (postData.is_premium ? 1 : 0) : null,
    postData.is_18_plus !== undefined ? (postData.is_18_plus ? 1 : 0) : null,
    postData.youtube_video_url !== undefined ? postData.youtube_video_url : null,
    postData.tags !== undefined ? postData.tags : null,
    id
  ]);
}


export async function deletePost(id: number, _tenantId?: string): Promise<any> {
  return run('DELETE FROM posts WHERE id = ?', [id]);
}

export async function getAllCategories(_tenantId?: string): Promise<Category[]> {
  return (await query('SELECT c.*, COUNT(DISTINCT pc.post_id) AS post_count FROM categories c LEFT JOIN post_categories pc ON c.id = pc.category_id LEFT JOIN posts p ON pc.post_id = p.id AND p.published = 1 GROUP BY c.id ORDER BY c.name')) as Category[];
}

export async function getPinterestEnabledCategories(_tenantId?: string): Promise<Category[]> {
  return (await query('SELECT * FROM categories WHERE pinterest_enabled = 1 ORDER BY name')) as Category[];
}

export async function getCategoryBySlug(slug: string, _tenantId?: string): Promise<Category | undefined> {
  return (await queryOne('SELECT * FROM categories WHERE slug = ?', [slug])) as Category | undefined;
}

export async function createCategory(name: string, slug: string, _tenantId?: string): Promise<any> {
  return run('INSERT INTO categories (name, slug, description, pinterest_enabled) VALUES (?, ?, NULL, 0)', [name, slug]);
}

export async function updateCategory(id: number, _tenantId: string | undefined, name: string, slug: string, pinterestEnabled: boolean): Promise<any> {
  return run('UPDATE categories SET name = ?, slug = ?, pinterest_enabled = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?', [
    name, slug, pinterestEnabled ? 1 : 0, id
  ]);
}

export async function deleteCategory(id: number, _tenantId?: string): Promise<any> {
  return run('DELETE FROM categories WHERE id = ?', [id]);
}

export async function assignCategoriesToPost(postId: number, categoryIds: number[]): Promise<void> {
  await run('DELETE FROM post_categories WHERE post_id = ?', [postId]);
  for (const catId of categoryIds) {
    await run('INSERT INTO post_categories (post_id, category_id) VALUES (?, ?)', [postId, catId]);
  }
}

export async function getCategoriesByPostId(postId: number, _tenantId?: string): Promise<Category[]> {
  return (await query('SELECT c.* FROM categories c JOIN post_categories pc ON c.id = pc.category_id WHERE pc.post_id = ?', [postId])) as Category[];
}

export async function getUserByUsername(username: string, _tenantId?: string): Promise<User | undefined> {
  return (await queryOne('SELECT * FROM users WHERE username = ?', [username])) as User | undefined;
}

export async function createUser(username: string, password: string, role = 'member'): Promise<any> {
  return run('INSERT INTO users (username, password, role) VALUES (?, ?, ?)', [username, password, role]);
}

export async function updateUserPassword(username: string, password: string): Promise<any> {
  return run('UPDATE users SET password = ? WHERE username = ?', [password, username]);
}

export async function getSettings(_tenantId?: string): Promise<Record<string, string>> {
  const rows = (await query('SELECT key, value FROM settings')) as Setting[];
  return rows.reduce((acc, row) => { acc[row.key] = row.value; return acc; }, {} as Record<string, string>);
}

export async function updateSetting(key: string, value: string): Promise<any> {
  return run('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)', [key, value]);
}

export async function createDBSession(id: string, username: string, expiresAt: number): Promise<any> {
  return run('INSERT INTO sessions (id, username, expires_at) VALUES (?, ?, ?)', [id, username, expiresAt]);
}

export async function getDBSession(id: string): Promise<{ id: string; username: string; expires_at: number } | undefined> {
  return (await queryOne('SELECT * FROM sessions WHERE id = ?', [id])) as any;
}

export async function deleteDBSession(id: string): Promise<any> {
  return run('DELETE FROM sessions WHERE id = ?', [id]);
}

export async function clearExpiredDBSessions(): Promise<any> {
  return run('DELETE FROM sessions WHERE expires_at < ?', [Date.now()]);
}

export async function getAllAds(_tenantId?: string): Promise<any[]> {
  return (await query('SELECT * FROM ads ORDER BY created_at DESC'));
}

export async function getActiveAdsByPlacement(placement: string, _tenantId?: string): Promise<any[]> {
  return (await query('SELECT * FROM ads WHERE placement = ? AND is_active = 1', [placement]));
}

export async function getAdById(id: number | string, _tenantId?: string): Promise<any> {
  return (await queryOne('SELECT * FROM ads WHERE id = ?', [id]));
}

export async function createAd(ad: {
  name: string; placement: string; type: string; content?: string; image_url?: string;
  link_url?: string; is_active?: number; weight?: number; style?: any; youtube_video_url?: string;
}): Promise<any> {
  return run('INSERT INTO ads (name, placement, type, content, image_url, link_url, is_active, weight, style, youtube_video_url) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', [
    ad.name, ad.placement, ad.type, ad.content || null, ad.image_url || null,
    ad.link_url || null,
    ad.is_active !== undefined ? (ad.is_active ? 1 : 0) : 1,
    ad.weight || 1,
    ad.style ? JSON.stringify(ad.style) : null,
    ad.youtube_video_url || null
  ]);
}

export async function updateAd(id: number | string, ad: {
  name?: string; placement?: string; type?: string; content?: string; image_url?: string;
  link_url?: string; is_active?: number; weight?: number; style?: any; youtube_video_url?: string;
}): Promise<any> {
  return run('UPDATE ads SET name = ?, placement = ?, type = ?, content = ?, image_url = ?, link_url = ?, is_active = ?, weight = ?, style = ?, youtube_video_url = ? WHERE id = ?', [
    ad.name ?? null, ad.placement ?? null, ad.type ?? null, ad.content ?? null,
    ad.image_url ?? null, ad.link_url ?? null,
    ad.is_active !== undefined ? (ad.is_active ? 1 : 0) : null,
    ad.weight ?? null,
    ad.style ? JSON.stringify(ad.style) : null,
    ad.youtube_video_url !== undefined ? ad.youtube_video_url : null,
    id
  ]);
}

export async function deleteAd(id: number | string, _tenantId?: string): Promise<any> {
  return run('DELETE FROM ads WHERE id = ?', [id]);
}

export async function getPostsForPinterest(_tenantId?: string): Promise<Post[]> {
  return (await query('SELECT p.* FROM posts p WHERE p.published = 1 AND p.pinterest_enabled = 1 ORDER BY p.created_at DESC')) as Post[];
}

export async function getPostsForPinterestByCategory(categorySlug: string, _tenantId?: string): Promise<Post[]> {
  return (await query(`SELECT DISTINCT p.* FROM posts p JOIN post_categories pc ON p.id = pc.post_id JOIN categories c ON pc.category_id = c.id WHERE p.published = 1 AND p.pinterest_enabled = 1 AND c.slug = ? ORDER BY p.created_at DESC`, [categorySlug])) as Post[];
}

export async function getRelatedPosts(postId: number | string, limit: number = 3, userInterests?: { categories: Record<string, number>; tags: Record<string, number> }): Promise<Post[]> {
  // Stable order only (no random). Soft personalization via capped CASE scores.
  // Raw affinity scores are log-capped so one strong interest cannot dominate related list forever.
  let orderClause = 'p.created_at DESC';

  if (userInterests) {
    const { categories = {}, tags = {} } = userInterests;
    const orderParts: string[] = [];
    const escapeStr = (val: string) => `'${val.replace(/'/g, "''")}'`;
    const cap = (raw: number) => {
      if (raw <= 0) return 0;
      // approximate log2(1+x) without floats exploding: min 8
      const v = Math.min(8, Math.log2(1 + raw));
      return Math.round(v * 100) / 100;
    };

    for (const [catName, score] of Object.entries(categories)) {
      if (score > 0) {
        orderParts.push(
          `(CASE WHEN EXISTS (SELECT 1 FROM post_categories jpc JOIN categories jc ON jpc.category_id = jc.id WHERE jpc.post_id = p.id AND jc.name = ${escapeStr(catName)}) THEN ${cap(score) * 2} ELSE 0 END)`
        );
      }
    }
    for (const [tagName, score] of Object.entries(tags)) {
      if (score > 0) {
        const safeTag = tagName.replace(/'/g, "''");
        orderParts.push(
          `(CASE WHEN p.tags LIKE '%${safeTag}%' THEN ${cap(score) * 1.5} ELSE 0 END)`
        );
      }
    }

    // Freshness competes fairly with capped affinity
    orderParts.push(
      `(CASE WHEN (strftime('%s', 'now') - strftime('%s', p.created_at)) < 3 * 86400 THEN 10 WHEN (strftime('%s', 'now') - strftime('%s', p.created_at)) < 14 * 86400 THEN 4 ELSE 0 END)`
    );

    if (orderParts.length > 0) {
      orderClause = `${orderParts.join(' + ')} DESC, p.created_at DESC`;
    }
  }

  const sql = `
    SELECT p.*, GROUP_CONCAT(c.name, ', ') as categories 
    FROM posts p 
    LEFT JOIN post_categories pc ON p.id = pc.post_id 
    LEFT JOIN categories c ON pc.category_id = c.id 
    WHERE p.published = 1 AND p.id != ? 
      AND (pc.category_id IN (SELECT pc2.category_id FROM post_categories pc2 WHERE pc2.post_id = ?) 
      OR (SELECT COUNT(*) FROM post_categories pc3 WHERE pc3.post_id = ?) = 0) 
    GROUP BY p.id 
    ORDER BY ${orderClause} 
    LIMIT ?`;

  return (await query(sql, [postId, postId, postId, limit])) as Post[];
}


export async function getAllPremiumPlans(_tenantId?: string): Promise<PremiumPlan[]> {
  const plans = (await query('SELECT * FROM premium_plans WHERE is_active = 1 ORDER BY price_cents ASC')) as PremiumPlan[];
  return plans.map((plan: any) => {
    if (plan.features && typeof plan.features === 'string') {
      try { plan.features = JSON.parse(plan.features); } catch {}
    }
    return plan;
  });
}

export async function getPremiumPlanById(id: number, _tenantId?: string): Promise<PremiumPlan | undefined> {
  const plan = (await queryOne('SELECT * FROM premium_plans WHERE id = ?', [id])) as PremiumPlan | undefined;
  if (plan && plan.features && typeof plan.features === 'string') {
    try { plan.features = JSON.parse(plan.features); } catch {}
  }
  return plan;
}

export async function getPremiumPlanBySlug(slug: string, _tenantId?: string): Promise<PremiumPlan | undefined> {
  const plan = (await queryOne('SELECT * FROM premium_plans WHERE slug = ?', [slug])) as PremiumPlan | undefined;
  if (plan && plan.features && typeof plan.features === 'string') {
    try { plan.features = JSON.parse(plan.features); } catch {}
  }
  return plan;
}

export async function createPremiumPlan(plan: {
  name: string; slug: string; description?: string; price_cents: number;
  interval_days?: number; features?: any; is_active?: number;
}): Promise<any> {
  return run('INSERT INTO premium_plans (name, slug, description, price_cents, interval_days, mp_plan_id, features, is_active) VALUES (?, ?, ?, ?, ?, ?, ?, ?)', [
    plan.name, plan.slug, plan.description || null, plan.price_cents,
    plan.interval_days || 30, null,
    plan.features ? JSON.stringify(plan.features) : null,
    plan.is_active !== undefined ? (plan.is_active ? 1 : 0) : 1
  ]);
}

export async function updatePremiumPlan(id: number, plan: {
  name?: string; slug?: string; description?: string; price_cents?: number;
  interval_days?: number; features?: any; is_active?: number;
}): Promise<any> {
  return run('UPDATE premium_plans SET name = ?, slug = ?, description = ?, price_cents = ?, interval_days = ?, mp_plan_id = ?, features = ?, is_active = ? WHERE id = ?', [
    plan.name ?? null, plan.slug ?? null, plan.description ?? null,
    plan.price_cents ?? null, plan.interval_days ?? null, null,
    plan.features ? JSON.stringify(plan.features) : null,
    plan.is_active !== undefined ? (plan.is_active ? 1 : 0) : null, id
  ]);
}

export async function deletePremiumPlan(id: number, _tenantId?: string): Promise<any> {
  return run('DELETE FROM premium_plans WHERE id = ?', [id]);
}

export async function getUserSubscription(userId: number, _tenantId?: string): Promise<any> {
  return (await queryOne(`SELECT * FROM premium_subscriptions WHERE user_id = ? AND status = 'active' AND expires_at > datetime('now') ORDER BY expires_at DESC LIMIT 1`, [userId]));
}

export async function getSubscriptionById(id: number, _tenantId?: string): Promise<any> {
  return (await queryOne('SELECT * FROM premium_subscriptions WHERE id = ?', [id]));
}

export async function getSubscriptionByAsaasId(asaasSubscriptionId: string): Promise<any> {
  return (await queryOne('SELECT * FROM premium_subscriptions WHERE asaas_subscription_id = ?', [asaasSubscriptionId]));
}

export async function createSubscription(sub: {
  user_id: number; plan_id: number;
  status?: string; started_at?: string; expires_at?: string;
  asaas_subscription_id?: string; asaas_customer_id?: string;
  stripe_subscription_id?: string; stripe_customer_id?: string;
}): Promise<any> {
  return run(
    `INSERT INTO premium_subscriptions (
      user_id, plan_id, mp_subscription_id, mp_payment_id, status, started_at, expires_at,
      asaas_subscription_id, asaas_customer_id, stripe_subscription_id, stripe_customer_id
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
    [
      sub.user_id,
      sub.plan_id,
      null,
      null,
      sub.status || 'pending',
      sub.started_at || null,
      sub.expires_at || null,
      sub.asaas_subscription_id || null,
      sub.asaas_customer_id || null,
      sub.stripe_subscription_id || null,
      sub.stripe_customer_id || null
    ]
  );
}

export async function updateSubscription(id: number, data: { status?: string; expires_at?: string }): Promise<any> {
  return run('UPDATE premium_subscriptions SET status = ?, mp_payment_id = ?, expires_at = ? WHERE id = ?', [
    data.status || null, null, data.expires_at || null, id
  ]);
}

export async function updateSubscriptionByAsaasId(asaasSubscriptionId: string, data: { status: string; expires_at: string }): Promise<any> {
  return run('UPDATE premium_subscriptions SET status = ?, expires_at = ? WHERE asaas_subscription_id = ?', [data.status, data.expires_at, asaasSubscriptionId]);
}

export async function updateSubscriptionByStripeId(
  stripeSubscriptionId: string,
  data: { status: string; expires_at?: string; stripe_customer_id?: string }
): Promise<any> {
  if (data.expires_at && data.stripe_customer_id) {
    return run(
      'UPDATE premium_subscriptions SET status = ?, expires_at = ?, stripe_customer_id = ? WHERE stripe_subscription_id = ?',
      [data.status, data.expires_at, data.stripe_customer_id, stripeSubscriptionId]
    );
  }
  if (data.expires_at) {
    return run('UPDATE premium_subscriptions SET status = ?, expires_at = ? WHERE stripe_subscription_id = ?', [
      data.status,
      data.expires_at,
      stripeSubscriptionId
    ]);
  }
  return run('UPDATE premium_subscriptions SET status = ? WHERE stripe_subscription_id = ?', [
    data.status,
    stripeSubscriptionId
  ]);
}

export async function getSubscriptionByStripeId(stripeSubscriptionId: string): Promise<any> {
  return queryOne('SELECT * FROM premium_subscriptions WHERE stripe_subscription_id = ?', [
    stripeSubscriptionId
  ]);
}

export async function createPayment(payment: {
  subscription_id?: number; amount_cents: number;
  status: string; payment_method?: string; asaas_payment_id?: string;
  stripe_payment_id?: string;
}): Promise<any> {
  return run(
    'INSERT INTO premium_payments (subscription_id, mp_payment_id, amount_cents, status, payment_method, asaas_payment_id, stripe_payment_id) VALUES (?, ?, ?, ?, ?, ?, ?)',
    [
      payment.subscription_id || null,
      null,
      payment.amount_cents,
      payment.status,
      payment.payment_method || null,
      payment.asaas_payment_id || null,
      payment.stripe_payment_id || null
    ]
  );
}

export async function getPaymentByAsaasId(asaasPaymentId: string): Promise<any> {
  return (await queryOne('SELECT * FROM premium_payments WHERE asaas_payment_id = ?', [asaasPaymentId]));
}

export async function getPaymentByStripeId(stripePaymentId: string): Promise<any> {
  return queryOne('SELECT * FROM premium_payments WHERE stripe_payment_id = ?', [stripePaymentId]);
}

export async function getAllUsersByRole(role: string): Promise<User[]> {
  return (await query('SELECT id, username, role, created_at FROM users WHERE role = ? ORDER BY created_at DESC', [role])) as User[];
}

export async function deleteUser(id: number): Promise<any> {
  // Excluir sessões e assinaturas primeiro
  await run('DELETE FROM sessions WHERE username = (SELECT username FROM users WHERE id = ?)', [id]);
  await run('DELETE FROM premium_subscriptions WHERE user_id = ?', [id]);
  return run('DELETE FROM users WHERE id = ?', [id]);
}

export async function grantPremiumAccessManual(userId: number, planId: number, days = 30): Promise<any> {
  const expiresAt = new Date(Date.now() + days * 24 * 60 * 60 * 1000).toISOString();
  // Verificar se já tem assinatura
  const existing = await queryOne('SELECT id FROM premium_subscriptions WHERE user_id = ?', [userId]);
  if (existing) {
    return run("UPDATE premium_subscriptions SET status = 'active', plan_id = ?, expires_at = ? WHERE user_id = ?", [planId, expiresAt, userId]);
  } else {
    return createSubscription({
      user_id: userId,
      plan_id: planId,
      status: 'active',
      started_at: new Date().toISOString(),
      expires_at: expiresAt
    });
  }
}

export async function revokePremiumAccessManual(userId: number): Promise<any> {
  return run("UPDATE premium_subscriptions SET status = 'cancelled', expires_at = datetime('now') WHERE user_id = ?", [userId]);
}

export async function getPaymentsBySubscription(subscriptionId: number, _tenantId?: string): Promise<any[]> {
  return (await query('SELECT * FROM premium_payments WHERE subscription_id = ? ORDER BY created_at DESC', [subscriptionId]));
}

export async function isUserPremium(userId: number, _tenantId?: string): Promise<boolean> {
  return !!(await getUserSubscription(userId));
}

export async function searchPosts(q: string, page: number = 1, limit: number = 10) {
  const offset = (page - 1) * limit;
  const like = `%${q}%`;
  const totalRow = await queryOne('SELECT COUNT(*) as count FROM posts WHERE published = 1 AND (title LIKE ? OR content LIKE ? OR excerpt LIKE ?)', [like, like, like]);
  const total = totalRow?.count ?? 0;
  const posts = await query(`SELECT p.*, GROUP_CONCAT(c.name) AS category_names FROM posts p LEFT JOIN post_categories pc ON p.id = pc.post_id LEFT JOIN categories c ON pc.category_id = c.id WHERE p.published = 1 AND (p.title LIKE ? OR p.content LIKE ? OR p.excerpt LIKE ?) GROUP BY p.id ORDER BY p.created_at DESC LIMIT ? OFFSET ?`, [like, like, like, limit, offset]);
  return { posts, total, page, totalPages: Math.ceil(total / limit), hasMore: offset + posts.length < total };
}

export async function getAllCategoriesAdmin(_tenantId?: string): Promise<Category[]> {
  return getAllCategories(_tenantId);
}

// Newsletter functions
export async function subscribeToNewsletter(email: string, name?: string) {
  const sql = `INSERT OR IGNORE INTO newsletter_subscribers (email, name) VALUES (?, ?)`;
  return run(sql, [email, name || null]);
}

export async function getNewsletterSubscribers(page: number = 1, limit: number = 20, search: string = '') {
  const offset = (page - 1) * limit;
  const searchTerm = `%${search}%`;
  
  const countSql = `SELECT COUNT(*) as count FROM newsletter_subscribers WHERE email LIKE ? OR name LIKE ?`;
  const countResult = await queryOne(countSql, [searchTerm, searchTerm]);
  const total = countResult?.count || 0;
  
  const sql = `
    SELECT * FROM newsletter_subscribers 
    WHERE email LIKE ? OR name LIKE ? 
    ORDER BY created_at DESC 
    LIMIT ? OFFSET ?
  `;
  const subscribers = await query(sql, [searchTerm, searchTerm, limit, offset]);
  
  return {
    subscribers,
    total,
    page,
    totalPages: Math.ceil(total / limit)
  };
}

export async function deleteNewsletterSubscriber(id: number) {
  return run(`DELETE FROM newsletter_subscribers WHERE id = ?`, [id]);
}

export async function createNewsletterCampaign(campaign: {
  subject: string;
  content: string;
  youtubeVideoUrl?: string;
  recipientsCount: number;
}): Promise<any> {
  const sql = `
    INSERT INTO newsletter_campaigns (subject, content, youtube_video_url, recipients_count)
    VALUES (?, ?, ?, ?)
  `;
  return run(sql, [
    campaign.subject,
    campaign.content,
    campaign.youtubeVideoUrl || null,
    campaign.recipientsCount
  ]);
}

export async function getNewsletterCampaigns(page: number = 1, limit: number = 10) {
  const offset = (page - 1) * limit;
  
  const countSql = `SELECT COUNT(*) as count FROM newsletter_campaigns`;
  const countResult = await queryOne(countSql);
  const total = countResult?.count || 0;
  
  const sql = `
    SELECT * FROM newsletter_campaigns
    ORDER BY sent_at DESC
    LIMIT ? OFFSET ?
  `;
  const campaigns = await query(sql, [limit, offset]);
  
  return {
    campaigns,
    total,
    page,
    totalPages: Math.ceil(total / limit)
  };
}

export async function getActiveNewsletterEmails(): Promise<string[]> {
  const rows = await query(`
    SELECT email FROM newsletter_subscribers
    WHERE status = 'active'
  `);
  return rows.map((r: any) => r.email);
}


// CLI Token functions
export async function getCLIToken(): Promise<string | null> {
  const row = await queryOne('SELECT value FROM settings WHERE key = ?', ['cli_token']);
  return row?.value ?? null;
}

export async function regenerateCLIToken(): Promise<string> {
  // Generate a secure random token
  const bytes = Array.from({ length: 32 }, () =>
    Math.floor(Math.random() * 256).toString(16).padStart(2, '0')
  ).join('');
  const token = `blog_${bytes}`;
  await run('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)', ['cli_token', token]);
  return token;
}

export async function validateCLIToken(token: string): Promise<boolean> {
  if (!token) return false;
  const stored = await getCLIToken();
  return stored !== null && stored === token;
}

export interface AnalyticsSummary {
  totalViews: number;
  viewsToday: number;
  viewsWeek: number;
  viewsByDay: { date: string; count: number }[];
  topPosts: { id: number; title: string; slug: string; views: number }[];
  uniqueVisitorsToday: number;
}

export async function recordPageView(pathname: string, ip: string, userAgent?: string): Promise<void> {
  let pageType = 'other';
  let slug: string | null = null;

  if (pathname === '/') {
    pageType = 'home';
  } else if (pathname.startsWith('/post/')) {
    pageType = 'post';
    slug = pathname.split('/post/')[1]?.split('?')[0] || null;
  } else if (pathname.startsWith('/category/')) {
    pageType = 'category';
    slug = pathname.split('/category/')[1]?.split('?')[0] || null;
  } else {
    return; // Don't track admin, api or other non-content pages
  }

  // Normalize IP: strip IPv6 prefix
  const normalizedIp = ip?.replace(/^::ffff:/, '') || 'unknown';
  // Use first 200 chars of UA to fingerprint device/browser
  const ua = (userAgent || '').substring(0, 200);

  try {
    // Rate limit: 1 hour per (IP + UA + slug) combination to prevent duplicates
    const recentView = await queryOne(
      `SELECT id FROM page_views 
       WHERE page_type = ? 
         AND (slug = ? OR (slug IS NULL AND ? IS NULL)) 
         AND ip_address = ? 
         AND (user_agent = ? OR (user_agent IS NULL AND ? = ''))
         AND created_at > datetime('now', '-1 hour')`,
      [pageType, slug, slug, normalizedIp, ua, ua]
    );

    if (!recentView) {
      await run(
        'INSERT INTO page_views (page_type, slug, ip_address, user_agent) VALUES (?, ?, ?, ?)',
        [pageType, slug, normalizedIp, ua || null]
      );
    }
  } catch (e) {
    console.error('Error recording page view:', e);
  }
}

export async function getAnalyticsSummary(tenantId?: string): Promise<AnalyticsSummary> {
  const [totalRow, todayRow, weekRow, daysRows, postsRows] = await Promise.all([
    queryOne('SELECT COUNT(*) as count FROM page_views'),
    queryOne("SELECT COUNT(*) as count FROM page_views WHERE created_at >= datetime('now', 'start of day')"),
    queryOne("SELECT COUNT(*) as count FROM page_views WHERE created_at >= datetime('now', '-7 days')"),
    query(`
      SELECT date(created_at) as view_date, COUNT(*) as count 
      FROM page_views 
      WHERE created_at >= datetime('now', '-7 days')
      GROUP BY date(created_at)
      ORDER BY view_date ASC
    `),
    query(`
      SELECT p.id, p.title, p.slug, COUNT(pv.id) as views
      FROM page_views pv
      JOIN posts p ON pv.slug = p.slug
      WHERE pv.page_type = 'post'
      GROUP BY p.id, p.title, p.slug
      ORDER BY views DESC
      LIMIT 5
    `)
  ]);

  // Format days to guarantee last 7 days are represented in viewsByDay
  const viewsByDayMap = new Map<string, number>();
  for (let i = 6; i >= 0; i--) {
    const d = new Date();
    d.setDate(d.getDate() - i);
    const dateStr = d.toISOString().split('T')[0];
    viewsByDayMap.set(dateStr, 0);
  }

  if (daysRows) {
    for (const r of daysRows) {
      if (r.view_date) {
        viewsByDayMap.set(r.view_date, Number(r.count || 0));
      }
    }
  }

  const viewsByDay = Array.from(viewsByDayMap.entries()).map(([date, count]) => ({
    date,
    count
  }));

  return {
    totalViews: Number(totalRow?.count || 0),
    viewsToday: Number(todayRow?.count || 0),
    viewsWeek: Number(weekRow?.count || 0),
    viewsByDay,
    topPosts: (postsRows || []).map((r: any) => ({
      id: Number(r.id),
      title: String(r.title),
      slug: String(r.slug),
      views: Number(r.views)
    }))
  };
}

export async function createOtp(email: string, code: string, expiresAt: string): Promise<any> {
  // Invalidate any existing active OTP codes for this email
  await run('UPDATE member_otps SET used = 1 WHERE email = ? AND used = 0', [email]);
  return run('INSERT INTO member_otps (email, code, expires_at) VALUES (?, ?, ?)', [email, code, expiresAt]);
}

export async function verifyOtpCode(email: string, code: string): Promise<boolean> {
  const row = await queryOne(`
    SELECT id FROM member_otps 
    WHERE email = ? AND code = ? AND used = 0 AND expires_at > datetime('now')
    ORDER BY id DESC LIMIT 1
  `, [email, code]);

  if (row) {
    // Consume the OTP code
    await run('UPDATE member_otps SET used = 1 WHERE id = ?', [row.id]);
    return true;
  }
  return false;
}

export interface Product {
  id: number;
  name: string;
  slug: string | null;
  description: string | null;
  price_cents: number;
  file_url: string | null;
  external_link: string | null;
  image_url: string | null;
  youtube_video_url?: string | null;
  category?: string | null;
  category_id?: number | null;
  created_at: string;
  // Campos de entrega manual (acesso via Google Drive, GitHub, etc.)
  resource_type?: string | null;
  access_label?: string | null;
  drive_instructions?: string | null;
  delivery_deadline?: string | null;
  is_premium_included?: number;
  // Esteira de produtos: upsell/downsell pós-compra
  upsell_product_id?: number | null;
  downsell_product_id?: number | null;
  has_extra_service?: number;
  extra_service_title?: string | null;
  extra_service_price_cents?: number;
  extra_service_description?: string | null;
}

export interface ProductCategory {
  id: number;
  name: string;
  slug: string;
  description: string | null;
}

export async function createProduct(prod: {
  name: string;
  slug?: string;
  description?: string;
  price_cents: number;
  file_url?: string;
  external_link?: string;
  image_url?: string;
  category_id?: number | null;
  youtube_video_url?: string | null;
  // Campos de entrega manual
  resource_type?: string | null;
  access_label?: string | null;
  drive_instructions?: string | null;
  delivery_deadline?: string | null;
  is_premium_included?: number;
  // Campos de serviço extra / order bump
  has_extra_service?: number;
  extra_service_title?: string | null;
  extra_service_price_cents?: number;
  extra_service_description?: string | null;
  // Esteira de produtos: upsell/downsell pós-compra
  upsell_product_id?: number | null;
  downsell_product_id?: number | null;
}): Promise<any> {
  return run(
    'INSERT INTO products (name, slug, description, price_cents, file_url, external_link, image_url, category_id, youtube_video_url, resource_type, access_label, drive_instructions, delivery_deadline, is_premium_included, has_extra_service, extra_service_title, extra_service_price_cents, extra_service_description, upsell_product_id, downsell_product_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
    [
      prod.name,
      prod.slug || null,
      prod.description || null,
      prod.price_cents,
      prod.file_url || null,
      prod.external_link || null,
      prod.image_url || null,
      prod.category_id || null,
      prod.youtube_video_url || null,
      prod.resource_type || 'file',
      prod.access_label || null,
      prod.drive_instructions || null,
      prod.delivery_deadline || null,
      prod.is_premium_included || 0,
      prod.has_extra_service || 0,
      prod.extra_service_title || null,
      prod.extra_service_price_cents || 0,
      prod.extra_service_description || null,
      prod.upsell_product_id || null,
      prod.downsell_product_id || null
    ]
  );
}

export async function updateProduct(
  id: number,
  prod: {
    name: string;
    slug: string | null;
    description: string | null;
    price_cents: number;
    file_url: string | null;
    external_link: string | null;
    image_url: string | null;
    category_id: number | null;
    youtube_video_url: string | null;
    // Campos de entrega manual
    resource_type?: string | null;
    access_label?: string | null;
    drive_instructions?: string | null;
    delivery_deadline?: string | null;
    is_premium_included?: number;
    // Campos de serviço extra / order bump
    has_extra_service?: number;
    extra_service_title?: string | null;
    extra_service_price_cents?: number;
    extra_service_description?: string | null;
    // Esteira de produtos: upsell/downsell pós-compra
    upsell_product_id?: number | null;
    downsell_product_id?: number | null;
  }
): Promise<any> {
  return run(
    'UPDATE products SET name = ?, slug = ?, description = ?, price_cents = ?, file_url = ?, external_link = ?, image_url = ?, category_id = ?, youtube_video_url = ?, resource_type = ?, access_label = ?, drive_instructions = ?, delivery_deadline = ?, is_premium_included = ?, has_extra_service = ?, extra_service_title = ?, extra_service_price_cents = ?, extra_service_description = ?, upsell_product_id = ?, downsell_product_id = ? WHERE id = ?',
    [
      prod.name,
      prod.slug,
      prod.description,
      prod.price_cents,
      prod.file_url,
      prod.external_link,
      prod.image_url,
      prod.category_id,
      prod.youtube_video_url,
      prod.resource_type || 'file',
      prod.access_label || null,
      prod.drive_instructions || null,
      prod.delivery_deadline || null,
      prod.is_premium_included || 0,
      prod.has_extra_service || 0,
      prod.extra_service_title || null,
      prod.extra_service_price_cents || 0,
      prod.extra_service_description || null,
      prod.upsell_product_id || null,
      prod.downsell_product_id || null,
      id
    ]
  );
}

/**
 * Resolve product rows with category name from product_categories.
 * IMPORTANT: products still has a legacy TEXT column `category`. With @libsql/client,
 * `SELECT p.*, pc.name AS category` keeps the FIRST "category" (legacy) and drops the JOIN.
 * Always alias the join as category_name and overwrite in JS.
 */
function mapProductRow(row: any): Product | undefined {
  if (!row) return undefined;
  const { category_name, ...rest } = row;
  return {
    ...rest,
    // Prefer joined name; never trust legacy products.category text column
    category: category_name ?? null,
  } as Product;
}

function mapProductRows(rows: any[]): Product[] {
  return (rows || []).map((row) => mapProductRow(row)!).filter(Boolean);
}

const PRODUCT_SELECT_WITH_CATEGORY = `
  SELECT p.*, pc.name AS category_name
  FROM products p
  LEFT JOIN product_categories pc ON p.category_id = pc.id
`;

export async function getProductBySlug(slug: string): Promise<Product | undefined> {
  return mapProductRow(
    await queryOne(`${PRODUCT_SELECT_WITH_CATEGORY} WHERE p.slug = ?`, [slug])
  );
}

export async function productSlugExists(slug: string, excludeId?: number): Promise<boolean> {
  const sql = excludeId
    ? 'SELECT id FROM products WHERE slug = ? AND id != ?'
    : 'SELECT id FROM products WHERE slug = ?';
  const params = excludeId ? [slug, excludeId] : [slug];
  const row = await queryOne(sql, params);
  return !!row;
}

export async function generateUniqueProductSlug(name: string, excludeId?: number): Promise<string> {
  let slug = name
    .toLowerCase()
    .trim()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9\s-]/g, '')
    .replace(/[\s_]+/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-+|-+$/g, '')
    .substring(0, 60);

  if (!slug) slug = 'produto';

  let exists = await productSlugExists(slug, excludeId);
  let counter = 2;
  while (exists) {
    const candidate = `${slug}-${counter}`;
    const check = await productSlugExists(candidate, excludeId);
    if (!check) {
      slug = candidate;
      break;
    }
    counter++;
  }
  return slug;
}

export async function deleteProduct(id: number): Promise<any> {
  await run('DELETE FROM post_products WHERE product_id = ?', [id]);
  return run('DELETE FROM products WHERE id = ?', [id]);
}

export async function getProductById(id: number): Promise<Product | undefined> {
  return mapProductRow(
    await queryOne(`${PRODUCT_SELECT_WITH_CATEGORY} WHERE p.id = ?`, [id])
  );
}

export async function getAllProducts(): Promise<Product[]> {
  return mapProductRows(
    await query(`${PRODUCT_SELECT_WITH_CATEGORY} ORDER BY p.created_at DESC`)
  );
}

export async function getProductsByPostId(postId: number): Promise<Product[]> {
  return mapProductRows(
    await query(
      `SELECT p.*, pc.name AS category_name
       FROM products p
       JOIN post_products pp ON p.id = pp.product_id
       LEFT JOIN product_categories pc ON p.category_id = pc.id
       WHERE pp.post_id = ?
       ORDER BY p.created_at DESC`,
      [postId]
    )
  );
}

export async function assignProductsToPost(postId: number, productIds: number[]): Promise<void> {
  await run('DELETE FROM post_products WHERE post_id = ?', [postId]);
  for (const prodId of productIds) {
    await run('INSERT INTO post_products (post_id, product_id) VALUES (?, ?)', [postId, prodId]);
  }
}

export async function createProductPurchase(purchase: {
  userId: number;
  productId: number;
  productNameSnapshot?: string;
  priceCents?: number;
  asaasPaymentId?: string;
  stripeSessionId?: string;
  status?: string;
  buyerAccessId?: string | null;
  hasExtraService?: number;
  extraServiceTitleSnapshot?: string | null;
  extraServicePriceCents?: number;
}): Promise<any> {
  return run(
    'INSERT INTO product_purchases (user_id, product_id, product_name_snapshot, price_cents, asaas_payment_id, status, buyer_access_id, stripe_session_id, has_extra_service, extra_service_title_snapshot, extra_service_price_cents) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
    [
      purchase.userId,
      purchase.productId,
      purchase.productNameSnapshot || null,
      purchase.priceCents || null,
      purchase.asaasPaymentId || null,
      purchase.status || 'pending',
      purchase.buyerAccessId || null,
      purchase.stripeSessionId || null,
      purchase.hasExtraService || 0,
      purchase.extraServiceTitleSnapshot || null,
      purchase.extraServicePriceCents || 0
    ]
  );
}

/**
 * Retorna o registro de compra do produto para o usuário (qualquer status exceto 'pending' do Asaas).
 * Útil para saber se a compra existe e qual é o status (completed, pending_delivery, etc.)
 */
export async function getProductPurchaseForUser(userId: number, productId: number): Promise<any | null> {
  return queryOne(
    "SELECT * FROM product_purchases WHERE user_id = ? AND product_id = ? AND status != 'pending' ORDER BY created_at DESC LIMIT 1",
    [userId, productId]
  );
}

export async function hasUserPurchasedProduct(userId: number, productId: number): Promise<boolean> {
  const row = await queryOne(
    "SELECT id FROM product_purchases WHERE user_id = ? AND product_id = ? AND status IN ('completed', 'pending_delivery')",
    [userId, productId]
  );
  return !!row;
}

/**
 * Marca uma compra de produto com entrega manual como entregue (status = 'completed').
 * Chamado pelo admin no painel de vendas após compartilhar o recurso com o comprador.
 */
export async function markManualDelivered(purchaseId: number): Promise<any> {
  return run(
    "UPDATE product_purchases SET status = 'completed' WHERE id = ? AND status = 'pending_delivery'",
    [purchaseId]
  );
}

// ── Área de Membros: Cursos ──────────────────────────────────────────────────

export async function getAllCourses(publishedOnly = false): Promise<any[]> {
  const where = publishedOnly ? 'WHERE mc.published = 1' : '';
  return query(`
    SELECT mc.*,
      (SELECT COUNT(*) FROM member_lessons ml WHERE ml.course_id = mc.id AND ml.published = 1) as lesson_count,
      (SELECT COUNT(*) FROM member_materials mm WHERE mm.course_id = mc.id) as material_count
    FROM member_courses mc
    ${where}
    ORDER BY mc.sort_order ASC, mc.created_at DESC
  `);
}

export async function getCourseBySlug(slug: string): Promise<any | null> {
  return queryOne('SELECT * FROM member_courses WHERE slug = ?', [slug]);
}

export async function getCourseById(id: number): Promise<any | null> {
  return queryOne('SELECT * FROM member_courses WHERE id = ?', [id]);
}

export async function createCourse(course: {
  title: string;
  slug: string;
  description?: string | null;
  cover_image?: string | null;
  access_type?: string;
  price_cents?: number;
  published?: number;
  sort_order?: number;
}): Promise<any> {
  return run(
    `INSERT INTO member_courses (title, slug, description, cover_image, access_type, price_cents, published, sort_order)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
    [
      course.title,
      course.slug,
      course.description || null,
      course.cover_image || null,
      course.access_type || 'premium',
      course.price_cents || 0,
      course.published || 0,
      course.sort_order || 0
    ]
  );
}

export async function updateCourse(id: number, course: {
  title: string;
  slug: string;
  description?: string | null;
  cover_image?: string | null;
  access_type?: string;
  price_cents?: number;
  published?: number;
  sort_order?: number;
}): Promise<any> {
  return run(
    `UPDATE member_courses SET title=?, slug=?, description=?, cover_image=?, access_type=?, price_cents=?, published=?, sort_order=?, updated_at=CURRENT_TIMESTAMP WHERE id=?`,
    [
      course.title,
      course.slug,
      course.description || null,
      course.cover_image || null,
      course.access_type || 'premium',
      course.price_cents || 0,
      course.published || 0,
      course.sort_order || 0,
      id
    ]
  );
}

export async function deleteCourse(id: number): Promise<any> {
  return run('DELETE FROM member_courses WHERE id = ?', [id]);
}

export async function generateUniqueCourseSlug(title: string, excludeId?: number): Promise<string> {
  let slug = title
    .toLowerCase().trim()
    .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9\s-]/g, '')
    .replace(/[\s_]+/g, '-').replace(/-+/g, '-')
    .replace(/^-+|-+$/g, '').substring(0, 60);

  let exists = await queryOne(
    excludeId ? 'SELECT slug FROM member_courses WHERE slug = ? AND id != ?' : 'SELECT slug FROM member_courses WHERE slug = ?',
    excludeId ? [slug, excludeId] : [slug]
  );
  let counter = 2;
  while (exists) {
    const candidate = `${slug}-${counter}`;
    exists = await queryOne('SELECT slug FROM member_courses WHERE slug = ?', [candidate]);
    if (!exists) { slug = candidate; break; }
    counter++;
  }
  return slug;
}

// ── Aulas ────────────────────────────────────────────────────────────────────

export async function getLessonsByCourseId(courseId: number, publishedOnly = false): Promise<any[]> {
  const where = publishedOnly ? 'AND published = 1' : '';
  return query(
    `SELECT * FROM member_lessons WHERE course_id = ? ${where} ORDER BY sort_order ASC, id ASC`,
    [courseId]
  );
}

export async function getLessonById(id: number): Promise<any | null> {
  return queryOne('SELECT * FROM member_lessons WHERE id = ?', [id]);
}

export async function createLesson(lesson: {
  course_id: number;
  title: string;
  content?: string | null;
  video_url?: string | null;
  video_type?: string;
  topic?: string | null;
  sort_order?: number;
  published?: number;
  is_preview?: number;
}): Promise<any> {
  return run(
    `INSERT INTO member_lessons (course_id, title, content, video_url, video_type, topic, sort_order, published, is_preview)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`,
    [
      lesson.course_id,
      lesson.title,
      lesson.content || null,
      lesson.video_url || null,
      lesson.video_type || 'youtube',
      lesson.topic || null,
      lesson.sort_order || 0,
      lesson.published ?? 1,
      lesson.is_preview ?? 0
    ]
  );
}

export async function updateLesson(id: number, lesson: {
  title: string;
  content?: string | null;
  video_url?: string | null;
  video_type?: string;
  topic?: string | null;
  sort_order?: number;
  published?: number;
  is_preview?: number;
}): Promise<any> {
  return run(
    `UPDATE member_lessons SET title=?, content=?, video_url=?, video_type=?, topic=?, sort_order=?, published=?, is_preview=? WHERE id=?`,
    [
      lesson.title,
      lesson.content || null,
      lesson.video_url || null,
      lesson.video_type || 'youtube',
      lesson.topic || null,
      lesson.sort_order ?? 0,
      lesson.published ?? 1,
      lesson.is_preview ?? 0,
      id
    ]
  );
}

export async function deleteLesson(id: number): Promise<any> {
  return run('DELETE FROM member_lessons WHERE id = ?', [id]);
}

// ── Materiais ─────────────────────────────────────────────────────────────────

export async function getMaterialsByCourseId(courseId: number): Promise<any[]> {
  return query('SELECT * FROM member_materials WHERE course_id = ? ORDER BY sort_order ASC, id ASC', [courseId]);
}

export async function createMaterial(material: {
  course_id?: number | null;
  title: string;
  description?: string | null;
  file_url: string;
  file_type?: string | null;
  sort_order?: number;
}): Promise<any> {
  return run(
    `INSERT INTO member_materials (course_id, title, description, file_url, file_type, sort_order)
     VALUES (?, ?, ?, ?, ?, ?)`,
    [
      material.course_id || null,
      material.title,
      material.description || null,
      material.file_url,
      material.file_type || null,
      material.sort_order || 0
    ]
  );
}

export async function deleteMaterial(id: number): Promise<any> {
  return run('DELETE FROM member_materials WHERE id = ?', [id]);
}

// ── Compras de Cursos ─────────────────────────────────────────────────────────

export async function getCoursePurchase(userId: number, courseId: number): Promise<any | null> {
  return queryOne(
    'SELECT * FROM course_purchases WHERE user_id = ? AND course_id = ? ORDER BY id DESC LIMIT 1',
    [userId, courseId]
  );
}

export async function hasUserPurchasedCourse(userId: number, courseId: number): Promise<boolean> {
  const row = await queryOne(
    "SELECT id FROM course_purchases WHERE user_id = ? AND course_id = ? AND status = 'approved'",
    [userId, courseId]
  );
  return !!row;
}

export async function createCoursePurchase(purchase: {
  userId: number;
  courseId: number;
  asaasPaymentId?: string;
  stripeSessionId?: string;
  amountCents?: number;
  status?: string;
}): Promise<any> {
  return run(
    `INSERT INTO course_purchases (user_id, course_id, asaas_payment_id, amount_cents, status, stripe_session_id)
     VALUES (?, ?, ?, ?, ?, ?)`,
    [
      purchase.userId,
      purchase.courseId,
      purchase.asaasPaymentId || null,
      purchase.amountCents || 0,
      purchase.status || 'pending',
      purchase.stripeSessionId || null
    ]
  );
}

export async function updateCoursePurchaseByAsaasId(asaasPaymentId: string, status: string): Promise<any> {
  return run(
    'UPDATE course_purchases SET status = ? WHERE asaas_payment_id = ?',
    [status, asaasPaymentId]
  );
}

export async function getUserCoursePurchases(userId: number): Promise<any[]> {
  return query(
    `SELECT cp.*, mc.title, mc.slug, mc.cover_image
     FROM course_purchases cp
     JOIN member_courses mc ON cp.course_id = mc.id
     WHERE cp.user_id = ? AND cp.status = 'approved'
     ORDER BY cp.created_at DESC`,
    [userId]
  );
}

// ============================================
// SHORTLINKS SYSTEM HELPERS
// ============================================

export interface Shortlink {
  id: number;
  slug: string;
  destination_url: string;
  use_ad_interstitial: number;
  ad_duration_seconds: number;
  clicks_count: number;
  is_indexed: number;
  meta_title?: string;
  meta_description?: string;
  fixed_ad_id?: number | null;
  created_at: string;
  updated_at: string;
}

export async function getAllShortlinks(): Promise<Shortlink[]> {
  return (await query('SELECT * FROM shortlinks ORDER BY created_at DESC')) as Shortlink[];
}

export async function getPaginatedShortlinks(
  q: string = '',
  limit: number = 10,
  offset: number = 0
): Promise<Shortlink[]> {
  const searchTerm = `%${q.trim().toLowerCase()}%`;
  return (await query(
    `SELECT * FROM shortlinks 
     WHERE slug LIKE ? OR destination_url LIKE ? 
     ORDER BY created_at DESC 
     LIMIT ? OFFSET ?`,
    [searchTerm, searchTerm, limit, offset]
  )) as Shortlink[];
}

export async function getShortlinksCount(q: string = ''): Promise<number> {
  const searchTerm = `%${q.trim().toLowerCase()}%`;
  const result = await queryOne(
    `SELECT COUNT(*) as count FROM shortlinks 
     WHERE slug LIKE ? OR destination_url LIKE ?`,
    [searchTerm, searchTerm]
  );
  return result ? (result as any).count : 0;
}

export async function getIndexedShortlinks(): Promise<Shortlink[]> {
  return (await query('SELECT * FROM shortlinks WHERE is_indexed = 1 ORDER BY created_at DESC')) as Shortlink[];
}

export async function getShortlinkBySlug(slug: string): Promise<Shortlink | null> {
  return (await queryOne('SELECT * FROM shortlinks WHERE slug = ?', [slug])) as Shortlink | null;
}

export async function getShortlinkById(id: number | string): Promise<Shortlink | null> {
  return (await queryOne('SELECT * FROM shortlinks WHERE id = ?', [id])) as Shortlink | null;
}

export async function createShortlink(link: {
  slug: string;
  destinationUrl: string;
  useAdInterstitial: number | boolean;
  adDurationSeconds?: number;
  isIndexed?: number | boolean;
  metaTitle?: string;
  metaDescription?: string;
  fixedAdId?: number | null;
}): Promise<any> {
  return run(
    'INSERT INTO shortlinks (slug, destination_url, use_ad_interstitial, ad_duration_seconds, is_indexed, meta_title, meta_description, fixed_ad_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
    [
      link.slug.trim().toLowerCase(),
      link.destinationUrl.trim(),
      link.useAdInterstitial ? 1 : 0,
      link.adDurationSeconds || 5,
      link.isIndexed ? 1 : 0,
      link.metaTitle ? link.metaTitle.trim() : null,
      link.metaDescription ? link.metaDescription.trim() : null,
      link.fixedAdId || null
    ]
  );
}

export async function updateShortlink(
  id: number | string,
  link: {
    slug: string;
    destinationUrl: string;
    useAdInterstitial: number | boolean;
    adDurationSeconds?: number;
    isIndexed?: number | boolean;
    metaTitle?: string;
    metaDescription?: string;
    fixedAdId?: number | null;
  }
): Promise<any> {
  return run(
    'UPDATE shortlinks SET slug = ?, destination_url = ?, use_ad_interstitial = ?, ad_duration_seconds = ?, is_indexed = ?, meta_title = ?, meta_description = ?, fixed_ad_id = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
    [
      link.slug.trim().toLowerCase(),
      link.destinationUrl.trim(),
      link.useAdInterstitial ? 1 : 0,
      link.adDurationSeconds || 5,
      link.isIndexed ? 1 : 0,
      link.metaTitle ? link.metaTitle.trim() : null,
      link.metaDescription ? link.metaDescription.trim() : null,
      link.fixedAdId || null,
      id
    ]
  );
}

export async function deleteShortlink(id: number | string): Promise<any> {
  return run('DELETE FROM shortlinks WHERE id = ?', [id]);
}

export async function incrementShortlinkClicks(slug: string): Promise<any> {
  return run('UPDATE shortlinks SET clicks_count = clicks_count + 1 WHERE slug = ?', [slug]);
}

// ─── Web Stories ────────────────────────────────────────────────────────────

export interface WebStory {
  id: number;
  title: string;
  slug: string;
  cover_image: string | null;
  poster_portrait: string | null;
  source_type: string;
  source_post_id: number | null;
  cta_url: string | null;
  cta_text: string | null;
  published: number;
  sort_order: number;
  created_at: string;
  updated_at: string;
  slide_count?: number;
}

export interface WebStorySlide {
  id: number;
  story_id: number;
  sort_order: number;
  background_image: string | null;
  title: string | null;
  body: string | null;
  cta_url: string | null;
  cta_text: string | null;
}

export async function getAllWebStories(): Promise<WebStory[]> {
  return (await query(
    `SELECT s.*, (SELECT COUNT(*) FROM web_story_slides wss WHERE wss.story_id = s.id) as slide_count
     FROM web_stories s
     ORDER BY s.sort_order ASC, s.created_at DESC`
  )) as WebStory[];
}

export async function getPublishedWebStories(limit: number = 24): Promise<WebStory[]> {
  const safeLimit = Math.max(1, Math.min(limit, 50));
  return (await query(
    `SELECT * FROM web_stories
     WHERE published = 1
     ORDER BY sort_order ASC, created_at DESC
     LIMIT ?`,
    [safeLimit]
  )) as WebStory[];
}

export async function getWebStoryBySlug(slug: string): Promise<WebStory | null> {
  return (await queryOne('SELECT * FROM web_stories WHERE slug = ?', [slug])) as WebStory | null;
}

export async function getWebStoryById(id: number | string): Promise<WebStory | null> {
  return (await queryOne('SELECT * FROM web_stories WHERE id = ?', [id])) as WebStory | null;
}

export async function getWebStorySlides(storyId: number | string): Promise<WebStorySlide[]> {
  return (await query(
    'SELECT * FROM web_story_slides WHERE story_id = ? ORDER BY sort_order ASC, id ASC',
    [storyId]
  )) as WebStorySlide[];
}

export async function createWebStory(data: {
  title: string;
  slug: string;
  coverImage?: string | null;
  posterPortrait?: string | null;
  sourceType?: string;
  sourcePostId?: number | null;
  ctaUrl?: string | null;
  ctaText?: string | null;
  published?: boolean | number;
  sortOrder?: number;
}): Promise<any> {
  return run(
    `INSERT INTO web_stories
      (title, slug, cover_image, poster_portrait, source_type, source_post_id, cta_url, cta_text, published, sort_order)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
    [
      data.title.trim(),
      data.slug.trim().toLowerCase(),
      data.coverImage || null,
      data.posterPortrait || data.coverImage || null,
      data.sourceType || 'manual',
      data.sourcePostId || null,
      data.ctaUrl || null,
      data.ctaText || null,
      data.published ? 1 : 0,
      data.sortOrder ?? 0
    ]
  );
}

export async function updateWebStory(
  id: number | string,
  data: {
    title: string;
    slug: string;
    coverImage?: string | null;
    posterPortrait?: string | null;
    sourceType?: string;
    sourcePostId?: number | null;
    ctaUrl?: string | null;
    ctaText?: string | null;
    published?: boolean | number;
    sortOrder?: number;
  }
): Promise<any> {
  return run(
    `UPDATE web_stories SET
      title = ?, slug = ?, cover_image = ?, poster_portrait = ?,
      source_type = ?, source_post_id = ?, cta_url = ?, cta_text = ?,
      published = ?, sort_order = ?, updated_at = CURRENT_TIMESTAMP
     WHERE id = ?`,
    [
      data.title.trim(),
      data.slug.trim().toLowerCase(),
      data.coverImage || null,
      data.posterPortrait || data.coverImage || null,
      data.sourceType || 'manual',
      data.sourcePostId || null,
      data.ctaUrl || null,
      data.ctaText || null,
      data.published ? 1 : 0,
      data.sortOrder ?? 0,
      id
    ]
  );
}

export async function deleteWebStory(id: number | string): Promise<any> {
  await run('DELETE FROM web_story_slides WHERE story_id = ?', [id]);
  return run('DELETE FROM web_stories WHERE id = ?', [id]);
}

export async function replaceWebStorySlides(
  storyId: number | string,
  slides: Array<{
    backgroundImage?: string | null;
    title?: string | null;
    body?: string | null;
    ctaUrl?: string | null;
    ctaText?: string | null;
  }>
): Promise<void> {
  await run('DELETE FROM web_story_slides WHERE story_id = ?', [storyId]);
  let order = 0;
  for (const slide of slides) {
    await run(
      `INSERT INTO web_story_slides
        (story_id, sort_order, background_image, title, body, cta_url, cta_text)
       VALUES (?, ?, ?, ?, ?, ?, ?)`,
      [
        storyId,
        order++,
        slide.backgroundImage || null,
        slide.title || null,
        slide.body || null,
        slide.ctaUrl || null,
        slide.ctaText || null
      ]
    );
  }
}

/** Generate a unique slug for web stories (not posts). */
export async function generateWebStorySlug(title: string, excludeId?: number): Promise<string> {
  let slug = title
    .toLowerCase()
    .trim()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9\s-]/g, '')
    .replace(/[\s_]+/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-+|-+$/g, '')
    .substring(0, 60) || 'story';

  let candidate = slug;
  let counter = 2;
  while (true) {
    const existing = await queryOne('SELECT id FROM web_stories WHERE slug = ?', [candidate]);
    if (!existing || (excludeId && Number(existing.id) === Number(excludeId))) break;
    candidate = `${slug}-${counter++}`;
  }
  return candidate;
}

export async function recordProductDownload(userId: number, productId: number): Promise<any> {
  return run(
    'INSERT INTO product_downloads (user_id, product_id) VALUES (?, ?)',
    [userId, productId]
  );
}

/**
 * Emails de compradores elegíveis para notificação de atualização de produto.
 * Inclui compras pagas (completed + pending_delivery) e, se o produto for
 * premium_included, assinantes premium ativos.
 */
export async function getProductBuyerEmails(productId: number): Promise<string[]> {
  const emails = new Set<string>();

  try {
    const buyers = await query(
      `SELECT DISTINCT u.username AS email
       FROM product_purchases pp
       JOIN users u ON pp.user_id = u.id
       WHERE pp.product_id = ?
         AND pp.status IN ('completed', 'pending_delivery')
         AND u.username IS NOT NULL
         AND trim(u.username) != ''`,
      [productId]
    );
    for (const row of buyers as any[]) {
      const email = String(row.email || '').trim().toLowerCase();
      if (email.includes('@')) emails.add(email);
    }

    const product = await queryOne(
      'SELECT is_premium_included FROM products WHERE id = ?',
      [productId]
    );
    if (product && Number(product.is_premium_included) === 1) {
      const premiumUsers = await query(
        `SELECT DISTINCT u.username AS email
         FROM premium_subscriptions ps
         JOIN users u ON ps.user_id = u.id
         WHERE ps.status = 'active'
           AND (ps.expires_at IS NULL OR ps.expires_at > datetime('now'))
           AND u.username IS NOT NULL
           AND trim(u.username) != ''`
      );
      for (const row of premiumUsers as any[]) {
        const email = String(row.email || '').trim().toLowerCase();
        if (email.includes('@')) emails.add(email);
      }
    }
  } catch (e) {
    console.error('[DB] getProductBuyerEmails error:', e);
  }

  return Array.from(emails);
}

export async function getSalesSummary(): Promise<any> {
  const db = await getClient();
  
  const products = await queryOne(
    `SELECT COUNT(*) as count, SUM(COALESCE(pp.price_cents, p.price_cents, 0)) as total 
     FROM product_purchases pp
     LEFT JOIN products p ON pp.product_id = p.id
     WHERE pp.status = 'completed'`
  );
  
  const courses = await queryOne(
    `SELECT COUNT(*) as count, SUM(cp.amount_cents) as total 
     FROM course_purchases cp
     WHERE cp.status = 'approved'`
  );

  const subscriptions = await queryOne(
    `SELECT COUNT(*) as count, SUM(py.amount_cents) as total 
     FROM premium_payments py
     WHERE py.status = 'approved'`
  );

  const activeSubscriptions = await queryOne(
    `SELECT COUNT(*) as count FROM premium_subscriptions WHERE status = 'active'`
  );

  const totalRevenueCents = (products?.total || 0) + (courses?.total || 0) + (subscriptions?.total || 0);

  return {
    totalRevenue: totalRevenueCents / 100,
    totalRevenueCents,
    productSalesCount: products?.count || 0,
    productRevenue: (products?.total || 0) / 100,
    courseSalesCount: courses?.count || 0,
    courseRevenue: (courses?.total || 0) / 100,
    subscriptionSalesCount: subscriptions?.count || 0,
    subscriptionRevenue: (subscriptions?.total || 0) / 100,
    activeSubscriptionsCount: activeSubscriptions?.count || 0
  };
}

export async function getSalesHistory(): Promise<any[]> {
  const db = await getClient();
  const result = await db.execute(`
    SELECT * FROM (
      SELECT 
        pp.id,
        pp.user_id,
        u.username,
        u.name as user_name,
        COALESCE(pp.product_name_snapshot, p.name, 'Produto') as item_name,
        COALESCE(pp.price_cents, p.price_cents, 0) as amount_cents,
        'product' as item_type,
        pp.status,
        pp.created_at,
        pp.buyer_access_id,
        COALESCE(p.resource_type, 'file') as product_resource_type,
        COALESCE(pp.has_extra_service, 0) as has_extra_service,
        pp.extra_service_title_snapshot,
        COALESCE(pp.extra_service_price_cents, 0) as extra_service_price_cents
      FROM product_purchases pp
      JOIN users u ON pp.user_id = u.id
      LEFT JOIN products p ON pp.product_id = p.id

      UNION ALL

      SELECT 
        cp.id,
        cp.user_id,
        u.username,
        u.name as user_name,
        c.title as item_name,
        COALESCE(cp.amount_cents, 0) as amount_cents,
        'course' as item_type,
        cp.status,
        cp.created_at,
        NULL as buyer_access_id,
        NULL as product_resource_type,
        0 as has_extra_service,
        NULL as extra_service_title_snapshot,
        0 as extra_service_price_cents
      FROM course_purchases cp
      JOIN users u ON cp.user_id = u.id
      JOIN member_courses c ON cp.course_id = c.id

      UNION ALL

      SELECT 
        py.id,
        s.user_id,
        u.username,
        u.name as user_name,
        pl.name as item_name,
        py.amount_cents,
        'subscription' as item_type,
        py.status,
        py.created_at,
        NULL as buyer_access_id,
        NULL as product_resource_type,
        0 as has_extra_service,
        NULL as extra_service_title_snapshot,
        0 as extra_service_price_cents
      FROM premium_payments py
      JOIN premium_subscriptions s ON py.subscription_id = s.id
      JOIN users u ON s.user_id = u.id
      JOIN premium_plans pl ON s.plan_id = pl.id
    ) AS sales
    ORDER BY created_at DESC
  `);
  return result.rows || [];
}

export async function getUsersHoldings(): Promise<any[]> {
  const db = await getClient();
  
  // 1. Fetch all users
  const usersResult = await db.execute(
    "SELECT id, username, name, role, created_at FROM users WHERE role != 'admin' ORDER BY created_at DESC"
  );
  const users = usersResult.rows || [];

  // 2. Fetch all product purchases
  const productsResult = await db.execute(`
    SELECT pp.user_id, pp.product_id, COALESCE(pp.product_name_snapshot, p.name, 'Produto') as item_name, pp.created_at,
           (SELECT COUNT(*) FROM product_downloads pd WHERE pd.user_id = pp.user_id AND pd.product_id = pp.product_id) as download_count
    FROM product_purchases pp
    LEFT JOIN products p ON pp.product_id = p.id
    WHERE pp.status = 'completed'
  `);
  const productPurchases = productsResult.rows || [];

  // 3. Fetch all course purchases
  const coursesResult = await db.execute(`
    SELECT cp.user_id, cp.course_id, c.title as item_name, cp.created_at
    FROM course_purchases cp
    JOIN member_courses c ON cp.course_id = c.id
    WHERE cp.status = 'approved'
  `);
  const coursePurchases = coursesResult.rows || [];

  // 4. Fetch all active subscriptions
  const subsResult = await db.execute(`
    SELECT s.user_id, pl.name as plan_name, s.expires_at, s.status, s.created_at
    FROM premium_subscriptions s
    JOIN premium_plans pl ON s.plan_id = pl.id
    WHERE s.status = 'active'
  `);
  const subscriptions = subsResult.rows || [];

  // Map everything together
  return users.map((u: any) => ({
    id: u.id,
    username: u.username,
    name: u.name,
    role: u.role,
    createdAt: u.created_at,
    products: productPurchases.filter((p: any) => p.user_id === u.id),
    courses: coursePurchases.filter((c: any) => c.user_id === u.id),
    subscription: subscriptions.find((s: any) => s.user_id === u.id) || null
  }));
}

export async function getRelatedProducts(productId: number, categoryId: number | null, limit: number = 3): Promise<Product[]> {
  let rows: Product[] = [];

  if (categoryId) {
    // 1. Try to find products in the same category_id
    rows = mapProductRows(
      await query(
        `${PRODUCT_SELECT_WITH_CATEGORY} WHERE p.category_id = ? AND p.id != ? ORDER BY p.created_at DESC LIMIT ?`,
        [categoryId, productId, limit]
      )
    );
  }

  // 2. If not enough, fill with other products
  if (rows.length < limit) {
    const needed = limit - rows.length;
    const excludeIds = [productId, ...rows.map((r) => r.id)];
    const placeholders = excludeIds.map(() => '?').join(',');

    const extra = mapProductRows(
      await query(
        `${PRODUCT_SELECT_WITH_CATEGORY} WHERE p.id NOT IN (${placeholders}) ORDER BY p.created_at DESC LIMIT ?`,
        [...excludeIds, needed]
      )
    );
    rows = [...rows, ...extra];
  }

  return rows;
}

export async function getProductCategories(): Promise<ProductCategory[]> {
  return (await query('SELECT * FROM product_categories ORDER BY name ASC')) as ProductCategory[];
}

export async function createProductCategory(name: string, description?: string): Promise<any> {
  let baseSlug = name
    .toLowerCase()
    .trim()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9\s-]/g, '')
    .replace(/[\s_]+/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-+|-+$/g, '')
    .substring(0, 60);
  if (!baseSlug) baseSlug = `categoria-${Date.now()}`;

  let slug = baseSlug;
  let counter = 2;
  while (true) {
    const check = await queryOne('SELECT id FROM product_categories WHERE slug = ?', [slug]);
    if (!check) break;
    slug = `${baseSlug}-${counter}`;
    counter++;
  }

  return run(
    'INSERT INTO product_categories (name, slug, description) VALUES (?, ?, ?)',
    [name.trim(), slug, description || null]
  );
}

export async function updateProductCategory(id: number, name: string, description?: string): Promise<any> {
  let baseSlug = name
    .toLowerCase()
    .trim()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9\s-]/g, '')
    .replace(/[\s_]+/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-+|-+$/g, '')
    .substring(0, 60);
  if (!baseSlug) baseSlug = `categoria-${Date.now()}`;

  let slug = baseSlug;
  let counter = 2;
  while (true) {
    const check = await queryOne('SELECT id FROM product_categories WHERE slug = ? AND id != ?', [slug, id]);
    if (!check) break;
    slug = `${baseSlug}-${counter}`;
    counter++;
  }

  return run(
    'UPDATE product_categories SET name = ?, slug = ?, description = ? WHERE id = ?',
    [name.trim(), slug, description || null, id]
  );
}

export async function deleteProductCategory(id: number): Promise<any> {
  return run('DELETE FROM product_categories WHERE id = ?', [id]);
}

export async function autoTagExistingPosts(): Promise<void> {
  try {
    const posts = await query('SELECT id, title, tags FROM posts');
    const keywords = ['IA', 'SEO', 'Pinterest', 'WordPress', 'Svelte', 'Cloudinary', 'Mercado Livre', 'Mercado Pago', 'Asaas', 'Google', 'WhatsApp', 'YouTube', 'Dinheiro', 'Tráfego', 'Afiliado'];
    for (const post of posts as any[]) {
      if (!post.tags || post.tags.trim() === '') {
        const tags: string[] = [];
        const titleLower = post.title.toLowerCase();
        for (const kw of keywords) {
          if (titleLower.includes(kw.toLowerCase())) {
            tags.push(kw);
          }
        }
        if (tags.length === 0) {
          tags.push('Geral');
        }
        await run('UPDATE posts SET tags = ? WHERE id = ?', [tags.join(', '), post.id]);
      }
    }
  } catch (e) {
    console.error('Error auto-tagging existing posts:', e);
  }
}

export async function incrementUserInterest(userId: number, type: 'category' | 'tag', name: string, points: number): Promise<void> {
  if (!userId || !name) return;
  const normalizedName = name.trim();
  try {
    const existing = await queryOne('SELECT score FROM user_interests WHERE user_id = ? AND interest_type = ? AND name = ?', [userId, type, normalizedName]);
    if (existing) {
      const newScore = (existing.score || 0) + points;
      await run('UPDATE user_interests SET score = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ? AND interest_type = ? AND name = ?', [newScore, userId, type, normalizedName]);
    } else {
      await run('INSERT INTO user_interests (user_id, interest_type, name, score) VALUES (?, ?, ?, ?)', [userId, type, normalizedName, points]);
    }
  } catch (e) {
    console.error('Error in incrementUserInterest:', e);
  }
}

export async function getUserInterests(userId: number): Promise<{ categories: Record<string, number>; tags: Record<string, number> }> {
  const result = { categories: {} as Record<string, number>, tags: {} as Record<string, number> };
  if (!userId) return result;
  try {
    const rows = await query('SELECT interest_type, name, score FROM user_interests WHERE user_id = ?', [userId]);
    for (const row of rows as any[]) {
      if (row.interest_type === 'category') {
        result.categories[row.name] = row.score || 0;
      } else if (row.interest_type === 'tag') {
        result.tags[row.name] = row.score || 0;
      }
    }
  } catch (e) {
    console.error('Error in getUserInterests:', e);
  }
  return result;
}

export async function mergeAnonymousInterests(userId: number, anonymousInterestsJson: string): Promise<void> {
  if (!userId || !anonymousInterestsJson) return;
  try {
    const parsed = JSON.parse(anonymousInterestsJson);
    const categories = parsed.categories || {};
    const tags = parsed.tags || {};

    for (const [name, score] of Object.entries(categories)) {
      if (typeof score === 'number' && score > 0) {
        await incrementUserInterest(userId, 'category', name, score);
      }
    }
    for (const [name, score] of Object.entries(tags)) {
      if (typeof score === 'number' && score > 0) {
        await incrementUserInterest(userId, 'tag', name, score);
      }
    }
  } catch (e) {
    console.error('Error merging anonymous interests:', e);
  }
}

/** Mark a post as recently seen for a logged-in member (upsert timestamp). */
export async function upsertUserSeenPost(userId: number, postId: number, seenAtMs: number = Date.now()): Promise<void> {
  if (!userId || !postId) return;
  try {
    const existing = await queryOne(
      'SELECT seen_at FROM user_seen_posts WHERE user_id = ? AND post_id = ?',
      [userId, postId]
    );
    if (existing) {
      await run(
        'UPDATE user_seen_posts SET seen_at = ? WHERE user_id = ? AND post_id = ?',
        [seenAtMs, userId, postId]
      );
    } else {
      await run(
        'INSERT INTO user_seen_posts (user_id, post_id, seen_at) VALUES (?, ?, ?)',
        [userId, postId, seenAtMs]
      );
    }
  } catch (e) {
    console.error('Error in upsertUserSeenPost:', e);
  }
}

/**
 * Recently-seen map for feed suppression: postId → seenAt (ms).
 * Only returns rows still inside the cooldown window.
 */
export async function getUserSeenPosts(
  userId: number,
  cooldownMs: number
): Promise<Map<number, number>> {
  const map = new Map<number, number>();
  if (!userId) return map;
  const since = Date.now() - cooldownMs;
  try {
    const rows = await query(
      'SELECT post_id, seen_at FROM user_seen_posts WHERE user_id = ? AND seen_at >= ?',
      [userId, since]
    );
    for (const row of rows as any[]) {
      map.set(Number(row.post_id), Number(row.seen_at));
    }
    // Opportunistic prune of very old rows (keep DB lean)
    const pruneBefore = Date.now() - cooldownMs * 2;
    await run('DELETE FROM user_seen_posts WHERE user_id = ? AND seen_at < ?', [userId, pruneBefore]);
  } catch (e) {
    console.error('Error in getUserSeenPosts:', e);
  }
  return map;
}

/** Merge anonymous cookie seen-history into the logged-in account on login/register. */
export async function mergeAnonymousSeenPosts(
  userId: number,
  seenMap: Map<number, number> | Record<string, number>
): Promise<void> {
  if (!userId) return;
  try {
    const entries =
      seenMap instanceof Map
        ? Array.from(seenMap.entries())
        : Object.entries(seenMap).map(([k, v]) => [Number(k), Number(v)] as [number, number]);

    for (const [postId, seenAt] of entries) {
      if (!postId || !seenAt) continue;
      const existing = await queryOne(
        'SELECT seen_at FROM user_seen_posts WHERE user_id = ? AND post_id = ?',
        [userId, postId]
      );
      if (!existing || Number(existing.seen_at) < seenAt) {
        await upsertUserSeenPost(userId, postId, seenAt);
      }
    }
  } catch (e) {
    console.error('Error merging anonymous seen posts:', e);
  }
}

export async function incrementCollaborativeRelation(fromId: number, toId: number): Promise<void> {
  if (!fromId || !toId || fromId === toId) return;
  try {
    const existing = await queryOne('SELECT score FROM collaborative_recommendations WHERE from_post_id = ? AND to_post_id = ?', [fromId, toId]);
    if (existing) {
      const newScore = (existing.score || 0) + 1;
      await run('UPDATE collaborative_recommendations SET score = ? WHERE from_post_id = ? AND to_post_id = ?', [newScore, fromId, toId]);
    } else {
      await run('INSERT INTO collaborative_recommendations (from_post_id, to_post_id, score) VALUES (?, ?, 1)', [fromId, toId]);
    }
  } catch (e) {
    console.error('Error in incrementCollaborativeRelation:', e);
  }
}

export async function getCollaborativeRecommendations(postId: number, limit: number = 3): Promise<Post[]> {
  if (!postId) return [];
  try {
    const sql = `
      SELECT p.*, GROUP_CONCAT(c.name) as categories
      FROM collaborative_recommendations cr
      JOIN posts p ON cr.to_post_id = p.id
      LEFT JOIN post_categories pc ON p.id = pc.post_id
      LEFT JOIN categories c ON pc.category_id = c.id
      WHERE cr.from_post_id = ? AND p.published = 1
      GROUP BY p.id
      ORDER BY cr.score DESC
      LIMIT ?`;
    const posts = await query(sql, [postId, limit]);
    return posts.map(p => ({ ...p, isCollaborative: true })) as Post[];
  } catch (e) {
    console.error('Error in getCollaborativeRecommendations:', e);
    return [];
  }
}

/**
 * Cria uma nova avaliação para um produto.
 */
export async function createProductReview(review: {
  productId: number;
  userId: number;
  rating: number;
  comment?: string | null;
}): Promise<any> {
  return run(
    'INSERT INTO product_reviews (product_id, user_id, rating, comment) VALUES (?, ?, ?, ?)',
    [
      review.productId,
      review.userId,
      review.rating,
      review.comment || null
    ]
  );
}

/**
 * Retorna todas as avaliações de um produto ordenadas pelas mais recentes.
 */
export async function getProductReviews(productId: number): Promise<any[]> {
  return query(
    `SELECT r.*, u.username, u.name as user_name
     FROM product_reviews r
     JOIN users u ON r.user_id = u.id
     WHERE r.product_id = ?
     ORDER BY r.created_at DESC`,
    [productId]
  );
}

/**
 * Retorna o resumo de avaliações de um produto (média e total de avaliações).
 */
export async function getProductReviewSummary(productId: number): Promise<{ averageRating: number; totalCount: number }> {
  const row = await queryOne(
    `SELECT COALESCE(AVG(rating), 0) as average_rating, COUNT(*) as total_count
     FROM product_reviews
     WHERE product_id = ?`,
    [productId]
  );

  return {
    averageRating: parseFloat(row?.average_rating ? row.average_rating.toFixed(1) : '0'),
    totalCount: row?.total_count || 0
  };
}

/**
 * Verifica se um usuário já avaliou um produto.
 */
export async function hasUserReviewedProduct(userId: number, productId: number): Promise<boolean> {
  const row = await queryOne(
    'SELECT id FROM product_reviews WHERE user_id = ? AND product_id = ? LIMIT 1',
    [userId, productId]
  );
  return !!row;
}

/**
 * Retorna todas as Landing Pages cadastradas.
 */
export async function getAllLandingPages(): Promise<any[]> {
  const rows = await query('SELECT * FROM landing_pages ORDER BY created_at DESC');
  return rows || [];
}

/**
 * Retorna uma Landing Page pelo ID.
 */
export async function getLandingPageById(id: number): Promise<any | null> {
  return await queryOne('SELECT * FROM landing_pages WHERE id = ?', [id]);
}

/**
 * Retorna uma Landing Page pelo Slug.
 */
export async function getLandingPageBySlug(slug: string): Promise<any | null> {
  return await queryOne('SELECT * FROM landing_pages WHERE slug = ?', [slug]);
}

/**
 * Cria uma nova Landing Page preliminar (sem conteúdo).
 */
export async function createLandingPage(title: string, slug: string): Promise<number> {
  const result = await run(
    'INSERT INTO landing_pages (title, slug, status, content, settings) VALUES (?, ?, ?, ?, ?)',
    [title.trim(), slug.trim(), 'draft', '[]', '{}']
  );
  if (result && result.lastInsertRowid !== undefined) {
    return Number(result.lastInsertRowid);
  }
  const lastIdRow = await queryOne('SELECT last_insert_rowid() AS id');
  if (lastIdRow && lastIdRow.id !== undefined) {
    return Number(lastIdRow.id);
  }
  throw new Error('Não foi possível obter o ID gerado para a landing page.');
}

/**
 * Atualiza os metadados ou conteúdo de uma Landing Page.
 */
export async function updateLandingPage(
  id: number,
  title: string,
  slug: string,
  status: string,
  content?: string,
  settings?: string
): Promise<void> {
  if (content !== undefined && settings !== undefined) {
    await run(
      'UPDATE landing_pages SET title = ?, slug = ?, status = ?, content = ?, settings = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
      [title.trim(), slug.trim(), status, content, settings, id]
    );
  } else {
    await run(
      'UPDATE landing_pages SET title = ?, slug = ?, status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
      [title.trim(), slug.trim(), status, id]
    );
  }
}

/**
 * Exclui uma Landing Page.
 */
export async function deleteLandingPage(id: number): Promise<void> {
  await run('DELETE FROM landing_pages WHERE id = ?', [id]);
}

/**
 * Duplica uma Landing Page (conteúdo + settings), com slug único e status draft.
 */
export async function duplicateLandingPage(id: number): Promise<number> {
  const source = await getLandingPageById(id);
  if (!source) {
    throw new Error('Landing page not found');
  }

  const baseSlug = `${source.slug}-copy`.substring(0, 50);
  let slug = baseSlug;
  let n = 2;
  while (await getLandingPageBySlug(slug)) {
    slug = `${baseSlug}-${n}`.substring(0, 60);
    n++;
  }

  const title = `${source.title} (copy)`;
  const result = await run(
    'INSERT INTO landing_pages (title, slug, status, content, settings) VALUES (?, ?, ?, ?, ?)',
    [title, slug, 'draft', source.content || '[]', source.settings || '{}']
  );
  if (result && result.lastInsertRowid !== undefined) {
    return Number(result.lastInsertRowid);
  }
  const lastIdRow = await queryOne('SELECT last_insert_rowid() AS id');
  if (lastIdRow && lastIdRow.id !== undefined) {
    return Number(lastIdRow.id);
  }
  throw new Error('Could not get new landing page id');
}