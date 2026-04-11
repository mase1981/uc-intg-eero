"""
eero WiFi switch entities for network feature toggles.

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging
from typing import Any

from ucapi import StatusCodes
from ucapi.switch import Attributes, Commands, States

from ucapi_framework import SwitchEntity, SwitchAttributes, create_entity_id

from uc_intg_eero.config import EeroDeviceConfig
from uc_intg_eero.device import EeroDevice

_LOG = logging.getLogger(__name__)


class EeroSwitch(SwitchEntity):
    """Base eero switch entity for network feature toggles."""

    def __init__(
        self,
        config: EeroDeviceConfig,
        device: EeroDevice,
        switch_id: str,
        switch_name: str,
    ):
        self._device = device
        self._config = config
        self._switch_id = switch_id

        entity_id = create_entity_id("switch", config.identifier, switch_id)

        super().__init__(
            entity_id,
            f"{config.name} - {switch_name}",
            [],
            {Attributes.STATE: States.UNAVAILABLE},
            cmd_handler=self._handle_command,
        )

        self.subscribe_to_device(device)

    async def _handle_command(self, entity_id: str, cmd_id: str, params: dict[str, Any] | None) -> StatusCodes:
        if not self._device.is_connected or not self._device.client:
            return StatusCodes.SERVICE_UNAVAILABLE

        try:
            if cmd_id == Commands.ON:
                await self._set_value(True)
                self.update(SwitchAttributes(STATE=States.ON))
                return StatusCodes.OK
            elif cmd_id == Commands.OFF:
                await self._set_value(False)
                self.update(SwitchAttributes(STATE=States.OFF))
                return StatusCodes.OK
            elif cmd_id == Commands.TOGGLE:
                current = self._get_current_state()
                new_state = not current
                await self._set_value(new_state)
                self.update(SwitchAttributes(STATE=States.ON if new_state else States.OFF))
                return StatusCodes.OK
        except Exception as err:
            _LOG.error("Switch %s command %s failed: %s", self._switch_id, cmd_id, err)
            return StatusCodes.SERVER_ERROR

        return StatusCodes.NOT_IMPLEMENTED

    async def sync_state(self) -> None:
        if not self._device.is_connected:
            self.update(SwitchAttributes(STATE=States.UNAVAILABLE))
            return
        current = self._get_current_state()
        self.update(SwitchAttributes(STATE=States.ON if current else States.OFF))

    def _get_current_state(self) -> bool:
        raise NotImplementedError

    async def _set_value(self, value: bool) -> None:
        raise NotImplementedError


class GuestNetworkSwitch(EeroSwitch):
    def __init__(self, config: EeroDeviceConfig, device: EeroDevice):
        super().__init__(config, device, "guest_network", "Guest Network")

    def _get_current_state(self) -> bool:
        return self._device.guest_network_enabled

    async def _set_value(self, value: bool) -> None:
        await self._device.client.set_guest_network(self._device.network_id, value)


class BandSteeringSwitch(EeroSwitch):
    def __init__(self, config: EeroDeviceConfig, device: EeroDevice):
        super().__init__(config, device, "band_steering", "Band Steering")

    def _get_current_state(self) -> bool:
        return self._device.band_steering

    async def _set_value(self, value: bool) -> None:
        await self._device.client.set_network_setting(
            self._device.settings_url, "band_steering", value
        )


class SqmSwitch(EeroSwitch):
    def __init__(self, config: EeroDeviceConfig, device: EeroDevice):
        super().__init__(config, device, "sqm", "SQM (Smart Queue Management)")

    def _get_current_state(self) -> bool:
        return self._device.sqm

    async def _set_value(self, value: bool) -> None:
        await self._device.client.set_network_setting(
            self._device.settings_url, "sqm", value
        )


class UpnpSwitch(EeroSwitch):
    def __init__(self, config: EeroDeviceConfig, device: EeroDevice):
        super().__init__(config, device, "upnp", "UPnP")

    def _get_current_state(self) -> bool:
        return self._device.upnp

    async def _set_value(self, value: bool) -> None:
        await self._device.client.set_network_setting(
            self._device.settings_url, "upnp", value
        )


class Wpa3Switch(EeroSwitch):
    def __init__(self, config: EeroDeviceConfig, device: EeroDevice):
        super().__init__(config, device, "wpa3", "WPA3")

    def _get_current_state(self) -> bool:
        return self._device.wpa3

    async def _set_value(self, value: bool) -> None:
        await self._device.client.set_network_setting(
            self._device.settings_url, "wpa3", value
        )


class Ipv6Switch(EeroSwitch):
    def __init__(self, config: EeroDeviceConfig, device: EeroDevice):
        super().__init__(config, device, "ipv6", "IPv6")

    def _get_current_state(self) -> bool:
        return self._device.ipv6

    async def _set_value(self, value: bool) -> None:
        await self._device.client.set_network_setting(
            self._device.settings_url, "ipv6_upstream", value
        )


class DnsCachingSwitch(EeroSwitch):
    def __init__(self, config: EeroDeviceConfig, device: EeroDevice):
        super().__init__(config, device, "dns_caching", "DNS Caching")

    def _get_current_state(self) -> bool:
        return self._device.dns_caching

    async def _set_value(self, value: bool) -> None:
        await self._device.client.set_dns_caching(self._device.network_id, value)


class AdBlockSwitch(EeroSwitch):
    def __init__(self, config: EeroDeviceConfig, device: EeroDevice):
        super().__init__(config, device, "ad_block", "Ad Blocking")

    def _get_current_state(self) -> bool:
        return self._device.ad_block_enabled

    async def _set_value(self, value: bool) -> None:
        await self._device.client.set_ad_block(self._device.network_url, value)


class BlockMalwareSwitch(EeroSwitch):
    def __init__(self, config: EeroDeviceConfig, device: EeroDevice):
        super().__init__(config, device, "block_malware", "Block Malware")

    def _get_current_state(self) -> bool:
        return self._device.block_malware

    async def _set_value(self, value: bool) -> None:
        await self._device.client.set_block_malware(self._device.network_url, value)


class ThreadSwitch(EeroSwitch):
    def __init__(self, config: EeroDeviceConfig, device: EeroDevice):
        super().__init__(config, device, "thread", "Thread")

    def _get_current_state(self) -> bool:
        return self._device.thread_enabled

    async def _set_value(self, value: bool) -> None:
        thread_url = self._device.thread_url
        if thread_url:
            await self._device.client.set_thread(thread_url, value)


class DdnsSwitch(EeroSwitch):
    def __init__(self, config: EeroDeviceConfig, device: EeroDevice):
        super().__init__(config, device, "ddns", "Dynamic DNS")

    def _get_current_state(self) -> bool:
        return self._device.ddns_enabled

    async def _set_value(self, value: bool) -> None:
        await self._device.client.set_ddns(self._device.network_id, value)


class Pause5gSwitch(EeroSwitch):
    def __init__(self, config: EeroDeviceConfig, device: EeroDevice):
        super().__init__(config, device, "pause_5g", "Pause 5GHz")

    def _get_current_state(self) -> bool:
        return self._device.pause_5g_enabled

    async def _set_value(self, value: bool) -> None:
        await self._device.client.set_pause_5g(self._device.network_url, value)


class EeroLedSwitch(SwitchEntity):
    """Switch for individual eero node LED status light."""

    def __init__(
        self,
        config: EeroDeviceConfig,
        device: EeroDevice,
        eero_data: dict,
        index: int,
    ):
        self._device = device
        self._config = config
        self._eero_url = eero_data.get("url", "")
        self._led_url = eero_data.get("resources", {}).get("led_action", "")
        self._index = index

        location = eero_data.get("location", f"Eero {index + 1}")
        eero_id = self._eero_url.replace("/2.2/eeros/", "") if self._eero_url else f"eero_{index}"

        entity_id = create_entity_id("switch", config.identifier, f"led_{eero_id}")

        super().__init__(
            entity_id,
            f"{config.name} - {location} LED",
            [],
            {Attributes.STATE: States.UNAVAILABLE},
            cmd_handler=self._handle_command,
        )

        self.subscribe_to_device(device)

    async def _handle_command(self, entity_id: str, cmd_id: str, params: dict[str, Any] | None) -> StatusCodes:
        if not self._device.is_connected or not self._device.client:
            return StatusCodes.SERVICE_UNAVAILABLE

        try:
            if cmd_id == Commands.ON:
                await self._device.client.set_eero_led(self._led_url, True)
                self.update(SwitchAttributes(STATE=States.ON))
                return StatusCodes.OK
            elif cmd_id == Commands.OFF:
                await self._device.client.set_eero_led(self._led_url, False)
                self.update(SwitchAttributes(STATE=States.OFF))
                return StatusCodes.OK
            elif cmd_id == Commands.TOGGLE:
                eero = self._find_eero()
                current = eero.get("led_on", True) if eero else True
                await self._device.client.set_eero_led(self._led_url, not current)
                self.update(SwitchAttributes(STATE=States.OFF if current else States.ON))
                return StatusCodes.OK
        except Exception as err:
            _LOG.error("LED switch command failed: %s", err)
            return StatusCodes.SERVER_ERROR

        return StatusCodes.NOT_IMPLEMENTED

    async def sync_state(self) -> None:
        if not self._device.is_connected:
            self.update(SwitchAttributes(STATE=States.UNAVAILABLE))
            return

        eero = self._find_eero()
        if eero:
            led_on = eero.get("led_on", True)
            self.update(SwitchAttributes(STATE=States.ON if led_on else States.OFF))
        else:
            self.update(SwitchAttributes(STATE=States.UNAVAILABLE))

    def _find_eero(self) -> dict | None:
        for eero in self._device.eeros:
            if eero.get("url") == self._eero_url:
                return eero
        if self._index < len(self._device.eeros):
            return self._device.eeros[self._index]
        return None


def create_network_switches(config: EeroDeviceConfig, device: EeroDevice) -> list:
    """Create network-level switch entities."""
    return [
        GuestNetworkSwitch(config, device),
        BandSteeringSwitch(config, device),
        SqmSwitch(config, device),
        UpnpSwitch(config, device),
        Wpa3Switch(config, device),
        Ipv6Switch(config, device),
        DnsCachingSwitch(config, device),
        AdBlockSwitch(config, device),
        BlockMalwareSwitch(config, device),
        ThreadSwitch(config, device),
        DdnsSwitch(config, device),
        Pause5gSwitch(config, device),
    ]


def create_eero_led_switches(config: EeroDeviceConfig, device: EeroDevice) -> list:
    """Create LED switch entities for each eero node."""
    switches = []
    for i, eero_data in enumerate(device.eeros):
        led_url = eero_data.get("resources", {}).get("led_action", "")
        if led_url:
            switches.append(EeroLedSwitch(config, device, eero_data, i))
    return switches
