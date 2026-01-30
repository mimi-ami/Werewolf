import { useState } from "react";
import { useGameStore } from "../../store/gameStore";
import { sendNightAction } from "../../ws/socket";

export function SkillPanel() {
  const role = useGameStore((s) => s.role);
  const skill = useGameStore((s) => s.nightSkill);
  const viewerMode = useGameStore((s) => s.viewerMode);
  const players = useGameStore((s) => s.players);
  const target = useGameStore((s) => s.nightTarget);
  const setTarget = useGameStore((s) => s.setNightTarget);
  const pending = useGameStore((s) => s.nightActionPending);
  const submitted = useGameStore((s) => s.nightActionSubmitted);
  const error = useGameStore((s) => s.nightActionError);
  const setPending = useGameStore((s) => s.setNightActionPending);
  const setSubmitted = useGameStore((s) => s.setNightActionSubmitted);
  const setError = useGameStore((s) => s.setNightActionError);
  const [witchAction, setWitchAction] = useState<"WITCH_SAVE" | "WITCH_POISON" | null>(null);

  const roleLabel: Record<string, string> = {
    SEER: "\u9884\u8a00\u5bb6",
    WITCH: "\u5973\u5deb",
    GUARD: "\u5b88\u536b",
    VILLAGER: "\u6751\u6c11",
    WEREWOLF: "\u72fc\u4eba",
  };
  const skillLabel: Record<string, string> = {
    CHECK: "\u67e5\u9a8c",
    SAVE: "\u89e3\u836f",
    POISON: "\u6bd2\u836f",
    GUARD: "\u5b88\u62a4",
    WEREWOLF: "\u51fb\u6740",
  };

  if (viewerMode === "OBSERVER") {
    return <div className="italic text-base text-slate-300">{"\u4e0a\u5e1d\u89c6\u89d2\u4e0d\u53ef\u64cd\u4f5c"}</div>;
  }

  if (!skill || !role) {
    return <div className="italic text-base text-slate-300">{"\u7b49\u5f85\u591c\u95f4\u884c\u52a8..."}</div>;
  }

  const locked = pending || submitted;

  const actionType = (() => {
    if (!role) return undefined;
    if (role === "SEER") return "SEER";
    if (role === "GUARD") return "GUARD";
    if (role === "WEREWOLF") return "WEREWOLF";
    if (role === "WITCH") return witchAction ?? undefined;
    return undefined;
  })();

  const requiresTarget = actionType !== "WITCH_SAVE";

  return (
    <div className="bg-black/60 p-5 rounded w-96">
      <div className="mb-1 text-sm uppercase tracking-[0.35em] text-emerald-200/70 text-center">
        {"\u591c\u95f4\u884c\u52a8"}
      </div>
      <div className="mb-2 text-xl text-center">
        {"\u4f60\u7684\u8eab\u4efd\uff1a"}{roleLabel[role] ?? role}
      </div>
      <div className="mb-3 text-center text-base text-white/80">
        {"\u53ef\u7528\u6280\u80fd\uff1a"}
        {role === "WITCH"
          ? `${skillLabel.SAVE}\u3001${skillLabel.POISON}`
          : skillLabel[skill] ?? skill}
      </div>

      {role === "WITCH" && (
        <div className="mb-3 flex items-center justify-center gap-2">
          <button
            type="button"
            disabled={locked}
            onClick={() => {
              setWitchAction("WITCH_SAVE");
              setTarget(undefined);
              setSubmitted(false);
              setError(undefined);
            }}
            className={`px-3 py-1 rounded text-base transition ${
              witchAction === "WITCH_SAVE"
                ? "bg-emerald-500 text-black"
                : "bg-white/10 hover:bg-white/20"
            } ${locked ? "opacity-50 cursor-not-allowed" : ""}`}
          >
            {skillLabel.SAVE}
          </button>
          <button
            type="button"
            disabled={locked}
            onClick={() => {
              setWitchAction("WITCH_POISON");
              setSubmitted(false);
              setError(undefined);
            }}
            className={`px-3 py-1 rounded text-base transition ${
              witchAction === "WITCH_POISON"
                ? "bg-emerald-500 text-black"
                : "bg-white/10 hover:bg-white/20"
            } ${locked ? "opacity-50 cursor-not-allowed" : ""}`}
          >
            {skillLabel.POISON}
          </button>
        </div>
      )}

      {submitted && (
        <div className="mb-3 text-center text-emerald-200 text-base">
          {"\u5df2\u63d0\u4ea4\u884c\u52a8\uff0c\u7b49\u5f85\u4e2d..."}
        </div>
      )}
      {error && !pending && !submitted && (
        <div className="mb-3 text-center text-red-300 text-base">{error}</div>
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
              className={`px-2 py-1 rounded text-base transition ${
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
        className="w-full bg-emerald-500 text-black py-2.5 text-base rounded disabled:opacity-50"
      >
        {pending ? "\u63d0\u4ea4\u4e2d..." : "\u786e\u8ba4\u884c\u52a8"}
      </button>
    </div>
  );
}
