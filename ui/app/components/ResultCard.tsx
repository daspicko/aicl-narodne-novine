import Link from 'next/link';
import { eliToPagePath } from '@/lib/eli-utils';
import type { SearchResultCard } from '@/lib/types';

export default function ResultCard({ result }: { result: SearchResultCard }) {
  const href = eliToPagePath(result.eli);


  return (
    <Link
      href={href}
      className="block rounded-xl border border-zinc-200 dark:border-zinc-700
                 bg-white dark:bg-zinc-900 p-5 hover:border-blue-400
                 dark:hover:border-blue-500 hover:shadow-md transition-all"
    >
      {/* Header row */}
      <div className="flex flex-wrap items-center gap-2 mb-1">
        {result.vrsta && (
          <span className="text-xs font-medium px-2 py-0.5 rounded-full
                           bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300">
            {result.vrsta}
          </span>
        )}
        {result.izdanje && (
          <span className="text-xs text-zinc-500 dark:text-zinc-400">
            {result.izdanje}
          </span>
        )}
        {result.datum && (
          <span className="text-xs text-zinc-400 dark:text-zinc-500 ml-auto">
            {result.datum}
          </span>
        )}
      </div>

      {/* Title */}
      <h2 className="text-base font-semibold text-zinc-900 dark:text-zinc-50 leading-snug mb-2">
        {result.naslov}
      </h2>

      {/* Short summary */}
      {result.short_summary && (
        <p className="text-sm text-zinc-600 dark:text-zinc-400 line-clamp-3 mb-3">
          {result.short_summary}
        </p>
      )}

      {/* Highlights */}
      {result.highlights && result.highlights.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-2">
          {result.highlights.slice(0, 3).map((h, i) => (
            <span
              key={i}
              className="text-xs px-2 py-0.5 rounded bg-yellow-50 dark:bg-yellow-900/30
                         text-yellow-800 dark:text-yellow-300 border border-yellow-200
                         dark:border-yellow-700"
            >
              …{h}…
            </span>
          ))}
        </div>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between mt-2">
        <span className="text-xs text-zinc-400 dark:text-zinc-500 font-mono truncate max-w-[60%]">
          {result.eli}
        </span>
        {result.match_type && result.match_type !== 'fallback' && (
          <span className="text-xs text-zinc-400 dark:text-zinc-500 italic">
            {result.match_type}
          </span>
        )}
      </div>
    </Link>
  );
}
