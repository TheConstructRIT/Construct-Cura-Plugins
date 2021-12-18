"""
Zachary Cook

Custom window for accepting university ids.
"""

import re
import threading
import time
from PyQt5 import QtWidgets,QtCore
from ..ThreadedMainWindow import ThreadedMainWindow


class LockableBuffer:
    """Lockable buffer class for storing the key presses.
    Can be locked to ignore presses
    """

    def __init__(self, maxSize: int):
        """Creates a Lockable Buffer object.

        :param maxSize: Maximum size of the buffer.
        """

        self.maxSize = maxSize
        self.buffer = []
        self.locked = False

    def append(self, string: str) -> None:
        """Adds a new character or string to the buffer.

        :param string: String to add to the buffer.
        """

        # Add the string if the buffer is not locked.
        if not self.locked:
            self.buffer.append(string)

        # Remove the first string if it is too long.
        if len(self.buffer) > self.maxSize:
            self.buffer.pop(0)

    def lock(self) -> None:
        """Locks the buffer.
        """

        self.locked = True

    def unlock(self) -> None:
        """Unlocks the buffer.
        """

        self.locked = False

    def clear(self) -> None:
        """Clears the buffer.
        """

        self.buffer = []

    def isLocked(self) -> bool:
        """Returns if the buffer is locked.
        """

        return self.locked

    def getBufferString(self) -> str:
        """Returns the buffer concatenated a string.
        """

        # Create the string.
        finalString = ""
        for string in self.buffer:
            finalString += string

        # Return the string.
        return finalString


