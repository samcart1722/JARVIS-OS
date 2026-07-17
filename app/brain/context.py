from dataclasses import dataclass, field


@dataclass
class Context:
    user_input: str

    conversation: list = field(default_factory=list)

    memory: dict = field(default_factory=dict)

    metadata: dict = field(default_factory=dict)
