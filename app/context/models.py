from dataclasses import dataclass, field


@dataclass
class Context:
    """
    Representa todo el contexto disponible
    para responder una solicitud.
    """

    # Conversación reciente
    conversation: list = field(default_factory=list)

    # Memoria permanente relevante
    memories: list = field(default_factory=list)

    # Conocimiento relacionado
    knowledge: list = field(default_factory=list)

    # Perfil del usuario
    profile: dict = field(default_factory=dict)

    # Información adicional
    metadata: dict = field(default_factory=dict)
