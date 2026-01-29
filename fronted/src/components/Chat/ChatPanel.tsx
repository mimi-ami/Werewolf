import { useGameStore } from "../../store/gameStore";
import { sendSpeech } from "../../ws/socket";
import { useState } from "react";
import { MessageBubble } from "./MessageBubble";

export function ChatPanel() {
  const messages = useGameStore((s) => s.messages);
  const thinkingPlayer = useGameStore((s) => s.thinkingPlayer);
  const [text, setText] = useState("");
  const phase = useGameStore((s) => s.phase);

  const inputDisabled = phase !== "DAY";

  return (
    <div className="w-[320px] m-6 bg-black/45 p-4 rounded-2xl border border-white/10 shadow-[0_20px_70px_rgba(0,0,0,0.55)] flex flex-col backdrop-blur">
      <div className="mb-3 flex items-center justify-between">
        <div className="text-sm uppercase tracking-[0.35em] text-slate-300/80">
          Chat
        </div>
        <div className="text-xs text-emerald-200/70">
          {inputDisabled ? "Muted" : "Open"}
        </div>
      </div>

      <div className="flex-1 overflow-auto space-y-3 pr-1">
        {messages.map((m, i) => (
          <div key={i} className="rounded-lg bg-white/5 px-3 py-2">
            <div className="text-xs uppercase tracking-[0.2em] text-emerald-200/70">
              {m.playerId}
            </div>
            <div className="text-sm text-white/90">
              <MessageBubble text={m.text} />
            </div>
          </div>
        ))}

        {thinkingPlayer && (
          <div className="italic text-slate-300/70">
            {thinkingPlayer} is thinking...
          </div>
        )}
      </div>

      <input
        disabled={inputDisabled}
        className="mt-4 p-3 rounded-lg text-black disabled:opacity-50"
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder={
          inputDisabled ? "Chat is disabled" : "Type your message..."
        }
        onKeyDown={(e) => {
          if (e.key === "Enter" && text.trim() && !inputDisabled) {
            sendSpeech(text);
            setText("");
          }
        }}
      />
    </div>
  );
}
