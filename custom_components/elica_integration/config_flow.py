"""Adds config flow for Elica integration."""

from __future__ import annotations

from os import access

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_ACCESS_TOKEN, CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.loader import async_get_loaded_integration
from httpx import get

from .api import (
    AuthTokens,
    BasicElicaIntegrationApiClient,
    ElicaIntegrationApiClient,
    ElicaIntegrationApiClientAuthenticationError,
    ElicaIntegrationApiClientCommunicationError,
    ElicaIntegrationApiClientError,
)
from .const import CONF_REFRESH_TOKEN, DOMAIN, LOGGER


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
            auth_tokens: AuthTokens
            try:
                auth_tokens = await self._get_auth_tokens(
                    username=user_input[CONF_USERNAME],
                    password=user_input[CONF_PASSWORD],
                )
                user_id = await self._get_user_id(auth_tokens)
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
                        CONF_ACCESS_TOKEN: auth_tokens.access_token,
                        CONF_REFRESH_TOKEN: auth_tokens.refresh_token,
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

    async def _get_auth_tokens(self, username: str, password: str) -> AuthTokens:
        """Get access token and refresh token."""
        client = BasicElicaIntegrationApiClient(
            session=async_create_clientsession(self.hass)
        )
        return await client.get_auth_tokens(username, password)

    async def _get_user_id(self, auth_tokens: AuthTokens) -> str:
        """Get user ID for the authenticated user."""
        client = ElicaIntegrationApiClient(
            async_create_clientsession(self.hass),
            auth_tokens,
        )
        return await client.get_user_id()
