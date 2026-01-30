import asyncio
import contextlib
import json
import re
import random
import sys
from collections import Counter
from pathlib import Path

import uvicorn
from fastapi import FastAPI, WebSocket
from starlette.websockets import WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

# Ensure backend root is on sys.path for absolute imports.
BACKEND_ROOT = Path(__file__).resolve().parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from agents.ai_agent import AIAgent
from agents.human_agent import HumanAgent
from agents.personality import Personality
from game.roles import Role

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MIN_PLAYERS = 5
MAX_PLAYERS = 12

PLAYERS = [
    {"id": "P1", "name": "P1", "alive": True},
]

ROLES = {}
AGENTS = {}


class ConnectionManager:
    def __init__(self) -> None:
        self.connections = {}
        self.spectators = set()
        self.lock = asyncio.Lock()

    async def connect(self, ws: WebSocket, mode: str | None = None) -> str | None:
        await ws.accept()
        async with self.lock:
            if mode == "observer":
                idx = 1
                while f"OBS{idx}" in self.connections:
                    idx += 1
                pid = f"OBS{idx}"
                self.connections[pid] = ws
                self.spectators.add(pid)
                return pid
            for player in PLAYERS:
                pid = player["id"]
                if pid not in self.connections:
                    self.connections[pid] = ws
                    return pid
        return None

    async def disconnect(self, player_id: str) -> None:
        async with self.lock:
            self.connections.pop(player_id, None)
            self.spectators.discard(player_id)

    def is_connected(self, player_id: str) -> bool:
        return player_id in self.connections

    def is_spectator(self, player_id: str) -> bool:
        return player_id in self.spectators

    async def broadcast(self, event: dict) -> None:
        for pid, ws in list(self.connections.items()):
            try:
                await ws.send_text(json.dumps(event))
            except Exception:
                # Drop broken connections to avoid sending on closed sockets.
                await self.disconnect(pid)

    async def send_to(self, player_id: str, event: dict) -> None:
        ws = self.connections.get(player_id)
        if ws:
            try:
                await ws.send_text(json.dumps(event))
            except Exception:
                await self.disconnect(player_id)


manager = ConnectionManager()

game_task: asyncio.Task | None = None

GAME = {
    "configured": False,
    "player_count": 1,
    "tick": 0,
    "timeline": [],
    "action_log": [],
    "phase": "INIT",
    "votes": {},
    "sheriff_votes": {},
    "sheriff_id": None,
    "night": 0,
    "day": 0,
    "current_speaker": None,
    "pending_speech": {},
    "last_guard_target": None,
    "last_night_deaths": [],
    "potions": {"save": True, "poison": True},
    "night_actions": {},
    "lock": asyncio.Lock(),
    "human_player_id": "P1",
}


def reset_game_state() -> None:
    GAME.update(
        {
            "tick": 0,
            "timeline": [],
            "action_log": [],
            "phase": "INIT",
            "votes": {},
            "sheriff_votes": {},
            "sheriff_id": None,
            "night": 0,
            "day": 0,
            "current_speaker": None,
            "pending_speech": {},
            "last_guard_target": None,
            "last_night_deaths": [],
            "potions": {"save": True, "poison": True},
            "night_actions": {},
            "human_player_id": GAME.get("human_player_id", "P1"),
        }
    )


