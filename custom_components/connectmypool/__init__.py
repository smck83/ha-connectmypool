"""The AstralPool ConnectMyPool integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryError, ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import ConnectMyPoolApi, ConnectMyPoolApiError, ConnectMyPoolThrottleError
from .const import (
    CONF_POOL_API_CODE,
    CONF_POOL_CONFIG,
    CONF_POOL_NAME,
    DOMAIN,
    PERMANENT_FAILURE_CODES,
    PLATFORMS,
)
from .coordinator import ConnectMyPoolCoordinator

_LOGGER = logging.getLogger(__name__)

type ConnectMyPoolConfigEntry = ConfigEntry


async def _async_get_pool_config(
    hass: HomeAssistant, entry: ConnectMyPoolConfigEntry, api: ConnectMyPoolApi
) -> dict[str, Any]:
    """Fetch the pool configuration, keeping a copy for when the API throttles.

    The config endpoint answers once every 60 seconds, so this call is
    throttled straight after the config flow or a quick restart.
    """
    try:
        config = await api.get_config()
    except ConnectMyPoolThrottleError as err:
        if CONF_POOL_CONFIG in entry.data:
            return entry.data[CONF_POOL_CONFIG]
        raise ConfigEntryNotReady(str(err)) from err
    except ConnectMyPoolApiError as err:
        if err.failure_code in PERMANENT_FAILURE_CODES:
            raise ConfigEntryError(str(err)) from err
        raise ConfigEntryNotReady(str(err)) from err

    if config != entry.data.get(CONF_POOL_CONFIG):
        hass.config_entries.async_update_entry(
            entry, data={**entry.data, CONF_POOL_CONFIG: config}
        )
    return config


async def async_setup_entry(hass: HomeAssistant, entry: ConnectMyPoolConfigEntry) -> bool:
    """Set up ConnectMyPool from a config entry."""
    session = async_get_clientsession(hass)
    api = ConnectMyPoolApi(session, entry.data[CONF_POOL_API_CODE])

    # Fetch pool configuration (heaters, channels, valves, lights, favourites)
    config = await _async_get_pool_config(hass, entry, api)

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
