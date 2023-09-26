"""The Polygon Zone module."""
from homeassistant.components.zone import Zone
from shapely.geometry import Point, Polygon
from homeassistant.const import (
    ATTR_EDITABLE,
    ATTR_ENTITY_ID,
    ATTR_LATITUDE,
    ATTR_LONGITUDE,
    ATTR_PERSONS,
    CONF_ICON,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_NAME,
    CONF_RADIUS,
    STATE_UNKNOWN,
)

from .const import ATTR_PASSIVE, ATTR_RADIUS, CONF_PASSIVE, HOME_ZONE
from homeassistant.core import HomeAssistant, callback


class PolygonZone(Zone):
    """Custom implementation of a polygon zone."""

    def __init__(self, config):
        """Initialize the Polygon Zone."""

        polygon = Polygon(config['points'])
        center = polygon.centroid

        super().__init__({
            CONF_NAME: config[CONF_NAME],
            CONF_LATITUDE: center.x,
            CONF_LONGITUDE: center.y,
            CONF_RADIUS: 0,
            CONF_ICON: config[CONF_ICON],
            CONF_PASSIVE: config[CONF_PASSIVE],
        })
        self._points = config['points']
        self._center = center

    @classmethod
    async def async_create(cls, hass, config):
        """Create a Polygon Zone."""
        points = config.get("points", [])
        polygon = Polygon(points)
        return cls(points=polygon.exterior.coords, **config)

    async def async_update_config(self, config) -> None:
        polygon = Polygon(config['points'])
        center = polygon.centroid

        self._config = {
          **self._config,
            CONF_LATITUDE: center.x,
            CONF_LONGITUDE: center.y,
        }
        self._points = config['points']
        self._center = center
        self._generate_attrs()
        self.async_write_ha_state()

    @callback
    def _generate_attrs(self) -> None:
        """Generate new attrs based on config."""
        super()._generate_attrs()
        parent_attributes = self._attr_extra_state_attributes
        self._attr_extra_state_attributes = parent_attributes.update({
            'points': self._points,
        })


    @property
    def extra_state_attributes(self):
        parent_attributes = self._attr_extra_state_attributes
        dev_specific = {
            ATTR_LATITUDE: self._config[CONF_LATITUDE],
            ATTR_LONGITUDE: self._config[CONF_LONGITUDE],
            ATTR_RADIUS: self._config[CONF_RADIUS],
            ATTR_PASSIVE: self._config[CONF_PASSIVE],
            ATTR_PERSONS: sorted(self._persons_in_zone),
            ATTR_EDITABLE: self.editable,
            'points': self._points,
        }

        return dev_specific