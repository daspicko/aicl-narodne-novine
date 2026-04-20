'use client';

import { useRouter } from 'next/navigation';
import { useRef, useState } from 'react';

export default function SearchBar({
  initialQuery = '',
  autoFocus = false,
}: {
  initialQuery?: string;
  autoFocus?: boolean;
}) {
  const router = useRouter();
  const [query, setQuery] = useState(initialQuery);
  const inputRef = useRef<HTMLInputElement | null>(null);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const q = query.trim();
    if (!q) return;
    router.push(`/search?q=${encodeURIComponent(q)}`);
  }

  return (
    <form onSubmit={handleSubmit} className="w-full flex gap-2">
      <input
        ref={inputRef}
        type="search"
        value={query}
        onChange={e => setQuery(e.target.value)}
        placeholder="Pretražite zakone, uredbe, odluke…"
        autoFocus={autoFocus}
        className="flex-1 rounded-xl border border-zinc-300 dark:border-zinc-700
                   bg-white dark:bg-zinc-900 px-4 py-3 text-base text-zinc-900
                   dark:text-zinc-50 placeholder:text-zinc-400
                   focus:outline-none focus:ring-2 focus:ring-blue-500"
      />
      <button
        type="submit"
        className="rounded-xl bg-blue-600 hover:bg-blue-700 px-5 py-3 text-sm
                   font-semibold text-white transition-colors whitespace-nowrap"
      >
        Pretraži
      </button>
    </form>
  );
}
