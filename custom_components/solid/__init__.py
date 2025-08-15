"""SOLID integration for Home Assistant."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import (
    async_track_time_change,
    # async_track_time_interval, <- for hourly updates
)

from .cache import SolidCache
from .const import DOMAIN
from .listener import async_start_sensor_listener
from .oidc_client import SolidOIDCClient

PLATFORMS = []
LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up SOLID login from a config entry."""

    # Set up the domain data structure
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = dict(entry.data)
    hass.data[DOMAIN][entry.entry_id]["oidc_client"] = SolidOIDCClient(
        hass,
        entry.data["OIDC"],
        entry.data["POD"],
        entry.data["CLIENT_TOKEN"],
        entry.data["CLIENT_SECRET"],
    )
    hass.data[DOMAIN][entry.entry_id]["cache"] = SolidCache(hass, entry)

    async def push_data(_now):
        """Push cached data to the SOLID server."""
        LOGGER.info("[%s] Pushing cached data", DOMAIN)
        cache = hass.data[DOMAIN][entry.entry_id]["cache"]
        await cache.async_push()

    await async_start_sensor_listener(hass, entry)

    # This uses local time
    async_track_time_change(hass, push_data, hour=0, minute=0, second=0)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload config entry."""

    hass.data[DOMAIN].pop(entry.entry_id, None)
    return True
