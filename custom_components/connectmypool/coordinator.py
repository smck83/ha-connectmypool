"""DataUpdateCoordinator for ConnectMyPool."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import ConnectMyPoolApi, ConnectMyPoolApiError, ConnectMyPoolThrottleError
from .const import (
    ACTION_CYCLE_CHANNEL,
    CHANNEL_MODES,
    DEFAULT_SCAN_INTERVAL,
    EXECUTION_FAILED,
    EXECUTION_TIMED_OUT,
)

_LOGGER = logging.getLogger(__name__)

# Short delay after the pool confirms an action before we fetch status,
# giving its new state a moment to reach ConnectMyPool.
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
        self._channel_lock = asyncio.Lock()

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

    async def _async_send_action(
        self,
        action_code: int,
        device_number: int = 0,
        value: str | int = "",
    ) -> None:
        """Send a pool action and wait for the pool to carry it out."""
        result = await self.api.pool_action(
            action_code, device_number, value, wait_for_execution=True
        )
        if result.get("execution_status") in (EXECUTION_FAILED, EXECUTION_TIMED_OUT):
            raise HomeAssistantError("The pool did not carry out the change")

    async def async_send_action_and_refresh(
        self,
        action_code: int,
        device_number: int = 0,
        value: str | int = "",
    ) -> None:
        """Send a pool action, wait for it to finish, then refresh status.

        Because the action lifts the 60-second throttle for 5 minutes,
        the subsequent status fetch will succeed straight away.
        """
        await self._async_send_action(action_code, device_number, value)

        await asyncio.sleep(ACTION_REFRESH_DELAY)

        await self.async_request_refresh()

    def _channel_mode(self, channel_number: int) -> int | None:
        """Return the last known mode of a channel."""
        for channel in (self.data or {}).get("channels", []):
            if channel.get("channel_number") == channel_number:
                return channel.get("mode")
        return None

    async def async_set_channel_mode(self, channel_number: int, target_mode: int) -> None:
        """Cycle a channel until it reaches the target mode.

        The API can only step a channel to its next mode, and the modes on
        offer depend on the device.  If the channel comes back to a mode it
        has already passed through then the target is not one of its modes.
        """
        async with self._channel_lock:
            start_mode = self._channel_mode(channel_number)
            if start_mode == target_mode:
                return

            seen = {start_mode}
            while True:
                await self._async_send_action(ACTION_CYCLE_CHANNEL, channel_number)

                await asyncio.sleep(ACTION_REFRESH_DELAY)
                self.async_set_updated_data(await self.api.get_status())

                mode = self._channel_mode(channel_number)
                if mode == target_mode:
                    return
                if mode in seen:
                    raise HomeAssistantError(
                        f"Channel {channel_number} does not have a "
                        f"{CHANNEL_MODES[target_mode]} mode"
                    )
                seen.add(mode)
