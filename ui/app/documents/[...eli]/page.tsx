import { readFileSync } from 'fs';
import { join } from 'path';
import { notFound } from 'next/navigation';
import Link from 'next/link';
import type { DocumentFull, SearchIndexEntry, SearchIndexManifest } from '@/lib/types';
import { paramsToEli } from '@/lib/eli-utils';
import SummaryBlock from '../../components/SummaryBlock';
import KeyInfoPanel from '../../components/KeyInfoPanel';
import DocumentText from '../../components/DocumentText';

export function generateStaticParams(): { eli: string[] }[] {
  try {
    const manifestPath = join(process.cwd(), 'public', 'search-index-manifest.json');
    const manifest: SearchIndexManifest = JSON.parse(readFileSync(manifestPath, 'utf-8'));
    const indexPath = join(process.cwd(), 'public', manifest.file);
    const index: SearchIndexEntry[] = JSON.parse(readFileSync(indexPath, 'utf-8'));

    return index.map(entry => ({
      eli: entry.eli.replace(/^\//, '').split('/'),
    }));
  } catch {
    return [];
  }
}

function loadDocument(eli: string): DocumentFull | null {
  try {
    const filePath = join(process.cwd(), 'public', 'data', eli.replace(/^\//, '') + '.json');
    return JSON.parse(readFileSync(filePath, 'utf-8')) as DocumentFull;
  } catch {
    return null;
  }
}

interface Props {
  params: Promise<{ eli: string[] }>;
}

export default async function DocumentPage({ params }: Props) {
  const { eli: eliParts } = await params;
  const eli = paramsToEli(eliParts);
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
    <main className="mx-auto max-w-[60vw] px-4 sm:px-6 py-10 space-y-8">

      <header className="space-y-3">
        <div className="flex flex-wrap gap-2 items-center">
          {doc.vrsta && (
            <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-blue-50 text-blue-600">
              {doc.vrsta}
            </span>
          )}
          {doc.izdanje && (
            <span className="text-xs text-zinc-500">{doc.izdanje}</span>
          )}
          {doc.datum && (
            <span className="text-xs text-zinc-400">{doc.datum}</span>
          )}
          {doc.donositelj && (
            <span className="text-xs text-zinc-400 italic">{doc.donositelj}</span>
          )}
        </div>

        <h1 className="text-2xl sm:text-3xl font-bold text-zinc-700 leading-snug">
          {doc.naslov}
        </h1>

        <div className="flex flex-wrap gap-4 items-center text-xs text-zinc-400">
          <span className="font-mono">{doc.eli}</span>
          {doc.eliUrl && (
            <a
              href={doc.eliUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-500 hover:underline"
            >
              Izvor (Narodne novine) ↗
            </a>
          )}
        </div>
      </header>

      {hasSummaries && <SummaryBlock summaries={doc.summaries!} />}

      {hasKeyInfo && <KeyInfoPanel ki={doc.key_information!} />}

      <DocumentText segments={doc.doc_segmented} fullText={doc.doc_cleaned ?? undefined} />

      <div>
        <Link
          href="/search"
          className="text-sm text-blue-500 hover:underline"
        >
          ← Natrag na pretraživanje
        </Link>
      </div>

    </main>
  );
}
