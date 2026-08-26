"""CLI for the durable action-permission revocation proof."""

import argparse
from collections.abc import Sequence
from pathlib import Path

from app.operations.durable_action_permission_revocation_demo_runtime import (
    revoke_durable_action_permission,
    verify_durable_action_permission_revocation,
)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run durable action-permission revocation proof."
        )
    )
    parser.add_argument(
        "phase",
        choices=("revoke", "verify"),
    )
    parser.add_argument(
        "--database",
        required=True,
        type=Path,
    )
    args = parser.parse_args(argv)
    title = (
        "Luxiom Durable Action Permission "
        "Revocation Demo v1"
    )

    try:
        operation = (
            revoke_durable_action_permission
            if args.phase == "revoke"
            else verify_durable_action_permission_revocation
        )
        report = operation(args.database)
        print(title)
        print(f"Phase: {report.phase}")
        for scenario in report.scenarios:
            print(f"Scenario: {scenario.scenario_id}")
            print(
                "Status: "
                f"{'PASS' if scenario.passed else 'FAIL'}"
            )
            print(f"Result: {scenario.status}")
        print(
            "Overall: "
            f"{'PASS' if report.success else 'FAIL'}"
        )
        return 0 if report.success else 1
    except Exception:
        print(title)
        print(
            "Durable action-permission revocation "
            "demo failed safely."
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
