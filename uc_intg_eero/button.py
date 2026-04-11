"""
eero WiFi button entities for actions (reboot, speed test).

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging
from typing import Any

from ucapi import StatusCodes
from ucapi.button import Button, Commands

from uc_intg_eero.config import EeroDeviceConfig
from uc_intg_eero.device import EeroDevice

_LOG = logging.getLogger(__name__)


class EeroButton(Button):
    """Base eero button entity."""

    def __init__(
        self,
        config: EeroDeviceConfig,
        device: EeroDevice,
        button_id: str,
        button_name: str,
    ):
        self._device = device
        self._config = config
        self._button_id = button_id

        entity_id = f"button.{config.identifier}.{button_id}"

        super().__init__(
            entity_id,
            f"{config.name} - {button_name}",
            cmd_handler=self._handle_command,
        )

    async def _handle_command(self, entity: Button, cmd_id: str, params: dict[str, Any] | None) -> StatusCodes:
        if not self._device.is_connected or not self._device.client:
            return StatusCodes.SERVICE_UNAVAILABLE

        if cmd_id == Commands.PUSH:
            try:
                await self._execute()
                return StatusCodes.OK
            except Exception as err:
                _LOG.error("Button %s action failed: %s", self._button_id, err)
                return StatusCodes.SERVER_ERROR

        return StatusCodes.NOT_IMPLEMENTED

    async def _execute(self) -> None:
        raise NotImplementedError


class RebootNetworkButton(EeroButton):
    """Button to reboot the entire eero network."""

    def __init__(self, config: EeroDeviceConfig, device: EeroDevice):
        super().__init__(config, device, "reboot_network", "Reboot Network")

    async def _execute(self) -> None:
        reboot_url = self._device.reboot_url
        if reboot_url:
            await self._device.client.reboot_network(reboot_url)
            _LOG.info("[%s] Network reboot initiated", self._device.log_id)
        else:
            raise RuntimeError("Reboot URL not available")


class RunSpeedTestButton(EeroButton):
    """Button to trigger a speed test."""

    def __init__(self, config: EeroDeviceConfig, device: EeroDevice):
        super().__init__(config, device, "speed_test", "Run Speed Test")

    async def _execute(self) -> None:
        await self._device.client.run_speed_test(self._device.network_url)
        _LOG.info("[%s] Speed test initiated", self._device.log_id)


class RebootEeroButton(Button):
    """Button to reboot an individual eero node."""

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
        resources = eero_data.get("resources", {})
        self._reboot_url = resources.get("reboot", "") if isinstance(resources, dict) else ""
        self._index = index

        location = eero_data.get("location", f"Eero {index + 1}")
        eero_id = self._eero_url.replace("/2.2/eeros/", "") if self._eero_url else f"eero_{index}"

        entity_id = f"button.{config.identifier}.reboot_{eero_id}"

        super().__init__(
            entity_id,
            f"{config.name} - Reboot {location}",
            cmd_handler=self._handle_command,
        )

    async def _handle_command(self, entity: Button, cmd_id: str, params: dict[str, Any] | None) -> StatusCodes:
        if not self._device.is_connected or not self._device.client:
            return StatusCodes.SERVICE_UNAVAILABLE

        if cmd_id == Commands.PUSH:
            try:
                if self._reboot_url:
                    await self._device.client.reboot_eero(self._reboot_url)
                    _LOG.info("[%s] Eero reboot initiated", self._device.log_id)
                    return StatusCodes.OK
                return StatusCodes.NOT_IMPLEMENTED
            except Exception as err:
                _LOG.error("Eero reboot failed: %s", err)
                return StatusCodes.SERVER_ERROR

        return StatusCodes.NOT_IMPLEMENTED


def create_buttons(config: EeroDeviceConfig, device: EeroDevice) -> list:
    """Create all button entities."""
    buttons = [
        RebootNetworkButton(config, device),
        RunSpeedTestButton(config, device),
    ]

    for i, eero_data in enumerate(device.eeros):
        resources = eero_data.get("resources", {})
        reboot_url = resources.get("reboot", "") if isinstance(resources, dict) else ""
        if reboot_url:
            buttons.append(RebootEeroButton(config, device, eero_data, i))

    return buttons
