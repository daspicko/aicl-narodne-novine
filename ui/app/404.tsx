import Link from 'next/link';

export default function NotFound() {
  return (
    <main className="mx-auto max-w-[60vw] px-4 sm:px-6 py-20 space-y-8">
      <div className="text-center space-y-4">
        <h1 className="text-6xl sm:text-8xl font-bold text-blue-500">
          404
        </h1>
        <h2 className="text-2xl sm:text-3xl font-bold text-zinc-600">
          Stranica nije pronađena
        </h2>
        <p className="text-lg text-zinc-500 leading-relaxed">
          Traženi dokument ili stranica ne postoji. Možda je prebrisana ili URL je promijenjen.
        </p>
      </div>

      <div className="space-y-3 text-center">
        <p className="text-sm text-zinc-400">
          Pokušajte s:
        </p>
        <div className="flex flex-wrap justify-center gap-3">
          <Link
            href="/"
            className="inline-flex items-center gap-2 rounded-md bg-blue-500 hover:bg-blue-600
                       px-4 py-2 text-sm font-semibold text-white transition-colors"
          >
            ← Početna
          </Link>
          <Link
            href="/search"
            className="inline-flex items-center gap-2 rounded-md border border-zinc-300
                       bg-white px-4 py-2 text-sm
                       font-semibold text-zinc-600 hover:bg-zinc-50 transition-colors"
          >
            🔍 Pretraživanje
          </Link>
        </div>
      </div>

      <div className="rounded-lg border border-zinc-200 bg-zinc-50 p-6 text-center text-sm">
        <p className="text-zinc-500">
          <strong>Primjena:</strong> Ako ste sigurni da bi ova stranica trebala postojati,
          <a
            href="https://github.com"
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-500 hover:underline"
          >
            {' '}prijavite grešku
          </a>
          .
        </p>
      </div>
    </main>
  );
}
