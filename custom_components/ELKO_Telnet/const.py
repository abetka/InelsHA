"""Constants for the ELKO integration."""

DOMAIN = "ELKO_telnet"
DOMAIN_DATA = f"{DOMAIN}_data"
VERSION = "0.0.1"
TITLE = "ELKO_telnet"

# Icons
ICON_SWITCH = "mdi:power-socket"
ICON_LIGHT = "mdi:lightbulb"

PLATFORM_SWITCH = "switch"
PLATFORM_LIGHT = "light"

CONF_PORT = 1111
CONF_HOST = ""
CONF_DEVICE_ID = ""


PLATFORMS = [PLATFORM_SWITCH, PLATFORM_LIGHT]
