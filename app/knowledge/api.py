from fastapi import APIRouter
from pydantic import BaseModel

from app.knowledge.manager import KnowledgeManager

router = APIRouter(
    prefix="/knowledge",
    tags=["Knowledge"],
)

manager = KnowledgeManager()


class LearnRequest(BaseModel):
    title: str

    content: str

    source: str = "Manual"

    category: str = "General"

    tags: list[str] = []


@router.post("/learn")
def learn(request: LearnRequest):

    unit = manager.learn(
        title=request.title,
        content=request.content,
        source=request.source,
        category=request.category,
        tags=request.tags,
    )

    return {
        "message": "Knowledge stored successfully.",
        "title": unit.title,
        "category": unit.category,
    }


@router.get("/related")
def related(concept: str):

    return {
        "concept": concept,
        "related": manager.related_to(concept),
    }
