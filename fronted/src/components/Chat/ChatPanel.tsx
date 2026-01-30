import { useGameStore } from "../../store/gameStore";
import { sendSkipSpeech, sendSpeech } from "../../ws/socket";
import { useEffect, useMemo, useRef, useState } from "react";
import { MessageBubble } from "./MessageBubble";

export function ChatPanel() {
  const messages = useGameStore((s) => s.messages);
  const players = useGameStore((s) => s.players);
  const thinkingPlayer = useGameStore((s) => s.thinkingPlayer);
  const [text, setText] = useState("");
  const [isComposing, setIsComposing] = useState(false);
  const phase = useGameStore((s) => s.phase);
  const viewerMode = useGameStore((s) => s.viewerMode);
  const listRef = useRef<HTMLDivElement | null>(null);

  const inputDisabled = phase !== "DAY" || viewerMode !== "PLAYER";
  const nameMap = useMemo(
    () => new Map(players.map((p) => [p.id, p.name])),
    [players]
  );

  useEffect(() => {
    const el = listRef.current;
    if (!el) return;
    el.scrollTop = el.scrollHeight;
  }, [messages.length]);

  return (
    <div className="w-[360px] m-6 bg-black/45 p-5 rounded-2xl border border-white/10 shadow-[0_20px_70px_rgba(0,0,0,0.55)] flex flex-col backdrop-blur">
      <div className="mb-3 flex items-center justify-between">
        <div className="text-base uppercase tracking-[0.35em] text-slate-300/80">
          {"\u804a\u5929"}
        </div>
        <div className="text-sm text-emerald-200/70">
          {inputDisabled ? "\u7981\u8a00" : "\u5f00\u653e"}
        </div>
      </div>

      <div ref={listRef} className="flex-1 overflow-auto space-y-3 pr-1">
        {messages
          .filter((m) => m.playerId === "SYSTEM")
          .map((m, i) => {
          const cleaned =
            typeof m.text === "string"
              ? m.text.replace(/undefined/gi, "").trim()
              : m.text;
          const name = nameMap.get(m.playerId);
          const displayName =
            m.playerId === "SYSTEM"
              ? "\u7cfb\u7edf"
              : name
                ? name === m.playerId
                  ? m.playerId
                  : `${m.playerId} \u00b7 ${name}`
                : m.playerId;
          return (
            <div key={i} className="rounded-lg bg-white/5 px-3 py-2">
              <div className="text-sm uppercase tracking-[0.2em] text-emerald-200/70">
                {displayName}
              </div>
              <div className="text-base text-white/90 chat-text">
                <MessageBubble text={cleaned} instant />
              </div>
            </div>
          );
        })}

        {thinkingPlayer && (
          <div className="italic text-slate-300/70">
            {(nameMap.get(thinkingPlayer) || thinkingPlayer) + " \u6b63\u5728\u601d\u8003..."}
          </div>
        )}
      </div>

      <input
        disabled={inputDisabled}
        className="mt-4 p-3 rounded-lg text-base text-black disabled:opacity-50"
        value={text}
        onChange={(e) => setText(e.target.value)}
        onCompositionStart={() => setIsComposing(true)}
        onCompositionEnd={() => setIsComposing(false)}
        placeholder={
          inputDisabled
            ? "\u804a\u5929\u5df2\u5173\u95ed"
            : "\u8f93\u5165\u4f60\u7684\u6d88\u606f..."
        }
        onKeyDown={(e) => {
          if (
            e.key === "Enter" &&
            text.trim() &&
            !inputDisabled &&
            !isComposing &&
            !(e.nativeEvent as any).isComposing
          ) {
            sendSpeech(text);
            setText("");
          }
        }}
      />
      <button
        disabled={inputDisabled}
        className="mt-3 w-full rounded-lg bg-white/10 py-2 text-base hover:bg-white/20 disabled:opacity-50"
        onClick={() => {
          if (inputDisabled) return;
          sendSkipSpeech();
          setText("");
        }}
      >
        {"\u8df3\u8fc7\u53d1\u8a00"}
      </button>
    </div>
  );
}
