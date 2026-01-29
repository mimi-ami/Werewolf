from agents.base import BaseAgent

class HumanAgent(BaseAgent):

    def observe(self, event: str):
        pass

    def act(self, phase: str, context: dict | None = None):
        return None  # Await frontend input.
