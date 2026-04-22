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
    threshold: 0.7,
    distance: 100,
    includeScore: true,
    includeMatches: true,
    minMatchCharLength: 2,
    ignoreLocation: true,
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

function normalizeIzdanje(izdanje: string): string {
  if (!izdanje) return '';
  const trimmed = izdanje.trim();
  const match = trimmed.match(/^(\d{1,3})\/(\d{4})$/);
  if (match) {
    return `NN ${match[1]}/${match[2]}`;
  }
  const withPrefix = trimmed.match(/^nn\s+(\d{1,3})\/(\d{4})$/i);
  if (withPrefix) {
    return `NN ${withPrefix[1]}/${withPrefix[2]}`;
  }
  return trimmed;
}

function applyFilters(entry: SearchIndexEntry, filters: SearchFilters): boolean {
  if (filters.vrsta && entry.vrsta !== filters.vrsta) return false;
  if (filters.izdanje) {
    const normalizedFilter = normalizeIzdanje(filters.izdanje);
    const entryIzdanje = entry.izdanje || '';
    if (entryIzdanje !== normalizedFilter) return false;
  }
  return true;
}

function normalizeNNQuery(query: string): string {
  const trimmed = query.trim();
  if (!trimmed) return trimmed;
  
  const nnMatch = trimmed.match(/^(\d{1,3})\/(\d{4})$/);
  if (nnMatch) {
    return `NN ${nnMatch[1]}/${nnMatch[2]}`;
  }
  
  const nnWithPrefix = trimmed.match(/^nn\s+(\d{1,3})\/(\d{4})$/i);
  if (nnWithPrefix) {
    return `NN ${nnWithPrefix[1]}/${nnWithPrefix[2]}`;
  }
  
  return trimmed;
}

function textContainsQuery(text: string | null | undefined, query: string): boolean {
  if (!text || !query) return false;
  return text.toLowerCase().includes(query.toLowerCase());
}

async function fallbackSearch(
  query: string,
  filters: SearchFilters,
): Promise<SearchResultCard[]> {
  const index = await loadSearchIndex();
  const normalizedQuery = normalizeNNQuery(query);

  if (!normalizedQuery) {
    return index
      .filter(e => applyFilters(e, filters))
      .slice(0, 20)
      .map(e => ({ ...e, match_type: 'fallback' as SearchResultCard['match_type'] }));
  }

  const fuse = await getFuse();
  const fuseResults = fuse.search(normalizedQuery);

  const fuseMatches = new Set(
    fuseResults
      .filter(r => applyFilters(r.item, filters))
      .map(r => r.item.eli)
  );

  const directMatches = index
    .filter(e => 
      applyFilters(e, filters) &&
      !fuseMatches.has(e.eli) &&
      (textContainsQuery(e.naslov, normalizedQuery) ||
       textContainsQuery(e.short_summary, normalizedQuery))
    )
    .map(e => ({ ...e, match_score: 0.99, match_type: 'fallback' as SearchResultCard['match_type'] }));

  const fuseCards = fuseResults
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

  return [...directMatches, ...fuseCards].slice(0, 20);
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
