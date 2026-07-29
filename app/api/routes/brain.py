from fastapi import APIRouter

from app.core.container import container

router = APIRouter(
    prefix="/brain",
    tags=["Brain"],
)

@router.post("/think")
def think(prompt: str):
    response = container.cognitive_engine.process(prompt)

    return {
        "input": prompt,
        "response": response,
    }
