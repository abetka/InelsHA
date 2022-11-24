"""Platform for light integration."""
from __future__ import annotations

import logging
import telnetlib

import voluptuous as vol

# Import the device class from the component that you want to support
import homeassistant.helpers.config_validation as cv
from homeassistant.components.light import (ATTR_BRIGHTNESS, PLATFORM_SCHEMA,
                                            LightEntity)
from homeassistant.const import CONF_NAME, CONF_HOST, CONF_PORT, CONF_DEVICE_ID, CONF_LIGHTS, CONF_VALUE_TEMPLATE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

_LOGGER = logging.getLogger(__name__)

DEFAULT_PORT = 1111

LIGHT_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): cv.port,
        vol.Required(CONF_DEVICE_ID): cv.string,
    }
)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {vol.Required(CONF_LIGHTS): cv.schema_with_slug_keys(LIGHT_SCHEMA)}
)

def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None
) -> None:
    """Set up the Telnet Light platform."""
    devices: dict[str, Any] = config[CONF_LIGHTS]
    lights = []

    for object_id, device_config in devices.items():
        value_template: Template | None = device_config.get(CONF_VALUE_TEMPLATE)

        if value_template is not None:
            value_template.hass = hass

        lights.append(
            ELKOLight(
                object_id,
                device_config[CONF_NAME],
                device_config[CONF_HOST],
                device_config[CONF_DEVICE_ID],
                device_config[CONF_PORT],
                value_template,
            )
        )

    if not lights:
        _LOGGER.error("No lights added")
        return

    add_entities(lights)

class ELKOLight(LightEntity):
    """Representation of an ELKO Light."""
    def __init__(
        self,
        object_id: str,
        name: str,
        host: str,
        device_id: str,
        port: int,
        value_template: Template | None,
        ) -> None:
        """Initialize an AwesomeLight."""
        self._object_id = object_id
        self._name = name
        self._host = host
        self._port = port
        self._device_id = device_id
        self._delimiter = ';'
        self._state = None
        self._brightness = None
        _LOGGER.debug("object_id: %s", object_id)
        _LOGGER.debug("name: %s", name)
        _LOGGER.debug("host: %s", host)
        _LOGGER.debug("device_id: %s", device_id)
        _LOGGER.debug("port: %s", port)
        _LOGGER.debug("self: %s", self)

    @property
    def name(self) -> str:
        """Return the display name of this light."""
        return self._name

    @property
    def brightness(self):
        """Return the brightness of the light.
        This method is optional. Removing it indicates to Home Assistant
        that brightness is not supported for this light.
        """
        return self._brightness

    @property
    def is_on(self) -> bool | None:
        """Return true if light is on."""
        return self._state

    def turn_on(self, **kwargs: Any) -> None:
        """Instruct the light to turn on.
        You can skip the brightness part if your light does not support
        brightness control.
        """
        self._brightness = str(kwargs.get(ATTR_BRIGHTNESS, 255))
        command = b"SET" + self._delimiter.encode('ascii') + self._device_id.encode('ascii')+ self._delimiter.encode('ascii')+ self._brightness.encode('ascii') + b"\r\n"
        _LOGGER.debug("Turn On: %s", command)
        self._telnet_command(command)

    def turn_off(self, **kwargs: Any) -> None:
        """Instruct the light to turn off."""
        command = b"SET" + self._delimiter.encode('ascii') + self._device_id.encode('ascii')+ self._delimiter.encode('ascii') + b"0\r\n"
        _LOGGER.debug("Turn Off: %s", command)
        self._telnet_command(command)

    def update(self) -> None:
        """Fetch new state data for this light.
        This is the only method that should fetch new data for Home Assistant.
        """

    def _telnet_command(self, command) -> str | None:
        try:
            _LOGGER.debug("Telnet connect to: %s with port: %s", self._host, self._port)
            telnet = telnetlib.Telnet(self._host, self._port)
            telnet.write(command)
            response = telnet.read_until(b"\r\n").decode('ascii').split(self._delimiter)[2].rstrip("\r").rstrip("\n")
            telnet.close()
        except OSError as error:
            _LOGGER.error(
                'Command "%s" failed with exception: %s', command, repr(error)
            )
            return None
        _LOGGER.debug("Telnet response: %s", response)
        return response