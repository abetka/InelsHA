"""Support for switch controlled using a telnet connection."""
from __future__ import annotations

from datetime import timedelta
import logging
from . import telnet
from typing import Any

import voluptuous as vol

from homeassistant.components.switch import (
    ENTITY_ID_FORMAT,
    PLATFORM_SCHEMA,
    SwitchEntity,
)
from homeassistant.const import (
    CONF_COMMAND_OFF,
    CONF_COMMAND_ON,
    CONF_COMMAND_STATE,
    CONF_NAME,
    CONF_PORT,
    CONF_RESOURCE,
    CONF_DEVICE_ID,
    CONF_SWITCHES,
    CONF_TIMEOUT,
    CONF_VALUE_TEMPLATE,
)
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.template import Template
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

_LOGGER = logging.getLogger(__name__)

DEFAULT_PORT = 1111
DEFAULT_TIMEOUT = 0.2
CONF_DELIMITER = 'delimiter'
DEFAULT_DELIMITER = ';'

SWITCH_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_COMMAND_OFF): cv.string,
        vol.Required(CONF_COMMAND_ON): cv.string,
        vol.Required(CONF_RESOURCE): cv.string,
        vol.Required(CONF_DEVICE_ID): cv.string,
        vol.Optional(CONF_DELIMITER, default=DEFAULT_DELIMITER): cv.string,
        vol.Optional(CONF_VALUE_TEMPLATE): cv.template,
        vol.Optional(CONF_COMMAND_STATE): cv.string,
        vol.Optional(CONF_NAME): cv.string,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
        vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): vol.Coerce(float),
    }
)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {vol.Required(CONF_SWITCHES): cv.schema_with_slug_keys(SWITCH_SCHEMA)}
)

SCAN_INTERVAL = timedelta(seconds=10)


def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Find and return switches controlled by telnet commands."""
    devices: dict[str, Any] = config[CONF_SWITCHES]
    switches = []

    for object_id, device_config in devices.items():
        value_template: Template | None = device_config.get(CONF_VALUE_TEMPLATE)

        if value_template is not None:
            value_template.hass = hass

        switches.append(
            ELKOSwitch(
                object_id,
                device_config[CONF_RESOURCE],
                device_config[CONF_DEVICE_ID],
                device_config[CONF_PORT],
                device_config.get(CONF_NAME, object_id),
                device_config[CONF_COMMAND_ON],
                device_config[CONF_COMMAND_OFF],
                device_config.get(CONF_COMMAND_STATE),
                value_template,
                device_config[CONF_TIMEOUT],
                device_config[CONF_DELIMITER],
            )
        )

    if not switches:
        _LOGGER.error("No switches added")
        return

    add_entities(switches)


class ELKOSwitch(SwitchEntity):
    """Representation of a switch that can be toggled using telnet commands."""
    def __init__(
        self,
        object_id: str,
        resource: str,
        device_id: str,
        port: int,
        friendly_name: str,
        command_on: str,
        command_off: str,
        command_state: str | None,
        value_template: Template | None,
        timeout: float,
        delimiter: str,
    ) -> None:
        """Initialize the switch."""
        self.entity_id = ENTITY_ID_FORMAT.format(object_id)
        self._resource = resource
        self._device_id = device_id
        self._port = port
        self._attr_name = friendly_name
        self._attr_is_on = False
        self._command_on = command_on
        self._command_off = command_off
        self._command_state = command_state
        self._value_template = value_template
        self._timeout = timeout
        self._attr_should_poll = bool(command_state)
        self._attr_assumed_state = bool(command_state is None)
        self._cmd = {
            'host': resource,
            'port': port,
            'delimiter': delimiter,
            'device_id': device_id,
        }

    def update(self) -> None:
        """Update device state."""
        if not self._command_state:
            return
        response = telnet.getData(**self._cmd)
        _LOGGER.debug("Status is: %s", response)
        if response == '1':
            self._attr_is_on = True
        else:
            self._attr_is_on = False

    def turn_on(self, **kwargs: Any) -> None:
        """Turn the device on."""
        self._cmd.update({
            'command': self._command_on,
        })
        responce = telnet.setData(**self._cmd)
        _LOGGER.debug("Status is: %s", response)
        if self.assumed_state:
            self._attr_is_on = True
            self.schedule_update_ha_state()

    def turn_off(self, **kwargs: Any) -> None:
        """Turn the device off."""
        self._cmd.update({
            'command': self._command_off,
        })
        responce = telnet.setData(**self._cmd)
        if self.assumed_state:
            self._attr_is_on = False
            self.schedule_update_ha_state()