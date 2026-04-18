"""Elica integration API Client."""

from __future__ import annotations

import socket
from typing import Any

import aiohttp
import async_timeout

from custom_components.elica.const import INITIAL_AUTH_TOKEN
from custom_components.elica.data import MAX_FAN_SPEED, DeviceInfo


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


_ID_KEY = "id"
_NAME_KEY = "name"
_TYPE_KEY = "type"
_DATA_MODEL_KEY = "dataModel"
_LIGHT_LEVEL_KEY = "96"
_UNBOOSTED_SPEED_KEY = "110"
_BOOST_KEY = "64"
_BOOST_OFF_VALUE = 1
_BOOST_ON_VALUE = 5


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

    async def get_info_on_devices(self) -> dict[str, DeviceInfo]:
        """Get information about the devices."""
        response = await self._make_request(
            method="get",
            url="https://cloudprod.elica.com/eiot-api/v1/devices",
        )
        info = {
            d[_ID_KEY]: DeviceInfo(
                id=d[_ID_KEY],
                name=d[_NAME_KEY],
                type=d[_TYPE_KEY],
                is_light_on=_is_light_on(_get_data_model(d)),
                fan_speed=_get_fan_speed(_get_data_model(d)),
            )
            for d in response
        }
        print(f"Got info: {info}")
        return info

    async def set_fan_speed(self, device_id: str, device_type: str, speed: int) -> Any:
        """Set the fan level."""
        is_boosted = _get_is_fan_boosted(speed)
        return await self._make_request(
            method="post",
            url=f"https://cloudprod.elica.com/eiot-api/v1/devices/{device_id}/commands",
            json={
                "async": True,
                "capabilities": {_BOOST_KEY: _BOOST_ON_VALUE}
                if is_boosted
                else {
                    _UNBOOSTED_SPEED_KEY: _get_unboosted_fan_speed(speed),
                    _BOOST_KEY: _BOOST_OFF_VALUE,
                },
                "name": "capabilities",
                _TYPE_KEY: device_type,
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
                "capabilities": {_LIGHT_LEVEL_KEY: value},
                "name": "capabilities",
                _TYPE_KEY: device_type,
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
        print(f"Making request. Method: {method}, URL: {url}, JSON: {json}")
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


def _get_data_model(device_json: dict) -> dict:
    """Get the data model from the response."""
    return device_json.get(_DATA_MODEL_KEY, {})


def _is_light_on(data_model: dict) -> bool:
    """Get whether the light is on from the data model."""
    return data_model.get(_LIGHT_LEVEL_KEY, 0) > 0


def _get_fan_speed(data_model: dict) -> int:
    """Get the fan speed from the data model."""
    is_boosted = data_model.get(_BOOST_KEY, 0) > _BOOST_OFF_VALUE
    if is_boosted:
        return MAX_FAN_SPEED
    return data_model.get(_UNBOOSTED_SPEED_KEY, 0)


def _get_is_fan_boosted(fan_speed: int) -> bool:
    """Get whether the fan is boosted from the fan speed."""
    return fan_speed == MAX_FAN_SPEED


def _get_unboosted_fan_speed(fan_speed: int) -> int:
    """Get the unboosted fan speed from the fan speed."""
    return min(fan_speed, MAX_FAN_SPEED - 1)
