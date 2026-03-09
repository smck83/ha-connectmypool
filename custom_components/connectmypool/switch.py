"""Switch platform for ConnectMyPool."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    ACTION_SET_HEATER_MODE,
    ACTION_SET_LIGHT_MODE,
    DOMAIN,
)
from .coordinator import ConnectMyPoolCoordinator
from .entity import ConnectMyPoolEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ConnectMyPool switch entities."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: ConnectMyPoolCoordinator = data["coordinator"]
    config = data["config"]

    entities: list[SwitchEntity] = []

    # Heater switches
    for heater in config.get("heaters", []):
        num = heater["heater_number"]
        entities.append(HeaterSwitch(coordinator, entry.entry_id, num))

    # Lighting zone switches (simple on/off)
    for zone in config.get("lighting_zones", []):
        num = zone["lighting_zone_number"]
        name = zone.get("name", f"Light {num}")
        entities.append(LightSwitch(coordinator, entry.entry_id, num, name))

    async_add_entities(entities)


class HeaterSwitch(ConnectMyPoolEntity, SwitchEntity):
    """Switch to turn a heater on/off."""

    _attr_icon = "mdi:water-boiler"

    def __init__(
        self,
        coordinator: ConnectMyPoolCoordinator,
        entry_id: str,
        heater_number: int,
    ) -> None:
        super().__init__(
            coordinator, entry_id,
            f"heater_{heater_number}_switch",
            f"Heater {heater_number}",
        )
        self._heater_number = heater_number

    @property
    def is_on(self) -> bool | None:
        if self.coordinator.data is None:
            return None
        for h in self.coordinator.data.get("heaters", []):
            if h.get("heater_number") == self._heater_number:
                return h.get("mode") == 1
        return None

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.async_send_action_and_refresh(
            ACTION_SET_HEATER_MODE, self._heater_number, 1
        )

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.async_send_action_and_refresh(
            ACTION_SET_HEATER_MODE, self._heater_number, 0
        )


class LightSwitch(ConnectMyPoolEntity, SwitchEntity):
    """Switch to turn a lighting zone on/off."""

    _attr_icon = "mdi:lightbulb"

    def __init__(
        self,
        coordinator: ConnectMyPoolCoordinator,
        entry_id: str,
        zone_number: int,
        zone_name: str,
    ) -> None:
        super().__init__(
            coordinator, entry_id,
            f"light_{zone_number}_switch",
            zone_name,
        )
        self._zone_number = zone_number

    @property
    def is_on(self) -> bool | None:
        if self.coordinator.data is None:
            return None
        for z in self.coordinator.data.get("lighting_zones", []):
            if z.get("lighting_zone_number") == self._zone_number:
                return z.get("mode") in (1, 2)  # Auto or On
        return None

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.async_send_action_and_refresh(
            ACTION_SET_LIGHT_MODE, self._zone_number, 2  # On
        )

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.async_send_action_and_refresh(
            ACTION_SET_LIGHT_MODE, self._zone_number, 0  # Off
        )
