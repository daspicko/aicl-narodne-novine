import Link from 'next/link';
import { eliToPagePath } from '@/lib/eli-utils';
import type { SearchResultCard } from '@/lib/types';

export default function ResultCard({ result }: { result: SearchResultCard }) {
  const href = eliToPagePath(result.eli);


  return (
    <Link
      href={href}
      className="block rounded-lg border border-zinc-200
                 bg-white p-5 hover:border-blue-300 hover:shadow-md transition-all"
    >
      {/* Header row */}
      <div className="flex flex-wrap items-center gap-2 mb-1">
        {result.vrsta && (
          <span className="text-xs font-medium px-2 py-0.5 rounded-full
                           bg-blue-50 text-blue-600">
            {result.vrsta}
          </span>
        )}
        {result.izdanje && (
          <span className="text-xs text-zinc-500">
            {result.izdanje}
          </span>
        )}
        {result.datum && (
          <span className="text-xs text-zinc-400 ml-auto">
            {result.datum}
          </span>
        )}
      </div>

      {/* Title */}
      <h2 className="text-base font-semibold text-zinc-700 leading-snug mb-2">
        {result.naslov}
      </h2>

      {/* Short summary */}
      {result.short_summary && (
        <p className="text-sm text-zinc-500 line-clamp-3 mb-3">
          {result.short_summary}
        </p>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between mt-2">
        <span className="text-xs text-zinc-400 font-mono truncate max-w-[60%]">
          {result.eli}
        </span>
        {result.match_type && result.match_type !== 'fallback' && (
          <span className="text-xs text-zinc-400 italic">
            {result.match_type}
          </span>
        )}
      </div>
    </Link>
  );
}
