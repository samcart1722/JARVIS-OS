"""Text-only local preparation endpoint; no execution or authority ports."""

import json

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.cognition.intent_preparation.models import is_bounded_input
from app.cognition.intent_preparation.service import IntentPreparationService

# JSON escaping can use twelve bytes per supplementary Unicode code point.
_MAX_REQUEST_BYTES = 8192 * 12 + 64


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate key.")
        result[key] = value
    return result


def create_intent_preparation_router(service: IntentPreparationService) -> APIRouter:
    router = APIRouter()

    @router.post("/local/intent-preparation")
    async def prepare_intent(request: Request) -> JSONResponse:
        try:
            body = bytearray()
            async for chunk in request.stream():
                if len(body) + len(chunk) > _MAX_REQUEST_BYTES:
                    raise ValueError("Request too large.")
                body.extend(chunk)
            payload = json.loads(body.decode("utf-8"), object_pairs_hook=_unique_object)
            if (
                type(payload) is not dict
                or set(payload) != {"text"}
                or not is_bounded_input(payload["text"])
            ):
                raise ValueError("Invalid input.")
        except (ValueError, TypeError, RecursionError):
            return JSONResponse(
                status_code=400, content={"state": "unsupported", "candidate": None}
            )
        result = await service.prepare(payload["text"])
        return JSONResponse(content=result.to_wire())

    return router
