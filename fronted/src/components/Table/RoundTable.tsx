import { useGameStore } from "../../store/gameStore";
import { Seat } from "./Seat";

export function RoundTable() {
  const players = useGameStore((s) => s.players);

  const radius = 220;
  const center = { x: 300, y: 300 };

  return (
    <div className="relative w-[600px] h-[600px] mx-auto mt-8 rounded-full bg-[radial-gradient(circle_at_30%_30%,#2f6e63,transparent_60%),radial-gradient(circle_at_70%_70%,#1d4a3f,transparent_55%),#1c3a2f] border border-white/15 shadow-[0_30px_80px_rgba(0,0,0,0.55)]">
      <div className="absolute inset-6 rounded-full border border-white/20" />
      <div className="absolute inset-16 rounded-full border border-white/10" />
      {players.map((p, i) => {
        const angle = (2 * Math.PI / players.length) * i - Math.PI / 2;
        return (
          <Seat
            key={p.id}
            player={p}
            x={center.x + radius * Math.cos(angle)}
            y={center.y + radius * Math.sin(angle)}
          />
        );
      })}
    </div>
  );
}
