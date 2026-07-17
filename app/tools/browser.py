from typing import List


class BrowserTool:
    def answer(self, question: str) -> str:
        """
        Punto de entrada público del Browser.

        En versiones futuras decidirá automáticamente
        si usar búsqueda web, caché o índice local.
        """

        results = self.search(question)

        if results:
            return results[0]

        return "No encontré información."

    def search(self, query: str) -> List[str]:
        """
        Implementación actual (stub).

        Más adelante será reemplazada por un proveedor real.
        """

        return [f"[Browser] Búsqueda simulada para: {query}"]
