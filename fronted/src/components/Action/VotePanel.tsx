import { useGameStore } from "../../store/gameStore";
import { sendVote } from "../../ws/socket";

export function VotePanel() {
  const phase = useGameStore((s) => s.phase);
  const votingOpen = useGameStore((s) => s.votingOpen);
  const players = useGameStore((s) => s.players);
  const selfId = useGameStore((s) => s.selfId);
  const viewerMode = useGameStore((s) => s.viewerMode);
  const votes = useGameStore((s) => s.votes);

  if (phase !== "VOTE" || !selfId || !votingOpen || viewerMode !== "PLAYER") return null;

  const selected = votes[selfId];

  return (
    <div className="absolute left-6 top-20 bg-black/50 p-5 rounded-xl border border-white/10 shadow-[0_20px_60px_rgba(0,0,0,0.45)] backdrop-blur">
      <h3 className="mb-3 text-base uppercase tracking-[0.3em] text-emerald-200/80">
        {"\u6295\u7968"}
      </h3>
      <div className="text-xl font-semibold mb-3">
        {"\u6295\u51fa\u4f60\u7684\u4e00\u7968"}
      </div>
      <div className="grid grid-cols-2 gap-2">
        {players
          .filter((p) => p.alive)
          .map((p) => (
            <button
              key={p.id}
              onClick={() => sendVote(p.id)}
              className={`px-3 py-2 rounded-md text-base transition ${
                selected === p.id
                  ? "bg-emerald-500/90 text-black shadow"
                  : "bg-white/10 hover:bg-white/20"
              }`}
            >
              {p.name}
            </button>
          ))}
      </div>
    </div>
  );
}
