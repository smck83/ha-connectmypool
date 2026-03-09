"""DataUpdateCoordinator for ConnectMyPool."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import ConnectMyPoolApi, ConnectMyPoolApiError, ConnectMyPoolThrottleError
from .const import DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)

# Short delay after an action before we fetch status, giving the pool
# controller a moment to process the command.
ACTION_REFRESH_DELAY = 2  # seconds


class ConnectMyPoolCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator that polls ConnectMyPool API for status updates.

    Polls every 61 seconds to stay safely outside the API's 60-second
    throttle window.  After any action is sent (light toggle, temp change,
    etc.) the API lifts the throttle for 5 minutes, so we immediately
    request a refresh to pick up the new state without waiting for the
    next scheduled poll.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        api: ConnectMyPoolApi,
        config: dict[str, Any],
        pool_name: str,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"ConnectMyPool ({pool_name})",
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.api = api
        self.pool_config = config
        self.pool_name = pool_name

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch the latest pool status."""
        try:
            return await self.api.get_status()
        except ConnectMyPoolThrottleError:
            _LOGGER.debug("API throttle hit, returning previous data")
            if self.data is not None:
                return self.data
            raise UpdateFailed("API throttle exceeded and no cached data available")
        except ConnectMyPoolApiError as err:
            raise UpdateFailed(f"Error communicating with ConnectMyPool: {err}") from err

    async def async_send_action_and_refresh(
        self,
        action_code: int,
        device_number: int = 0,
        value: str | int = "",
    ) -> None:
        """Send a pool action then immediately refresh status.

        Because the action lifts the 60-second throttle for 5 minutes,
        the subsequent status fetch will succeed straight away.
        """
        await self.api.pool_action(action_code, device_number, value)

        # Small delay so the controller can process the command
        import asyncio
        await asyncio.sleep(ACTION_REFRESH_DELAY)

        await self.async_request_refresh()
