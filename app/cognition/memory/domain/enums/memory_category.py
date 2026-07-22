"""
Memory categories for the Cognitive Memory Engine.

Each category defines the semantic meaning of a MemoryFact.
These categories are part of JARVIS' ubiquitous language and
must remain stable across the system.
"""

from enum import StrEnum


class MemoryCategory(StrEnum):
    """
    Represents the semantic category of a memory.

    Every MemoryFact belongs to exactly one category.
    """

    PERSONAL = "personal"
    PROJECT = "project"
    PREFERENCE = "preference"
    GOAL = "goal"
    KNOWLEDGE = "knowledge"
    CONVERSATION = "conversation"
    SYSTEM = "system"
