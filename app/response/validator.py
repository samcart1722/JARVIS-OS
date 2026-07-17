import json

from app.response.models import Response, ResponseType


class ResponseValidator:
    """Valida respuestas producidas por el modelo."""

    @staticmethod
    def validate(response: Response) -> Response:
        """
        Valida la respuesta según su tipo.

        Actualmente solo valida respuestas JSON.
        """

        if response.response_type is ResponseType.JSON:
            json.loads(response.content)

        return response