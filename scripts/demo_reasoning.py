"""Command-line adapter for the controlled reasoning demonstration."""

import argparse
from collections.abc import Sequence

from app.cognition.domain.cognitive_outcome import CognitiveOutcome
from app.cognition.memory.scoped.models import MemoryScope, ScopedMemoryRecord
from app.core.config import Settings
from app.core.container import Container
from app.operations.demo_runtime import (
    COMPARISON_SUCCEEDED,
    FunctionalCognitiveDemoRuntime,
)


def _settings_for_demo(
    base: Settings,
    *,
    memory_enabled: bool,
) -> Settings:
    values = base.model_dump()
    values.update(
        {
            "REASONING_ENABLED": True,
            "MEMORY_RETRIEVAL_ENABLED": memory_enabled,
            "MEMORY_PROMPT_CONTEXT_ENABLED": memory_enabled,
        }
    )
    return Settings(**values, _env_file=None)


def _non_blank(value: str) -> str:
    if not value.strip():
        raise argparse.ArgumentTypeError("value must not be empty")
    return value


def _format_outcome(label: str, outcome: CognitiveOutcome) -> str:
    if outcome.success:
        return f"{label}\nSuccess: true\nResponse:\n{outcome.response}"
    if outcome.error is None:
        raise ValueError("Failed cognitive outcome requires a safe error.")
    return (
        f"{label}\nSuccess: false\n"
        f"Error code: {outcome.error.code}\n"
        f"Message: {outcome.error.message}"
    )


def _demo_record_content(prompt: str, content: str) -> str:
    """Create transparent query-addressable content for the literal demo store."""
    return (
        "[DEMO RETRIEVAL KEY]\n"
        f"{prompt}\n\n"
        "[USER-PROVIDED REFERENCE]\n"
        f"{content}"
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Compare Luxiom reasoning with and without scoped memory."
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
        help="Synthetic ephemeral memory record; repeat for multiple records.",
    )
    parser.add_argument(
        "prompt",
        type=_non_blank,
        help="Explicit prompt to process.",
    )
    args = parser.parse_args(argv)

    try:
        scope = MemoryScope(args.memory_scope)
        records = tuple(
            ScopedMemoryRecord(
                scope=scope,
                content=_demo_record_content(args.prompt, content),
            )
            for content in args.memory_record
        )
        base_settings = Settings()
        baseline_container = Container(
            _settings_for_demo(base_settings, memory_enabled=False)
        )
        memory_container = Container(
            _settings_for_demo(base_settings, memory_enabled=True),
            scoped_memory_records=records,
        )
        result = FunctionalCognitiveDemoRuntime(
            readiness_probe=baseline_container.provider_readiness_probe,
            baseline_engine=baseline_container.cognitive_engine,
            memory_engine=memory_container.cognitive_engine,
            memory_scope=scope,
            record_count=len(records),
        ).run(args.prompt)
    except Exception:
        print("Luxiom Functional Cognitive Demo v1")
        print("------------------------------------")
        print("Demo execution failed safely.")
        print("Demo comparison completed: no")
        return 1

    print("Luxiom Functional Cognitive Demo v1")
    print("------------------------------------")
    print(f"Provider readiness: {result.readiness.status}")
    print(
        "Explicit memory scope: "
        f"{'yes' if result.explicit_scope else 'no'}"
    )
    print(f"Ephemeral scoped records: {result.record_count}")
    print()

    if result.status != COMPARISON_SUCCEEDED:
        print(f"Readiness message: {result.readiness.message}")
        print("Cognitive execution performed: no")
        return 1

    if result.baseline_outcome is None or result.memory_outcome is None:
        raise RuntimeError("Ready comparison omitted cognitive outcomes.")
    print(
        _format_outcome(
            "BASELINE — WITHOUT MEMORY CONTEXT",
            result.baseline_outcome,
        )
    )
    print()
    print(
        _format_outcome(
            "MEMORY-AWARE — WITH SCOPED MEMORY CONTEXT",
            result.memory_outcome,
        )
    )
    return 0 if (
        result.baseline_outcome.success and result.memory_outcome.success
    ) else 1


if __name__ == "__main__":
    raise SystemExit(main())
