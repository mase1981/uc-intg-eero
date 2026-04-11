"""
eero cloud API client using aiohttp.

Ported from the Home Assistant eero integration (schmittx/home-assistant-eero).
Converted from synchronous requests to async aiohttp.

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging
import ssl
from typing import Any

import aiohttp
import certifi

from uc_intg_eero.const import API_ENDPOINT, URL_ACCOUNT

_LOG = logging.getLogger(__name__)


class EeroApiError(Exception):
    def __init__(self, code: int | None = None, error: str | None = None, message: str | None = None):
        super().__init__(message or error or f"API error {code}")
        self.code = code
        self.error = error
        self.message = message


class EeroClient:
    """Async client for the eero cloud API."""

    def __init__(self, user_token: str | None = None):
        self._user_token = user_token
        self._session: aiohttp.ClientSession | None = None

    @property
    def user_token(self) -> str | None:
        return self._user_token

    @user_token.setter
    def user_token(self, value: str | None):
        self._user_token = value

    async def _ensure_session(self):
        if self._session is None or self._session.closed:
            ssl_ctx = ssl.create_default_context(cafile=certifi.where())
            connector = aiohttp.TCPConnector(ssl=ssl_ctx)
            self._session = aiohttp.ClientSession(connector=connector)

    def _cookies(self) -> dict:
        if self._user_token:
            return {"s": self._user_token}
        return {}

    async def _request(self, method: str, url: str, **kwargs) -> dict[str, Any]:
        await self._ensure_session()
        full_url = f"{API_ENDPOINT}{url}"
        _LOG.debug("API %s %s", method, url)

        try:
            async with self._session.request(
                method, full_url, cookies=self._cookies(), **kwargs
            ) as resp:
                text = await resp.json(content_type=None)

                if resp.status == 401:
                    meta = text.get("meta", {})
                    error = meta.get("error", "")
                    if error in ("error.session.invalid", "error.session.refresh"):
                        _LOG.debug("Session expired, refreshing token")
                        await self._refresh_token()
                        async with self._session.request(
                            method, full_url, cookies=self._cookies(), **kwargs
                        ) as retry_resp:
                            text = await retry_resp.json(content_type=None)
                            if not retry_resp.ok:
                                raise EeroApiError(
                                    code=retry_resp.status,
                                    error=text.get("meta", {}).get("error"),
                                    message=f"Request failed after token refresh: {url}",
                                )
                    else:
                        raise EeroApiError(code=401, error=error, message="Authentication failed")

                elif not resp.ok:
                    meta = text.get("meta", {})
                    raise EeroApiError(
                        code=resp.status,
                        error=meta.get("error"),
                        message=f"Request failed: {url} ({resp.status})",
                    )

                return text.get("data", text)

        except aiohttp.ClientError as err:
            raise EeroApiError(message=f"Connection error: {err}") from err

    async def _refresh_token(self):
        await self._ensure_session()
        url = f"{API_ENDPOINT}/2.2/login/refresh"
        async with self._session.post(url, cookies=self._cookies()) as resp:
            text = await resp.json(content_type=None)
            if resp.ok:
                self._user_token = text.get("data", {}).get("user_token", self._user_token)
                _LOG.info("Token refreshed successfully")
            else:
                raise EeroApiError(code=resp.status, message="Token refresh failed")

    async def login(self, login_id: str) -> dict[str, Any]:
        result = await self._request("POST", "/2.2/login", json={"login": login_id})
        self._user_token = result.get("user_token")
        return result

    async def login_verify(self, code: str) -> dict[str, Any]:
        return await self._request("POST", "/2.2/login/verify", json={"code": code})

    async def get_account(self) -> dict[str, Any]:
        return await self._request("GET", URL_ACCOUNT)

    async def get_network(self, network_url: str) -> dict[str, Any]:
        return await self._request("GET", network_url)

    async def get_network_devices(self, resources_url: str) -> list[dict]:
        return await self._request("GET", resources_url)

    async def get_eeros(self, network_data: dict) -> list[dict]:
        return network_data.get("eeros", {}).get("data", [])

    async def set_network_setting(self, network_url: str, setting: str, value: Any) -> None:
        settings_url = f"{network_url}/settings"
        await self._request("PUT", settings_url, json={setting: value})

    async def set_guest_network(self, network_id: str, enabled: bool) -> None:
        await self._request("PUT", f"/2.2/networks/{network_id}/guestnetwork", json={"enabled": enabled})

    async def set_dns_caching(self, network_id: str, caching: bool) -> None:
        await self._request("PUT", f"/2.2/networks/{network_id}/dns", json={"caching": caching})

    async def set_ad_block(self, network_url: str, enabled: bool) -> None:
        await self._request("POST", f"{network_url}/dns_policies/adblock", json={"enable": enabled})

    async def set_block_malware(self, network_url: str, enabled: bool) -> None:
        await self._request("POST", f"{network_url}/dns_policies/network", json={"block_malware": enabled})

    async def set_ddns(self, network_id: str, enabled: bool) -> None:
        target = "enable" if enabled else "disable"
        await self._request("PUT", f"/2.2/networks/{network_id}/ddns/{target}")

    async def set_thread(self, thread_url: str, enabled: bool) -> None:
        await self._request("PUT", f"{thread_url}/enable", json={"enabled": enabled})

    async def set_pause_5g(self, network_url: str, enabled: bool) -> None:
        url = f"{network_url}/temporary_flags/hide_5g"
        if enabled:
            await self._request("PUT", url, json={"value": True})
        else:
            await self._request("DELETE", url)

    async def set_eero_led(self, led_url: str, on: bool) -> None:
        await self._request("PUT", led_url, json={"led_on": on})

    async def reboot_network(self, reboot_url: str) -> None:
        await self._request("POST", reboot_url)

    async def reboot_eero(self, reboot_url: str) -> None:
        await self._request("POST", reboot_url)

    async def run_speed_test(self, network_url: str) -> None:
        await self._request("POST", f"{network_url}/speedtest")

    async def set_client_paused(self, network_id: str, mac: str, paused: bool) -> None:
        await self._request("PUT", f"/2.3/networks/{network_id}/devices/{mac}", json={"paused": paused})

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    async def test_connection(self) -> bool:
        try:
            account = await self.get_account()
            return bool(account)
        except Exception:
            return False
