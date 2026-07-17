from app.response.cleaner import ResponseCleaner
from app.response.formatter import ResponseFormatter
from app.response.models import Response
from app.response.validator import ResponseValidator


class ResponseManager:
    """Coordina el procesamiento final de las respuestas del modelo."""

    def process(self, response: Response) -> Response:
        """
        Ejecuta el pipeline completo de procesamiento.

        Flujo:
            1. Limpieza
            2. Validación
            3. Formateo
        """

        cleaned = Response(
            content=ResponseCleaner.clean(response.content),
            response_type=response.response_type,
        )

        validated = ResponseValidator.validate(cleaned)

        formatted = ResponseFormatter.format(validated)

        return formatted