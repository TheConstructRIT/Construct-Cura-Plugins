"""
Zachary Cook

Custom window toggling the settings sandbox.
"""

from PyQt5 import QtWidgets,QtCore
from ConstructRIT.UI.ThreadedMainWindow import ThreadedMainWindow


class SandboxConfirmWindow(ThreadedMainWindow):
    """
    Confirm window for enabling or disabling the sandbox.
    """

    onConfirmed = QtCore.pyqtSignal()
    openWindows = []

    def __init__(self, windowName: str, message: str, initialSizeX: int = 300, initialSizeY: int = 40):
        """Creates the window.

        :param windowName: Name of the window.
        :param windowName: Message to display on the window.
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

        # Create the UI.
        layout = QtWidgets.QVBoxLayout()
        buttonLayout = QtWidgets.QHBoxLayout()

        label = QtWidgets.QLabel(message)
        label.setStyleSheet("QLabel {font-weight: 700; font-size: 14px}")
        label.setAlignment(QtCore.Qt.AlignCenter)
        confirmButton = QtWidgets.QPushButton("Yes")
        confirmButton.setStyleSheet("QPushButton {font-size: 14px}")
        confirmButton.setFixedSize(120, 26)
        cancelButton = QtWidgets.QPushButton("No")
        cancelButton.setStyleSheet("QPushButton {font-size: 14px}")
        cancelButton.setFixedSize(120, 26)

        layout.addWidget(label)
        buttonLayout.addWidget(confirmButton)
        buttonLayout.addWidget(cancelButton)
        layout.addLayout(buttonLayout)
        self.widget.setLayout(layout)

        # Connect the events.
        confirmButton.clicked.connect(self.confirmed)
        cancelButton.clicked.connect(self.closeThreaded)

        # Show the window.
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.raise_()
        self.activateWindow()
        self.show()
        self.widget.setFocus()
        self.openWindows.append(self)

    def closeEvent(self, event) -> None:
        """Handles the window being closed.
        """

        self.openWindows.remove(self)
        event.accept()

    def confirmed(self) -> None:
        """Callback for the prompt being confirmed.
        """

        self.onConfirmed.emit()
        self.closeThreaded()