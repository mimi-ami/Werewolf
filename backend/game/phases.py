from enum import Enum, auto

class Phase(Enum):
    NIGHT = auto()
    DAY = auto()
    VOTE = auto()
    ENDED = auto()
