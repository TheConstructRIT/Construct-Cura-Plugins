"""
Zachary Cook

Swipe window used to load user data.
"""

import threading
import time
from PyQt5 import QtWidgets, QtCore
from ConstructRIT.UI.Swipe.SwipeWindow import SwipeWindow
from ConstructRIT.Util import Http


class ImportUserDataWindow(SwipeWindow):
    """Window for loading user data.
    """

    onImported = QtCore.pyqtSignal([dict], [type(None)])

    def __init__(self):
        """Creates the user data importer window.
        """

        super().__init__("Import")

        # Connect the swipe event.
        self.onIdEntered.connect(self.importDataIdThreaded)

    def importData(self, universityId: str) -> None:
        """Imports the user data.

        :param universityId: University id to import.
        """

        # Set the initial text.
        self.buffer.lock()
        self.setLabelText("Importing data. Please wait...")

        # Import the data.
        try:
            userData = Http.getLastPrintInformation(universityId)
        except IOError:
            self.setLabelText("Error occurred. Try again.")
            self.buffer.unlock()
            return

        # Close the window and invoke the event with the data.
        if userData is None:
            self.setLabelText("No information found.")
            self.cancelled = True
            time.sleep(0.5)
            self.closeThreaded()
            self.onCancelled.emit()
        else:
            self.setLabelText("Information found.")
            self.cancelled = True
            time.sleep(0.5)
            self.closeThreaded()
            self.onImported.emit(userData)

    def importDataIdThreaded(self, universityId: str) -> None:
        """Imports user data in a thread.

        :param universityId: University id to import.
        """

        threading.Thread(target=self.importData, args=[universityId]).start()


if __name__ == '__main__':
    # Create an app.
    app = QtWidgets.QApplication([])

    # Create a window.
    swipeWindow = ImportUserDataWindow()

    # Connect the test events.
    def onImport(data):
        print("IMPORTED: " + str(data))
    def onCancel():
        print("CANCEL")
    swipeWindow.onImported.connect(onImport)
    swipeWindow.onCancelled.connect(onCancel)

    # Run the app.
    app.exec()