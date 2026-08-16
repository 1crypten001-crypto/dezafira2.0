# AI Agent Developer Guide (agents.md)

Welcome, AI Coding Agent! This document acts as your onboarding manual to understand the technical architecture, constraints, coding style, database schema, and best practices of this SvelteKit Whitelabel Blog.

---

## 🛠️ Tech Stack & Key Integrations

* **Framework**: SvelteKit 2.x with Svelte 5 (using Runes: `$state`, `$derived`, `$effect`, `$props`).
* **Database**: Dual-driver database integration using LibSQL (Turso) for production, falling back to `better-sqlite3` for local development.
  > [!IMPORTANT]
  > **Hosting Compatibility**: While local SQLite (`better-sqlite3`) works flawlessly in production on persistent servers (VPS, Dedicated, PM2, Docker, Hostinger Node), Turso is strictly required for Serverless platforms (Vercel, Netlify) due to their ephemeral filesystems.
* **Storage**: Media uploads (such as post cover images and course materials) are hosted on Cloudinary.
* **Payments**: Integration with Asaas for subscriptions, products, and courses (configured via Admin Panel settings).
* **AI engine**: Powered by Google Gemini API (using `gemini-2.5-flash` model) to automate content imports and translations.

---

## 📁 Project Structure

```text
/
├── docs/                      # General documentation
│   ├── agents.md              # This onboarding file
│   └── ...
├── src/
│   ├── app.css                # Global styles, variables, dark mode theme
│   ├── hooks.server.ts        # Performance handles, auth checks, server-side analytics
│   ├── lib/
│   │   ├── components/        # Reusable Svelte components (Header, Footer, Pagination)
│   │   ├── server/
│   │   │   ├── database.ts    # Main database interface, query builders, and CRUD helpers
│   │   │   ├── auth.ts        # Sessions validation, rate limiting, and password hashing
│   │   │   ├── sanitize.ts    # XSS prevention utilities
│   │   │   └── tenant.ts      # Multi-tenant context helpers
│   ├── routes/
│   │   ├── +layout.svelte     # Main layout, StoriesBar (optional), user state
│   │   ├── +page.svelte       # Homepage (smart feed + hero)
│   │   ├── admin/             # Admin panel (admin_session cookie)
│   │   │   └── web-stories/   # Web Stories CRUD (Tools menu)
│   │   ├── api/               # Webhooks, CLI, upload, recommendations track
│   │   ├── l/[slug]/          # Shortlinks (redirect / ad interstitial)
│   │   ├── stories/[slug]/    # Public AMP Web Story (+server.ts HTML)
│   │   ├── members/           # Members Area & registration/login
│   │   ├── post/[slug]/       # Public post view
│   │   └── ...
│   ├── lib/server/
│   │   ├── interest-engine.ts # Smart home feed + seen cooldown
│   │   └── web-story-amp.ts   # AMP HTML builder for stories
├── scripts/
│   └── init-db.ts             # Database schema seeding script
├── package.json
└── tsconfig.json
```

---

## 🗄️ Database Schemas (SQLite/LibSQL)

Review the core tables schema to understand query parameters and database operations:

```sql
-- Users and Accounts
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL,
  role TEXT DEFAULT 'member', -- 'admin' | 'member'
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Sessions
CREATE TABLE IF NOT EXISTS sessions (
  id TEXT PRIMARY KEY,
  username TEXT NOT NULL,
  expires_at INTEGER NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Blog Posts
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
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Categories
CREATE TABLE IF NOT EXISTS categories (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT UNIQUE NOT NULL,
  slug TEXT UNIQUE NOT NULL,
  description TEXT,
  pinterest_enabled INTEGER DEFAULT 0,
  updated_at DATETIME
);

-- Member Courses (Members Area)
CREATE TABLE IF NOT EXISTS member_courses (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  slug TEXT UNIQUE NOT NULL,
  description TEXT,
  cover_image TEXT,
  access_type TEXT DEFAULT 'premium', -- 'free' | 'premium' | 'paid'
  price_cents INTEGER DEFAULT 0,
  asaas_product_id TEXT,
  published INTEGER DEFAULT 0,
  sort_order INTEGER DEFAULT 0,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Course Lessons
CREATE TABLE IF NOT EXISTS member_lessons (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  course_id INTEGER NOT NULL,
  title TEXT NOT NULL,
  content TEXT,
  video_url TEXT,
  video_type TEXT DEFAULT 'youtube',
  sort_order INTEGER DEFAULT 0,
  published INTEGER DEFAULT 1,
  is_preview INTEGER DEFAULT 0,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (course_id) REFERENCES member_courses(id) ON DELETE CASCADE
);

-- Page views (Analytics)
CREATE TABLE IF NOT EXISTS page_views (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  page_type TEXT NOT NULL, -- 'home' | 'post' | 'category' | 'other'
  slug TEXT,
  ip_address TEXT,
  user_agent TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Web Stories (AMP)
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
);

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
);

-- Recently seen posts (feed cooldown, logged-in users)
CREATE TABLE IF NOT EXISTS user_seen_posts (
  user_id INTEGER NOT NULL,
  post_id INTEGER NOT NULL,
  seen_at INTEGER NOT NULL,
  PRIMARY KEY (user_id, post_id)
);
```

