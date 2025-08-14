"""A selector for the miner's mining mode."""
from __future__ import annotations

import logging
from importlib.metadata import version

from .const import PYASIC_VERSION

try:
    import pyasic

    if not version("pyasic") == PYASIC_VERSION:
        raise ImportError
except ImportError:
    from .patch import install_package

    install_package(f"pyasic=={PYASIC_VERSION}")
    import pyasic

from pyasic.config.mining import MiningModeHPM
from pyasic.config.mining import MiningModeLPM
from pyasic.config.mining import MiningModeNormal

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from custom_components.miner import DOMAIN
from custom_components.miner import MinerCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback,
) -> None:
    """Add sensors for passed config_entry in HA."""
    coordinator: MinerCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    created = set()

    @callback
    def _create_entity(key: str):
        """Create a sensor entity."""
        created.add(key)

    await coordinator.async_config_entry_first_refresh()
    if (
            coordinator.miner.supports_power_modes
            and not coordinator.miner.supports_autotuning
    ):
        async_add_entities(
            [
                MinerPowerModeSwitch(
                    coordinator=coordinator,
                )
            ]
        )
    # EBE_20250812_BEGIN
    else:
        if coordinator.miner.supports_autotuning:
            _LOGGER.warning(f"EBE_20250812: select.py: add select entity for power limit value")

            async_add_entities(
                [
                    MinerPowerValueSwitch(
                        coordinator=coordinator,
                    )
                ]
            )


# EBE_20250812_END


class MinerPowerModeSwitch(CoordinatorEntity[MinerCoordinator], SelectEntity):
    """A selector for the miner's miner mode."""

    def __init__(
            self,
            coordinator: MinerCoordinator,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator=coordinator)
        self._attr_unique_id = f"{self.coordinator.data['mac']}-power-mode"

    @property
    def name(self) -> str | None:
        """Return name of the entity."""
        return f"{self.coordinator.config_entry.title} power mode"

    @property
    def device_info(self) -> entity.DeviceInfo:
        """Return device info."""
        return entity.DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.data["mac"])},
            manufacturer=self.coordinator.data["make"],
            model=self.coordinator.data["model"],
            sw_version=self.coordinator.data["fw_ver"],
            name=f"{self.coordinator.config_entry.title}",
        )

    @property
    def current_option(self) -> str | None:
        """The current option selected with the select."""
        config: pyasic.MinerConfig = self.coordinator.data["config"]
        # EBE_QQQ
        _LOGGER.warning(f"EBE_20250812: select.py: config.mining_mode.mode: {str(config.mining_mode.mode).title()}")
        return str(config.mining_mode.mode).title()

    @property
    def options(self) -> list[str]:
        """The allowed options for the selector."""
        return ["Normal", "High", "Low"]

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        option_map = {
            "High": MiningModeHPM,
            "Normal": MiningModeNormal,
            "Low": MiningModeLPM,
        }
        cfg = await self.coordinator.miner.get_config()
        cfg.mining_mode = option_map[option]()
        await self.coordinator.miner.send_config(cfg)


# EBE_20250812_BEGIN

