import { useGameStore } from "../../store/gameStore";
import { sendNightAction } from "../../ws/socket";

export function SkillPanel() {
  const role = useGameStore((s) => s.role);
  const skill = useGameStore((s) => s.nightSkill);
  const players = useGameStore((s) => s.players);
  const target = useGameStore((s) => s.nightTarget);
  const setTarget = useGameStore((s) => s.setNightTarget);
  const pending = useGameStore((s) => s.nightActionPending);
  const submitted = useGameStore((s) => s.nightActionSubmitted);
  const error = useGameStore((s) => s.nightActionError);
  const setPending = useGameStore((s) => s.setNightActionPending);
  const setSubmitted = useGameStore((s) => s.setNightActionSubmitted);
  const setError = useGameStore((s) => s.setNightActionError);

  const roleLabel: Record<string, string> = {
    SEER: "预言家",
    WITCH: "女巫",
    GUARD: "守卫",
    VILLAGER: "村民",
    WEREWOLF: "狼人",
  };
  const skillLabel: Record<string, string> = {
    CHECK: "查验",
    SAVE: "救人",
    POISON: "毒药",
    GUARD: "守护",
    WEREWOLF: "击杀",
  };

  if (!skill || !role) {
    return <div className="italic text-slate-300">等待夜间行动...</div>;
  }

  const locked = pending || submitted;

  const actionType = (() => {
    if (!role || !skill) return undefined;
    if (role === "SEER") return "SEER";
    if (role === "GUARD") return "GUARD";
    if (role === "WEREWOLF") return "WEREWOLF";
    if (role === "WITCH" && skill === "SAVE") return "WITCH_SAVE";
    if (role === "WITCH" && skill === "POISON") return "WITCH_POISON";
    return undefined;
  })();

  const requiresTarget = actionType !== "WITCH_SAVE";

  return (
    <div className="bg-black/60 p-4 rounded w-80">
      <div className="mb-1 text-xs uppercase tracking-[0.35em] text-emerald-200/70 text-center">
        夜间行动
      </div>
      <div className="mb-2 text-lg text-center">你的身份：{roleLabel[role] ?? role}</div>
      <div className="mb-3 text-center text-sm text-white/80">
        可用技能：{skillLabel[skill] ?? skill}
      </div>

      {submitted && (
        <div className="mb-3 text-center text-emerald-200 text-sm">
          已提交行动，等待中...
        </div>
      )}
      {error && !pending && !submitted && (
        <div className="mb-3 text-center text-red-300 text-sm">{error}</div>
      )}

      <div className="grid grid-cols-3 gap-2 mb-4">
        {players
          .filter((p) => p.alive)
          .map((p) => (
            <button
              key={p.id}
              onClick={() => {
                if (locked) return;
                setTarget(p.id);
                setSubmitted(false);
                setError(undefined);
              }}
              disabled={locked}
              className={`px-2 py-1 rounded text-sm transition ${
                target === p.id ? "bg-emerald-500 text-black" : "bg-white/10"
              } ${locked ? "opacity-50 cursor-not-allowed" : ""}`}
            >
              {p.name}
            </button>
          ))}
      </div>

      <button
        disabled={!actionType || locked || (requiresTarget && !target)}
        onClick={() => {
          if (!actionType || locked) return;
          if (requiresTarget && !target) return;
          setPending(true);
          setError(undefined);
          sendNightAction(actionType, requiresTarget ? target : undefined);
        }}
        className="w-full bg-emerald-500 text-black py-2 rounded disabled:opacity-50"
      >
        {pending ? "提交中..." : "确认行动"}
      </button>
    </div>
  );
}
