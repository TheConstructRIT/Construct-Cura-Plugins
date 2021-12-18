"""
Zachary Cook

Adds a job mode to top bar.
"""

from UM.Application import Application
from UM.Logger import Logger


# Exposed to allow external name changes.
metaData = {
        "stage": {
            "name": "Job Mode: Inactive",
            "weight": 40
        }
    }


def setTabName(name: str) -> None:
    """Sets the name of the tab.

    :param name: New name for the tab.
    """

    metaData["stage"]["name"] = name
    Application.getInstance().getController().stagesChanged.emit()


def getMetaData():
    """Returns the metadata of the plugin.
    """
    return metaData


def register(app):
    """Registers the plugin.

    :param app: Instance of the application.
    """

    try:
        # Create the Job Mode stage. An ImportError will occur if Construct Core is not set up.
        # The import happens here instead of above so the error for Construct Core can be caught.
        from .src import JobModeStage
        return {
            "stage": JobModeStage.JobModeStage(setTabName)
        }
    except ImportError:
        # Log that Construct Core may be missing.
        Logger.log("e", "Module missing for loading plugin. Is Construct Core loaded?")
        return {}
