"""ElicaIntegrationEntity class."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DOMAIN
from .coordinator import ElicaIntegrationDataUpdateCoordinator


class ElicaIntegrationEntity(CoordinatorEntity[ElicaIntegrationDataUpdateCoordinator]):
    """ElicaIntegrationEntity class."""

    _attr_attribution = ATTRIBUTION

    def __init__(
        self,
        coordinator: ElicaIntegrationDataUpdateCoordinator,
        device_id: str,
        device_name: str | None = None,
        device_model: str | None = None,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{device_id}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name=device_name,
            model=device_model,
        )
