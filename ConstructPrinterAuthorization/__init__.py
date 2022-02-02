"""
Zachary Cook

Registers monitoring changes to printers and materials.
"""

from UM.Logger import Logger
from UM.PluginObject import PluginObject


def getMetaData():
    """Returns the metadata of the plugin.
    """
    return {}

def register(app):
    """Registers the plugin.

    :param app: Instance of the application.
    """

    try:
        # Create the Job Mode stage. An ImportError will occur if Construct Core is not set up.
        # The import happens here instead of above so the error for Construct Core can be caught.
        from .src.AuthorizationMonitor import AuthorizationMonitor
        AuthorizationMonitor(app)

        # Return an empty PluginObject.
        # As of Uranium for Cura 4.13, the plugin will fail to load if there is nothing registered.
        return {
            "empty_object": PluginObject(),
        }
    except ImportError:
        # Log that Construct Core may be missing.
        Logger.log("e", "Module missing for loading plugin. Is Construct Core loaded?")
        return {}
