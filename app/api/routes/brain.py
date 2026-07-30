from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.api.models.brain import BrainError, BrainResponse
from app.cognition.domain.cognitive_outcome import (
    CAPABILITY_EXECUTION_FAILED,
    CAPABILITY_NOT_FOUND,
    EMPTY_CAPABILITY_OUTPUT,
    GROUNDED_RESPONSE_PROTOCOL_INVALID,
)
from app.core.container import container

router = APIRouter(
    prefix="/brain",
    tags=["Brain"],
)


_HTTP_STATUS_BY_ERROR_CODE = {
    CAPABILITY_NOT_FOUND: 500,
    CAPABILITY_EXECUTION_FAILED: 503,
    EMPTY_CAPABILITY_OUTPUT: 503,
    GROUNDED_RESPONSE_PROTOCOL_INVALID: 503,
}


@router.post("/think")
def think(prompt: str) -> JSONResponse:
    outcome = container.cognitive_engine.process(prompt)
    error = (
        BrainError(code=outcome.error.code, message=outcome.error.message)
        if outcome.error
        else None
    )
    payload = BrainResponse(
        success=outcome.success,
        prompt=prompt,
        input=prompt,
        response=outcome.response,
        error=error,
    )
    status_code = (
        200
        if outcome.success
        else _HTTP_STATUS_BY_ERROR_CODE[outcome.error.code]
    )
    return JSONResponse(
        status_code=status_code,
        content=payload.model_dump(),
    )
