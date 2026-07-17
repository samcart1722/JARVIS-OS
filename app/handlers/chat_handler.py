from app.core.container import container


class ChatHandler:
    def __init__(self):

        self.model = container.model

        self.memory = container.memory

    def handle(self, user_input: str):

        response = self.model.chat(user_input)

        self.memory.remember_conversation(
            "assistant",
            response,
        )

        return response
