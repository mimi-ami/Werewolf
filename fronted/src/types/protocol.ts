export type Phase = "NIGHT" | "DAY" | "VOTE" | "ENDED";

export interface Player {
  id: string;
  name: string;
  alive: boolean;
  isSelf?: boolean;
}

export type Role = "SEER" | "WITCH" | "GUARD" | "VILLAGER" | "WEREWOLF";
export type NightSkill = "CHECK" | "SAVE" | "POISON" | "GUARD";


export interface ReplayEvent {
  tick: number;
  event: ServerMessage;
}

export interface Review {
  overall_strategy: string;
  biggest_mistake?: string;
  turning_point?: string;
  if_play_again?: string;
}



export type ServerMessage =
  | { type: "ROLE"; role: Role }
  | { type: "NIGHT_SKILL"; skill: NightSkill }
  | { type: "NIGHT_ACTION_ACK"; ok: boolean; message?: string }
  | { type: "INIT"; players: Player[]; selfId: string }
  | { type: "PHASE"; phase: Phase }
  | { type: "THINKING"; playerId: string }
  | { type: "SPEECH_START"; playerId: string }
  | { type: "SPEECH"; playerId: string; text: string }
  | { type: "VOTE"; from: string; to: string }
  | { type: "VOTE_END" }
  | { type: "DEATH"; playerId: string }
  | { type: "REVIEW"; data: any }
  | { type: "REPLAY_DATA"; timeline: ReplayEvent[]; reviews: Record<string, Review> }
