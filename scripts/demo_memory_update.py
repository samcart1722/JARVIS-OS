"""CLI adapter for the explicit scoped memory update demonstration."""

import argparse
from collections.abc import Sequence

from app.cognition.domain.cognitive_outcome import CognitiveOutcome
from app.cognition.memory.scoped.models import MemoryScope
from app.core.config import Settings
from app.core.container import Container
from app.operations.demo_records import query_addressable_demo_content
from app.operations.memory_update_demo_runtime import (
    MEMORY_UPDATE_COMPLETED,
    ExplicitMemoryUpdateDemoRuntime,
)


def _non_blank(value: str) -> str:
    if not value.strip():
        raise argparse.ArgumentTypeError("value must not be empty")
    return value


def _settings_for_update_demo(base: Settings) -> Settings:
    values = base.model_dump()
    values.update(
        {
            "REASONING_ENABLED": True,
            "MEMORY_RETRIEVAL_ENABLED": True,
            "MEMORY_PROMPT_CONTEXT_ENABLED": True,
            "MEMORY_UPDATE_ENABLED": True,
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
        f"Error code: {outcome.error.code}\n"
        f"Message: {outcome.error.message}"
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Demonstrate an explicit ephemeral scoped memory update."
    )
    parser.add_argument(
        "--memory-scope",
        required=True,
        type=_non_blank,
        help="Explicit opaque scope for this ephemeral demo.",
    )
    parser.add_argument(
        "--remember",
        action="append",
        required=True,
        type=_non_blank,
        help="Synthetic reference to remember; repeat for multiple records.",
    )
    parser.add_argument(
        "prompt",
        type=_non_blank,
        help="Exact prompt used before and after the explicit update.",
    )
    args = parser.parse_args(argv)

    try:
        scope = MemoryScope(args.memory_scope)
        contents = tuple(
            query_addressable_demo_content(args.prompt, content)
            for content in args.remember
        )
        settings = _settings_for_update_demo(Settings())
        container = Container(settings)
        report = ExplicitMemoryUpdateDemoRuntime(
            readiness_probe=container.provider_readiness_probe,
            cognitive_engine=container.cognitive_engine,
            update_service=container.explicit_memory_update_service,
            memory_scope=scope,
            contents=contents,
        ).run(args.prompt)
    except Exception:
        print("Luxiom Explicit Scoped Memory Update Demo v1")
        print("--------------------------------------------")
        print(f"Records requested: {len(args.remember)}")
        print("Records written: not confirmed")
        print("Demo stopped safely.")
        return 1

    print("Luxiom Explicit Scoped Memory Update Demo v1")
    print("--------------------------------------------")
    print(f"Provider readiness: {report.readiness.status}")
    print(
        "Explicit memory scope: "
        f"{'yes' if report.explicit_scope else 'no'}"
    )
    print(f"Records requested: {report.records_requested}")
    print(f"Records written: {report.records_written}")
    print("Persistence: none")
    print()

    if report.status != MEMORY_UPDATE_COMPLETED:
        print(f"Readiness message: {report.readiness.message}")
        print("Demo stopped safely.")
        print("No cognitive execution or memory update was performed.")
        return 1

    if report.before_outcome is None or report.after_outcome is None:
        raise RuntimeError("Completed update omitted cognitive outcomes.")
    print(
        _format_outcome(
            "BEFORE EXPLICIT MEMORY UPDATE",
            report.before_outcome,
        )
    )
    print()
    print(
        _format_outcome(
            "AFTER EXPLICIT MEMORY UPDATE",
            report.after_outcome,
        )
    )
    return 0 if (
        report.before_outcome.success and report.after_outcome.success
    ) else 1


if __name__ == "__main__":
    raise SystemExit(main())
