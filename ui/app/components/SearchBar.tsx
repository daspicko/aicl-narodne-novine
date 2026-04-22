'use client';

import { useRouter } from 'next/navigation';
import { useEffect, useRef, useState } from 'react';

const DEBOUNCE_TIME = parseInt(process.env.NEXT_PUBLIC_SEARCH_DEBOUNCE_TIME ?? '300', 10);

export default function SearchBar({
  initialQuery = '',
  autoFocus = false,
  showButton = true,
  minChars = 0,
}: {
  initialQuery?: string;
  autoFocus?: boolean;
  showButton?: boolean;
  minChars?: number;
}) {
  const router = useRouter();
  const [query, setQuery] = useState(initialQuery);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    setQuery(initialQuery);
  }, [initialQuery]);

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    const value = e.target.value;
    setQuery(value);

    if (minChars > 0) {
      if (value.trim().length >= minChars) {
        if (timeoutRef.current) clearTimeout(timeoutRef.current);
        timeoutRef.current = setTimeout(() => {
          router.push(`/search?q=${encodeURIComponent(value.trim())}`);
        }, DEBOUNCE_TIME);
      } else if (value.trim().length === 0 && initialQuery) {
        if (timeoutRef.current) clearTimeout(timeoutRef.current);
        timeoutRef.current = setTimeout(() => {
          router.push('/search');
        }, DEBOUNCE_TIME);
      } else if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
        timeoutRef.current = null;
      }
    }
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const q = query.trim();
    if (!q) return;
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    router.push(`/search?q=${encodeURIComponent(q)}`);
  }

  return (
    <form onSubmit={handleSubmit} className="w-full flex gap-2 max-w-[60vw]">
      <input
        type="search"
        value={query}
        onChange={handleChange}
        placeholder="Pretražite zakone, uredbe, odluke…"
        autoFocus={autoFocus}
        className="flex-1 rounded-lg border border-zinc-300
                   bg-white px-4 py-3 text-base text-zinc-700
                   placeholder:text-zinc-400
                   focus:outline-none focus:ring-2 focus:ring-blue-400"
      />
      {showButton && (
        <button
          type="submit"
          className="rounded-lg bg-blue-500 hover:bg-blue-600 px-5 py-3 text-sm
                     font-semibold text-white transition-colors whitespace-nowrap"
        >
          Pretraži
        </button>
      )}
    </form>
  );
}