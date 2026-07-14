from dataclasses import dataclass
from enum import Enum


class ActionType(str, Enum):

    MEMORY = "MEMORY"

    KNOWLEDGE = "KNOWLEDGE"

    TOOL = "TOOL"

    BROWSER = "BROWSER"

    MODEL = "MODEL"


@dataclass
class Decision:

    action: ActionType

    reason: str