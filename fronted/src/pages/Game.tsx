import { useEffect } from "react";
import { connectWS } from "../ws/socket";
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
  useEffect(() => {
    connectWS();
  }, []);

  return (
    <div className="game-shell w-screen h-screen text-white flex">
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
