from agents.base import BaseAgent

class HumanAgent(BaseAgent):

    def observe(self, event: str):
        pass

    def act(self, phase: str):
        return None  # 等待前端输入
