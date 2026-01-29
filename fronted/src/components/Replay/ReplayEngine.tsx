import { useEffect } from "react";
import { useGameStore } from "../../store/gameStore";

export function ReplayEngine() {
  const timeline = useGameStore((s) => s.replayTimeline);
  const index = useGameStore((s) => s.replayIndex);
  const replaying = useGameStore((s) => s.replaying);

  useEffect(() => {
    if (!replaying || !timeline) return;
    const store = useGameStore.getState();
    if (index >= timeline.length) {
      store.stopReplay();
      return;
    }

    const { event } = timeline[index];
    // Reuse the same message handling logic as live updates.
    store.applyServerMessage(event);
  }, [index, replaying, timeline]);

  return null;
}
