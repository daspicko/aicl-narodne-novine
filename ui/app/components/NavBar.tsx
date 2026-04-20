import Link from 'next/link';

export default function NavBar() {
  return (
    <header className="sticky top-0 z-40 border-b border-zinc-200 dark:border-zinc-800
                       bg-white/90 dark:bg-zinc-950/90 backdrop-blur-sm">
      <div className="mx-auto max-w-6xl px-4 sm:px-6 h-14 flex items-center gap-4">
        <Link
          href="/"
          className="font-bold text-zinc-900 dark:text-zinc-50 text-sm whitespace-nowrap
                     hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
        >
          🏛 Narodne novine
        </Link>

        {/* Inline mini search bar */}
        <form
          action="/search"
          method="get"
          className="flex-1 flex gap-2 max-w-lg"
        >
          <input
            type="search"
            name="q"
            placeholder="Pretraži zakone…"
            className="flex-1 min-w-0 rounded-lg border border-zinc-300 dark:border-zinc-700
                       bg-zinc-50 dark:bg-zinc-900 px-3 py-1.5 text-sm text-zinc-900
                       dark:text-zinc-50 placeholder:text-zinc-400
                       focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            type="submit"
            className="rounded-lg bg-blue-600 hover:bg-blue-700 px-3 py-1.5 text-sm
                       font-semibold text-white transition-colors"
          >
            Traži
          </button>
        </form>

        <nav className="flex items-center gap-3 text-sm text-zinc-600 dark:text-zinc-400">
          <Link href="/" className="hover:text-zinc-900 dark:hover:text-zinc-50 transition-colors">
            Početna
          </Link>
          <Link href="/search" className="hover:text-zinc-900 dark:hover:text-zinc-50 transition-colors">
            Pretraži
          </Link>
        </nav>
      </div>
    </header>
  );
}
