"""
Zachary Cook

State for the settings sandbox plugin.
"""

import json
import os


class State:
    """State for the settings sandbox plugin.
    """

    def __init__(self, fileLocation: str = os.path.realpath(os.path.join(__file__, "..", "..", "state.json"))):
        """Creates the state.
        """

        self.fileLocation = fileLocation

        # Load the state if the file exists.
        self.state = None
        if os.path.exists(self.fileLocation):
            with open(self.fileLocation) as file:
                self.state = json.loads(file.read())

        # Correct the state.
        if self.state is None:
            self.state = {}
        if "saveSettings" not in self.state.keys():
            self.state["saveSettings"] = False

    def canSaveSettings(self) -> bool:
        """Returns if the settings can save.
        """

        return self.state["saveSettings"]

    def setCanSaveSettings(self, saveSettings: bool) -> None:
        """Sets if settings can be saved.

        :param saveSettings: Whether the settings can save.
        """

        self.state["saveSettings"] = saveSettings
        self.save()

    def save(self) -> None:
        """Saves the state.
        """

        with open(self.fileLocation, "w") as file:
            file.write(json.dumps(self.state))