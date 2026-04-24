/**
 * build-static-data.mjs
 * ---------------------
 * Pre-build script. Run via `npm run prebuild` (automatic before `npm run build`).
 *
 * Reads all enriched document JSONs from  data/extracted/**\/*.json
 * Writes:
 *   public/search-index.<hash>.json    – slim search index (immutable, long-cached)
 *   public/search-index-manifest.json  – pointer to current index file (short-cached)
 *   public/data/<eli-path>.json        – full document data, one file per document
 *
 * Old search-index.*.json files from previous builds are removed automatically.
 */

import { createHash } from 'node:crypto';
import { existsSync, mkdirSync, readdirSync, readFileSync, rmSync, statSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(__dirname, '../..');          // project root (narodne-novine/)
const EXTRACTED_DIR = join(ROOT, 'data', 'extracted');
const PUBLIC_DIR = resolve(__dirname, '../public');
const DATA_OUT_DIR = join(PUBLIC_DIR, 'data');

// ── helpers ──────────────────────────────────────────────────────────────────

function ensureDir(dir) {
  if (!existsSync(dir)) mkdirSync(dir, { recursive: true });
}

/** Recursively collect all .json file paths under a directory */
function collectJsonFiles(dir) {
  const results = [];
  for (const entry of readdirSync(dir)) {
    const full = join(dir, entry);
    if (statSync(full).isDirectory()) {
      results.push(...collectJsonFiles(full));
    } else if (entry.endsWith('.json')) {
      results.push(full);
    }
  }
  return results;
}

/**
 * Convert an ELI string like "/eli/sluzbeni/1990/10/125"
 * to a relative path like "eli/sluzbeni/1990/10/125"
 * (strips leading slash).
 */
function eliToRelPath(eli) {
  return eli.replace(/^\//, '');
}

// ── main ─────────────────────────────────────────────────────────────────────

// ── clean up stale public/data from previous build ──────────────────────────

if (existsSync(DATA_OUT_DIR)) {
  rmSync(DATA_OUT_DIR, { recursive: true, force: true });
  console.log('   🗑  removed stale public/data');
}

console.log('🔨 build-static-data: collecting documents from', EXTRACTED_DIR);

const allFiles = collectJsonFiles(EXTRACTED_DIR);
console.log(`   found ${allFiles.length} document files`);

const searchIndex = [];

for (const filePath of allFiles) {
  let doc;
  try {
    doc = JSON.parse(readFileSync(filePath, 'utf-8'));
  } catch (err) {
    console.warn(`   ⚠ skipping ${filePath}: ${err.message}`);
    continue;
  }

  if (!doc.eli) {
    console.warn(`   ⚠ skipping ${filePath}: missing eli field`);
    continue;
  }

  // ── write full document JSON to public/data/<eli-path>.json ──────────────
  const relPath = eliToRelPath(doc.eli);          // e.g. "eli/sluzbeni/1990/10/125"
  const outPath = join(DATA_OUT_DIR, relPath + '.json');
  ensureDir(dirname(outPath));
  writeFileSync(outPath, JSON.stringify(doc), 'utf-8');

  // ── build slim index entry ───────────────────────────────────────────────
  const shortSummary = doc.summaries?.short ?? null;
  searchIndex.push({
    eli:          doc.eli,
    izdanje:      doc.izdanje       ?? null,
    naslov:       doc.naslov        ?? '',
    vrsta:        doc.vrsta         ?? null,
    datum:        doc.datum         ?? null,
    donositelj:   doc.donositelj    ?? null,
    brojDokumenta: doc.brojDokumenta ?? null,
    short_summary: shortSummary,
  });
}

// Sort newest-first (by vydanje / datum lexicographic — works for NN YY/YYYY)
searchIndex.sort((a, b) => {
  const da = a.datum ?? '';
  const db = b.datum ?? '';
  return db.localeCompare(da);
});

console.log(`   indexed ${searchIndex.length} documents`);

// ── write fingerprinted search index ─────────────────────────────────────────

const indexJson = JSON.stringify(searchIndex);
const hash = createHash('sha256').update(indexJson).digest('hex').slice(0, 16);
const indexFileName = `search-index.${hash}.json`;
const indexOutPath = join(PUBLIC_DIR, indexFileName);

// Clean up old search-index.*.json files
for (const entry of readdirSync(PUBLIC_DIR)) {
  if (/^search-index\.[a-f0-9]+\.json$/.test(entry) && entry !== indexFileName) {
    rmSync(join(PUBLIC_DIR, entry));
    console.log(`   🗑  removed old index: ${entry}`);
  }
}

writeFileSync(indexOutPath, indexJson, 'utf-8');
console.log(`   ✅ wrote ${indexFileName}`);

// ── write manifest ────────────────────────────────────────────────────────────

const manifest = {
  file: indexFileName,
  hash,
  count: searchIndex.length,
  generatedAt: new Date().toISOString(),
};
writeFileSync(
  join(PUBLIC_DIR, 'search-index-manifest.json'),
  JSON.stringify(manifest, null, 2),
  'utf-8',
);
console.log(`   ✅ wrote search-index-manifest.json  (${manifest.count} entries, hash=${hash})`);
