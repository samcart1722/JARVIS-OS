from dataclasses import dataclass, field


@dataclass
class Identity:
    name: str = ""

    profession: str = ""

    company: str = ""


@dataclass
class UserProfile:
    identity: Identity = field(default_factory=Identity)

    projects: list[str] = field(default_factory=list)

    preferences: dict = field(default_factory=dict)

    goals: list[str] = field(default_factory=list)
