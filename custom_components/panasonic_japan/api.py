"""API client for Panasonic Japan Kitchen Appliances."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

import requests

from .const import (
    API_BASE_URL,
    API_KEY,
    AUTH0_AUDIENCE,
    AUTH0_CLIENT_ID,
    AUTH0_DOMAIN,
    AUTH0_TOKEN_URL,
    KAPF_API_BASE_URL,
    YEN_PER_KWH,
)

_LOGGER = logging.getLogger(__name__)


class PanasonicAPIError(Exception):
    """Base exception for Panasonic API errors."""


class PanasonicAPI:
    """API client for Panasonic Japan Kitchen Appliances."""

    def __init__(
        self, access_token: str | None = None, refresh_token: str | None = None
    ) -> None:
        """Initialize the API client."""
        self._access_token = access_token
        self._refresh_token = refresh_token
        self._session = requests.Session()

    def _get_reizo_date(self) -> str:
        """Get current date in Japan timezone for X-Reizo-Date header."""
        # Use Asia/Tokyo timezone
        try:
            from zoneinfo import ZoneInfo

            tz = ZoneInfo("Asia/Tokyo")
        except ImportError:
            # Fallback for Python < 3.9
            from datetime import timezone
            import pytz

            tz = pytz.timezone("Asia/Tokyo")

        return datetime.now(tz).strftime("%Y-%m-%dT%H:%M:%S")

    def _get_headers(self, include_reizo_date: bool = True) -> dict[str, str]:
        """Get default headers for API requests."""
        headers = {
            "Content-Type": "application/json; charset=UTF-8",
            "Accept": "application/json",
        }

        if include_reizo_date:
            headers["X-Reizo-Date"] = self._get_reizo_date()

        if self._access_token:
            headers["Authorization"] = f"Bearer {self._access_token}"

        return headers

    def _url_encode_appliance_id(self, appliance_id: str) -> str:
        """URL encode appliance_id (handles + and = characters)."""
        from urllib.parse import quote

        return quote(appliance_id, safe="")

    def _make_request_with_retry(
        self, method: str, url: str, **kwargs: Any
    ) -> requests.Response:
        """Make an API request with automatic token refresh on 401/403 errors."""
        response = self._session.request(method, url, **kwargs)
        
        # If we get 401/403, try refreshing the token and retry once
        if response.status_code in (401, 403):
            _LOGGER.warning(
                "Received %d error, attempting to refresh access token",
                response.status_code,
            )
            try:
                self.refresh_access_token()
                # Retry the request with the new token
                # Update Authorization header
                if "headers" in kwargs:
                    kwargs["headers"]["Authorization"] = f"Bearer {self._access_token}"
                else:
                    kwargs["headers"] = {"Authorization": f"Bearer {self._access_token}"}
                
                response = self._session.request(method, url, **kwargs)
            except Exception as err:
                _LOGGER.error("Failed to refresh token and retry: %s", err)
                raise PanasonicAPIError(
                    f"Authentication failed: {response.status_code} {response.text}"
                ) from err
        
        return response

    def get_user_info(self) -> dict[str, Any]:
        """Get user information and list of appliances."""
        url = f"{KAPF_API_BASE_URL}/user/info"
        headers = self._get_headers(include_reizo_date=False)
        headers["X-API-Key"] = API_KEY
        headers["User-Agent"] = "KitchenPocketA/5.1.0"

        response = self._make_request_with_retry("GET", url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()

    def get_device_status(self, appliance_id: str) -> dict[str, Any]:
        """Get device status."""
        appliance_id_encoded = self._url_encode_appliance_id(appliance_id)
        url = f"{API_BASE_URL}/devices/{appliance_id_encoded}/status"
        params = {"usages": 1}

        response = self._make_request_with_retry(
            "GET", url, headers=self._get_headers(), params=params, timeout=30
        )
        response.raise_for_status()
        return response.json()

    def get_electricity_reduction(self, appliance_id: str) -> dict[str, Any]:
        """Get electricity cost reduction data."""
        appliance_id_encoded = self._url_encode_appliance_id(appliance_id)
        url = f"{API_BASE_URL}/devices/{appliance_id_encoded}/reduction"

        response = self._make_request_with_retry(
            "GET", url, headers=self._get_headers(), timeout=30
        )
        response.raise_for_status()
        return response.json()

    def calculate_electricity_usage(self, cost_reduction: int) -> float:
        """Calculate electricity usage in kWh/month."""
        # Formula: electricity_usage (kWh/month) = (750円 - cost_reduction) / 31円
        return (750 - cost_reduction) / YEN_PER_KWH

    def get_device_functions(self, appliance_id: str) -> dict[str, Any]:
        """Get device functions list."""
        appliance_id_encoded = self._url_encode_appliance_id(appliance_id)
        url = f"{API_BASE_URL}/products/{appliance_id_encoded}/functions"

        response = self._make_request_with_retry(
            "GET", url, headers=self._get_headers(), timeout=30
        )
        response.raise_for_status()
        return response.json()

    def refresh_access_token(self) -> dict[str, Any] | None:
        """Refresh the access token using refresh token."""
        if not self._refresh_token:
            raise PanasonicAPIError("No refresh token available")

        data = {
            "grant_type": "refresh_token",
            "client_id": AUTH0_CLIENT_ID,
            "refresh_token": self._refresh_token,
        }

        try:
            response = self._session.post(AUTH0_TOKEN_URL, data=data, timeout=30)
            response.raise_for_status()
            token_data = response.json()

            # Update tokens
            self._access_token = token_data.get("access_token")
            if "refresh_token" in token_data:
                self._refresh_token = token_data.get("refresh_token")

            return token_data
        except Exception as err:
            _LOGGER.exception("Error refreshing access token: %s", err)
            raise PanasonicAPIError(f"Failed to refresh token: {err}") from err

    @property
    def access_token(self) -> str | None:
        """Get current access token."""
        return self._access_token

    @property
    def refresh_token(self) -> str | None:
        """Get current refresh token."""
        return self._refresh_token
