"""Literal grounding and frozen list-role evidence, without command authority."""

import re

from .eligibility import (
    keyword_text,
    quoted_spans,
    recognize_frozen_request,
)
from .models import (
    EDGE_WHITESPACE,
    Candidate,
    Intent,
    is_bounded_input,
    strip_edge_whitespace,
)


def check_grounding(candidate: Candidate, original_text: object) -> str | None:
    """Require every field to preserve a contiguous original text slice."""
    if not is_bounded_input(original_text):
        return "invalid_input"
    for _, value in candidate.fields:
        if not is_bounded_input(value):
            return "invalid_field"
        if strip_edge_whitespace(value) not in original_text:
            return "non_grounded_field"
    return None


def _quoted_overlap(text: str, start: int, end: int) -> bool:
    return any(left < end and right >= start for left, right in quoted_spans(text))


def _destinations(text: str, intent: Intent) -> tuple[tuple[int, int], ...]:
    compared = keyword_text(text)
    pattern = (
        r" a la lista(?= |$)"
        if intent is Intent.ADD_FOLLOW_UP
        else r"(?<![^ ])la lista(?= |$)"
    )
    return tuple(match.span() for match in re.finditer(pattern, compared))


def check_roles(candidate: Candidate, original_text: str) -> str | None:
    """Check frozen roles without inventing a paraphrase vocabulary.

    Closed models restrict Capture/Recall to value/key, respectively. Literal
    grounding is separate; no general Spanish role classifier is claimed.
    Unproven requests remain protected by the independent eligibility gate.
    """
    if not is_bounded_input(original_text):
        return "invalid_input"
    fields = dict(candidate.fields)
    recognized = recognize_frozen_request(strip_edge_whitespace(original_text))
    if recognized == "ambiguous_structure":
        return "ambiguous_destination"
    if recognized is not None:
        # Use only existing frozen recognition evidence, never a new verb corpus.
        if candidate.intent is None or recognized.intent != candidate.intent.value:
            return "wrong_role_field"
        known_fields = dict(recognized.fields)
        if any(
            name not in known_fields
            or value != strip_edge_whitespace(known_fields[name])
            for name, value in candidate.fields
        ):
            return "wrong_role_field"
    if candidate.intent not in (Intent.ADD_FOLLOW_UP, Intent.READ_FOLLOW_UP):
        return None
    list_id = fields.get("list_id")
    item = fields.get("item")
    if list_id is not None and (
        not list_id
        or any(character in EDGE_WHITESPACE for character in list_id)
        or "::" in list_id
    ):
        return "invalid_list_id"
    if item is not None and (not strip_edge_whitespace(item) or "|" in item):
        return "invalid_item"

    source = strip_edge_whitespace(original_text)
    if candidate.intent is Intent.READ_FOLLOW_UP:
        if source.startswith("¿"):
            source = source[1:]
        if source.endswith("?"):
            source = source[:-1]
    destinations = _destinations(source, candidate.intent)
    # Sprint 41 destination ambiguity has no quoted-payload suppression rule.
    generic_suffix = candidate.intent is Intent.ADD_FOLLOW_UP and keyword_text(
        source
    ).endswith(" a mis pendientes")
    if len(destinations) + int(generic_suffix) > 1:
        return "ambiguous_destination"
    if not destinations:
        return "missing_destination_evidence" if list_id is not None else None

    start, end = destinations[0]
    identifier = "" if end == len(source) else strip_edge_whitespace(source[end + 1 :])
    if list_id is not None:
        if not identifier or _quoted_overlap(source, start, len(source)):
            return "missing_destination_evidence"
        if identifier != list_id:
            return "wrong_role_field"
    if item is not None and item not in source[:start]:
        return "wrong_role_field"
    return None
