from app.language.normalizer import TextNormalizer
from app.memory.long_term import LongTermMemory
from app.memory.short_term import ShortTermMemory


class MemoryManager:

    def __init__(self):

        self.short_term = ShortTermMemory()

        self.long_term = LongTermMemory()

        self.normalizer = TextNormalizer()

    # ==========================
    # Short Term Memory
    # ==========================

    def remember_conversation(
        self,
        role: str,
        content: str,
    ):

        self.short_term.add(
            role,
            content,
        )

    def conversation(self):

        return self.short_term.get_history()

    def clear_conversation(self):

        self.short_term.clear()

    # ==========================
    # Long Term Memory
    # ==========================

    def remember(
        self,
        key: str,
        value: str,
    ):

        self.long_term.save(
            key,
            value,
        )

    def recall(
        self,
        key: str,
    ):

        return self.long_term.get(key)

    def knowledge(self):

        return self.long_term.all()

    def clear_memory(self):

        self.long_term.clear()

    # ==========================
    # High Level Queries
    # ==========================

    def answer(
        self,
        user_input: str,
    ):

        text = self.normalizer.normalize(
            user_input,
        )

        # --------------------------
        # Proyecto principal
        # --------------------------

        if "proyecto principal" in text:

            project = self.recall(
                "project",
            )

            if project:

                return f"Tu proyecto principal es {project}."

            return "Todavía no conozco tu proyecto principal."

        # --------------------------
        # Lista de proyectos
        # --------------------------

        if "que proyectos tengo" in text:

            project = self.recall(
                "project",
            )

            if project:

                return project

            return "No conozco ningún proyecto registrado."

        return None