"""Switch platform for Panasonic Japan."""
from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import PanasonicDataUpdateCoordinator

# Note: Control switches would require POST endpoints
# For now, we'll create read-only switches that show status
# Actual control implementation would need to be added based on available API endpoints


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Panasonic Japan switches from a config entry."""
    coordinator: PanasonicDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Add switches for controllable features if available
    # For now, we'll skip switches as the API endpoints for control
    # would need to be implemented based on available POST endpoints
    async_add_entities([])
