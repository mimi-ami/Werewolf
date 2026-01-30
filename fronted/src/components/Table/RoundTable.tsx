import { useGameStore } from "../../store/gameStore";
import { Seat } from "./Seat";

export function RoundTable() {
  const players = useGameStore((s) => s.players);

  const radius = 245;
  const center = { x: 320, y: 320 };

  return (
    <div className="relative w-[640px] h-[640px] mx-auto rounded-full bg-[radial-gradient(circle_at_30%_25%,#4f8c7b,transparent_55%),radial-gradient(circle_at_70%_75%,#22493f,transparent_60%),#142821] border border-emerald-200/20 shadow-[0_40px_90px_rgba(0,0,0,0.6)]">
      <div className="absolute inset-5 rounded-full border border-emerald-200/20" />
      <div className="absolute inset-14 rounded-full border border-white/10" />
      <div className="absolute inset-24 rounded-full border border-emerald-200/10" />
      {players.map((p, i) => {
        const angle = (2 * Math.PI / players.length) * i - Math.PI / 2;
        return (
          <Seat
            key={p.id}
            player={p}
            x={center.x + radius * Math.cos(angle)}
            y={center.y + radius * Math.sin(angle)}
            angle={angle}
          />
        );
      })}
    </div>
  );
}
