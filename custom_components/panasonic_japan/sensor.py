"""Sensor platform for Panasonic Japan."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTR_APPLIANCE_ID, ATTR_PRODUCT_CODE, DOMAIN
from .coordinator import PanasonicDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Panasonic Japan sensors from a config entry."""
    coordinator: PanasonicDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    sensors = [
        PanasonicCostReductionSensor(coordinator),
        PanasonicOperationModeSensor(coordinator),
        PanasonicFirmwareSensor(coordinator),
    ]

    async_add_entities(sensors)


class PanasonicSensor(CoordinatorEntity[PanasonicDataUpdateCoordinator], SensorEntity):
    """Base class for Panasonic sensors."""

    def __init__(self, coordinator: PanasonicDataUpdateCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.appliance_id)},
            name=f"Panasonic Fridge ({coordinator.product_code})",
            manufacturer="Panasonic",
            model=coordinator.product_code,
        )

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        """Return extra state attributes."""
        data = self.coordinator.data
        return {
            ATTR_APPLIANCE_ID: data.get("appliance_id", ""),
            ATTR_PRODUCT_CODE: data.get("product_code", ""),
        }


class PanasonicCostReductionSensor(PanasonicSensor):
    """Sensor for electricity cost reduction."""

    _attr_name = "Electricity Cost Reduction"
    _attr_unique_id = "cost_reduction"
    _attr_native_unit_of_measurement = "yen"
    _attr_icon = "mdi:currency-jpy"
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> int:
        """Return the cost reduction in yen."""
        electricity_data = self.coordinator.data.get("electricity", {})
        return electricity_data.get("current_reduction_amount", 0)

    @property
    def extra_state_attributes(self) -> dict:
        """Return extra state attributes."""
        attrs = super().extra_state_attributes
        electricity_data = self.coordinator.data.get("electricity", {})
        attrs.update(
            {
                "last_month_reduction": electricity_data.get(
                    "lastmonth_reduction_amount", 0
                ),
                "last_year_reduction": electricity_data.get(
                    "lastyear_reduction_amount", 0
                ),
            }
        )
        return attrs


class PanasonicOperationModeSensor(PanasonicSensor):
    """Sensor for operation mode."""

    _attr_name = "Operation Mode"
    _attr_unique_id = "operation_mode"
    _attr_icon = "mdi:air-conditioner"

    @property
    def native_value(self) -> str:
        """Return the operation mode."""
        device_status = self.coordinator.data.get("device_status", {})
        return device_status.get("operation_mode", "unknown")

    @property
    def extra_state_attributes(self) -> dict:
        """Return extra state attributes."""
        attrs = super().extra_state_attributes
        device_status = self.coordinator.data.get("device_status", {})
        attrs.update(
            {
                "winter_setting": device_status.get("winter_setting_status", False),
                "house_sitting": device_status.get("house_sitting_status", False),
                "pre_cooling": device_status.get("pre_cooling_status", False),
                "outage_prepare": device_status.get("outage_prepare_status", False),
            }
        )
        return attrs


class PanasonicFirmwareSensor(PanasonicSensor):
    """Sensor for firmware version."""

    _attr_name = "Firmware Version"
    _attr_unique_id = "firmware_version"
    _attr_icon = "mdi:chip"

    @property
    def native_value(self) -> str:
        """Return the firmware version."""
        device_status = self.coordinator.data.get("device_status", {})
        return device_status.get("firmware_current_version", "unknown")

    @property
    def extra_state_attributes(self) -> dict:
        """Return extra state attributes."""
        attrs = super().extra_state_attributes
        device_status = self.coordinator.data.get("device_status", {})
        attrs.update(
            {
                "latest_version": device_status.get("firmware_latest_version", ""),
                "update_status": device_status.get("firmware_update_status", ""),
            }
        )
        return attrs
