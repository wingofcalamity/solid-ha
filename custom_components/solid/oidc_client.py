"""OIDC Client for SOLID Home Assistant integration, version 2."""

import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

LOGGER = logging.getLogger(__name__)


class SolidOIDCClient:
    """Handle OIDC client operations for the SOLID integration."""

    def __init__(
        self, hass: HomeAssistant, oidc_url, pod_url, client_token, client_secret
    ) -> None:
        """Initialize the OIDC client."""
        LOGGER.debug(
            "Initializing SolidOIDCClient with OIDC URL: %s, POD URL: %s",
            oidc_url,
            pod_url,
        )
        self.hass = hass
        self.client_token = client_token
        self.client_secret = client_secret
        self.pod_url = pod_url
        self.oidc_url = oidc_url
        self.token_endpoint = None
        self.session = async_get_clientsession(hass)

    async def _get_token_endpoint(self) -> None | str:
        """Retrieve the token endpoint from the OIDC provider."""
        if self.token_endpoint:
            return self.token_endpoint

        async with self.session.get(
            f"{self.oidc_url.rstrip('/')}/.well-known/openid-configuration"
        ) as response:
            if response.status != 200:
                LOGGER.error("Failed to retrieve OIDC configuration")
                return None
            config = await response.json()
            self.token_endpoint = config.get("token_endpoint")
            return self.token_endpoint

    async def _authenticate(self) -> None | str:
        """Authenticate with the OIDC provider."""
        token_endpoint = await self._get_token_endpoint()
        if not token_endpoint:
            LOGGER.error("Token endpoint not found")
            return None

        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_token,
            "client_secret": self.client_secret,
            "scope": "webid",
        }

        async with self.session.post(token_endpoint, data=data) as response:
            if response.status != 200:
                LOGGER.error("Authentication failed with status %s", response.status)
                return None
            token_data = await response.json()
            return token_data.get("access_token")

    async def get(self, resource) -> str | None:
        """Retrieve a resource from the SOLID pod."""
        token = await self._authenticate()
        if not token:
            LOGGER.error("Failed to authenticate")
            return None
        headers = {"Authorization": f"Bearer {token}"}
        async with self.session.get(
            f"{self.pod_url.rstrip('/')}/{resource}", headers=headers
        ) as response:
            if response.status != 200:
                LOGGER.error("Failed to retrieve resource %s", resource)
                return None
            return await response.text()

    async def post(self, resource, data) -> None:
        """Post data to a resource in the SOLID pod."""
        token = await self._authenticate()
        if not token:
            LOGGER.error("Failed to authenticate")
            return
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
            if isinstance(data, dict)
            else "text/plain",
        }
        async with self.session.post(
            f"{self.pod_url.rstrip('/')}/{resource}", json=data, headers=headers
        ) as response:
            if response.status != 205:
                LOGGER.error("Failed to post data to resource %s", resource)
            return

    async def put(self, resource, data) -> None:
        """Put data to a resource in the SOLID pod."""
        token = await self._authenticate()
        if not token:
            LOGGER.error("Failed to authenticate")
            return
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
            if isinstance(data, dict)
            else "text/plain",
        }
        LOGGER.debug("Putting to %s/%s", self.pod_url.rstrip("/"), resource)
        async with self.session.put(
            f"{self.pod_url.rstrip('/')}/{resource}", json=data, headers=headers
        ) as response:
            # 205 Reset Content is expected for successful PUT requests
            if response.status != 205:
                LOGGER.error("Failed to put data to resource %s", resource)
            return
