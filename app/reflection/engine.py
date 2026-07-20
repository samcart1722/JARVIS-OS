from app.reflection.evaluator import ReflectionEvaluator
from app.reflection.models import ReflectionResult


class ReflectionEngine:
    """
    Motor encargado de revisar la calidad
    de las respuestas generadas por JARVIS.
    """

    def __init__(
        self,
    ):

        self.evaluator = ReflectionEvaluator()

    def reflect(
        self,
        question: str,
        answer: str,
    ) -> ReflectionResult:

        return self.evaluator.evaluate(
            question,
            answer,
        )
