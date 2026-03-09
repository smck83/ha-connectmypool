"""Sensor platform for ConnectMyPool."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import ConnectMyPoolCoordinator
from .entity import ConnectMyPoolEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ConnectMyPool sensor entities."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: ConnectMyPoolCoordinator = data["coordinator"]

    entities: list[SensorEntity] = [
        PoolTemperatureSensor(coordinator, entry.entry_id),
    ]

    # Per-heater set temp sensors
    config = data["config"]
    for heater in config.get("heaters", []):
        num = heater["heater_number"]
        entities.append(
            HeaterSetTempSensor(coordinator, entry.entry_id, num, is_spa=False)
        )
        entities.append(
            HeaterSetTempSensor(coordinator, entry.entry_id, num, is_spa=True)
        )

    # Per-solar set temp sensors
    for solar in config.get("solar_systems", []):
        num = solar["solar_number"]
        entities.append(SolarSetTempSensor(coordinator, entry.entry_id, num))

    async_add_entities(entities)


class PoolTemperatureSensor(ConnectMyPoolEntity, SensorEntity):
    """Current water temperature sensor."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(self, coordinator: ConnectMyPoolCoordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id, "temperature", "Water Temperature")

    @property
    def native_value(self) -> float | None:
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get("temperature")


class HeaterSetTempSensor(ConnectMyPoolEntity, SensorEntity):
    """Heater set temperature (read-only sensor view)."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_entity_registry_enabled_default = False  # disabled by default, number entity is primary

    def __init__(
        self,
        coordinator: ConnectMyPoolCoordinator,
        entry_id: str,
        heater_number: int,
        is_spa: bool,
    ) -> None:
        suffix = "spa_set_temp" if is_spa else "set_temp"
        label = "Spa Set Temp" if is_spa else "Set Temp"
        super().__init__(
            coordinator,
            entry_id,
            f"heater_{heater_number}_{suffix}_sensor",
            f"Heater {heater_number} {label}",
        )
        self._heater_number = heater_number
        self._is_spa = is_spa

    @property
    def native_value(self) -> float | None:
        if self.coordinator.data is None:
            return None
        for h in self.coordinator.data.get("heaters", []):
            if h.get("heater_number") == self._heater_number:
                key = "spa_set_temperature" if self._is_spa else "set_temperature"
                return h.get(key)
        return None


class SolarSetTempSensor(ConnectMyPoolEntity, SensorEntity):
    """Solar set temperature (read-only sensor view)."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: ConnectMyPoolCoordinator,
        entry_id: str,
        solar_number: int,
    ) -> None:
        super().__init__(
            coordinator, entry_id,
            f"solar_{solar_number}_set_temp_sensor",
            f"Solar {solar_number} Set Temp",
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
