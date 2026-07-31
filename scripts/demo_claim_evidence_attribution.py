"""CLI comparing Sprint 17 and Sprint 18 evidence protocols."""

import argparse
from collections.abc import Sequence

from app.cognition.domain.cognitive_outcome import CognitiveOutcome
from app.cognition.memory.scoped.models import MemoryScope, ScopedMemoryRecord
from app.core.config import Settings
from app.core.container import Container
from app.operations.claim_evidence_attribution_demo_runtime import (
    CLAIM_COMPARISON_COMPLETED,
    ClaimEvidenceAttributionDemoRuntime,
)
from app.operations.demo_records import query_addressable_demo_content


def _non_blank(value: str) -> str:
    if not value.strip():
        raise argparse.ArgumentTypeError("value must not be empty")
    return value


def _settings_for_claim_demo(base: Settings, *, claim_enabled: bool) -> Settings:
    values = base.model_dump()
    values.update(
        {
            "REASONING_ENABLED": True,
            "MEMORY_RETRIEVAL_ENABLED": True,
            "MEMORY_PROMPT_CONTEXT_ENABLED": True,
            "MEMORY_GROUNDED_RESPONSE_ENABLED": True,
            "MEMORY_CLAIM_EVIDENCE_ATTRIBUTION_ENABLED": claim_enabled,
        }
    )
    return Settings(**values, _env_file=None)


def _format(label: str, outcome: CognitiveOutcome) -> str:
    if outcome.success:
        return f"{label}\nSuccess: true\nResponse:\n{outcome.response}"
    if outcome.error is None:
        raise ValueError("Failed outcome requires safe error.")
    return (
        f"{label}\nSuccess: false\nCode: {outcome.error.code}\n"
        f"Message: {outcome.error.message}"
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compare claim attribution.")
    parser.add_argument("--memory-scope", required=True, type=_non_blank)
    parser.add_argument(
        "--memory-record", action="append", required=True, type=_non_blank
    )
    parser.add_argument("prompt", type=_non_blank)
    args = parser.parse_args(argv)
    title = "Luxiom Claim-Level Evidence Attribution Demo v1"
    try:
        scope = MemoryScope(args.memory_scope)
        records = tuple(
            ScopedMemoryRecord(
                scope, query_addressable_demo_content(args.prompt, content)
            )
            for content in args.memory_record
        )
        base = Settings()
        evidence = Container(
            _settings_for_claim_demo(base, claim_enabled=False),
            scoped_memory_records=records,
        )
        claim = Container(
            _settings_for_claim_demo(base, claim_enabled=True),
            scoped_memory_records=records,
        )
        report = ClaimEvidenceAttributionDemoRuntime(
            readiness_probe=evidence.provider_readiness_probe,
            evidence_bounded_engine=evidence.cognitive_engine,
            claim_attributed_engine=claim.cognitive_engine,
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
    if report.status != CLAIM_COMPARISON_COMPLETED:
        print(f"Readiness message: {report.readiness.message}")
        print("No cognitive execution was performed.")
        return 1
    if (
        report.evidence_bounded_outcome is None
        or report.claim_attributed_outcome is None
    ):
        raise RuntimeError("Completed report omitted outcomes.")
    print(_format("EVIDENCE-BOUNDED — SPRINT 17", report.evidence_bounded_outcome))
    print()
    print(
        _format("CLAIM-LEVEL ATTRIBUTION — SPRINT 18", report.claim_attributed_outcome)
    )
    return (
        0
        if (
            report.evidence_bounded_outcome.success
            and report.claim_attributed_outcome.success
        )
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
