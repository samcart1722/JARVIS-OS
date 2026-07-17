from app.language.intents import Intent
from app.language.synonyms import INTENT_SYNONYMS


class IntentMatcher:
    """
    Convierte lenguaje natural
    en Intents internos.
    """

    def match(
        self,
        text: str,
    ) -> Intent:

        best_intent = Intent.GENERAL_CHAT

        best_length = 0

        for intent, phrases in INTENT_SYNONYMS.items():
            for phrase in phrases:
                if phrase in text:
                    if len(phrase) > best_length:
                        best_intent = intent

                        best_length = len(phrase)

        return best_intent
