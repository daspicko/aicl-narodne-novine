interface DocumentTextProps {
  segments?: Array<{
    glava?: string;
    članci: Array<{
      članak: string;
      stavci: Array<{
        stavak: string | null;
        točke: string[];
      }>;
    }>;
  }>;
  fullText?: string;
}

function parseTočke(točke: string[]): Array<{ type: string; items: string[] } | string> {
  const result: Array<{ type: string; items: string[] } | string> = [];
  let buffer: string[] = [];
  let listType = '';
  let currentList: string[] = [];
  let lastNum = 0;

  const flush = () => {
    if (buffer.length > 0) result.push(...buffer);
    if (currentList.length > 0) result.push({ type: listType, items: [...currentList] });
    buffer = [];
    currentList = [];
    listType = '';
    lastNum = 0;
  };

  for (const line of točke) {
    const trimmed = line.trim();
    const numMatch = trimmed.match(/^(\d+)\.\s*(.+)$/);
    const dashMatch = trimmed.match(/^-\s*(.+)$/);

    if (numMatch) {
      const num = parseInt(numMatch[1]);
      const isSequential = listType === 'decimal' && (num === lastNum + 1 || (lastNum === 0 && currentList.length > 0));
      if (isSequential && currentList.length > 0) {
        currentList.push(numMatch[2]);
      } else {
        flush();
        listType = 'decimal';
        currentList.push(numMatch[2]);
      }
      lastNum = num;
    } else if (dashMatch) {
      flush();
      listType = 'disc';
      currentList.push(dashMatch[1]);
      lastNum = 0;
    } else {
      if (currentList.length > 0 && (trimmed === '' || trimmed.startsWith('da ') || trimmed.match(/^[a-zäöü]/))) {
        currentList.push(trimmed);
        lastNum = 0;
      } else {
        flush();
        buffer.push(line);
      }
    }
  }
  flush();
  return result;
}

function TočkeRenderer({ točke }: { točke: string[] }) {
  const parsed = parseTočke(točke);

  return (
    <>
      {parsed.map((item, idx) => {
        if (typeof item === 'string') {
          return <p key={idx} className="mb-1">{item}</p>;
        }
        const isOrdered = item.type === 'decimal';
        return isOrdered ? (
          <ol key={idx} className="list-decimal list-inside ml-4 mb-2 space-y-1">
            {item.items.map((it, si) => (
              <li key={si} className="text-sm text-zinc-600">{it}</li>
            ))}
          </ol>
        ) : (
          <ul key={idx} className="list-disc list-inside ml-4 mb-2 space-y-1">
            {item.items.map((it, si) => (
              <li key={si} className="text-sm text-zinc-600">{it}</li>
            ))}
          </ul>
        );
      })}
    </>
  );
}

export default function DocumentText({ segments, fullText }: DocumentTextProps) {
  const hasSegments = segments && segments.length > 0 && segments.some(s => s.članci && s.članci.length > 0);

  if (hasSegments) {
    return (
      <section>
        <h2 className="text-xs font-semibold uppercase tracking-wider text-zinc-400 mb-4">
          Tekst propisa
        </h2>
        <div className="bg-white rounded-lg border border-zinc-200 p-8 space-y-6">
          {segments.map((glava, chIdx) => (
            <div key={chIdx} className="w-full">
              {glava.glava && (
                <div className="text-sm font-bold text-zinc-700 mb-6 mt-8 text-center border-b border-zinc-200 pb-2">
                  {glava.glava}
                </div>
              )}
              {glava.članci.map((clanak, clIdx) => (
                <div key={clIdx} className="w-full">
                  <div className="text-sm font-semibold text-zinc-700 mb-2 text-center">
                    {clanak.članak}
                  </div>
                  <div className="space-y-2">
                    {clanak.stavci.map((stavak, stIdx) => (
                      <div key={stIdx} className="text-sm text-zinc-600 leading-relaxed">
                        <TočkeRenderer točke={stavak.točke} />
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          ))}
        </div>
      </section>
    );
  }

  if (fullText) {
    const paragraphs = fullText.split(/(?=Član\s+\d+\.)/);
    return (
      <section>
        <h2 className="text-xs font-semibold uppercase tracking-wider text-zinc-400 mb-4">
          Tekst propisa
        </h2>
        <div className="bg-white rounded-lg border border-zinc-200 p-8 space-y-6">
          {paragraphs.map((para, idx) => {
            const isClanak = para.match(/^Član\s+\d+/);
            return (
              <div key={idx} className="w-full">
                {isClanak && (
                  <div className="text-sm font-semibold text-zinc-700 mb-2 text-center">
                    {para.match(/^Član\s+\d+\.[^. ]*/)?.[0] || para.slice(0, 30)}
                  </div>
                )}
                <p className="text-sm text-zinc-600 leading-relaxed">
                  {para}
                </p>
              </div>
            );
          })}
        </div>
      </section>
    );
  }

  return null;
}
