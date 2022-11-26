"""Platform for sensor integration."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import (
    UnitOfTemperature,
    PERCENTAGE,
    STATE_ON,
    STATE_OFF,
    STATE_OPEN,
    STATE_CLOSED,
    CONF_PORT,
    CONF_HOST,
    CONF_DEVICE_ID,
    CONF_FRIENDLY_NAME,
    CONF_UNIT_OF_MEASUREMENT,
    CONF_SENSORS,
    CONF_UNIQUE_ID,
    CONF_DEVICE_CLASS,
)
import logging
from . import telnet
from typing import Any
import voluptuous as vol
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.config_validation import PLATFORM_SCHEMA
import homeassistant.helpers.config_validation as cv

CONF_DELIMITER = 'delimiter'
DEFAULT_DELIMITER = ';'
CONF_STATE_CLASS = 'state_class'
DEFAULT_STATE_CLASS = "measurement"
    # """State class for sensors."""

    # MEASUREMENT = "measurement"
    # """The state represents a measurement in present time."""

    # TOTAL = "total"
    # """The state represents a total amount.
    # For example: net energy consumption"""

    # TOTAL_INCREASING = "total_increasing"
    # """The state represents a monotonically increasing total.
    # For example: an amount of consumed gas"""
DEFAULT_DEVICE_CLASS = "temperature"
# #
#     """Device class for sensors."""

#     # Non-numerical device classes
#     DATE = "date"
#     """Date.
#     Unit of measurement: `None`
#     ISO8601 format: https://en.wikipedia.org/wiki/ISO_8601
#     """

#     DURATION = "duration"
#     """Fixed duration.
#     Unit of measurement: `d`, `h`, `min`, `s`
#     """

#     TIMESTAMP = "timestamp"
#     """Timestamp.
#     Unit of measurement: `None`
#     ISO8601 format: https://en.wikipedia.org/wiki/ISO_8601
#     """

#     # Numerical device classes, these should be aligned with NumberDeviceClass
#     APPARENT_POWER = "apparent_power"
#     """Apparent power.
#     Unit of measurement: `VA`
#     """

#     AQI = "aqi"
#     """Air Quality Index.
#     Unit of measurement: `None`
#     """

#     BATTERY = "battery"
#     """Percentage of battery that is left.
#     Unit of measurement: `%`
#     """

#     CO = "carbon_monoxide"
#     """Carbon Monoxide gas concentration.
#     Unit of measurement: `ppm` (parts per million)
#     """

#     CO2 = "carbon_dioxide"
#     """Carbon Dioxide gas concentration.
#     Unit of measurement: `ppm` (parts per million)
#     """

#     CURRENT = "current"
#     """Current.
#     Unit of measurement: `A`
#     """

#     DISTANCE = "distance"
#     """Generic distance.
#     Unit of measurement: `LENGTH_*` units
#     - SI /metric: `mm`, `cm`, `m`, `km`
#     - USCS / imperial: `in`, `ft`, `yd`, `mi`
#     """

#     ENERGY = "energy"
#     """Energy.
#     Unit of measurement: `Wh`, `kWh`, `MWh`, `GJ`
#     """

#     FREQUENCY = "frequency"
#     """Frequency.
#     Unit of measurement: `Hz`, `kHz`, `MHz`, `GHz`
#     """

#     GAS = "gas"
#     """Gas.
#     Unit of measurement: `m³`, `ft³`
#     """

#     HUMIDITY = "humidity"
#     """Relative humidity.
#     Unit of measurement: `%`
#     """

#     ILLUMINANCE = "illuminance"
#     """Illuminance.
#     Unit of measurement: `lx`, `lm`
#     """

#     MOISTURE = "moisture"
#     """Moisture.
#     Unit of measurement: `%`
#     """

#     MONETARY = "monetary"
#     """Amount of money.
#     Unit of measurement: ISO4217 currency code
#     See https://en.wikipedia.org/wiki/ISO_4217#Active_codes for active codes
#     """

