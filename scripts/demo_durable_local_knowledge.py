"""CLI for the cross-process durable local knowledge proof."""

import argparse
from collections.abc import Sequence
from pathlib import Path

from app.operations.durable_local_knowledge_demo_runtime import (
    seed_durable_local_knowledge,
    verify_durable_local_knowledge,
)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run durable local knowledge proof.")
    parser.add_argument("phase", choices=("seed", "verify"))
    parser.add_argument("--database", required=True, type=Path)
    args = parser.parse_args(argv)
    title = "Luxiom Durable Local Knowledge Demo v1"
    try:
        operation = (
            seed_durable_local_knowledge
            if args.phase == "seed"
            else verify_durable_local_knowledge
        )
        report = operation(args.database)
        print(title)
        print(f"Phase: {report.phase} complete")
        print(f"Persisted list: {', '.join(report.list_items)}")
        print("Provenance: preserved exactly")
        if report.phase == "seed":
            print("Durable state: seeded")
        else:
            print("Workspace isolation: verified")
            print("Denied access and mutation: verified")
        print(f"Model calls: {report.model_calls}")
        print(f"External calls: {report.external_calls}")
        print(f"Readiness calls: {report.readiness_calls}")
        print(f"Network calls: {report.network_calls}")
        return 0
    except Exception:
        print(title)
        print("Durable local knowledge demo failed safely.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