def build_roles(player_count: int) -> list[str]:
    wolves = max(2, player_count // 3)
    roles = ["WEREWOLF"] * wolves
    roles += ["SEER", "WITCH", "GUARD"]
    remaining = player_count - len(roles)
    if remaining < 1:
        remaining = 1
    roles += ["VILLAGER"] * remaining
    roles = roles[:player_count]
    random.shuffle(roles)
    return roles


def configure_game(player_count: int, human_player_id: str | None = "P1") -> None:
    global PLAYERS, ROLES, AGENTS

    if player_count < MIN_PLAYERS or player_count > MAX_PLAYERS:
        raise ValueError("invalid player_count")

    PLAYERS = [{"id": "P1", "name": "P1", "alive": True}]
    for i in range(2, player_count + 1):
        PLAYERS.append({"id": f"P{i}", "name": f"P{i}", "alive": True})

    role_list = build_roles(player_count)
    ROLES = {player["id"]: role_list[idx] for idx, player in enumerate(PLAYERS)}

    AGENTS = {}
    for player in PLAYERS:
        pid = player["id"]
        if human_player_id and pid == human_player_id:
            AGENTS[pid] = HumanAgent(pid)
            continue
        role = Role[ROLES[pid]]
        personality = Personality(
            aggressiveness=round(random.uniform(0.2, 0.9), 2),
            deception=round(random.uniform(0.2, 0.9), 2),
            logic=round(random.uniform(0.2, 0.9), 2),
            tone=random.choice(["cautious", "bold", "skeptical", "warm", "cold"]),
            quirk=random.choice([
                "asks short questions",
                "speaks in concise points",
                "prefers evidence",
                "focuses on contradictions",
                "avoids overcommitting",
            ]),
        )
        agent = AIAgent(pid, role, personality=personality)
        agent.memory.alive_players = {p["id"] for p in PLAYERS}
        AGENTS[pid] = agent

    wolf_ids = {pid for pid, role in ROLES.items() if role == "WEREWOLF"}
    for pid in wolf_ids:
        if pid in AGENTS:
            AGENTS[pid].wolf_team = wolf_ids

    GAME["human_player_id"] = human_player_id
    reset_game_state()
    GAME["configured"] = True
    GAME["player_count"] = player_count


def living_player_ids() -> list:
    return [p["id"] for p in PLAYERS if p["alive"]]


def mark_dead(player_id: str) -> None:
    for player in PLAYERS:
        if player["id"] == player_id:
            player["alive"] = False
            break
    for agent in AGENTS.values():
        if hasattr(agent, "memory"):
            agent.memory.alive_players.discard(player_id)


def check_win() -> str | None:
    alive = set(living_player_ids())
    wolves = {pid for pid, role in ROLES.items() if role == "WEREWOLF"}
    alive_wolves = alive & wolves
    alive_others = alive - wolves

    if not alive_wolves:
        return "VILLAGERS_WIN"
    if len(alive_wolves) >= len(alive_others):
        return "WEREWOLVES_WIN"
    return None


def observe_event(event: dict) -> None:
    text = json.dumps(event, ensure_ascii=False)
    for agent in AGENTS.values():
        agent.observe(text)
        if event.get("type") == "INIT" and hasattr(agent, "memory"):
            try:
                agent.memory.set_players(event.get("players", []))
            except Exception:
                pass
        if event.get("type") == "SPEECH" and hasattr(agent, "memory"):
            try:
                agent.memory.add_speech(event.get("playerId", "?"), event.get("text", ""))
            except Exception:
                pass


async def send_event(event: dict) -> None:
    async with GAME["lock"]:
        tick = GAME["tick"]
        GAME["tick"] += 1
        GAME["timeline"].append({"tick": tick, "event": event})

    if event.get("type") == "SPEECH":
        text = event.get("text")
        if isinstance(text, str):
            event["text"] = _sanitize_speech(text) or ""
        print(f"[SPEECH] {event.get('playerId')}: {event.get('text')}")

    observe_event(event)
    await manager.broadcast(event)


async def send_private(player_id: str, event: dict) -> None:
    if event.get("type") == "SPEECH":
        print(f"[SPEECH][private] {player_id}: {event.get('text')}")
    observe_event(event)
    await manager.send_to(player_id, event)


def record_action(action: dict) -> None:
    entry = {
        "phase": GAME.get("phase"),
        "night": GAME.get("night"),
        "day": GAME.get("day"),
    }
    entry.update(action)
    GAME["action_log"].append(entry)


def is_player_mode() -> bool:
    return bool(GAME.get("human_player_id"))


def append_replay_event(event: dict) -> None:
    tick = GAME["tick"]
    GAME["tick"] += 1
    GAME["timeline"].append({"tick": tick, "event": event})


def build_agent_context(player_id: str, phase: str) -> dict:
    role = ROLES.get(player_id)
    context = {
        "phase": phase,
        "player_id": player_id,
        "role": role,
        "alive_players": living_player_ids(),
        "dead_players": [p["id"] for p in PLAYERS if not p["alive"]],
        "night": GAME.get("night"),
        "day": GAME.get("day"),
        "last_night_deaths": GAME.get("last_night_deaths", []),
        "last_guard_target": GAME.get("last_guard_target"),
        "potions": GAME.get("potions", {}),
    }
    agent = AGENTS.get(player_id)
    if agent and getattr(agent, "wolf_team", None):
        context["wolf_team"] = sorted(list(agent.wolf_team))
    return context


async def _agent_act(agent: AIAgent, phase: str, context: dict | None = None) -> dict:
    return await asyncio.to_thread(agent.act, phase, context)


def _valid_target(target: str | None) -> str | None:
    if not target:
        return None
    alive = set(living_player_ids())
    return target if target in alive else None


def _sanitize_speech(text: str | None, speaker_id: str | None = None) -> str | None:
    if not text:
        return text
    cleaned = text.strip()
    # Drop any stray "undefined" tokens from model output.
    cleaned = cleaned.replace("undefined", "").replace("Undefined", "").replace("UNDEFINED", "")
    cleaned = cleaned.strip()
    # Replace ambiguous single "P" with the speaker id when available.
    if speaker_id:
        cleaned = re.sub(r"\bP\b", speaker_id, cleaned)
        cleaned = re.sub(r"\bP(?!\d)\b", speaker_id, cleaned)
    # Prevent AI from claiming a living player is dead.
    alive = set(living_player_ids())
    for pid in alive:
        pattern = f"{pid}.{{0,6}}(\u5df2\u6b7b|\u6b7b\u4ea1|\u6b7b\u4e86|\u51fa\u5c40|\u88ab\u6295|\u88ab\u5200)"
        if re.search(pattern, cleaned):
            cleaned = re.sub(pattern, f"{pid}\u4ecd\u5b58\u6d3b", cleaned)
    return cleaned


def choose_wolf_target() -> str | None:
    alive = [pid for pid in living_player_ids() if ROLES.get(pid) != "WEREWOLF"]
    return alive[0] if alive else None


def choose_seer_target() -> str | None:
    alive = [pid for pid in living_player_ids() if ROLES.get(pid) != "SEER"]
    return alive[0] if alive else None


def choose_guard_target() -> str | None:
    alive = living_player_ids()
    if not alive:
        return None
    target = alive[-1]
    if target == GAME["last_guard_target"] and len(alive) > 1:
        target = alive[0]
    return target


def choose_witch_poison_target() -> str | None:
    alive_wolves = [pid for pid in living_player_ids() if ROLES.get(pid) == "WEREWOLF"]
    return alive_wolves[0] if alive_wolves else None


async def send_init_to(player_id: str) -> None:
    await manager.send_to(player_id, {
        "type": "INIT",
        "players": PLAYERS,
        "selfId": player_id,
    })
    if manager.is_spectator(player_id):
        await manager.send_to(player_id, {
            "type": "ROLE_MAP",
            "roles": {p["id"]: ROLES.get(p["id"]) for p in PLAYERS},
        })
    else:
        await manager.send_to(player_id, {
            "type": "ROLE",
            "playerId": player_id,
            "role": ROLES.get(player_id),
        })


async def broadcast_init() -> None:
    for pid in list(manager.connections.keys()):
        await send_init_to(pid)


async def handle_client_messages(ws: WebSocket, player_id: str) -> None:
    try:
        while True:
            raw = await ws.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue

            msg_type = msg.get("type")
            phase = GAME.get("phase")
            if msg_type == "CONFIG":
                try:
                    count = int(msg.get("playerCount", 0))
                    observer = bool(msg.get("observer", False))
                    human_id = None if observer else "P1"
                    configure_game(count, human_player_id=human_id)
                except Exception:
                    await send_private(player_id, {
                        "type": "CONFIG_ERROR",
                        "message": f"\u73a9\u5bb6\u4eba\u6570\u8303\u56f4\uff1a{MIN_PLAYERS}-{MAX_PLAYERS}"
                    })
                    continue

                await broadcast_init()

                global game_task
                if game_task and not game_task.done():
                    game_task.cancel()
                game_task = asyncio.create_task(game_loop())
            elif msg_type == "SPEECH" and phase == "DAY":
                if GAME.get("current_speaker") != player_id:
                    continue
                if player_id not in living_player_ids():
                    continue
                text = (msg.get("text", "") or "").strip()
                if not text:
                    text = "\uFF08\u8DF3\u8FC7\uFF09"
                GAME["pending_speech"][player_id] = text
            elif msg_type == "SPEECH_SKIP" and phase == "DAY":
                if GAME.get("current_speaker") != player_id:
                    continue
                if player_id not in living_player_ids():
                    continue
                GAME["pending_speech"][player_id] = "\uFF08\u8DF3\u8FC7\uFF09"
            elif msg_type == "VOTE" and phase == "VOTE":
                if player_id not in living_player_ids():
                    continue
                to_id = msg.get("to")
                if to_id not in living_player_ids():
                    continue
                GAME["votes"][player_id] = to_id
                await send_event({
                    "type": "VOTE",
                    "from": player_id,
                    "to": to_id
                })
                record_action({
                    "type": "VOTE",
                    "from": player_id,
                    "to": to_id,
                    "source": "human",
                })
            elif msg_type == "SHERIFF_VOTE" and phase == "SHERIFF":
                if player_id not in living_player_ids():
                    continue
                to_id = msg.get("to")
                if to_id == "ABSTAIN":
                    to_id = None
                GAME["sheriff_votes"][player_id] = to_id
                await send_event({
                    "type": "SHERIFF_VOTE",
                    "from": player_id,
                    "to": to_id or "ABSTAIN"
                })
                record_action({
                    "type": "SHERIFF_VOTE",
                    "from": player_id,
                    "to": to_id or "ABSTAIN",
                    "source": "human",
                })
            elif msg_type == "NIGHT_ACTION" and phase == "NIGHT":
                action_type = msg.get("actionType")
                target = msg.get("target")
                if player_id not in living_player_ids():
                    await send_private(player_id, {
                        "type": "NIGHT_ACTION_ACK",
                        "ok": False,
                        "message": "\u4f60\u5df2\u51fa\u5c40\uff0c\u65e0\u6cd5\u884c\u52a8",
                    })
                    continue
                if action_type:
                    GAME["night_actions"][player_id] = {
                        "actionType": action_type,
                        "target": target
                    }
                    await send_private(player_id, {
                        "type": "NIGHT_ACTION_ACK",
                        "ok": True,
                        "actionType": action_type,
                        "target": target,
                    })
                else:
                    await send_private(player_id, {
                        "type": "NIGHT_ACTION_ACK",
                        "ok": False,
                        "message": "\u884c\u52a8\u65e0\u6548",
                    })
    except WebSocketDisconnect:
        return
async def run_night(night_idx: int) -> list:
    GAME["phase"] = "NIGHT"
    GAME["night_actions"].clear()
    await send_event({"type": "PHASE", "phase": "NIGHT"})
    await send_event({
        "type": "SPEECH",
        "playerId": "SYSTEM",
        "text": "\u5929\u9ed1\u8bf7\u95ed\u773c\u3002"
    })
    await send_event({
        "type": "SPEECH",
        "playerId": "SYSTEM",
        "text": "\u591c\u665a\u9636\u6bb5\u5f00\u59cb\u3002"
    })

    # Private prompts
    for pid, role in ROLES.items():
        if pid not in living_player_ids():
            continue
        if not manager.is_connected(pid):
            continue
        await send_private(pid, {
            "type": "NIGHT_SKILL",
            "playerId": pid,
            "role": role,
            "hint": "Choose a target privately."
        })

    # AI night actions (ordered)
    await send_event({
        "type": "SPEECH",
        "playerId": "SYSTEM",
        "text": "\u72fc\u4eba\u8bf7\u8fdb\u884c\u884c\u52a8\u3002"
    })
    for pid, role in ROLES.items():
        if role != "WEREWOLF":
            continue
        if pid == GAME.get("human_player_id") or pid not in AGENTS:
            continue
        if pid not in living_player_ids():
            continue
        agent = AGENTS[pid]
        context = build_agent_context(pid, "NIGHT")
        result = await _agent_act(agent, "NIGHT", context)
        action = result.get("action", {}) if isinstance(result, dict) else {}
        target = _valid_target(action.get("kill")) or choose_wolf_target()
        GAME["night_actions"][pid] = {"actionType": "WEREWOLF", "target": target}

    # Resolve wolf target early for witch context.
    wolf_target_hint = None
    for pid, action in GAME["night_actions"].items():
        role = ROLES.get(pid)
        action_type = action.get("actionType")
        target = action.get("target")
        if role == "WEREWOLF" and action_type == "WEREWOLF":
            if target in living_player_ids() and ROLES.get(target) != "WEREWOLF":
                wolf_target_hint = target
                break

    await send_event({
        "type": "SPEECH",
        "playerId": "SYSTEM",
        "text": "\u9884\u8a00\u5bb6\u8bf7\u8fdb\u884c\u67e5\u9a8c\u3002"
    })
    await send_event({
        "type": "SPEECH",
        "playerId": "SYSTEM",
        "text": "\u5b88\u536b\u8bf7\u8fdb\u884c\u5b88\u62a4\u3002"
    })
    await send_event({
        "type": "SPEECH",
        "playerId": "SYSTEM",
        "text": "\u5973\u5deb\u8bf7\u51b3\u5b9a\u662f\u5426\u4f7f\u7528\u89e3\u836f\u3002"
    })
    await send_event({
        "type": "SPEECH",
        "playerId": "SYSTEM",
        "text": "\u5973\u5deb\u8bf7\u51b3\u5b9a\u662f\u5426\u4f7f\u7528\u6bd2\u836f\u3002"
    })
    for pid, role in ROLES.items():
        if role == "WEREWOLF":
            continue
        if pid == GAME.get("human_player_id") or pid not in AGENTS:
            continue
        if pid not in living_player_ids():
            continue
        agent = AGENTS[pid]
        context = build_agent_context(pid, "NIGHT")
        if role == "WITCH" and wolf_target_hint:
            context["wolf_target"] = wolf_target_hint
        result = await _agent_act(agent, "NIGHT", context)
        action = result.get("action", {}) if isinstance(result, dict) else {}

        if role == "SEER":
            target = _valid_target(action.get("check")) or choose_seer_target()
            GAME["night_actions"][pid] = {"actionType": "SEER", "target": target}
        elif role == "GUARD":
            target = _valid_target(action.get("guard")) or choose_guard_target()
            GAME["night_actions"][pid] = {"actionType": "GUARD", "target": target}
        elif role == "WITCH":
            poison_target = _valid_target(action.get("poison")) or None
            if poison_target:
                GAME["night_actions"][pid] = {"actionType": "WITCH_POISON", "target": poison_target}
            elif action.get("save"):
                GAME["night_actions"][pid] = {"actionType": "WITCH_SAVE", "target": None}

    # Allow clients to submit night actions
    await asyncio.sleep(3)

    wolf_target = None
    seer_target = None
    guard_target = None
    witch_save = False
    witch_poison_target = None

    for pid, action in GAME["night_actions"].items():
        role = ROLES.get(pid)
        action_type = action.get("actionType")
        target = action.get("target")
        if role == "WEREWOLF" and action_type == "WEREWOLF":
            if target in living_player_ids() and ROLES.get(target) != "WEREWOLF":
                wolf_target = target
        elif role == "SEER" and action_type == "SEER":
            if target in living_player_ids() and target != pid:
                seer_target = target
        elif role == "GUARD" and action_type == "GUARD":
            if target in living_player_ids():
                if target != GAME["last_guard_target"] or len(living_player_ids()) <= 1:
                    guard_target = target
        elif role == "WITCH":
            if action_type == "WITCH_SAVE":
                witch_save = True
            elif action_type == "WITCH_POISON":
                if target in living_player_ids() and target != pid:
                    witch_poison_target = target

    if wolf_target is None:
        wolf_target = choose_wolf_target()
    if seer_target is None:
        seer_target = choose_seer_target()
    if guard_target is None:
        guard_target = choose_guard_target()
    GAME["last_guard_target"] = guard_target

    save_available = GAME["potions"]["save"]
    poison_available = GAME["potions"]["poison"]

    guard_blocks = wolf_target is not None and wolf_target == guard_target
    wolf_death = wolf_target if wolf_target and not guard_blocks else None

    if witch_save:
        if not save_available:
            witch_save = False
        elif wolf_death:
            wolf_death = None
            GAME["potions"]["save"] = False
        else:
            witch_save = False

    if witch_poison_target and not poison_available:
        witch_poison_target = None
    if witch_poison_target:
        GAME["potions"]["poison"] = False

    # Private seer result
    if seer_target:
        seer_result = ROLES.get(seer_target)
        seer_player = next((pid for pid, role in ROLES.items() if role == "SEER"), None)
        if seer_player:
            await send_private(seer_player, {
                "type": "SEER_RESULT",
                "target": seer_target,
                "role": seer_result
            })

    deaths = []
    if wolf_death:
        deaths.append(wolf_death)
    if witch_poison_target:
        deaths.append(witch_poison_target)


    for pid, role in ROLES.items():
        if not manager.is_connected(pid):
            continue
        if role == "WEREWOLF":
            await send_private(pid, {
                "type": "NIGHT_ACTION_ACK",
                "playerId": pid,
                "actionType": "WEREWOLF",
                "target": wolf_target,
                "status": "ok" if wolf_target else "rejected"
            })
        elif role == "SEER":
            await send_private(pid, {
                "type": "NIGHT_ACTION_ACK",
                "playerId": pid,
                "actionType": "SEER",
                "target": seer_target,
                "status": "ok" if seer_target else "rejected"
            })
        elif role == "GUARD":
            await send_private(pid, {
                "type": "NIGHT_ACTION_ACK",
                "playerId": pid,
                "actionType": "GUARD",
                "target": guard_target,
                "status": "ok" if guard_target else "rejected"
            })
        elif role == "WITCH":
            await send_private(pid, {
                "type": "NIGHT_ACTION_ACK",
                "playerId": pid,
                "actionType": "WITCH_SAVE",
                "target": wolf_target if witch_save else None,
                "status": "ok" if witch_save else "rejected"
            })
            await send_private(pid, {
                "type": "NIGHT_ACTION_ACK",
                "playerId": pid,
                "actionType": "WITCH_POISON",
                "target": witch_poison_target,
                "status": "ok" if witch_poison_target else "rejected"
            })

    # Record resolved night actions for end-game replay.
    def wolf_action_status(target: str | None) -> str:
        if not target:
            return "rejected"
        if target != wolf_target:
            return "overruled"
        if wolf_death == target:
            return "success"
        if guard_blocks and target == guard_target:
            return "blocked_by_guard"
        if witch_save and target == wolf_target:
            return "saved_by_witch"
        return "no_effect"

    for pid, role in ROLES.items():
        if role != "WEREWOLF":
            continue
        action = GAME["night_actions"].get(pid, {})
        if action.get("actionType") != "WEREWOLF":
            continue
        target = action.get("target")
        record_action({
            "type": "NIGHT_ACTION",
            "playerId": pid,
            "role": "WEREWOLF",
            "actionType": "WEREWOLF_KILL",
            "target": target,
            "status": wolf_action_status(target),
        })

    seer_player = next((pid for pid, role in ROLES.items() if role == "SEER"), None)
    if seer_player:
        action = GAME["night_actions"].get(seer_player)
        if action and action.get("actionType") == "SEER":
            target = action.get("target")
            ok = bool(target and target in living_player_ids() and target != seer_player)
            record_action({
                "type": "NIGHT_ACTION",
                "playerId": seer_player,
                "role": "SEER",
                "actionType": "SEER_CHECK",
                "target": target,
                "status": "ok" if ok else "rejected",
                "resultRole": ROLES.get(target) if ok else None,
            })
        elif seer_target:
            record_action({
                "type": "NIGHT_ACTION",
                "playerId": seer_player,
                "role": "SEER",
                "actionType": "SEER_CHECK",
                "target": seer_target,
                "status": "auto",
                "resultRole": ROLES.get(seer_target),
            })

    guard_player = next((pid for pid, role in ROLES.items() if role == "GUARD"), None)
    if guard_player:
        action = GAME["night_actions"].get(guard_player)
        if action and action.get("actionType") == "GUARD":
            target = action.get("target")
            ok = bool(target and target in living_player_ids())
            status = "ok"
            if not ok:
                status = "rejected"
            elif target == GAME["last_guard_target"] and len(living_player_ids()) > 1:
                status = "rejected_same_target"
            elif guard_blocks and target == guard_target:
                status = "blocked_attack"
            record_action({
                "type": "NIGHT_ACTION",
                "playerId": guard_player,
                "role": "GUARD",
                "actionType": "GUARD_PROTECT",
                "target": target,
                "status": status,
            })
        elif guard_target:
            status = "blocked_attack" if guard_blocks and guard_target == wolf_target else "auto"
            record_action({
                "type": "NIGHT_ACTION",
                "playerId": guard_player,
                "role": "GUARD",
                "actionType": "GUARD_PROTECT",
                "target": guard_target,
                "status": status,
            })

    witch_player = next((pid for pid, role in ROLES.items() if role == "WITCH"), None)
    if witch_player:
        action = GAME["night_actions"].get(witch_player)
        if action and action.get("actionType") == "WITCH_SAVE":
            record_action({
                "type": "NIGHT_ACTION",
                "playerId": witch_player,
                "role": "WITCH",
                "actionType": "WITCH_SAVE",
                "target": wolf_target if action else None,
                "status": "ok" if witch_save else "rejected",
            })
        elif action and action.get("actionType") == "WITCH_POISON":
            target = action.get("target")
            record_action({
                "type": "NIGHT_ACTION",
                "playerId": witch_player,
                "role": "WITCH",
                "actionType": "WITCH_POISON",
                "target": target,
                "status": "ok" if witch_poison_target == target else "rejected",
            })

    # Public timeline summary for end-game replay.
    def _who_did_what() -> list[str]:
        parts = []
        wolf_lines = []
        for pid, role in ROLES.items():
            if role != "WEREWOLF":
                continue
            action = GAME["night_actions"].get(pid, {})
            if action.get("actionType") != "WEREWOLF":
                continue
            target = action.get("target")
            if target:
                wolf_lines.append(f"{pid}刀了{target}")
        if wolf_lines:
            parts.append("狼人请进行行动：" + "，".join(wolf_lines) + "。")

        if seer_player:
            target = seer_target or (GAME["night_actions"].get(seer_player, {}) or {}).get("target")
            if target:
                parts.append(f"预言家进行查验：{seer_player}验了{target}。")

        if guard_player:
            target = guard_target or (GAME["night_actions"].get(guard_player, {}) or {}).get("target")
            if target:
                parts.append(f"守卫进行守护：{guard_player}守了{target}。")

        if witch_player:
            action = GAME["night_actions"].get(witch_player, {})
            if action.get("actionType") == "WITCH_SAVE":
                target = wolf_target if wolf_target else "无人"
                parts.append(f"女巫使用解药：{witch_player}救了{target}。")
            elif action.get("actionType") == "WITCH_POISON":
                target = action.get("target")
                if target:
                    parts.append(f"女巫使用毒药：{witch_player}毒了{target}。")
        return parts

    if is_player_mode():
        for line in _who_did_what():
            append_replay_event({
                "type": "SPEECH",
                "playerId": "SYSTEM",
                "text": line,
            })
    else:
        for line in _who_did_what():
            await send_event({
                "type": "SPEECH",
                "playerId": "SYSTEM",
                "text": line,
            })
    return list(dict.fromkeys(deaths))


async def run_day(day_idx: int, night_deaths: list) -> None:
    GAME["phase"] = "DAY"
    await send_event({"type": "PHASE", "phase": "DAY"})
    await send_event({
        "type": "SPEECH",
        "playerId": "SYSTEM",
        "text": "\u5929\u4eae\u4e86\u3002"
    })

    if night_deaths:
        report_text = f"\u6628\u591c\u6b7b\u4ea1\uff1a{'、'.join(night_deaths)}\u3002"
    else:
        report_text = "\u6628\u591c\u65e0\u4eba\u6b7b\u4ea1\u3002"
    await send_event({
        "type": "SPEECH",
        "playerId": "SYSTEM",
        "text": report_text
    })

    for player_id in night_deaths:
        mark_dead(player_id)
        await send_event({"type": "DEATH", "playerId": player_id})

    # Speaking order: each alive player gets a turn.
    for pid in living_player_ids():
        GAME["current_speaker"] = pid
        await asyncio.sleep(0.2)
        if pid != "P1" or not manager.is_connected(pid):
            await send_event({"type": "THINKING", "playerId": pid})
            await asyncio.sleep(0.4)
        await send_event({"type": "SPEECH_START", "playerId": pid})
        if pid == GAME.get("human_player_id") and manager.is_connected(pid):
            while pid not in GAME["pending_speech"]:
                # Wait for user input; do not auto-skip on a timer.
                if not manager.is_connected(pid):
                    break
                await asyncio.sleep(0.2)
            text = GAME["pending_speech"].pop(pid, None) or "\uFF08\u8DF3\u8FC7\uFF09"
        else:
            agent = AGENTS.get(pid)
            context = build_agent_context(pid, "DAY")
            result = await _agent_act(agent, "DAY", context) if agent else {}
            speech = result.get("speech") if isinstance(result, dict) else None
            speech = _sanitize_speech(speech, pid)
            text = speech or "\uFF08\u8DF3\u8FC7\uFF09"
        await send_event({
            "type": "SPEECH",
            "playerId": pid,
            "text": text
        })
        GAME["current_speaker"] = None


async def run_sheriff_election() -> None:
    GAME["phase"] = "SHERIFF"
    GAME["sheriff_votes"].clear()
    await send_event({"type": "PHASE", "phase": "SHERIFF"})

    # AI sheriff votes
    alive = living_player_ids()
    for pid in alive:
        if manager.is_connected(pid):
            continue
        agent = AGENTS.get(pid)
        target = None
        if agent:
            context = build_agent_context(pid, "SHERIFF")
            result = await _agent_act(agent, "SHERIFF", context)
            action = result.get("action", {}) if isinstance(result, dict) else {}
            target = _valid_target(action.get("vote"))
        if not target:
            target = alive[0] if alive else None
        GAME["sheriff_votes"][pid] = target
        await asyncio.sleep(0.2)
        await send_event({"type": "SHERIFF_VOTE", "from": pid, "to": target or "ABSTAIN"})
        record_action({
            "type": "SHERIFF_VOTE",
            "from": pid,
            "to": target or "ABSTAIN",
            "source": "ai",
        })

    await asyncio.sleep(1)

    tally = Counter(v for v in GAME["sheriff_votes"].values() if v)
    if not tally:
        await send_event({"type": "SHERIFF_NONE"})
        return

    top = tally.most_common()
    if len(top) > 1 and top[0][1] == top[1][1]:
        await send_event({"type": "SHERIFF_TIE"})
        return

    sheriff_id = top[0][0]
    GAME["sheriff_id"] = sheriff_id
    await send_event({"type": "SHERIFF", "playerId": sheriff_id})


async def run_vote() -> str | None:
    GAME["phase"] = "VOTE"
    GAME["votes"].clear()
    await send_event({"type": "PHASE", "phase": "VOTE"})
    await send_event({
        "type": "SPEECH",
        "playerId": "SYSTEM",
        "text": "\u5f00\u59cb\u6295\u7968\u3002"
    })

    # AI votes for non-connected players
    alive = living_player_ids()
    for pid in alive:
        if manager.is_connected(pid):
            continue
        agent = AGENTS.get(pid)
        target = None
        if agent:
            context = build_agent_context(pid, "VOTE")
            result = await _agent_act(agent, "VOTE", context)
            action = result.get("action", {}) if isinstance(result, dict) else {}
            target = _valid_target(action.get("vote"))
        if not target:
            target = alive[0] if alive else None
        GAME["votes"][pid] = target
        await asyncio.sleep(0.2)
        await send_event({"type": "VOTE", "from": pid, "to": target})
        record_action({
            "type": "VOTE",
            "from": pid,
            "to": target,
            "source": "ai",
        })

    # Allow players to vote (wait until everyone votes or timeout).
    required = set(living_player_ids())
    for _ in range(60):  # ~15s
        if required.issubset(GAME["votes"].keys()):
            break
        await asyncio.sleep(0.25)

    # Auto-vote for anyone who didn't vote.
    missing = required - set(GAME["votes"].keys())
    for pid in missing:
        target = random.choice(list(required))
        GAME["votes"][pid] = target
        await send_event({"type": "VOTE", "from": pid, "to": target})
        record_action({
            "type": "VOTE",
            "from": pid,
            "to": target,
            "source": "auto",
        })

    await send_event({"type": "VOTE_END"})

    # Defensive: drop votes from dead players.
    alive_set = set(living_player_ids())
    GAME["votes"] = {voter: target for voter, target in GAME["votes"].items() if voter in alive_set}

    if not GAME["votes"]:
        return None

    # Weighted tally with sheriff double vote
    counts = {}
    for voter, target in GAME["votes"].items():
        if not target:
            continue
        weight = 2 if voter == GAME["sheriff_id"] else 1
        counts[target] = counts.get(target, 0) + weight

    if not counts:
        return None

    sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    if len(sorted_counts) > 1 and sorted_counts[0][1] == sorted_counts[1][1]:
        await send_event({"type": "VOTE_TIE"})
        return None

    return sorted_counts[0][0]


async def game_loop() -> None:
    # INIT broadcast is per-connection; gameplay starts here
    result = None
    max_rounds = 3
    for round_idx in range(max_rounds):
        if not manager.connections:
            break
        print(f"[GAME] Round {round_idx} start")
        GAME["night"] = round_idx
        night_deaths = await run_night(round_idx)
        GAME["last_night_deaths"] = list(night_deaths)
        await asyncio.sleep(1)

        GAME["day"] = round_idx + 1
        await run_day(round_idx + 1, night_deaths)
        result = check_win()
        print(f"[GAME] After day {round_idx + 1}, result={result}")
        if result:
            break

        print("[GAME] Starting vote phase")
        execute_id = await run_vote()
        print(f"[GAME] Vote ended, execute_id={execute_id}")
        if execute_id:
            mark_dead(execute_id)
            await send_event({"type": "DEATH", "playerId": execute_id})
            await send_event({
                "type": "SPEECH",
                "playerId": "SYSTEM",
                "text": f"\u6295\u7968\u5904\u51b3\uff1a{execute_id}\u51fa\u5c40\u3002"
            })
        else:
            await send_event({
                "type": "SPEECH",
                "playerId": "SYSTEM",
                "text": "\u6295\u7968\u7ed3\u679c\u5e73\u7968\uff0c\u672c\u8f6e\u65e0\u4eba\u51fa\u5c40\u3002"
            })

        result = check_win()
        if result:
            break

    if not manager.connections:
        return
    # GAME END
    result = result or "DRAW"
    await send_event({
        "type": "REPLAY_DATA",
        "timeline": list(GAME["timeline"]),
        "actionLog": list(GAME["action_log"]),
        "reviews": {},
        "result": result,
        "finalRoles": [
            {"id": p["id"], "name": p["name"], "role": ROLES.get(p["id"])}
            for p in PLAYERS
        ]
    })

    await send_event({
        "type": "REVIEW",
        "data": {
            "P2": {
                "overall_strategy": "Stay quiet early.",
                "biggest_mistake": "Voted too fast."
            }
        }
    })


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    global game_task

    mode = ws.query_params.get("mode")
    player_id = await manager.connect(ws, mode=mode)
    if not player_id:
        await ws.close()
        return

    listener_task = asyncio.create_task(handle_client_messages(ws, player_id))

    if GAME["configured"]:
        await send_init_to(player_id)

        if game_task is None or game_task.done():
            game_task = asyncio.create_task(game_loop())
    else:
        await ws.send_text(json.dumps({
            "type": "CONFIG_REQUIRED",
            "minPlayers": MIN_PLAYERS,
            "maxPlayers": MAX_PLAYERS
        }))

    try:
        await listener_task
    except Exception:
        pass
    finally:
        listener_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await listener_task
        await manager.disconnect(player_id)
        if not manager.connections and game_task and not game_task.done():
            game_task.cancel()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)



