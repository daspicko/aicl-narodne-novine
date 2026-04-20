import type { Summaries } from '@/lib/types';

export default function SummaryBlock({ summaries }: { summaries: Summaries }) {
  const { short, detailed, structured } = summaries;

  return (
    <section className="space-y-6">
      {short && (
        <div className="rounded-xl bg-blue-50 dark:bg-blue-900/20 border border-blue-100
                        dark:border-blue-800 p-5">
          <h2 className="text-xs font-semibold uppercase tracking-wider text-blue-600
                         dark:text-blue-400 mb-2">
            Kratki sažetak
          </h2>
          <p className="text-sm text-zinc-800 dark:text-zinc-200 leading-relaxed">{short}</p>
        </div>
      )}

      {detailed && (
        <div className="rounded-xl bg-zinc-50 dark:bg-zinc-800/50 border border-zinc-200
                        dark:border-zinc-700 p-5">
          <h2 className="text-xs font-semibold uppercase tracking-wider text-zinc-500
                         dark:text-zinc-400 mb-2">
            Detaljni sažetak
          </h2>
          <p className="text-sm text-zinc-700 dark:text-zinc-300 leading-relaxed">{detailed}</p>
        </div>
      )}

      {structured && (
        <div className="rounded-xl bg-zinc-50 dark:bg-zinc-800/50 border border-zinc-200
                        dark:border-zinc-700 p-5 space-y-4">
          <h2 className="text-xs font-semibold uppercase tracking-wider text-zinc-500
                         dark:text-zinc-400">
            Strukturirani sažetak
          </h2>
          {structured.što_zakon_uređuje && (
            <div>
              <h3 className="text-xs font-semibold text-zinc-600 dark:text-zinc-400 mb-1">
                Što zakon uređuje
              </h3>
              <p className="text-sm text-zinc-700 dark:text-zinc-300 leading-relaxed">
                {structured.što_zakon_uređuje}
              </p>
            </div>
          )}
          {structured.na_koga_se_odnosi && (
            <div>
              <h3 className="text-xs font-semibold text-zinc-600 dark:text-zinc-400 mb-1">
                Na koga se odnosi
              </h3>
              <p className="text-sm text-zinc-700 dark:text-zinc-300 leading-relaxed">
                {structured.na_koga_se_odnosi}
              </p>
            </div>
          )}
          {structured.što_uvodi_ili_mijenja && (
            <div>
              <h3 className="text-xs font-semibold text-zinc-600 dark:text-zinc-400 mb-1">
                Što uvodi ili mijenja
              </h3>
              <p className="text-sm text-zinc-700 dark:text-zinc-300 leading-relaxed">
                {structured.što_uvodi_ili_mijenja}
              </p>
            </div>
          )}
        </div>
      )}
    </section>
  );
}
