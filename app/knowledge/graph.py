from collections import defaultdict


class KnowledgeGraph:

    def __init__(self):

        self.graph = defaultdict(set)

    def connect(
        self,
        source: str,
        target: str,
    ):

        self.graph[source].add(target)

        self.graph[target].add(source)

    def related_to(
        self,
        concept: str,
    ):

        return sorted(
            self.graph.get(
                concept,
                set(),
            )
        )

    def all_concepts(self):

        return sorted(
            self.graph.keys()
        )