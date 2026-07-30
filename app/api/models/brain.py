"""Public models for the cognitive endpoint."""

from pydantic import BaseModel


class BrainError(BaseModel):
    """Safe public representation of a cognitive failure."""

    code: str
    message: str


class BrainResponse(BaseModel):
    """Stable public response envelope for cognitive requests."""

    success: bool
    prompt: str
    input: str
    response: str | None
    error: BrainError | None
