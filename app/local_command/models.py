"""Public immutable contracts for the authenticated local-command gateway."""
from dataclasses import dataclass, field
from enum import Enum
from typing import NoReturn

WORKSPACE_ID_MAX_LENGTH = 256
LOCAL_COMMAND_TEXT_MAX_LENGTH = 8192


class LocalCommandApplicationRoute(str, Enum):
    LOCAL = "local"
    COGNITIVE = "cognitive"
    SAFE_INSUFFICIENCY = "safe_insufficiency"


class LocalCommandProjectionKind(str, Enum):
    LIST = "list"


class LocalListProjectionOperation(str, Enum):
    ADD = "add"
    READ = "read"


def _projection_list_id(value: object) -> str:
    if type(value) is not str:
        raise ValueError("Projection list ID must be a string.")
    normalized = value.strip()
    if not normalized:
        raise ValueError("Projection list ID must be non-empty.")
    return normalized


def _projection_items(value: object, label: str) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"Projection {label} must be a tuple.")
    if any(type(item) is not str or not item.strip() for item in value):
        raise ValueError(
            f"Projection {label} must contain non-empty strings."
        )
    return value


@dataclass(frozen=True, slots=True)
class LocalListAddProjection:
    list_id: str
    added: tuple[str, ...]
    already_present: tuple[str, ...]
    items: tuple[str, ...]
    kind: LocalCommandProjectionKind = field(
        default=LocalCommandProjectionKind.LIST,
        init=False,
    )
    operation: LocalListProjectionOperation = field(
        default=LocalListProjectionOperation.ADD,
        init=False,
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "list_id", _projection_list_id(self.list_id))
        _projection_items(self.added, "added items")
        _projection_items(self.already_present, "already-present items")
        _projection_items(self.items, "current items")


@dataclass(frozen=True, slots=True)
class LocalListReadProjection:
    list_id: str
    items: tuple[str, ...]
    kind: LocalCommandProjectionKind = field(
        default=LocalCommandProjectionKind.LIST,
        init=False,
    )
    operation: LocalListProjectionOperation = field(
        default=LocalListProjectionOperation.READ,
        init=False,
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "list_id", _projection_list_id(self.list_id))
        _projection_items(self.items, "items")


LocalListProjection = LocalListAddProjection | LocalListReadProjection


class LocalCommandApplicationErrorCode(str, Enum):
    INVALID_REQUEST = "invalid_request"
    ACCESS_DENIED = "access_denied"
    LOCAL_PERMISSION_DENIED = "local_permission_denied"
    LOCAL_VALIDATION_FAILED = "local_validation_failed"
    LOCAL_KNOWLEDGE_NOT_FOUND = "local_knowledge_not_found"
    LOCAL_KNOWLEDGE_CONFLICT = "local_knowledge_conflict"
    COGNITIVE_FALLBACK_NOT_AUTHORIZED = "cognitive_fallback_not_authorized"
    COGNITIVE_REQUEST_FAILED = "cognitive_request_failed"
    SERVICE_UNAVAILABLE = "service_unavailable"
    INTERNAL_ERROR = "internal_error"


_ERROR_MESSAGES = {
    LocalCommandApplicationErrorCode.INVALID_REQUEST: (
        "The request is invalid."
    ),
    LocalCommandApplicationErrorCode.ACCESS_DENIED: (
        "Access denied."
    ),
    LocalCommandApplicationErrorCode.LOCAL_PERMISSION_DENIED: (
        "The local operation is not permitted."
    ),
    LocalCommandApplicationErrorCode.LOCAL_VALIDATION_FAILED: (
        "The local operation could not be completed."
    ),
    LocalCommandApplicationErrorCode.LOCAL_KNOWLEDGE_NOT_FOUND: (
        "The requested local knowledge was not found."
    ),
    LocalCommandApplicationErrorCode.LOCAL_KNOWLEDGE_CONFLICT: (
        "The local knowledge operation conflicts with existing state."
    ),
    LocalCommandApplicationErrorCode.COGNITIVE_FALLBACK_NOT_AUTHORIZED: (
        "Cognitive fallback is not authorized."
    ),
    LocalCommandApplicationErrorCode.COGNITIVE_REQUEST_FAILED: (
        "The cognitive request could not be completed."
    ),
    LocalCommandApplicationErrorCode.SERVICE_UNAVAILABLE: (
        "The requested service is unavailable."
    ),
    LocalCommandApplicationErrorCode.INTERNAL_ERROR: (
        "The request could not be completed."
    ),
}


