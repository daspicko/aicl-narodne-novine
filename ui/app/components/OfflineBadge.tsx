export default function OfflineBadge() {
  return (
    <span className="inline-flex items-center gap-1.5 text-xs font-medium px-2.5 py-1
                     rounded-full bg-red-50
                     text-red-700
                     border border-red-200">
      <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />
      Offline — dostupna je samo osnovna pretraga
    </span>
  );
}
