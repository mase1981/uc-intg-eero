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
from uc_intg_eero.remote import create_remote
from uc_intg_eero.sensor import create_sensors
from uc_intg_eero.switch import create_network_switches, create_eero_led_switches

_LOG = logging.getLogger(__name__)


class EeroDriver(BaseIntegrationDriver[EeroDevice, EeroDeviceConfig]):
    """eero WiFi integration driver."""

    def __init__(self):
        super().__init__(
            device_class=EeroDevice,
            entity_classes=[
                lambda cfg, dev: create_sensors(cfg, dev),
                lambda cfg, dev: create_network_switches(cfg, dev),
                lambda cfg, dev: create_eero_led_switches(cfg, dev),
                lambda cfg, dev: create_buttons(cfg, dev),
                lambda cfg, dev: create_remote(cfg, dev),
            ],
        )