class LocalCommandApplicationRequest:
    """Immutable secret-aware request without generic dataclass serialization."""

    __slots__ = (
        "_allow_cognitive_fallback",
        "_proof",
        "_requested_workspace_id",
        "_text",
    )

    def __init__(
        self,
        proof: object,
        requested_workspace_id: str,
        text: str,
        allow_cognitive_fallback: bool,
    ) -> None:
        if proof is None:
            raise ValueError("Authentication proof is required.")
        if isinstance(proof, str) and not proof.strip():
            raise ValueError("Authentication proof is required.")

        if type(requested_workspace_id) is not str:
            raise ValueError("Workspace ID must be a string.")
        workspace_id = requested_workspace_id.strip()
        if not workspace_id:
            raise ValueError("Workspace ID must be non-empty.")
        if len(workspace_id) > WORKSPACE_ID_MAX_LENGTH:
            raise ValueError("Workspace ID is too long.")

        if type(text) is not str:
            raise ValueError("Local command text must be a string.")
        if not text.strip():
            raise ValueError("Local command text must be non-empty.")
        if len(text) > LOCAL_COMMAND_TEXT_MAX_LENGTH:
            raise ValueError("Local command text is too long.")

        if type(allow_cognitive_fallback) is not bool:
            raise ValueError(
                "Cognitive fallback authorization must be an explicit boolean."
            )

        object.__setattr__(self, "_proof", proof)
        object.__setattr__(
            self,
            "_requested_workspace_id",
            workspace_id,
        )
        object.__setattr__(self, "_text", text)
        object.__setattr__(
            self,
            "_allow_cognitive_fallback",
            allow_cognitive_fallback,
        )

    def __setattr__(self, name: str, value: object) -> None:
        raise AttributeError(
            "LocalCommandApplicationRequest is immutable."
        )

    def __reduce_ex__(self, protocol: int) -> NoReturn:
        del protocol
        raise TypeError(
            "LocalCommandApplicationRequest serialization is prohibited."
        )

    @property
    def proof(self) -> object:
        return self._proof

    @property
    def requested_workspace_id(self) -> str:
        return self._requested_workspace_id

    @property
    def text(self) -> str:
        return self._text

    @property
    def allow_cognitive_fallback(self) -> bool:
        return self._allow_cognitive_fallback

    def __repr__(self) -> str:
        return (
            "LocalCommandApplicationRequest("
            f"requested_workspace_id={self.requested_workspace_id!r}, "
            f"text={self.text!r}, "
            "allow_cognitive_fallback="
            f"{self.allow_cognitive_fallback!r})"
        )


@dataclass(frozen=True, slots=True)
class LocalCommandApplicationError:
    code: LocalCommandApplicationErrorCode
    message: str

    def __post_init__(self) -> None:
        if type(self.code) is not LocalCommandApplicationErrorCode:
            raise ValueError("Application error code is invalid.")
        expected_message = _ERROR_MESSAGES[self.code]
        if self.message != expected_message:
            raise ValueError("Application error message is not canonical.")


def application_error(
    code: LocalCommandApplicationErrorCode,
) -> LocalCommandApplicationError:
    if type(code) is not LocalCommandApplicationErrorCode:
        raise ValueError("Application error code is invalid.")
    return LocalCommandApplicationError(
        code=code,
        message=_ERROR_MESSAGES[code],
    )


_FAILURE_CODES_BY_ROUTE = {
    None: frozenset(
        (
            LocalCommandApplicationErrorCode.INVALID_REQUEST,
            LocalCommandApplicationErrorCode.ACCESS_DENIED,
            LocalCommandApplicationErrorCode.SERVICE_UNAVAILABLE,
            LocalCommandApplicationErrorCode.INTERNAL_ERROR,
        )
    ),
    LocalCommandApplicationRoute.LOCAL: frozenset(
        (
            LocalCommandApplicationErrorCode.LOCAL_PERMISSION_DENIED,
            LocalCommandApplicationErrorCode.LOCAL_VALIDATION_FAILED,
            LocalCommandApplicationErrorCode.LOCAL_KNOWLEDGE_NOT_FOUND,
            LocalCommandApplicationErrorCode.LOCAL_KNOWLEDGE_CONFLICT,
        )
    ),
    LocalCommandApplicationRoute.COGNITIVE: frozenset(
        (
            LocalCommandApplicationErrorCode.COGNITIVE_REQUEST_FAILED,
        )
    ),
    LocalCommandApplicationRoute.SAFE_INSUFFICIENCY: frozenset(
        (
            LocalCommandApplicationErrorCode.INVALID_REQUEST,
            LocalCommandApplicationErrorCode.COGNITIVE_FALLBACK_NOT_AUTHORIZED,
        )
    ),
}


@dataclass(frozen=True, slots=True)
class LocalCommandApplicationResult:
    success: bool
    route: LocalCommandApplicationRoute | None = None
    response: str | None = None
    error: LocalCommandApplicationError | None = None
    projection: LocalListProjection | None = None

    def __post_init__(self) -> None:
        if type(self.success) is not bool:
            raise ValueError("Application result success must be explicit.")

        if (
            self.route is not None
            and type(self.route) is not LocalCommandApplicationRoute
        ):
            raise ValueError("Application result route is invalid.")

        if self.projection is not None:
            if type(self.projection) not in (
                LocalListAddProjection,
                LocalListReadProjection,
            ):
                raise ValueError("Application result projection is invalid.")
            if (
                not self.success
                or self.route is not LocalCommandApplicationRoute.LOCAL
            ):
                raise ValueError(
                    "Application result projection requires local success."
                )

        if self.success:
            if self.route not in (
                LocalCommandApplicationRoute.LOCAL,
                LocalCommandApplicationRoute.COGNITIVE,
            ):
                raise ValueError(
                    "Successful application result requires a usable route."
                )
            if type(self.response) is not str or not self.response.strip():
                raise ValueError(
                    "Successful application result requires a response."
                )
            if self.error is not None:
                raise ValueError(
                    "Successful application result forbids an error."
                )
            return

        if self.response is not None:
            raise ValueError(
                "Failed application result forbids a response."
            )
        if type(self.error) is not LocalCommandApplicationError:
            raise ValueError(
                "Failed application result requires an application error."
            )

        allowed_codes = _FAILURE_CODES_BY_ROUTE[self.route]
        if self.error.code not in allowed_codes:
            raise ValueError(
                "Application failure route and error are inconsistent."
            )
