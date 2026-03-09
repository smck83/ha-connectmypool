"""Config flow for ConnectMyPool integration."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import ConnectMyPoolApi, ConnectMyPoolApiError
from .const import CONF_POOL_API_CODE, CONF_POOL_NAME, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_POOL_API_CODE): str,
        vol.Optional(CONF_POOL_NAME, default="Pool"): str,
    }
)


class ConnectMyPoolConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for ConnectMyPool."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            api_code = user_input[CONF_POOL_API_CODE].strip()
            pool_name = user_input.get(CONF_POOL_NAME, "Pool").strip()

            # Prevent duplicate entries for the same API code
            await self.async_set_unique_id(api_code)
            self._abort_if_unique_id_configured()

            session = async_get_clientsession(self.hass)
            api = ConnectMyPoolApi(session, api_code)

            try:
                await api.validate()
            except ConnectMyPoolApiError as err:
                _LOGGER.error("Validation failed: %s", err)
                if err.failure_code in (2, 3, 5):
                    errors["base"] = "invalid_auth"
                elif err.failure_code == 4:
                    errors["base"] = "api_not_enabled"
                elif err.failure_code == 7:
                    errors["base"] = "pool_not_connected"
                else:
                    errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=pool_name,
                    data={
                        CONF_POOL_API_CODE: api_code,
                        CONF_POOL_NAME: pool_name,
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
