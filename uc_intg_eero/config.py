"""
eero WiFi integration configuration.

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

from dataclasses import dataclass, field


@dataclass
class EeroDeviceConfig:
    identifier: str
    name: str
    user_token: str
    network_id: str = ""
    network_name: str = ""
