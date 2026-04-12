"""DataUpdateCoordinator for elica."""

from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple

from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    ElicaIntegrationApiClientAuthenticationError,
    ElicaIntegrationApiClientError,
)

if TYPE_CHECKING:
    from .data import ElicaIntegrationConfigEntry


class DeviceInfo(NamedTuple):
    """Device info."""

    id: str
    name: str
    type: str
    light_level: int
    unboosted_fan_level: int


# https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
class ElicaIntegrationDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    config_entry: ElicaIntegrationConfigEntry

    async def _async_update_data(self) -> dict[str, DeviceInfo]:
        """Update data via library."""
        try:
            response = await self.config_entry.runtime_data.client.get_info_on_devices()
            return {
                d["id"]: DeviceInfo(
                    id=d["id"],
                    name=d["name"],
                    type=d["type"],
                    light_level=d.get("dataModel", {}).get("96", 0),
                    unboosted_fan_level=d.get("dataModel", {}).get("110", 0),
                )
                for d in response
            }
        except ElicaIntegrationApiClientAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except ElicaIntegrationApiClientError as exception:
            raise UpdateFailed(exception) from exception