#     NITROGEN_DIOXIDE = "nitrogen_dioxide"
#     """Amount of NO2.
#     Unit of measurement: `µg/m³`
#     """

#     NITROGEN_MONOXIDE = "nitrogen_monoxide"
#     """Amount of NO.
#     Unit of measurement: `µg/m³`
#     """

#     NITROUS_OXIDE = "nitrous_oxide"
#     """Amount of N2O.
#     Unit of measurement: `µg/m³`
#     """

#     OZONE = "ozone"
#     """Amount of O3.
#     Unit of measurement: `µg/m³`
#     """

#     PM1 = "pm1"
#     """Particulate matter <= 0.1 μm.
#     Unit of measurement: `µg/m³`
#     """

#     PM10 = "pm10"
#     """Particulate matter <= 10 μm.
#     Unit of measurement: `µg/m³`
#     """

#     PM25 = "pm25"
#     """Particulate matter <= 2.5 μm.
#     Unit of measurement: `µg/m³`
#     """

#     POWER_FACTOR = "power_factor"
#     """Power factor.
#     Unit of measurement: `%`
#     """

#     POWER = "power"
#     """Power.
#     Unit of measurement: `W`, `kW`
#     """

#     PRECIPITATION = "precipitation"
#     """Precipitation.
#     Unit of measurement:
#     - SI / metric: `mm`
#     - USCS / imperial: `in`
#     """

#     PRECIPITATION_INTENSITY = "precipitation_intensity"
#     """Precipitation intensity.
#     Unit of measurement: UnitOfVolumetricFlux
#     - SI /metric: `mm/d`, `mm/h`
#     - USCS / imperial: `in/d`, `in/h`
#     """

#     PRESSURE = "pressure"
#     """Pressure.
#     Unit of measurement:
#     - `mbar`, `cbar`, `bar`
#     - `Pa`, `hPa`, `kPa`
#     - `inHg`
#     - `psi`
#     """

#     REACTIVE_POWER = "reactive_power"
#     """Reactive power.
#     Unit of measurement: `var`
#     """

#     SIGNAL_STRENGTH = "signal_strength"
#     """Signal strength.
#     Unit of measurement: `dB`, `dBm`
#     """

#     SPEED = "speed"
#     """Generic speed.
#     Unit of measurement: `SPEED_*` units or `UnitOfVolumetricFlux`
#     - SI /metric: `mm/d`, `mm/h`, `m/s`, `km/h`
#     - USCS / imperial: `in/d`, `in/h`, `ft/s`, `mph`
#     - Nautical: `kn`
#     """

#     SULPHUR_DIOXIDE = "sulphur_dioxide"
#     """Amount of SO2.
#     Unit of measurement: `µg/m³`
#     """

#     TEMPERATURE = "temperature"
#     """Temperature.
#     Unit of measurement: `°C`, `°F`
#     """

#     VOLATILE_ORGANIC_COMPOUNDS = "volatile_organic_compounds"
#     """Amount of VOC.
#     Unit of measurement: `µg/m³`
#     """

#     VOLTAGE = "voltage"
#     """Voltage.
#     Unit of measurement: `V`
#     """

#     VOLUME = "volume"
#     """Generic volume.
#     Unit of measurement: `VOLUME_*` units
#     - SI / metric: `mL`, `L`, `m³`
#     - USCS / imperial: `fl. oz.`, `ft³`, `gal` (warning: volumes expressed in
#     USCS/imperial units are currently assumed to be US volumes)
#     """

#     WATER = "water"
#     """Water.
#     Unit of measurement:
#     - SI / metric: `m³`, `L`
#     - USCS / imperial: `ft³`, `gal` (warning: volumes expressed in
#     USCS/imperial units are currently assumed to be US volumes)
#     """

