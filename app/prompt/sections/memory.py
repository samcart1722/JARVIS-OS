from app.context.models import Context
from app.prompt.formatters.memory import MemoryFormatter
from app.prompt.sections.base import PromptSection


class MemorySection(PromptSection):
    """
    Construye la sección de memorias
    del prompt.
    """

    def __init__(
        self,
        formatter: MemoryFormatter | None = None,
    ) -> None:

        self.formatter = formatter or MemoryFormatter()

    def build(
        self,
        context: Context,
    ) -> str:

        return self.formatter.format(
            context.memories,
        )
