"""CLI for the durable action-permission proof."""

import argparse
from collections.abc import Sequence
from pathlib import Path

from app.operations.durable_action_permission_demo_runtime import (
    seed_durable_action_permission,
    verify_durable_action_permission,
)


def main(
    argv: Sequence[str] | None = None,
) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run durable local action-permission proof."
        )
    )

    parser.add_argument(
        "phase",
        choices=(
            "seed",
            "verify",
        ),
    )

    parser.add_argument(
        "--database",
        required=True,
        type=Path,
    )

    args = parser.parse_args(argv)

    title = (
        "Luxiom Durable Action Permission Demo v1"
    )

    try:
        operation = (
            seed_durable_action_permission
            if args.phase == "seed"
            else verify_durable_action_permission
        )

        report = operation(
            args.database
        )

        print(title)
        print(
            f"Phase: {report.phase}"
        )

        for scenario in report.scenarios:
            print(
                f"Scenario: {scenario.scenario_id}"
            )

            print(
                "Status: "
                f"{'PASS' if scenario.passed else 'FAIL'}"
            )

            print(
                f"Result: {scenario.status}"
            )

            if report.phase == "verify":
                print(
                    "Calls: "
                    f"auth={scenario.authenticator_calls}, "
                    f"map={scenario.mapper_calls}, "
                    "mapping_repository="
                    f"{scenario.mapping_repository_calls}, "
                    f"membership={scenario.membership_calls}, "
                    f"router={scenario.router_calls}, "
                    "permission_repository="
                    f"{scenario.permission_repository_calls}, "
                    f"list_read={scenario.list_read_calls}, "
                    f"list_add={scenario.list_add_calls}, "
                    f"cognitive={scenario.cognitive_calls}"
                )

        print(
            f"Model calls: {report.model_calls}"
        )

        print(
            f"Provider calls: {report.provider_calls}"
        )

        print(
            f"Readiness calls: {report.readiness_calls}"
        )

        print(
            f"Network calls: {report.network_calls}"
        )

        print(
            "Overall: "
            f"{'PASS' if report.success else 'FAIL'}"
        )

        return (
            0
            if report.success
            else 1
        )

    except Exception:
        print(title)

        print(
            "Durable action-permission "
            "demo failed safely."
        )

        return 1


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
