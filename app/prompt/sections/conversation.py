from app.context.models import Context
from app.prompt.formatters.conversation import ConversationFormatter
from app.prompt.sections.base import PromptSection


class ConversationSection(PromptSection):
    """
    Construye la sección de conversación
    del prompt.
    """

    def __init__(
        self,
        formatter: ConversationFormatter | None = None,
    ) -> None:

        self.formatter = formatter or ConversationFormatter()

    def build(
        self,
        context: Context,
    ) -> str:

        return self.formatter.format(
            context.conversation,
        )
