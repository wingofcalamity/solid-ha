"""Cache Logic for the SOLID Integration."""

from datetime import datetime
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import DOMAIN

LOGGER = logging.getLogger(__name__)


class SolidCache:
    """Returns a Cache adapter."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the cache."""
        LOGGER.info(
            "[%s] Initializing cache <%s>",
            DOMAIN,
            entry.entry_id,
        )
        self.hass = hass
        self.key = f"{DOMAIN}_{entry.entry_id}"
        self.store = Store(hass, 1, self.key)
        self.oidc_client = hass.data[DOMAIN][entry.entry_id]["oidc_client"]

    async def async_get(self) -> list[Any]:
        """Get the cache data."""
        LOGGER.debug("[%s] Getting cache data for %s", DOMAIN, self.key)
        data = await self.store.async_load()
        if not isinstance(data, list):
            data = []
        return data

    async def async_set(self, data: list[Any]) -> None:
        """Set the cache data."""
        LOGGER.debug("[%s] Setting cache data for %s", DOMAIN, self.key)
        await self.store.async_save(data)

    async def async_append(self, item: Any) -> None:
        """Append an item to the cache."""
        data = await self.async_get()
        data.append(item)
        LOGGER.debug("[%s] Appended item to cache %s: %s", DOMAIN, self.key, item)
        await self.async_set(data)

    async def async_clear(self) -> None:
        """Clear the cache."""
        LOGGER.info("[%s] Clearing cache for %s", DOMAIN, self.key)
        await self.async_set([])

    async def async_push(self) -> None:
        """Push the cache data to the SOLID server via OIDC client."""
        data = await self.async_get()
        if not data:
            LOGGER.info("[%s] No cached data to push", DOMAIN)
            return

        # TODO: resource path should be configurable
        await self.oidc_client.put(
            f"{self.key}/{datetime.now().strftime('%Y-%m-%d')}",
            data,
        )

        await self.async_clear()
        LOGGER.info("[%s] Pushed cache data to SOLID server: %s", DOMAIN, self.key)
