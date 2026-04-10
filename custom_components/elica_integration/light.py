"""Light platform for elica_integration."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.light import (
    ColorMode,
    LightEntity,
    LightEntityDescription,
)

from .entity import ElicaIntegrationEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import ElicaIntegrationDataUpdateCoordinator
    from .data import ElicaIntegrationConfigEntry

ENTITY_DESCRIPTIONS = (
    LightEntityDescription(
        key="elica_integration",
        name="Elica Integration Light",
        icon="mdi:led-strip",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    entry: ElicaIntegrationConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the light platform."""
    async_add_entities(
        ElicaIntegrationLight(
            coordinator=entry.runtime_data.coordinator,
            entity_description=entity_description,
        )
        for entity_description in ENTITY_DESCRIPTIONS
    )


class ElicaIntegrationLight(ElicaIntegrationEntity, LightEntity):
    """elica_integration light class."""

    def __init__(
        self,
        coordinator: ElicaIntegrationDataUpdateCoordinator,
        entity_description: LightEntityDescription,
    ) -> None:
        """Initialize the light class."""
        super().__init__(coordinator)
        self.entity_description = entity_description
        self._attr_supported_color_modes = {ColorMode.ONOFF}
        self._attr_color_mode = ColorMode.ONOFF

    @property
    def is_on(self) -> bool:
        """Return true if the light is on."""
        return self.coordinator.data.get("dataModel", {}).get("96", 0) > 0

    async def async_turn_on(self, **_: Any) -> None:
        """Turn on the light."""
        await self.coordinator.config_entry.runtime_data.client.turn_on_light()
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **_: Any) -> None:
        """Turn off the light."""
        await self.coordinator.config_entry.runtime_data.client.turn_off_light()
        await self.coordinator.async_request_refresh()
