"""
Zachary Cook

Extends QMainWindow to improve threading.
"""

from typing import Callable, Dict
from PyQt5 import QtWidgets, QtCore


class ThreadedMainWindow(QtWidgets.QMainWindow):
    """Class for a threaded main window.
    """

    runThreadedOperationEvent = QtCore.pyqtSignal(dict)

    def __init__(self):
        """Creates the window.
        """

        super().__init__()

        # Connect the event.
        self.runThreadedOperationEvent.connect(self.performOperation)

    def closeThreaded(self) -> None:
        """Closes the window in a thread.
        """

        self.runThreadedOperation(self.close)

    def runThreadedOperation(self, callback: Callable, *args) -> None:
        """Runs a threaded operation.

        :param callback: Function to run in the main thread.
        """

        self.runThreadedOperationEvent.emit({
            "callback": callback,
            "args": args,
        })

    def performOperation(self, dictionary: Dict) -> None:
        """Performs an operation.

        :param dictionary: Internal data of the operation to perform.
        """

        dictionary["callback"](*dictionary["args"])


def ThreadedOperation(func: Callable) -> Callable:
    """Decorator to make a function that is called by a thread.
    This should only be used for changing UI elements and does
    not have yielding.

    :param func: Function to run in the main method.
    """

    def wrapper(*args):
        args[0].runThreadedOperation(func, *args)
    return wrapper


if __name__ == '__main__':
    import threading
    import time

    # Create an app.
    app = QtWidgets.QApplication([])

    # Create a window.
    class customWindow(ThreadedMainWindow):
        def threadTest1(self):
            self.runThreadedOperation(print, "String 1", "String 2")

        @ThreadedOperation
        def threadTest2(self, test):
            print(test)

    mainWindow = customWindow()
    mainWindow.show()
    mainWindow.threadTest1()
    mainWindow.threadTest2("String 3")

    # Run a thread.
    def runThread():
        time.sleep(1)
        mainWindow.closeThreaded()
    threading.Thread(target=runThread).start()

    # Run the app.
    app.exec()