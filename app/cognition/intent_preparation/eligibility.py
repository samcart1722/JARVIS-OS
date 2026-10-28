"""Pure Sprint 41 safety parity and conservative Sprint 42 eligibility.

The approved contracts freeze no positive paraphrase-recognition vocabulary.
Consequently every currently decidable input is protected, and otherwise unknown
text remains protected rather than granting model access from a reason string.
"""

import re
from dataclasses import dataclass
from unicodedata import category

from app.cognition.intent_preparation.models import (
    EDGE_WHITESPACE,
    EligibilityDecision,
    EligibilityResult,
    is_bounded_input,
    strip_edge_whitespace,
)

_KEYWORD_TRANSLATION = str.maketrans(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚÜÑ", "abcdefghijklmnopqrstuvwxyzáéíóúüñ"
)
_CONTEXT_WORDS = frozenset(
    ("esto", "eso", "aquello", "ello", "él", "ella", "ellos", "ellas")
)
_CONDITIONAL_WORDS = frozenset(("si", "cuando"))
_MULTIPLE_ACTIONS = re.compile(
    r"( y también | y | luego | después | entonces |; |\. |! |\? |"
    r"\r\n[ \t]*|[\r\n][ \t]*)"
    r"(recuerda|guarda|anota|agrega|añade|agrégalo|añádelo|muéstrame|¿?qué) "
)
_DESTINATIONS = re.compile(r" a la lista | a mis pendientes$")
_PREFIXES = (
    ("recuerda que", "CAPTURE_KNOWLEDGE", "value"),
    ("guarda que", "CAPTURE_KNOWLEDGE", "value"),
    ("anota que", "CAPTURE_KNOWLEDGE", "value"),
    ("qué te dije sobre", "RECALL_KNOWLEDGE", "key"),
    ("qué sabes de", "RECALL_KNOWLEDGE", "key"),
    ("qué hay en la lista", "READ_FOLLOW_UP", "list_id"),
    ("muéstrame la lista", "READ_FOLLOW_UP", "list_id"),
)


def keyword_text(text: str) -> str:
    """Map only the frozen keywords, retaining original code-point positions."""
    return text.translate(_KEYWORD_TRANSLATION)


def _letter_or_number(character: str) -> bool:
    return category(character)[0] in ("L", "N")


def _has_standalone(text: str, words: frozenset[str]) -> bool:
    for word in words:
        start = 0
        while (index := text.find(word, start)) != -1:
            end = index + len(word)
            if (index == 0 or not _letter_or_number(text[index - 1])) and (
                end == len(text) or not _letter_or_number(text[end])
            ):
                return True
            start = index + 1
    return False


def _starts_bounded(text: str, words: tuple[str, ...]) -> bool:
    return any(
        text.startswith(word)
        and (len(text) == len(word) or not _letter_or_number(text[len(word)]))
        for word in words
    )


def quoted_spans(text: str) -> tuple[tuple[int, int], ...]:
    """Return inclusive balanced non-nested double-quote spans as Sprint 41.

    Odd-backslash ASCII quote escapes never delimit a span. Unmatched openers
    remain ordinary text. Quote suppression applies to the action detector only.
    """
    spans: list[tuple[int, int]] = []
    opener: str | None = None
    start = 0
    for index, character in enumerate(text):
        if character == '"':
            slashes = 0
            at = index - 1
            while at >= 0 and text[at] == "\\":
                slashes += 1
                at -= 1
            if slashes % 2:
                continue
        if opener is None and character in ('"', "“"):
            opener = character
            start = index
        elif (opener == '"' and character == '"') or (
            opener == "“" and character == "”"
        ):
            spans.append((start, index))
            opener = None
    return tuple(spans)


def has_multiple_actions(text: str) -> bool:
    """Apply exactly the frozen boundary/introducer lexical guard."""
    compared = keyword_text(text)
    spans = quoted_spans(compared)
    return any(
        not any(match.start() <= right and match.end() > left for left, right in spans)
        for match in _MULTIPLE_ACTIONS.finditer(compared)
    )


@dataclass(frozen=True, slots=True)
class _Recognition:
    """Private recognizer evidence, never a proposal or executable command."""

    intent: str
    fields: tuple[tuple[str, str], ...]


