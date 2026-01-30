import { useGameStore } from "../../store/gameStore";
import { SkillPanel } from "../Action/SkillPanel";

export function NightOverlay() {
  const phase = useGameStore((s) => s.phase);
  const viewerMode = useGameStore((s) => s.viewerMode);

  if (phase !== "NIGHT") return null;

  return (
    <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_30%,rgba(255,255,255,0.12),transparent_55%),rgba(5,10,20,0.9)] z-20 flex items-center justify-center">
      <div className="text-center text-gray-200">
        <div className="mb-4 text-3xl tracking-wide text-emerald-100">
          {"\u591c\u5e55\u964d\u4e34\uff0c\u95ed\u4e0a\u773c\u775b\u3002"}
        </div>
        <div className="inline-block rounded-2xl border border-white/10 bg-black/40 p-5 shadow-[0_20px_60px_rgba(0,0,0,0.6)] backdrop-blur">
          {viewerMode === "OBSERVER" ? (
            <div className="text-base text-slate-300">
              {"\u4f60\u6b63\u5728\u4e0a\u5e1d\u89c6\u89d2\u89c2\u770b"}
            </div>
          ) : (
            <SkillPanel />
          )}
        </div>
      </div>
    </div>
  );
}
