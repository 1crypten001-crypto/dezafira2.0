import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import pool from './pool.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

async function migrate() {
  const client = await pool.connect();
  try {
    const sql = readFileSync(join(__dirname, '../../migrations/001_initial.sql'), 'utf-8');
    await client.query(sql);
    console.log('Migração executada com sucesso!');
  } catch (err) {
    console.error('Erro na migração:', err);
    process.exit(1);
  } finally {
    client.release();
    await pool.end();
  }
}

migrate();
