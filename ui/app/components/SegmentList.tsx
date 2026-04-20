'use client';

import { useState } from 'react';

interface SegmentStavak {
  stavak: string | null;
  točke: string[];
}

interface SegmentClanak {
  članak: string;
  stavci: SegmentStavak[];
}

interface Segment {
  glava: string;
  članci: SegmentClanak[];
}

export default function SegmentList({ segments }: { segments: Segment[] }) {
  const [expanded, setExpanded] = useState<Set<number>>(new Set([0]));

  if (!segments || segments.length === 0) return null;

  function toggle(i: number) {
    setExpanded(prev => {
      const next = new Set(prev);
      if (next.has(i)) next.delete(i); else next.add(i);
      return next;
    });
  }

  const allClanci = segments.flatMap(ch => ch.članci);

  return (
    <section>
      <h2 className="text-xs font-semibold uppercase tracking-wider text-zinc-400 mb-3">
        Članci ({allClanci.length})
      </h2>
      <div className="space-y-1">
        {allClanci.map((clanak, i) => {
          const isOpen = expanded.has(i);
          const preview = clanak.stavci[0]?.točke[0];
          return (
            <div
              key={i}
              className="rounded-md border border-zinc-200 bg-white overflow-hidden"
            >
              <button
                onClick={() => toggle(i)}
                className="w-full flex items-center justify-between px-4 py-2.5
                           text-left text-sm font-medium text-zinc-600
                           hover:bg-zinc-50 transition-colors"
              >
                <span>{clanak.članak}</span>
                <span className={`text-zinc-400 transition-transform ${isOpen ? 'rotate-180' : ''}`}>
                  ▾
                </span>
              </button>

              {!isOpen && preview && (
                <p className="px-4 pb-2.5 text-xs text-zinc-400 line-clamp-1">
                  {preview}
                </p>
              )}

              {isOpen && (
                <div className="px-4 pb-4 space-y-2">
                  {clanak.stavci.map((stavak, si) =>
                    stavak.točke.map((točka, ti) => (
                      <p
                        key={`${si}-${ti}`}
                        className="text-sm text-zinc-600 leading-relaxed"
                      >
                        {točka}
                      </p>
                    ))
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </section>
  );
}