from app.reflection.models import ReflectionResult, ReflectionStatus


class ReflectionEvaluator:
    """
    Evalúa una respuesta generada
    por el modelo.
    """

    MINIMUM_SCORE = 0.70

    def evaluate(
        self,
        question: str,
        answer: str,
    ) -> ReflectionResult:

        feedback: list[str] = []

        score = 1.0

        if not answer.strip():
            score = 0.0
            feedback.append(
                "La respuesta está vacía.",
            )

        elif len(answer.strip()) < 10:
            score = 0.50
            feedback.append(
                "La respuesta es demasiado corta.",
            )

        if score >= 1.0:
            status = ReflectionStatus.APPROVED

        elif score >= self.MINIMUM_SCORE:
            status = ReflectionStatus.REVIEW

        else:
            status = ReflectionStatus.REJECTED

        return ReflectionResult(
            status=status,
            score=score,
            feedback=feedback,
        )
