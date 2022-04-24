"""
Zachary Cook

Utilities for interacting with external services.
"""

import hashlib
import requests
from .. import Configuration
from typing import Dict, Optional, Tuple


def hashId(universityId: str) -> str:
    """Hashes a university id.

    :param universityId: University id to hash.
    """

    return hashlib.sha256(universityId.encode("UTF-8")).hexdigest()


def getHost() -> str:
    """Returns the host to use.
    """

    return Configuration.SERVER_HOST


def isAuthorized(universityId: str) -> bool:
    """Returns if an id is authorized.

    :param universityId: University id to check.
    """

    # Get the user information and return if the LabManager permission exists.
    userResult = requests.get(getHost() + "/user/get?hashedid=" + hashId(universityId)).json()
    if "permissions" in userResult.keys():
        for permission in userResult["permissions"]:
            if permission.lower() == "labmanager":
                return True

    # Return false (unauthorized).
    return False


def getUniversityIdHash(email) -> Optional[str]:
    """Returns the university id hash for an email.

    :param email: Email to get the university id hash of.
    """

    # Send and read the HTTP request.
    response = requests.get(getHost() + "/user/find?email=" + email).json()

    # If the request was successful.
    if "hashedId" in response.keys() and response["hashedId"] is not None:
        return response["hashedId"]
    return None


def getLastPrint(email: str) -> Tuple[Optional[float], Optional[float]]:
    """Returns the last print time and weight. If there is no
    last print, none is returned.

    :param email: Email to get the last print of.
    """

    # Get the hashed id and return if there is none.
    hashedId = getUniversityIdHash(email)
    if hashedId is None:
        return None, None

    # Send and read the HTTP request.
    response = requests.get(getHost() + "/print/last?hashedid=" + hashedId).json()

    # If the request was successful, return the last print time and weight if there is one.
    if "timeStamp" in response and "weight" in response and response["timeStamp"] is not None and response["weight"] is not None:
        return float(response["timeStamp"]), float(response["weight"])

    # Return None (no prints)
    return None, None


def getLastPrintInformation(universityId: str) -> Optional[Dict]:
    """Returns the last print information of a user.

    :param universityId: University id of the user to get the last print of.
    """

    # Get the email of the user.
    hashedId = hashId(universityId)
    userResult = requests.get(getHost() + "/user/get?hashedid=" + hashedId).json()
    if "email" not in userResult.keys():
        return None
    userData = {
        "email": userResult["email"],
    }

    # Add the last print information and return it.
    printResponse = requests.get(getHost() + "/print/last?hashedid=" + hashedId).json()
    if "purpose" in printResponse.keys() and printResponse["purpose"] is not None:
        userData["lastPurpose"] = printResponse["purpose"]
    if "billTo" in printResponse.keys() and printResponse["billTo"] is not None:
        userData["lastMSDNumber"] = printResponse["billTo"]
    return userData


def getName(universityId: str) -> Optional[str]:
    """Returns the name for a user.

    :param universityId: University id of the user to get the name of.
    """

    # Get the user information.
    userResult = requests.get(getHost() + "/user/get?hashedid=" + hashId(universityId)).json()

    # Process and return the result.
    if "name" in userResult.keys():
        return userResult["name"]
    else:
        return None


def LogPrint(email: str, fileName: str, materialType: str, printWeight: float, printPurpose: str, msdNumber: Optional[str], paymentOwed: bool) -> bool:
    """Logs a print. Returns if the task was successful.

    :param email: Email of the user exporting the print.
    :param fileName: Name of the file that was exported.
    :param materialType: Type of the material being used.
    :param printWeight: Weight of the print being exported.
    :param printPurpose: Purpose of the print being exported.
    :param msdNumber: MSD Number of the print being exported.
    :param paymentOwed: Whether the payment is owed or not.
    """

    # Get the hashed id and return if there is none.
    hashedId = getUniversityIdHash(email)
    if hashedId is None:
        return False

    # Check if this is a Senior Design print.
    msd = printPurpose == "Senior Design Project (Reimbursed)"

    # Create the payload.
    arguments = {
        "hashedId": hashedId,
        "fileName": fileName,
        "material": materialType,
        "weight": printWeight,
        "purpose": printPurpose,
        "billTo": msdNumber if msd else None,
        "owed": paymentOwed,
    }

    # Send the request and return the result.
    printResult = requests.post(getHost() + "/print/add", json=arguments).json()
    return "status" in printResult.keys() and printResult["status"] == "success"
