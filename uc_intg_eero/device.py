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
        return self._network_data.get("ip_settings", {}).get("public_ip", "N/A")

    @property
    def wan_router_ip(self) -> str:
        return self._network_data.get("lease", {}).get("dhcp", {}).get("router", "N/A")

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
        return self._network_data.get("speed", {}).get("date", "N/A")

    @property
    def connected_clients_count(self) -> int:
        return self._network_data.get("clients", {}).get("count", 0)

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
        return self._network_data.get("guest_network", {}).get("enabled", False)

    @property
    def guest_network_name(self) -> str:
        return self._network_data.get("guest_network", {}).get("name", "")

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
        return self._network_data.get("dns", {}).get("caching", False)

    @property
    def ad_block_enabled(self) -> bool:
        return (
            self._network_data.get("premium_dns", {})
            .get("ad_block_settings", {})
            .get("enabled", False)
        )

    @property
    def block_malware(self) -> bool:
        return (
            self._network_data.get("premium_dns", {})
            .get("dns_policies", {})
            .get("block_malware", False)
        )

    @property
    def thread_enabled(self) -> bool:
        return self._network_data.get("thread", {}).get("enabled", False)

    @property
    def ddns_enabled(self) -> bool:
        return self._network_data.get("ddns", {}).get("enabled", False)

    @property
    def pause_5g_enabled(self) -> bool:
        return self._network_data.get("temporary_flags", {}).get("hide_5g", {}).get("value", False)

    @property
    def premium_enabled(self) -> bool:
        status = self._network_data.get("premium_status", "")
        capable = self._network_data.get("capabilities", {}).get("premium", {}).get("capable", False)
        return capable and status in ("active", "trialing")

    @property
    def health_internet_status(self) -> str:
        return self._network_data.get("health", {}).get("internet", {}).get("status", "unknown")

    @property
    def health_eero_network_status(self) -> str:
        return self._network_data.get("health", {}).get("eero_network", {}).get("status", "unknown")

    @property
    def isp(self) -> str:
        return self._network_data.get("geo_ip", {}).get("isp", "N/A")

    @property
    def city(self) -> str:
        return self._network_data.get("geo_ip", {}).get("city", "")

    @property
    def thread_url(self) -> str:
        return self._network_data.get("resources", {}).get("thread", "")

    @property
    def reboot_url(self) -> str:
        return self._network_data.get("resources", {}).get("reboot", "")

    @property
    def settings_url(self) -> str:
        return self._network_data.get("resources", {}).get("settings", "")

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

        networks = account.get("networks", {}).get("data", [])
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

        speed = network_data.get("speed", {})
        down = speed.get("down", {})
        up = speed.get("up", {})
        self._speed_down = down.get("value")
        self._speed_down_units = down.get("units", "Mbps")
        self._speed_up = up.get("value")
        self._speed_up_units = up.get("units", "Mbps")

        self._eeros = network_data.get("eeros", {}).get("data", [])

        devices_url = network_data.get("resources", {}).get("devices", "")
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
            self.push_update()
        except Exception as err:
            _LOG.warning("[%s] Poll failed: %s", self.log_id, err)
            self._is_connected = False
            self.events.emit(DeviceEvents.DISCONNECTED, self.identifier)

    async def disconnect(self) -> None:
        _LOG.info("[%s] Disconnecting", self.log_id)
        await super().disconnect()
        if self._client:
            await self._client.close()
            self._client = None
        self._is_connected = False
        self.events.emit(DeviceEvents.DISCONNECTED, self.identifier)
