import { useGameStore } from "../../store/gameStore";

export function PhaseBanner() {
  const phase = useGameStore((s) => s.phase);

  return (
    <div className="absolute top-6 left-1/2 -translate-x-1/2 px-8 py-3 rounded-full bg-black/50 border border-white/10 shadow-[0_10px_40px_rgba(0,0,0,0.45)] backdrop-blur">
      <div className="text-xs uppercase tracking-[0.35em] text-amber-200/70 text-center">
        Phase
      </div>
      <div className="text-lg text-center">
        {phase === "NIGHT" && "Night phase"}
        {phase === "DAY" && "Day discussion"}
        {phase === "VOTE" && "Voting phase"}
      </div>
    </div>
  );
}
