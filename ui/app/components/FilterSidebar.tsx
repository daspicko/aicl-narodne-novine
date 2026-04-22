'use client';

interface FilterSidebarProps {
  vrsta: string;
  onVrstaChange: (v: string) => void;
}

const VRSTE = ['', 'Zakon', 'Uredba', 'Odluka', 'Pravilnik', 'Naredba', 'Rješenje', 'Ostalo'];

export default function FilterSidebar({
  vrsta,
  onVrstaChange,
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
    </aside>
  );
}
