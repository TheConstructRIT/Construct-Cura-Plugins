"""
Zachary Cook

Main script for the plugin for sandboxing settings.
"""

from UM.Logger import Logger


def getMetaData():
    """Returns the metadata of the plugin.
    """

    return {}


def register(app):
    """Registers the plugin.

    :param app: Instance of the application.
    """

    try:
        # Create the Sandbox Plugin. An ImportError will occur if Construct Core is not set up.
        # The import happens here instead of above so the error for Construct Core can be caught.
        from .src.SandboxPlugin import SandboxPlugin
        return {
            "extension": SandboxPlugin()
        }
    except ImportError:
        # Log that Construct Core may be missing.
        Logger.log("e", "Module missing for loading plugin. Is Construct Core loaded?")
        return {}
