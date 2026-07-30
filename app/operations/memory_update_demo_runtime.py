"""Operational runtime for an explicit scoped memory update demonstration."""

from dataclasses import dataclass

from app.cognition.domain.cognitive_outcome import CognitiveOutcome
from app.cognition.engine import CognitiveEngine
from app.cognition.memory.scoped.explicit_update import (
    ExplicitMemoryUpdateService,
)
from app.cognition.memory.scoped.models import MemoryScope
from app.operations.provider_readiness import (
    ProviderReadinessProbe,
    ProviderReadinessResult,
)

MEMORY_UPDATE_COMPLETED = "memory_update_completed"
MEMORY_UPDATE_READINESS_FAILED = "readiness_failed"


@dataclass(frozen=True)
class ExplicitMemoryUpdateDemoReport:
    """Safe immutable report for one controlled before/update/after run."""

    status: str
    message: str
    readiness: ProviderReadinessResult
    before_outcome: CognitiveOutcome | None
    after_outcome: CognitiveOutcome | None
    records_requested: int
    records_written: int
    explicit_scope: bool

    def __post_init__(self) -> None:
        if self.records_requested <= 0:
            raise ValueError("Requested record count must be positive.")
        if self.explicit_scope is not True:
            raise ValueError("Memory update demo requires an explicit scope.")
        outcomes_present = (
            self.before_outcome is not None
            and self.after_outcome is not None
        )
        if self.readiness.ready:
            if self.status != MEMORY_UPDATE_COMPLETED:
                raise ValueError("Ready report requires completed status.")
            if not outcomes_present:
                raise ValueError("Completed update requires both outcomes.")
            if self.records_written != self.records_requested:
                raise ValueError(
                    "Completed update must write every requested record."
                )
            return
        if self.status != MEMORY_UPDATE_READINESS_FAILED:
            raise ValueError("Unready report requires readiness-failed status.")
        if outcomes_present or self.before_outcome is not None:
            raise ValueError("Readiness failure cannot contain outcomes.")
        if self.after_outcome is not None or self.records_written != 0:
            raise ValueError(
                "Readiness failure cannot contain writes or outcomes."
            )


class ExplicitMemoryUpdateDemoRuntime:
    """Run readiness, before, explicit writes, and after in strict order."""

    def __init__(
        self,
        *,
        readiness_probe: ProviderReadinessProbe,
        cognitive_engine: CognitiveEngine,
        update_service: ExplicitMemoryUpdateService,
        memory_scope: MemoryScope,
        contents: tuple[str, ...],
    ) -> None:
        if not isinstance(memory_scope, MemoryScope):
            raise TypeError("Memory update demo requires a MemoryScope.")
        if not isinstance(contents, tuple) or not contents:
            raise ValueError("Memory update demo requires explicit contents.")
        if any(
            not isinstance(content, str) or not content.strip()
            for content in contents
        ):
            raise ValueError("Memory update demo contents cannot be empty.")
        self._readiness_probe = readiness_probe
        self._cognitive_engine = cognitive_engine
        self._update_service = update_service
        self._memory_scope = memory_scope
        self._contents = contents

    def run(self, prompt: str) -> ExplicitMemoryUpdateDemoReport:
        """Execute one controlled before/update/after comparison."""
        if not prompt.strip():
            raise ValueError("Demo prompt cannot be empty.")

        readiness = self._readiness_probe.check()
        if not readiness.ready:
            return ExplicitMemoryUpdateDemoReport(
                status=MEMORY_UPDATE_READINESS_FAILED,
                message=f"{readiness.status}: {readiness.message}",
                readiness=readiness,
                before_outcome=None,
                after_outcome=None,
                records_requested=len(self._contents),
                records_written=0,
                explicit_scope=True,
            )

        before = self._cognitive_engine.process(
            prompt,
            memory_scope=self._memory_scope,
        )
        for content in self._contents:
            self._update_service.remember(self._memory_scope, content)
        after = self._cognitive_engine.process(
            prompt,
            memory_scope=self._memory_scope,
        )
        return ExplicitMemoryUpdateDemoReport(
            status=MEMORY_UPDATE_COMPLETED,
            message="Explicit scoped memory update completed.",
            readiness=readiness,
            before_outcome=before,
            after_outcome=after,
            records_requested=len(self._contents),
            records_written=len(self._contents),
            explicit_scope=True,
        )
