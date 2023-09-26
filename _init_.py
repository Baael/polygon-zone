import logging

from homeassistant.helpers import (
    collection,
    config_validation as cv,
    entity_component,
    storage
)
from homeassistant.core import HomeAssistant, State, callback
from homeassistant.const import (
    ATTR_LATITUDE,
    ATTR_LONGITUDE,
    CONF_ICON,
    CONF_ID,
    CONF_NAME,
    STATE_HOME,
    STATE_NOT_HOME,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from homeassistant.loader import bind_hass
from typing import Any, cast
from shapely.geometry import Point, Polygon
from homeassistant.util.location import distance
import voluptuous as vol

from homeassistant.components import zone
from homeassistant import components
from .zone import PolygonZone
from .const import (
    ATTR_PASSIVE,
    ATTR_RADIUS,
    CONF_PASSIVE,
    HOME_ZONE,
    DEFAULT_PASSIVE,
    DEFAULT_RADIUS,
    ICON_HOME,
    ICON_IMPORT,
    DOMAIN,
    SUBDOMAIN,
    STORAGE_KEY,
    STORAGE_VERSION,
)

_LOGGER = logging.getLogger(__name__)

@bind_hass
def async_active_zone(
    hass: HomeAssistant, latitude: float, longitude: float, radius: int = 0
) -> State | None:

    point = Point(latitude, longitude)
    zones = (
        hass.states.get(entity_id)
        for entity_id in sorted(hass.states.async_entity_ids(DOMAIN))
    )

    min_dist = None
    closest = None

    for zone in zones:
        if 'points' in zone.attributes:
            if zone.state == STATE_UNAVAILABLE or zone.attributes.get(ATTR_PASSIVE):
                continue

        polygon = Polygon(zone.attributes['points'])
        if polygon.contains(point):
            return zone
        else:
            if zone.state == STATE_UNAVAILABLE or zone.attributes.get(ATTR_PASSIVE):
                continue

        zone_dist = distance(
            latitude,
            longitude,
            zone.attributes[ATTR_LATITUDE],
            zone.attributes[ATTR_LONGITUDE],
        )

        if zone_dist is None:
            continue

        within_zone = zone_dist - radius < zone.attributes[ATTR_RADIUS]
        closer_zone = closest is None or zone_dist < min_dist  # type: ignore[unreachable]
        smaller_zone = (
            zone_dist == min_dist
            and zone.attributes[ATTR_RADIUS]
            < cast(State, closest).attributes[ATTR_RADIUS]
        )

        if within_zone and (closer_zone or smaller_zone):
            min_dist = zone_dist
            closest = zone

    return closest

def in_zone(zone: State, latitude: float, longitude: float, radius: float = 0) -> bool:
    if zone.state == STATE_UNAVAILABLE:
        return False

    if 'points' in zone.attributes:
        polygon = Polygon(zone.attributes['points'])
        point = Point(latitude, longitude)
        return polygon.contains(point)


    zone_dist = distance(
        latitude,
        longitude,
        zone.attributes[ATTR_LATITUDE],
        zone.attributes[ATTR_LONGITUDE],
    )

    if zone_dist is None or zone.attributes[ATTR_RADIUS] is None:
        return False
    return zone_dist - radius < cast(float, zone.attributes[ATTR_RADIUS])


components.zone.async_active_zone = async_active_zone
components.zone.in_zone = in_zone


CREATE_FIELDS = {
    vol.Required(CONF_NAME): cv.string,
    vol.Required('points'): vol.All(cv.ensure_list, [vol.All(cv.ensure_list, [vol.Coerce(float)])]),
    vol.Optional(CONF_PASSIVE, default=DEFAULT_PASSIVE): cv.boolean,
    vol.Optional(CONF_ICON): cv.icon,
}


UPDATE_FIELDS = {
    vol.Optional(CONF_NAME): cv.string,
    vol.Optional('points'): vol.All(cv.ensure_list, [vol.All(cv.ensure_list, [vol.Coerce(float)])]),
    vol.Optional(CONF_PASSIVE, default=DEFAULT_PASSIVE): cv.boolean,
    vol.Optional(CONF_ICON): cv.icon,
}


class PolygonZoneStorageCollection(collection.StorageCollection):

    CREATE_SCHEMA = vol.Schema(CREATE_FIELDS)
    UPDATE_SCHEMA = vol.Schema(UPDATE_FIELDS)

    async def _process_create_data(self, data: dict) -> dict:
        return cast(dict, self.CREATE_SCHEMA(data))

    @callback
    def _get_suggested_id(self, info: dict) -> str:
        return cast(str, info[CONF_NAME])

    async def _update_data(self, data: dict, update_data: dict) -> dict:
        update_data = self.UPDATE_SCHEMA(update_data)
        return {**data, **update_data}

    async def async_create_item(self, data: dict) -> dict:
        item = await self._process_create_data(data)
        item[CONF_ID] = self.id_manager.generate_id(self._get_suggested_id(item))
        self.data[item[CONF_ID]] = item
        self._async_schedule_save()
        await self.notify_changes(
            [collection.CollectionChangeSet(collection.CHANGE_ADDED, item[CONF_ID], item)]
        )
        return item

async def async_setup(hass, config):
    component = entity_component.EntityComponent[PolygonZone](_LOGGER, DOMAIN, hass)
    id_manager = collection.IDManager()


    storage_collection = PolygonZoneStorageCollection(
        storage.Store(hass, STORAGE_VERSION, STORAGE_KEY),
        logging.getLogger(f"{__name__}.storage_collection"),
        id_manager,
    )
    collection.sync_entity_lifecycle(
        hass, SUBDOMAIN, DOMAIN, component, storage_collection, PolygonZone
    )

    await storage_collection.async_load()

    collection.StorageCollectionWebsocket(
        storage_collection, SUBDOMAIN, DOMAIN, CREATE_FIELDS, UPDATE_FIELDS
    ).async_setup(hass)

    return True
