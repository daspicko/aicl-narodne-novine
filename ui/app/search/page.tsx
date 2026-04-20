'use client';

import { Suspense, useEffect, useRef, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { searchDocuments } from '@/lib/api-client';
import type { SearchFilters, SearchResultCard } from '@/lib/types';
import ResultCard from '../components/ResultCard';
import FilterSidebar from '../components/FilterSidebar';
import OfflineBadge from '../components/OfflineBadge';
import SearchBar from '../components/SearchBar';

// Static export compatibility
export const dynamic = 'force-static';

// ── Inner component (reads searchParams) ─────────────────────────────────────

function SearchResults() {
  const searchParams = useSearchParams();
  const router = useRouter();

  const query = searchParams.get('q') ?? '';
  const [vrsta,   setVrsta]   = useState(searchParams.get('vrsta')   ?? '');
  const [izdanje, setIzdanje] = useState(searchParams.get('izdanje') ?? '');

  const [results,   setResults]   = useState<SearchResultCard[]>([]);
  const [isOffline, setIsOffline] = useState(false);
  const [loading,   setLoading]   = useState(false);
  const [error,     setError]     = useState<string | null>(null);
  const [searched,  setSearched]  = useState(false);

  // Track in-flight request so we can cancel on re-trigger
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    if (!query && !vrsta && !izdanje) return;

    abortRef.current?.abort();
    abortRef.current = new AbortController();

    setLoading(true);
    setError(null);

    const filters: SearchFilters = {
      ...(vrsta   ? { vrsta }   : {}),
      ...(izdanje ? { izdanje } : {}),
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
  }, [query, vrsta, izdanje]);

  // Update URL when filters change
  function handleVrstaChange(v: string) {
    setVrsta(v);
    const params = new URLSearchParams(searchParams.toString());
    if (v) params.set('vrsta', v); else params.delete('vrsta');
    router.replace(`/search?${params.toString()}`);
  }

  function handleIzdanjeChange(v: string) {
    setIzdanje(v);
    const params = new URLSearchParams(searchParams.toString());
    if (v) params.set('izdanje', v); else params.delete('izdanje');
    router.replace(`/search?${params.toString()}`);
  }

  return (
    <div className="mx-auto max-w-6xl px-4 sm:px-6 py-8 space-y-6">

      {/* Search bar */}
      <SearchBar initialQuery={query} autoFocus={!query} />

      {/* Status bar */}
      <div className="flex flex-wrap items-center gap-3 min-h-[24px]">
        {loading && (
          <span className="text-sm text-zinc-500 dark:text-zinc-400 animate-pulse">
            Pretražujem…
          </span>
        )}
        {!loading && searched && (
          <span className="text-sm text-zinc-500 dark:text-zinc-400">
            {results.length} {results.length === 1 ? 'rezultat' : 'rezultata'}
            {query ? ` za „${query}"` : ''}
          </span>
        )}
        {isOffline && <OfflineBadge />}
        {error && (
          <span className="text-sm text-red-600 dark:text-red-400">{error}</span>
        )}
      </div>

      {/* Main layout: sidebar + results */}
      <div className="flex flex-col md:flex-row gap-8">
        <FilterSidebar
          vrsta={vrsta}
          izdanje={izdanje}
          onVrstaChange={handleVrstaChange}
          onIzdanjeChange={handleIzdanjeChange}
        />

        <div className="flex-1 space-y-4">
          {!loading && searched && results.length === 0 && (
            <div className="rounded-xl border border-zinc-200 dark:border-zinc-700
                            bg-white dark:bg-zinc-900 p-10 text-center text-zinc-500
                            dark:text-zinc-400 text-sm">
              Nema rezultata za zadanu pretragu.
            </div>
          )}
          {results.map(r => (
            <ResultCard key={r.eli} result={r} />
          ))}
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
        <div className="mx-auto max-w-6xl px-4 sm:px-6 py-8 text-sm text-zinc-500">
          Učitavam…
        </div>
      }
    >
      <SearchResults />
    </Suspense>
  );
}
