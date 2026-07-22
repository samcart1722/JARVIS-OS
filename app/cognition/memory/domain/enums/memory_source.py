"""
Sources of knowledge for the Cognitive Memory Engine.
"""

from enum import StrEnum


class MemorySource(StrEnum):
    """
    Indicates where a MemoryFact originated.
    """

    USER = "user"
    CONVERSATION = "conversation"
    EXTRACTOR = "extractor"
    SEMANTIC = "semantic"
    SYSTEM = "system"
