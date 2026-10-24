"""The device and base entity every Foreca entity shares."""

from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, CONFIGURATION_URL, DOMAIN, MANUFACTURER
from .coordinator import ForecaConfigEntry, ForecaCoordinator


def foreca_device_info(entry: ForecaConfigEntry) -> DeviceInfo:
    """Describe the one service device a config entry's entities belong to."""
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=entry.title,
        manufacturer=MANUFACTURER,
        entry_type=DeviceEntryType.SERVICE,
        configuration_url=CONFIGURATION_URL,
    )


class ForecaEntity(CoordinatorEntity[ForecaCoordinator]):
    """An entity fed by the entry's coordinator, crediting Foreca."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True

    def __init__(self, coordinator: ForecaCoordinator, key: str) -> None:
        """Key the entity's unique id to its config entry."""
        super().__init__(coordinator)
        entry = coordinator.config_entry
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_device_info = foreca_device_info(entry)
