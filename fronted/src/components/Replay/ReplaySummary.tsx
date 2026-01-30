import { useMemo } from "react";
import { useGameStore } from "../../store/gameStore";

function formatEvent(event: any): string {
  if (!event || !event.type) return "";
  switch (event.type) {
    case "PHASE":
      return `\u9636\u6bb5\u5207\u6362\uff1a${event.phase}`;
    case "SPEECH":
      return `${event.playerId}: ${event.text}`;
    case "DEATH":
      return `\u51fa\u5c40\uff1a${event.playerId}`;
    case "VOTE":
      return `\u6295\u7968\uff1a${event.from} -> ${event.to}`;
    case "VOTE_END":
      return "\u6295\u7968\u7ed3\u675f";
    case "SHERIFF":
      return `\u8b66\u957f\u5f53\u9009\uff1a${event.playerId}`;
    case "SHERIFF_TIE":
      return "\u8b66\u957f\u5e73\u7968";
    case "SHERIFF_NONE":
      return "\u672c\u8f6e\u65e0\u8b66\u957f";
    case "THINKING":
      return `${event.playerId} \u601d\u8003\u4e2d`;
    case "SPEECH_START":
      return `${event.playerId} \u5f00\u59cb\u53d1\u8a00`;
    default:
      return event.type;
  }
}

export function ReplaySummary() {
  const replaying = useGameStore((s) => s.replaying);
  const timeline = useGameStore((s) => s.replayTimeline);
  const finalRoles = useGameStore((s) => s.finalRoles);
  const result = useGameStore((s) => s.result);

  const timelineText = useMemo(() => {
    if (!timeline) return [];
    return timeline.map((item) => ({
      tick: item.tick,
      text: formatEvent(item.event),
    }));
  }, [timeline]);

  if (!replaying || (!finalRoles && !timeline)) return null;

  return (
    <div className="absolute left-6 top-6 z-30 w-[420px] max-h-[80vh] overflow-auto rounded-2xl border border-white/10 bg-black/50 p-5 shadow-[0_20px_60px_rgba(0,0,0,0.45)] backdrop-blur">
      <div className="text-sm uppercase tracking-[0.3em] text-amber-200/70 mb-3">
        {"\u56de\u653e\u603b\u89c8"}
      </div>

      {result && (
        <div className="mb-4">
          <div className="text-base text-emerald-200/80 mb-2">
            {"\u6e38\u620f\u7ed3\u679c"}
          </div>
          <div className="text-base text-white/85">
            {result === "VILLAGERS_WIN"
              ? "\u597d\u4eba\u80dc\u5229"
              : result === "WEREWOLVES_WIN"
                ? "\u72fc\u4eba\u80dc\u5229"
                : "\u5e73\u5c40"}
          </div>
        </div>
      )}

      {finalRoles && (
        <div className="mb-4">
          <div className="text-base text-emerald-200/80 mb-2">
            {"\u8eab\u4efd\u516c\u5e03"}
          </div>
          <div className="space-y-1 text-base text-white/85">
            {finalRoles.map((p) => (
              <div key={p.id}>
                {p.id} - {p.role}
              </div>
            ))}
          </div>
        </div>
      )}

      {timelineText.length > 0 && (
        <div>
          <div className="text-base text-emerald-200/80 mb-2">
            {"\u6d41\u7a0b\u65f6\u95f4\u7ebf"}
          </div>
          <div className="space-y-1 text-sm text-white/75">
            {timelineText.map((item) => (
              <div key={item.tick}>
                [{item.tick}] {item.text}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
