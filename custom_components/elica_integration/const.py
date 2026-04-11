"""Constants for elica_integration."""

from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

DOMAIN = "elica_integration"
ATTRIBUTION = "Data provided by https://www.elica.com"
CONF_REFRESH_TOKEN = "refresh_token"  # noqa: S105
# Initial basic auth token (shared by all instances of Android app - not a secret
# credential). Base64 encoding of "eiot-app:VqwG1KTB77UeROu".
INITIAL_AUTH_TOKEN = "ZWlvdC1hcHA6VnF3RzFLVEI3N1VlUk91"  # noqa: S105
