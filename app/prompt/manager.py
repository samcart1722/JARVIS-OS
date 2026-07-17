from app.context.models import Context
from app.prompt.builder import PromptBuilder
from app.prompt.strategy import PromptStrategy
from app.prompt.types import PromptType


class PromptManager:
    """
    Punto de entrada del Prompt Engine.

    Selecciona la estrategia adecuada y construye
    el prompt final que será enviado al modelo.
    """

    def __init__(self):

        self.strategy = PromptStrategy()

        self.builder = PromptBuilder()

    def build_prompt(
        self,
        intent: str,
        context: Context,
        user_input: str,
    ) -> str:

        prompt_type: PromptType = self.strategy.select(
            intent,
        )

        return self.builder.build(
            prompt_type=prompt_type,
            context=context,
            user_input=user_input,
        )