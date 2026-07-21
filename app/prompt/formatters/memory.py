class MemoryFormatter:
    """
    Formatea la sección de memorias
    del prompt.
    """

    LABELS = {
        "project": "Proyecto principal",
        "profession": "Profesión",
    }

    TITLE = """==============================
MEMORIAS
=============================="""

    def format(
        self,
        memories: list[dict],
    ) -> str:

        if not memories:
            return ""

        lines: list[str] = []

        for memory in memories:
            key = memory.get(
                "key",
                "",
            )

            value = memory.get(
                "value",
                "",
            )

            if not value:
                continue

            label = self.LABELS.get(
                key,
                key.replace(
                    "_",
                    " ",
                ).capitalize(),
            )

            lines.append(f"• {label}: {value}")

        if not lines:
            return ""

        body = "\n".join(
            lines,
        )

        return f"""{self.TITLE}

{body}"""
