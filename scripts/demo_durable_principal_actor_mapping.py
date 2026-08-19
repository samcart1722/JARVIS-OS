"""CLI for the durable principal-to-actor mapping proof."""

import argparse
from collections.abc import Sequence
from pathlib import Path

from app.operations.durable_principal_actor_mapping_demo_runtime import (
    seed_durable_principal_actor_mapping,
    verify_durable_principal_actor_mapping,
)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run durable principal-to-actor mapping proof."
    )
    parser.add_argument(
        "phase",
        choices=("seed", "verify"),
    )
    parser.add_argument(
        "--database",
        required=True,
        type=Path,
    )
    args = parser.parse_args(argv)

    title = "Luxiom Durable Principal-Actor Mapping Demo v1"

    try:
        operation = (
            seed_durable_principal_actor_mapping
            if args.phase == "seed"
            else verify_durable_principal_actor_mapping
        )

        report = operation(args.database)

        print(title)
        print(f"Phase: {report.phase}")

        for scenario in report.scenarios:
            print(f"Scenario: {scenario.scenario_id}")
            print(
                f"Status: "
                f"{'PASS' if scenario.passed else 'FAIL'}"
            )
            print(f"Result: {scenario.status}")

            if report.phase == "verify":
                print(
                    "Calls: "
                    f"auth={scenario.authenticator_calls}, "
                    f"map={scenario.mapper_calls}, "
                    f"mapping_repository="
                    f"{scenario.mapping_repository_calls}, "
                    f"membership={scenario.membership_calls}, "
                    f"router={scenario.router_calls}, "
                    f"permission={scenario.permission_calls}, "
                    f"capability_repository="
                    f"{scenario.capability_repository_calls}, "
                    f"cognitive={scenario.cognitive_calls}"
                )

        print(f"Model calls: {report.model_calls}")
        print(f"Provider calls: {report.provider_calls}")
        print(f"Readiness calls: {report.readiness_calls}")
        print(f"Network calls: {report.network_calls}")
        print(
            f"Overall: "
            f"{'PASS' if report.success else 'FAIL'}"
        )

        return 0 if report.success else 1

    except Exception:
        print(title)
        print(
            "Durable principal-to-actor mapping "
            "demo failed safely."
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
