'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

export default function NavBar() {
  const pathname = usePathname() ?? '/';

  const isActive = (path: string) => {
    if (path === '/') return pathname === '/';
    return pathname.startsWith(path);
  };

  return (
    <header className="sticky top-0 z-40 border-b border-zinc-200
                       bg-white/90 backdrop-blur-sm">
      <div className="mx-auto max-w-[60vw] px-4 sm:px-6 h-14 flex items-center justify-between">
        <Link
          href="/"
          className="font-bold text-zinc-700 text-sm whitespace-nowrap
                     hover:text-blue-500 transition-colors"
        >
          🏛 Narodne novine
        </Link>

        <nav className="flex items-center gap-4 text-sm">
          <Link
            href="/"
            className={`transition-colors ${
              isActive('/')
                ? 'text-blue-500 font-medium'
                : 'text-zinc-500 hover:text-zinc-700'
            }`}
          >
            Početna
          </Link>
          <Link
            href="/search"
            className={`transition-colors ${
              isActive('/search')
                ? 'text-blue-500 font-medium'
                : 'text-zinc-500 hover:text-zinc-700'
            }`}
          >
            Pretraži
          </Link>
        </nav>
      </div>
    </header>
  );
}
