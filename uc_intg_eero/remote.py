"""
eero WiFi remote entity - provides organized UI pages for all network controls.

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging
from typing import Any

from ucapi import StatusCodes
from ucapi.remote import Remote, Attributes, Commands, Features, States
from ucapi.ui import EntityCommand, Size, UiPage, create_ui_text

from uc_intg_eero.config import EeroDeviceConfig
from uc_intg_eero.device import EeroDevice

_LOG = logging.getLogger(__name__)

CMD_TOGGLE_GUEST_NETWORK = "toggle_guest_network"
CMD_TOGGLE_BAND_STEERING = "toggle_band_steering"
CMD_TOGGLE_SQM = "toggle_sqm"
CMD_TOGGLE_UPNP = "toggle_upnp"
CMD_TOGGLE_WPA3 = "toggle_wpa3"
CMD_TOGGLE_IPV6 = "toggle_ipv6"
CMD_TOGGLE_DNS_CACHING = "toggle_dns_caching"
CMD_TOGGLE_AD_BLOCK = "toggle_ad_block"
CMD_TOGGLE_BLOCK_MALWARE = "toggle_block_malware"
CMD_TOGGLE_THREAD = "toggle_thread"
CMD_TOGGLE_DDNS = "toggle_ddns"
CMD_TOGGLE_PAUSE_5G = "toggle_pause_5g"
CMD_REBOOT_NETWORK = "reboot_network"
CMD_SPEED_TEST = "speed_test"
CMD_TOGGLE_LED_PREFIX = "toggle_led_"
CMD_REBOOT_EERO_PREFIX = "reboot_eero_"


class EeroRemote(Remote):
    """Remote entity for eero WiFi network control."""

    def __init__(self, config: EeroDeviceConfig, device: EeroDevice):
        self._config = config
        self._device = device

        entity_id = f"remote.{config.identifier}"
        simple_commands = self._get_simple_commands()

        super().__init__(
            identifier=entity_id,
            name=f"{config.name} Remote",
            features=[Features.ON_OFF, Features.SEND_CMD],
            attributes={Attributes.STATE: States.ON},
            simple_commands=simple_commands,
            ui_pages=self._create_ui_pages(),
            cmd_handler=self._handle_command,
        )

    def _get_simple_commands(self) -> list[str]:
        cmds = [
            CMD_TOGGLE_GUEST_NETWORK,
            CMD_TOGGLE_BAND_STEERING,
            CMD_TOGGLE_SQM,
            CMD_TOGGLE_UPNP,
            CMD_TOGGLE_WPA3,
            CMD_TOGGLE_IPV6,
            CMD_TOGGLE_DNS_CACHING,
            CMD_TOGGLE_AD_BLOCK,
            CMD_TOGGLE_BLOCK_MALWARE,
            CMD_TOGGLE_THREAD,
            CMD_TOGGLE_DDNS,
            CMD_TOGGLE_PAUSE_5G,
            CMD_REBOOT_NETWORK,
            CMD_SPEED_TEST,
        ]

        for eero_data in self._device.eeros:
            eero_url = eero_data.get("url", "")
            eero_id = eero_url.replace("/2.2/eeros/", "") if eero_url else ""
            if eero_id:
                resources = eero_data.get("resources", {})
                if isinstance(resources, dict):
                    if resources.get("led_action", ""):
                        cmds.append(f"{CMD_TOGGLE_LED_PREFIX}{eero_id}")
                    if resources.get("reboot", ""):
                        cmds.append(f"{CMD_REBOOT_EERO_PREFIX}{eero_id}")

        return cmds

    async def _handle_command(
        self, entity: Remote, cmd_id: str, params: dict[str, Any] | None = None
    ) -> StatusCodes:
        if not self._device.is_connected or not self._device.client:
            return StatusCodes.SERVICE_UNAVAILABLE

        try:
            if cmd_id in (Commands.ON, Commands.OFF):
                return StatusCodes.OK

            if cmd_id == Commands.SEND_CMD:
                if not params or "command" not in params:
                    return StatusCodes.BAD_REQUEST
                return await self._execute_command(params["command"])

            return StatusCodes.NOT_IMPLEMENTED

        except Exception as err:
            _LOG.error("Remote command failed: %s", err)
            return StatusCodes.SERVER_ERROR

    async def _execute_command(self, command: str) -> StatusCodes:
        client = self._device.client

        if command == CMD_TOGGLE_GUEST_NETWORK:
            new_val = not self._device.guest_network_enabled
            await client.set_guest_network(self._device.network_id, new_val)

        elif command == CMD_TOGGLE_BAND_STEERING:
            new_val = not self._device.band_steering
            await client.set_network_setting(self._device.settings_url, "band_steering", new_val)

        elif command == CMD_TOGGLE_SQM:
            new_val = not self._device.sqm
            await client.set_network_setting(self._device.settings_url, "sqm", new_val)

        elif command == CMD_TOGGLE_UPNP:
            new_val = not self._device.upnp
            await client.set_network_setting(self._device.settings_url, "upnp", new_val)

        elif command == CMD_TOGGLE_WPA3:
            new_val = not self._device.wpa3
            await client.set_network_setting(self._device.settings_url, "wpa3", new_val)

        elif command == CMD_TOGGLE_IPV6:
            new_val = not self._device.ipv6
            await client.set_network_setting(self._device.settings_url, "ipv6_upstream", new_val)

        elif command == CMD_TOGGLE_DNS_CACHING:
            new_val = not self._device.dns_caching
            await client.set_dns_caching(self._device.dns_url, new_val)

        elif command == CMD_TOGGLE_AD_BLOCK:
            new_val = not self._device.ad_block_enabled
            await client.set_ad_block(self._device.network_url, new_val)

        elif command == CMD_TOGGLE_BLOCK_MALWARE:
            new_val = not self._device.block_malware
            await client.set_block_malware(self._device.network_url, new_val)

        elif command == CMD_TOGGLE_THREAD:
            new_val = not self._device.thread_enabled
            thread_url = self._device.thread_url
            if thread_url:
                await client.set_thread(thread_url, new_val)
            else:
                return StatusCodes.NOT_IMPLEMENTED

        elif command == CMD_TOGGLE_DDNS:
            new_val = not self._device.ddns_enabled
            await client.set_ddns(self._device.network_id, new_val)

        elif command == CMD_TOGGLE_PAUSE_5G:
            new_val = not self._device.pause_5g_enabled
            await client.set_pause_5g(self._device.network_url, new_val)

        elif command == CMD_REBOOT_NETWORK:
            reboot_url = self._device.reboot_url
            if reboot_url:
                await client.reboot_network(reboot_url)
                _LOG.info("[%s] Network reboot initiated", self._device.log_id)
            else:
                return StatusCodes.NOT_IMPLEMENTED

        elif command == CMD_SPEED_TEST:
            await client.run_speed_test(self._device.network_url)
            _LOG.info("[%s] Speed test initiated", self._device.log_id)

        elif command.startswith(CMD_TOGGLE_LED_PREFIX):
            eero_id = command[len(CMD_TOGGLE_LED_PREFIX):]
            return await self._toggle_eero_led(eero_id)

        elif command.startswith(CMD_REBOOT_EERO_PREFIX):
            eero_id = command[len(CMD_REBOOT_EERO_PREFIX):]
            return await self._reboot_eero(eero_id)

        else:
            _LOG.warning("Unknown remote command: %s", command)
            return StatusCodes.NOT_IMPLEMENTED

        return StatusCodes.OK

    async def _toggle_eero_led(self, eero_id: str) -> StatusCodes:
        for eero_data in self._device.eeros:
            eero_url = eero_data.get("url", "")
            if eero_url.endswith(eero_id):
                resources = eero_data.get("resources", {})
                led_url = resources.get("led_action", "") if isinstance(resources, dict) else ""
                if led_url:
                    current = eero_data.get("led_on", True)
                    await self._device.client.set_eero_led(led_url, not current)
                    return StatusCodes.OK
        return StatusCodes.NOT_FOUND

    async def _reboot_eero(self, eero_id: str) -> StatusCodes:
        for eero_data in self._device.eeros:
            eero_url = eero_data.get("url", "")
            if eero_url.endswith(eero_id):
                resources = eero_data.get("resources", {})
                reboot_url = resources.get("reboot", "") if isinstance(resources, dict) else ""
                if reboot_url:
                    await self._device.client.reboot_eero(reboot_url)
                    _LOG.info("Eero %s reboot initiated", eero_id)
                    return StatusCodes.OK
        return StatusCodes.NOT_FOUND

    def _create_ui_pages(self) -> list[UiPage]:
        pages = [
            self._create_network_page(),
            self._create_security_dns_page(),
            self._create_actions_page(),
        ]

        eero_page = self._create_eero_nodes_page()
        if eero_page:
            pages.append(eero_page)

        return pages

    def _create_network_page(self) -> UiPage:
        items = [
            create_ui_text("Network Settings", 0, 0, size=Size(4, 1)),
            create_ui_text("Guest Net", 0, 1, size=Size(2, 1),
                           cmd=EntityCommand("send_cmd", {"command": CMD_TOGGLE_GUEST_NETWORK})),
            create_ui_text("WPA3", 2, 1, size=Size(2, 1),
                           cmd=EntityCommand("send_cmd", {"command": CMD_TOGGLE_WPA3})),
            create_ui_text("Band Steer", 0, 2, size=Size(2, 1),
                           cmd=EntityCommand("send_cmd", {"command": CMD_TOGGLE_BAND_STEERING})),
            create_ui_text("SQM", 2, 2, size=Size(2, 1),
                           cmd=EntityCommand("send_cmd", {"command": CMD_TOGGLE_SQM})),
            create_ui_text("UPnP", 0, 3, size=Size(2, 1),
                           cmd=EntityCommand("send_cmd", {"command": CMD_TOGGLE_UPNP})),
            create_ui_text("IPv6", 2, 3, size=Size(2, 1),
                           cmd=EntityCommand("send_cmd", {"command": CMD_TOGGLE_IPV6})),
        ]
        return UiPage(page_id="network", name="Network", grid=Size(4, 6), items=items)

    def _create_security_dns_page(self) -> UiPage:
        items = [
            create_ui_text("Security & DNS", 0, 0, size=Size(4, 1)),
            create_ui_text("Ad Block", 0, 1, size=Size(2, 1),
                           cmd=EntityCommand("send_cmd", {"command": CMD_TOGGLE_AD_BLOCK})),
            create_ui_text("Malware", 2, 1, size=Size(2, 1),
                           cmd=EntityCommand("send_cmd", {"command": CMD_TOGGLE_BLOCK_MALWARE})),
            create_ui_text("DNS Cache", 0, 2, size=Size(2, 1),
                           cmd=EntityCommand("send_cmd", {"command": CMD_TOGGLE_DNS_CACHING})),
            create_ui_text("DDNS", 2, 2, size=Size(2, 1),
                           cmd=EntityCommand("send_cmd", {"command": CMD_TOGGLE_DDNS})),
            create_ui_text("Thread", 0, 3, size=Size(2, 1),
                           cmd=EntityCommand("send_cmd", {"command": CMD_TOGGLE_THREAD})),
            create_ui_text("Pause 5G", 2, 3, size=Size(2, 1),
                           cmd=EntityCommand("send_cmd", {"command": CMD_TOGGLE_PAUSE_5G})),
        ]
        return UiPage(page_id="security", name="Security", grid=Size(4, 6), items=items)

    def _create_actions_page(self) -> UiPage:
        items = [
            create_ui_text("Actions", 0, 0, size=Size(4, 1)),
            create_ui_text("Reboot Network", 0, 1, size=Size(2, 1),
                           cmd=EntityCommand("send_cmd", {"command": CMD_REBOOT_NETWORK})),
            create_ui_text("Speed Test", 2, 1, size=Size(2, 1),
                           cmd=EntityCommand("send_cmd", {"command": CMD_SPEED_TEST})),
        ]
        return UiPage(page_id="actions", name="Actions", grid=Size(4, 6), items=items)

    def _create_eero_nodes_page(self) -> UiPage | None:
        eeros = self._device.eeros
        if not eeros:
            return None

        items = [
            create_ui_text("Eero Nodes", 0, 0, size=Size(4, 1)),
        ]

        row = 1
        for eero_data in eeros:
            if row >= 6:
                break

            eero_url = eero_data.get("url", "")
            eero_id = eero_url.replace("/2.2/eeros/", "") if eero_url else ""
            location = eero_data.get("location", "Eero")
            resources = eero_data.get("resources", {})
            if not isinstance(resources, dict):
                resources = {}

            has_led = bool(resources.get("led_action", ""))
            has_reboot = bool(resources.get("reboot", ""))

            if has_led and has_reboot:
                items.append(create_ui_text(location, 0, row, size=Size(2, 1)))
                items.append(create_ui_text("LED", 2, row, size=Size(1, 1),
                                            cmd=EntityCommand("send_cmd", {"command": f"{CMD_TOGGLE_LED_PREFIX}{eero_id}"})))
                items.append(create_ui_text("Reboot", 3, row, size=Size(1, 1),
                                            cmd=EntityCommand("send_cmd", {"command": f"{CMD_REBOOT_EERO_PREFIX}{eero_id}"})))
            elif has_led:
                items.append(create_ui_text(location, 0, row, size=Size(2, 1)))
                items.append(create_ui_text("LED", 2, row, size=Size(2, 1),
                                            cmd=EntityCommand("send_cmd", {"command": f"{CMD_TOGGLE_LED_PREFIX}{eero_id}"})))
            elif has_reboot:
                items.append(create_ui_text(location, 0, row, size=Size(2, 1)))
                items.append(create_ui_text("Reboot", 2, row, size=Size(2, 1),
                                            cmd=EntityCommand("send_cmd", {"command": f"{CMD_REBOOT_EERO_PREFIX}{eero_id}"})))

            row += 1

        return UiPage(page_id="nodes", name="Nodes", grid=Size(4, 6), items=items)


def create_remote(config: EeroDeviceConfig, device: EeroDevice) -> list:
    return [EeroRemote(config, device)]
