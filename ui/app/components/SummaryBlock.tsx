import type { Summaries } from '@/lib/types';

export default function SummaryBlock({ summaries }: { summaries: Summaries }) {
  const { short, detailed, structured } = summaries;

  return (
    <section className="space-y-6">
      {short && (
        <div className="rounded-lg bg-blue-50 border border-blue-100 p-5">
          <h2 className="text-xs font-semibold uppercase tracking-wider text-blue-600 mb-2">
            Kratki sažetak
          </h2>
          <p className="text-sm text-zinc-600 leading-relaxed">{short}</p>
        </div>
      )}

      {detailed && (
        <div className="rounded-lg bg-zinc-50 border border-zinc-200 p-5">
          <h2 className="text-xs font-semibold uppercase tracking-wider text-zinc-500 mb-2">
            Detaljni sažetak
          </h2>
          <p className="text-sm text-zinc-600 leading-relaxed">{detailed}</p>
        </div>
      )}

      {structured && (
        <div className="rounded-lg bg-zinc-50 border border-zinc-200 p-5 space-y-4">
          <h2 className="text-xs font-semibold uppercase tracking-wider text-zinc-500">
            Strukturirani sažetak
          </h2>
          {structured.što_zakon_uređuje && (
            <div>
              <h3 className="text-xs font-semibold text-zinc-500 mb-1">
                Što zakon uređuje
              </h3>
              <p className="text-sm text-zinc-600 leading-relaxed">
                {structured.što_zakon_uređuje}
              </p>
            </div>
          )}
          {structured.na_koga_se_odnosi && (
            <div>
              <h3 className="text-xs font-semibold text-zinc-500 mb-1">
                Na koga se odnosi
              </h3>
              <p className="text-sm text-zinc-600 leading-relaxed">
                {structured.na_koga_se_odnosi}
              </p>
            </div>
          )}
          {structured.što_uvodi_ili_mijenja && (
            <div>
              <h3 className="text-xs font-semibold text-zinc-500 mb-1">
                Što uvodi ili mijenja
              </h3>
              <p className="text-sm text-zinc-600 leading-relaxed">
                {structured.što_uvodi_ili_mijenja}
              </p>
            </div>
          )}
        </div>
      )}
    </section>
  );
}