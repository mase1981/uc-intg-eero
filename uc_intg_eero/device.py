"""
eero WiFi device - PollingDevice for eero cloud API.

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging
from typing import Any

from ucapi_framework import DeviceEvents, PollingDevice

from uc_intg_eero.client import EeroClient
from uc_intg_eero.config import EeroDeviceConfig
from uc_intg_eero.const import POLL_INTERVAL

_LOG = logging.getLogger(__name__)


def _safe_get(data: dict, *keys, default=None):
    """Safely traverse nested dict keys, returning default if any key is missing or not a dict."""
    for key in keys:
        if not isinstance(data, dict):
            return default
        data = data.get(key, default)
    return data


class EeroDevice(PollingDevice):
    """eero WiFi network device with cloud polling."""

    def __init__(self, device_config: EeroDeviceConfig, **kwargs):
        super().__init__(device_config, poll_interval=POLL_INTERVAL, **kwargs)
        self._device_config = device_config
        self._client: EeroClient | None = None
        self._is_connected = False

        # Account data
        self._account_data: dict[str, Any] = {}
        self._account_name: str = ""

        # Network data
        self._network_data: dict[str, Any] = {}
        self._network_id: str = device_config.network_id
        self._network_url: str = f"/2.2/networks/{device_config.network_id}" if device_config.network_id else ""

        # Eero nodes (mesh routers)
        self._eeros: list[dict[str, Any]] = []

        # Connected clients
        self._clients: list[dict[str, Any]] = []

        # Firmware update data
        self._target_firmware: dict[str, Any] = {}
        self._firmware_history: list[dict[str, Any]] = []

        # Speed test data
        self._speed_down: float | None = None
        self._speed_down_units: str = "Mbps"
        self._speed_up: float | None = None
        self._speed_up_units: str = "Mbps"

    @property
    def identifier(self) -> str:
        return self._device_config.identifier

    @property
    def name(self) -> str:
        return self._device_config.name

    @property
    def address(self) -> str:
        return "eero-cloud"

    @property
    def log_id(self) -> str:
        return f"{self.name} ({self._network_id})"

    @property
    def is_connected(self) -> bool:
        return self._is_connected

    @property
    def state(self) -> str:
        return "ON" if self._is_connected else "OFF"

    @property
    def client(self) -> EeroClient | None:
        return self._client

    @property
    def network_data(self) -> dict[str, Any]:
        return self._network_data

    @property
    def network_id(self) -> str:
        return self._network_id

    @property
    def network_url(self) -> str:
        return self._network_url

    @property
    def network_name(self) -> str:
        return self._network_data.get("name", self._device_config.network_name)

    @property
    def network_status(self) -> str:
        return self._network_data.get("status", "unknown")

    @property
    def gateway_ip(self) -> str:
        return self._network_data.get("gateway_ip", "N/A")

    @property
    def public_ip(self) -> str:
        return _safe_get(self._network_data, "ip_settings", "public_ip", default="N/A")

    @property
    def wan_router_ip(self) -> str:
        return _safe_get(self._network_data, "lease", "dhcp", "router", default="N/A")

    @property
    def speed_down(self) -> str:
        if self._speed_down is not None:
            return f"{self._speed_down} {self._speed_down_units}"
        return "N/A"

    @property
    def speed_up(self) -> str:
        if self._speed_up is not None:
            return f"{self._speed_up} {self._speed_up_units}"
        return "N/A"

    @property
    def speed_date(self) -> str:
        return _safe_get(self._network_data, "speed", "date", default="N/A")

    @property
    def connected_clients_count(self) -> int:
        return _safe_get(self._network_data, "clients", "count", default=0)

    @property
    def eeros(self) -> list[dict[str, Any]]:
        return self._eeros

    @property
    def eero_count(self) -> int:
        return len(self._eeros)

    @property
    def clients(self) -> list[dict[str, Any]]:
        return self._clients

    @property
    def guest_network_enabled(self) -> bool:
        return _safe_get(self._network_data, "guest_network", "enabled", default=False)

    @property
    def guest_network_name(self) -> str:
        return _safe_get(self._network_data, "guest_network", "name", default="")

    @property
    def band_steering(self) -> bool:
        return self._network_data.get("band_steering", False)

    @property
    def sqm(self) -> bool:
        return self._network_data.get("sqm", False)

    @property
    def upnp(self) -> bool:
        return self._network_data.get("upnp", False)

    @property
    def wpa3(self) -> bool:
        return self._network_data.get("wpa3", False)

    @property
    def ipv6(self) -> bool:
        return self._network_data.get("ipv6_upstream", False)

    @property
    def dns_caching(self) -> bool:
        return _safe_get(self._network_data, "dns", "caching", default=False)

    @property
    def ad_block_enabled(self) -> bool:
        return _safe_get(self._network_data, "premium_dns", "ad_block_settings", "enabled", default=False)

    @property
    def block_malware(self) -> bool:
        return _safe_get(self._network_data, "premium_dns", "dns_policies", "block_malware", default=False)

    @property
    def thread_enabled(self) -> bool:
        return _safe_get(self._network_data, "thread", "enabled", default=False)

    @property
    def ddns_enabled(self) -> bool:
        return _safe_get(self._network_data, "ddns", "enabled", default=False)

    @property
    def pause_5g_enabled(self) -> bool:
        return _safe_get(self._network_data, "temporary_flags", "hide_5g", "value", default=False)

    @property
    def premium_enabled(self) -> bool:
        status = self._network_data.get("premium_status", "")
        capable = _safe_get(self._network_data, "capabilities", "premium", "capable", default=False)
        return capable and status in ("active", "trialing")

    @property
    def health_internet_status(self) -> str:
        return _safe_get(self._network_data, "health", "internet", "status", default="unknown")

    @property
    def health_eero_network_status(self) -> str:
        return _safe_get(self._network_data, "health", "eero_network", "status", default="unknown")

    @property
    def isp(self) -> str:
        return _safe_get(self._network_data, "geo_ip", "isp", default="N/A")

    @property
    def city(self) -> str:
        return _safe_get(self._network_data, "geo_ip", "city", default="")

    @property
    def target_firmware(self) -> dict[str, Any]:
        return self._target_firmware

    @property
    def updates_url(self) -> str:
        return _safe_get(self._network_data, "resources", "updates", default="")

    def get_eero_firmware_info(self, eero_data: dict) -> dict[str, str]:
        current = eero_data.get("os_version", "Unknown")
        current_base = current.split("-")[0] if current else "Unknown"
        target_ver = _safe_get(self._target_firmware, "os_version", default=None)
        if target_ver and target_ver != current_base:
            return {"current": current, "target": target_ver, "update_available": "Yes"}
        return {"current": current, "target": current_base, "update_available": "No"}

    @property
    def thread_url(self) -> str:
        return _safe_get(self._network_data, "resources", "thread", default="")

    @property
    def reboot_url(self) -> str:
        return _safe_get(self._network_data, "resources", "reboot", default="")

    @property
    def dns_url(self) -> str:
        return _safe_get(self._network_data, "resources", "dns", default="")

    @property
    def settings_url(self) -> str:
        return _safe_get(self._network_data, "resources", "settings", default="")

    async def establish_connection(self) -> None:
        _LOG.info("[%s] Connecting to eero cloud API", self.log_id)

        self._client = EeroClient(user_token=self._device_config.user_token)

        try:
            connected = await self._client.test_connection()
            if not connected:
                raise ConnectionError("Failed to authenticate with eero cloud API")

            await self._fetch_data()
            self._is_connected = True
            self.events.emit(DeviceEvents.CONNECTED, self.identifier)
            _LOG.info("[%s] Connected - Network: %s, Eeros: %d, Clients: %d",
                      self.log_id, self.network_name, self.eero_count, self.connected_clients_count)

        except Exception as err:
            _LOG.error("[%s] Connection failed: %s", self.log_id, err)
            if self._client:
                await self._client.close()
                self._client = None
            raise ConnectionError(f"Failed to connect: {err}") from err

    async def _fetch_data(self) -> None:
        if not self._client:
            raise ConnectionError("No API client")

        account = await self._client.get_account()
        self._account_data = account
        self._account_name = account.get("name", "")

        networks = _safe_get(account, "networks", "data", default=[])
        if not networks:
            raise ConnectionError("No networks found in eero account")

        target_network = None
        for net in networks:
            net_url = net.get("url", "")
            net_id = net_url.replace("/2.2/networks/", "")
            if self._network_id and net_id == self._network_id:
                target_network = net
                break

        if not target_network and not self._network_id:
            target_network = networks[0]
            self._network_url = target_network.get("url", "")
            self._network_id = self._network_url.replace("/2.2/networks/", "")

        if not target_network:
            raise ConnectionError(f"Network {self._network_id} not found")

        self._network_url = target_network.get("url", self._network_url)
        network_data = await self._client.get_network(self._network_url)
        self._network_data = network_data

        self._speed_down = _safe_get(network_data, "speed", "down", "value", default=None)
        self._speed_down_units = _safe_get(network_data, "speed", "down", "units", default="Mbps")
        self._speed_up = _safe_get(network_data, "speed", "up", "value", default=None)
        self._speed_up_units = _safe_get(network_data, "speed", "up", "units", default="Mbps")

        self._eeros = _safe_get(network_data, "eeros", "data", default=[])

        self._target_firmware = _safe_get(
            network_data, "updates", "release_notes", "target", default={}
        )
        self._firmware_history = _safe_get(
            network_data, "updates", "release_notes", "history", default=[]
        )

        devices_url = _safe_get(network_data, "resources", "devices", default="")
        if devices_url:
            try:
                self._clients = await self._client.get_network_devices(devices_url)
            except Exception as err:
                _LOG.warning("[%s] Failed to fetch clients: %s", self.log_id, err)
                self._clients = []

    async def poll_device(self) -> None:
        if not self._is_connected or not self._client:
            _LOG.debug("[%s] Not connected, attempting reconnection", self.log_id)
            try:
                await self.establish_connection()
            except Exception as err:
                _LOG.debug("[%s] Reconnection failed: %s", self.log_id, err)
                return

        try:
            await self._fetch_data()
            self._emit_entity_updates()
        except Exception as err:
            _LOG.warning("[%s] Poll failed: %s", self.log_id, err)
            self._is_connected = False
            self.events.emit(DeviceEvents.DISCONNECTED, self.identifier)

    def _emit_entity_updates(self) -> None:
        """Emit per-entity UPDATE events for all entities."""
        ident = self._device_config.identifier

        # Sensor updates
        self.events.emit(DeviceEvents.UPDATE, f"sensor.{ident}.network_status",
                        {"state": "ON", "value": f"{self.network_status} | Internet: {self.health_internet_status}"})
        self.events.emit(DeviceEvents.UPDATE, f"sensor.{ident}.gateway_ip",
                        {"state": "ON", "value": self.gateway_ip})
        self.events.emit(DeviceEvents.UPDATE, f"sensor.{ident}.public_ip",
                        {"state": "ON", "value": self.public_ip})
        self.events.emit(DeviceEvents.UPDATE, f"sensor.{ident}.wan_router_ip",
                        {"state": "ON", "value": self.wan_router_ip})
        self.events.emit(DeviceEvents.UPDATE, f"sensor.{ident}.speed_down",
                        {"state": "ON", "value": self.speed_down})
        self.events.emit(DeviceEvents.UPDATE, f"sensor.{ident}.speed_up",
                        {"state": "ON", "value": self.speed_up})
        self.events.emit(DeviceEvents.UPDATE, f"sensor.{ident}.connected_clients",
                        {"state": "ON", "value": str(self.connected_clients_count)})
        self.events.emit(DeviceEvents.UPDATE, f"sensor.{ident}.eero_count",
                        {"state": "ON", "value": str(self.eero_count)})
        self.events.emit(DeviceEvents.UPDATE, f"sensor.{ident}.isp",
                        {"state": "ON", "value": self.isp})
        self.events.emit(DeviceEvents.UPDATE, f"sensor.{ident}.speed_date",
                        {"state": "ON", "value": self.speed_date})

        for eero_data in self._eeros:
            eero_url = eero_data.get("url", "")
            eero_id = eero_url.replace("/2.2/eeros/", "") if eero_url else ""
            if eero_id:
                status = eero_data.get("status", "unknown")
                clients = eero_data.get("connected_clients_count", 0)
                os_ver = eero_data.get("os_version", "?")
                value = f"{status} | Clients: {clients} | OS: {os_ver}"
                self.events.emit(DeviceEvents.UPDATE, f"sensor.{ident}.eero_{eero_id}",
                                {"state": "ON", "value": value})

                fw_info = self.get_eero_firmware_info(eero_data)
                if fw_info["update_available"] == "Yes":
                    fw_value = f"{fw_info['current']} → {fw_info['target']}"
                else:
                    fw_value = f"{fw_info['current']} (Up to date)"
                self.events.emit(DeviceEvents.UPDATE, f"sensor.{ident}.firmware_{eero_id}",
                                {"state": "ON", "value": fw_value})

        # Switch updates
        switch_states = {
            "guest_network": self.guest_network_enabled,
            "band_steering": self.band_steering,
            "sqm": self.sqm,
            "upnp": self.upnp,
            "wpa3": self.wpa3,
            "ipv6": self.ipv6,
            "dns_caching": self.dns_caching,
            "ad_block": self.ad_block_enabled,
            "block_malware": self.block_malware,
            "thread": self.thread_enabled,
            "ddns": self.ddns_enabled,
            "pause_5g": self.pause_5g_enabled,
        }
        for switch_id, enabled in switch_states.items():
            state = "ON" if enabled else "OFF"
            self.events.emit(DeviceEvents.UPDATE, f"switch.{ident}.{switch_id}",
                            {"state": state})

        for eero_data in self._eeros:
            eero_url = eero_data.get("url", "")
            eero_id = eero_url.replace("/2.2/eeros/", "") if eero_url else ""
            if eero_id:
                led_on = eero_data.get("led_on", True)
                self.events.emit(DeviceEvents.UPDATE, f"switch.{ident}.led_{eero_id}",
                                {"state": "ON" if led_on else "OFF"})

        _LOG.debug("[%s] Emitted entity updates", self.log_id)

    async def disconnect(self) -> None:
        _LOG.info("[%s] Disconnecting", self.log_id)
        await super().disconnect()
        if self._client:
            await self._client.close()
            self._client = None
        self._is_connected = False
        self.events.emit(DeviceEvents.DISCONNECTED, self.identifier)
