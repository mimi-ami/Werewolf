import { create } from "zustand";
import { FinalRole, GameResult, NightSkill, Phase, Player, ReplayEvent, Review, Role, ServerMessage } from "../types/protocol";

interface Message {
  playerId: string;
  text: string;
}

interface GameState {
  players: Player[];
  selfId?: string;
  viewerMode?: "PLAYER" | "OBSERVER";
  roleMap?: Record<string, Role>;
  phase: Phase;

  thinkingPlayer?: string;
  speakingPlayer?: string;

  messages: Message[];

  votes: Record<string, string>;
  voteCounts: Record<string, number>;
  votingOpen: boolean;

  role?: Role;
  nightSkill?: NightSkill;
  nightTarget?: string;
  nightActionPending: boolean;
  nightActionSubmitted: boolean;
  nightActionError?: string;

  setRole(role: Role): void;
  setNightSkill(skill?: NightSkill): void;
  setNightTarget(pid?: string): void;
  setNightActionPending(pending: boolean): void;
  setNightActionSubmitted(submitted: boolean): void;
  setNightActionError(message?: string): void;

  setPlayers(players: Player[], selfId: string): void;
  setViewerMode(mode: "PLAYER" | "OBSERVER"): void;
  setRoleMap(roles: Record<string, Role>): void;
  setPhase(phase: Phase): void;

  setThinking(playerId?: string): void;
  setSpeaking(playerId?: string): void;

  addMessage(playerId: string, text: string): void;
  markDead(playerId: string): void;

  addVote(from: string, to: string): void;
  clearVotes(): void;

  replayTimeline?: ReplayEvent[];
  finalRoles?: FinalRole[];
  result?: GameResult;
  reviews?: Record<string, Review>;
  replayIndex: number;
  replaying: boolean;

  startReplay(): void;
  stopReplay(): void;
  stepReplay(): void;
  applyServerMessage(msg: ServerMessage): void;
}

