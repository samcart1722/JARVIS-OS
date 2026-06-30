from fastapi import APIRouter

from app.brain.brain import Brain

router = APIRouter(
    prefix="/brain",
    tags=["Brain"],
)

brain = Brain()


@router.post("/think")
def think(prompt: str):

    response = brain.think(prompt)

    return {
        "input": prompt,
        "response": response,
    }