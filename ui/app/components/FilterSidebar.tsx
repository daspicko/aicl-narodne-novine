'use client';

interface FilterSidebarProps {
  vrsta: string;
  izdanje: string;
  onVrstaChange: (v: string) => void;
  onIzdanjeChange: (v: string) => void;
}

const VRSTE = ['', 'Zakon', 'Uredba', 'Odluka', 'Pravilnik', 'Naredba', 'Rješenje', 'Ostalo'];

function displayNN(value: string): string {
  if (!value) return '';
  const match = value.match(/^NN\s+(\d{1,3})\/(\d{4})$/);
  if (match) {
    return `${match[1]}/${match[2]}`;
  }
  return value;
}

export default function FilterSidebar({
  vrsta,
  izdanje,
  onVrstaChange,
  onIzdanjeChange,
}: FilterSidebarProps) {
  return (
    <aside className="w-full md:w-56 shrink-0 space-y-6">
      <div>
        <h3 className="text-xs font-semibold uppercase tracking-wider text-zinc-500 mb-2">
          Vrsta dokumenta
        </h3>
        <div className="space-y-1">
          {VRSTE.map(v => (
            <button
              key={v}
              onClick={() => onVrstaChange(v)}
              className={`w-full text-left text-sm px-3 py-1.5 rounded-md transition-colors ${
                vrsta === v
                  ? 'bg-blue-500 text-white font-medium'
                  : 'text-zinc-600 hover:bg-zinc-100'
              }`}
            >
              {v || 'Sve vrste'}
            </button>
          ))}
        </div>
      </div>

      <div>
        <h3 className="text-xs font-semibold uppercase tracking-wider text-zinc-500 mb-2">
          Broj NN
        </h3>
        <input
          type="text"
          value={displayNN(izdanje)}
          onChange={e => onIzdanjeChange(e.target.value)}
          placeholder="npr. 10/1990"
          className="w-full rounded-md border border-zinc-300
                     bg-white px-3 py-2 text-sm text-zinc-600
                     placeholder:text-zinc-400
                     focus:outline-none focus:ring-2 focus:ring-blue-400"
        />
      </div>
    </aside>
  );
}
