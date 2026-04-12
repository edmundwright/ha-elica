"""Adds config flow for Elica integration."""

from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.loader import async_get_loaded_integration

from .api import (
    ElicaIntegrationApiClient,
    ElicaIntegrationApiClientAuthenticationError,
    ElicaIntegrationApiClientCommunicationError,
    ElicaIntegrationApiClientError,
)
from .const import DOMAIN, LOGGER


class ElicaIntegrationConfigFlowError(Exception):
    """Exception to indicate an error in Elica config flow."""


class ElicaIntegrationConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Elica integration."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle a flow initialized by the user."""
        _errors = {}
        if user_input is not None:
            user_id: str
            try:
                username = user_input[CONF_USERNAME]
                password = user_input[CONF_PASSWORD]
                user_id = await self._get_user_id(username, password)
            except ElicaIntegrationApiClientAuthenticationError as exception:
                LOGGER.warning(exception)
                _errors["base"] = "auth"
            except ElicaIntegrationApiClientCommunicationError as exception:
                LOGGER.error(exception)
                _errors["base"] = "connection"
            except ElicaIntegrationApiClientError as exception:
                LOGGER.exception(exception)
                _errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(
                    unique_id=user_id,
                )
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=user_input[CONF_USERNAME],
                    data={
                        CONF_USERNAME: user_input[CONF_USERNAME],
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                    },
                )

        integration = async_get_loaded_integration(self.hass, DOMAIN)
        assert integration.documentation is not None, (  # noqa: S101
            "Integration documentation URL is not set in manifest.json"
        )

        return self.async_show_form(
            step_id="user",
            description_placeholders={
                "documentation_url": integration.documentation,
            },
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_USERNAME,
                        default=(user_input or {}).get(CONF_USERNAME, vol.UNDEFINED),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT,
                        ),
                    ),
                    vol.Required(CONF_PASSWORD): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.PASSWORD,
                        ),
                    ),
                },
            ),
            errors=_errors,
        )

    async def _get_user_id(self, username: str, password: str) -> str:
        """Get user ID for the authenticated user."""
        client = ElicaIntegrationApiClient(
            async_create_clientsession(self.hass),
            username=username,
            password=password,
        )
        return await client.get_user_id()
