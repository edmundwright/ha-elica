"""Custom types for elica."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.loader import Integration

    from .api import ElicaIntegrationApiClient
    from .coordinator import ElicaIntegrationDataUpdateCoordinator


type ElicaIntegrationConfigEntry = ConfigEntry[ElicaIntegrationData]


@dataclass
class ElicaIntegrationData:
    """Data for the Elica integration."""

    client: ElicaIntegrationApiClient
    coordinator: ElicaIntegrationDataUpdateCoordinator
    integration: Integration


@dataclass
class DeviceInfo:
    """Device info."""

    id: str
    name: str
    type: str
    is_light_on: bool
    fan_speed: int


MAX_FAN_SPEED = 4
MIN_FAN_SPEED = 1
