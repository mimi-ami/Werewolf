from agents.base import BaseAgent
from agents.memory import AgentMemory
from agents.personality import Personality
from agents.prompts import (
    SYSTEM_PROMPT,
    WEREWOLF_PROMPT,
    SEER_PROMPT,
    VILLAGER_PROMPT,
)
from agents.prompts.runtime import build_runtime_prompt
from agents.prompts.werewolf_night import build_wolf_night_prompt
from llm.client import call_llm

ROLE_PROMPT_MAP = {
    "WEREWOLF": WEREWOLF_PROMPT,
    "SEER": SEER_PROMPT,
    "VILLAGER": VILLAGER_PROMPT,
}

class AIAgent(BaseAgent):

    def __init__(self, player_id: str, role, personality: Personality | None = None, memory: AgentMemory | None = None):
        super().__init__(player_id)
        self.role = role
        self.memory = memory or AgentMemory()
        self.personality = personality or Personality()
        self.vote_history = []
        self.last_vote = None
        self.wolf_team = set()

    def observe(self, event: str):
        self.memory.add_event(event)

    def act(self, phase):
        role_prompt = ROLE_PROMPT_MAP.get(self.role.name, "")
        phase_prompt = self._get_phase_prompt(phase)

        prompt = build_runtime_prompt(
            SYSTEM_PROMPT,
            role_prompt,
            phase_prompt,
            self.memory.summary(),
            self.memory.visible_events(),
            self.personality,
        )

        result = call_llm(prompt)
        return result

    def _get_phase_prompt(self, phase):
        # Keep this minimal until phase-specific prompts are added.
        if hasattr(phase, "name"):
            return f"Current phase: {phase.name}"
        return f"Current phase: {phase}"

    def wolf_night_action(self, wolf_channel):
        prompt = build_wolf_night_prompt(
            wolves=wolf_channel.memory.wolves,
            night_summary=wolf_channel.get_context(),
            alive_players=list(self.memory.alive_players),
        )

        response = call_llm(prompt)

        if "speech" in response:
            wolf_channel.broadcast(
                self.player_id,
                response["speech"],
            )

        action = response.get("action", {}) if isinstance(response, dict) else {}
        return action.get("kill")