'use client';

const LEGAL_TERMS_L1 = [
  { text: 'Zakon', size: 'text-9xl', rotate: -12, x: '5%', y: '10%' },
  { text: 'Uredba', size: 'text-8xl', rotate: 8, x: '70%', y: '5%' },
  { text: 'Odluka', size: 'text-7xl', rotate: -6, x: '20%', y: '60%' },
  { text: 'Pravilnik', size: 'text-8xl', rotate: 10, x: '75%', y: '55%' },
  { text: 'Rješenje', size: 'text-6xl', rotate: -8, x: '45%', y: '80%' },
  { text: 'Narodne novine', size: 'text-5xl', rotate: 5, x: '10%', y: '35%' },
];

const LEGAL_TERMS_L2 = [
  { text: 'Članak', size: 'text-6xl', rotate: 15, x: '60%', y: '15%' },
  { text: 'Stavak', size: 'text-5xl', rotate: -10, x: '15%', y: '70%' },
  { text: 'Točka', size: 'text-5xl', rotate: 5, x: '80%', y: '75%' },
  { text: 'Odjeljak', size: 'text-4xl', rotate: -5, x: '35%', y: '20%' },
  { text: 'Prilog', size: 'text-4xl', rotate: 12, x: '55%', y: '45%' },
  { text: 'Izmjene', size: 'text-4xl', rotate: -15, x: '5%', y: '55%' },
  { text: 'Dodatak', size: 'text-3xl', rotate: 8, x: '85%', y: '30%' },
];

const LEGAL_TERMS_L3 = [
  { text: 'Ministarstvo', size: 'text-3xl', rotate: 6, x: '30%', y: '8%' },
  { text: 'Vlada', size: 'text-3xl', rotate: -4, x: '90%', y: '50%' },
  { text: 'Sabor', size: 'text-2xl', rotate: 10, x: '25%', y: '45%' },
  { text: 'Predsjednik', size: 'text-2xl', rotate: -8, x: '65%', y: '35%' },
  { text: 'Pravilnik', size: 'text-2xl', rotate: 3, x: '50%', y: '70%' },
  { text: 'Uredba', size: 'text-2xl', rotate: -6, x: '8%', y: '25%' },
  { text: 'Zakon', size: 'text-2xl', rotate: 5, x: '75%', y: '90%' },
  { text: 'Odluka', size: 'text-xl', rotate: -3, x: '40%', y: '5%' },
  { text: 'Rješenje', size: 'text-xl', rotate: 8, x: '20%', y: '85%' },
  { text: 'Prijedlog', size: 'text-xl', rotate: -10, x: '70%', y: '65%' },
];

function DecorativeWord({ term }: { term: { text: string; size: string; rotate: number; x: string; y: string } }) {
  return (
    <span
      className={term.size}
      style={{
        transform: `rotate(${term.rotate}deg)`,
        left: term.x,
        top: term.y,
      }}
    >
      {term.text}
    </span>
  );
}

export default function Background() {
  return (
    <div className="bg-decorative" aria-hidden="true">
      {LEGAL_TERMS_L1.map((term, i) => (
        <DecorativeWord key={`l1-${i}`} term={term} />
      ))}
      {LEGAL_TERMS_L2.map((term, i) => (
        <DecorativeWord key={`l2-${i}`} term={term} />
      ))}
      {LEGAL_TERMS_L3.map((term, i) => (
        <DecorativeWord key={`l3-${i}`} term={term} />
      ))}
    </div>
  );
}