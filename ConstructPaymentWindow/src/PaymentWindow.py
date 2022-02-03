"""
Zachary Cook

Prompt for user information.
"""

import math
import ntpath
import os
import threading
import time
from PyQt5 import QtWidgets,QtCore
from cura.CuraApplication import CuraApplication
from ConstructRIT import Configuration
from ConstructRIT.UI.ThreadedMainWindow import ThreadedMainWindow, ThreadedOperation
from ConstructRIT.UI.Swipe.LabManagerAuthenticationWindow import LabManagerAuthenticationWindow
from ConstructRIT.Util import Http
from ConstructRIT.Util.AsyncProcedure import AsyncProcedureContext, AsyncProcedure, UIAsyncProcedure
from typing import Optional
from .ImportUserDataWindow import ImportUserDataWindow
from .PrintTimeUtil import getPrintLengthError, getLastPrintTimeError


class PaymentWindow(ThreadedMainWindow):
    """Payment window used for logging prints.
    """

    onCompleted = QtCore.pyqtSignal(list)
    onClose = QtCore.pyqtSignal()
    onSubmitStateChanged = QtCore.pyqtSignal(dict)

    def __init__(self, printLocation: str, printWeight: Optional[float] = None, printTimeHours: Optional[float] = None, printMaterial: Optional[str] = None, printVolume: Optional[str] = None):
        """Creates the window.

        :param printLocation: Location to save the print.
        :param printWeight: Weight of the print.
        :param printTimeHours: Duration in hours of the print.
        :param printMaterial: Material of the print.
        :param printVolume: Volume of the print.
        """

        super().__init__()

        # Set the values from Cura they aren't specified.
        if printWeight is None:
            printWeight = 0
            for weightList in CuraApplication.getInstance().getPrintInformation()._material_weights.values():
                for weight in weightList:
                    printWeight += weight
        if printTimeHours is None:
            printTimeHours = 0
            for duraction in CuraApplication.getInstance().getPrintInformation()._current_print_time.values():
                printTimeHours += int(duraction)/(60 * 60)
        if printMaterial is None:
            for extruder in CuraApplication.getInstance().getMachineManager()._global_container_stack.extruders.values():
                printMaterial = extruder.material.getName()
                break
        if printVolume is None:
            app = CuraApplication.getInstance()
            printVolume = "{:,.1f} (L) x {:,.1f} (W) x {:,.1f} (H)".format(app._scene_bounding_box.width.item(),app._scene_bounding_box.depth.item(),app._scene_bounding_box.height.item())

        # Truncate the file name if it is too long.
        printName = ntpath.basename(printLocation)
        directoryLocation = ntpath.dirname(printLocation)
        curaApplication = CuraApplication.getInstance()
        if curaApplication is not None:
            machineName = curaApplication.getMachineManager()._global_container_stack.getName()
        else:
            machineName = "[Test Machine]"
        if machineName in Configuration.MAX_FILE_NAME_LENGTHS.keys() and len(printName) > Configuration.MAX_FILE_NAME_LENGTHS[machineName]:
            fileTypeIndex = printName.rfind(".")
            printName = printName[0:Configuration.MAX_FILE_NAME_LENGTHS[machineName] - (len(printName) - fileTypeIndex)] + printName[fileTypeIndex:]
            printLocation = os.path.join(directoryLocation,printName)
        self.fileLocation = printLocation

        # Get the print weight as a string.
        printWeight = math.ceil(printWeight)
        if printWeight == 1:
            printWeightString = "1 gram"
        else:
            printWeightString = str(printWeight) + " grams"

        # Store the print information.
        self.machineName = machineName
        self.printLocation = printLocation
        self.printName = printName
        self.printWeight = printWeight
        self.printTimeHours = printTimeHours
        self.printMaterial = printMaterial
        self.printCost = printWeight * Configuration.PRINT_COST_PER_GRAM
        self.formattedPrintCost = "${:,.2f}".format(self.printCost)
        self.printVolume = printVolume
        self.ignorePayment = False
        self.ignoreTime = False

        # Set the window properties.
        initialSizeX, initialSizeY = 500, 420
        screenSize = QtWidgets.QDesktopWidget().screenGeometry(-1)
        self.setGeometry(int((screenSize.width() - initialSizeX)/2), int((screenSize.height() - initialSizeY)/2), initialSizeX, initialSizeY)
        self.setWindowTitle("Export Print")

        # Create the widget.
        self.widget = QtWidgets.QWidget()
        self.setCentralWidget(self.widget)

        # Initialize the UI.
        self.cancelled = False
        self.currentTransaction = 0
        self.layout = QtWidgets.QVBoxLayout()

        fileNameLabel = QtWidgets.QLabel("File name: " + printName)
        fileNameLabel.setStyleSheet("QLabel {font-weight: 700; font-size: 14px}")
        fileNameLabel.setAlignment(QtCore.Qt.AlignCenter)

        printWeightLabel = QtWidgets.QLabel("Print weight: " + printWeightString)
        printWeightLabel.setStyleSheet("QLabel {font-weight: 700; font-size: 14px}")
        printWeightLabel.setAlignment(QtCore.Qt.AlignCenter)

        printMaterialLabel = QtWidgets.QLabel("Print material: " + printMaterial)
        printMaterialLabel.setStyleSheet("QLabel {font-weight: 700; font-size: 14px}")
        printMaterialLabel.setAlignment(QtCore.Qt.AlignCenter)

        self.expectedCostLabel = QtWidgets.QLabel("Expected cost: " + self.formattedPrintCost)
        self.expectedCostLabel.setStyleSheet("QLabel {font-weight: 700; font-size: 14px}")
        self.expectedCostLabel.setAlignment(QtCore.Qt.AlignCenter)

        alreadySwipedLabel = QtWidgets.QLabel("\n\nAlready swiped in the main lab?")
        alreadySwipedLabel.setStyleSheet("QLabel {font-weight: 700; font-size: 14px}")
        alreadySwipedLabel.setAlignment(QtCore.Qt.AlignCenter)

        importInformationButtonLayout = QtWidgets.QHBoxLayout()
        self.importInformationButton = QtWidgets.QPushButton("Import Information")
        self.importInformationButton.setStyleSheet("QPushButton {font-size: 14px}")
        self.importInformationButton.setFixedSize(140, 26)
        importInformationButtonLayout.addWidget(self.importInformationButton)

        self.emailLabel = QtWidgets.QLabel("\nRIT Username/Email?")
        self.emailLabel.setStyleSheet("QLabel {font-weight: 700; font-size: 14px}")
        self.emailLabel.setAlignment(QtCore.Qt.AlignCenter)

        emailFieldLayout = QtWidgets.QHBoxLayout()
        self.emailField = QtWidgets.QLineEdit()
        self.emailField.setStyleSheet("QLineEdit {font-size: 14px}")
        self.emailField.setFixedSize(300, 26)
        if Configuration.DISABLE_MANUALLY_ENTERING_EMAIL:
            self.emailField.setStyleSheet("QLineEdit {font-size: 14px; background-color: #DDDDDD;}")
            self.emailField.setReadOnly(True)
        emailFieldLayout.addWidget(self.emailField)

        self.printPurposeLabel = QtWidgets.QLabel("Print Purpose?")
        self.printPurposeLabel.setStyleSheet("QLabel {font-weight: 700; font-size: 14px}")
        self.printPurposeLabel.setAlignment(QtCore.Qt.AlignCenter)

        printPurposeLayout = QtWidgets.QHBoxLayout()
        self.printPurposeField = QtWidgets.QComboBox()
        self.printPurposeField.setStyleSheet("QLineEdit {font-size: 14px}")
        self.printPurposeField.setFixedSize(300, 26)
        self.printPurposeField.addItem("Please Select...")
        for entry in Configuration.NORMAL_PRINT_PURPOSES:
            self.printPurposeField.addItem(entry)
        printPurposeLayout.addWidget(self.printPurposeField)
        self.additionalPrintPurposesAdded = False

        self.msdNumberLabel = QtWidgets.QLabel("\nMSD Number (if any)? (P#####)")
        self.msdNumberLabel.setStyleSheet("QLabel {font-weight: 700; font-size: 14px}")
        self.msdNumberLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.msdNumberLabel.hide()

        msdNumberFieldLayout = QtWidgets.QHBoxLayout()
        self.msdNumberField = QtWidgets.QLineEdit()
        self.msdNumberField.setStyleSheet("QLineEdit {font-size: 14px}")
        self.msdNumberField.setFixedSize(300, 26)
        msdNumberFieldLayout.addWidget(self.msdNumberField)
        self.msdNumberField.hide()

        self.errorLabel = QtWidgets.QLabel("\n")
        self.errorLabel.setAlignment(QtCore.Qt.AlignCenter)

        self.primaryButtonsLayout = QtWidgets.QHBoxLayout()
        self.cancelButton = QtWidgets.QPushButton("Cancel")
        self.cancelButton.setStyleSheet("QPushButton {font-size: 14px}")
        self.cancelButton.setFixedSize(120, 26)
        self.submitButton = QtWidgets.QPushButton("Submit")
        self.submitButton.setStyleSheet("QPushButton {font-size: 14px}")
        self.submitButton.setFixedSize(120, 26)
        self.primaryButtonsLayout.addWidget(self.cancelButton)
        self.primaryButtonsLayout.addWidget(self.submitButton)

        self.adminButtonsVisible = False
        self.secondaryButtonLayout = QtWidgets.QHBoxLayout()
        self.adminButton = QtWidgets.QPushButton("Administrate")
        self.adminButton.setStyleSheet("QPushButton {font-size: 14px}")
        self.adminButton.setFixedSize(120, 26)
        self.ignorePaymentButton = QtWidgets.QPushButton("Ignore Payment")
        self.ignorePaymentButton.setStyleSheet("QPushButton {font-size: 14px}")
        self.ignorePaymentButton.setFixedSize(140, 26)
        self.ignorePaymentButton.hide()
        self.ignoreTimeButton = QtWidgets.QPushButton("Ignore Time")
        self.ignoreTimeButton.setStyleSheet("QPushButton {font-size: 14px}")
        self.ignoreTimeButton.setFixedSize(140, 26)
        self.ignoreTimeButton.hide()
        self.secondaryButtonLayout.addWidget(self.adminButton)
        self.secondaryButtonLayout.addWidget(self.ignorePaymentButton)
        self.secondaryButtonLayout.addWidget(self.ignoreTimeButton)

        self.layout.addWidget(fileNameLabel)
        self.layout.addWidget(printWeightLabel)
        self.layout.addWidget(printMaterialLabel)
        self.layout.addWidget(self.expectedCostLabel)
        self.layout.addWidget(alreadySwipedLabel)
        self.layout.addLayout(importInformationButtonLayout)
        self.layout.addWidget(self.emailLabel)
        self.layout.addLayout(emailFieldLayout)
        self.layout.addWidget(self.printPurposeLabel)
        self.layout.addLayout(printPurposeLayout)
        self.layout.addWidget(self.msdNumberLabel)
        self.layout.addLayout(msdNumberFieldLayout)
        self.layout.addWidget(self.errorLabel)
        self.layout.addLayout(self.primaryButtonsLayout)
        self.layout.addLayout(self.secondaryButtonLayout)
        self.widget.setLayout(self.layout)

        # Connect the events.
        self.printPurposeField.currentTextChanged.connect(self.printPurposeChanged)
        self.importInformationButton.clicked.connect(self.promptImportInformation)
        self.cancelButton.clicked.connect(self.cancelPayment)
        self.submitButton.clicked.connect(self.submitPayment)
        self.adminButton.clicked.connect(self.enableAdmin)
        self.ignorePaymentButton.clicked.connect(self.promptIgnorePayment)
        self.ignoreTimeButton.clicked.connect(self.promptIgnoreTime)

        app = CuraApplication.getInstance()
        if app.ConstructRIT.currentJobModeUser is not None:
            # Set up the job mode fields.
            self.setPaymentIgnored()
            self.setTimeIgnored()
            self.setStatusMessage("Job mode defaults set.")
            self.emailField.setText(app.ConstructRIT.currentJobModeUser["email"])
            self.printPurposeField.setCurrentText("Job Mode")
        else:
            # Display an initial error if the print time is too long.
            printTimeError = getPrintLengthError(printTimeHours)
            if printTimeError is not None:
                self.setErrorMessage(printTimeError)

        # Show and focus the window.
        self.show()

    def getValidEmail(self) -> Optional[str]:
        """Returns if the input email, or None if it is invalid.
        Only works with RIT emails if the "@" is used.

        :return: The valid RIT email, if any.
        """

        currentEmail = self.emailField.text().lower().strip()

        # Cut off email domain. Return none if email isn't "@rit.edu" or "@g.rit.edu"
        domainLocation = currentEmail.find("@")
        if domainLocation != -1:
            domain = currentEmail[domainLocation:]
            currentEmail = currentEmail[0:domainLocation]
            if domain != "@rit.edu" and domain != "@g.rit.edu" and domain != "@mail.rit.edu":
                return None

        # Return if invalid character.
        for character in currentEmail:
            characterNum = ord(character)
            if characterNum < 43 or (characterNum >= 58 and characterNum <= 65) or (characterNum >= 91 and characterNum <= 96 and characterNum != 95) or characterNum >= 123:
                return None

        # Return if empty.
        if currentEmail == "":
            return None

        # Remove @g.rit.edu
        emailIndex = currentEmail.find("@g.rit.edu")
        if emailIndex > -1:
            currentEmail = currentEmail[0:emailIndex]

        # Remove @mail.rit.edu
        emailIndex = currentEmail.find("@mail.rit.edu")
        if emailIndex > -1:
            currentEmail = currentEmail[0:emailIndex]

        # Add @rit.edu
        emailIndex = currentEmail.find("@rit.edu")
        if emailIndex == -1:
            currentEmail += "@rit.edu"

        # Return the email (valid).
        return currentEmail

    def getValidMSDNumber(self) -> Optional[str]:
        """Returns the MSD number entered, or an empty string.
        If the number is invalid, None is returned.

        :return: The MSD Number entered, if any.
        """

        currentMSDNumber = self.msdNumberField.text().upper().strip()

        # Return an empty string if the MSD number is empty.
        if currentMSDNumber == "":
            return ""

        # Return None if the first letter isn't P.
        if currentMSDNumber[0] != "P":
            return None

        # Return None if the following characters are not numbers.
        if not currentMSDNumber[1:].isdigit():
            return None

        # Return the MSD number.
        return currentMSDNumber

    def promptImportInformation(self, event) -> None:
        """Prompts to import user information.
        """

        swipeWindow = ImportUserDataWindow()
        swipeWindow.onImported.connect(self.importInformation)

    @ThreadedOperation
    def importInformation(self, data: dict) -> None:
        """Imports user information to the inputs.

        :param data: Data from the import.
        """

        if "email" in data.keys():
            self.emailField.setText(data["email"])
        if "lastPurpose" in data.keys():
            self.printPurposeField.setCurrentText(data["lastPurpose"])
        if "lastMSDNumber" in data.keys():
            self.msdNumberField.setText(data["lastMSDNumber"])

    @ThreadedOperation
    def hideButtons(self):
        """Hides the buttons.
        """

        self.cancelButton.hide()
        self.submitButton.hide()
        self.adminButton.hide()
        self.ignorePaymentButton.hide()
        self.ignoreTimeButton.hide()

    @ThreadedOperation
    def showButtons(self) -> None:
        """Shows the buttons.
        """

        self.cancelButton.show()
        self.submitButton.show()
        if self.adminButtonsVisible:
            self.ignoreTimeButton.show()
            self.ignorePaymentButton.hide()
        else:
            self.adminButton.show()

    def close(self) -> None:
        """Closes the window.
        """

        self.runThreadedOperation(super().close)
        self.onClose.emit()

    def cancelPayment(self, event) -> None:
        """Cancels the payment.
        """

        self.close()

    def exportPrint(self) -> None:
        """Exports the print.
        """

        # Log the print.
        try:
            self.setStatusMessage("Logging print...")
            Http.LogPrint(self.getValidEmail(), self.printName, self.printMaterial, self.printWeight, self.printPurposeField.currentText(), self.getValidMSDNumber(), not self.ignorePayment)
        except IOError as error:
            if "[Errno socket error]" in str(error):
                self.setErrorMessage("An error occurred logging print. (Server can't be reached)")
            else:
                self.setErrorMessage("An error occurred logging print. (Internal server error)")
            self.showButtons()
            return

        # Invoke the event and wait a bit to close.
        self.setStatusMessage("Print accepted. Exporting print.")
        self.onCompleted.emit([self.printLocation])
        time.sleep(0.5)
        self.close()

    def submitPayment(self, event) -> None:
        """Submits a payment.
        """

        self.hideButtons()
        self.setStatusMessage("Please wait...")

        # Display an initial error if the print time is too long.
        printTimeError = getPrintLengthError(self.printTimeHours)
        if printTimeError is not None and not self.ignoreTime:
            self.setErrorMessage(printTimeError)
            self.showButtons()
            return

        # Get the email and display notification if invalid.
        email = self.getValidEmail()
        if email is None:
            self.setErrorMessage("Email is invalid.")
            self.emailLabel.setStyleSheet("QLabel {font-weight: 700; font-size: 14px; color: #FF0000;}")
            self.showButtons()
            return
        else:
            self.emailLabel.setStyleSheet("QLabel {font-weight: 700; font-size: 14px;}")

        # Get the purpose and display notification if it isn't selected.
        printPurpose = self.printPurposeField.currentText()
        if printPurpose == "Please Select...":
            self.setErrorMessage("Select a print purpose.")
            self.printPurposeLabel.setStyleSheet("QLabel {font-weight: 700; font-size: 14px; color: #FF0000;}")
            self.showButtons()
            return
        else:
            self.printPurposeLabel.setStyleSheet("QLabel {font-weight: 700; font-size: 14px;}")

        # Get the MSD number and display notification if invalid.
        msdNumber = self.getValidMSDNumber()
        if msdNumber is None:
            self.setErrorMessage("MSD Number is invalid.")
            self.msdNumberLabel.setStyleSheet("QLabel {font-weight: 700; font-size: 14px; color: #FF0000;}")
            self.showButtons()
            return
        else:
            self.msdNumberLabel.setStyleSheet("QLabel {font-weight: 700; font-size: 14px;}")

        # Set the current transaction.
        newTransaction = self.currentTransaction + 1
        self.currentTransaction = newTransaction

        # Start the submit states so that the UI gets updated.
        self.startWriteCheck()

    @AsyncProcedure
    def startWriteCheck(self, routineContext: AsyncProcedureContext) -> None:
        """Starts to check if the output is writable.

        :param routineContext: Routine context for calling steps.
        """

        # Check if the directory is writable.
        try:
            open(self.printLocation, "w").close()
            routineContext.next(True)
        except IOError:
            routineContext.next(False)

    @UIAsyncProcedure
    def writeChecked(self, routineContext: AsyncProcedureContext, writable: bool) -> None:
        """Handles write access being checked.

        :param routineContext: Routine context for calling steps.
        :param writable: Whether the output was writable.
        """

        # Set a message if the directory can't be writen to.
        if not writable:
            self.showButtons()
            self.setErrorMessage("Can't write file. Is the slider on the SD card set to be locked?")
        else:
            routineContext.next()

    @AsyncProcedure
    def startIdCheck(self, routineContext: AsyncProcedureContext) -> None:
        """Starts to check the id.

        :param routineContext: Routine context for calling steps.
        """

        # Check if registration is required and if the email is registered.
        try:
            email = self.getValidEmail()
            if Http.getUniversityIdHash(email) is None:
                routineContext.next(False, "Your email isn't registered. Please swipe in the main lab to continue.")
                return
        except IOError as error:
            if "[Errno socket error]" in str(error):
                routineContext.next(False, "An error occurred checking if you are registered. (Server can't be reached)")
                return
            else:
                routineContext.next(False, "An error occurred checking if you are registered. (Internal server error)")
                return

        # Invoke that the id is valid.
        routineContext.next(True)

    @UIAsyncProcedure
    def idChecked(self, routineContext: AsyncProcedureContext, valid: bool, errorMessage: Optional[str] = None) -> None:
        """Handles the id being checked.

        :param routineContext: Routine context for calling steps.
        :param valid: Whether the id is valid.
        :param errorMessage: Error message to display, if any.
        """

        # Set the displayed message.
        if not valid:
            self.showButtons()
            self.setErrorMessage(errorMessage)
            return

        # Check the time of the print.
        routineContext.next()

    @AsyncProcedure
    def startTimeCheck(self, routineContext: AsyncProcedureContext) -> None:
        """Starts to check the time of the print.

        :param routineContext: Routine context for calling steps.
        """

        # Compare the last print time and display a notification if invalid.
        try:
            if not self.ignoreTime:
                email = self.getValidEmail()
                printTimeMessage = getLastPrintTimeError(email)
                if printTimeMessage is not None:
                    routineContext.next(False, printTimeMessage)
                    return
        except IOError as error:
            if "[Errno socket error]" in str(error):
                routineContext.next(False, "An error occurred checking your last print. (Server can't be reached)")
            else:
                routineContext.next(False, "An error occurred checking your last print. (Internal server error)")
            return

        # Invoke that the time is valid.
        routineContext.next(True)

    @UIAsyncProcedure
    def timeChecked(self, routineContext: AsyncProcedureContext, valid: bool, errorMessage: Optional[str] = None) -> None:
        """Handles the time being checked.

        :param routineContext: Routine context for calling steps.
        :param valid: Whether the time check was valid.
        :param errorMessage: Error message to display, if any.
        """

        # Set the displayed message.
        if not valid:
            self.showButtons()
            self.setErrorMessage(errorMessage)
            return

        # Log the print and export it.
        threading.Thread(target=self.exportPrint).start()

    def printPurposeChanged(self, event) -> None:
        """Handles the print purpose being changed.
        Used to show and hide MSD information.
        """

        if self.printPurposeField.currentText() == "Senior Design Project (Reimbursed)":
            self.msdNumberLabel.show()
            self.msdNumberField.show()
        else:
            self.msdNumberLabel.hide()
            self.msdNumberField.hide()

    def enableAdmin(self, event) -> None:
        """Enables the admin buttons.
        """

        self.adminButtonsVisible = True
        self.adminButton.hide()
        self.ignorePaymentButton.show()
        self.ignoreTimeButton.show()

    def promptIgnorePayment(self, event) -> None:
        """Prompts to mark a print as not owed.
        If it is not owed, it is made owed without a prompt.
        """

        if self.ignorePayment:
            self.ignorePayment = False
            self.expectedCostLabel.setText("Expected cost: " + self.formattedPrintCost)
            self.ignorePaymentButton.setText("Ignore Payment")
            self.setStatusMessage("Payment will be owed.")
        else:
            app = CuraApplication.getInstance()
            if app.ConstructRIT.currentJobModeUser is not None:
                self.setPaymentIgnored()
            else:
                swipeWindow = LabManagerAuthenticationWindow()
                swipeWindow.onAuthenticated.connect(self.setPaymentIgnored)

    def setPaymentIgnored(self) -> None:
        """Sets a payment as being ignored.
        """

        if not self.additionalPrintPurposesAdded:
            self.additionalPrintPurposesAdded = True
            if Configuration.RESET_PRINT_PURPOSE_ON_IGNORE:
                self.printPurposeField.setCurrentText("Please Select...")
            for additionalPurpose in Configuration.IGNORED_PAYMENT_ADDITIONAL_PRINT_PURPOSES:
                self.printPurposeField.addItem(additionalPurpose)

        self.ignorePayment = True
        self.expectedCostLabel.setText("Expected cost: $0.00 (Payment ignored)")
        self.ignorePaymentButton.setText("Unignore Payment")
        self.setStatusMessage("Payment will not be owed.")

    def promptIgnoreTime(self, event) -> None:
        """ Prompts to ignore the time.
        If the time is ignored, it is made not ignored without a prompt.
        """

        if self.ignoreTime:
            self.ignoreTime = False
            self.ignoreTimeButton.setText("Ignore Time")
            self.setStatusMessage("Time no longer ignored.")
        else:
            app = CuraApplication.getInstance()
            if app.ConstructRIT.currentJobModeUser is not None:
                self.setTimeIgnored()
            else:
                swipeWindow = LabManagerAuthenticationWindow()
                swipeWindow.onAuthenticated.connect(self.setTimeIgnored)

    def setTimeIgnored(self) -> None:
        """Sets a time as being ignored.
        """

        self.ignoreTime = True
        self.ignoreTimeButton.setText("Unignore Time")
        self.setStatusMessage("Long print authorized.")

    @ThreadedOperation
    def setStatusMessage(self, message: str) -> None:
        """Sets the status message.

        :param message: Message to display.
        """

        self.errorLabel.setText("\n" + message)
        self.errorLabel.setStyleSheet("QLabel {font-weight: 700; font-size: 14px;}")

    @ThreadedOperation
    def setErrorMessage(self, message: str) -> None:
        """Sets the error message.

        :param message: Message to display.
        """

        self.errorLabel.setText("\n" + message)
        self.errorLabel.setStyleSheet("QLabel {font-weight: 700; font-size: 14px; color: #FF0000;}")



# Add the steps to the procedure.
PaymentWindow.startWriteCheck.appendLast(PaymentWindow.writeChecked)
PaymentWindow.startWriteCheck.appendLast(PaymentWindow.startIdCheck)
PaymentWindow.startWriteCheck.appendLast(PaymentWindow.idChecked)
PaymentWindow.startWriteCheck.appendLast(PaymentWindow.startTimeCheck)
PaymentWindow.startWriteCheck.appendLast(PaymentWindow.timeChecked)



if __name__ == '__main__':
    # Create an app.
    app = QtWidgets.QApplication([])

    # Create a window.
    paymentWindow = PaymentWindow("Test Print.gcode",120,4,"PLA","29.1 (L) x 25.4 (W) x 3.0 (H)")

    # Connect the test events.
    def onCompleted(data):
        print("COMPLETED: " + str(data))
    paymentWindow.onCompleted.connect(onCompleted)

    # Run the app.
    app.exec()