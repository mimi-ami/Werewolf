import { useGameStore } from "../../store/gameStore";

export function VoteResultPanel() {
  const voteCounts = useGameStore((s) => s.voteCounts);
  const phase = useGameStore((s) => s.phase);

  if (phase !== "VOTE") return null;

  return (
    <div className="absolute right-6 top-20 bg-black/45 p-4 rounded-xl border border-white/10 shadow-[0_20px_60px_rgba(0,0,0,0.45)] backdrop-blur">
      <h3 className="mb-3 text-sm uppercase tracking-[0.3em] text-amber-200/80">
        Tally
      </h3>
      <div className="space-y-2 text-sm">
        {Object.entries(voteCounts).length === 0 && (
          <div className="text-white/60">No votes yet</div>
        )}
        {Object.entries(voteCounts).map(([pid, count]) => (
          <div key={pid} className="flex items-center justify-between gap-6">
            <span className="text-white/80">{pid}</span>
            <span className="rounded-full bg-white/10 px-2 py-0.5 text-xs">
              {count}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
