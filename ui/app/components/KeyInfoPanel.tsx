import type { KeyInformation } from '@/lib/types';

interface Section {
  label: string;
  items: string[];
  color: string;
}

export default function KeyInfoPanel({ ki }: { ki: KeyInformation }) {
  const sections: Section[] = [
    { label: 'Nadležna tijela',    items: ki.responsible_bodies, color: 'blue' },
    { label: 'Subjekti',          items: ki.subjects,           color: 'zinc'   },
    { label: 'Obveze',            items: ki.obligations,        color: 'green'  },
    { label: 'Rokovi',            items: ki.deadlines,          color: 'amber'  },
    { label: 'Sankcije',          items: ki.sanctions,          color: 'red'    },
    { label: 'Područje primjene', items: ki.scope,              color: 'zinc'   },
  ].filter(s => s.items && s.items.length > 0);

  if (sections.length === 0) return null;

  const colorMap: Record<string, string> = {
    blue:   'bg-blue-50 border-blue-100 text-blue-700',
    green:  'bg-green-50 border-green-100 text-green-700',
    amber:  'bg-amber-50 border-amber-100 text-amber-700',
    red:    'bg-red-50 border-red-100 text-red-700',
    zinc:   'bg-zinc-50 border-zinc-200 text-zinc-600',
  };

  return (
    <section>
      <h2 className="text-xs font-semibold uppercase tracking-wider text-zinc-500 mb-3">
        Ključne informacije
      </h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {sections.map(s => (
          <div
            key={s.label}
            className={`rounded-lg border p-4 ${colorMap[s.color]}`}
          >
            <h3 className="text-xs font-semibold mb-2 opacity-80">{s.label}</h3>
            <ul className="space-y-1">
              {s.items.slice(0, 5).map((item, i) => (
                <li key={i} className="text-xs leading-snug line-clamp-2">
                  • {item}
                </li>
              ))}
              {s.items.length > 5 && (
                <li className="text-xs opacity-60">
                  + {s.items.length - 5} više…
                </li>
              )}
            </ul>
          </div>
        ))}
      </div>
    </section>
  );
}
