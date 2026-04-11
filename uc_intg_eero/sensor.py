"""
eero WiFi sensor entities.

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging

from ucapi.sensor import Attributes, DeviceClasses, Sensor, States

from uc_intg_eero.config import EeroDeviceConfig
from uc_intg_eero.device import EeroDevice

_LOG = logging.getLogger(__name__)


class EeroSensor(Sensor):
    """Base eero sensor entity."""

    def __init__(
        self,
        config: EeroDeviceConfig,
        device: EeroDevice,
        sensor_id: str,
        sensor_name: str,
    ):
        self._device = device
        self._config = config
        self._sensor_id = sensor_id

        entity_id = f"sensor.{config.identifier}.{sensor_id}"

        super().__init__(
            entity_id,
            f"{config.name} - {sensor_name}",
            [],
            {
                Attributes.STATE: States.ON,
                Attributes.VALUE: "N/A",
            },
            device_class=DeviceClasses.CUSTOM,
        )


class NetworkStatusSensor(EeroSensor):
    def __init__(self, config: EeroDeviceConfig, device: EeroDevice):
        super().__init__(config, device, "network_status", "Network Status")


class GatewayIpSensor(EeroSensor):
    def __init__(self, config: EeroDeviceConfig, device: EeroDevice):
        super().__init__(config, device, "gateway_ip", "Gateway IP")


class PublicIpSensor(EeroSensor):
    def __init__(self, config: EeroDeviceConfig, device: EeroDevice):
        super().__init__(config, device, "public_ip", "Public IP")


class WanRouterIpSensor(EeroSensor):
    def __init__(self, config: EeroDeviceConfig, device: EeroDevice):
        super().__init__(config, device, "wan_router_ip", "WAN Router IP")


class SpeedDownSensor(EeroSensor):
    def __init__(self, config: EeroDeviceConfig, device: EeroDevice):
        super().__init__(config, device, "speed_down", "Download Speed")


class SpeedUpSensor(EeroSensor):
    def __init__(self, config: EeroDeviceConfig, device: EeroDevice):
        super().__init__(config, device, "speed_up", "Upload Speed")


class ConnectedClientsSensor(EeroSensor):
    def __init__(self, config: EeroDeviceConfig, device: EeroDevice):
        super().__init__(config, device, "connected_clients", "Connected Clients")


class EeroCountSensor(EeroSensor):
    def __init__(self, config: EeroDeviceConfig, device: EeroDevice):
        super().__init__(config, device, "eero_count", "Eero Nodes")


class IspSensor(EeroSensor):
    def __init__(self, config: EeroDeviceConfig, device: EeroDevice):
        super().__init__(config, device, "isp", "ISP")


class SpeedDateSensor(EeroSensor):
    def __init__(self, config: EeroDeviceConfig, device: EeroDevice):
        super().__init__(config, device, "speed_date", "Last Speed Test")


class EeroNodeSensor(Sensor):
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

        entity_id = f"sensor.{config.identifier}.eero_{eero_id}"

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
