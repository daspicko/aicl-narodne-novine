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
    <main className="mx-auto max-w-[60vw] px-4 sm:px-6 py-16 space-y-16">

        {/* Hero */}
        <section className="text-center space-y-6">
          <h1 className="text-4xl sm:text-5xl font-bold tracking-tight text-zinc-700 leading-tight">
            Inteligentno pretraživanje<br />
            <span className="text-blue-500">Narodnih novina</span>
          </h1>
          <p className="text-lg text-zinc-500 max-w-xl mx-auto leading-relaxed">
            Pretraži zakone, uredbe i odluke semantičkim pretraživanjem.
            Svaki dokument obogaćen je automatski generiranim sažetkom i
            ključnim informacijama (obveze, rokovi, nadležna tijela).
          </p>
          <div className="max-w-xl mx-auto">
            <SearchBar autoFocus />
          </div>
        </section>

        {/* Feature pills */}
        <section className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {[
            { 
              icon: <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><circle cx="11" cy="11" r="8"/><path strokeLinecap="round" d="m21 21-4.35-4.35"/></svg>, 
              title: 'Hibridno pretraživanje', 
              desc: 'Leksičko + semantičko + rangiranje' 
            },
            { 
              icon: <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>, 
              title: 'Automatski sažeci', 
              desc: 'Kratki, detaljni i strukturirani sažetak svakog zakona' 
            },
            { 
              icon: <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>, 
              title: 'Ključne informacije', 
              desc: 'Obveze, rokovi, nadležna tijela, kaznene mjere' 
            },
          ].map(f => (
            <div key={f.title} className="rounded-lg border border-zinc-200
                                            bg-white p-5 text-center flex flex-col items-center">
              <div className="text-zinc-400 mb-3">{f.icon}</div>
              <h3 className="font-semibold text-zinc-600 text-sm mb-1">{f.title}</h3>
              <p className="text-xs text-zinc-400 leading-snug">{f.desc}</p>
            </div>
          ))}
        </section>

        {/* Latest documents */}
        {latest.length > 0 && (
          <section>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xs font-semibold uppercase tracking-wider text-zinc-400">
                Najnoviji dokumenti
              </h2>
              <Link
                href="/search"
                className="text-xs text-blue-500 hover:underline"
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
