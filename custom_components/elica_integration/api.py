"""Elica integration API Client."""

from __future__ import annotations

import socket
from typing import Any

import aiohttp
import async_timeout


class ElicaIntegrationApiClientError(Exception):
    """Exception to indicate a general API error."""


class ElicaIntegrationApiClientCommunicationError(
    ElicaIntegrationApiClientError,
):
    """Exception to indicate a communication error."""


class ElicaIntegrationApiClientAuthenticationError(
    ElicaIntegrationApiClientError,
):
    """Exception to indicate an authentication error."""


def _verify_response_or_raise(response: aiohttp.ClientResponse) -> None:
    """Verify that the response is valid."""
    if response.status in (401, 403):
        msg = "Invalid credentials"
        raise ElicaIntegrationApiClientAuthenticationError(
            msg,
        )
    response.raise_for_status()


class ElicaIntegrationApiClient:
    """Elica integration API Client."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        access_token: str | None = None,
        username: str | None = None,
        password: str | None = None,
    ) -> None:
        """Elica integration API Client."""
        self._access_token = access_token
        self._username = username
        self._password = password
        self._session = session

    async def get_info_on_me(self) -> Any:
        """Get information about the authenticated user."""
        return await self._make_request(
            method="get",
            url="https://cloudprod.elica.com/eiot-api/v1/me",
        )

    async def get_info_on_device(self) -> Any:
        """Get information about the device."""
        return await self._make_request(
            method="get",
            url="https://cloudprod.elica.com/eiot-api/v1/devices/1YuzGG",
        )

    async def turn_on_light(self) -> Any:
        """Turn on the light."""
        return await self._set_light_level(100)

    async def turn_off_light(self) -> Any:
        """Turn on the light."""
        return await self._set_light_level(0)

    async def _set_light_level(self, value: int) -> Any:
        """Set the light level."""
        return await self._make_request(
            method="post",
            url="https://cloudprod.elica.com/eiot-api/v1/devices/1YuzGG/commands",
            data={
                "async": True,
                "capabilities": {"96": value},
                "name": "capabilities",
                "type": "Hood",
                "timeout": 30000,
            },
        )

    async def _make_request(
        self,
        method: str,
        url: str,
        data: dict | None = None,
    ) -> Any:
        """Make an authenticated request to the API."""
        headers = (
            {"Authorization": f"Bearer {self._access_token}"}
            if self._access_token
            else {}
        )
        return await self._make_request_with_headers(
            method=method,
            url=url,
            data=data,
            headers=headers,
        )

    async def _make_request_with_headers(
        self,
        method: str,
        url: str,
        data: dict | None = None,
        headers: dict | None = None,
    ) -> Any:
        """Make a request to the API."""
        try:
            async with async_timeout.timeout(10):
                response = await self._session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=data,
                )
                _verify_response_or_raise(response)
                return await response.json()

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
