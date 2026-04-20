// ── Slim search index entry (loaded from search-index.<hash>.json) ──────────

export interface SearchIndexEntry {
  eli: string;
  izdanje: string | null;
  naslov: string;
  vrsta: string | null;
  datum: string | null;
  donositelj: string | null;
  brojDokumenta: string | null;
  short_summary: string | null;
}

// ── Manifest (search-index-manifest.json) ───────────────────────────────────

export interface SearchIndexManifest {
  file: string;
  hash: string;
  count: number;
  generatedAt: string;
}

// ── Full document (public/data/eli/…json) ───────────────────────────────────

export interface Segment {
  članak: string;
  stavci: Array<{
    stavak: string | null;
    točke: string[];
  }>;
}

export interface StructuredSummary {
  što_zakon_uređuje: string;
  na_koga_se_odnosi: string;
  što_uvodi_ili_mijenja: string;
}

export interface Summaries {
  short: string | null;
  detailed: string | null;
  structured: StructuredSummary | null;
}

export interface KeyInformation {
  responsible_bodies: string[];
  obligations: string[];
  deadlines: string[];
  scope: string[];
  subjects: string[];
  sanctions: string[];
}

export interface DocumentFull {
  eli: string;
  eliUrl: string | null;
  izdanje: string | null;
  izdanjeUrl: string | null;
  brojDokumenta: string | null;
  dio: string | null;
  vrsta: string | null;
  donositelj: string | null;
  datum: string | null;
  naslov: string;
  opis: string | null;
  doc_cleaned: string | null;
  doc_segmented: Segment[];
  summaries: Summaries | null;
  key_information: KeyInformation | null;
}

// ── Search result card (displayed in the search results list) ────────────────

export interface SearchResultCard extends SearchIndexEntry {
  highlights?: string[];
  match_score?: number | null;
  match_type?: 'lexical' | 'semantic' | 'hybrid' | 'fallback';
}

// ── Filters ──────────────────────────────────────────────────────────────────

export interface SearchFilters {
  vrsta?: string;
  izdanje?: string;
}
