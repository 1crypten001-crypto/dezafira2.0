// ============================================================================
// DEZAFIRACLUBE — Migração SQLite local → Turso Cloud
// Copia TODAS as tabelas e dados do blog.db (SQLite local) para o banco Turso.
//
// Uso:
//   DATABASE_URL=libsql://seu-banco.turso.io DATABASE_AUTH_TOKEN=seu_token \
//   npx tsx scripts/migrate-sqlite-to-turso.ts
//
// Requisitos:
//   1. Banco Turso criado (turso db create dezafiraclube)
//   2. URL + token no ambiente (ou no .env)
// ============================================================================
import { createClient } from '@libsql/client';
import Database from 'better-sqlite3';
import * as dotenv from 'dotenv';
import path from 'path';
import { fileURLToPath } from 'url';

dotenv.config();

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const LOCAL_DB = process.env.DATABASE_PATH || path.join(__dirname, '..', 'blog.db');
const DATABASE_URL = process.env.DATABASE_URL;
const DATABASE_AUTH_TOKEN = process.env.DATABASE_AUTH_TOKEN;

if (!DATABASE_URL) {
  console.error('❌ DATABASE_URL não definido (ex.: libsql://seu-banco.turso.io)');
  process.exit(1);
}

async function main() {
  console.log(`🔄 Migrando: ${LOCAL_DB} → ${DATABASE_URL}`);

  const local = new Database(LOCAL_DB, { readonly: true });
  const remote = createClient({ url: DATABASE_URL, authToken: DATABASE_AUTH_TOKEN });

  // Descobre todas as tabelas do banco local
  const tables = local.prepare(
    `SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'`
  ).all() as { name: string }[];

  console.log(`📋 Tabelas encontradas: ${tables.length}`);

  // Índices (fora dos auto-gerados pelo SQLite) — preserva performance
  const indexes = local.prepare(
    `SELECT sql FROM sqlite_master WHERE type='index' AND sql IS NOT NULL AND name NOT LIKE 'sqlite_%'`
  ).all() as { sql: string }[];
  console.log(`📋 Índices encontrados: ${indexes.length}`);

  // Triggers e views — preserva comportamento e dados derivados
  const others = local.prepare(
    `SELECT sql FROM sqlite_master WHERE type IN ('trigger','view') AND sql IS NOT NULL`
  ).all() as { sql: string }[];
  console.log(`📋 Triggers/views encontrados: ${others.length}`);

  for (const { name } of tables) {
    try {
      // 1. Cria a tabela no Turso com o mesmo schema
      const createSql = (local.prepare(
        `SELECT sql FROM sqlite_master WHERE type='table' AND name=?`
      ).get(name) as { sql: string }).sql;
      await remote.execute(createSql);
      console.log(`✅ Tabela criada: ${name}`);

      // 2. Copia os dados
      const rows = local.prepare(`SELECT * FROM "${name}"`).all() as Record<string, unknown>[];
      if (rows.length === 0) {
        console.log(`   (vazia — sem dados para copiar)`);
        continue;
      }

      const cols = Object.keys(rows[0]);
      const placeholders = cols.map(() => '?').join(', ');
      const insertSql = `INSERT INTO "${name}" (${cols.map((c) => `"${c}"`).join(', ')}) VALUES (${placeholders})`;

      // Insere em lotes de 200 para eficiência
      for (let i = 0; i < rows.length; i += 200) {
        const batch = rows.slice(i, i + 200);
        for (const row of batch) {
          await remote.execute({
            sql: insertSql,
            args: cols.map((c) => row[c]),
          });
        }
      }
      console.log(`   ✅ ${rows.length} registros copiados`);
    } catch (e) {
      console.warn(`⚠️  Erro na tabela ${name}: ${(e as Error).message}`);
    }
  }

  // Copia índices (depois dos dados, mais rápido que por linha)
  for (const { sql } of indexes) {
    try {
      await remote.execute(sql);
    } catch (e) {
      console.warn(`⚠️  Erro ao criar índice: ${(e as Error).message}`);
    }
  }

  // Copia triggers e views
  for (const { sql } of others) {
    try {
      await remote.execute(sql);
    } catch (e) {
      console.warn(`⚠️  Erro ao criar trigger/view: ${(e as Error).message}`);
    }
  }

  console.log('🎉 Migração concluída! Verifique o banco Turso.');
  local.close();
}

main().catch((e) => {
  console.error('Erro fatal:', e);
  process.exit(1);
});
