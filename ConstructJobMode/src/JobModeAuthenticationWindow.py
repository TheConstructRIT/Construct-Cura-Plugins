"""
Zachary Cook

Swipe window used to authenticate lab managers
for job mode and import their information.
"""

import threading
import time
from PyQt5 import QtCore
from ConstructRIT.UI.Swipe.SwipeWindow import SwipeWindow
from ConstructRIT.Util import Http


class JobModeAuthenticationWindow(SwipeWindow):
    """Swipe window used to authenticate lab managers
    for job mode and import their information.
    """

    onAuthenticated = QtCore.pyqtSignal(dict)

    def __init__(self):
        """Creates the job mode authentication window.
        """
        super().__init__("Start Job Mode")

        # Connect the swipe event.
        self.onIdEntered.connect(self.authenticateIdThreaded)


    def authenticateId(self, universityId: str) -> None:
        """Authenticates a lab manager.

        :param universityId: University id to authenticate.
        """

        # Set the initial text.
        self.buffer.lock()
        self.setLabelText("Authenticating. Please wait...")

        # Authenticate the id.
        try:
            authorized = Http.isAuthorized(universityId)
        except IOError:
            self.setLabelText("Error occurred. Try again.")
            self.buffer.unlock()
            return

        if authorized:
            # Load the user information.
            self.setLabelText("Importing information. Please wait...")
            try:
                userInformation = Http.getLastPrintInformation(universityId)
            except IOError:
                self.setLabelText("Error occurred. Try again.")
                self.buffer.unlock()
                return
            try:
                name = Http.getName(universityId)
            except IOError:
                self.setLabelText("Error occurred. Try again.")
                self.buffer.unlock()
                return

            # Return if a profile doesn't exist.
            if userInformation is None or name is None:
                self.setLabelText("No user information found.")
                self.buffer.unlock()
                return

            # Authorize the user.
            returnData = {
                "email": userInformation["email"],
                "name": name,
            }
            self.setLabelText("Authorization accepted.")
            self.cancelled = True
            time.sleep(0.5)
            self.closeThreaded()
            self.onAuthenticated.emit(returnData)
        else:
            # Unlock the buffer and display an error.
            self.setLabelText("Authorization failed.")
            self.buffer.unlock()

    def authenticateIdThreaded(self, universityId):
        """Authenticates a lab manager in a thread.

        :param universityId: University id to authenticate.
        """

        threading.Thread(target=self.authenticateId, args=[universityId]).start()