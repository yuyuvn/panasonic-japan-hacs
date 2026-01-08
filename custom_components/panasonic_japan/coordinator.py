"""Data update coordinator for Panasonic Japan."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import PanasonicAPI, PanasonicAPIError
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class PanasonicDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the Panasonic API."""

    def __init__(self, hass: HomeAssistant, config_entry) -> None:
        """Initialize."""
        self.api = PanasonicAPI(
            access_token=config_entry.data["access_token"],
            refresh_token=config_entry.data.get("refresh_token"),
        )
        self.appliance_id = config_entry.data["appliance_id"]
        self.product_code = config_entry.data.get("product_code", "Unknown")
        self.config_entry = config_entry
        self.hass = hass

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )

    async def _async_update_data(self) -> dict:
        """Fetch data from Panasonic API."""
        try:
            # Fetch device status and electricity data
            device_status = await self.hass.async_add_executor_job(
                self.api.get_device_status, self.appliance_id
            )
            electricity_data = await self.hass.async_add_executor_job(
                self.api.get_electricity_reduction, self.appliance_id
            )

            # Calculate electricity usage
            current_reduction = electricity_data.get("current_reduction_amount", 0)
            electricity_usage = self.api.calculate_electricity_usage(current_reduction)

            return {
                "device_status": device_status,
                "electricity": electricity_data,
                "electricity_usage_kwh": electricity_usage,
                "appliance_id": self.appliance_id,
                "product_code": self.product_code,
            }

        except PanasonicAPIError as err:
            # Try to refresh token if we have a refresh token
            if "401" in str(err) or "403" in str(err):
                try:
                    token_data = await self.hass.async_add_executor_job(
                        self.api.refresh_access_token
                    )
                    if token_data:
                        # Update config entry with new tokens
                        new_data = dict(self.config_entry.data)
                        new_data["access_token"] = self.api.access_token
                        if self.api.refresh_token:
                            new_data["refresh_token"] = self.api.refresh_token
                        self.hass.config_entries.async_update_entry(
                            self.config_entry, data=new_data
                        )

                        # Retry the request
                        device_status = await self.hass.async_add_executor_job(
                            self.api.get_device_status, self.appliance_id
                        )
                        electricity_data = await self.hass.async_add_executor_job(
                            self.api.get_electricity_reduction, self.appliance_id
                        )

                        current_reduction = electricity_data.get(
                            "current_reduction_amount", 0
                        )
                        electricity_usage = self.api.calculate_electricity_usage(
                            current_reduction
                        )

                        return {
                            "device_status": device_status,
                            "electricity": electricity_data,
                            "electricity_usage_kwh": electricity_usage,
                            "appliance_id": self.appliance_id,
                            "product_code": self.product_code,
                        }
                except Exception as refresh_err:
                    _LOGGER.warning(
                        "Token refresh failed, using original error: %s", refresh_err
                    )

            raise UpdateFailed(f"Error communicating with API: {err}") from err
        except Exception as err:
            raise UpdateFailed(f"Unexpected error: {err}") from err
