"""Number platform for ConnectMyPool."""
from __future__ import annotations

import logging

from homeassistant.components.number import NumberDeviceClass, NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    ACTION_SET_HEATER_TEMP,
    ACTION_SET_SOLAR_TEMP,
    DOMAIN,
    POOL_MODE,
    POOL_SPA_MODES,
    SPA_MODE,
)
from .coordinator import ConnectMyPoolCoordinator
from .entity import ConnectMyPoolEntity

_LOGGER = logging.getLogger(__name__)


def _ensure_pool_spa_mode(coordinator: ConnectMyPoolCoordinator, required_mode: int) -> None:
    """Refuse a change the API would apply to the other mode's set temperature.

    On a combined system the API always writes the set temperature of the
    active mode, whichever entity the change came from.
    """
    if not coordinator.pool_config.get("pool_spa_selection_enabled"):
        return
    current_mode = (coordinator.data or {}).get("pool_spa_selection")
    if current_mode is not None and current_mode != required_mode:
        raise HomeAssistantError(
            f"Switch to {POOL_SPA_MODES[required_mode]} mode to change this temperature"
        )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ConnectMyPool number entities."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: ConnectMyPoolCoordinator = data["coordinator"]
    config = data["config"]

    entities: list[NumberEntity] = []

    for heater in config.get("heaters", []):
        num = heater["heater_number"]
        entities.append(HeaterSetTempNumber(coordinator, entry.entry_id, num))
        # Spa set temp only relevant for combined pool/spa
        if config.get("pool_spa_selection_enabled"):
            entities.append(HeaterSpaSetTempNumber(coordinator, entry.entry_id, num))

    for solar in config.get("solar_systems", []):
        num = solar["solar_number"]
        entities.append(SolarSetTempNumber(coordinator, entry.entry_id, num))

    async_add_entities(entities)


class HeaterSetTempNumber(ConnectMyPoolEntity, NumberEntity):
    """Number entity to adjust heater set temperature."""

    _attr_device_class = NumberDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_native_min_value = 10
    _attr_native_max_value = 40
    _attr_native_step = 1
    _attr_mode = NumberMode.SLIDER
    _attr_icon = "mdi:thermometer"

    def __init__(
        self,
        coordinator: ConnectMyPoolCoordinator,
        entry_id: str,
        heater_number: int,
    ) -> None:
        super().__init__(
            coordinator, entry_id,
            f"heater_{heater_number}_set_temp",
            f"Heater {heater_number} Set Temperature",
        )
        self._heater_number = heater_number

    @property
    def native_value(self) -> float | None:
        if self.coordinator.data is None:
            return None
        for h in self.coordinator.data.get("heaters", []):
            if h.get("heater_number") == self._heater_number:
                return h.get("set_temperature")
        return None

    async def async_set_native_value(self, value: float) -> None:
        _ensure_pool_spa_mode(self.coordinator, POOL_MODE)
        await self.coordinator.async_send_action_and_refresh(
            ACTION_SET_HEATER_TEMP, self._heater_number, int(value)
        )


class HeaterSpaSetTempNumber(ConnectMyPoolEntity, NumberEntity):
    """Number entity to adjust heater spa set temperature."""

    _attr_device_class = NumberDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_native_min_value = 10
    _attr_native_max_value = 40
    _attr_native_step = 1
    _attr_mode = NumberMode.SLIDER
    _attr_icon = "mdi:hot-tub"

    def __init__(
        self,
        coordinator: ConnectMyPoolCoordinator,
        entry_id: str,
        heater_number: int,
    ) -> None:
        super().__init__(
            coordinator, entry_id,
            f"heater_{heater_number}_spa_set_temp",
            f"Heater {heater_number} Spa Set Temperature",
        )
        self._heater_number = heater_number

    @property
    def native_value(self) -> float | None:
        if self.coordinator.data is None:
            return None
        for h in self.coordinator.data.get("heaters", []):
            if h.get("heater_number") == self._heater_number:
                return h.get("spa_set_temperature")
        return None

    async def async_set_native_value(self, value: float) -> None:
        _ensure_pool_spa_mode(self.coordinator, SPA_MODE)
        await self.coordinator.async_send_action_and_refresh(
            ACTION_SET_HEATER_TEMP, self._heater_number, int(value)
        )


class SolarSetTempNumber(ConnectMyPoolEntity, NumberEntity):
    """Number entity to adjust solar set temperature."""

    _attr_device_class = NumberDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_native_min_value = 10
    _attr_native_max_value = 40
    _attr_native_step = 1
    _attr_mode = NumberMode.SLIDER
    _attr_icon = "mdi:solar-power-variant"

    def __init__(
        self,
        coordinator: ConnectMyPoolCoordinator,
        entry_id: str,
        solar_number: int,
    ) -> None:
        super().__init__(
            coordinator, entry_id,
            f"solar_{solar_number}_set_temp",
            f"Solar {solar_number} Set Temperature",
        )
        self._solar_number = solar_number

    @property
    def native_value(self) -> float | None:
        if self.coordinator.data is None:
            return None
        for s in self.coordinator.data.get("solar_systems", []):
            if s.get("solar_number") == self._solar_number:
                return s.get("set_temperature")
        return None

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_send_action_and_refresh(
            ACTION_SET_SOLAR_TEMP, self._solar_number, int(value)
        )
