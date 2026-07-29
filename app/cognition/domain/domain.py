"""Cognitive domain classifications."""

from enum import Enum


class Domain(Enum):
    """Represent the domain associated with a user goal."""

    MEDICAL = "medical"
    BUSINESS = "business"
    EDUCATION = "education"
    LEGAL = "legal"
    PERSONAL = "personal"
    UNKNOWN = "unknown"
