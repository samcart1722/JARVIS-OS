"""CLI for the cross-process durable membership proof."""

import argparse
from collections.abc import Sequence
from pathlib import Path

from app.operations.durable_membership_demo_runtime import (
    seed_durable_membership,
    verify_durable_membership,
)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run durable membership proof.")
    parser.add_argument("phase", choices=("seed", "verify"))
    parser.add_argument("--database", required=True, type=Path)
    args = parser.parse_args(argv)
    title = "Luxiom Durable Actor-Workspace Membership Demo v1"
    try:
        operation = (
            seed_durable_membership
            if args.phase == "seed"
            else verify_durable_membership
        )
        report = operation(args.database)
        print(title)
        print(f"Phase: {report.phase} complete")
        for scenario in report.scenarios:
            print(f"Scenario: {scenario.scenario_id}")
            print(f"Status: {'PASS' if scenario.passed else 'FAIL'}")
            print(f"Result: {scenario.status}")
        print(f"Model calls: {report.model_calls}")
        print(f"Provider calls: {report.provider_calls}")
        print(f"Readiness calls: {report.readiness_calls}")
        print(f"Network calls: {report.network_calls}")
        print(f"Overall: {'PASS' if report.success else 'FAIL'}")
        return 0 if report.success else 1
    except Exception:
        print(title)
        print("Durable membership demo failed safely.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
