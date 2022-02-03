"""
Zachary Cook

Utility for getting information based on print time.
"""

import datetime
import math
from ConstructRIT import Configuration
from ConstructRIT.Util import Http
from typing import Optional


def getCurrentHour() -> float:
    """Returns the current hour of the system.

    :return: The current hour of system.
    """

    currentTime = datetime.datetime.now()
    currentHour = currentTime.hour
    currentHour += (currentTime.minute / 60.0)

    return currentHour


def getLastPrintTimeError(email: str) -> Optional[str]:
    """Returns a message as a String determining if the last print is
    old enough to print again. If the print is old enough, None
    is returned.

    :param email: The email to check with.
    :return: The error to display if the last print was too recent.
    """

    lastPrintTime, lastPrintWeight = Http.getLastPrint(email)

    # If there is no last print timestamp, return true.
    if lastPrintTime is None or lastPrintWeight is None or lastPrintWeight <= 0:
        return None

    # Get the time difference.
    date = datetime.datetime.utcnow()
    currentTimestamp = (date - datetime.datetime(1970,1,1)).total_seconds()
    deltaTime = currentTimestamp - lastPrintTime

    # Return an error if the print is too recent.
    requiredTime = ((math.log(lastPrintWeight) * 8) + 8) * 60
    if deltaTime < requiredTime:
        return "Your last print was too recent. Make sure you are using only 1 printer."

    # Return None (no error).
    return None


def getCurrentTimeLimit() -> (Optional[float], Optional[float]):
    """Returns the current time limit and when the time limit ends.
    If there is no current limit, None and None are returned.

    :return: The current time limit in hours, and the hour that the limit ends.
    """

    currentHour = getCurrentHour()

    # Iterate through the hour limits.
    for limit in Configuration.PRINTER_TIME_LIMITS:
        startHour = limit["startHour"]
        endHour = limit["endHour"]
        hourLimit = limit["printHoursLimit"]

        # If the current time is within the range, return the time and the end time.
        if startHour <= currentHour and endHour > currentHour:
            return hourLimit, endHour

    # Return None and None (no limit)
    return None, None


def getPrintLengthError(printHours: float) -> Optional[str]:
    """Returns a warning message if the print is too long.

    :param printHours: Total hours the print will take.
    :return: The message to display if the print is too long.
    """

    currentLimit, limitEnds = getCurrentTimeLimit()

    if currentLimit is not None and limitEnds is not None and printHours > currentLimit:
        currentLimit = int(currentLimit)
        limitEnds = int(limitEnds)
        formattedPrintTime = str(currentLimit) + " hour" + str(currentLimit == 1 and "" or "s")

        if currentLimit is not None and limitEnds is not None:
            if limitEnds >= 24:
                # If the upper bound is 24 or greater, return an "All prints" message.
                return "All prints must be less than " + formattedPrintTime + ". Talk to a lab manager."
            else:
                # If the upper bound is less than 24, display a bounded limit.
                formattedLimitTimeEnd = str(limitEnds) + ":00 AM"
                if limitEnds == 12:
                    formattedLimitTimeEnd = "12:00 PM"
                elif limitEnds > 12:
                    formattedLimitTimeEnd = str(limitEnds - 12) + ":00 PM"

                return "Prints before " + formattedLimitTimeEnd + " must be less than " + formattedPrintTime + ". Talk to a lab manager."

    # Return None (no message)
    return None
