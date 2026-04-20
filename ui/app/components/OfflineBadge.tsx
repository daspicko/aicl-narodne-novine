export default function OfflineBadge() {
  return (
    <span className="inline-flex items-center gap-1.5 text-xs font-medium px-2.5 py-1
                     rounded-full bg-amber-50 dark:bg-amber-900/30
                     text-amber-700 dark:text-amber-300
                     border border-amber-200 dark:border-amber-700">
      <span className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse" />
      Offline pretraživanje — semantička pretraga nije dostupna
    </span>
  );
}
