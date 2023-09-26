"""The Polygon Zone Trigger module."""
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.event import async_track_state_change

import voluptuous as vol


DOMAIN = "polygon_zone_trigger"

CONF_ZONE = "zone"
CONF_TRACKERS = "trackers"

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_ZONE): cv.entity_id,
                vol.Required(CONF_TRACKERS): vol.All(cv.ensure_list, [cv.entity_id]),
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup_trigger(hass: HomeAssistant, config: dict):
    """Set up the Polygon Zone Trigger."""

    async def zone_tracker_entered_zone(entity_id, old_state, new_state):
        """Activate trigger when person or device enters the zone."""

        zone_entity_id = config[DOMAIN][CONF_ZONE]
        zone_state = hass.states.get(zone_entity_id)

        # If the new state is None, the entity no longer exists, so we can't continue
        if new_state is None:
            return

        # If the entity is in the zone, activate the trigger
        if zone_state is not None and zone_state.attributes["polygon"].contains(
            new_state.attributes["latitude"], new_state.attributes["longitude"]
        ):
            hass.bus.async_fire(
                "polygon_zone_trigger",
                {"entity_id": entity_id, "zone_entity_id": zone_entity_id},
            )

    # Start tracking state changes for all trackers in the configuration
    for tracker_entity_id in config[DOMAIN][CONF_TRACKERS]:
        async_track_state_change(
            hass, tracker_entity_id, zone_tracker_entered_zone
        )

    return True