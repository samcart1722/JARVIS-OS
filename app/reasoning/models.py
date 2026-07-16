from dataclasses import dataclass, field
from enum import Enum


class ActionType(str, Enum):

    MEMORY = "MEMORY"

    KNOWLEDGE = "KNOWLEDGE"

    TOOL = "TOOL"

    BROWSER = "BROWSER"

    MODEL = "MODEL"


@dataclass
class Decision:

    # Qué módulo debe actuar
    action: ActionType

    # Por qué se tomó la decisión
    reason: str

    # Qué quiere hacer realmente el usuario
    intent: str = "GENERAL"

    # Confianza de la decisión
    confidence: float = 1.0

    # Entidades relevantes detectadas
    entities: list[str] = field(default_factory=list)

    # Información adicional para futuras capacidades
    metadata: dict = field(default_factory=dict)