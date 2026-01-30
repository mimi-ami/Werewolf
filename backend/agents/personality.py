from dataclasses import dataclass

@dataclass
class Personality:
    aggressiveness: float = 0.5
    deception: float = 0.5
    logic: float = 0.5
    tone: str = "neutral"
    quirk: str = ""
