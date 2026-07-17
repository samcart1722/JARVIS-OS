from app.response.models import Response


class ResponseFormatter:
    """Aplica el formato final a la respuesta antes de entregarla al usuario."""

    @staticmethod
    def format(response: Response) -> Response:
        """
        Formatea la respuesta según su tipo.

        En esta primera versión no modifica el contenido.
        El objetivo es establecer el punto central donde se
        aplicarán futuras reglas de presentación.
        """

        match response.response_type:
            case _:
                return response
