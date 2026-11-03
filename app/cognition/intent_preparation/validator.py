"""Provider-independent semantic acceptance; no commands or authority decisions."""

from app.cognition.intent_preparation.grounding import check_grounding, check_roles
from app.cognition.intent_preparation.models import (
    FIELD_ORDER,
    Candidate,
    ProviderOutcome,
    ValidationResult,
    ValidationStatus,
    is_bounded_input,
)


def _rejected(reason: str) -> ValidationResult:
    return ValidationResult(ValidationStatus.REJECTED, reason=reason)


def validate_candidate(candidate: object, original_text: object) -> ValidationResult:
    """Validate semantic data in isolation, not eligibility or provider invocation.

    Complete means only the model-extractable fields are present. In particular,
    it does not mean Capture metadata exists, a command exists or execution is
    authorized. A later orchestrator must independently enforce eligibility.
    """
    if not is_bounded_input(original_text):
        return _rejected("invalid_input")
    if type(candidate) is not Candidate:
        return _rejected("invalid_candidate")
    # Recheck the closed schema rather than trusting a caller's nominal instance.
    try:
        checked = Candidate(candidate.outcome, candidate.intent, candidate.fields)
    except (AttributeError, ValueError, TypeError):
        return _rejected("invalid_candidate")
    if checked.outcome is ProviderOutcome.UNSUPPORTED:
        return _rejected("unsupported")
    error = check_grounding(checked, original_text)
    if error is not None:
        return _rejected(error)
    error = check_roles(checked, original_text)
    if error is not None:
        return _rejected(error)
    present = dict(checked.fields)
    missing = tuple(name for name in FIELD_ORDER[checked.intent] if name not in present)
    status = ValidationStatus.PARTIAL if missing else ValidationStatus.COMPLETE
    return ValidationResult(status, checked, missing)