export const useGameStore = create<GameState>((set, get) => ({
  players: [],
  phase: "NIGHT",
  viewerMode: undefined,
  roleMap: undefined,
  messages: [],
  votes: {},
  voteCounts: {},
  votingOpen: false,
  replayTimeline: undefined,
  finalRoles: undefined,
  result: undefined,
  reviews: undefined,
  replayIndex: 0,
  replaying: false,
  nightActionPending: false,
  nightActionSubmitted: false,
  nightActionError: undefined,
  
  setRole: (role) => set({ role }),
  setNightSkill: (skill) => set({ nightSkill: skill }),
  setNightTarget: (pid) => set({ nightTarget: pid }),
  setNightActionPending: (pending) => set({ nightActionPending: pending }),
  setNightActionSubmitted: (submitted) => set({ nightActionSubmitted: submitted }),
  setNightActionError: (message) => set({ nightActionError: message }),

  setPlayers: (players, selfId) => set({ players, selfId }),
  setViewerMode: (mode) => set({ viewerMode: mode }),
  setRoleMap: (roles) => set({ roleMap: roles }),

  setPhase: (phase) =>
    set({ phase }),

  setThinking: (playerId) =>
    set({ thinkingPlayer: playerId }),

  setSpeaking: (playerId) =>
    set({ speakingPlayer: playerId, thinkingPlayer: undefined }),

  addMessage: (playerId, text) =>
    set((s) => {
      const cleaned =
        typeof text === "string"
          ? text.replace(/undefined/gi, "").trim()
          : text;
      return {
        messages: [...s.messages, { playerId, text: cleaned }],
        speakingPlayer: playerId,
      };
    }),

  markDead: (playerId) =>
    set((s) => ({
      players: s.players.map((p) =>
        p.id === playerId ? { ...p, alive: false } : p
      ),
    })),

  addVote: (from, to) =>
    set((s) => {
      const votes = { ...s.votes, [from]: to };
      const voteCounts = { ...s.voteCounts };
      const previous = s.votes[from];
      if (previous) {
        voteCounts[previous] = Math.max(0, (voteCounts[previous] || 1) - 1);
        if (voteCounts[previous] === 0) delete voteCounts[previous];
      }
      voteCounts[to] = (voteCounts[to] || 0) + 1;
      return { votes, voteCounts };
    }),

  clearVotes: () =>
    set({ votes: {}, voteCounts: {} }),

  startReplay: () =>
    set({
      replaying: true,
      replayIndex: 0,
      players: [],
      selfId: undefined,
      phase: "NIGHT",
      messages: [],
      votes: {},
      voteCounts: {},
      votingOpen: false,
      nightActionPending: false,
      nightActionSubmitted: false,
      nightActionError: undefined,
      thinkingPlayer: undefined,
      speakingPlayer: undefined,
      role: undefined,
      nightSkill: undefined,
      nightTarget: undefined,
    }),
  stopReplay: () => set({ replaying: false, replayIndex: 0 }),
  stepReplay: () =>
    set((s) => ({ replayIndex: s.replayIndex + 1 })),

  applyServerMessage: (msg) => {
    const store = get();
    switch (msg.type) {
      case "INIT":
        if (!get().replaying) {
          set({
            players: msg.players,
            selfId: msg.selfId,
            phase: "NIGHT",
            roleMap: undefined,
            messages: [],
            votes: {},
            voteCounts: {},
            votingOpen: false,
            nightActionPending: false,
            nightActionSubmitted: false,
            nightActionError: undefined,
            thinkingPlayer: undefined,
            speakingPlayer: undefined,
            role: undefined,
            nightSkill: undefined,
            nightTarget: undefined,
      replayTimeline: undefined,
      finalRoles: undefined,
      result: undefined,
      reviews: undefined,
          });
        } else {
          store.setPlayers(msg.players, msg.selfId);
        }
        break;
      case "PHASE":
        set((s) => ({
          phase: msg.phase,
          thinkingPlayer: undefined,
          speakingPlayer: undefined,
          nightTarget: undefined,
          nightSkill: undefined,
          nightActionPending: false,
          nightActionSubmitted: false,
          nightActionError: undefined,
          votingOpen: msg.phase === "VOTE",
          messages:
            msg.phase === "NIGHT"
              ? s.messages.filter((m) => m.playerId === "SYSTEM")
              : s.messages,
        }));
        if (msg.phase === "VOTE") store.clearVotes();
        break;
      case "THINKING":
        store.setThinking(msg.playerId);
        break;
      case "SPEECH_START":
        store.setSpeaking(msg.playerId);
        break;
      case "SPEECH":
        store.addMessage(msg.playerId, msg.text);
        store.setSpeaking(undefined);
        break;
      case "VOTE":
        store.addVote(msg.from, msg.to);
        break;
      case "VOTE_END":
        set({ votingOpen: false, speakingPlayer: undefined, thinkingPlayer: undefined });
        break;
      case "DEATH":
        store.markDead(msg.playerId);
        break;
      case "ROLE":
        store.setRole(msg.role);
        store.addMessage("SYSTEM", `\u4f60\u7684\u8eab\u4efd\uff1a${msg.role}`);
        break;
      case "ROLE_MAP":
        store.setRoleMap(msg.roles);
        break;
      case "NIGHT_SKILL": {
        const fallbackSkill =
          msg.skill ??
          (msg.role === "SEER"
            ? "CHECK"
            : msg.role === "GUARD"
              ? "GUARD"
              : msg.role === "WEREWOLF"
                ? "WEREWOLF"
                : msg.role === "WITCH"
                  ? "POISON"
                  : undefined);
        set({
          role: msg.role ?? store.role,
          nightSkill: fallbackSkill,
          nightActionPending: false,
          nightActionSubmitted: false,
          nightActionError: undefined,
        });
        break;
      }
      case "NIGHT_ACTION_ACK": {
        if (msg.summary) {
          set({ nightActionPending: false });
        }
        const ok = msg.ok ?? (msg.status ? msg.status === "ok" : undefined);
        if (ok === undefined) break;
        if (ok) {
          set({
            nightActionPending: false,
            nightActionSubmitted: true,
            nightActionError: undefined,
          });
        } else {
          set({
            nightActionPending: false,
            nightActionSubmitted: false,
            nightActionError: msg.message || "行动被拒绝",
          });
        }
        break;
      }
      case "REPLAY_DATA":
        set({
          replayTimeline: msg.timeline,
          reviews: msg.reviews,
          finalRoles: msg.finalRoles,
          result: msg.result,
        });
        store.startReplay();
        break;
      case "REVIEW":
        set({ reviews: { ...(get().reviews || {}), ...msg.data } });
        break;
    }
  },
}));
