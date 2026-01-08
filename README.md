# Panasonic Japan Kitchen Appliances Home Assistant Integration

Home Assistant custom component for Panasonic Japan kitchen appliances (fridge, etc.).

## Features

- **Electricity Usage Monitoring**: Track electricity consumption in kWh/month
- **Cost Reduction Tracking**: Monitor energy savings from eco features
- **Device Status**: Operation mode, firmware version, and device status
- **Real-time Updates**: Automatic updates every 5 minutes

## Installation

### HACS Installation

1. Open HACS in Home Assistant
2. Go to "Integrations"
3. Click the three dots menu (⋮) → "Custom repositories"
4. Add repository: `https://github.com/yuyuvn/panasonic-japan-hacs`
5. Select category: "Integration"
6. Click "Add"
7. Search for "Panasonic Japan" and install

### Manual Installation

1. Copy the `custom_components/panasonic_japan` folder to your Home Assistant `custom_components` directory
2. Restart Home Assistant
3. Add integration via Settings → Devices & Services → Add Integration

## Configuration

### Setup Steps

The integration uses Auth0 PKCE (Proof Key for Code Exchange) flow for secure authentication:

1. Go to Settings → Devices & Services
2. Click "Add Integration"
3. Search for "Panasonic Japan"
4. The integration will generate a login URL
5. Click the login URL to open it in your browser
6. Login with your Panasonic account credentials
7. After login, you'll be redirected to a callback URL
8. Copy the entire callback URL and paste it into the integration form
9. The integration will automatically:
   - Extract the authorization code from the callback URL
   - Exchange it for access and refresh tokens
   - Discover your fridge device
   - Complete the setup

### Token Management

The integration automatically:
- Stores both access and refresh tokens securely
- Refreshes the access token when it expires (using the refresh token)
- Updates the stored tokens automatically

No manual token management is required!

## Entities

### Sensors

- **Electricity Usage**: Current monthly electricity consumption (kWh/month)
- **Electricity Cost Reduction**: Energy savings from eco features (yen)
- **Operation Mode**: Current operation mode (econavi, normal, etc.)
- **Firmware Version**: Current firmware version

### Attributes

Each sensor includes additional attributes:
- Appliance ID
- Product Code
- Operation status flags (winter setting, house sitting, etc.)
- Historical reduction data

## API Endpoints Used

- `GET /user/info` - Get user devices
- `GET /devices/{appliance_id}/status` - Device status
- `GET /devices/{appliance_id}/reduction` - Electricity cost reduction data

## Formula

Electricity usage is calculated using:
```
electricity_usage (kWh/month) = (750円 - cost_reduction) / 31円
```

Where:
- 750 yen = Baseline monthly electricity cost
- 31 yen = Cost per kWh
- cost_reduction = Energy savings in yen

## Requirements

- Home Assistant 2023.1 or later
- Python 3.10 or later
- `requests` library
- `zoneinfo` (Python 3.9+)

## Troubleshooting

### Invalid Token Error

- Tokens expire after a certain time
- Generate a new token using the scripts
- Re-configure the integration with the new token

### No Fridge Found

- Ensure your account has a registered fridge
- Check that the appliance is properly registered in the Panasonic app

## Development

### Project Structure

```
panasonic-japan-hacs/
├── custom_components/
│   └── panasonic_japan/
│       ├── __init__.py
│       ├── manifest.json
│       ├── config_flow.py
│       ├── api.py
│       ├── coordinator.py
│       ├── sensor.py
│       ├── switch.py
│       └── const.py
└── README.md
```

## License

MIT License

## Support

For issues and feature requests, please open an issue on GitHub.
