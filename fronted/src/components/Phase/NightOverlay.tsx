import { useGameStore } from "../../store/gameStore";
import { SkillPanel } from "../Action/SkillPanel";

export function NightOverlay() {
  const phase = useGameStore((s) => s.phase);

  if (phase !== "NIGHT") return null;

  return (
    <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_30%,rgba(255,255,255,0.12),transparent_55%),rgba(5,10,20,0.9)] z-20 flex items-center justify-center">
      <div className="text-center text-gray-200">
        <div className="mb-4 text-2xl tracking-wide text-emerald-100">
          夜幕降临，闭上眼睛。
        </div>
        <div className="inline-block rounded-2xl border border-white/10 bg-black/40 p-4 shadow-[0_20px_60px_rgba(0,0,0,0.6)] backdrop-blur">
          <SkillPanel />
        </div>
      </div>
    </div>
  );
}
