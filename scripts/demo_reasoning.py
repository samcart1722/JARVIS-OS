"""Command-line adapter for the controlled reasoning demonstration."""

import argparse

from app.core.config import Settings
from app.core.container import Container
from app.operations.demo_runtime import ReasoningDemoRuntime


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Luxiom reasoning demo.")
    parser.add_argument("prompt", help="Explicit prompt to process.")
    args = parser.parse_args()

    settings = Settings()
    container = Container(settings)
    result = ReasoningDemoRuntime(
        reasoning_enabled=settings.REASONING_ENABLED,
        readiness_probe=container.provider_readiness_probe,
        cognitive_engine=container.cognitive_engine,
    ).run(args.prompt)
    print(f"{result.status}: {result.message}")
    return 0 if result.status == "cognitive_succeeded" else 1


if __name__ == "__main__":
    raise SystemExit(main())
