class ConversationFormatter:
    """
    Formatea el historial de conversación
    para incluirlo en el prompt.
    """

    TITLE = """==============================
CONVERSACIÓN
=============================="""

    def format(
        self,
        conversation: list[object],
    ) -> str:

        if not conversation:
            return ""

        content = "\n".join(str(item) for item in conversation)

        if not content:
            return ""

        return f"""{self.TITLE}

{content}"""
