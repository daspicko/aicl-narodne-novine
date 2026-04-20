import { readFileSync } from 'fs';
import { join } from 'path';
import Link from 'next/link';
import SearchBar from './components/SearchBar';
import ResultCard from './components/ResultCard';
import type { SearchIndexEntry, SearchIndexManifest } from '@/lib/types';

// ── Load search index at build time (server component) ──────────────────────

function loadLatestDocuments(count = 6): SearchIndexEntry[] {
  try {
    const manifestPath = join(process.cwd(), 'public', 'search-index-manifest.json');
    const manifest: SearchIndexManifest = JSON.parse(readFileSync(manifestPath, 'utf-8'));
    const indexPath = join(process.cwd(), 'public', manifest.file);
    const index: SearchIndexEntry[] = JSON.parse(readFileSync(indexPath, 'utf-8'));
    return index.slice(0, count);
  } catch {
    return [];
  }
}

const EXAMPLE_QUERIES = [
  'zakon o udruženjima',
  'registracija društvenih organizacija',
  'prestanak udruženja',
  'novčana kazna prekršaj',
];

// ── Page ─────────────────────────────────────────────────────────────────────

export default function Home() {
  const latest = loadLatestDocuments(6);

  return (
    <main className="mx-auto max-w-4xl px-4 sm:px-6 py-16 space-y-16">

        {/* Hero */}
        <section className="text-center space-y-6">
          <h1 className="text-4xl sm:text-5xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50 leading-tight">
            Inteligentno pretraživanje<br />
            <span className="text-blue-600 dark:text-blue-400">Narodnih novina</span>
          </h1>
          <p className="text-lg text-zinc-600 dark:text-zinc-400 max-w-xl mx-auto leading-relaxed">
            Pretraži zakone, uredbe i odluke semantičkim pretraživanjem.
            Svaki dokument obogaćen je automatski generiranim sažetkom i
            ključnim informacijama (obveze, rokovi, nadležna tijela).
          </p>
          <div className="max-w-xl mx-auto">
            <SearchBar autoFocus />
          </div>
        </section>

        {/* Example queries */}
        <section>
          <h2 className="text-xs font-semibold uppercase tracking-wider text-zinc-500
                         dark:text-zinc-400 mb-3 text-center">
            Primjeri upita
          </h2>
          <div className="flex flex-wrap justify-center gap-2">
            {EXAMPLE_QUERIES.map(q => (
              <Link
                key={q}
                href={`/search?q=${encodeURIComponent(q)}`}
                className="text-sm px-4 py-2 rounded-full border border-zinc-300 dark:border-zinc-700
                           bg-white dark:bg-zinc-900 text-zinc-700 dark:text-zinc-300
                           hover:border-blue-400 dark:hover:border-blue-500 hover:text-blue-600
                           dark:hover:text-blue-400 transition-colors"
              >
                {q}
              </Link>
            ))}
          </div>
        </section>

        {/* Feature pills */}
        <section className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {[
            { icon: '🔍', title: 'Hibridno pretraživanje', desc: 'Leksičko + semantičko + rerankiranje' },
            { icon: '📝', title: 'Automatski sažeci', desc: 'Kratki, detaljni i strukturirani sažetak svakog zakona' },
            { icon: '🔑', title: 'Ključne informacije', desc: 'Obveze, rokovi, nadležna tijela, sankcije' },
          ].map(f => (
            <div key={f.title} className="rounded-xl border border-zinc-200 dark:border-zinc-700
                                            bg-white dark:bg-zinc-900 p-5 text-center">
              <div className="text-3xl mb-2">{f.icon}</div>
              <h3 className="font-semibold text-zinc-900 dark:text-zinc-50 text-sm mb-1">{f.title}</h3>
              <p className="text-xs text-zinc-500 dark:text-zinc-400 leading-snug">{f.desc}</p>
            </div>
          ))}
        </section>

        {/* Latest documents */}
        {latest.length > 0 && (
          <section>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xs font-semibold uppercase tracking-wider text-zinc-500
                             dark:text-zinc-400">
                Najnoviji dokumenti
              </h2>
              <Link
                href="/search"
                className="text-xs text-blue-600 dark:text-blue-400 hover:underline"
              >
                Prikaži sve →
              </Link>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {latest.map(doc => (
                <ResultCard key={doc.eli} result={{ ...doc }} />
              ))}
            </div>
          </section>
        )}

    </main>
  );
}
