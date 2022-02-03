# Construct Cura Plugins
Plugins created for use in The Construct @ RIT.

## Plugins
### ConstructCore
*No dependencies.*

Core library used by other plugins, including classes that
are common between multiple plugins. No functionality is
added by this plugin.

### ConstructJobMode
*Requires ConstructCore*

Adds a button on the top of the main view for enabling "Job Mode",
which is used with the payment window to auto-fill the email,
print purpose, and admin fields for batch printing. No functionality
is added by this plugin unless the ConstructPaymentWindow plugin
is used as well.

### ConstructPaymentWindow
*Requires ConstructCore*<br>
**Depends on Ultimaker/Uranium#777 and Ultimaker/Cura#11412**

Adds a payment window when attempting to export .gcode and .x3g
files for logging and payment purposes. Provides other checks, such
as attempting to block long prints and users using multiple printers
at once.

### ConstructPrinterAuthorization
*Requires ConstructCore*

Requires lab manager authorization to change to certain printers
and materials. If a user changes the printer or material to one
that is not whitelisted, they will be prompted to authenticate. If
the authentication fails, the settngs will be rolled back.

### ConstructSettingsSandbox
*Requires ConstructCore*

Resets the settings on start to a pre-saved version of the settings
to ensure consistent settings when starting Cura.