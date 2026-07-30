"""CLI adapter for standard versus evidence-bounded memory reasoning."""

import argparse
from collections.abc import Sequence

from app.cognition.domain.cognitive_outcome import CognitiveOutcome
from app.cognition.memory.scoped.models import MemoryScope, ScopedMemoryRecord
from app.core.config import Settings
from app.core.container import Container
from app.operations.demo_records import query_addressable_demo_content
from app.operations.grounded_reasoning_demo_runtime import (
    GROUNDED_COMPARISON_COMPLETED,
    GroundedReasoningDemoRuntime,
)


def _non_blank(value: str) -> str:
    if not value.strip():
        raise argparse.ArgumentTypeError("value must not be empty")
    return value


def _settings_for_grounded_demo(
    base: Settings,
    *,
    grounded_enabled: bool,
) -> Settings:
    values = base.model_dump()
    values.update(
        {
            "REASONING_ENABLED": True,
            "MEMORY_RETRIEVAL_ENABLED": True,
            "MEMORY_PROMPT_CONTEXT_ENABLED": True,
            "MEMORY_GROUNDED_RESPONSE_ENABLED": grounded_enabled,
        }
    )
    return Settings(**values, _env_file=None)


def _format_outcome(label: str, outcome: CognitiveOutcome) -> str:
    if outcome.success:
        return f"{label}\nSuccess: true\nResponse:\n{outcome.response}"
    if outcome.error is None:
        raise ValueError("Failed cognitive outcome requires a safe error.")
    return (
        f"{label}\nSuccess: false\n"
        f"Code: {outcome.error.code}\n"
        f"Message: {outcome.error.message}"
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Compare standard and evidence-bounded memory reasoning."
    )
    parser.add_argument(
        "--memory-scope",
        required=True,
        type=_non_blank,
        help="Explicit opaque scope for ephemeral demo records.",
    )
    parser.add_argument(
        "--memory-record",
        action="append",
        required=True,
        type=_non_blank,
        help="Synthetic scoped record; repeat for multiple records.",
    )
    parser.add_argument(
        "prompt",
        type=_non_blank,
        help="Exact prompt used for both executions.",
    )
    args = parser.parse_args(argv)

    try:
        scope = MemoryScope(args.memory_scope)
        records = tuple(
            ScopedMemoryRecord(
                scope=scope,
                content=query_addressable_demo_content(
                    args.prompt,
                    content,
                ),
            )
            for content in args.memory_record
        )
        base = Settings()
        standard = Container(
            _settings_for_grounded_demo(base, grounded_enabled=False),
            scoped_memory_records=records,
        )
        grounded = Container(
            _settings_for_grounded_demo(base, grounded_enabled=True),
            scoped_memory_records=records,
        )
        report = GroundedReasoningDemoRuntime(
            readiness_probe=standard.provider_readiness_probe,
            standard_engine=standard.cognitive_engine,
            grounded_engine=grounded.cognitive_engine,
            memory_scope=scope,
            record_count=len(records),
        ).run(args.prompt)
    except Exception:
        print("Luxiom Evidence-Bounded Memory Reasoning Demo v1")
        print("-------------------------------------------------")
        print("Demo execution failed safely.")
        return 1

    print("Luxiom Evidence-Bounded Memory Reasoning Demo v1")
    print("-------------------------------------------------")
    print(f"Provider readiness: {report.readiness.status}")
    print(
        "Explicit memory scope: "
        f"{'yes' if report.explicit_scope else 'no'}"
    )
    print(f"Ephemeral scoped records: {report.record_count}")
    print()

    if report.status != GROUNDED_COMPARISON_COMPLETED:
        print(f"Readiness message: {report.readiness.message}")
        print("No cognitive execution was performed.")
        return 1
    if report.standard_outcome is None or report.grounded_outcome is None:
        raise RuntimeError("Completed comparison omitted cognitive outcomes.")
    print(_format_outcome("STANDARD MEMORY-AWARE", report.standard_outcome))
    print()
    print(_format_outcome("EVIDENCE-BOUNDED", report.grounded_outcome))
    return 0 if (
        report.standard_outcome.success
        and report.grounded_outcome.success
    ) else 1


if __name__ == "__main__":
    raise SystemExit(main())
