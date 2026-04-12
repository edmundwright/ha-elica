"""Light platform for elica_integration."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.light import (
    LightEntity,
    LightEntityDescription,
)
from homeassistant.components.light.const import ColorMode

from .entity import ElicaIntegrationEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import ElicaIntegrationDataUpdateCoordinator
    from .data import ElicaIntegrationConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    entry: ElicaIntegrationConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the light platform."""
    coordinator = entry.runtime_data.coordinator
    async_add_entities(
        ElicaIntegrationLight(
            coordinator=coordinator,
            device_id=device_info.id,
            device_name=device_info.name,
            device_model=device_info.type,
        )
        for device_info in coordinator.data.values()
        if device_info.type == "Hood"
    )


class ElicaIntegrationLight(ElicaIntegrationEntity, LightEntity):
    """elica_integration light class."""

    def __init__(
        self,
        coordinator: ElicaIntegrationDataUpdateCoordinator,
        device_id: str,
        device_name: str,
        device_model: str,
    ) -> None:
        """Initialize the light class."""
        super().__init__(
            coordinator,
            device_id=device_id,
            device_name=device_name,
            device_model=device_model,
        )
        self._attr_name = f"{device_name} light"
        self.entity_description = LightEntityDescription(
            key=f"elica_integration_{device_id}_light",
            name=self._attr_name,
            icon="mdi:led-strip",
        )
        self._attr_supported_color_modes = {ColorMode.ONOFF}
        self._attr_color_mode = ColorMode.ONOFF
        self.device_id = device_id

    @property
    def is_on(self) -> bool:
        """Return true if the light is on."""
        device_info = self.coordinator.data.get(self.device_id)
        if not device_info:
            msg = f"Device info for device ID {self.device_id} not found."
            raise ValueError(msg)
        return device_info.light_level > 0

    async def async_turn_on(self, **_: Any) -> None:
        """Turn on the light."""
        await self.coordinator.config_entry.runtime_data.client.turn_on_light(
            self.device_id
        )
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **_: Any) -> None:
        """Turn off the light."""
        await self.coordinator.config_entry.runtime_data.client.turn_off_light(
            self.device_id
        )
        await self.coordinator.async_request_refresh()
