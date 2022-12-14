"""Support for Template lights."""
from __future__ import annotations

import logging
from . import telnet
from typing import Any

import voluptuous as vol

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_RGB_COLOR,
    ATTR_TRANSITION,
    ColorMode,
    LightEntity,
    LightEntityFeature,
    filter_supported_color_modes,
)
from homeassistant.const import (
    CONF_PORT,
    CONF_HOST,
    CONF_DEVICE_ID,
    CONF_FRIENDLY_NAME,
    CONF_LIGHTS,
    CONF_UNIQUE_ID,
    CONF_VALUE_TEMPLATE,
    STATE_OFF,
    STATE_ON,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import TemplateError
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.config_validation import PLATFORM_SCHEMA
from homeassistant.helpers.entity import async_generate_entity_id
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.script import Script
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType


_LOGGER = logging.getLogger(__name__)
_VALID_STATES = [STATE_ON, STATE_OFF, "true", "false"]

CONF_COLOR_ACTION = "set_color"
CONF_COLOR_TEMPLATE = "color_template"
CONF_SUPPORTS_TRANSITION = "supports_transition_template"
CONF_RED_DEVICE_ID = "red_device_id"
CONF_GREEN_DEVICE_ID = "green_device_id"
CONF_BLUE_DEVICE_ID = "blue_device_id"
CONF_DELIMITER = 'delimiter'
DEFAULT_DELIMITER = ';'

LIGHT_SCHEMA = vol.All(
    vol.Schema(
        {
            vol.Optional(CONF_COLOR_ACTION): cv.SCRIPT_SCHEMA,
            vol.Optional(CONF_COLOR_TEMPLATE): cv.template,
            vol.Optional(CONF_FRIENDLY_NAME): cv.string,
            vol.Optional(CONF_DEVICE_ID): cv.string,
            vol.Optional(CONF_RED_DEVICE_ID): cv.string,
            vol.Optional(CONF_GREEN_DEVICE_ID): cv.string,
            vol.Optional(CONF_BLUE_DEVICE_ID): cv.string,
            vol.Optional(CONF_DELIMITER, default=DEFAULT_DELIMITER): cv.string,
            vol.Required(CONF_HOST): cv.string,
            vol.Required(CONF_PORT): cv.port,
            vol.Optional(CONF_SUPPORTS_TRANSITION): cv.template,
            vol.Optional(CONF_UNIQUE_ID): cv.string,
            vol.Optional(CONF_VALUE_TEMPLATE): cv.template,
        }
    ),
)

PLATFORM_SCHEMA = vol.All(
    PLATFORM_SCHEMA.extend(
        {vol.Required(CONF_LIGHTS): cv.schema_with_slug_keys(LIGHT_SCHEMA)}
    ),
)


async def _async_create_entities(hass, config):
    """Create the Template Lights."""
    lights = []

    for object_id, entity_config in config[CONF_LIGHTS].items():
        unique_id = entity_config.get(CONF_UNIQUE_ID)
        lights.append(
            ELKOLight(
                hass,
                object_id,
                entity_config,
                unique_id,
            )
        )

    return lights


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the template lights."""
    async_add_entities(await _async_create_entities(hass, config))


class ELKOLight(LightEntity):
    """Representation of a templated Light, including dimmable."""

    _attr_should_poll = False

    def __init__(
        self,
        hass,
        object_id,
        config,
        unique_id,
    ):
        """Initialize the light."""
        self._friendly_name = config.get(CONF_FRIENDLY_NAME)
        self._template = config.get(CONF_VALUE_TEMPLATE)

        self._color_script = None
        if (color_action := config.get(CONF_COLOR_ACTION)) is not None:
            self._color_script = Script(hass, color_action, self._friendly_name, "ELKO_telnet")
        self._color_template = config.get(CONF_COLOR_TEMPLATE)
        self._supports_transition_template = config.get(CONF_SUPPORTS_TRANSITION)

        self._state = False
        self._brightness = None
        self._color = None
        self._fixed_color_mode = None
        self._supports_transition = False

        self._device_id = config.get(CONF_DEVICE_ID)
        self._red_device_id = config.get(CONF_RED_DEVICE_ID)
        self._green_device_id = config.get(CONF_GREEN_DEVICE_ID)
        self._blue_device_id = config.get(CONF_BLUE_DEVICE_ID)

        self._cmd = {
            'host': config.get(CONF_HOST),
            'port': config.get(CONF_PORT),
            'delimiter': config.get(CONF_DELIMITER),
        }

        self._attr_name = config.get(CONF_FRIENDLY_NAME)

        color_modes = {ColorMode.ONOFF}
        color_modes.add(ColorMode.RGB)
        self._supported_color_modes = filter_supported_color_modes(color_modes)
        if len(self._supported_color_modes) == 1:
            self._fixed_color_mode = next(iter(self._supported_color_modes))

    @property
    def brightness(self) -> int | None:
        """Return the brightness of the light."""
        return self._brightness

    @property
    def color_mode(self):
        """Return current color mode."""
        if self._fixed_color_mode:
            return self._fixed_color_mode
        # Support for ct + hs, prioritize hs
        if self._color is not None:
            return ColorMode.RGB
        return ColorMode.COLOR_TEMP

    @property
    def supported_color_modes(self):
        """Flag supported color modes."""
        return self._supported_color_modes


    @property
    def is_on(self) -> bool | None:
        """Return true if device is on."""
        return self._state

    async def async_added_to_hass(self) -> None:
        """Register callbacks."""
        if self._template:
            self.add_template_attribute(
                "_state", self._template, None, self._update_state
            )
        if self._color_template:
            self.add_template_attribute(
                "_color",
                self._color_template,
                None,
                self._update_color,
                none_on_template_error=True,
            )
        if self._supports_transition_template:
            self.add_template_attribute(
                "_supports_transition_template",
                self._supports_transition_template,
                None,
                self._update_supports_transition,
                none_on_template_error=True,
            )
        await super().async_added_to_hass()

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on."""
        optimistic_set = False
        # set optimistic states
        if self._template is None:
            self._state = True
            optimistic_set = True

        common_params = {}
        _LOGGER.debug("kwargs: %s", kwargs.keys())
        if ATTR_BRIGHTNESS in kwargs and self._device_id:
            self._cmd.update({
                'device_id': self._device_id,
                'command': str(int( kwargs[ATTR_BRIGHTNESS] * 0.39 )),
            })
            response = telnet.setData(**self._cmd)
            _LOGGER.debug("Status is: %s", response)

        # if ATTR_TRANSITION in kwargs and self._supports_transition is True:
        #     common_params["transition"] = kwargs[ATTR_TRANSITION]

        if ATTR_RGB_COLOR in kwargs and self._red_device_id and self._green_device_id and self._blue_device_id:
            rgb_value = kwargs[ATTR_RGB_COLOR]
            self._cmd.update({
                'device_id': self._red_device_id,
                'command': str(int( rgb_value[0] * 0.39 )),
            })
            response = telnet.setData(**self._cmd)
            _LOGGER.debug("Status is: %s", response)
            self._cmd.update({
                'device_id': self._green_device_id,
                'command': str(int( rgb_value[1] * 0.39 )),
            })
            response = telnet.setData(**self._cmd)
            _LOGGER.debug("Status is: %s", response)
            self._cmd.update({
                'device_id': self._blue_device_id,
                'command': str(int( rgb_value[2] * 0.39 )),
            })
            response = telnet.setData(**self._cmd)
            _LOGGER.debug("Status is: %s", response)

        if optimistic_set:
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the light off."""
        # if ATTR_TRANSITION in kwargs and self._supports_transition is True:
        #     await self.async_run_script(
        #         self._off_script,
        #         run_variables={"transition": kwargs[ATTR_TRANSITION]},
        #         context=self._context,
        #     )
        # else:
        #     await self.async_run_script(self._off_script, context=self._context)
        if self._red_device_id is not None:
            self._cmd.update({
                'device_id': self._red_device_id,
                'command': '0',
            })
            response = telnet.setData(**self._cmd)
            _LOGGER.debug("Status is: %s", response)
        if self._green_device_id is not None:
            self._cmd.update({
                'device_id': self._green_device_id,
                'command': '0',
            })
            response = telnet.setData(**self._cmd)
            _LOGGER.debug("Status is: %s", response)
        if self._blue_device_id is not None:
            self._cmd.update({
                'device_id': self._blue_device_id,
                'command': '0',
            })
            response = telnet.setData(**self._cmd)
            _LOGGER.debug("Status is: %s", response)
        if self._device_id is not None:
            self._cmd.update({
                'device_id': self._device_id,
                'command': '0',
            })
            response = telnet.setData(**self._cmd)
            _LOGGER.debug("Status is: %s", response)

        if self._template is None:
            self._state = False
            self.async_write_ha_state()

    @callback
    def _update_brightness(self, brightness):
        """Update the brightness from the template."""
        try:
            if brightness in (None, "None", ""):
                self._brightness = None
                return
            if 0 <= int(brightness) <= 100:
                self._brightness = int(brightness)
            else:
                _LOGGER.error(
                    "Received invalid brightness : %s for entity %s. Expected: 0-100",
                    brightness,
                    self.entity_id,
                )
                self._brightness = None
        except ValueError:
            _LOGGER.error(
                "Template must supply an integer brightness from 0-100, or 'None'",
                exc_info=True,
            )
            self._brightness = None

    @callback
    def _update_state(self, result):
        """Update the state from the template."""
        if isinstance(result, TemplateError):
            # This behavior is legacy
            self._state = False
            if not self._availability_template:
                self._attr_available = True
            return

        if isinstance(result, bool):
            self._state = result
            return

        state = str(result).lower()
        if state in _VALID_STATES:
            self._state = state in ("true", STATE_ON)
            return

        _LOGGER.error(
            "Received invalid light is_on state: %s for entity %s. Expected: %s",
            state,
            self.entity_id,
            ", ".join(_VALID_STATES),
        )
        self._state = None

    @callback
    def _update_color(self, render):
        """Update the hs_color from the template."""
        if render is None:
            self._color = None
            return

        r_str = g_str = b_str = None
        if isinstance(render, str):
            if render in ("None", ""):
                self._color = None
                return
            r_str, g_str, b_str = map(
                float, render.replace("(", "").replace(")", "").split(",", 1)
            )
        elif isinstance(render, (list, tuple)) and len(render) == 2:
            r_str, g_str, b_str = render

        if (
            h_str is not None
            and s_str is not None
            and 0 <= h_str <= 360
            and 0 <= s_str <= 100
        ):
            self._color = (r_str, g_str, b_str)
        elif r_str is not None and g_str is not None and b_str is not None:
            _LOGGER.error(
                "Received invalid rgb_color : (%s, %s, %s) for entity %s. Expected: (0-256, 0-256, 0-256)",
                r_str,
                g_str,
                b_str,
                self.entity_id,
            )
            self._color = None
        else:
            _LOGGER.error(
                "Received invalid hs_color : (%s) for entity %s", render, self.entity_id
            )
            self._color = None

    @callback
    def _update_supports_transition(self, render):
        """Update the supports transition from the template."""
        if render in (None, "None", ""):
            self._supports_transition = False
            return
        self._supports_transition = bool(render)
