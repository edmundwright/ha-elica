"""Fan platform for elica."""

from __future__ import annotations

from hmac import new
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

from custom_components.elica.data import MAX_FAN_SPEED, MIN_FAN_SPEED


from .entity import ElicaIntegrationEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from custom_components.elica.coordinator import DeviceInfo

    from .coordinator import ElicaIntegrationDataUpdateCoordinator
    from .data import ElicaIntegrationConfigEntry

_SPEED_RANGE = (MIN_FAN_SPEED, MAX_FAN_SPEED)


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
        return device_info.fan_speed > 0

    @property
    def percentage(self) -> int | None:
        """Return the current speed percentage."""
        device_info = self.coordinator.data.get(self._device_id, None)
        if not device_info:
            msg = f"Device info for device ID {self._device_id} not found."
            raise ValueError(msg)
        return _get_percentage(device_info.fan_speed)

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
        new_speed = self._get_new_speed(percentage)
        await self.coordinator.config_entry.runtime_data.client.set_fan_speed(
            device_id=self._device_id,
            device_type=self._device_type,
            speed=new_speed,
        )
        self.coordinator.data[self._device_id].fan_speed = new_speed
        self.coordinator.async_update_listeners()

    def _get_new_speed(self, requested_percentage: int | None) -> int:
        if requested_percentage is not None:
            return _get_speed(requested_percentage)
        if self.percentage is not None and self.percentage > 0:
            return _get_speed(self.percentage)
        return MIN_FAN_SPEED

    async def async_turn_off(self, **_: Any) -> None:
        """Turn off the fan."""
        await self.coordinator.config_entry.runtime_data.client.set_fan_speed(
            device_id=self._device_id,
            device_type=self._device_type,
            speed=0,
        )
        self.coordinator.data[self._device_id].fan_speed = 0
        self.coordinator.async_update_listeners()

    async def async_set_percentage(self, percentage: int) -> None:
        """Set the speed percentage of the fan."""
        new_speed = _get_speed(percentage)
        await self.coordinator.config_entry.runtime_data.client.set_fan_speed(
            device_id=self._device_id,
            device_type=self._device_type,
            speed=new_speed,
        )
        self.coordinator.data[self._device_id].fan_speed = new_speed
        self.coordinator.async_update_listeners()


def _get_speed(percentage: int) -> int:
    return math.ceil(percentage_to_ranged_value(_SPEED_RANGE, percentage))


def _get_percentage(speed: int) -> int:
    return ranged_value_to_percentage(_SPEED_RANGE, speed)