#     WEIGHT = "weight"
#     """Generic weight, represents a measurement of an object's mass.
#     Weight is used instead of mass to fit with every day language.
#     Unit of measurement: `MASS_*` units
#     - SI / metric: `µg`, `mg`, `g`, `kg`
#     - USCS / imperial: `oz`, `lb`
#     """

#     WIND_SPEED = "wind_speed"
#     """Wind speed.
#     Unit of measurement: `SPEED_*` units
#     - SI /metric: `m/s`, `km/h`
#     - USCS / imperial: `ft/s`, `mph`
#     - Nautical: `kn`
#     """




_LOGGER = logging.getLogger(__name__)

SENSOR_SCHEMA = vol.All(
    vol.Schema(
        {
            vol.Optional(CONF_FRIENDLY_NAME): cv.string,
            vol.Optional(CONF_DELIMITER, default=DEFAULT_DELIMITER): cv.string,
            vol.Optional(CONF_DEVICE_CLASS, default=DEFAULT_DEVICE_CLASS): cv.string,
            vol.Optional(CONF_STATE_CLASS, default=DEFAULT_STATE_CLASS): cv.string,
            vol.Required(CONF_HOST): cv.string,
            vol.Required(CONF_PORT): cv.port,
            vol.Required(CONF_DEVICE_ID): cv.string,
            vol.Optional(CONF_UNIT_OF_MEASUREMENT): cv.string,
        }
    ),
)
PLATFORM_SCHEMA = vol.All(
    PLATFORM_SCHEMA.extend(
        {vol.Required(CONF_SENSORS): cv.schema_with_slug_keys(SENSOR_SCHEMA)}
    ),
)

async def _async_create_entities(hass, config):
    """Create the Template Lights."""
    sensors = []

    for object_id, entity_config in config[CONF_SENSORS].items():
        unique_id = entity_config.get(CONF_UNIQUE_ID)
        lights.append(
            ELKOSensors(
                hass,
                object_id,
                entity_config,
                unique_id,
            )
        )

    return sensors

async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the sensors."""
    async_add_entities(await _async_create_entities(hass, config))

class ELKOSensors(SensorEntity):
    def __init__(
        self,
        hass,
        object_id,
        config,
        unique_id,
    ):
        """Initialize the Sensor."""
        self._friendly_name = config.get(CONF_FRIENDLY_NAME)
        self._cmd = {
            'host': config.get(CONF_HOST),
            'port': config.get(CONF_PORT),
            'delimiter': config.get(CONF_DELIMITER),
            'device_id': config.get(CONF_DEVICE_ID),
        }
        self._attr_native_unit_of_measurement = config.get(CONF_UNIT_OF_MEASUREMENT)
        self._attr_name = config.get(CONF_FRIENDLY_NAME)
        self._attr_device_class = config.get(CONF_DEVICE_CLASS)
        self._attr_state_class = config.get(CONF_STATE_CLASS)
        self._attr_native_value = None

    def async_update(self) -> None:
        """Fetch new state data for the sensor.
        This is the only method that should fetch new data for Home Assistant.
        """
        response = telnet.getData(**self._cmd)
        _LOGGER.debug("Status is: %s", response)
        if self._attr_device_class == 'binary':
            if self._attr_native_unit_of_measurement == 'on/off':
                if response == '1':
                    self._attr_native_value = 'on'
                else:
                    self._attr_native_value = 'off'
            if self._attr_native_unit_of_measurement == 'off/on':
                if response == '0':
                    self._attr_native_value = 'on'
                else:
                    self._attr_native_value = 'off'
            if self._attr_native_unit_of_measurement == 'open/closed':
                if response == '1':
                    self._attr_native_value = 'open'
                else:
                    self._attr_native_value = 'closed'
            if self._attr_native_unit_of_measurement == 'closed/open':
                if response == '0':
                    self._attr_native_value = 'open'
                else:
                    self._attr_native_value = 'closed'
        else:
            self._attr_native_value = int( response * 0.01 )
