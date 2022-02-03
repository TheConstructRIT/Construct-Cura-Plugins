"""
Zachary Cook

Registers monitoring changes to printers and materials.
"""

from UM.Logger import Logger
from UM.PluginObject import PluginObject

wrappedOutputDevices = []


def getMetaData():
    """Returns the metadata of the plugin.
    """
    return {}


def register(app):
    """Registers the plugin.
    """

    try:
        from ConstructRIT.Util.AsyncProcedure import AsyncProcedureContext, UIAsyncProcedure

        @UIAsyncProcedure
        def promptPaymentWindow(_, context: AsyncProcedureContext, file_name: str, *args, **kwargs) -> None:
            """Step for prompting a payment window.

            :param context: Procedure context for calling the next steps.
            :param file_name: File name to use.
            :param args: Additional arguments to pass.
            """

            from .src.PaymentWindow import PaymentWindow
            if file_name.endswith(".gcode") or file_name.endswith(".x3g"):
                window = PaymentWindow(file_name)
                window.onCompleted.connect(lambda data: context.end(data[0], *args))
            else:
                context.end(file_name, *args)

        def wrapOutputs() -> None:
            """Wraps the output devices.
            """

            global wrappedOutputDevices
            outputDeviceManager = app.getOutputDeviceManager()
            for output in outputDeviceManager.getOutputDevices():
                outputType = type(output)
                Logger.error(outputType)
                if outputType not in wrappedOutputDevices and hasattr(outputType, "_performWrite"):
                    outputType._performWrite = UIAsyncProcedure(outputType._performWrite)
                    outputType._performWrite.appendFirst(promptPaymentWindow)
                    wrappedOutputDevices.append(outputType)

        def init() -> None:
            """Initializes the plugin after the application starts.
            """

            outputDeviceManager = app.getOutputDeviceManager()
            outputDeviceManager.outputDevicesChanged.connect(wrapOutputs)
            wrapOutputs()

        # Connect the initialization finishing.
        app.initializationFinished.connect(init)

        # Return an empty PluginObject.
        # As of Uranium for Cura 4.13, the plugin will fail to load if there is nothing registered.
        return {
            "empty_object": PluginObject(),
        }
    except ImportError:
        Logger.log("e", "Module missing for loading plugin. Is Construct Core loaded?")
        return {}
