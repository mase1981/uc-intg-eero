"""
eero WiFi setup flow with multi-step authentication.

The eero API requires a 2-step auth:
1. User enters email/phone -> eero sends verification code
2. User enters verification code -> token is returned

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import asyncio
import logging
from typing import Any

from ucapi import RequestUserInput, SetupAction, SetupError
from ucapi.api_definitions import DriverSetupRequest
from ucapi_framework import BaseSetupFlow, SetupSteps

from uc_intg_eero.client import EeroClient
from uc_intg_eero.config import EeroDeviceConfig

_LOG = logging.getLogger(__name__)


class EeroSetupFlow(BaseSetupFlow[EeroDeviceConfig]):
    """eero setup flow with 2-step cloud authentication."""

    async def _handle_driver_setup_request(
        self, msg: DriverSetupRequest
    ) -> SetupAction:
        """Skip restore prompt - go directly to manual entry."""
        if msg.reconfigure:
            self._setup_step = SetupSteps.CONFIGURATION_MODE
            return await self._build_configuration_mode_screen()

        self.config.clear()
        self._pre_discovery_data = {}
        self._setup_step = SetupSteps.MANUAL_ENTRY
        return self.get_manual_entry_form()

    def get_manual_entry_form(self) -> RequestUserInput:
        return RequestUserInput(
            {"en": "eero WiFi Setup"},
            [
                {
                    "id": "info",
                    "label": {"en": "Setup Information"},
                    "field": {
                        "label": {
                            "value": {
                                "en": (
                                    "Enter your eero account email or phone number. "
                                    "eero will send a verification code to authenticate."
                                )
                            }
                        }
                    },
                },
                {
                    "id": "name",
                    "label": {"en": "Device Name"},
                    "field": {"text": {"value": "eero"}},
                },
                {
                    "id": "login",
                    "label": {"en": "Email or Phone Number"},
                    "field": {"text": {"value": ""}},
                },
            ],
        )

    async def query_device(
        self, input_values: dict[str, Any]
    ) -> RequestUserInput | EeroDeviceConfig:
        login = input_values.get("login", "").strip()
        verification_code = input_values.get("verification_code", "").strip()
        name = input_values.get("name", "eero").strip() or "eero"

        if verification_code:
            return await self._verify_code(input_values)

        if not login:
            raise ValueError("Email or phone number is required")

        _LOG.info("SETUP: Initiating login for %s", login)

        client = EeroClient()
        try:
            async with asyncio.timeout(15):
                result = await client.login(login)

            user_token = client.user_token
            _LOG.info("SETUP: Verification code sent to %s", login)

            self._pre_discovery_data["user_token"] = user_token
            self._pre_discovery_data["login"] = login
            self._pre_discovery_data["name"] = name

            await client.close()

            return RequestUserInput(
                {"en": "eero Verification"},
                [
                    {
                        "id": "info",
                        "label": {"en": "Verification"},
                        "field": {
                            "label": {
                                "value": {
                                    "en": (
                                        f"A verification code has been sent to {login}. "
                                        "Enter the code below to complete setup."
                                    )
                                }
                            }
                        },
                    },
                    {
                        "id": "verification_code",
                        "label": {"en": "Verification Code"},
                        "field": {"text": {"value": ""}},
                    },
                ],
            )

        except Exception as err:
            await client.close()
            _LOG.error("SETUP: Login failed: %s", err)
            raise ValueError(f"Login failed: {err}") from err

    async def _verify_code(self, input_values: dict[str, Any]) -> EeroDeviceConfig:
        code = input_values.get("verification_code", "").strip()
        user_token = self._pre_discovery_data.get("user_token", "")
        name = self._pre_discovery_data.get("name", "eero")

        if not code:
            raise ValueError("Verification code is required")

        _LOG.info("SETUP: Verifying code")

        client = EeroClient(user_token=user_token)
        try:
            async with asyncio.timeout(15):
                await client.login_verify(code)

            final_token = client.user_token
            account = await client.get_account()

            networks = account.get("networks", {}).get("data", [])
            if not networks:
                await client.close()
                raise ValueError("No eero networks found in this account")

            network = networks[0]
            network_url = network.get("url", "")
            network_id = network_url.replace("/2.2/networks/", "")

            network_data = await client.get_network(network_url)
            network_name = network_data.get("name", "eero Network")

            eero_count = len(network_data.get("eeros", {}).get("data", []))
            client_count = network_data.get("clients", {}).get("count", 0)

            _LOG.info("SETUP: Verified! Network: %s, Eeros: %d, Clients: %d",
                      network_name, eero_count, client_count)

            await client.close()

            account_log_id = account.get("log_id", network_id)
            identifier = f"eero_{account_log_id}"

            return EeroDeviceConfig(
                identifier=identifier,
                name=name,
                user_token=final_token,
                network_id=network_id,
                network_name=network_name,
            )

        except ValueError:
            await client.close()
            raise
        except Exception as err:
            await client.close()
            _LOG.error("SETUP: Verification failed: %s", err)
            raise ValueError(f"Verification failed: {err}") from err
