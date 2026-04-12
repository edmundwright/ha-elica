"""Light platform for elica_integration."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Final

from homeassistant.components.light import (
    LightEntity,
    LightEntityDescription,
)
from homeassistant.components.light.const import ColorMode

from custom_components.elica_integration.coordinator import DeviceInfo

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
            device_info=device_info,
        )
        for device_info in coordinator.data.values()
        if device_info.type == "Hood"
    )


class ElicaIntegrationLight(ElicaIntegrationEntity, LightEntity):
    """elica_integration light class."""

    def __init__(
        self,
        coordinator: ElicaIntegrationDataUpdateCoordinator,
        device_info: DeviceInfo,
    ) -> None:
        """Initialize the light class."""
        super().__init__(
            coordinator,
            device_id=device_info.id,
            device_name=device_info.name,
            device_model=device_info.type,
        )
        self._attr_name = f"{device_info.name} light"
        self.entity_description = LightEntityDescription(
            key=f"elica_{device_info.id}_light",
            name=self._attr_name,
            icon="mdi:led-strip",
        )
        self._attr_supported_color_modes = {ColorMode.ONOFF}
        self._attr_color_mode = ColorMode.ONOFF
        self._device_id = device_info.id
        self._device_type = device_info.type

    @property
    def is_on(self) -> bool:
        """Return true if the light is on."""
        device_info = self.coordinator.data.get(self._device_id, None)
        if not device_info:
            msg = f"Device info for device ID {self._device_id} not found."
            raise ValueError(msg)
        return device_info.light_level > 0

    async def async_turn_on(self, **_: Any) -> None:
        """Turn on the light."""
        await self.coordinator.config_entry.runtime_data.client.turn_on_light(
            self._device_id,
            self._device_type,
        )
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **_: Any) -> None:
        """Turn off the light."""
        await self.coordinator.config_entry.runtime_data.client.turn_off_light(
            self._device_id,
            self._device_type,
        )
        await self.coordinator.async_request_refresh()
