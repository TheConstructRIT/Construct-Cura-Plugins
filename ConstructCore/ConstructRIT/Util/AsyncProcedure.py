"""
Zachary Cook

Asynchronous steps for simplifying threaded operations.
"""

import threading
from typing import Callable, List, Optional
from PyQt5 import QtCore


class QtAsyncWrapper(QtCore.QObject):
    """Function wrapper for calling functions in the Qt main thread, such as for UI updates.
    """

    runSignal = QtCore.pyqtSignal(dict)

    def __init__(self, function):
        """Creates the wrapper.

        :param function: Function to wrap.
        """

        # Store the function.
        super().__init__()
        self.function = function

        # Connect calling the function.
        self.runSignal.connect(lambda args: self.function(*args["args"], **args["kwargs"]))

    def call(self, *args, **kwargs) -> None:
        """Calls the wrapped function in the main Qt thread.
        """

        self.runSignal.emit({
            "args": args,
            "kwargs": kwargs,
        })


class AsyncProcedureContext:
    """Context for an individual ryn of an async procedure.
    """

    def __init__(self, functions: List[Callable]):
        """Creates the async procedure context.

        :param functions: Functions to call in the context.
        """

        self.functions = functions
        self.selfArgument = None

    def next(self, *args, **kwargs) -> None:
        """Calls the next step of the procedure.
        """

        function = self.functions.pop(0)
        threading.Thread(target=function, args=[self.selfArgument, self, *args], kwargs=kwargs).start()


def AsyncProcedure(function: Optional[Callable] = None) -> Callable:
    """Creates an async procedure container. Can include a base callable as the first step, or can be empty to only
    contain other steps added. Steps of the procedure are not guaranteed to be called as they depend on previous
    steps confirming the next step. The thread they are called from is also not guaranteed unless specified to execute
    in the main thread for updating UI.

    :param function: Optional initial step of the procedure.
    :return: Function to invoke the procedure. A function is used instead of an object with __call__ due to the
    reference to self being lost.
    """

    def asyncProcedureWrapper(self, *args, **kwargs) -> None:
        """Runs the procedure.

        :param self: Reference to self of the object containing the procedure function.
        """

        # Create the procedure context.
        context = AsyncProcedureContext(asyncProcedureWrapper.getFunctions())
        context.selfArgument = self

        # Perform the next (first) step.
        context.next(*args, **kwargs)

    def appendFirst(step: Callable) -> None:
        """Adds a step to the front of the procedure.

        :param step: Step to add. Can either be a function or an AsyncProcedure.
        """

        asyncProcedureWrapper.steps.insert(0, step)

    def appendLast(step: Callable) -> None:
        """Adds a step to the end of the procedure.

        :param step: Step to add. Can either be a function or an AsyncProcedure.
        """

        asyncProcedureWrapper.steps.append(step)

    def getFunctions() -> List[Callable]:
        """Returns the functions to call in order for the procedure.

        :return: A list of functions to call in order.
        """

        # Get the functions to run.
        functions = []
        for step in asyncProcedureWrapper.steps:
            # Either add the child functions if it is an AsyncProcedure, or add the function itself.
            if hasattr(step, "getFunctions"):
                for procedureStep in step.getFunctions():
                    functions.append(procedureStep)
            else:
                functions.append(step)

        # Return the functions.
        return functions

    # Add the methods and attributes to the wrapper.
    asyncProcedureWrapper.appendFirst = appendFirst
    asyncProcedureWrapper.appendLast = appendLast
    asyncProcedureWrapper.getFunctions = getFunctions

    # Add the initial step.
    asyncProcedureWrapper.steps = []
    if function is not None:
        asyncProcedureWrapper.steps.append(function)

    # Return the wrapper.
    return asyncProcedureWrapper


def UIAsyncProcedure(function: Optional[Callable]) -> Callable:
    """Wrapper for AsyncProcedure that specifies the provided callable must be called in the UI thread.

    :param function: Optional initial step of the procedure.
    :return: Function to invoke the procedure. A function is used instead of an object with __call__ due to the
    reference to self being lost.
    """

    return AsyncProcedure(QtAsyncWrapper(function).call)