class SwipeWindow(ThreadedMainWindow):
    """Class for a swipe window.
    """

    onIdEntered = QtCore.pyqtSignal(str)
    onCancelled = QtCore.pyqtSignal()
    openWindows = []

    def __init__(self, windowName: str, initialSizeX: int = 300, initialSizeY: int = 40):
        """Creates the window.

        :param windowName: Name of the window.
        :param initialSizeX: Initial width of the window.
        :param initialSizeY: Initial height of the window.
        """

        super().__init__()

        # Set the window properties.
        screenSize = QtWidgets.QDesktopWidget().screenGeometry(-1)
        self.setGeometry((screenSize.width() - initialSizeX)/2, (screenSize.height() - initialSizeY)/2, initialSizeX, initialSizeY)
        self.setWindowTitle(windowName)

        # Create the widget.
        self.widget = QtWidgets.QWidget()
        self.setCentralWidget(self.widget)
        self.widget.focusOutEvent = self.focusOutEvent

        # Create the buffer.
        self.buffer = LockableBuffer(16)

        # Initialize the UI.
        self.cancelled = False
        self.manualMode = False
        self.initializeSwipeMode()

        # Show the window.
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.raise_()
        self.activateWindow()
        self.show()
        self.widget.setFocus()
        self.openWindows.append(self)

    def focusOutEvent(self, event) -> None:
        """Handles the window being unfocused.
        """

        # Invoked when the focus is lost.
        def focusLost():
            time.sleep(0.25)

            # Close the window and invoke the event if the mode wasn't changed.
            if not self.manualMode and not self.cancelled:
                self.closeThreaded()
                self.cancelled = True
                self.onCancelled.emit()

        # Run the focus lost method in a thread. Does since focus is lost when changing modes.
        if not self.manualMode:
            threading.Thread(target=focusLost).start()

    def closeEvent(self, event) -> None:
        """Handles the window being closed.
        """

        # Invoke the cancelled event.
        if not self.cancelled:
            self.cancelled = True
            self.onCancelled.emit()
        self.openWindows.remove(self)

        # Allow the window to close.
        event.accept()

    def keyPressEvent(self, event) -> None:
        """Handles a key press.
        """

        # Add the character if it has a valid byte code.
        if event.key() < 128:
            self.buffer.append(chr(event.key()))

            # Register the swipe if the id is complete.
            bufferString = self.buffer.getBufferString()
            if len(bufferString) == 16 and bufferString[0] == ";" and bufferString[10] == "=" and bufferString[15] == "?":
                self.handleUniversityId(bufferString)

    def initializeSwipeMode(self) -> None:
        """Sets up the window to use the swipe mode.
        """

        # Create the layouts.
        self.layout = QtWidgets.QVBoxLayout()
        buttonLayout = QtWidgets.QHBoxLayout()

        # Create the elements.
        self.label = QtWidgets.QLabel("Swipe your university id.")
        self.label.setStyleSheet("QLabel {font-weight: 700; font-size: 14px}")
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.modeButton = QtWidgets.QPushButton("Manually enter")
        self.modeButton.setStyleSheet("QPushButton {font-size: 14px}")
        self.modeButton.setFixedSize(120,26)

        # Add the elements.
        self.layout.addWidget(self.label)
        buttonLayout.addWidget(self.modeButton)
        self.layout.addLayout(buttonLayout)

        # Set the widget layout.
        self.widget.setLayout(self.layout)

        # Connect the events.
        self.modeButton.clicked.connect(self.switchMode)

    def initializeManualMode(self):
        """Set up the window to use the manual mode.
        """

        # Create the layouts.
        self.layout = QtWidgets.QVBoxLayout()
        inputLayout = QtWidgets.QHBoxLayout()
        buttonLayout = QtWidgets.QHBoxLayout()

        # Create the elements.
        self.label = QtWidgets.QLabel("Enter your university id.")
        self.label.setStyleSheet("QLabel {font-weight: 700; font-size: 14px}")
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.modeButton = QtWidgets.QPushButton("Swipe Id")
        self.modeButton.setStyleSheet("QPushButton {font-size: 14px}")
        self.modeButton.setFixedSize(120,26)
        inputText = QtWidgets.QLineEdit()
        inputText.setStyleSheet("QLineEdit {font-size: 14px}")
        enterButton = QtWidgets.QPushButton("Enter")
        enterButton.setStyleSheet("QPushButton {font-size: 14px}")
        enterButton.setFixedSize(80,26)

        # Add the elements.
        self.layout.addWidget(self.label)
        buttonLayout.addWidget(self.modeButton)
        inputLayout.addWidget(inputText)
        inputLayout.addWidget(enterButton)
        self.layout.addLayout(inputLayout)
        self.layout.addLayout(buttonLayout)

        # Set the widget layout.
        self.widget.setLayout(self.layout)

        # Connect the events.
        def onEnter(event):
            self.handleUniversityId(inputText.text())
        self.modeButton.clicked.connect(self.switchMode)
        enterButton.clicked.connect(onEnter)

    def switchMode(self) -> None:
        """Switches the mode between swipe and manual.
        """

        # Remove the existing layout.
        QtWidgets.QWidget().setLayout(self.widget.layout())

        # Change the mode.
        if self.manualMode:
            self.manualMode = False
            self.initializeSwipeMode()
        else:
            self.manualMode = True
            self.initializeManualMode()

        # Focus the window.
        self.setFocus()

    def handleUniversityId(self, idString: str) -> None:
        """Processes a string as a university id.

        :param idString: University id to process.
        """

        # Get the ids.
        numbers = re.findall(r"\d+", idString)

        # Emit the event if a valid number is found, or show an error.
        if len(numbers) > 0 and len(numbers[0]) == 9:
            self.onIdEntered.emit(numbers[0])
        elif self.manualMode:
            self.setLabelText("Id is not valid. Expected 9 digits.")

    def setLabelText(self, text: str) -> None:
        """Sets the label text.

        :param text: Message to set for the text.
        """
        self.label.setText(text)



if __name__ == '__main__':
    # Create an app.
    app = QtWidgets.QApplication([])

    # Create a window.
    swipeWindow = SwipeWindow("Enter Id")

    # Connect the test events.
    def onEnter(id):
        print("ID: " + id)
    def onCancel():
        print("CANCEL")
    swipeWindow.onIdEntered.connect(onEnter)
    swipeWindow.onCancelled.connect(onCancel)

    # Run the app.
    app.exec()