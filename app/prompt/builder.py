from app.context.models import Context
from app.prompt.templates import PROMPT_TEMPLATES
from app.prompt.types import PromptType


class PromptBuilder:
    """
    Construye el prompt final que será enviado
    al modelo de lenguaje.
    """

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

        conversation = "\n".join(
            str(item)
            for item in context.conversation
        )

        memories = "\n".join(
            str(item)
            for item in context.memories
        )

        knowledge = "\n".join(
            str(item)
            for item in context.knowledge
        )

        profile = str(context.profile)

        metadata = str(context.metadata)

        return f"""{template}

==============================
CONVERSACIÓN
==============================

{conversation}

==============================
MEMORIAS
==============================

{memories}

==============================
CONOCIMIENTO
==============================

{knowledge}

==============================
PERFIL
==============================

{profile}

==============================
METADATOS
==============================

{metadata}

==============================
SOLICITUD DEL USUARIO
==============================

{user_input}

==============================
RESPUESTA
==============================
"""