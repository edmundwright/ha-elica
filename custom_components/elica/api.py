"""Elica integration API Client."""

from __future__ import annotations

from re import U
import socket
from typing import Any, Callable, NamedTuple

import aiohttp
import async_timeout

from custom_components.elica.const import INITIAL_AUTH_TOKEN


class ElicaIntegrationApiClientError(Exception):
    """Exception to indicate a general API error."""


class ElicaIntegrationApiClientCommunicationError(
    ElicaIntegrationApiClientError,
):
    """Exception to indicate a communication error."""


class ElicaIntegrationApiClientUnexpectedResponseError(
    ElicaIntegrationApiClientError,
):
    """Exception to indicate an unexpected response."""


class ElicaIntegrationApiClientForbiddenError(
    ElicaIntegrationApiClientError,
):
    """Exception to indicate server returned 403 (forbidden)."""


class ElicaIntegrationApiClientAuthenticationError(
    ElicaIntegrationApiClientError,
):
    """Exception to indicate an authentication error."""


class ElicaIntegrationApiClientBadRequestError(
    ElicaIntegrationApiClientError,
):
    """Exception to indicate server returned 400."""


class ElicaIntegrationApiClient:
    """Elica integration API Client."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        username: str,
        password: str,
    ) -> None:
        """Elica integration API Client."""
        self._session = session
        self._username = username
        self._password = password
        self._access_token: str | None = None

    async def get_user_id(self) -> str:
        """Get user ID for the authenticated user."""
        response = await self._make_request(
            method="get",
            url="https://cloudprod.elica.com/eiot-api/v1/me",
        )
        user_id = response.get("id", None)
        if not user_id:
            msg = "User ID empty or absent."
            raise ElicaIntegrationApiClientUnexpectedResponseError(msg)
        return user_id

    async def get_info_on_devices(self) -> Any:
        """Get information about the devices."""
        return await self._make_request(
            method="get",
            url="https://cloudprod.elica.com/eiot-api/v1/devices",
        )

    async def set_fan_level(self, device_id: str, device_type: str, level: int) -> Any:
        """Set the fan level."""
        return await self._make_request(
            method="post",
            url=f"https://cloudprod.elica.com/eiot-api/v1/devices/{device_id}/commands",
            json={
                "async": True,
                "capabilities": {"110": level},
                "name": "capabilities",
                "type": device_type,
                "timeout": 30000,
            },
        )

    async def turn_on_light(self, device_id: str, device_type: str) -> Any:
        """Turn on the light."""
        return await self._set_light_level(device_id, device_type, 100)

    async def turn_off_light(self, device_id: str, device_type: str) -> Any:
        """Turn off the light."""
        return await self._set_light_level(device_id, device_type, 0)

    async def _set_light_level(
        self, device_id: str, device_type: str, value: int
    ) -> Any:
        """Set the light level."""
        return await self._make_request(
            method="post",
            url=f"https://cloudprod.elica.com/eiot-api/v1/devices/{device_id}/commands",
            json={
                "async": True,
                "capabilities": {"96": value},
                "name": "capabilities",
                "type": device_type,
                "timeout": 30000,
            },
        )

    async def _make_request(
        self,
        method: str,
        url: str,
        json: dict | None = None,
    ) -> Any:
        if not self._access_token:
            await self._update_access_token()
        print("Makring request.")
        print("Method:", method)
        print("URL:", url)
        print("JSON:", json)
        print("Headers:", self._get_auth_headers())
        """Make an authenticated request to the API."""
        try:
            return await self._make_basic_request(
                method=method,
                url=url,
                json=json,
                headers=self._get_auth_headers(),
            )
        except ElicaIntegrationApiClientAuthenticationError:
            # Auth error. Get a new access token and try once more.
            await self._update_access_token()
            return await self._make_basic_request(
                method=method,
                url=url,
                json=json,
                headers=self._get_auth_headers(),
            )

    def _get_auth_headers(self) -> dict:
        """Get the authentication headers."""
        return {"Authorization": f"Bearer {self._access_token}"}

    async def _update_access_token(self) -> None:
        """Update access token."""
        response: Any
        try:
            response = await self._make_basic_request(
                method="post",
                url="https://cloudprod.elica.com/eiot-api/v1/oauth/token",
                data={
                    "scope": "default",
                    "grant_type": "password",
                    "username": self._username,
                    "password": self._password,
                },
                headers={"Authorization": f"Basic {INITIAL_AUTH_TOKEN}"},
            )
        except ElicaIntegrationApiClientAuthenticationError as error:
            msg = "Initial auth token rejected. May have changed?"
            raise ElicaIntegrationApiClientError(msg) from error
        except ElicaIntegrationApiClientBadRequestError as error:
            msg = "Server threw 400 - in this case suggests invalid credentials."
            raise ElicaIntegrationApiClientAuthenticationError(msg) from error

        access_token = response.get("access_token", None)
        if not access_token:
            msg = "Access token empty or absent."
            raise ElicaIntegrationApiClientUnexpectedResponseError(msg)
        self._access_token = access_token

    async def _make_basic_request(
        self,
        method: str,
        url: str,
        data: dict | None = None,
        json: dict | None = None,
        headers: dict | None = None,
    ) -> Any:
        """Make a request to the API."""
        try:
            async with async_timeout.timeout(10):
                response = await self._session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    data=data,
                    json=json,
                )
                print("Response status:", response.status)
                print("Response JSON:", await response.json())
                _verify_response_or_raise(response)
                return await response.json()

        except ElicaIntegrationApiClientError:
            raise
        except TimeoutError as exception:
            msg = f"Timeout error fetching information - {exception}"
            raise ElicaIntegrationApiClientCommunicationError(
                msg,
            ) from exception
        except (aiohttp.ClientError, socket.gaierror) as exception:
            msg = f"Error fetching information - {exception}"
            raise ElicaIntegrationApiClientCommunicationError(
                msg,
            ) from exception
        except Exception as exception:  # pylint: disable=broad-except
            msg = f"Something really wrong happened! - {exception}"
            raise ElicaIntegrationApiClientError(
                msg,
            ) from exception


def _verify_response_or_raise(response: aiohttp.ClientResponse) -> None:
    """Verify that the response is valid."""
    if response.status == 400:
        msg = "Bad request."
        raise ElicaIntegrationApiClientBadRequestError(
            msg,
        )
    if response.status == 401:
        msg = "Invalid credentials"
        raise ElicaIntegrationApiClientAuthenticationError(
            msg,
        )
    if response.status == 403:
        msg = "Forbidden"
        raise ElicaIntegrationApiClientForbiddenError(
            msg,
        )

    response.raise_for_status()
