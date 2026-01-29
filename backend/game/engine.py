from game.state import GameState
from game.phases import Phase
from game.victory import check_victory
from agents.wolf.wolf_memory import WolfSharedMemory
from agents.wolf.wolf_channel import WolfChannel
from agents.wolf.wolf_consensus import reach_kill_consensus

class GameEngine:

    def __init__(self, state: GameState):
        self.state = state
        self.phase = Phase.NIGHT

    def next_phase(self):
        if self.phase == Phase.NIGHT:
            self.phase = Phase.DAY
        elif self.phase == Phase.DAY:
            self.phase = Phase.VOTE
        elif self.phase == Phase.VOTE:
            self.phase = Phase.NIGHT
            self.state.round += 1

    def kill_player(self, player_id: str):
        self.state.players[player_id].alive = False
        self.state.history.append(f"{player_id} died")

    def check_game_end(self):
        return check_victory(self.state)

    def handle_wolf_night(self, wolf_agents):
        shared_memory = WolfSharedMemory()
        channel = WolfChannel(shared_memory)

        kills = []
        for wolf in wolf_agents:
            kill = wolf.wolf_night_action(channel)
            kills.append({
                "wolf": wolf.player_id,
                "kill": kill,
            })

        final_target = reach_kill_consensus(kills)
        return final_target