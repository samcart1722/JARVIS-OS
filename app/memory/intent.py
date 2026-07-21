from dataclasses import dataclass, field


@dataclass(slots=True)
class Intent:
    """
    Representa la intención detectada
    en la solicitud del usuario.
    """

    topics: list[str] = field(
        default_factory=list,
    )

    entities: list[str] = field(
        default_factory=list,
    )

    confidence: float = 1.0
