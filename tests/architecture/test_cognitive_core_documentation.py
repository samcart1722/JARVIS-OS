"""Minimum completeness checks for Cognitive Core governance documents."""

from pathlib import Path

ROOT = Path(__file__).parents[2]
DOCUMENTS = {
    "Components.md": (
        "## Purpose",
        "## Canonical active flow",
        "## Component catalog",
        "## Composition Root",
        "## Legacy code",
    ),
    "Contracts.md": (
        "## Orchestration contracts",
        "## Selection contract",
        "## Capability contracts",
        "## Reasoning contracts",
        "## Verified invariants",
    ),
    "Dependency_Rules.md": (
        "## General rule",
        "## API",
        "## Composition Root",
        "## Explicit prohibited imports",
        "## Legacy exclusion",
    ),
}


def document_text(filename: str) -> str:
    path = (
        ROOT
        / "docs/architecture/domains/Cognitive_Core"
        / filename
    )
    assert path.exists(), f"Missing Cognitive Core document: {path}"
    text = path.read_text(encoding="utf-8")
    assert text.strip(), f"Cognitive Core document is empty: {path}"
    return text


def test_governance_documents_contain_essential_sections() -> None:
    for filename, headings in DOCUMENTS.items():
        text = document_text(filename)
        for heading in headings:
            assert heading in text, f"{filename} is missing {heading}"


def test_documents_describe_active_flow_and_infrastructure_boundary() -> None:
    combined = "\n".join(document_text(name) for name in DOCUMENTS)

    for term in (
        "POST /brain/think",
        "CognitiveEngine",
        "CapabilityExecutor",
        "ReasoningProvider",
        "Container",
        "OllamaClient",
        "infrastructure",
        "Legacy",
    ):
        assert term in combined, f"Governance baseline does not mention {term}"
