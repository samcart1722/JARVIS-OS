class ResponseCleaner:
    """Realiza una limpieza básica sobre la respuesta del modelo."""

    @staticmethod
    def clean(text: str) -> str:
        """
        Limpia espacios innecesarios al inicio y al final.

        En futuras versiones este componente también podrá:
        - eliminar tokens especiales
        - normalizar saltos de línea
        - remover texto oculto del modelo
        """

        return text.strip()
