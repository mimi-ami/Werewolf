import random

from agents.wolf.wolf_strategy import choose_scapegoat
from game.roles import Role


def choose_vote(agent):
    suspects = agent.memory.suspicion.top_suspects()
    if not suspects:
        return None

    return suspects[0][0]


def decide_vote(agent):
    if agent.role == Role.WEREWOLF:
        scapegoat = choose_scapegoat(agent)
        alive = list(agent.memory.alive_players)
        return scapegoat or (random.choice(alive) if alive else None)

    suspects = agent.memory.suspicion.top_suspects(1)
    return suspects[0][0] if suspects else None