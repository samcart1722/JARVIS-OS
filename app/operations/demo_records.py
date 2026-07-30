"""Stable synthetic-record adaptation shared by explicit local demos."""


def query_addressable_demo_content(prompt: str, content: str) -> str:
    """Preserve explicit content while adding a literal demo retrieval key."""
    return (
        "[DEMO RETRIEVAL KEY]\n"
        f"{prompt}\n\n"
        "[USER-PROVIDED REFERENCE]\n"
        f"{content}"
    )
