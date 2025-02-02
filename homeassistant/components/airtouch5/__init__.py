"""The Airtouch 5 integration."""

from __future__ import annotations

from airtouch5py.airtouch5_simple_client import Airtouch5SimpleClient

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DOMAIN

PLATFORMS: list[Platform] = [Platform.CLIMATE]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Airtouch 5 from a config entry."""

    hass.data.setdefault(DOMAIN, {})

    # Create API instance
    host = entry.data[CONF_HOST]
    client = Airtouch5SimpleClient(host)

    # Connect to the API
    try:
        await client.connect_and_stay_connected()
    except TimeoutError as t:
        raise ConfigEntryNotReady() from t

    # Store an API object for your platforms to access
    hass.data[DOMAIN][entry.entry_id] = client

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        client: Airtouch5SimpleClient = hass.data[DOMAIN][entry.entry_id]
        await client.disconnect()
        client.ac_status_callbacks.clear()
        client.connection_state_callbacks.clear()
        client.data_packet_callbacks.clear()
        client.zone_status_callbacks.clear()
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
