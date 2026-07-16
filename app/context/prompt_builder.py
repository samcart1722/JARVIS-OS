from app.context.models import Context


class PromptBuilder:
    """
    Construye el prompt que será enviado
    al modelo utilizando el contexto.
    """

    def build(
        self,
        context: Context,
        user_input: str,
    ) -> str:

        sections = []

        # ==========================
        # Conversación
        # ==========================

        if context.conversation:

            sections.append(
                "=== Conversación reciente ==="
            )

            for message in context.conversation[-10:]:

                sections.append(
                    f"{message['role']}: {message['content']}"
                )

        # ==========================
        # Memoria
        # ==========================

        if context.memories:

            sections.append(
                "\n=== Memoria ==="
            )

            for memory in context.memories:

                sections.append(str(memory))

        # ==========================
        # Pregunta
        # ==========================

        sections.append(
            "\n=== Solicitud ==="
        )

        sections.append(user_input)

        return "\n".join(sections)