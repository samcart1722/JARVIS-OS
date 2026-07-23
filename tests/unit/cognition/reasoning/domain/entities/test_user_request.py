from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from app.cognition.reasoning.domain.entities.user_request import UserRequest


def test_should_create_valid_user_request() -> None:
    request = UserRequest(
        content="Hello, JARVIS!",
    )

    assert request.content == "Hello, JARVIS!"
    assert request.request_id is not None
    assert request.created_at is not None


def test_should_strip_whitespace() -> None:
    request = UserRequest(
        content="   Hello   ",
    )

    assert request.content == "Hello"


@pytest.mark.parametrize(
    "content",
    [
        "",
        " ",
        "     ",
        "\n",
        "\t",
    ],
)
def test_should_reject_empty_content(content: str) -> None:
    with pytest.raises(ValueError):
        UserRequest(content=content)


def test_should_be_immutable() -> None:
    request = UserRequest(
        content="Hello",
    )

    with pytest.raises(FrozenInstanceError):
        object.__setattr__(request, "content", "Modified")