"""Light platform for ELKO_telnet."""
import logging

from pyinels.device.pyLight import pyLight
from pyinels.const import RANGE_BRIGHTNESS

from homeassistant.components.light import LightEntity
from homeassistant.components.light import ATTR_BRIGHTNESS, SUPPORT_BRIGHTNESS, PLATFORM_SCHEMA

from custom_components.ELKO_Telnet.entity import ElkoEntity
from custom_components.ELKO_Telnet.const import DOMAIN, DOMAIN_DATA, ICON_LIGHT, PLATFORM_LIGHT
from homeassistant.const import (
    CONF_NAME,
    CONF_PORT,
    CONF_HOST,
    CONF_DEVICE_ID,
    CONF_LIGHTS,
    CONF_TIMEOUT,
)
import voluptuous as vol

_LOGGER = logging.getLogger(__name__)

MIN_BRIGHTNESS = RANGE_BRIGHTNESS[0]
MAX_BRIGHTNESS = RANGE_BRIGHTNESS[1]

LIGHT_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_PORT): cv.string,
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_DEVICE_ID): cv.string
        vol.Optional(CONF_NAME): cv.string,
        vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): vol.Coerce(float),
    }
)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {vol.Required(CONF_LIGHTS): cv.schema_with_slug_keys(LIGHT_SCHEMA)}
)



async def async_setup_entry(hass, entry, async_add_devices):
    """Setup light platform."""

    _LOGGER.info("Setting up lights")

    devices = hass.data[DOMAIN][DOMAIN_DATA]
    coordinator = hass.data[DOMAIN][entry.entry_id]

    dimmable_lights = []
    usual_lights = []

    lights = [
        await hass.async_add_executor_job(pyLight, dev)
        for dev in devices
        if dev.type == PLATFORM_LIGHT
    ]

    for light in lights:
        if light.has_brightness is True:
            dimmable_lights.append(light)
        else:
            usual_lights.append(light)

    await coordinator.async_refresh()

    if len(usual_lights) > 0:
        async_add_devices(
            [ElkoLight(coordinator, light) for light in usual_lights], True
        )

    if len(dimmable_lights) > 0:
        async_add_devices(
            [ElkoLightDimmable(coordinator, light) for light in dimmable_lights], True
        )


class ElkoLightBase(ElkoEntity, LightEntity):
    """Inels base light class."""

    def __init__(self, coordinator, light):
        """Initialize of the InelsLight."""
        super().__init__(coordinator, light)

        self._light = light
        self._coordinator = coordinator
        self._state = False
        self._delimiter = ';'

    def _telnet_command(self, command) -> str | None:
        try:
            _LOGGER.debug("Telnet connect to: %s with port: %s", self._resource, self._port)
            telnet = telnetlib.Telnet(self._resource, self._port)
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

    async def async_turn_on(self, **kwargs):  # pylint: disable=unused-argument
        """Turn on the light."""
        command = b"SET" + self._delimiter.encode('ascii') + self._device_id.encode('ascii')+ self._delimiter.encode('ascii')+ self._command_on.encode('ascii') + b"\r\n"
        _LOGGER.debug("Turn On: %s", command)
        # await self.hass.async_add_executor_job(self._light.turn_on)
        self._state = True

        await self._coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):  # pylint: disable=unused-argument
        """Turn off the light."""
        command = b"SET" + self._delimiter.encode('ascii') + self._device_id.encode('ascii')+ self._delimiter.encode('ascii')+ self._command_off.encode('ascii') + b"\r\n"
        _LOGGER.debug("Turn Off: %s", command)
        # await self.hass.async_add_executor_job(self._light.turn_off)
        self._state = False

        await self._coordinator.async_request_refresh()

    @property
    def name(self):
        """Return the name of the light."""
        return self._light.name

    @property
    def icon(self):
        """Return the icon of this light."""
        return ICON_LIGHT

    @property
    def is_on(self):
        """Return true if the light is on."""
        return self._light.state

    def update(self):
        """Update the data from the device."""
        return self.update()


class ElkoLight(ElkoLightBase, LightEntity):
    """Inels light class."""

    def __init__(self, coordinator, light):
        """Initialize of the InelsLight."""
        super().__init__(coordinator, light)


class ElkoLightDimmable(ElkoLightBase, LightEntity):
    """Inels dimmable light class."""

    def __init__(self, coordinator, light):
        """Initialize of the InelsLightDimmable."""
        super().__init__(coordinator, light)

        self._brightness = None
        self._features = 0
        self._light = light
        self._coordinator = coordinator
        self._has_brightness = True
        self._state = False

        if self._has_brightness is True:
            self._features = SUPPORT_BRIGHTNESS

    @property
    def supported_features(self):
        """Supported feature of the light. We support brightnes.
        In future maybee i RGB and temperature."""
        return self._features

    @property
    def brightness(self):
        """Return the brightness of the light."""
        if self._has_brightness is True:
            self._brightness = self._light.brightness()

            return int(self._brightness * 2.55)
        return None

    async def async_turn_on(self, **kwargs):  # pylint: disable=unused-argument
        """Turn on the light."""
        brightness = 0

        if ATTR_BRIGHTNESS in kwargs:
            brightness = int(kwargs[ATTR_BRIGHTNESS] / 2.55)
            self._brightness = brightness
            await self.hass.async_add_executor_job(
                self._light.set_brightness, float(brightness)
            )
            self._state = self._light.state
        else:
            await self.hass.async_add_executor_job(self._light.turn_on)
            self._brightness = MAX_BRIGHTNESS
            self._state = True

        await self._coordinator.async_request_refresh()