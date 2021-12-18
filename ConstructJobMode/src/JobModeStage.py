"""
Zachary Cook

Stage for job mode.
"""

import os.path
from cura.CuraApplication import CuraApplication
from cura.Stages.CuraStage import CuraStage
from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSlot, pyqtProperty
from typing import Callable, Dict
from UM.Application import Application
from .JobModeAuthenticationWindow import JobModeAuthenticationWindow


class JobModeStage(CuraStage):
    """Stage for job mode.
    """

    stateChanged = QtCore.pyqtSignal(str)
    _jobModeState = "Job Mode: Inactive"

    def __init__(self, setTabName: Callable[[str], None], parent=None):
        """Creates the stage.

        :param setTabName: Callback for setting the tab name.
        """

        # Set up the stage.
        super().__init__(parent)
        self.setTabName = setTabName
        setTabName(self._jobModeState)

        # Wait until QML engine is created, otherwise creating the new QML components will fail.
        Application.getInstance().engineCreatedSignal.connect(self.onEngineCreated)

    @pyqtProperty(str, notify=stateChanged)
    def jobModeState(self) -> str:
        """Qt property for the state.
        """

        return self._jobModeState

    @jobModeState.setter
    def jobModeState(self, value: str) -> None:
        """Sets the Qt property for the state.

        :param value: Name of the stage to use.
        """

        self._jobModeState = value
        self.stateChanged.emit(value)
        self.setTabName(value)

    def jobModeStartedCallback(self, jobModeUser: Dict) -> None:
        """Callback for job mode being started.

        :param jobModeUser: Job mode user to set.
        """

        app = CuraApplication.getInstance()
        app.ConstructRIT.currentJobModeUser = jobModeUser
        self.jobModeState = "Job Mode: " + app.ConstructRIT.currentJobModeUser["name"]

    @pyqtSlot()
    def onClick(self) -> None:
        """Invoked when the button is clicked.
        """

        app = CuraApplication.getInstance()
        if app.ConstructRIT.currentJobModeUser is not None:
            # De-activate job mode.
            app.ConstructRIT.currentJobModeUser = None
            self.jobModeState = "Job Mode: Inactive"
        else:
            # Prompt to activate job mode.
            authenticationWindow = JobModeAuthenticationWindow()
            authenticationWindow.onAuthenticated.connect(self.jobModeStartedCallback)

    def onEngineCreated(self) -> None:
        """Sets up the Qt components.
        """

        # Register the UI component.
        plugin_path = Application.getInstance().getPluginRegistry().getPluginPath(self.getPluginId())
        if plugin_path is not None:
            Application.getInstance()._qml_engine.rootContext().setContextProperty("JobModeStage", self)
            menu_component_path = os.path.join(plugin_path, "src", "JobModeMenu.qml")
            self.addDisplayComponent("menu", menu_component_path)