import { useMemo } from "react";
import { useGameStore } from "../../store/gameStore";

export function PhaseBanner() {
  const phase = useGameStore((s) => s.phase);
  const role = useGameStore((s) => s.role);

  const phaseLabel = useMemo(() => {
    if (phase === "NIGHT") return "\u591c\u665a\u9636\u6bb5";
    if (phase === "DAY") return "\u767d\u5929\u8ba8\u8bba";
    if (phase === "VOTE") return "\u6295\u7968\u9636\u6bb5";
    if (phase === "SHERIFF") return "\u8b66\u957f\u8fdb\u9009";
    return "\u7ed3\u675f";
  }, [phase]);

  const roleLabel = useMemo(() => {
    if (!role) return "";
    switch (role) {
      case "SEER":
        return "\u9884\u8a00\u5bb6";
      case "WITCH":
        return "\u5973\u5deb";
      case "GUARD":
        return "\u5b88\u536b";
      case "VILLAGER":
        return "\u6751\u6c11";
      case "WEREWOLF":
        return "\u72fc\u4eba";
      default:
        return role;
    }
  }, [role]);

  return (
    <div className="absolute top-6 left-1/2 -translate-x-1/2 px-9 py-3.5 rounded-full bg-black/50 border border-white/10 shadow-[0_10px_40px_rgba(0,0,0,0.45)] backdrop-blur">
      <div className="text-sm uppercase tracking-[0.35em] text-amber-200/70 text-center">
        {"\u9636\u6bb5"}
      </div>
      <div className="text-xl text-center">{phaseLabel}</div>
      {roleLabel && (
        <div className="mt-1 text-base text-center text-emerald-200/80">
          {"\u4f60\u7684\u8eab\u4efd\uff1a"}{roleLabel}
        </div>
      )}
    </div>
  );
}
