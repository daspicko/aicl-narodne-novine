'use client';

import { useState } from 'react';
import type { Segment } from '@/lib/types';

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

  return (
    <section>
      <h2 className="text-xs font-semibold uppercase tracking-wider text-zinc-500
                     dark:text-zinc-400 mb-3">
        Članci ({segments.length})
      </h2>
      <div className="space-y-1">
        {segments.map((seg, i) => {
          const isOpen = expanded.has(i);
          const preview = seg.stavci[0]?.točke[0];
          return (
            <div
              key={i}
              className="rounded-lg border border-zinc-200 dark:border-zinc-700
                         bg-white dark:bg-zinc-900 overflow-hidden"
            >
              <button
                onClick={() => toggle(i)}
                className="w-full flex items-center justify-between px-4 py-2.5
                           text-left text-sm font-medium text-zinc-800 dark:text-zinc-200
                           hover:bg-zinc-50 dark:hover:bg-zinc-800 transition-colors"
              >
                <span>{seg.članak}</span>
                <span className={`text-zinc-400 transition-transform ${isOpen ? 'rotate-180' : ''}`}>
                  ▾
                </span>
              </button>

              {!isOpen && preview && (
                <p className="px-4 pb-2.5 text-xs text-zinc-500 dark:text-zinc-400 line-clamp-1">
                  {preview}
                </p>
              )}

              {isOpen && (
                <div className="px-4 pb-4 space-y-2">
                  {seg.stavci.map((stavak, si) =>
                    stavak.točke.map((točka, ti) => (
                      <p
                        key={`${si}-${ti}`}
                        className="text-sm text-zinc-700 dark:text-zinc-300 leading-relaxed"
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
