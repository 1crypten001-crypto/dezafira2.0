import { env } from '$env/dynamic/private';
import { createClient } from '@libsql/client';
import * as dotenv from 'dotenv';

dotenv.config();

const DATABASE_URL = process.env.DATABASE_URL;
const DATABASE_AUTH_TOKEN = process.env.DATABASE_AUTH_TOKEN;

if (!DATABASE_URL) {
    console.error("DATABASE_URL is not set");
    process.exit(1);
}

const db = createClient({
    url: DATABASE_URL,
    authToken: DATABASE_AUTH_TOKEN
});

const schema = [
    `CREATE TABLE IF NOT EXISTS users (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		username TEXT UNIQUE NOT NULL,
		password TEXT NOT NULL,
		created_at DATETIME DEFAULT CURRENT_TIMESTAMP
	)`,
    `CREATE TABLE IF NOT EXISTS settings (
		key TEXT PRIMARY KEY,
		value TEXT
	)`,
    `CREATE TABLE IF NOT EXISTS posts (
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
		created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
		updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
	)`,
    `CREATE TABLE IF NOT EXISTS categories (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		name TEXT UNIQUE NOT NULL,
		slug TEXT UNIQUE NOT NULL,
		description TEXT,
		pinterest_enabled INTEGER DEFAULT 0,
        updated_at DATETIME
	)`,
    `CREATE TABLE IF NOT EXISTS sessions (
		id TEXT PRIMARY KEY,
		username TEXT NOT NULL,
		expires_at INTEGER NOT NULL,
		created_at DATETIME DEFAULT CURRENT_TIMESTAMP
	)`,
    `CREATE TABLE IF NOT EXISTS post_categories (
		post_id INTEGER NOT NULL,
		category_id INTEGER NOT NULL,
		PRIMARY KEY (post_id, category_id),
		FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
		FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
	)`,
    `CREATE TABLE IF NOT EXISTS ads (
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
		created_at DATETIME DEFAULT CURRENT_TIMESTAMP
	)`,
    `CREATE TABLE IF NOT EXISTS premium_plans (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		name TEXT NOT NULL,
		slug TEXT UNIQUE NOT NULL,
		description TEXT,
		price_cents INTEGER NOT NULL,
		interval_days INTEGER NOT NULL DEFAULT 30,
		mp_plan_id TEXT,
		features TEXT,
		is_active INTEGER DEFAULT 1,
		created_at DATETIME DEFAULT CURRENT_TIMESTAMP
	)`,
    `CREATE TABLE IF NOT EXISTS premium_subscriptions (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		user_id INTEGER NOT NULL,
		plan_id INTEGER NOT NULL,
		mp_subscription_id TEXT,
		mp_payment_id TEXT,
		status TEXT NOT NULL DEFAULT 'pending',
		started_at DATETIME,
		expires_at DATETIME,
		created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
		FOREIGN KEY (user_id) REFERENCES users(id),
		FOREIGN KEY (plan_id) REFERENCES premium_plans(id)
	)`,
    `CREATE TABLE IF NOT EXISTS premium_payments (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		subscription_id INTEGER,
		mp_payment_id TEXT UNIQUE,
		amount_cents INTEGER NOT NULL,
		status TEXT NOT NULL,
		payment_method TEXT,
		created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
		FOREIGN KEY (subscription_id) REFERENCES premium_subscriptions(id)
	)`
];

async function init() {
    console.log("Initializing Turso database schema...");
    for (const sql of schema) {
        try {
            await db.execute(sql);
            console.log("Executed: " + sql.split('(')[0].trim());
        } catch (e: any) {
            console.error("Error executing SQL: " + e.message);
        }
    }

    // Seed admin user if it doesn't exist
    const adminUser = process.env.ADMIN_USERNAME || 'admin';
    const adminPass = process.env.ADMIN_PASSWORD || 'admin';
    
    try {
        const userExists = await db.execute({
            sql: "SELECT id FROM users WHERE username = ?",
            args: [adminUser]
        });

        if (userExists.rows.length === 0) {
            console.log("Seeding admin user...");
            const bcrypt = await import('bcryptjs');
            const hasher = bcrypt.default ? bcrypt.default : bcrypt;
            const hashedPassword = await hasher.hash(adminPass, 10);
            await db.execute({
                sql: "INSERT INTO users (username, password) VALUES (?, ?)",
                args: [adminUser, hashedPassword]
            });
            console.log("Admin user created!");
        }
    } catch (e: any) {
        console.error("Error seeding admin user: " + e.message);
    }

    // Seed default settings
    const defaultSettings = [
        { key: 'site_name', value: 'Meu Blog Svelte' },
        { key: 'site_description', value: 'Um blog moderno feito com SvelteKit e SQLite' },
        { key: 'feed_loading_mode', value: 'pagination' }
    ];

    for (const setting of defaultSettings) {
        try {
            await db.execute({
                sql: "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
                args: [setting.key, setting.value]
            });
        } catch (e: any) {
            console.error(`Error seeding setting ${setting.key}: ${e.message}`);
        }
    }

    console.log("Database initialization and seeding complete!");
}

init();