### Smart feed & Web Stories (quick notes)

* **Home feed**: `getHomeFeed` in `interest-engine.ts` mixes fresh / relevant / discover buckets; `applySeenCooldown` demotes posts viewed in the last ~48h. Infinite scroll must call the same ranking (`/api/posts`).
* **Web Stories**: Never inject free HTML into AMP. Use `buildAmpWebStoryHtml`. Public route is `+server.ts` returning full HTML. Setting `enable_web_stories_bar=1` shows bubbles under the header.
* **Docs**: `docs/web-stories.md`, `docs/shortlinks.md`, `docs/changelog-v1.7.md`.

---

## 🎨 Coding Style Guidelines (Svelte 5)

When creating or modifying components, align with Svelte 5 standards:

### 1. Runes Usage
Avoid Svelte 4 reactivity syntax (`let` for reactive updates or `$:` for computed values). Use runes:
* Use `$state(...)` for reactive values.
* Use `$derived(...)` for computed properties derived from state.
* Use `$effect(...)` for side-effects. Remember to perform cleanup inside effects if subscribing to intervals or timers.
* Use `$props()` to destructure properties:
  ```typescript
  let { data, children } = $props();
  ```

### 2. Form Actions
Use SvelteKit's standard form actions with the `<form method="POST" use:enhance>` directive for client-side enhancement without full page reloads.

### 3. Server Hooks
Do not write tracking or security controls inside load functions if they can be handled globally. Use `src/hooks.server.ts` to implement middleware checks (such as performance tracking, auth parsing, CORS headers, and analytics view registration).

### 4. Admin Security Rule
Always validate `ADMIN_PASSWORD` on server startup. Production builds (`NODE_ENV=production`) will abort if the admin password is too weak or does not exist. Do not bypass this validation.

---

## ⚠️ Svelte 5 & SvelteKit Gotchas & Architectural Rules

### 1. JSON-LD Escaping inside `<svelte:head>`
* **Gotcha**: Svelte automatically escapes HTML entities (like converting double quotes `"` to `&quot;`) when rendering standard script tags in `<svelte:head>`. This breaks JSON-LD structured data formats, causing Google Search Console errors.
* **Fix**: Always wrap the JSON payload of structured data `<script type="application/ld+json">` inside a Svelte `{@html ...}` tag:
  ```html
  <svelte:head>
    <script type="application/ld+json">
      {@html JSON.stringify(mySchemaObject)}
    </script>
  </svelte:head>
  ```

### 2. Form Checkboxes & DOM Destruction
* **Gotcha**: If you conditionally hide a checkbox element using `{#if !state}` after it is checked, Svelte destroys the input node. When the form is submitted, the value will NOT be included in the form data payload.
* **Fix**: To submit removal/boolean flags reliably, bind the state to a reactive boolean variable and output a persistent hidden input element that is always rendered in the DOM:
  ```html
  <input type="checkbox" bind:checked={removeImage} />
  <input type="hidden" name="remove_image" value={removeImage ? "1" : "0"} />
  ```

### 3. Server Request Body Size Limit (`BODY_SIZE_LIMIT`)
* **Rule**: By default, SvelteKit node adapter rejects payloads exceeding 10MB.
* **Fix**: If you need to support uploads up to 30MB (such as downloadable PDF/ZIP product files), ensure `BODY_SIZE_LIMIT=104857600` (100MB) is configured in your `.env` and production host variables.

### 4. Media/Asset File Deletion (Self-Cleaning)
* **Rule**: Whenever an asset-linked DB row is deleted (e.g. deleting a product or post with local attachments), you must clean up the physical file on disk (`static/uploads/...`) using `fs.unlinkSync` inside a try-catch block to prevent disk clutter and orphaned file security issues.

---

## 🛠️ CLI Commands Reference

Use these scripts during development and testing tasks:

* **Start Dev Server**: `npm run dev`
* **Build App**: `npm run build`
* **Test Local Build**: `npm run preview`
* **Initialize/Seed Database**: `npm run init-db` (Runs `scripts/init-db.ts`)
* **Run Tests**: `npm run test` (Uses Vitest)
* **Run Typecheck**: `npm run typecheck`

