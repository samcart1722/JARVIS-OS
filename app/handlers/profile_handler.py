from app.core.container import container


class ProfileHandler:

    def __init__(self):

        self.profile = container.profile

    def handle(self):

        profile = self.profile.get_profile()

        if profile.projects:

            return "\n".join(profile.projects)

        return "Todavía no tienes proyectos registrados."