"""API client for ConnectMyPool."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp

from .const import (
    API_POOL_ACTION,
    API_POOL_ACTION_STATUS,
    API_POOL_CONFIG,
    API_POOL_STATUS,
)

_LOGGER = logging.getLogger(__name__)

HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "HomeAssistant-ConnectMyPool/1.0",
}


class ConnectMyPoolApiError(Exception):
    """Base exception for API errors."""

    def __init__(self, failure_code: int, failure_description: str) -> None:
        self.failure_code = failure_code
        self.failure_description = failure_description
        super().__init__(f"API error {failure_code}: {failure_description}")


class ConnectMyPoolThrottleError(ConnectMyPoolApiError):
    """Raised when the API time throttle is exceeded."""


class ConnectMyPoolApi:
    """Client for the ConnectMyPool REST API."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        pool_api_code: str,
    ) -> None:
        self._session = session
        self._pool_api_code = pool_api_code

    async def _post(self, url: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Make a POST request and return the JSON response."""
        try:
            async with self._session.post(
                url, json=payload, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                data = await resp.json()
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise ConnectMyPoolApiError(0, f"Connection error: {err}") from err

        if "failure_code" in data:
            code = data["failure_code"]
            desc = data.get("failure_description", "Unknown error")
            if code == 6:
                raise ConnectMyPoolThrottleError(code, desc)
            raise ConnectMyPoolApiError(code, desc)

        return data

    async def get_config(self) -> dict[str, Any]:
        """Fetch pool configuration."""
        return await self._post(
            API_POOL_CONFIG,
            {"pool_api_code": self._pool_api_code},
        )

    async def get_status(self) -> dict[str, Any]:
        """Fetch current pool status."""
        return await self._post(
            API_POOL_STATUS,
            {
                "pool_api_code": self._pool_api_code,
                "temperature_scale": 0,  # Celsius
            },
        )

    async def pool_action(
        self,
        action_code: int,
        device_number: int = 0,
        value: str | int = "",
        wait_for_execution: bool = False,
    ) -> dict[str, Any]:
        """Send a pool action command."""
        payload: dict[str, Any] = {
            "pool_api_code": self._pool_api_code,
            "action_code": action_code,
            "device_number": device_number,
            "value": str(value),
            "temperature_scale": 0,
            "wait_for_execution": wait_for_execution,
        }
        return await self._post(API_POOL_ACTION, payload)

    async def get_action_status(self, action_number: int) -> dict[str, Any]:
        """Check execution status of a previously sent action."""
        return await self._post(
            API_POOL_ACTION_STATUS,
            {
                "pool_api_code": self._pool_api_code,
                "action_number": action_number,
            },
        )

    async def validate(self) -> bool:
        """Validate the API code by fetching config. Returns True on success."""
        await self.get_config()
        return True
