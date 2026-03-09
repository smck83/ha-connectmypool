"""Base entity for ConnectMyPool."""
from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ConnectMyPoolCoordinator


class ConnectMyPoolEntity(CoordinatorEntity[ConnectMyPoolCoordinator]):
    """Base class for ConnectMyPool entities."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: ConnectMyPoolCoordinator,
        entry_id: str,
        key: str,
        name: str,
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry_id}_{key}"
        self._attr_name = name
        self._entry_id = entry_id

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry_id)},
            name=f"AstralPool {self.coordinator.pool_name}",
            manufacturer="AstralPool",
            model="ConnectMyPool",
        )
