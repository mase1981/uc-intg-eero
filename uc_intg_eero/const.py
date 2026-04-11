"""
eero WiFi integration constants.

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

API_ENDPOINT = "https://api-user.e2ro.com"
URL_ACCOUNT = "/2.2/account"

POLL_INTERVAL = 120

NETWORK_FEATURES = [
    "ad_block",
    "band_steering",
    "dns_caching",
    "guest_network",
    "ipv6",
    "sqm",
    "upnp",
    "wpa3",
    "block_malware",
    "thread",
    "ddns",
    "pause_5g",
]
