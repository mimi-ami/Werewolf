import classNames from "classnames";
import { Player } from "../../types/protocol";
import { useGameStore } from "../../store/gameStore";

export function PlayerAvatar({ player }: { player: Player }) {
  const thinking = useGameStore((s) => s.thinkingPlayer === player.id);
  const speaking = useGameStore((s) => s.speakingPlayer === player.id);
  const votes = useGameStore((s) => s.votes);

  const votedBy = Object.entries(votes)
    .filter(([_, to]) => to === player.id)
    .map(([from]) => from);

  return (
    <div className="relative">
      <div
        className={classNames(
          "w-16 h-16 rounded-full flex items-center justify-center border-2 text-sm tracking-wide shadow-lg transition-all",
          {
            "bg-slate-600 text-slate-200 border-slate-400/60": !player.alive,
            "bg-[radial-gradient(circle_at_30%_30%,#7fd1c1,transparent_60%),#1e4b46] text-amber-50 border-amber-200/60":
              player.alive,
            "ring-4 ring-emerald-300/70 animate-pulse": thinking,
            "ring-4 ring-amber-300/80": speaking,
            "ring-0": !thinking && !speaking,
          }
        )}
      >
        {player.name}
      </div>

      {votedBy.length > 0 && (
        <div className="absolute -top-2 -right-2 bg-red-600 text-xs px-2 rounded-full shadow">
          {votedBy.length}
        </div>
      )}
    </div>
  );
}
