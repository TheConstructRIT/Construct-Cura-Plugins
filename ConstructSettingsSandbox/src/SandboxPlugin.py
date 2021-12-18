"""
Zachary Cook

Plugin class for managing the settings sandbox.
"""

import os
import shutil
from UM.Application import Application
from UM.Extension import Extension
from UM.Resources import Resources
from .State import State
from .SandboxConfirmWindow import SandboxConfirmWindow


# Files and directories that are not stored or updated with the sandbox.
IGNORE_FILES = [
    "plugins",
]


class SandboxPlugin(Extension):
    """Plugin for managing the settings sandbox.
    """

    def __init__(self):
        """Creates the plugin.
        """

        Extension.__init__(self)
        self.state = State()

        # Set up the menu.
        self.setMenuName("Sandbox Settings")
        self.addMenuItem("Toggle Sandbox", self.toggle) # Technical limitation: can't change menu item text, so the status can't be displayed.

        # Replacing the saving method.
        self.originalSavePreferences = Application.savePreferences
        Application.savePreferences = self.savePreferences
        self.replaceSettings()

    def toggle(self) -> None:
        """Requests toggling the sandbox state.
        """

        if self.state.canSaveSettings():
            # Request turning on the settings sandbox.
            confirmWindow = SandboxConfirmWindow("Confirm Enable Sandbox", "Do you want to enable the settings sandbox?\nChanges to settings won't save.")
            confirmWindow.onConfirmed.connect(lambda: self.state.setCanSaveSettings(False))
        else:
            # Request turning off the settings sandbox.
            confirmWindow = SandboxConfirmWindow("Confirm Enable Sandbox", "Do you want to disable the settings sandbox?\nChanges to settings will now save.")
            confirmWindow.onConfirmed.connect(lambda: self.state.setCanSaveSettings(True))

    def copySettings(self, sourceDirectory: str, targetDirectory: str) -> None:
        """Copies the settings files from one location to another.

        :param sourceDirectory: Settings directory to copy from.
        :param targetDirectory: Settings directory to copy to.
        """

        # Create the target directory if it doesn't exist.
        if not os.path.exists(targetDirectory):
            os.makedirs(targetDirectory)

        # Copy the files and directories that aren't ignored (plugins and logs).
        for file in os.listdir(sourceDirectory):
            if file.lower() not in IGNORE_FILES and "cura.log" not in file:
                # Determine the path to copy from and to.
                sourcePath = os.path.join(sourceDirectory, file)
                destinationPath = os.path.join(targetDirectory, file)

                # Replace the destination file or directory.
                if os.path.isfile(sourcePath):
                    if os.path.exists(destinationPath):
                        os.remove(destinationPath)
                    shutil.copy(sourcePath, destinationPath)
                elif os.path.isdir(sourcePath):
                    if os.path.exists(destinationPath):
                        shutil.rmtree(destinationPath)
                    shutil.copytree(sourcePath, destinationPath)

    def storeSettings(self) -> None:
        """Updates the stored sandbox settings from the current settings.
        """

        basePath = os.path.realpath(os.path.join(__file__, "..", "..", "SandboxedSettings"))
        if os.path.exists(basePath):
            shutil.rmtree(basePath)
        self.copySettings(Resources.getConfigStoragePath(), basePath)

    def replaceSettings(self) -> None:
        """Replaces the user settings with the ones stored for sandboxing.
        """

        basePath = os.path.realpath(os.path.join(__file__, "..", "..", "SandboxedSettings"))
        if os.path.exists(basePath):
            self.copySettings(basePath, Resources.getConfigStoragePath())

    def savePreferences(self) -> None:
        """Saves the preferences of the application. Used as a wrapper to store the
        settings if saving the settings (updating the sandbox) is enabled.
        """

        self.originalSavePreferences(Application.getInstance())
        if self.state.canSaveSettings():
            self.storeSettings()