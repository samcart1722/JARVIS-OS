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

        for intent, phrases in INTENT_SYNONYMS.items():

            for phrase in phrases:

                if phrase in text:

                    return intent

        return Intent.GENERAL_CHAT