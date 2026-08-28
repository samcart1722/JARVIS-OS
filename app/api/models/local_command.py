"""Secret-aware HTTP transport models for authenticated local commands."""

from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    SecretStr,
    StrictBool,
    StrictStr,
    field_validator,
)

from app.local_command import (
    LOCAL_COMMAND_TEXT_MAX_LENGTH,
    WORKSPACE_ID_MAX_LENGTH,
)

LocalCommandHttpRoute = Literal[
    "local",
    "cognitive",
    "safe_insufficiency",
]


class LocalCommandHttpListAddProjection(BaseModel):
    """Closed HTTP projection for a successful local list addition."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    kind: Literal["list"] = "list"
    operation: Literal["add"] = "add"
    list_id: str
    added: tuple[str, ...]
    already_present: tuple[str, ...]
    items: tuple[str, ...]


class LocalCommandHttpListReadProjection(BaseModel):
    """Closed HTTP projection for a successful local list read."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    kind: Literal["list"] = "list"
    operation: Literal["read"] = "read"
    list_id: str
    items: tuple[str, ...]


LocalCommandHttpListProjection = Annotated[
    LocalCommandHttpListAddProjection | LocalCommandHttpListReadProjection,
    Field(discriminator="operation"),
]


class LocalCommandHttpRequest(BaseModel):
    """Strict transport request whose authentication proof stays redacted."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    proof: SecretStr
    requested_workspace_id: StrictStr
    text: StrictStr = Field(
        min_length=1,
        max_length=LOCAL_COMMAND_TEXT_MAX_LENGTH,
    )
    allow_cognitive_fallback: StrictBool

    @field_validator("proof", mode="before")
    @classmethod
    def _validate_proof(cls, value: object) -> object:
        if type(value) is not str or not value.strip():
            raise ValueError("Authentication proof is required.")
        return value

    @field_validator("requested_workspace_id")
    @classmethod
    def _normalize_workspace_id(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Workspace ID must be non-empty.")
        if len(normalized) > WORKSPACE_ID_MAX_LENGTH:
            raise ValueError("Workspace ID is too long.")
        return normalized

    @field_validator("text")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Local command text must be non-empty.")
        return value


class LocalCommandHttpError(BaseModel):
    """Closed public error representation for the local-command endpoint."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    code: str
    message: str


class LocalCommandHttpResponse(BaseModel):
    """Stable JSON response envelope for the local-command endpoint."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    success: bool
    route: LocalCommandHttpRoute | None
    response: str | None
    error: LocalCommandHttpError | None
    projection: LocalCommandHttpListProjection | None = None
