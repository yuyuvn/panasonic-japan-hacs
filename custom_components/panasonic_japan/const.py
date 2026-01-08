"""Constants for the Panasonic Japan integration."""
from __future__ import annotations

DOMAIN = "panasonic_japan"

# API Configuration
API_BASE_URL = "https://app.ref.apws.panasonic.com/reizo/v3"
KAPF_API_BASE_URL = "https://api.kitchen-appliances-pf.com/api/kapf/v1"
AUTH0_DOMAIN = "auth.digital.panasonic.com"
AUTH0_CLIENT_ID = "w7UI3iLByFFz3GOj6Ef6BCHfPczOcsy8"
AUTH0_AUDIENCE = "https://club.panasonic.jp/w7UI3iLByFFz3GOj6Ef6BCHfPczOcsy8/api/v1/"
AUTH0_TOKEN_URL = f"https://{AUTH0_DOMAIN}/oauth/token"
API_KEY = "x6pdB3r5z2eqDCgwf0gF1Ffre7Au7Km3YoFY0fDh"

# Default values
DEFAULT_SCAN_INTERVAL = 300  # 5 minutes
BASELINE_COST = 750  # yen/month
YEN_PER_KWH = 31  # yen/kWh

# Attributes
ATTR_APPLIANCE_ID = "appliance_id"
ATTR_PRODUCT_CODE = "product_code"
ATTR_OPERATION_MODE = "operation_mode"
ATTR_FIRMWARE_VERSION = "firmware_version"
ATTR_COST_REDUCTION = "cost_reduction"
ATTR_ELECTRICITY_USAGE = "electricity_usage"

# Device types
DEVICE_TYPE_FRIDGE = "fridge"
