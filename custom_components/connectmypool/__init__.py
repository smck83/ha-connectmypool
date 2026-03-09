"""The AstralPool ConnectMyPool integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import ConnectMyPoolApi
from .const import CONF_POOL_API_CODE, CONF_POOL_NAME, DOMAIN, PLATFORMS
from .coordinator import ConnectMyPoolCoordinator

_LOGGER = logging.getLogger(__name__)

type ConnectMyPoolConfigEntry = ConfigEntry


async def async_setup_entry(hass: HomeAssistant, entry: ConnectMyPoolConfigEntry) -> bool:
    """Set up ConnectMyPool from a config entry."""
    session = async_get_clientsession(hass)
    api = ConnectMyPoolApi(session, entry.data[CONF_POOL_API_CODE])

    # Fetch pool configuration (heaters, channels, valves, lights, favourites)
    config = await api.get_config()

    pool_name = entry.data.get(CONF_POOL_NAME, "Pool")
    coordinator = ConnectMyPoolCoordinator(hass, api, config, pool_name)

    # Fetch initial status
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "api": api,
        "config": config,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConnectMyPoolConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
