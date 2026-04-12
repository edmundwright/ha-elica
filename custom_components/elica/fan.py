"""Fan platform for elica."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any

from homeassistant.components.fan import (
    FanEntity,
    FanEntityDescription,
    FanEntityFeature,
)

from homeassistant.util.percentage import (
    ranged_value_to_percentage,
    percentage_to_ranged_value,
)
from homeassistant.util.scaling import int_states_in_range


from .entity import ElicaIntegrationEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from custom_components.elica.coordinator import DeviceInfo

    from .coordinator import ElicaIntegrationDataUpdateCoordinator
    from .data import ElicaIntegrationConfigEntry

# TODO: Support boost speed too.
_SPEED_RANGE = (1, 3)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    entry: ElicaIntegrationConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the fan platform."""
    coordinator = entry.runtime_data.coordinator
    async_add_entities(
        ElicaIntegrationFan(
            coordinator=coordinator,
            device_id=device_info.id,
            device_type=device_info.type,
            device_name=device_info.name,
            fan_name=device_info.name,
        )
        for device_info in coordinator.data.values()
        if device_info.type == "Hood"
    )


class ElicaIntegrationFan(ElicaIntegrationEntity, FanEntity):
    """elica fan class."""

    def __init__(
        self,
        coordinator: ElicaIntegrationDataUpdateCoordinator,
        device_id: str,
        device_type: str,
        device_name: str,
        fan_name: str,
    ) -> None:
        """Initialize the fan class."""
        super().__init__(
            coordinator,
            device_id=device_id,
            device_name=device_name,
            device_model=device_type,
        )
        self._attr_name = fan_name
        self.entity_description = FanEntityDescription(
            key=f"elica_{device_id}_fan",
            name=fan_name,
            icon="mdi:fan",
        )
        self._device_id = device_id
        self._device_type = device_type
        self._attr_supported_features = (
            FanEntityFeature.SET_SPEED
            | FanEntityFeature.TURN_ON
            | FanEntityFeature.TURN_OFF
        )

    @property
    def is_on(self) -> bool:
        """Return true if the fan is on."""
        device_info = self.coordinator.data.get(self._device_id, None)
        if not device_info:
            msg = f"Device info for device ID {self._device_id} not found."
            raise ValueError(msg)
        return device_info.unboosted_fan_level > 0

    @property
    def percentage(self) -> int | None:
        """Return the current speed percentage."""
        device_info = self.coordinator.data.get(self._device_id, None)
        if not device_info:
            msg = f"Device info for device ID {self._device_id} not found."
            raise ValueError(msg)
        return ranged_value_to_percentage(_SPEED_RANGE, device_info.unboosted_fan_level)

    @property
    def speed_count(self) -> int:
        """Return the number of speeds the fan supports."""
        return int_states_in_range(_SPEED_RANGE)

    async def async_turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Turn on the fan."""
        await self.coordinator.config_entry.runtime_data.client.set_fan_level(
            device_id=self._device_id,
            device_type=self._device_type,
            level=math.ceil(percentage_to_ranged_value(_SPEED_RANGE, percentage))
            if percentage is not None
            else _SPEED_RANGE[0],
        )
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **_: Any) -> None:
        """Turn off the fan."""
        await self.coordinator.config_entry.runtime_data.client.set_fan_level(
            device_id=self._device_id,
            device_type=self._device_type,
            level=0,
        )
        await self.coordinator.async_request_refresh()

    async def async_set_percentage(self, percentage: int) -> None:
        """Set the speed percentage of the fan."""
        await self.coordinator.config_entry.runtime_data.client.set_fan_level(
            device_id=self._device_id,
            device_type=self._device_type,
            level=math.ceil(percentage_to_ranged_value(_SPEED_RANGE, percentage)),
        )
        await self.coordinator.async_request_refresh()
