'use client';

import { Suspense, useEffect, useRef, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { searchDocuments } from '@/lib/api-client';
import type { SearchFilters, SearchResultCard } from '@/lib/types';
import ResultCard from '../components/ResultCard';
import FilterSidebar from '../components/FilterSidebar';
import OfflineBadge from '../components/OfflineBadge';
import SearchBar from '../components/SearchBar';

const PAGE_SIZE = parseInt(process.env.NEXT_PUBLIC_SEARCH_RESULT_SIZE ?? '10', 10);

function normalizeInput(query: string): string {
  const q = query.trim();
  const nnMatch = q.match(/^(\d{1,3})\/(\d{4})$/);
  if (nnMatch) {
    return `NN ${nnMatch[1]}/${nnMatch[2]}`;
  }
  return q;
}

function SearchResults() {
  const searchParams = useSearchParams();
  const router = useRouter();

  const rawQuery = searchParams.get('q') ?? '';
  const query = normalizeInput(rawQuery);
  const [vrsta, setVrsta] = useState(searchParams.get('vrsta') ?? '');

  const [results, setResults] = useState<SearchResultCard[]>([]);
  const [isOffline, setIsOffline] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searched, setSearched] = useState(false);
  const [limit, setLimit] = useState(PAGE_SIZE);

  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    setLimit(PAGE_SIZE);
  }, [query, vrsta]);

  useEffect(() => {
    if (!query && !vrsta) return;

    abortRef.current?.abort();
    abortRef.current = new AbortController();

    setLoading(true);
    setError(null);

    const filters: SearchFilters = {
      ...(vrsta ? { vrsta } : {}),
    };

    searchDocuments(query, filters)
      .then(res => {
        setResults(res.results);
        setIsOffline(res.isOffline);
        setSearched(true);
      })
      .catch(err => {
        if (err.name !== 'AbortError') setError('Greška pri pretraživanju.');
      })
      .finally(() => setLoading(false));
  }, [query, vrsta]);

  function handleVrstaChange(v: string) {
    setVrsta(v);
    const params = new URLSearchParams(searchParams.toString());
    if (v) params.set('vrsta', v); else params.delete('vrsta');
    router.replace(`/search?${params.toString()}`);
  }

  const displayedResults = results.slice(0, limit);
  const hasMore = results.length > limit;

  return (
    <div className="mx-auto max-w-[60vw] px-4 sm:px-6 py-8 space-y-6">

      {/* Search bar */}
      <SearchBar initialQuery={query} autoFocus={!query} showButton={false} minChars={3} />

      {/* Status bar */}
      <div className="flex flex-wrap items-center gap-3 min-h-[24px]">
        {loading && (
          <span className="text-sm text-zinc-400 animate-pulse">
            Pretražujem…
          </span>
        )}
        {!loading && searched && (
          <span className="text-sm text-zinc-400">
            {results.length} {results.length === 1 ? 'rezultat' : 'rezultata'}
            {query ? ` za „${query}"` : ''}
          </span>
        )}
        {isOffline && <OfflineBadge />}
        {error && (
          <span className="text-sm text-red-500">{error}</span>
        )}
      </div>

      {/* Main layout: sidebar + results */}
      <div className="flex flex-col md:flex-row gap-8">
        <FilterSidebar
          vrsta={vrsta}
          onVrstaChange={handleVrstaChange}
        />

        <div className="flex-1 space-y-4">
          {!query && !vrsta && !searched && (
            <div className="rounded-lg border border-zinc-200
                            bg-white p-10 text-center text-zinc-400 text-sm">
              Upišite pojam za pretraživanje zakona, uredbi ili odluka.
            </div>
          )}
          {!loading && searched && results.length === 0 && (
            <div className="rounded-lg border border-zinc-200
                            bg-white p-10 text-center text-zinc-400 text-sm">
              Nema rezultata za zadanu pretragu.
            </div>
          )}
          {displayedResults.map(r => (
            <ResultCard key={r.eli} result={r} />
          ))}
          {hasMore && (
            <button
              onClick={() => setLimit(l => l + PAGE_SIZE)}
              className="text-sm text-blue-500 hover:underline"
            >
              Prikaži više
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Page export ───────────────────────────────────────────────────────────────

export default function SearchPage() {
  return (
    <Suspense
      fallback={
        <div className="mx-auto max-w-[60vw] px-4 sm:px-6 py-8 text-sm text-zinc-400">
          Učitavam…
        </div>
      }
    >
      <SearchResults />
    </Suspense>
  );
}