class MinerPowerValueSwitch(CoordinatorEntity[MinerCoordinator], SelectEntity):
    """A selector for the miner's power value."""

    def __init__(
            self,
            coordinator: MinerCoordinator,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator=coordinator)
        self._attr_unique_id = f"{self.coordinator.data['mac']}-power-value"

    @property
    def name(self) -> str | None:
        """Return name of the entity."""
        return f"{self.coordinator.config_entry.title} Power Value"

    @property
    def device_info(self) -> entity.DeviceInfo:
        """Return device info."""
        return entity.DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.data["mac"])},
            manufacturer=self.coordinator.data["make"],
            model=self.coordinator.data["model"],
            sw_version=self.coordinator.data["fw_ver"],
            name=f"{self.coordinator.config_entry.title}",
        )

    def get_miner_current_power_limit(self) -> str | None:

        #        _LOGGER.warning(f"EBE_20250812: select.py get_miner_current_power_limit: self.coordinator.data: {self.coordinator.data}")
        #        _LOGGER.warning(f"EBE_20250812: select.py get_miner_current_power_limit: self.coordinator.miner: {self.coordinator.miner}")

        value = None

        try:

            _LOGGER.warning(
                f"EBE_20250812: select.py get_miner_current_power_limit: self.coordinator.data: {self.coordinator.data}")

            miner_data = str(self.coordinator.data)

            len = miner_data.__len__()
            #        _LOGGER.warning(f"EBE_20250812: select.py get_miner_current_power_limit: miner_data.len: {len}")
            if len <= 0:
                return None

            pos = miner_data.find("'power_limit':", 0, len - 1)
            #        _LOGGER.warning(f"EBE_20250812: select.py get_miner_current_power_limit: miner_data.pos: {pos}")

            #            value = None
            if pos != -1:
                pos_separator = miner_data.find(",", pos, len - 1)
                if pos_separator == -1:
                    pos_separator = len
                #            _LOGGER.warning(f"EBE_20250812: select.py get_miner_current_power_limit: miner_data.pos_separator: {pos_separator}")

                value = miner_data[pos + 15:pos_separator]
        #            _LOGGER.warning(f"EBE_20250812: select.py get_miner_current_power_limit: miner_data.value: {value}")

        except Exception as err:
            _LOGGER.error(
                f"EBE_20250812: select.py current_option: get_miner_current_power_limit: couldn't get miner data")
            return None

        return str(value)

    @property
    def current_option(self) -> str | None:
        """The current option selected with the select."""
        #        config: pyasic.MinerConfig = self.coordinator.data["config"]
        #        return str(config.mining_mode.mode).title()

        #        _LOGGER.warning(f"EBE_20250812_167: select.py current_option: self.coordinator.data: {self.coordinator.data}")
        ##        _LOGGER.warning(f"EBE_20250812_168: select.py current_option: self.coordinator.miner: {self.coordinator.miner}")

        #        miner_data = str(self.coordinator.data)

        #        len = miner_data.__len__()
        #        _LOGGER.warning(f"EBE_20250812_173: select.py current_option: miner_data.len: {len}")
        #        if len <= 0:
        #            return None

        #        pos = miner_data.find("'power_limit':", 0, len - 1)
        #        _LOGGER.warning(f"EBE_20250812_178: select.py current_option: miner_data.pos: {pos}")

        #        value = None
        #        if pos != -1:
        #            pos_separator = miner_data.find(",", pos, len - 1)
        #            if pos_separator == -1:
        #                pos_separator = len
        #            _LOGGER.warning(f"EBE_20250812_185: select.py current_option: miner_data.pos_separator: {pos_separator}")

        #            value = miner_data[pos+15:pos_separator]
        #            _LOGGER.warning(f"EBE_20250812_188: select.py current_option: miner_data.value: {value}")

        #        value = 4200

        #        return str(value)

        current_power_limit = self.get_miner_current_power_limit()
        #        current_power_limit = None
        #
        #        try:
        #            current_power_limit = self.get_miner_current_power_limit()
        #            _LOGGER.warning(f"EBE_20250812: select.py current_option: miner_data.value: current_power_limit {current_power_limit}")
        #        except Exception as err:
        #            _LOGGER.error(f"EBE_20250812: select.py current_option: miner_data.value: couldn't get current_power_limit")
        #            return None

        _LOGGER.warning(
            f"EBE_20250812: select.py current_option: miner_data.value: current_power_limit {current_power_limit}")

        return current_power_limit

    def define_option_list(self) -> list[str]:

        list = ["1800", "2700", "3900", "4200", "5400"]

        #        current_power_limit = None
        #        try:

        current_power_limit = self.get_miner_current_power_limit()
        _LOGGER.warning(f"EBE_20250812: select.py options: miner_data.value: define_option_list {current_power_limit}")

        if current_power_limit != None:

            found = False
            for entry in list:
                if entry == current_power_limit:
                    found = True
                    break
            if not found:
                list.insert(0, current_power_limit)

            _LOGGER.warning(f"EBE_20250812: select.py options: miner_data.value: define_option_list {list}")

        #        except Exception as err:
        #            _LOGGER.error(f"EBE_20250812: select.py current_option: define_option_list: couldn't get miner data")
        #            return None

        return list

    @property
    def options(self) -> list[str]:
        """The allowed options for the selector."""
        #        return [ "2100 - Low", "3900 - Normal", "5400 - High"]

        list = self.define_option_list()

        return list

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        #        option_map = {
        #            "High": MiningModeHPM,
        #            "Normal": MiningModeNormal,
        #            "Low": MiningModeLPM,
        #        }
        #        cfg = await self.coordinator.miner.get_config()
        #        cfg.mining_mode = option_map[option]()
        #        await self.coordinator.miner.send_config(cfg)

        _LOGGER.warning(f"EBE_20250812: select.py: set select entity for power limit value: {option}")

        #        if (
        #            option == "2100"
        #            or option == "3900"
        #            or option == "5400"
        #        ):
        #            value = option

        list = self.define_option_list()

        found = False
        for entry in list:
            if entry == option:
                found = True
                break

        if found:
            _LOGGER.warning(f"EBE_20250812: select.py: async_select_option: valid option found: {option}")

            value = option

            miner = self.coordinator.miner

            _LOGGER.debug(
                f"{self.coordinator.config_entry.title}: setting power limit to {value}."
            )

            if not miner.supports_autotuning:
                raise TypeError(
                    f"{self.coordinator.config_entry.title}: Tuning not supported."
                )

            #            result = False
            result = await miner.set_power_limit(int(value))
            result = True

            if not result:
                raise pyasic.APIError("Failed to set wattage.")

            _LOGGER.warning(f"EBE_20250812: select.py: successfully set power limit value: {value}")

            self._attr_native_value = value
            self.async_write_ha_state()
        else:
            _LOGGER.warning(f"EBE_20250812: select.py: invalid option for power limit value: {option}")

# EBE_20250812_END

