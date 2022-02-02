"""
Zachary Cook

Adds the classes used by The Construct @ RIT.
"""

import os
import site
from .ConstructRIT import Configuration
from UM.PluginObject import PluginObject


class ConstructState:
    """Empty class for storing the shared state.
    """

    def __init__(self):
        """Creates the state.
        """

        self.currentJobModeUser = None


def getMetaData():
    """Returns the metadata of the plugin.
    """

    return {}


def register(app):
    """Registers the plugin.

    :param app: Instance of the application.
    """

    # Add the shared state.
    app.ConstructRIT = ConstructState()

    # Register the ConstructRIT module.
    site.addsitedir(os.path.realpath(os.path.join(__file__, "..")))

    # Return an empty PluginObject.
    # As of Uranium for Cura 4.13, the plugin will fail to load if there is nothing registered.
    return {
        "empty_object": PluginObject(),
    }
