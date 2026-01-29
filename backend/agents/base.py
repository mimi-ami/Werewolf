from abc import ABC, abstractmethod

class BaseAgent(ABC):

    def __init__(self, player_id: str):
        self.player_id = player_id

    @abstractmethod
    def observe(self, event: str):
        pass

    @abstractmethod
    def act(self, phase: str, context: dict | None = None):
        pass
