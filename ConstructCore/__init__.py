"""
Zachary Cook

Adds the classes used by The Construct @ RIT.
"""

import json
import site
import os
from .ConstructRIT import Configuration


class ConstructState:
    """Empty class for storing the shared state.
    """

    def __init__(self):
        """Creates the state.
        """

        self.currentJobModeUser = None


def replaceConfigurationBindings():
    """Replaces the environment bindings in the configuration.
    """

    # Read the environment file and determine the bindings.
    bindings = {}
    environmentFile = os.path.realpath(os.path.join(__file__, "..", "environment.json"))
    if os.path.exists(environmentFile):
        with open(environmentFile) as file:
            bindings = json.loads(file.read())

    # Replace the configuration bindings.
    for attribute in dir(Configuration):
        if not attribute.startswith("__") and isinstance(getattr(Configuration, attribute), str):
            for binding in bindings.keys():
                setattr(Configuration, attribute, getattr(Configuration, attribute).replace("{ENV/" + binding + "}", bindings[binding]))


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
    replaceConfigurationBindings()
    return {}
