"""Adds config flow for Elica integration."""

from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_ACCESS_TOKEN, CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.loader import async_get_loaded_integration
from slugify import slugify

from .api import (
    ElicaIntegrationApiClient,
    ElicaIntegrationApiClientAuthenticationError,
    ElicaIntegrationApiClientCommunicationError,
    ElicaIntegrationApiClientError,
)
from .const import DOMAIN, LOGGER


class ElicaIntegrationFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Elica integration."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle a flow initialized by the user."""
        _errors = {}
        if user_input is not None:
            try:
                await self._test_credentials(
                    # username=user_input[CONF_USERNAME],
                    # password=user_input[CONF_PASSWORD],
                    access_token=user_input[CONF_ACCESS_TOKEN],
                )
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
                    ## Do NOT use this in production code
                    ## The unique_id should never be something that can change
                    ## https://developers.home-assistant.io/docs/config_entries_config_flow_handler#unique-ids
                    unique_id="unique_id_for_this_integration",
                )
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title="title - what is this for? here's the access token: "
                    + user_input[CONF_ACCESS_TOKEN],
                    data=user_input,
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
                        CONF_ACCESS_TOKEN,
                        default=(user_input or {}).get(
                            CONF_ACCESS_TOKEN, vol.UNDEFINED
                        ),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT,
                        ),
                    ),
                    # vol.Required(
                    #     CONF_USERNAME,
                    #     default=(user_input or {}).get(CONF_USERNAME, vol.UNDEFINED),
                    # ): selector.TextSelector(
                    #     selector.TextSelectorConfig(
                    #         type=selector.TextSelectorType.TEXT,
                    #     ),
                    # ),
                    # vol.Required(CONF_PASSWORD): selector.TextSelector(
                    #     selector.TextSelectorConfig(
                    #         type=selector.TextSelectorType.PASSWORD,
                    #     ),
                    # ),
                },
            ),
            errors=_errors,
        )

    async def _test_credentials(self, access_token: str) -> None:
        """Validate credentials."""
        client = ElicaIntegrationApiClient(
            # username=username,
            # password=password,
            access_token=access_token,
            session=async_create_clientsession(self.hass),
        )
        await client.get_info_on_me()
