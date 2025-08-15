"""Sensor listener for the SOLID integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_state_change_event

from .const import DOMAIN

LOGGER = logging.getLogger(__name__)


async def async_start_sensor_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Start listening to the selected sensor and send updates to the Pod."""
    data = entry.data
    cache = hass.data[DOMAIN][entry.entry_id]["cache"]

    async def handle_sensor_change(event):
        """Handle sensor state change."""
        # entity_id = event.data["entity_id"]
        new_state = event.data.get("new_state")

        if not new_state or new_state.state in ("unknown", "unavailable"):
            return

        LOGGER.debug(
            "[%s] Event: %s Data: %s",
            DOMAIN,
            event.data,
            entry.data,
        )

        await cache.async_append(
            {
                "timestamp": new_state.last_changed.isoformat(),
                "state": new_state.state,
                "attributes": new_state.attributes,
            },
        )

    # Subscribe to state changes for selected sensor
    async_track_state_change_event(hass, data["SENSOR"], handle_sensor_change)

    LOGGER.debug("[%s] Listening to sensor: %s", DOMAIN, data["SENSOR"])
