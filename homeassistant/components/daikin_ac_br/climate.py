"""Support for the Daikin HVAC."""

from __future__ import annotations

import voluptuous as vol

from homeassistant.components.climate import (
    ATTR_TEMPERATURE,
    FAN_AUTO,
    FAN_HIGH,
    FAN_LOW,
    FAN_MEDIUM,
    PLATFORM_SCHEMA,
    SWING_OFF,
    SWING_VERTICAL,
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_NAME, UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import DOMAIN
from .coordinator import DaikinACBRCoordinator

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {vol.Required(CONF_HOST): cv.string, vol.Optional(CONF_NAME): cv.string}
)


DAIKIN_FAN_TO_HA_FAN = {
    3: FAN_LOW,
    4: FAN_LOW,
    5: FAN_MEDIUM,
    6: FAN_HIGH,
    7: FAN_HIGH,
    17: FAN_AUTO,
}


DAIKIN_MODE_TO_HA_MODE = {
    6: HVACMode.FAN_ONLY,
    3: HVACMode.COOL,
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Daikin climate based on config_entry."""
    api = hass.data[DOMAIN].get(entry.entry_id)

    coordinator = DaikinACBRCoordinator(hass, api)

    await coordinator.async_config_entry_first_refresh()

    async_add_entities([DaikinBRClimate(coordinator, "1")], update_before_add=True)


class DaikinBRClimate(CoordinatorEntity, ClimateEntity):
    _attr_has_entity_name = True
    _attr_name = "DaikinBRClimate"
    _attr_temperature_unit = UnitOfTemperature.CELSIUS

    _attr_hvac_modes = [HVACMode.FAN_ONLY, HVACMode.COOL, HVACMode.OFF, HVACMode.AUTO]
    _attr_hvac_mode = HVACMode.FAN_ONLY

    _attr_fan_modes: list[str] = [FAN_LOW, FAN_MEDIUM, FAN_HIGH, FAN_AUTO]
    _attr_fan_mode = FAN_AUTO

    _attr_supported_features = (
        ClimateEntityFeature.FAN_MODE
        | ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.TURN_OFF
        | ClimateEntityFeature.TURN_ON
        | ClimateEntityFeature.SWING_MODE
    )

    _attr_swing_mode = SWING_OFF
    _attr_swing_modes = [SWING_OFF, SWING_VERTICAL]

    _attr_target_temperature_step = 1
    _enable_turn_on_off_backwards_compatibility = False

    def __init__(self, coordinator: DaikinACBRCoordinator, idx):
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator, context=idx)
        self.idx = idx
        self._attr_name = f"DaikinBRClimate ${idx}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self.unique_id)},
            manufacturer="Daikin",
        )

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return "123456"
        # TODO: Implement this
        # return self._api.device.mac

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        data = self.coordinator.data["port1"]

        self._attr_current_temperature = data["sensors"]["room_temp"]
        self._attr_fan_mode = DAIKIN_FAN_TO_HA_FAN[data["fan"]]

        self._attr_hvac_mode = (
            HVACMode.OFF if data["power"] == 0 else DAIKIN_MODE_TO_HA_MODE[data["mode"]]
        )
        self._attr_target_temperature = data["temperature"]

        self.swing_mode = SWING_OFF if data["v_swing"] == 0 else SWING_VERTICAL

        self.async_write_ha_state()

    async def async_set_swing_mode(self, swing_mode: str) -> None:
        """Set new target temperature."""

        SWING_MODES = {
            SWING_OFF: 0,
            SWING_VERTICAL: 1,
        }

        self.coordinator.api.send_command({"v_swing": SWING_MODES[swing_mode]})

        await self.coordinator.async_request_refresh()

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """Set new target temperature."""

        FAN_MODES = {
            FAN_LOW: 3,
            FAN_MEDIUM: 5,
            FAN_HIGH: 6,
            FAN_AUTO: 7,
        }

        self.coordinator.api.send_command({"fan": FAN_MODES[fan_mode]})

        await self.coordinator.async_request_refresh()

    async def async_turn_on(self) -> None:
        """Turn the entity on."""
        self.coordinator.api.send_command({"power": 1})
        await self.coordinator.async_request_refresh()

    async def async_set_hvac_mode(self, hvac_mode: str) -> None:
        """Set new target temperature."""

        HVAC_MODES = {
            HVACMode.FAN_ONLY: 6,
            HVACMode.COOL: 3,
            HVACMode.OFF: 0,
            HVACMode.AUTO: 0,
        }

        if hvac_mode == HVACMode.OFF:
            self.coordinator.api.send_command({"power": 0})
        else:
            self.coordinator.api.send_command({"mode": HVAC_MODES[hvac_mode]})

        await self.coordinator.async_request_refresh()

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set a new target temperature."""

        # Ignore if HVAC is fan only
        if self.hvac_mode != HVACMode.COOL:
            return

        self.coordinator.api.send_command({"temperature": kwargs[ATTR_TEMPERATURE]})

        await self.coordinator.async_request_refresh()
