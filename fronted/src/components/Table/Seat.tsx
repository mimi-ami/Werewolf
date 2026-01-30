import { Player } from "../../types/protocol";
import { PlayerAvatar } from "./PlayerAvatar";
import { useGameStore } from "../../store/gameStore";

export function Seat({
  player,
  x,
  y,
  angle,
}: {
  player: Player;
  x: number;
  y: number;
  angle: number;
}) {
  const messages = useGameStore((s) => s.messages);
  const lastMessage = [...messages]
    .reverse()
    .find((m) => m.playerId === player.id);
  const bubbleText =
    typeof lastMessage?.text === "string"
      ? lastMessage.text.replace(/undefined/gi, "").trim()
      : "";
  const offset = 115;
  const bubbleX = Math.cos(angle) * offset;
  const bubbleY = Math.sin(angle) * offset;

  return (
    <div
      className="absolute"
      style={{ left: x, top: y, transform: "translate(-50%, -50%)" }}
    >
      <div className="relative">
        <PlayerAvatar player={player} />
        {bubbleText && (
          <div
            className="speech-bubble speech-bubble--square text-sm"
            style={{
              left: "50%",
              top: "50%",
              transform: `translate(-50%, -50%) translate(${bubbleX}px, ${bubbleY}px)`,
            }}
          >
            {bubbleText}
          </div>
        )}
      </div>
    </div>
  );
}
