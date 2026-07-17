import subprocess


class WindowsTool:
    def open_application(self, app: str) -> str:

        app = app.lower()

        applications = {
            "vscode": "code",
            "notepad": "notepad",
            "calculator": "calc",
            "explorer": "explorer",
        }

        if app not in applications:
            return f"No conozco la aplicación: {app}"

        try:
            subprocess.Popen(applications[app])

            return f"{app} abierto correctamente."

        except Exception as e:
            return str(e)
