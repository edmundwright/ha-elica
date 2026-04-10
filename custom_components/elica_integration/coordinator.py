"""DataUpdateCoordinator for elica_integration."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    ElicaIntegrationApiClientAuthenticationError,
    ElicaIntegrationApiClientError,
)

if TYPE_CHECKING:
    from .data import ElicaIntegrationConfigEntry


# https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
class ElicaIntegrationDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    config_entry: ElicaIntegrationConfigEntry

    async def _async_update_data(self) -> Any:
        """Update data via library."""
        try:
            # TODO(edmund): replace this with something else
            return await self.config_entry.runtime_data.client.get_info_on_device()
        except ElicaIntegrationApiClientAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except ElicaIntegrationApiClientError as exception:
            raise UpdateFailed(exception) from exception
