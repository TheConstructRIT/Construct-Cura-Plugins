"""
Zachary Cook

Swipe window used to authenticate lab managers.
"""

import threading
import time
from PyQt5 import QtWidgets,QtCore
from .SwipeWindow import SwipeWindow
from ...Util import Http



class LabManagerAuthenticationWindow(SwipeWindow):
    """Window for authenticating lab manager ids.
    """

    onAuthenticated = QtCore.pyqtSignal()

    def __init__(self):
        """Creates the lab manager authentication window.
        """

        super().__init__("Authenticate")

        # Connect the swipe event.
        self.onIdEntered.connect(self.authenticateIdThreaded)

    def authenticateId(self, universityId: str) -> None:
        """Authenticates a lab manager.

        :param universityId: University id to attempt to verify.
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

        # Invoke the event and close or unlock the buffer and display an error.
        if authorized:
            self.setLabelText("Authorization accepted.")
            self.cancelled = True
            time.sleep(0.5)
            self.closeThreaded()
            self.onAuthenticated.emit()
        else:
            self.setLabelText("Authorization failed.")
            self.buffer.unlock()

    def authenticateIdThreaded(self, universityId) -> None:
        """Authenticates a lab manager in a thread.

        :param universityId: University id to attempt to verify.
        """

        threading.Thread(target=self.authenticateId, args=[universityId]).start()


if __name__ == '__main__':
    # Create an app.
    app = QtWidgets.QApplication([])

    # Create a window.
    swipeWindow = LabManagerAuthenticationWindow()

    # Connect the test events.
    def onAuthenticate():
        print("AUTHENTICATED")
    def onCancel():
        print("CANCEL")
    swipeWindow.onAuthenticated.connect(onAuthenticate)
    swipeWindow.onCancelled.connect(onCancel)

    # Run the app.
    app.exec()