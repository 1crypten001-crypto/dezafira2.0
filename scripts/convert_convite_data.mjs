#!/usr/bin/env node
/**
 * Convert 1Convite source data into canonical JSON under data/convite/.
 *
 * One-time migration helper: extracts the real daily matrix from the Express
 * backend (index.js), and dumps the arcade + kingdom trail datasets from the
 * React frontend (ESM modules). The JSON files are the repo's canonical copy
 * of the 1Convite content and feed scripts/seed_convite.py.
 *
 * Usage:
 *   node scripts/convert_convite_data.mjs [path-to-1convite-src]
 *   (default source: /tmp/1convite-src)
 */
import fs from 'fs';
import path from 'path';
import { pathToFileURL } from 'url';
import vm from 'vm';

const SRC = process.argv[2] || '/tmp/1convite-src';
const OUT_DIR = path.join(process.cwd(), 'data', 'convite');

function die(msg) {
  console.error(`[convert] ✗ ${msg}`);
  process.exit(1);
}

function writeJson(name, data) {
  fs.mkdirSync(OUT_DIR, { recursive: true });
  const file = path.join(OUT_DIR, name);
  fs.writeFileSync(file, JSON.stringify(data, null, 2), 'utf8');
  console.log(`[convert] ✓ ${name} (${(fs.statSync(file).size / 1024).toFixed(1)} KB)`);
}

/** Extract a balanced [...] block starting at `startIdx` (which points at '['). */
function extractBalanced(source, startIdx) {
  let depth = 0;
  let inStr = false;
  let strCh = '';
  for (let i = startIdx; i < source.length; i++) {
    const ch = source[i];
    if (inStr) {
      if (ch === '\\') { i++; continue; }
      if (ch === strCh) inStr = false;
      continue;
    }
    if (ch === '"' || ch === "'" || ch === '`') { inStr = true; strCh = ch; continue; }
    if (ch === '[') depth++;
    else if (ch === ']') {
      depth--;
      if (depth === 0) return source.slice(startIdx, i + 1);
    }
  }
  return null;
}

// ─────────────────────────────────────────────────────────────────────────────
// 1) Matriz diária — dias reais (1–7) embutidos no backend/src/index.js
// ─────────────────────────────────────────────────────────────────────────────
const indexJs = path.join(SRC, 'backend', 'src', 'index.js');
if (!fs.existsSync(indexJs)) die(`backend não encontrado em ${SRC}`);
const indexSrc = fs.readFileSync(indexJs, 'utf8');

const marker = 'const reais = [';
const start = indexSrc.indexOf(marker);
if (start === -1) die('marcador "const reais = [" não encontrado no index.js');
const arrayText = extractBalanced(indexSrc, start + marker.length - 1);
if (!arrayText) die('não consegui extrair o array "reais" do index.js');

let reais = [];
try {
  reais = vm.runInNewContext(`(${arrayText})`, {});
} catch (e) {
  die(`erro ao avaliar "reais": ${e.message}`);
}
if (!Array.isArray(reais) || reais.length < 7) {
  die(`esperava 7 dias reais, achei ${Array.isArray(reais) ? reais.length : 'não-array'}`);
}
writeJson('matriz_diaria_real.json', { dias: reais });

// ─────────────────────────────────────────────────────────────────────────────
// 2) Arcade Bíblico (frontend/src/data/arcadeData.js)
// ─────────────────────────────────────────────────────────────────────────────
const arcadeUrl = pathToFileURL(path.join(SRC, 'frontend', 'src', 'data', 'arcadeData.js')).href;
let arcade;
try {
  arcade = await import(arcadeUrl);
} catch (e) {
  die(`erro ao importar arcadeData.js: ${e.message}`);
}
writeJson('arcade_quiz.json', { perguntas: arcade.ARCADE_QUIZ_QUESTIONS });
writeJson('arcade_charadas.json', { perguntas: arcade.ARCADE_CHARADAS_QUESTIONS });
writeJson('arcade_forca.json', { palavras: arcade.ARCADE_FORCA_WORDS });
writeJson('arcade_caca_palavras.json', { palavras: arcade.ARCADE_CACA_PALAVRAS_LIST });

// ─────────────────────────────────────────────────────────────────────────────
// 3) Trilha do Reino (frontend/src/data/trailData.js) — planos já gerados
// ─────────────────────────────────────────────────────────────────────────────
const trailUrl = pathToFileURL(path.join(SRC, 'frontend', 'src', 'data', 'trailData.js')).href;
let trail;
try {
  trail = await import(trailUrl);
} catch (e) {
  die(`erro ao importar trailData.js: ${e.message}`);
}
writeJson('trilha_reino.json', {
  config: trail.TRAIL_CONFIG,
  acoes: trail.TRAIL_ACTIONS,
  devocionais: trail.DEVOCIONAIS,
  dias_18m: trail.TRAIL_DAYS_18M,
  dias_12m: trail.TRAIL_DAYS_12M,
});

console.log('\n[convert] Conteúdo do 1Convite convertido para JSON canônico em data/convite/.');
