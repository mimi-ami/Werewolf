import { useGameStore } from "../../store/gameStore";

export function PhaseBanner() {
  const phase = useGameStore((s) => s.phase);

  return (
    <div className="absolute top-6 left-1/2 -translate-x-1/2 px-8 py-3 rounded-full bg-black/50 border border-white/10 shadow-[0_10px_40px_rgba(0,0,0,0.45)] backdrop-blur">
      <div className="text-xs uppercase tracking-[0.35em] text-amber-200/70 text-center">
        阶段
      </div>
      <div className="text-lg text-center">
        {phase === "NIGHT" && "夜晚阶段"}
        {phase === "DAY" && "白天讨论"}
        {phase === "VOTE" && "投票阶段"}
      </div>
    </div>
  );
}
