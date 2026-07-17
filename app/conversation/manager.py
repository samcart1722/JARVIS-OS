from app.conversation.history import ConversationHistory
from app.conversation.models import Conversation, Message, MessageRole


class ConversationManager:
    DEFAULT_CONTEXT_WINDOW = 20

    def __init__(
        self,
    ):

        self._history = ConversationHistory()

    @property
    def conversation(
        self,
    ) -> Conversation:

        return self._history.conversation

    def add_user_message(
        self,
        content: str,
    ) -> Message:

        return self._history.add(
            MessageRole.USER,
            content,
        )

    def add_assistant_message(
        self,
        content: str,
    ) -> Message:

        return self._history.add(
            MessageRole.ASSISTANT,
            content,
        )

    def add_system_message(
        self,
        content: str,
    ) -> Message:

        return self._history.add(
            MessageRole.SYSTEM,
            content,
        )

    def add_tool_message(
        self,
        content: str,
    ) -> Message:

        return self._history.add(
            MessageRole.TOOL,
            content,
        )

    def messages(
        self,
    ) -> list[Message]:

        return self._history.messages()

    def recent_messages(
        self,
        limit: int = DEFAULT_CONTEXT_WINDOW,
    ) -> list[Message]:

        if limit <= 0:
            return []

        return self._history.messages()[-limit:]

    def last_message(
        self,
    ) -> Message | None:

        return self._history.last()

    def clear(
        self,
    ) -> None:

        self._history.clear()

    def size(
        self,
    ) -> int:

        return self._history.size()
