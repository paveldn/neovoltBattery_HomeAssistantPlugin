"""Binary sensor platform for Byte-Watt integration."""
from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import BINARY_SENSOR_OFF_GRID_MODE, DOMAIN
from .sensor import LIVE_CONNECTION_STATUSES

OFF_GRID_ATTRIBUTES = (
    "upsModel",
    "pgrid",
    "pload",
    "pbat",
    "ppv",
    "soc",
    "forceChargeMode",
    "dataType",
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Byte-Watt binary sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    async_add_entities([
        ByteWattOffGridModeBinarySensor(coordinator, entry),
    ])


class ByteWattOffGridModeBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor for Byte-Watt off-grid/UPS mode."""

    _attr_name = "ByteWatt Off Grid Mode"
    _attr_icon = "mdi:power-plug-off"

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._attr_unique_id = f"{config_entry.entry_id}_{BINARY_SENSOR_OFF_GRID_MODE}"

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device info."""
        username = "Unknown"
        if self._config_entry.data:
            username = self._config_entry.data.get("username", "Unknown")

        return {
            "identifiers": {(DOMAIN, self._config_entry.entry_id)},
            "name": f"Byte-Watt Battery ({username})",
            "manufacturer": "Byte-Watt",
            "model": "Battery Monitor",
        }

    @property
    def available(self) -> bool:
        """Return if the latest state came from a live API connection."""
        if not self.coordinator.data:
            return False
        if self.coordinator.data.get("connection_status") not in LIVE_CONNECTION_STATUSES:
            return False
        return "upsModel" in self.coordinator.data.get("battery", {})

    @property
    def is_on(self) -> bool | None:
        """Return true when the battery reports off-grid/UPS mode."""
        if not self.available:
            return None

        ups_model = self.coordinator.data["battery"].get("upsModel")
        try:
            return int(ups_model) == 1
        except (TypeError, ValueError):
            return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return live power attributes useful for outage automations."""
        if not self.available:
            return {}

        battery_data = self.coordinator.data["battery"]
        return {
            key: battery_data[key]
            for key in OFF_GRID_ATTRIBUTES
            if key in battery_data
        }
