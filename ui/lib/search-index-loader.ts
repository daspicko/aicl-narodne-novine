/**
 * search-index-loader.ts
 *
 * Fetches the manifest (short-lived cache) to discover the current hashed
 * index filename, then fetches the actual index (immutable / long-lived cache).
 *
 * Results are cached in module scope so repeated calls are free within a
 * single browser session.
 */

import type { SearchIndexEntry, SearchIndexManifest } from './types';

let cachedIndex: SearchIndexEntry[] | null = null;
let loadPromise: Promise<SearchIndexEntry[]> | null = null;

export async function loadSearchIndex(): Promise<SearchIndexEntry[]> {
  if (cachedIndex) return cachedIndex;
  if (loadPromise) return loadPromise;

  loadPromise = (async () => {
    // 1. Fetch manifest – short cache so it is always fresh
    const manifestRes = await fetch('/search-index-manifest.json', {
      cache: 'no-store',
    });
    if (!manifestRes.ok) throw new Error('Failed to fetch search index manifest');
    const manifest: SearchIndexManifest = await manifestRes.json();

    // 2. Fetch the hashed index – immutable, browser may cache forever
    const indexRes = await fetch(`/${manifest.file}`, {
      cache: 'force-cache',
    });
    if (!indexRes.ok) throw new Error(`Failed to fetch search index: ${manifest.file}`);
    const index: SearchIndexEntry[] = await indexRes.json();

    cachedIndex = index;
    return index;
  })();

  return loadPromise;
}

/** Clears the in-memory cache (useful in tests or hot-reload scenarios). */
export function clearSearchIndexCache(): void {
  cachedIndex = null;
  loadPromise = null;
}
