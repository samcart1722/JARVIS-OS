"""CLI comparing Sprint 18 and Sprint 19 claim evidence behavior."""

import argparse
from collections.abc import Sequence

from app.cognition.domain.cognitive_outcome import CognitiveOutcome
from app.cognition.memory.scoped.models import MemoryScope, ScopedMemoryRecord
from app.core.config import Settings
from app.core.container import Container
from app.operations.claim_evidence_verification_demo_runtime import (
    VERIFICATION_COMPARISON_COMPLETED,
    ClaimEvidenceVerificationDemoRuntime,
)
from app.operations.demo_records import query_addressable_demo_content


def _non_blank(value: str) -> str:
    if not value.strip():
        raise argparse.ArgumentTypeError("value must not be empty")
    return value


def _settings_for_demo(base: Settings, *, verification_enabled: bool) -> Settings:
    values = base.model_dump()
    values.update(
        {
            "REASONING_ENABLED": True,
            "MEMORY_RETRIEVAL_ENABLED": True,
            "MEMORY_PROMPT_CONTEXT_ENABLED": True,
            "MEMORY_GROUNDED_RESPONSE_ENABLED": True,
            "MEMORY_CLAIM_EVIDENCE_ATTRIBUTION_ENABLED": True,
            "MEMORY_CLAIM_EVIDENCE_VERIFICATION_ENABLED": verification_enabled,
        }
    )
    return Settings(**values, _env_file=None)


def _format(label: str, outcome: CognitiveOutcome) -> str:
    if outcome.success:
        return f"{label}\nSuccess: true\nResponse:\n{outcome.response}"
    if outcome.error is None:
        raise ValueError("Failed outcome requires a safe error.")
    return (
        f"{label}\nSuccess: false\nCode: {outcome.error.code}\n"
        f"Message: {outcome.error.message}"
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compare claim evidence verification.")
    parser.add_argument("--memory-scope", required=True, type=_non_blank)
    parser.add_argument(
        "--memory-record", action="append", required=True, type=_non_blank
    )
    parser.add_argument("prompt", type=_non_blank)
    args = parser.parse_args(argv)
    title = "Luxiom Claim Evidence Support Verification Demo v1"
    try:
        scope = MemoryScope(args.memory_scope)
        records = tuple(
            ScopedMemoryRecord(
                scope, query_addressable_demo_content(args.prompt, content)
            )
            for content in args.memory_record
        )
        base = Settings()
        sprint18 = Container(
            _settings_for_demo(base, verification_enabled=False),
            scoped_memory_records=records,
        )
        sprint19 = Container(
            _settings_for_demo(base, verification_enabled=True),
            scoped_memory_records=records,
        )
        report = ClaimEvidenceVerificationDemoRuntime(
            readiness_probe=sprint18.provider_readiness_probe,
            claim_attributed_engine=sprint18.cognitive_engine,
            verified_engine=sprint19.cognitive_engine,
            memory_scope=scope,
            record_count=len(records),
        ).run(args.prompt)
    except Exception:
        print(title)
        print("-" * len(title))
        print("Demo execution failed safely.")
        return 1
    print(title)
    print("-" * len(title))
    print(f"Provider readiness: {report.readiness.status}")
    print("Explicit memory scope: yes")
    print(f"Ephemeral scoped records: {report.record_count}\n")
    if report.status != VERIFICATION_COMPARISON_COMPLETED:
        print(f"Readiness message: {report.readiness.message}")
        print("No cognitive execution was performed.")
        return 1
    if report.claim_attributed_outcome is None or report.verified_outcome is None:
        raise RuntimeError("Completed report omitted outcomes.")
    print(_format("CLAIM ATTRIBUTION — SPRINT 18", report.claim_attributed_outcome))
    print()
    print(_format("SUPPORT VERIFICATION — SPRINT 19", report.verified_outcome))
    return (
        0
        if report.claim_attributed_outcome.success and report.verified_outcome.success
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
