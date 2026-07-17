import re
import unicodedata


class TextNormalizer:
    """
    Convierte cualquier texto de entrada
    a una representación consistente.
    """

    def normalize(
        self,
        text: str,
    ) -> str:

        # Minúsculas
        text = text.lower()

        # Eliminar acentos
        text = unicodedata.normalize(
            "NFD",
            text,
        )

        text = "".join(c for c in text if unicodedata.category(c) != "Mn")

        # Eliminar signos
        text = re.sub(
            r"[^\w\s]",
            "",
            text,
        )

        # Espacios múltiples
        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return text.strip()
