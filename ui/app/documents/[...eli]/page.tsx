import { readFileSync } from 'fs';
import { join } from 'path';
import { notFound } from 'next/navigation';
import Link from 'next/link';
import type { DocumentFull, SearchIndexEntry, SearchIndexManifest } from '@/lib/types';
import { paramsToEli } from '@/lib/eli-utils';
import SummaryBlock from '../../components/SummaryBlock';
import KeyInfoPanel from '../../components/KeyInfoPanel';
import SegmentList from '../../components/SegmentList';

// ── Static params generation ──────────────────────────────────────────────────

export function generateStaticParams(): { eli: string[] }[] {
  try {
    const manifestPath = join(process.cwd(), 'public', 'search-index-manifest.json');
    const manifest: SearchIndexManifest = JSON.parse(readFileSync(manifestPath, 'utf-8'));
    const indexPath = join(process.cwd(), 'public', manifest.file);
    const index: SearchIndexEntry[] = JSON.parse(readFileSync(indexPath, 'utf-8'));

    return index.map(entry => ({
      // eli field is "/eli/sluzbeni/1990/10/125"
      // → strip leading slash → split by "/" → ["eli","sluzbeni","1990","10","125"]
      eli: entry.eli.replace(/^\//, '').split('/'),
    }));
  } catch {
    return [];
  }
}

// ── Load document data at build time ─────────────────────────────────────────

function loadDocument(eli: string): DocumentFull | null {
  try {
    // eli = "/eli/sluzbeni/1990/10/125"
    // file at  public/data/eli/sluzbeni/1990/10/125.json
    const filePath = join(process.cwd(), 'public', 'data', eli.replace(/^\//, '') + '.json');
    return JSON.parse(readFileSync(filePath, 'utf-8')) as DocumentFull;
  } catch {
    return null;
  }
}

// ── Page ──────────────────────────────────────────────────────────────────────

interface Props {
  params: Promise<{ eli: string[] }>;
}

export default async function DocumentPage({ params }: Props) {
  const { eli: eliParts } = await params;
  const eli = paramsToEli(eliParts);   // "/eli/sluzbeni/1990/10/125"
  const doc = loadDocument(eli);

  if (!doc) notFound();

  const hasSummaries = doc.summaries && (
    doc.summaries.short || doc.summaries.detailed || doc.summaries.structured
  );
  const hasKeyInfo = doc.key_information && (
    (doc.key_information.responsible_bodies?.length ?? 0) > 0 ||
    (doc.key_information.subjects?.length ?? 0) > 0 ||
    (doc.key_information.obligations?.length ?? 0) > 0 ||
    (doc.key_information.deadlines?.length ?? 0) > 0
  );

  return (
    <main className="mx-auto max-w-4xl px-4 sm:px-6 py-10 space-y-10">

      {/* ── Metadata header ─────────────────────────────────────────────── */}
      <header className="space-y-3">
        <div className="flex flex-wrap gap-2 items-center">
          {doc.vrsta && (
            <span className="text-xs font-medium px-2 py-0.5 rounded-full
                             bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300">
              {doc.vrsta}
            </span>
          )}
          {doc.izdanje && (
            <span className="text-xs text-zinc-500 dark:text-zinc-400">{doc.izdanje}</span>
          )}
          {doc.datum && (
            <span className="text-xs text-zinc-400 dark:text-zinc-500">{doc.datum}</span>
          )}
          {doc.donositelj && (
            <span className="text-xs text-zinc-500 dark:text-zinc-400 italic">{doc.donositelj}</span>
          )}
        </div>

        <h1 className="text-2xl sm:text-3xl font-bold text-zinc-900 dark:text-zinc-50 leading-snug">
          {doc.naslov}
        </h1>

        <div className="flex flex-wrap gap-4 items-center text-xs text-zinc-400 dark:text-zinc-500">
          <span className="font-mono">{doc.eli}</span>
          {doc.eliUrl && (
            <a
              href={doc.eliUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 dark:text-blue-400 hover:underline"
            >
              Izvor (Narodne novine) ↗
            </a>
          )}
        </div>
      </header>

      {/* ── Summaries (top) ─────────────────────────────────────────────── */}
      {hasSummaries && <SummaryBlock summaries={doc.summaries!} />}

      {/* ── Key information ─────────────────────────────────────────────── */}
      {hasKeyInfo && <KeyInfoPanel ki={doc.key_information!} />}

      {/* ── Segments / articles ─────────────────────────────────────────── */}
      {doc.doc_segmented && doc.doc_segmented.length > 0 && (
        <SegmentList segments={doc.doc_segmented} />
      )}

      {/* ── Full text (bottom) ──────────────────────────────────────────── */}
      {doc.doc_cleaned && (
        <section>
          <h2 className="text-xs font-semibold uppercase tracking-wider text-zinc-500
                         dark:text-zinc-400 mb-3">
            Puni tekst
          </h2>
          <div className="rounded-xl border border-zinc-200 dark:border-zinc-700
                          bg-white dark:bg-zinc-900 p-6">
            <p className="text-sm text-zinc-700 dark:text-zinc-300 leading-relaxed whitespace-pre-wrap">
              {doc.doc_cleaned}
            </p>
          </div>
        </section>
      )}

      {/* ── Back link ───────────────────────────────────────────────────── */}
      <div>
        <Link
          href="/search"
          className="text-sm text-blue-600 dark:text-blue-400 hover:underline"
        >
          ← Natrag na pretraživanje
        </Link>
      </div>

    </main>
  );
}