def recognize_frozen_request(text: str) -> _Recognition | str | None:
    """Recognize only Sprint 41's anchored corpus, retaining original slices."""
    compared = keyword_text(text)
    question = text[1:] if compared.startswith("¿") else text
    unwrapped = question[:-1] if question.endswith("?") else question
    for prefix, intent, field in _PREFIXES:
        candidate = unwrapped if prefix.startswith("qué") else text
        lower = keyword_text(candidate)
        if lower == prefix or lower.startswith(prefix + " "):
            payload = candidate[len(prefix) + 1 :]
            trimmed = strip_edge_whitespace(payload)
            if intent == "RECALL_KNOWLEDGE" and (
                trimmed.startswith(("¿", "?")) or trimmed.endswith(("¿", "?"))
            ):
                return None
            return _Recognition(intent, ((field, payload),))
    if keyword_text(unwrapped) == "qué tengo pendiente":
        return _Recognition("READ_FOLLOW_UP", ())
    for prefix in ("agrega ", "añade "):
        if not compared.startswith(prefix):
            continue
        body = text[len(prefix) :]
        lower = keyword_text(body)
        separators = [
            (match.start(), match[0]) for match in _DESTINATIONS.finditer(lower)
        ]
        # Outer edge trimming removes the final separator space for an empty ID.
        if lower.endswith(" a la lista"):
            separators.append((len(lower) - len(" a la lista"), " a la lista"))
        if len(separators) > 1:
            return "ambiguous_structure"
        if len(separators) != 1:
            continue
        index, separator = separators[0]
        item = body[:index]
        if separator == " a mis pendientes":
            return _Recognition("ADD_FOLLOW_UP", (("item", item),))
        return _Recognition(
            "ADD_FOLLOW_UP",
            (("item", item), ("list_id", body[index + len(separator) :])),
        )
    return None


def _recognition_reason(recognized: _Recognition) -> str:
    required = {
        "CAPTURE_KNOWLEDGE": ("value",),
        "RECALL_KNOWLEDGE": ("key",),
        "ADD_FOLLOW_UP": ("item", "list_id"),
        "READ_FOLLOW_UP": ("list_id",),
    }[recognized.intent]
    fields = {name: strip_edge_whitespace(value) for name, value in recognized.fields}
    if any(not fields.get(name) for name in required):
        return "deterministic_clarification"
    list_id = fields.get("list_id")
    if list_id is not None and (
        "::" in list_id or any(character in EDGE_WHITESPACE for character in list_id)
    ):
        return "deterministic_clarification"
    if "|" in fields.get("item", ""):
        return "deterministic_clarification"
    return "deterministic_recognized"


def assess_eligibility(text: object) -> EligibilityResult:
    """Independently protect recognized/safety/unknown input; grant no authority.

    No caller-supplied reason, recognition flag or eligibility assertion is used.
    Positive eligibility needs a separately frozen deterministic rule; the closed
    eligible_unrecognized domain value is intentionally not produced in Block A.
    """
    reason = _protected_reason(text)
    return EligibilityResult(EligibilityDecision.PROTECTED, reason)


def _protected_reason(text: object) -> str:
    if not is_bounded_input(text):
        return "invalid_input"
    assert isinstance(text, str)
    stripped = strip_edge_whitespace(text)
    compared = keyword_text(stripped)
    recognized = recognize_frozen_request(stripped)
    conditional = _has_standalone(compared, _CONDITIONAL_WORDS)
    # Preserve Sprint 41 precedence: recognized conditional payload wins first.
    if isinstance(recognized, _Recognition) and conditional:
        return "conditional_request"
    if _starts_bounded(compared, ("no", "si", "cuando")) or (
        compared.startswith(('"', "“", "por ejemplo:"))
    ):
        return "unsupported_request"
    if has_multiple_actions(compared):
        return "multiple_actions"
    if _has_standalone(compared, _CONTEXT_WORDS):
        return "context_reference"
    if recognized == "ambiguous_structure":
        return "ambiguous_structure"
    if isinstance(recognized, _Recognition):
        return _recognition_reason(recognized)
    if any(
        compared == namespace
        or (
            compared.startswith(namespace)
            and len(compared) > len(namespace)
            and compared[len(namespace)] in EDGE_WHITESPACE
        )
        for namespace in ("knowledge", "list")
    ):
        return "direct_command_namespace"
    # Sprint 42 also protects conditions outside the recognized positive corpus.
    if conditional:
        return "conditional_request"
    return "unproven_paraphrase"
