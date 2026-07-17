from app.conversation.models import Conversation, Message, MessageRole


class ConversationHistory:
    def __init__(self):

        self._conversation = Conversation()

    @property
    def conversation(self) -> Conversation:

        return self._conversation

    def add(
        self,
        role: MessageRole,
        content: str,
    ) -> Message:

        message = Message(
            role=role,
            content=content,
        )

        self._conversation.messages.append(
            message,
        )

        return message

    def clear(self) -> None:

        self._conversation.messages.clear()

    def messages(self) -> list[Message]:

        return list(
            self._conversation.messages,
        )

    def last(
        self,
    ) -> Message | None:

        if not self._conversation.messages:
            return None

        return self._conversation.messages[-1]

    def size(
        self,
    ) -> int:

        return len(
            self._conversation.messages,
        )
