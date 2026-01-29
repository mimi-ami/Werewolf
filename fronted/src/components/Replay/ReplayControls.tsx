import { useGameStore } from "../../store/gameStore";

export function ReplayControls() {
  const replaying = useGameStore((s) => s.replaying);
  const stepReplay = useGameStore((s) => s.stepReplay);
  const stopReplay = useGameStore((s) => s.stopReplay);

  if (!replaying) return null;

  return (
    <div className="absolute bottom-6 right-6 bg-black/50 p-4 rounded-2xl border border-white/10 shadow-[0_20px_60px_rgba(0,0,0,0.45)] backdrop-blur">
      <div className="text-xs uppercase tracking-[0.3em] text-slate-300/80 mb-3">
        回放
      </div>
      <div className="flex gap-2">
        <button
          onClick={stepReplay}
          className="px-3 py-2 bg-white/10 rounded-md hover:bg-white/20"
        >
          下一步
        </button>
        <button
          onClick={stopReplay}
          className="px-3 py-2 bg-red-500/80 rounded-md hover:bg-red-500"
        >
          退出回放
        </button>
      </div>
    </div>
  );
}
