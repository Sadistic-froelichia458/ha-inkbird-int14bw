"""The Inkbird INT-14-BW integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ADDRESS, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from homeassistant.components import bluetooth

from .const import DOMAIN
from .coordinator import InkbirdCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]

type InkbirdConfigEntry = ConfigEntry[InkbirdCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: InkbirdConfigEntry) -> bool:
    """Set up Inkbird INT-14-BW from a config entry."""
    address: str = entry.data[CONF_ADDRESS].upper()

    # Ensure a Bluetooth adapter/proxy capable of connecting is present.
    if not bluetooth.async_scanner_count(hass, connectable=True):
        raise ConfigEntryNotReady(
            "No connectable Bluetooth adapter or proxy is available"
        )

    coordinator = InkbirdCoordinator(hass, address)
    await coordinator.async_start()
    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: InkbirdConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        await entry.runtime_data.async_stop()
    return unload_ok
