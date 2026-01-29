from game.roles import Role

def check_victory(state):
    alive = [p for p in state.players.values() if p.alive]
    wolves = [p for p in alive if p.role == Role.WEREWOLF]
    villagers = [p for p in alive if p.role != Role.WEREWOLF]

    if not wolves:
        return "VILLAGERS_WIN"
    if len(wolves) >= len(villagers):
        return "WEREWOLVES_WIN"
    return None
