class Projects:
    def __init__(self):

        self.items = []

    def add(self, project: str):

        if project not in self.items:
            self.items.append(project)

    def get_all(self):

        return self.items
