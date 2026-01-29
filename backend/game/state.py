from dataclasses import dataclass, field
from typing import Dict, List
from game.roles import Role

@dataclass
class PlayerState:
    player_id: str
    role: Role
    alive: bool = True
    revealed: bool = False

@dataclass
class GameState:
    players: Dict[str, PlayerState]
    round: int = 0
    history: List[str] = field(default_factory=list)
