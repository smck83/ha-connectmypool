"""Select platform for ConnectMyPool."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    ACTION_CYCLE_CHANNEL,
    ACTION_SET_FAVOURITE,
    ACTION_SET_HEAT_COOL,
    ACTION_SET_LIGHT_COLOR,
    ACTION_SET_LIGHT_MODE,
    ACTION_SET_POOL_SPA,
    ACTION_SET_SOLAR_MODE,
    ACTION_SET_VALVE_MODE,
    CHANNEL_FUNCTIONS,
    CHANNEL_MODES,
    DOMAIN,
    HEAT_COOL_MODES,
    LIGHT_COLORS,
    LIGHT_MODES,
    POOL_SPA_MODES,
    SOLAR_MODES,
    VALVE_FUNCTIONS,
    VALVE_MODES,
)
from .coordinator import ConnectMyPoolCoordinator
from .entity import ConnectMyPoolEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ConnectMyPool select entities."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: ConnectMyPoolCoordinator = data["coordinator"]
    config = data["config"]

    entities: list[SelectEntity] = []

    # Pool/Spa selection
    if config.get("pool_spa_selection_enabled"):
        entities.append(PoolSpaSelect(coordinator, entry.entry_id))

    # Heat/Cool selection
    if config.get("heat_cool_selection_enabled"):
        entities.append(HeatCoolSelect(coordinator, entry.entry_id))

    # Channel mode selects
    for channel in config.get("channels", []):
        num = channel["channel_number"]
        func = channel.get("function", 0)
        name = channel.get("name") or CHANNEL_FUNCTIONS.get(func, f"Channel {num}")
        entities.append(ChannelModeSelect(coordinator, entry.entry_id, num, name))

    # Valve mode selects
    for valve in config.get("valves", []):
        num = valve["valve_number"]
        func = valve.get("function", 0)
        name = valve.get("name") or VALVE_FUNCTIONS.get(func, f"Valve {num}")
        entities.append(ValveModeSelect(coordinator, entry.entry_id, num, name))

    # Solar mode selects
    for solar in config.get("solar_systems", []):
        num = solar["solar_number"]
        entities.append(SolarModeSelect(coordinator, entry.entry_id, num))

    # Lighting zone mode selects + colour selects
    for zone in config.get("lighting_zones", []):
        num = zone["lighting_zone_number"]
        name = zone.get("name", f"Light {num}")
        entities.append(LightModeSelect(coordinator, entry.entry_id, num, name))
        if zone.get("color_enabled"):
            colors = {
                c["color_number"]: c["color_name"]
                for c in zone.get("colors_available", [])
            }
            if not colors:
                colors = dict(LIGHT_COLORS)
            entities.append(
                LightColorSelect(coordinator, entry.entry_id, num, name, colors)
            )

    # Favourites
    favourites = config.get("favourites", [])
    if favourites:
        fav_map = {f["favourite_number"]: f["name"] for f in favourites}
        entities.append(FavouriteSelect(coordinator, entry.entry_id, fav_map))

    async_add_entities(entities)


# ---------------------------------------------------------------------------
# Pool / Spa
# ---------------------------------------------------------------------------
class PoolSpaSelect(ConnectMyPoolEntity, SelectEntity):
    """Select between Pool and Spa mode."""

    _attr_icon = "mdi:pool"
    _attr_options = list(POOL_SPA_MODES.values())

    def __init__(self, coordinator: ConnectMyPoolCoordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id, "pool_spa_select", "Pool/Spa Mode")

    @property
    def current_option(self) -> str | None:
        if self.coordinator.data is None:
            return None
        val = self.coordinator.data.get("pool_spa_selection")
        return POOL_SPA_MODES.get(val)

    async def async_select_option(self, option: str) -> None:
        reverse = {v: k for k, v in POOL_SPA_MODES.items()}
        value = reverse.get(option)
        if value is not None:
            await self.coordinator.async_send_action_and_refresh(ACTION_SET_POOL_SPA, 0, value)


# ---------------------------------------------------------------------------
# Heat / Cool
# ---------------------------------------------------------------------------
class HeatCoolSelect(ConnectMyPoolEntity, SelectEntity):
    """Select between Heating and Cooling."""

    _attr_icon = "mdi:thermostat"
    _attr_options = list(HEAT_COOL_MODES.values())

    def __init__(self, coordinator: ConnectMyPoolCoordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id, "heat_cool_select", "Heat/Cool Mode")

    @property
    def current_option(self) -> str | None:
        if self.coordinator.data is None:
            return None
        val = self.coordinator.data.get("heat_cool_selection")
        return HEAT_COOL_MODES.get(val)

    async def async_select_option(self, option: str) -> None:
        reverse = {v: k for k, v in HEAT_COOL_MODES.items()}
        value = reverse.get(option)
        if value is not None:
            await self.coordinator.async_send_action_and_refresh(ACTION_SET_HEAT_COOL, 0, value)


# ---------------------------------------------------------------------------
# Channel
# ---------------------------------------------------------------------------
class ChannelModeSelect(ConnectMyPoolEntity, SelectEntity):
    """Select a channel mode (cycles through modes via API)."""

    _attr_icon = "mdi:pump"
    _attr_options = list(CHANNEL_MODES.values())

    def __init__(
        self,
        coordinator: ConnectMyPoolCoordinator,
        entry_id: str,
        channel_number: int,
        channel_name: str,
    ) -> None:
        super().__init__(
            coordinator, entry_id,
            f"channel_{channel_number}_mode",
            f"{channel_name} Mode",
        )
        self._channel_number = channel_number

    @property
    def current_option(self) -> str | None:
        if self.coordinator.data is None:
            return None
        for ch in self.coordinator.data.get("channels", []):
            if ch.get("channel_number") == self._channel_number:
                return CHANNEL_MODES.get(ch.get("mode"))
        return None

    async def async_select_option(self, option: str) -> None:
        # Channel API uses cycle action — we cycle until we reach desired mode.
        # For simplicity, just send the cycle action once. The user may need to
        # tap multiple times for multi-step cycling.
        await self.coordinator.async_send_action_and_refresh(
            ACTION_CYCLE_CHANNEL, self._channel_number
        )


# ---------------------------------------------------------------------------
# Valve
# ---------------------------------------------------------------------------
class ValveModeSelect(ConnectMyPoolEntity, SelectEntity):
    """Select valve mode."""

    _attr_icon = "mdi:valve"
    _attr_options = list(VALVE_MODES.values())

    def __init__(
        self,
        coordinator: ConnectMyPoolCoordinator,
        entry_id: str,
        valve_number: int,
        valve_name: str,
    ) -> None:
        super().__init__(
            coordinator, entry_id,
            f"valve_{valve_number}_mode",
            f"{valve_name} Mode",
        )
        self._valve_number = valve_number

    @property
    def current_option(self) -> str | None:
        if self.coordinator.data is None:
            return None
        for v in self.coordinator.data.get("valves", []):
            if v.get("valve_number") == self._valve_number:
                return VALVE_MODES.get(v.get("mode"))
        return None

    async def async_select_option(self, option: str) -> None:
        reverse = {v: k for k, v in VALVE_MODES.items()}
        value = reverse.get(option)
        if value is not None:
            await self.coordinator.async_send_action_and_refresh(
                ACTION_SET_VALVE_MODE, self._valve_number, value
            )


# ---------------------------------------------------------------------------
# Solar
# ---------------------------------------------------------------------------
class SolarModeSelect(ConnectMyPoolEntity, SelectEntity):
    """Select solar system mode."""

    _attr_icon = "mdi:solar-power"
    _attr_options = list(SOLAR_MODES.values())

    def __init__(
        self,
        coordinator: ConnectMyPoolCoordinator,
        entry_id: str,
        solar_number: int,
    ) -> None:
        super().__init__(
            coordinator, entry_id,
            f"solar_{solar_number}_mode",
            f"Solar {solar_number} Mode",
        )
        self._solar_number = solar_number

    @property
    def current_option(self) -> str | None:
        if self.coordinator.data is None:
            return None
        for s in self.coordinator.data.get("solar_systems", []):
            if s.get("solar_number") == self._solar_number:
                return SOLAR_MODES.get(s.get("mode"))
        return None

    async def async_select_option(self, option: str) -> None:
        reverse = {v: k for k, v in SOLAR_MODES.items()}
        value = reverse.get(option)
        if value is not None:
            await self.coordinator.async_send_action_and_refresh(
                ACTION_SET_SOLAR_MODE, self._solar_number, value
            )


# ---------------------------------------------------------------------------
# Lighting Mode
# ---------------------------------------------------------------------------
class LightModeSelect(ConnectMyPoolEntity, SelectEntity):
    """Select lighting zone mode (Off/Auto/On)."""

    _attr_icon = "mdi:lightbulb-cfl"
    _attr_options = list(LIGHT_MODES.values())

    def __init__(
        self,
        coordinator: ConnectMyPoolCoordinator,
        entry_id: str,
        zone_number: int,
        zone_name: str,
    ) -> None:
        super().__init__(
            coordinator, entry_id,
            f"light_{zone_number}_mode",
            f"{zone_name} Mode",
        )
        self._zone_number = zone_number

    @property
    def current_option(self) -> str | None:
        if self.coordinator.data is None:
            return None
        for z in self.coordinator.data.get("lighting_zones", []):
            if z.get("lighting_zone_number") == self._zone_number:
                return LIGHT_MODES.get(z.get("mode"))
        return None

    async def async_select_option(self, option: str) -> None:
        reverse = {v: k for k, v in LIGHT_MODES.items()}
        value = reverse.get(option)
        if value is not None:
            await self.coordinator.async_send_action_and_refresh(
                ACTION_SET_LIGHT_MODE, self._zone_number, value
            )


# ---------------------------------------------------------------------------
# Lighting Color
# ---------------------------------------------------------------------------
class LightColorSelect(ConnectMyPoolEntity, SelectEntity):
    """Select lighting zone colour."""

    _attr_icon = "mdi:palette"

    def __init__(
        self,
        coordinator: ConnectMyPoolCoordinator,
        entry_id: str,
        zone_number: int,
        zone_name: str,
        colors: dict[int, str],
    ) -> None:
        super().__init__(
            coordinator, entry_id,
            f"light_{zone_number}_color",
            f"{zone_name} Colour",
        )
        self._zone_number = zone_number
        self._colors = colors  # {number: name}
        self._attr_options = list(colors.values())

    @property
    def current_option(self) -> str | None:
        if self.coordinator.data is None:
            return None
        for z in self.coordinator.data.get("lighting_zones", []):
            if z.get("lighting_zone_number") == self._zone_number:
                color_num = z.get("color")
                return self._colors.get(color_num)
        return None

    async def async_select_option(self, option: str) -> None:
        reverse = {v: k for k, v in self._colors.items()}
        value = reverse.get(option)
        if value is not None:
            await self.coordinator.async_send_action_and_refresh(
                ACTION_SET_LIGHT_COLOR, self._zone_number, value
            )


# ---------------------------------------------------------------------------
# Favourites
# ---------------------------------------------------------------------------
class FavouriteSelect(ConnectMyPoolEntity, SelectEntity):
    """Select active favourite."""

    _attr_icon = "mdi:star"

    def __init__(
        self,
        coordinator: ConnectMyPoolCoordinator,
        entry_id: str,
        favourites: dict[int, str],
    ) -> None:
        super().__init__(coordinator, entry_id, "favourite_select", "Active Favourite")
        self._favourites = favourites  # {number: name}
        self._attr_options = list(favourites.values())

    @property
    def current_option(self) -> str | None:
        if self.coordinator.data is None:
            return None
        active = self.coordinator.data.get("active_favourite")
        if active == 255:
            return None
        return self._favourites.get(active)

    async def async_select_option(self, option: str) -> None:
        reverse = {v: k for k, v in self._favourites.items()}
        value = reverse.get(option)
        if value is not None:
            await self.coordinator.async_send_action_and_refresh(
                ACTION_SET_FAVOURITE, value
            )
