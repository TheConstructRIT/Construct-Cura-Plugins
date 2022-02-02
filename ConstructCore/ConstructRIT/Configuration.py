"""
Zachary Cook

Configuration for The Construct @ RIT.
"""


# Host for the server.
SERVER_HOST = "{ENV/SERVER_HOST}"

# Cost to print per gram in USD.
PRINT_COST_PER_GRAM = 0.03

# If true, emails can only be entered by importing
# from a university id.
DISABLE_MANUALLY_ENTERING_EMAIL = True

# If true, the print purpose will reset after the payment
# is ignored. This is to make it clear that other options
# can be selected.
RESET_PRINT_PURPOSE_ON_IGNORE = True

# The print purposes displayed when asking for user information.
NORMAL_PRINT_PURPOSES = ["Class/academic project", "Personal project", "Senior Design Project (Reimbursed)", "Club Project"]

# Additional print purposes that are displayed when
# the payment is ignored.
IGNORED_PAYMENT_ADDITIONAL_PRINT_PURPOSES = ["Test Print", "Internal Print", "Reprint", "Job Mode"]

# The limits for print times.
PRINTER_TIME_LIMITS = [
    {"printHoursLimit": 5, "startHour": 8, "endHour": 17},
    {"printHoursLimit": 12, "startHour": -1, "endHour": 25},
]

# Printer names that don't require lab manager authentication to use.
AUTO_AUTHORIZED_PRINTERS = [
    "FlashForge Creator Pro", "Artillery Sidewinder X1", "Prusa i3 Mk3/Mk3s",
]

# Material names that don't require lab manager authentication to use.
AUTO_AUTHORIZED_MATERIALS = [
    "generic_pla_175",
]

# Max file name size for a given printer.
# If no max length is given, the file name is not truncated.
MAX_FILE_NAME_LENGTHS = {
    "FlashForge Creator Pro": 31
}

# Names of the removable media that are whitelisted.
# If the list is empty, no whitelisting is done.
# All removable drive names must be lower case.
REMOVABLE_DRIVE_WHITELIST = [
    "printer_sd",
    "printer_usb",
]



# Read the environment file and determine the bindings.
import json
import os
import sys
bindings = {}
environmentFile = os.path.realpath(os.path.join(__file__, "..", "..", "environment.json"))
if os.path.exists(environmentFile):
    with open(environmentFile) as file:
        bindings = json.loads(file.read())

# Replace the configuration bindings.
module = sys.modules[__name__]
for attribute in dir(module):
    if not attribute.startswith("__") and isinstance(getattr(module, attribute), str):
        for binding in bindings.keys():
            setattr(module, attribute, getattr(module, attribute).replace("{ENV/" + binding + "}", bindings[binding]))
