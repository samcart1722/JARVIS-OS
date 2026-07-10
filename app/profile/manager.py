from app.profile.models import UserProfile
from app.profile.projects import Projects


class ProfileManager:

    def __init__(self):

        self.profile = UserProfile()

        self.projects = Projects()

    # =====================
    # Actualizar desde Memory
    # =====================

    def update_from_memory(self, item):

        if item.key == "project":
            self.add_project(item.value)

    # =====================
    # Identity
    # =====================

    def set_name(self, name: str):

        self.profile.identity.name = name

    def set_profession(self, profession: str):

        self.profile.identity.profession = profession

    def set_company(self, company: str):

        self.profile.identity.company = company

    # =====================
    # Projects
    # =====================

    def add_project(self, project: str):

        self.projects.add(project)

        self.profile.projects = self.projects.get_all()

    # =====================
    # Preferences
    # =====================

    def set_preference(self, key: str, value: str):

        self.profile.preferences[key] = value

    # =====================
    # Goals
    # =====================

    def add_goal(self, goal: str):

        if goal not in self.profile.goals:
            self.profile.goals.append(goal)

    # =====================
    # Profile
    # =====================

    def get_profile(self):

        return self.profile