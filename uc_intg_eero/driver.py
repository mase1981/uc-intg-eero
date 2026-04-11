"""
eero WiFi integration driver for Unfolded Circle Remote.

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging

from ucapi_framework import BaseIntegrationDriver

from uc_intg_eero.button import create_buttons
from uc_intg_eero.config import EeroDeviceConfig
from uc_intg_eero.device import EeroDevice
from uc_intg_eero.sensor import create_sensors
from uc_intg_eero.switch import create_network_switches, create_eero_led_switches

_LOG = logging.getLogger(__name__)


def _create_all_entities(config: EeroDeviceConfig, device: EeroDevice) -> list:
    """Create all entities for the eero network."""
    entities = []
    entities.extend(create_sensors(config, device))
    entities.extend(create_network_switches(config, device))
    entities.extend(create_eero_led_switches(config, device))
    entities.extend(create_buttons(config, device))
    return entities


class EeroDriver(BaseIntegrationDriver[EeroDevice, EeroDeviceConfig]):
    """eero WiFi integration driver."""

    def __init__(self):
        super().__init__(
            device_class=EeroDevice,
            entity_classes=[_create_all_entities],
            require_connection_before_registry=True,
        )
