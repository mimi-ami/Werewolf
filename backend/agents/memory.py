class AgentMemory:

    def __init__(self):
        self.events = []
        self.suspicion = SuspicionTable()
        self.confirmed_roles = {}
        self.alive_players = set()

    def add_event(self, event: str, max_events: int = 50):
        self.events.append(event)
        if len(self.events) > max_events:
            self.events = self.events[-max_events:]

    def summary(self):
        suspects = self.suspicion.top_suspects()
        return {
            "top_suspects": suspects,
            "confirmed_roles": self.confirmed_roles,
        }

    def visible_events(self, k: int = 10):
        return self.events[-k:]

    def find_events_about(self, player_id, k: int = 2):
        return [
            e for e in self.events
            if player_id in e
        ][:k]


class SuspicionTable:
    """
    Track suspicion score per player.
    0.0 = neutral, >0 = more suspicious, <0 = more trusted
    """

    def __init__(self):
        self.scores = {}

    def init_player(self, player_id):
        self.scores[player_id] = 0.0

    def add(self, player_id, delta):
        self.scores[player_id] = self.scores.get(player_id, 0.0) + delta

    def get(self, player_id):
        return self.scores.get(player_id, 0.0)

    def top_suspects(self, k=3):
        return sorted(
            self.scores.items(),
            key=lambda x: x[1],
            reverse=True,
        )[:k]


def generate_memory_summary(memory: AgentMemory):
    suspects = memory.suspicion.top_suspects()

    lines = []
    for pid, score in suspects:
        lines.append(f"{pid}: suspicion {score:.2f}")

    for pid, role in memory.confirmed_roles.items():
        lines.append(f"Confirmed {pid} is {role}")

    return "\n".join(lines)