import asyncio
import contextlib
import json
from collections import Counter

import uvicorn
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PLAYERS = [
    {"id": "P1", "name": "You", "alive": True},
    {"id": "P2", "name": "AI-1", "alive": True},
    {"id": "P3", "name": "AI-2", "alive": True},
    {"id": "P4", "name": "AI-3", "alive": True},
]

ROLES = {
    "P1": "SEER",
    "P2": "WITCH",
    "P3": "WEREWOLF",
    "P4": "GUARD",
}


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
        for ws in list(self.connections.values()):
            await ws.send_text(json.dumps(event))

    async def send_to(self, player_id: str, event: dict) -> None:
        ws = self.connections.get(player_id)
        if ws:
            await ws.send_text(json.dumps(event))


manager = ConnectionManager()

game_task: asyncio.Task | None = None

GAME = {
    "tick": 0,
    "timeline": [],
    "phase": "INIT",
    "votes": {},
    "sheriff_votes": {},
    "sheriff_id": None,
    "night": 0,
    "day": 0,
    "last_guard_target": None,
    "potions": {"save": True, "poison": True},
    "night_actions": {},
    "lock": asyncio.Lock(),
}


def living_player_ids() -> list:
    return [p["id"] for p in PLAYERS if p["alive"]]


def mark_dead(player_id: str) -> None:
    for player in PLAYERS:
        if player["id"] == player_id:
            player["alive"] = False
            break


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


async def send_event(event: dict) -> None:
    async with GAME["lock"]:
        tick = GAME["tick"]
        GAME["tick"] += 1
        GAME["timeline"].append({"tick": tick, "event": event})

    await manager.broadcast(event)


async def send_private(player_id: str, event: dict) -> None:
    await manager.send_to(player_id, event)


async def handle_client_messages(ws: WebSocket, player_id: str) -> None:
    while True:
        raw = await ws.receive_text()
        try:
            msg = json.loads(raw)
        except json.JSONDecodeError:
            continue

        msg_type = msg.get("type")
        phase = GAME.get("phase")
        if msg_type == "SPEECH" and phase == "DAY":
            await send_event({
                "type": "SPEECH",
                "playerId": player_id,
                "text": msg.get("text", "")
            })
        elif msg_type == "VOTE" and phase == "VOTE":
            to_id = msg.get("to")
            if to_id == "ABSTAIN":
                to_id = None
            GAME["votes"][player_id] = to_id
            await send_event({
                "type": "VOTE",
                "from": player_id,
                "to": to_id or "ABSTAIN"
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

    if witch_save and not GAME["potions"]["save"]:
        witch_save = False
    if witch_save:
        GAME["potions"]["save"] = False

    if witch_poison_target and not GAME["potions"]["poison"]:
        witch_poison_target = None
    if witch_poison_target:
        GAME["potions"]["poison"] = False

    # Private seer result
    if seer_target:
        seer_result = ROLES.get(seer_target)
        await send_private("P1", {
            "type": "SEER_RESULT",
            "target": seer_target,
            "role": seer_result
        })

    deaths = []
    if wolf_target and not witch_save and wolf_target != guard_target:
        deaths.append(wolf_target)

    if witch_poison_target:
        deaths.append(witch_poison_target)

    # No intermediate broadcasts here
    await send_event({
        "type": "NIGHT_ACTION_ACK",
        "night": night_idx,
        "summary": {
            "wolf": wolf_target is not None,
            "seer": seer_target is not None,
            "guard": guard_target is not None,
            "witch_save": witch_save,
            "witch_poison": witch_poison_target is not None
        }
    })

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

    for player_id in night_deaths:
        mark_dead(player_id)
        await send_event({"type": "DEATH", "playerId": player_id})

    # AI speech for non-connected players
    for pid in living_player_ids():
        if manager.is_connected(pid):
            continue
        await asyncio.sleep(0.6)
        await send_event({"type": "THINKING", "playerId": pid})
        await asyncio.sleep(0.6)
        await send_event({"type": "SPEECH_START", "playerId": pid})
        await asyncio.sleep(0.5)
        await send_event({
            "type": "SPEECH",
            "playerId": pid,
            "text": "I want to hear everyone first."
        })


async def run_sheriff_election() -> None:
    GAME["phase"] = "SHERIFF"
    GAME["sheriff_votes"].clear()
    await send_event({"type": "PHASE", "phase": "SHERIFF"})

    # AI sheriff votes
    alive = living_player_ids()
    for pid in alive:
        if manager.is_connected(pid):
            continue
        target = alive[0] if alive else None
        GAME["sheriff_votes"][pid] = target
        await asyncio.sleep(0.4)
        await send_event({"type": "SHERIFF_VOTE", "from": pid, "to": target or "ABSTAIN"})

    await asyncio.sleep(2)

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
        target = alive[0] if alive else None
        GAME["votes"][pid] = target
        await asyncio.sleep(0.4)
        await send_event({"type": "VOTE", "from": pid, "to": target or "ABSTAIN"})

    # Allow players to vote
    await asyncio.sleep(2)

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
        GAME["night"] = round_idx
        night_deaths = await run_night(round_idx)
        await asyncio.sleep(1)

        GAME["day"] = round_idx + 1
        await run_day(round_idx + 1, night_deaths)
        result = check_win()
        if result:
            break

        if GAME["sheriff_id"] is None:
            await run_sheriff_election()

        execute_id = await run_vote()
        if execute_id:
            mark_dead(execute_id)
            await send_event({"type": "DEATH", "playerId": execute_id})

        result = check_win()
        if result:
            break

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

    try:
        await listener_task
    finally:
        listener_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await listener_task
        await manager.disconnect(player_id)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
