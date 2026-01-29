import { Player } from "../../types/protocol";
import { PlayerAvatar } from "./PlayerAvatar";

export function Seat({
  player,
  x,
  y,
}: {
  player: Player;
  x: number;
  y: number;
}) {
  return (
    <div
      className="absolute"
      style={{ left: x, top: y, transform: "translate(-50%, -50%)" }}
    >
      <PlayerAvatar player={player} />
    </div>
  );
}
