"""
Zachary Cook

Monitors the changes to machines and materials of Cura.
"""

from ConstructRIT import Configuration
from ConstructRIT.UI.Swipe.LabManagerAuthenticationWindow import LabManagerAuthenticationWindow
from typing import List, Optional


class AuthorizationMonitor:
    """Monitors the changes to machines and materials of Cura.
    """

    def __init__(self, app):
        """Creates the authorization monitor.

        :param app: Instance of the Cura app.
        """

        # Store the initial, empty state.
        self.lastMachine = None
        self.lastExtruders = []

        # Connect the app loading.
        # Loading the machine manager before the app loads results in the settings not loading.
        self.app = app
        self.app.initializationFinished.connect(lambda: self._initializationFinished())

    def getMachine(self) -> Optional[str]:
        """Returns the name of the current machine.
        """

        stack = self.app.getMachineManager()._global_container_stack
        if stack is None:
            return None
        return stack.getName()

    def getExtruderMaterials(self) -> List[str]:
        """Returns a list of the names of the materials in the extruders.
        """

        materials = []
        stack = self.app.getMachineManager()._global_container_stack
        if stack is None:
            return materials
        for extruder in self.app.getMachineManager()._global_container_stack.extruderList:
            materials.append(extruder.material.getMetaDataEntry("base_file"))
        return materials

    def _machineChanged(self) -> None:
        """Event listener for the machine changing.
        """

        # Determine the new machine.
        newMachine = self.getMachine()
        if self.lastMachine == newMachine:
            return

        # Return if the new machine is allowed.
        lastMachine = self.lastMachine
        self.lastMachine = newMachine
        if newMachine in Configuration.AUTO_AUTHORIZED_PRINTERS or newMachine is None:
            return

        # Return if job mode is active.
        if self.app.ConstructRIT.currentJobModeUser is not None:
            return

        # Prompt for authorization, and revert the machine change if the authorization failed.
        swipeWindow = LabManagerAuthenticationWindow()
        swipeWindow.onCancelled.connect(lambda: self.app.getMachineManager().setActiveMachine(lastMachine))

    def _materialChanged(self) -> None:
        """Event listener for the material changing.
        """

        # Determine the changed extruder.
        newExtruders = self.getExtruderMaterials()
        changedExtruder = None
        for i in range(0, len(newExtruders)):
            if i < len(self.lastExtruders) and self.lastExtruders[i] != newExtruders[i]:
                changedExtruder = i
                break
        if changedExtruder is None:
            return

        # Return if the changed material is allowed.
        previousMaterialName = self.lastExtruders[changedExtruder]
        self.lastExtruders = newExtruders
        if newExtruders[changedExtruder] in Configuration.AUTO_AUTHORIZED_MATERIALS:
            return

        # Return if job mode is active.
        if self.app.ConstructRIT.currentJobModeUser is not None:
            return

        # Prompt for authorization, and revert the material if the authorization failed.
        swipeWindow = LabManagerAuthenticationWindow()
        swipeWindow.onCancelled.connect(lambda: self.app.getMachineManager().setMaterialById(changedExtruder, previousMaterialName))

    def _initializationFinished(self) -> None:
        """Event listener for Cura initializing.
        """

        # Load the initial state.
        self.lastMachine = self.getMachine()
        self.lastExtruders = self.getExtruderMaterials()

        # Connect the events.
        self.app.getMachineManager().globalContainerChanged.connect(self._machineChanged)
        self.app.getMachineManager().activeMaterialChanged.connect(self._materialChanged)