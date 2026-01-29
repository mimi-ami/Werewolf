import asyncio
import contextlib
import json
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
    {"id": "P1", "name": "You", "alive": True},
]

ROLES = {}
AGENTS = {}


class ConnectionManager:
    def __init__(self) -> None:
        self.connections = {}
        self.lock = asyncio.Lock()

    async def connect(self, ws: WebSocket) -> str | None:
        await ws.accept()
        async with self.lock:
            for player in PLAYERS:
                pid = player["id"]
                if pid not in self.connections:
                    self.connections[pid] = ws
                    return pid
        return None

    async def disconnect(self, player_id: str) -> None:
        async with self.lock:
            self.connections.pop(player_id, None)

    def is_connected(self, player_id: str) -> bool:
        return player_id in self.connections

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
}


def reset_game_state() -> None:
    GAME.update(
        {
            "tick": 0,
            "timeline": [],
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


def configure_game(player_count: int) -> None:
    global PLAYERS, ROLES, AGENTS

    if player_count < MIN_PLAYERS or player_count > MAX_PLAYERS:
        raise ValueError("invalid player_count")

    PLAYERS = [{"id": "P1", "name": "You", "alive": True}]
    for i in range(2, player_count + 1):
        PLAYERS.append({"id": f"P{i}", "name": f"AI-{i - 1}", "alive": True})

    role_list = build_roles(player_count)
    ROLES = {player["id"]: role_list[idx] for idx, player in enumerate(PLAYERS)}

    AGENTS = {"P1": HumanAgent("P1")}
    for player in PLAYERS:
        pid = player["id"]
        if pid == "P1":
            continue
        role = Role[ROLES[pid]]
        agent = AIAgent(pid, role)
        agent.memory.alive_players = {p["id"] for p in PLAYERS}
        AGENTS[pid] = agent

    wolf_ids = {pid for pid, role in ROLES.items() if role == "WEREWOLF"}
    for pid in wolf_ids:
        if pid in AGENTS:
            AGENTS[pid].wolf_team = wolf_ids

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
        print(f"[SPEECH] {event.get('playerId')}: {event.get('text')}")

    observe_event(event)
    await manager.broadcast(event)


async def send_private(player_id: str, event: dict) -> None:
    if event.get("type") == "SPEECH":
        print(f"[SPEECH][private] {player_id}: {event.get('text')}")
    observe_event(event)
    await manager.send_to(player_id, event)


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


def _sanitize_speech(text: str | None) -> str | None:
    if not text:
        return text
    cleaned = text.strip()
    # Drop any stray "undefined" tokens from model output.
    cleaned = cleaned.replace("undefined", "").replace("Undefined", "").replace("UNDEFINED", "")
    cleaned = cleaned.strip()
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
                    configure_game(count)
                except Exception:
                    await send_private(player_id, {
                        "type": "CONFIG_ERROR",
                        "message": f"\u73a9\u5bb6\u4eba\u6570\u8303\u56f4\uff1a{MIN_PLAYERS}-{MAX_PLAYERS}"
                    })
                    continue

                await send_private(player_id, {
                    "type": "INIT",
                    "players": PLAYERS,
                    "selfId": player_id,
                })
                await send_private(player_id, {
                    "type": "ROLE",
                    "playerId": player_id,
                    "role": ROLES.get(player_id),
                })

                global game_task
                if game_task and not game_task.done():
                    game_task.cancel()
                game_task = asyncio.create_task(game_loop())
            elif msg_type == "SPEECH" and phase == "DAY":
                if GAME.get("current_speaker") != player_id:
                    continue
                text = (msg.get("text", "") or "").strip()
                if not text:
                    text = "\uFF08\u8DF3\u8FC7\uFF09"
                GAME["pending_speech"][player_id] = text
            elif msg_type == "SPEECH_SKIP" and phase == "DAY":
                if GAME.get("current_speaker") != player_id:
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
            elif msg_type == "SHERIFF_VOTE" and phase == "SHERIFF":
                to_id = msg.get("to")
                if to_id == "ABSTAIN":
                    to_id = None
                GAME["sheriff_votes"][player_id] = to_id
                await send_event({
                    "type": "SHERIFF_VOTE",
                    "from": player_id,
                    "to": to_id or "ABSTAIN"
                })
            elif msg_type == "NIGHT_ACTION" and phase == "NIGHT":
                action_type = msg.get("actionType")
                target = msg.get("target")
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

    # Private prompts
    for pid, role in ROLES.items():
        if not manager.is_connected(pid):
            continue
        await send_private(pid, {
            "type": "NIGHT_SKILL",
            "playerId": pid,
            "role": role,
            "hint": "Choose a target privately."
        })

    # AI night actions (ordered)
    for pid, role in ROLES.items():
        if role != "WEREWOLF":
            continue
        if pid == "P1" or pid not in AGENTS:
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

    for pid, role in ROLES.items():
        if role == "WEREWOLF":
            continue
        if pid == "P1" or pid not in AGENTS:
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
    return list(dict.fromkeys(deaths))


async def run_day(day_idx: int, night_deaths: list) -> None:
    GAME["phase"] = "DAY"
    await send_event({"type": "PHASE", "phase": "DAY"})

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
        if pid == "P1" and manager.is_connected(pid):
            for _ in range(60):  # ~15s
                if pid in GAME["pending_speech"]:
                    break
                await asyncio.sleep(0.25)
            text = GAME["pending_speech"].pop(pid, None) or "\uFF08\u8DF3\u8FC7\uFF09"
        else:
            agent = AGENTS.get(pid)
            context = build_agent_context(pid, "DAY")
            result = await _agent_act(agent, "DAY", context) if agent else {}
            speech = result.get("speech") if isinstance(result, dict) else None
            speech = _sanitize_speech(speech)
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

    await send_event({"type": "VOTE_END"})

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
        GAME["night"] = round_idx
        night_deaths = await run_night(round_idx)
        GAME["last_night_deaths"] = list(night_deaths)
        await asyncio.sleep(1)

        GAME["day"] = round_idx + 1
        await run_day(round_idx + 1, night_deaths)
        result = check_win()
        if result:
            break

        execute_id = await run_vote()
        if execute_id:
            mark_dead(execute_id)
            await send_event({"type": "DEATH", "playerId": execute_id})

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
        "reviews": {}
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

    player_id = await manager.connect(ws)
    if not player_id:
        await ws.close()
        return

    listener_task = asyncio.create_task(handle_client_messages(ws, player_id))

    if GAME["configured"]:
        await ws.send_text(json.dumps({
            "type": "INIT",
            "players": PLAYERS,
            "selfId": player_id
        }))

        await ws.send_text(json.dumps({
            "type": "ROLE",
            "playerId": player_id,
            "role": ROLES.get(player_id)
        }))

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



