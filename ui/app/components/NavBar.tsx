import Link from 'next/link';

export default function NavBar() {
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

        <nav className="flex items-center gap-4 text-sm text-zinc-500">
          <Link href="/" className="hover:text-zinc-700 transition-colors">
            Početna
          </Link>
          <Link href="/search" className="hover:text-zinc-700 transition-colors">
            Pretraži
          </Link>
        </nav>
      </div>
    </header>
  );
}
