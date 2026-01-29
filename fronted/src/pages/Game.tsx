import { useEffect, useState } from "react";
import { connectWS, sendConfig } from "../ws/socket";
import { RoundTable } from "../components/Table/RoundTable";
import { ChatPanel } from "../components/Chat/ChatPanel";
import { PhaseBanner } from "../components/Phase/PhaseBanner";
import { VotePanel } from "../components/Action/VotePanel";
import { VoteResultPanel } from "../components/Action/VoteResultPanel";
import { NightOverlay } from "../components/Phase/NightOverlay";
import { ReplayControls } from "../components/Replay/ReplayControls";
import { ReplayEngine } from "../components/Replay/ReplayEngine";
import { ReviewPanel } from "../components/Replay/ReviewPanel";

export function Game() {
  const [configured, setConfigured] = useState(false);
  const [playerCount, setPlayerCount] = useState(5);

  useEffect(() => {
    connectWS();
  }, []);

  return (
    <div className="game-shell w-screen h-screen text-white flex">
      {!configured && (
        <div className="absolute inset-0 z-30 flex items-center justify-center bg-black/70 backdrop-blur">
          <div className="w-[360px] rounded-2xl border border-white/10 bg-[#0f1b24] p-6 shadow-[0_30px_80px_rgba(0,0,0,0.6)]">
            <div className="text-xs uppercase tracking-[0.35em] text-emerald-200/70 mb-2 text-center">
              {"\u6e38\u620f\u8bbe\u7f6e"}
            </div>
            <div className="text-xl font-semibold text-center mb-4">
              {"\u9009\u62e9\u73a9\u5bb6\u4eba\u6570"}
            </div>
            <div className="flex items-center justify-between gap-3 mb-6">
              <button
                className="px-3 py-2 rounded-lg bg-white/10 hover:bg-white/20"
                onClick={() => setPlayerCount((c) => Math.max(5, c - 1))}
              >
                -
              </button>
              <div className="text-2xl font-semibold">
                {playerCount}{" \u4eba"}
              </div>
              <button
                className="px-3 py-2 rounded-lg bg-white/10 hover:bg-white/20"
                onClick={() => setPlayerCount((c) => Math.min(12, c + 1))}
              >
                +
              </button>
            </div>
            <button
              className="w-full rounded-lg bg-emerald-500 text-black py-2 font-semibold"
              onClick={() => {
                sendConfig(playerCount);
                setConfigured(true);
              }}
            >
              {"\u5f00\u59cb\u6e38\u620f"}
            </button>
            <div className="mt-3 text-xs text-slate-300/70 text-center">
              {"\u6700\u5c11 5 \u4eba"}
            </div>
          </div>
        </div>
      )}
      <div className="flex-1 relative px-6 py-6">
        <PhaseBanner />
        <RoundTable />
        <VotePanel />
        <VoteResultPanel />
        <NightOverlay />
        <ReplayEngine />
        <ReplayControls />
        <ReviewPanel />
      </div>
      <ChatPanel />
    </div>
  );
}
