"""CLI comparing shared-client and independent-client verification."""

import argparse
from collections.abc import Sequence

from app.cognition.domain.cognitive_outcome import CognitiveOutcome
from app.cognition.memory.scoped.models import MemoryScope, ScopedMemoryRecord
from app.core.config import Settings
from app.core.container import Container
from app.operations.demo_records import query_addressable_demo_content
from app.operations.independent_claim_verifier_demo_runtime import (
    INDEPENDENT_COMPARISON_COMPLETED,
    IndependentClaimVerifierDemoRuntime,
)


def _non_blank(value: str) -> str:
    if not value.strip():
        raise argparse.ArgumentTypeError("value must not be empty")
    return value


def _settings_for_demo(
    base: Settings, *, independent: bool, verifier_model: str | None = None
) -> Settings:
    values = base.model_dump()
    values.update(
        {
            "REASONING_ENABLED": True,
            "MEMORY_RETRIEVAL_ENABLED": True,
            "MEMORY_PROMPT_CONTEXT_ENABLED": True,
            "MEMORY_GROUNDED_RESPONSE_ENABLED": True,
            "MEMORY_CLAIM_EVIDENCE_ATTRIBUTION_ENABLED": True,
            "MEMORY_CLAIM_EVIDENCE_VERIFICATION_ENABLED": True,
            "MEMORY_INDEPENDENT_CLAIM_VERIFIER_ENABLED": independent,
        }
    )
    if verifier_model is not None:
        values["OLLAMA_VERIFIER_MODEL"] = verifier_model
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


def _present(title: str, report) -> int:
    print(title)
    print("-" * len(title))
    print(f"Primary readiness: {report.primary_readiness.status}")
    print(f"Verifier readiness: {report.verifier_readiness.status}")
    print("Explicit memory scope: yes")
    print(f"Ephemeral scoped records: {report.record_count}\n")
    if report.status != INDEPENDENT_COMPARISON_COMPLETED:
        print("No cognitive execution was performed.")
        return 1
    print(_format("SHARED VERIFIER CLIENT — SPRINT 19", report.shared_outcome))
    print()
    print(
        _format(
            "INDEPENDENT VERIFIER CLIENT — SPRINT 20",
            report.independent_outcome,
        )
    )
    return (
        0 if report.shared_outcome.success and report.independent_outcome.success else 1
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compare verifier client roles.")
    parser.add_argument("--memory-scope", required=True, type=_non_blank)
    parser.add_argument(
        "--memory-record", action="append", required=True, type=_non_blank
    )
    parser.add_argument("--verifier-model", type=_non_blank)
    parser.add_argument("prompt", type=_non_blank)
    args = parser.parse_args(argv)
    title = "Luxiom Independent Claim Verifier Demo v1"
    try:
        scope = MemoryScope(args.memory_scope)
        records = tuple(
            ScopedMemoryRecord(
                scope, query_addressable_demo_content(args.prompt, content)
            )
            for content in args.memory_record
        )
        base = Settings()
        shared = Container(
            _settings_for_demo(base, independent=False), scoped_memory_records=records
        )
        independent = Container(
            _settings_for_demo(
                base, independent=True, verifier_model=args.verifier_model
            ),
            scoped_memory_records=records,
        )
        report = IndependentClaimVerifierDemoRuntime(
            primary_probe=shared.provider_readiness_probe,
            verifier_probe=independent.claim_verifier_readiness_probe,
            shared_engine=shared.cognitive_engine,
            independent_engine=independent.cognitive_engine,
            memory_scope=scope,
            record_count=len(records),
        ).run(args.prompt)
        return _present(title, report)
    except Exception:
        print(title)
        print("-" * len(title))
        print("Demo execution failed safely.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
