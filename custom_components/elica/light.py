"""Light platform for elica."""

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

    from custom_components.elica.coordinator import DeviceInfo

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
            device_type=device_info.type,
            device_name=device_info.name,
            light_name=f"{device_info.name} light",
        )
        for device_info in coordinator.data.values()
        if device_info.type == "Hood"
    )


class ElicaIntegrationLight(ElicaIntegrationEntity, LightEntity):
    """elica light class."""

    def __init__(
        self,
        coordinator: ElicaIntegrationDataUpdateCoordinator,
        device_id: str,
        device_type: str,
        device_name: str,
        light_name: str,
    ) -> None:
        """Initialize the light class."""
        super().__init__(
            coordinator,
            device_id=device_id,
            device_name=device_name,
            device_model=device_type,
        )
        self._attr_name = light_name
        self.entity_description = LightEntityDescription(
            key=f"elica_{device_id}_light",
            name=light_name,
            icon="mdi:led-strip",
        )
        self._attr_supported_color_modes = {ColorMode.ONOFF}
        self._attr_color_mode = ColorMode.ONOFF
        self._device_id = device_id
        self._device_type = device_type

    @property
    def is_on(self) -> bool:
        """Return true if the light is on."""
        print("light#is_on()")
        device_info = self.coordinator.data.get(self._device_id, None)
        if not device_info:
            msg = f"Device info for device ID {self._device_id} not found."
            raise ValueError(msg)
        return device_info.is_light_on

    async def async_turn_on(self, **_: Any) -> None:
        """Turn on the light."""
        print("light#async_turn_on()")
        await self.coordinator.config_entry.runtime_data.client.turn_on_light(
            self._device_id,
            self._device_type,
        )
        print("light#async_turn_on() got response, updating data")
        self.coordinator.data[self._device_id].is_light_on = True
        self.coordinator.async_update_listeners()

    async def async_turn_off(self, **_: Any) -> None:
        """Turn off the light."""
        print("light#async_turn_off()")
        await self.coordinator.config_entry.runtime_data.client.turn_off_light(
            self._device_id,
            self._device_type,
        )
        print("light#async_turn_off() got response, updating data")
        self.coordinator.data[self._device_id].is_light_on = False
        self.coordinator.async_update_listeners()
