"""Elica integration API Client."""

from __future__ import annotations

import base64
import socket
from typing import Any, NamedTuple

import aiohttp
import async_timeout

from custom_components.elica_integration.const import INITIAL_AUTH_TOKEN


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


class ElicaIntegrationApiClientAuthenticationError(
    ElicaIntegrationApiClientError,
):
    """Exception to indicate an authentication error."""


class ElicaIntegrationApiClientBadRequestError(
    ElicaIntegrationApiClientError,
):
    """Exception to indicate server returned 400."""


class AuthTokens(NamedTuple):
    """Auth tokens."""

    access_token: str
    refresh_token: str


class BasicElicaIntegrationApiClient:
    """Basic Elica API integration client."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
    ) -> None:
        """Init basic Elica API integration client."""
        self._session = session

    async def get_auth_tokens(self, username: str, password: str) -> AuthTokens:
        """Get auth tokens."""
        response: Any
        try:
            response = await self._make_basic_request(
                method="post",
                url="https://cloudprod.elica.com/eiot-api/v1/oauth/token",
                data={
                    "scope": "default",
                    "grant_type": "password",
                    "username": username,
                    "password": password,
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
        refresh_token = response.get("refresh_token", None)
        if not access_token:
            msg = "Access token empty or absent."
            raise ElicaIntegrationApiClientUnexpectedResponseError(msg)
        if not refresh_token:
            msg = "Refresh token empty or absent."
            raise ElicaIntegrationApiClientUnexpectedResponseError(msg)
        return AuthTokens(access_token=access_token, refresh_token=refresh_token)

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


class ElicaIntegrationApiClient(BasicElicaIntegrationApiClient):
    """Elica integration API Client."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        auth_tokens: AuthTokens,
    ) -> None:
        """Elica integration API Client."""
        super().__init__(session)
        self._auth_tokens = auth_tokens

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
            json={
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
        json: dict | None = None,
    ) -> Any:
        """Make an authenticated request to the API."""
        return await self._make_basic_request(
            method=method,
            url=url,
            json=json,
            headers={"Authorization": f"Bearer {self._auth_tokens.access_token}"},
        )


def _verify_response_or_raise(response: aiohttp.ClientResponse) -> None:
    """Verify that the response is valid."""
    if response.status in (401, 403):
        msg = "Invalid credentials"
        raise ElicaIntegrationApiClientAuthenticationError(
            msg,
        )
    if response.status == 400:
        msg = "Bad request."
        raise ElicaIntegrationApiClientBadRequestError(
            msg,
        )
    response.raise_for_status()
