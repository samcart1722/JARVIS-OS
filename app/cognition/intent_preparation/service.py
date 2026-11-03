"""Non-executing, independently gated local preparation orchestration."""

import asyncio
from dataclasses import dataclass
from enum import Enum
from threading import BoundedSemaphore, Lock
from time import monotonic

from .contracts import IntentPreparationProvider, PreparationProviderUnavailable
from .eligibility import assess_eligibility
from .models import Candidate, EligibilityDecision, ProviderOutcome, ValidationStatus
from .parser import parse_candidate
from .validator import validate_candidate

_OPERATION_SECONDS = 30.0


class PreparationState(str, Enum):
    CANDIDATE_ACCEPTED = "candidate_accepted"
    UNSUPPORTED = "unsupported"
    PROVIDER_UNAVAILABLE = "provider_unavailable"
    PROVIDER_FAILURE = "provider_failure"


@dataclass(frozen=True, slots=True)
class PreparationResult:
    state: PreparationState
    candidate: Candidate | None = None

    def __post_init__(self) -> None:
        if type(self.state) is not PreparationState:
            raise ValueError("Invalid preparation state.")
        accepted = self.state is PreparationState.CANDIDATE_ACCEPTED
        if accepted:
            if (
                type(self.candidate) is not Candidate
                or self.candidate.outcome is not ProviderOutcome.SUPPORTED
            ):
                raise ValueError("Invalid accepted candidate.")
        elif self.candidate is not None:
            raise ValueError("Failure cannot contain a candidate.")

    def to_wire(self) -> dict[str, object]:
        candidate = self.candidate
        return {
            "state": self.state.value,
            "candidate": None
            if candidate is None
            else {
                "intent": candidate.intent.value,
                "fields": dict(candidate.fields),
                "provenance": "local_model_assisted",
            },
        }


class _Attempt:
    """Serialize provider-start permission with terminal finalization.

    The locked queued-to-started transition is the linearization point. A start
    that wins is already admitted work; later cancellation does not release its
    capacity or start another operation. Finalization that wins prevents launch.
    No lock is held across provider I/O.
    """

    def __init__(self, deadline: float) -> None:
        self._deadline = deadline
        self._lock = Lock()
        self._started = False
        self._finalized = False

    def claim_start(self) -> bool:
        with self._lock:
            if self._finalized or self._started:
                return False
            if monotonic() >= self._deadline:
                self._finalized = True
                return False
            self._started = True
            return True

    def finalize(self) -> None:
        with self._lock:
            self._finalized = True

    def finish(self) -> bool:
        with self._lock:
            valid = (
                not self._finalized and self._started and monotonic() < self._deadline
            )
            self._finalized = True
            return valid


class IntentPreparationService:
    """One active operation, no waiting queue and no execution dependencies."""

    def __init__(self, provider: IntentPreparationProvider) -> None:
        self._provider = provider
        self._slot = BoundedSemaphore(1)

    async def prepare(self, text: object) -> PreparationResult:
        deadline = monotonic() + _OPERATION_SECONDS
        if assess_eligibility(text).decision is EligibilityDecision.PROTECTED:
            return PreparationResult(PreparationState.UNSUPPORTED)
        if not self._slot.acquire(blocking=False):
            return PreparationResult(PreparationState.PROVIDER_FAILURE)
        attempt = _Attempt(deadline)
        operation = asyncio.to_thread(self._prepare, text, attempt)
        try:
            task = asyncio.create_task(operation)
        except Exception:
            operation.close()
            attempt.finalize()
            self._slot.release()
            return PreparationResult(PreparationState.PROVIDER_FAILURE)
        # Keep admission until the queued/running callable actually completes.
        # Retrieve its exception even after the requesting coroutine is gone.
        task.add_done_callback(self._worker_done)
        try:
            done, _ = await asyncio.wait(
                {task}, timeout=max(0.0, deadline - monotonic())
            )
            if not done:
                attempt.finalize()
                return PreparationResult(PreparationState.PROVIDER_FAILURE)
            result = task.result()
            if not attempt.finish():
                return PreparationResult(PreparationState.PROVIDER_FAILURE)
            return result
        except TimeoutError:
            attempt.finalize()
            return PreparationResult(PreparationState.PROVIDER_FAILURE)
        except asyncio.CancelledError:
            attempt.finalize()
            raise
        except Exception:
            attempt.finalize()
            return PreparationResult(PreparationState.PROVIDER_FAILURE)

    def _worker_done(self, task: asyncio.Task[PreparationResult]) -> None:
        try:
            if not task.cancelled():
                task.exception()
        finally:
            self._slot.release()

    def _prepare(self, text: str, attempt: _Attempt) -> PreparationResult:
        if not attempt.claim_start():
            return PreparationResult(PreparationState.PROVIDER_FAILURE)
        try:
            candidate = parse_candidate(self._provider.prepare(text))
            if candidate.outcome is ProviderOutcome.UNSUPPORTED:
                return PreparationResult(PreparationState.UNSUPPORTED)
            validated = validate_candidate(candidate, text)
            if validated.status is ValidationStatus.REJECTED:
                return PreparationResult(PreparationState.PROVIDER_FAILURE)
            return PreparationResult(
                PreparationState.CANDIDATE_ACCEPTED, validated.candidate
            )
        except PreparationProviderUnavailable:
            return PreparationResult(PreparationState.PROVIDER_UNAVAILABLE)
        except Exception:
            return PreparationResult(PreparationState.PROVIDER_FAILURE)
