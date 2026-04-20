import type { KeyInformation } from '@/lib/types';

interface Section {
  label: string;
  items: string[];
  color: string;
}

export default function KeyInfoPanel({ ki }: { ki: KeyInformation }) {
  const sections: Section[] = [
    { label: 'Nadležna tijela',    items: ki.responsible_bodies, color: 'purple' },
    { label: 'Subjekti',          items: ki.subjects,           color: 'blue'   },
    { label: 'Obveze',            items: ki.obligations,        color: 'green'  },
    { label: 'Rokovi',            items: ki.deadlines,          color: 'amber'  },
    { label: 'Sankcije',          items: ki.sanctions,          color: 'red'    },
    { label: 'Područje primjene', items: ki.scope,              color: 'zinc'   },
  ].filter(s => s.items && s.items.length > 0);

  if (sections.length === 0) return null;

  const colorMap: Record<string, string> = {
    purple: 'bg-purple-50 dark:bg-purple-900/20 border-purple-100 dark:border-purple-800 text-purple-700 dark:text-purple-300',
    blue:   'bg-blue-50 dark:bg-blue-900/20 border-blue-100 dark:border-blue-800 text-blue-700 dark:text-blue-300',
    green:  'bg-green-50 dark:bg-green-900/20 border-green-100 dark:border-green-800 text-green-700 dark:text-green-300',
    amber:  'bg-amber-50 dark:bg-amber-900/20 border-amber-100 dark:border-amber-800 text-amber-700 dark:text-amber-300',
    red:    'bg-red-50 dark:bg-red-900/20 border-red-100 dark:border-red-800 text-red-700 dark:text-red-300',
    zinc:   'bg-zinc-50 dark:bg-zinc-800/50 border-zinc-200 dark:border-zinc-700 text-zinc-700 dark:text-zinc-300',
  };

  return (
    <section>
      <h2 className="text-xs font-semibold uppercase tracking-wider text-zinc-500
                     dark:text-zinc-400 mb-3">
        Ključne informacije
      </h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {sections.map(s => (
          <div
            key={s.label}
            className={`rounded-xl border p-4 ${colorMap[s.color]}`}
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
