"""Thin CLI for the local-first family-resolution proof."""

import argparse
from collections.abc import Sequence

from app.operations.local_first_family_demo_runtime import (
    create_local_first_family_demo_runtime,
)


def _non_blank(value: str) -> str:
    if not value.strip():
        raise argparse.ArgumentTypeError("value must not be empty")
    return value


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run local-first list resolution.")
    parser.add_argument("--actor-id", required=True, type=_non_blank)
    parser.add_argument("--workspace-id", required=True, type=_non_blank)
    args = parser.parse_args(argv)
    title = "Luxiom Local-First Family Resolution Demo v1"
    try:
        report = create_local_first_family_demo_runtime(
            args.actor_id, args.workspace_id
        ).run()
        if not all(
            (
                report.initial_add.success,
                report.initial_read.success,
                report.duplicate_add.success,
                report.final_read.success,
                not report.denied_read.success,
                report.denied_list_unchanged,
            )
        ):
            raise ValueError("Local demo scenario was incomplete.")
        print(title)
        print("Scenario completed locally.")
        print("Actor: explicit synthetic demo identity")
        print("Workspace: explicit synthetic demo workspace")
        print(f"Added: {', '.join(report.initial_add.added)}")
        print(f"Duplicate: {', '.join(report.duplicate_add.already_present)}")
        print(f"Final list: {', '.join(report.final_read.items)}")
        print("Denied operation: safe; no disclosure or mutation")
        print(f"Resolution route: {report.final_read.resolution_route}")
        print(f"Model calls: {report.model_calls}")
        print(f"External calls: {report.external_calls}")
        return 0
    except Exception:
        print(title)
        print("Local demo failed safely.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
