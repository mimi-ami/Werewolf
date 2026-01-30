import { useGameStore } from "../store/gameStore";
import { ServerMessage } from "../types/protocol";

let socket: WebSocket | undefined;
let currentMode: "PLAYER" | "OBSERVER" | undefined;
let pendingMessages: string[] = [];

function sendMessage(payload: unknown) {
  if (!socket || socket.readyState !== WebSocket.OPEN) {
    pendingMessages.push(JSON.stringify(payload));
    return;
  }
  socket.send(JSON.stringify(payload));
}

export function connectWS(mode?: "PLAYER" | "OBSERVER") {
  if (mode && currentMode && currentMode !== mode && socket) {
    try {
      socket.close();
    } catch {
      // ignore
    }
    socket = undefined;
  }
  if (socket && socket.readyState === WebSocket.OPEN) return;
  if (socket && socket.readyState === WebSocket.CONNECTING) return;
  if (socket && socket.readyState === WebSocket.CLOSING) return;
  if (socket && socket.readyState === WebSocket.CLOSED) {
    socket = undefined;
  }

  const url =
    mode === "OBSERVER"
      ? "ws://localhost:8000/ws?mode=observer"
      : "ws://localhost:8000/ws";
  socket = new WebSocket(url);
  currentMode = mode;
  socket.onopen = () => {
    if (pendingMessages.length > 0) {
      for (const msg of pendingMessages) {
        try {
          socket?.send(msg);
        } catch {
          // ignore
        }
      }
      pendingMessages = [];
    }
  };

  socket.onmessage = (event) => {
    try {
      const msg: ServerMessage = JSON.parse(event.data);
      const store = useGameStore.getState();
      store.applyServerMessage(msg);
    } catch {
      // Ignore malformed messages.
    }
  };
}

export function sendSpeech(text: string) {
  sendMessage({ type: "SPEECH", text });
}

export function sendSkipSpeech() {
  sendMessage({ type: "SPEECH_SKIP" });
}

export function sendVote(targetId: string) {
  sendMessage({ type: "VOTE", to: targetId });
}

export function sendNightAction(actionType: string, target?: string) {
  const payload: { type: "NIGHT_ACTION"; actionType: string; target?: string } = {
    type: "NIGHT_ACTION",
    actionType,
  };
  if (target) payload.target = target;
  sendMessage(payload);
}

export function sendConfig(playerCount: number) {
  sendMessage({ type: "CONFIG", playerCount });
}

export function sendConfigWithMode(playerCount: number, observer: boolean) {
  sendMessage({ type: "CONFIG", playerCount, observer });
}
