'use client';

interface FilterSidebarProps {
  vrsta: string;
  izdanje: string;
  onVrstaChange: (v: string) => void;
  onIzdanjeChange: (v: string) => void;
}

const VRSTE = ['', 'Zakon', 'Uredba', 'Odluka', 'Pravilnik', 'Naredba', 'Rješenje', 'Ostalo'];

export default function FilterSidebar({
  vrsta,
  izdanje,
  onVrstaChange,
  onIzdanjeChange,
}: FilterSidebarProps) {
  return (
    <aside className="w-full md:w-56 shrink-0 space-y-6">
      <div>
        <h3 className="text-xs font-semibold uppercase tracking-wider text-zinc-500
                       dark:text-zinc-400 mb-2">
          Vrsta dokumenta
        </h3>
        <div className="space-y-1">
          {VRSTE.map(v => (
            <button
              key={v}
              onClick={() => onVrstaChange(v)}
              className={`w-full text-left text-sm px-3 py-1.5 rounded-lg transition-colors ${
                vrsta === v
                  ? 'bg-blue-600 text-white font-medium'
                  : 'text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-800'
              }`}
            >
              {v || 'Sve vrste'}
            </button>
          ))}
        </div>
      </div>

      <div>
        <h3 className="text-xs font-semibold uppercase tracking-wider text-zinc-500
                       dark:text-zinc-400 mb-2">
          Broj NN
        </h3>
        <input
          type="text"
          value={izdanje}
          onChange={e => onIzdanjeChange(e.target.value)}
          placeholder="npr. NN 10/1990"
          className="w-full rounded-lg border border-zinc-300 dark:border-zinc-700
                     bg-white dark:bg-zinc-900 px-3 py-2 text-sm text-zinc-900
                     dark:text-zinc-50 placeholder:text-zinc-400
                     focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>
    </aside>
  );
}
