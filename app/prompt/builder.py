from app.context.models import Context
from app.core.logger import logger
from app.prompt.sections.conversation import ConversationSection
from app.prompt.sections.memory import MemorySection
from app.prompt.templates import PROMPT_TEMPLATES
from app.prompt.types import PromptType


class PromptBuilder:
    """
    Construye el prompt final que será enviado
    al modelo de lenguaje.
    """

    def __init__(
        self,
    ) -> None:

        self.sections = [
            ConversationSection(),
            MemorySection(),
        ]

    def build(
        self,
        prompt_type: PromptType,
        context: Context,
        user_input: str,
    ) -> str:

        template = PROMPT_TEMPLATES.get(
            prompt_type,
            PROMPT_TEMPLATES[PromptType.GENERAL],
        )

        parts: list[str] = []

        for section in self.sections:
            block = section.build(
                context,
            )

            if block:
                parts.append(
                    block,
                )

        knowledge = "\n".join(str(item) for item in context.knowledge)

        if knowledge:
            parts.append(
                f"""==============================
CONOCIMIENTO
==============================

{knowledge}"""
            )

        if context.profile:
            parts.append(
                f"""==============================
PERFIL
==============================

{context.profile}"""
            )

        if context.metadata:
            parts.append(
                f"""==============================
METADATOS
==============================

{context.metadata}"""
            )

        parts.append(
            f"""==============================
SOLICITUD DEL USUARIO
==============================

{user_input}"""
        )

        body = "\n\n".join(
            parts,
        )

        prompt = f"""{template}

{body}

==============================
RESPUESTA
==============================
"""
        logger.info(
            "----------------------------------------\n"
            "PROMPT ENVIADO AL LLM\n"
            "{}\n"
            "----------------------------------------",
            prompt,
        )

        return prompt
