"""Config flow for Panasonic Japan integration."""
from __future__ import annotations

import base64
import hashlib
import logging
import secrets
from typing import Any
from urllib.parse import parse_qs, urlparse

import requests
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_ACCESS_TOKEN
from homeassistant.data_entry_flow import FlowResult

from .api import PanasonicAPI
from .const import (
    AUTH0_AUDIENCE,
    AUTH0_CLIENT_ID,
    AUTH0_DOMAIN,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

REDIRECT_URI = "com.panasonic.jp.kitchenpocket.auth0://auth.digital.panasonic.com/android/com.panasonic.jp.kitchenpocket/callback"
SCOPE = "openid kitchenpocket.service smartrf_prd.control eatpick.service offline_access"


def get_callback_schema(login_url: str = "") -> vol.Schema:
    """Get callback schema with login URL in description."""
    # Home Assistant doesn't support description in vol.Required directly
    # We'll show it in the step description instead
    return vol.Schema(
        {
            vol.Required("callback_url"): str,
        }
    )


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Panasonic Japan."""

    VERSION = 1

    def _generate_pkce(self) -> tuple[str, str, str, str]:
        """Generate PKCE parameters."""
        # Generate code verifier (43-128 characters, URL-safe)
        code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode(
            "utf-8"
        ).rstrip("=")

        # Generate code challenge (SHA256 hash of verifier, base64url encoded)
        code_challenge_bytes = hashlib.sha256(code_verifier.encode("utf-8")).digest()
        code_challenge = base64.urlsafe_b64encode(code_challenge_bytes).decode(
            "utf-8"
        ).rstrip("=")

        # Generate state and nonce
        state = secrets.token_urlsafe(16)
        nonce = secrets.token_urlsafe(16)

        return code_verifier, code_challenge, state, nonce

    def _generate_login_url(
        self, code_challenge: str, state: str, nonce: str
    ) -> str:
        """Generate Auth0 login URL."""
        from urllib.parse import quote

        # Auth0Client parameter (base64 encoded JSON)
        auth0_client = {
            "name": "Auth0.Android",
            "env": {"android": "31"},
            "version": "2.5.0",
        }
        import json

        auth0_client_json = json.dumps(auth0_client, separators=(",", ":"))
        auth0_client_b64 = base64.b64encode(
            auth0_client_json.encode("utf-8")
        ).decode("utf-8")
        auth0_client_encoded = quote(auth0_client_b64)

        params = {
            "scope": quote(SCOPE),
            "audience": quote(AUTH0_AUDIENCE),
            "response_type": "code",
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
            "auth0Client": auth0_client_encoded,
            "client_id": AUTH0_CLIENT_ID,
            "redirect_uri": quote(REDIRECT_URI),
            "state": state,
            "nonce": nonce,
        }

        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        return f"https://{AUTH0_DOMAIN}/authorize?{query_string}"

    def _extract_code_from_callback(self, callback_url: str) -> str | None:
        """Extract authorization code from callback URL."""
        try:
            parsed = urlparse(callback_url)
            params = parse_qs(parsed.query)
            code = params.get("code", [None])[0]
            return code
        except Exception as err:
            _LOGGER.exception("Error extracting code from callback URL: %s", err)
            return None

    def _exchange_code_for_tokens(
        self, code: str, code_verifier: str
    ) -> dict[str, Any] | None:
        """Exchange authorization code for access and refresh tokens."""
        try:
            token_url = f"https://{AUTH0_DOMAIN}/oauth/token"
            data = {
                "grant_type": "authorization_code",
                "client_id": AUTH0_CLIENT_ID,
                "code": code,
                "redirect_uri": REDIRECT_URI,
                "code_verifier": code_verifier,
            }

            response = requests.post(token_url, data=data, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as err:
            _LOGGER.exception("Error exchanging code for tokens: %s", err)
            return None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step - generate login URL and show callback form."""
        # Generate PKCE parameters
        code_verifier, code_challenge, state, nonce = self._generate_pkce()

        # Store PKCE parameters in flow context
        self.context["code_verifier"] = code_verifier
        self.context["state"] = state
        self.context["nonce"] = nonce

        # Generate login URL
        login_url = self._generate_login_url(code_challenge, state, nonce)

        # Store login URL in context
        self.context["login_url"] = login_url

        # Show login URL step first
        return await self.async_step_login_url()

    async def async_step_login_url(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Show the login URL to the user."""
        login_url = self.context.get("login_url", "")
        
        if user_input is None:
            # Show form with login URL in description
            # Use a simple schema with a dummy field to ensure form shows
            return self.async_show_form(
                step_id="login_url",
                data_schema=vol.Schema(
                    {
                        vol.Optional("_continue"): str,  # Hidden field to ensure form renders
                    }
                ),
                description_placeholders={
                    "login_url": login_url,
                },
            )
        
        # User clicked continue, move to callback step
        return await self.async_step_callback()

    async def async_step_callback(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle callback URL entry step."""
        errors = {}

        login_url = self.context.get("login_url", "")
        code_verifier = self.context.get("code_verifier", "")

        if user_input is None:
            # Show form with login URL in description
            # Home Assistant uses strings.json for descriptions with placeholders
            return self.async_show_form(
                step_id="callback",
                data_schema=get_callback_schema(login_url),
                description_placeholders={
                    "login_url": login_url,
                },
                errors=errors,
            )

        callback_url = user_input.get("callback_url", "").strip()

        if not callback_url:
            errors["base"] = "callback_url_required"
            return self.async_show_form(
                step_id="callback",
                data_schema=get_callback_schema(login_url),
                description_placeholders={
                    "login_url": login_url,
                },
                errors=errors,
            )

        # Extract code from callback URL
        code = self._extract_code_from_callback(callback_url)
        if not code:
            errors["base"] = "invalid_callback_url"
            return self.async_show_form(
                step_id="callback",
                data_schema=get_callback_schema(login_url),
                description_placeholders={
                    "login_url": login_url,
                },
                errors=errors,
            )

        # Exchange code for tokens
        try:
            token_response = await self.hass.async_add_executor_job(
                self._exchange_code_for_tokens, code, code_verifier
            )

            if not token_response:
                errors["base"] = "token_exchange_failed"
                return self.async_show_form(
                    step_id="callback",
                    data_schema=get_callback_schema(login_url),
                    description_placeholders={
                        "login_url": login_url,
                    },
                    errors=errors,
                )

            access_token = token_response.get("access_token")
            refresh_token = token_response.get("refresh_token")

            if not access_token:
                errors["base"] = "no_access_token"
                return self.async_show_form(
                    step_id="callback",
                    data_schema=get_callback_schema(login_url),
                    description_placeholders={
                        "login_url": login_url,
                    },
                    errors=errors,
                )

            # Validate token by getting user info
            api = PanasonicAPI(access_token=access_token)
            user_info = await self.hass.async_add_executor_job(api.get_user_info)

            if not user_info or not user_info.get("myAppliances"):
                errors["base"] = "invalid_token"
                return self.async_show_form(
                    step_id="callback",
                    data_schema=get_callback_schema(login_url),
                    description_placeholders={
                        "login_url": login_url,
                    },
                    errors=errors,
                )

            # Get first appliance (fridge)
            appliances = user_info.get("myAppliances", [])
            fridge_appliance = None
            for appliance in appliances:
                if appliance.get("eoj") == "03B7":  # Fridge EOJ
                    fridge_appliance = appliance
                    break

            if not fridge_appliance:
                errors["base"] = "no_fridge_found"
                return self.async_show_form(
                    step_id="callback",
                    data_schema=get_callback_schema(login_url),
                    description_placeholders={
                        "login_url": login_url,
                    },
                    errors=errors,
                )

            appliance_id = fridge_appliance["info"]["applianceId"]
            product_code = fridge_appliance["info"]["productCode"]

            # Check if already configured
            await self.async_set_unique_id(appliance_id)
            self._abort_if_unique_id_configured()

            # Store tokens and device info
            entry_data = {
                CONF_ACCESS_TOKEN: access_token,
                "appliance_id": appliance_id,
                "product_code": product_code,
            }

            if refresh_token:
                entry_data["refresh_token"] = refresh_token

            return self.async_create_entry(
                title=f"Panasonic Fridge ({product_code})",
                data=entry_data,
            )

        except Exception as err:
            _LOGGER.exception("Unexpected exception: %s", err)
            errors["base"] = "unknown"
            return self.async_show_form(
                step_id="callback",
                data_schema=get_callback_schema(login_url),
                description_placeholders={
                    "login_url": login_url,
                },
                errors=errors,
            )

    async def async_step_import(self, import_info: dict[str, Any]) -> FlowResult:
        """Handle import from configuration.yaml."""
        # For import, we still need to go through the flow
        return await self.async_step_user()
