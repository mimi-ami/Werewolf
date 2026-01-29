import { useGameStore } from "../store/gameStore";
import { ServerMessage } from "../types/protocol";

let socket: WebSocket | undefined;

function sendMessage(payload: unknown) {
  if (!socket || socket.readyState !== WebSocket.OPEN) {
    return;
  }
  socket.send(JSON.stringify(payload));
}

export function connectWS() {
  if (socket && socket.readyState === WebSocket.OPEN) return;
  if (socket && socket.readyState === WebSocket.CONNECTING) return;
  if (socket && socket.readyState === WebSocket.CLOSING) return;
  if (socket && socket.readyState === WebSocket.CLOSED) {
    socket = undefined;
  }

  socket = new WebSocket("ws://localhost:8000/ws");

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
