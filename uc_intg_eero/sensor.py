"""
eero WiFi sensor entities.

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging

from ucapi.sensor import Attributes, DeviceClasses, States

from ucapi_framework import SensorEntity, SensorAttributes, create_entity_id

from uc_intg_eero.config import EeroDeviceConfig
from uc_intg_eero.device import EeroDevice

_LOG = logging.getLogger(__name__)


class EeroSensor(SensorEntity):
    """Base eero sensor entity."""

    def __init__(
        self,
        config: EeroDeviceConfig,
        device: EeroDevice,
        sensor_id: str,
        sensor_name: str,
        unit: str = "",
    ):
        self._device = device
        self._config = config
        self._sensor_id = sensor_id

        entity_id = create_entity_id("sensor", config.identifier, sensor_id)

        attrs = {
            Attributes.STATE: States.ON,
            Attributes.VALUE: "N/A",
        }
        if unit:
            attrs[Attributes.UNIT] = unit

        super().__init__(
            entity_id,
            f"{config.name} - {sensor_name}",
            [],
            attrs,
            device_class=DeviceClasses.CUSTOM,
        )

        self.subscribe_to_device(device)

    async def sync_state(self) -> None:
        if not hasattr(self, "_api"):
            return
        value = self._get_value()
        self.update(SensorAttributes(
            STATE=States.ON if self._device.is_connected else States.UNAVAILABLE,
            VALUE=str(value) if value is not None else "N/A",
        ))

    def _get_value(self) -> str | int | float | None:
        raise NotImplementedError


class NetworkStatusSensor(EeroSensor):
    def __init__(self, config: EeroDeviceConfig, device: EeroDevice):
        super().__init__(config, device, "network_status", "Network Status")

    def _get_value(self) -> str:
        status = self._device.network_status
        internet = self._device.health_internet_status
        return f"{status} | Internet: {internet}"


class GatewayIpSensor(EeroSensor):
    def __init__(self, config: EeroDeviceConfig, device: EeroDevice):
        super().__init__(config, device, "gateway_ip", "Gateway IP")

    def _get_value(self) -> str:
        return self._device.gateway_ip


class PublicIpSensor(EeroSensor):
    def __init__(self, config: EeroDeviceConfig, device: EeroDevice):
        super().__init__(config, device, "public_ip", "Public IP")

    def _get_value(self) -> str:
        return self._device.public_ip


class WanRouterIpSensor(EeroSensor):
    def __init__(self, config: EeroDeviceConfig, device: EeroDevice):
        super().__init__(config, device, "wan_router_ip", "WAN Router IP")

    def _get_value(self) -> str:
        return self._device.wan_router_ip


class SpeedDownSensor(EeroSensor):
    def __init__(self, config: EeroDeviceConfig, device: EeroDevice):
        super().__init__(config, device, "speed_down", "Download Speed")

    def _get_value(self) -> str:
        return self._device.speed_down


class SpeedUpSensor(EeroSensor):
    def __init__(self, config: EeroDeviceConfig, device: EeroDevice):
        super().__init__(config, device, "speed_up", "Upload Speed")

    def _get_value(self) -> str:
        return self._device.speed_up


class ConnectedClientsSensor(EeroSensor):
    def __init__(self, config: EeroDeviceConfig, device: EeroDevice):
        super().__init__(config, device, "connected_clients", "Connected Clients")

    def _get_value(self) -> str:
        return str(self._device.connected_clients_count)


class EeroCountSensor(EeroSensor):
    def __init__(self, config: EeroDeviceConfig, device: EeroDevice):
        super().__init__(config, device, "eero_count", "Eero Nodes")

    def _get_value(self) -> str:
        return str(self._device.eero_count)


class IspSensor(EeroSensor):
    def __init__(self, config: EeroDeviceConfig, device: EeroDevice):
        super().__init__(config, device, "isp", "ISP")

    def _get_value(self) -> str:
        return self._device.isp


class SpeedDateSensor(EeroSensor):
    def __init__(self, config: EeroDeviceConfig, device: EeroDevice):
        super().__init__(config, device, "speed_date", "Last Speed Test")

    def _get_value(self) -> str:
        return self._device.speed_date


class EeroNodeSensor(SensorEntity):
    """Sensor for an individual eero node."""

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
        self._index = index

        location = eero_data.get("location", f"Eero {index + 1}")
        model = eero_data.get("model", "eero")
        eero_id = self._eero_url.replace("/2.2/eeros/", "") if self._eero_url else f"eero_{index}"

        entity_id = create_entity_id("sensor", config.identifier, f"eero_{eero_id}")

        super().__init__(
            entity_id,
            f"{config.name} - {location} ({model})",
            [],
            {
                Attributes.STATE: States.ON,
                Attributes.VALUE: "N/A",
            },
            device_class=DeviceClasses.CUSTOM,
        )

        self.subscribe_to_device(device)

    async def sync_state(self) -> None:
        if not hasattr(self, "_api"):
            return
        eero_data = self._find_eero()
        if eero_data:
            status = eero_data.get("status", "unknown")
            clients = eero_data.get("connected_clients_count", 0)
            os_ver = eero_data.get("os_version", "?")
            value = f"{status} | Clients: {clients} | OS: {os_ver}"
        else:
            value = "N/A"

        self.update(SensorAttributes(
            STATE=States.ON if self._device.is_connected else States.UNAVAILABLE,
            VALUE=value,
        ))

    def _find_eero(self) -> dict | None:
        for eero in self._device.eeros:
            if eero.get("url") == self._eero_url:
                return eero
        if self._index < len(self._device.eeros):
            return self._device.eeros[self._index]
        return None


def create_sensors(config: EeroDeviceConfig, device: EeroDevice) -> list:
    """Create all sensor entities for the eero network."""
    sensors = [
        NetworkStatusSensor(config, device),
        GatewayIpSensor(config, device),
        PublicIpSensor(config, device),
        WanRouterIpSensor(config, device),
        SpeedDownSensor(config, device),
        SpeedUpSensor(config, device),
        ConnectedClientsSensor(config, device),
        EeroCountSensor(config, device),
        IspSensor(config, device),
        SpeedDateSensor(config, device),
    ]

    for i, eero_data in enumerate(device.eeros):
        sensors.append(EeroNodeSensor(config, device, eero_data, i))

    return sensors
