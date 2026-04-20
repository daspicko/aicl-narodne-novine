/**
 * api-client.ts
 *
 * searchDocuments():
 *   1. Tries POST to the FastAPI backend.
 *      Backend returns SearchResultItem[] with `eli` values.
 *      FE enriches each result from the local search index.
 *   2. On network failure falls back to Fuse.js search over the
 *      bundled search index (lexical / fuzzy fallback).
 *
 * Returns { results, isOffline } so the UI can show an offline badge.
 */

import Fuse from 'fuse.js';
import { loadSearchIndex } from './search-index-loader';
import type { SearchFilters, SearchIndexEntry, SearchResultCard } from './types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? '';

// Fuse.js instance cached after first creation
let fuseInstance: Fuse<SearchIndexEntry> | null = null;

async function getFuse(): Promise<Fuse<SearchIndexEntry>> {
  if (fuseInstance) return fuseInstance;
  const index = await loadSearchIndex();
  fuseInstance = new Fuse(index, {
    keys: [
      { name: 'naslov',        weight: 0.5 },
      { name: 'eli',           weight: 0.2 },
      { name: 'izdanje',       weight: 0.15 },
      { name: 'short_summary', weight: 0.1 },
      { name: 'donositelj',    weight: 0.05 },
    ],
    threshold: 0.4,
    includeScore: true,
    includeMatches: true,
    minMatchCharLength: 2,
  });
  return fuseInstance;
}

// ── Backend search ────────────────────────────────────────────────────────────

interface BackendResult {
  eli: string;
  highlights?: string[];
  match_score?: number | null;
  match_type?: string;
}

interface BackendSearchResponse {
  results: BackendResult[];
}

async function backendSearch(
  query: string,
  filters: SearchFilters,
  signal?: AbortSignal,
): Promise<BackendResult[]> {
  const res = await fetch(`${API_BASE}/api/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query,
      search_type: 'hybrid',
      vrsta:  filters.vrsta  ?? null,
      izdanje: filters.izdanje ?? null,
      page: 1,
      page_size: 20,
    }),
    signal,
  });
  if (!res.ok) throw new Error(`Backend search failed: ${res.status}`);
  const data: BackendSearchResponse = await res.json();
  return data.results;
}

// ── Fallback (Fuse.js) search ─────────────────────────────────────────────────

function applyFilters(entry: SearchIndexEntry, filters: SearchFilters): boolean {
  if (filters.vrsta   && entry.vrsta   !== filters.vrsta)   return false;
  if (filters.izdanje && entry.izdanje !== filters.izdanje) return false;
  return true;
}

async function fallbackSearch(
  query: string,
  filters: SearchFilters,
): Promise<SearchResultCard[]> {
  const index = await loadSearchIndex();

  if (!query.trim()) {
    // No query → return latest documents filtered
    return index
      .filter(e => applyFilters(e, filters))
      .slice(0, 20)
      .map(e => ({ ...e, match_type: 'fallback' as SearchResultCard['match_type'] }));
  }

  const fuse = await getFuse();
  const results = fuse.search(query);

  return results
    .filter(r => applyFilters(r.item, filters))
    .slice(0, 20)
    .map(r => {
      const highlights = r.matches
        ?.flatMap(m => m.indices.map(([s, e]) => m.value?.slice(s, e + 1) ?? ''))
        .filter((h): h is string => Boolean(h))
        .slice(0, 3) ?? [];
      return {
        ...r.item,
        highlights,
        match_score: r.score != null ? 1 - r.score : null,
        match_type: 'fallback' as SearchResultCard['match_type'],
      };
    });
}

// ── Public API ────────────────────────────────────────────────────────────────

export interface SearchResult {
  results: SearchResultCard[];
  isOffline: boolean;
}

export async function searchDocuments(
  query: string,
  filters: SearchFilters = {},
): Promise<SearchResult> {
  // ── Try backend ───────────────────────────────────────────────────────────
  if (API_BASE) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 5000);
    try {
      const beResults = await backendSearch(query, filters, controller.signal);
      clearTimeout(timeout);

      // Enrich backend results with local index data
      const index = await loadSearchIndex();
      const byEli = new Map(index.map(e => [e.eli, e]));

      const cards: SearchResultCard[] = beResults
        .flatMap(r => {
          const entry = byEli.get(r.eli);
          if (!entry) return [];
          const card: SearchResultCard = {
            ...entry,
            highlights:  r.highlights ?? [],
            match_score: r.match_score ?? null,
            match_type:  (r.match_type ?? 'hybrid') as SearchResultCard['match_type'],
          };
          return [card];
        });

      return { results: cards, isOffline: false };
    } catch {
      clearTimeout(timeout);
      // fall through to offline path
    }
  }

  // ── Offline fallback ──────────────────────────────────────────────────────
  const results = await fallbackSearch(query, filters);
  return { results, isOffline: true };
}

// ── Autocomplete suggestions ──────────────────────────────────────────────────

export interface Suggestion {
  eli: string;
  naslov: string;
}

export async function getSuggestions(q: string): Promise<Suggestion[]> {
  if (API_BASE) {
    try {
      const res = await fetch(
        `${API_BASE}/api/search/suggest?q=${encodeURIComponent(q)}&limit=8`,
        { signal: AbortSignal.timeout(3000) },
      );
      if (res.ok) return res.json();
    } catch {
      // fall through
    }
  }

  // Fallback: search the local index
  const fuse = await getFuse();
  return fuse
    .search(q, { limit: 8 })
    .map(r => ({ eli: r.item.eli, naslov: r.item.naslov }));
}
