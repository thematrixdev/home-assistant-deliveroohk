"""Config flow for the Deliveroo HK integration."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import aiohttp_client

from .const import (
    API_ENDPOINT,
    CONF_LOCALE,
    CONF_TOKEN,
    DOMAIN,
    LANG_EN,
    LANG_TC,
    LOCALE_EN,
    LOCALE_TC,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_TOKEN): str,
        vol.Required(CONF_LOCALE, default=LOCALE_EN): vol.In([LOCALE_TC, LOCALE_EN]),
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    session = aiohttp_client.async_get_clientsession(hass)

    # Set language based on locale
    lang = LANG_TC if data[CONF_LOCALE] == LOCALE_TC else LANG_EN
    
    headers = {
        "Authorization": f"Bearer {data[CONF_TOKEN]}",
        "accept-language": lang
    }
    params = {"limit": "1", "offset": "0", "include_ugc": "true"}

    _LOGGER.debug(
        "Validating token - URL: %s, Headers: %s, Params: %s",
        API_ENDPOINT,
        headers,
        params,
    )

    try:
        async with session.get(API_ENDPOINT, headers=headers, params=params) as response:
            if response.status != 200:
                raise InvalidAuth
            
            response_data = await response.json()
            _LOGGER.debug("Validation response: %s", response_data)
            
            return {"title": "Deliveroo HK"}

    except aiohttp.ClientError as err:
        _LOGGER.error("Failed to connect to Deliveroo HK API: %s", err)
        raise CannotConnect from err


class ConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Deliveroo HK."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
