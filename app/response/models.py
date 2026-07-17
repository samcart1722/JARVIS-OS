from dataclasses import dataclass
from enum import Enum


class ResponseType(str, Enum):
    """Tipos de respuesta que puede procesar el Response Engine."""

    TEXT = "TEXT"
    MARKDOWN = "MARKDOWN"
    CODE = "CODE"
    JSON = "JSON"
    ERROR = "ERROR"


@dataclass(slots=True)
class Response:
    """Representa una respuesta procesada por el Response Engine."""

    content: str
    response_type: ResponseType = ResponseType.TEXT
