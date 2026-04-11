# eero WiFi Integration for Unfolded Circle Remote

![eero](https://img.shields.io/badge/eero-WiFi%20Mesh-000000?style=flat-square)
[![GitHub Release](https://img.shields.io/github/v/release/mase1981/uc-intg-eero?style=flat-square)](https://github.com/mase1981/uc-intg-eero/releases)
![License](https://img.shields.io/badge/license-MPL--2.0-blue?style=flat-square)
[![GitHub issues](https://img.shields.io/github/issues/mase1981/uc-intg-eero?style=flat-square)](https://github.com/mase1981/uc-intg-eero/issues)
[![Community Forum](https://img.shields.io/badge/community-forum-blue?style=flat-square)](https://unfolded.community/)
[![Discord](https://badgen.net/discord/online-members/zGVYf58)](https://discord.gg/zGVYf58)
![GitHub Downloads](https://img.shields.io/github/downloads/mase1981/uc-intg-eero/total?style=flat-square)
[![Buy Me A Coffee](https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg?style=flat-square)](https://buymeacoffee.com/meirmiyara)
[![PayPal](https://img.shields.io/badge/PayPal-donate-blue.svg?style=flat-square)](https://paypal.me/mmiyara)
[![Github Sponsors](https://img.shields.io/badge/GitHub%20Sponsors-30363D?&logo=GitHub-Sponsors&logoColor=EA4AAA&style=flat-square)](https://github.com/sponsors/mase1981)

Monitor and control your eero WiFi mesh network directly from your Unfolded Circle Remote 2 or Remote 3 with real-time network monitoring, feature toggles, and device management.

---

## Support Development

[![GitHub Sponsors](https://img.shields.io/badge/Sponsor-GitHub-pink?style=for-the-badge&logo=github)](https://github.com/sponsors/mase1981)
[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-FFDD00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://www.buymeacoffee.com/meirmiyara)
[![PayPal](https://img.shields.io/badge/PayPal-00457C?style=for-the-badge&logo=paypal&logoColor=white)](https://paypal.me/mmiyara)

---

## Supported Devices

| Device | Support |
|--------|---------|
| eero 6 | Full |
| eero 6+ | Full |
| eero 6E | Full |
| eero Pro 6 | Full |
| eero Pro 6E | Full |
| eero PoE 6 | Full |
| eero Max 7 | Full |
| eero Beacon | Full (including nightlight info) |
| All other eero models | Full |

> **Note:** This integration uses the eero cloud API. An active internet connection is required.

---

## Sensors

Real-time monitoring of your eero network.

| Sensor | Description |
|--------|-------------|
| Network Status | Network status and internet health |
| Gateway IP | Local gateway IP address |
| Public IP | External public IP address |
| WAN Router IP | WAN router IP address |
| Download Speed | Last speed test download result |
| Upload Speed | Last speed test upload result |
| Connected Clients | Total number of connected devices |
| Eero Nodes | Number of eero nodes in the network |
| ISP | Internet service provider name |
| Last Speed Test | Date of last speed test |
| Per-Eero Status | Status, client count, and firmware per eero node |

---

## Switches

Toggle network features on/off.

| Switch | Description |
|--------|-------------|
| Guest Network | Enable/disable guest WiFi network |
| Band Steering | Automatic band selection for clients |
| SQM | Smart Queue Management for reduced bufferbloat |
| UPnP | Universal Plug and Play |
| WPA3 | Enhanced WiFi security protocol |
| IPv6 | IPv6 upstream connectivity |
| DNS Caching | Local DNS cache |
| Ad Blocking | Block ads network-wide (eero Secure) |
| Block Malware | Block malicious domains (eero Secure) |
| Thread | Thread protocol for smart home devices |
| Dynamic DNS | Dynamic DNS service |
| Pause 5GHz | Temporarily disable 5GHz band |
| Per-Eero LED | Control status LED on each eero node |

---

## Buttons

Trigger actions on your eero network.

| Button | Description |
|--------|-------------|
| Reboot Network | Reboot the entire eero network |
| Run Speed Test | Trigger a new speed test |
| Reboot Eero | Reboot individual eero nodes |

---

## Installation

### Option 1: Remote Web Interface (Recommended)

1. Download the latest `.tar.gz` from [Releases](https://github.com/mase1981/uc-intg-eero/releases)
2. Open Remote web interface → **Settings** → **Integrations**
3. Click **Upload** and select the downloaded file
4. Follow the setup flow (see below)

### Option 2: Docker (Advanced Users)

The integration is available as a pre-built Docker image from GitHub Container Registry:

**Image**: `ghcr.io/mase1981/uc-intg-eero:latest`

**Docker Compose:**
```yaml
services:
  uc-intg-eero:
    image: ghcr.io/mase1981/uc-intg-eero:latest
    container_name: uc-intg-eero
    ports:
      - "9090:9090"
    volumes:
      - </local/path>:/data
    environment:
      - UC_CONFIG_HOME=/data
      - UC_INTEGRATION_HTTP_PORT=9090
      - UC_INTEGRATION_INTERFACE=0.0.0.0
      - PYTHONPATH=/app
    restart: unless-stopped
```

**Docker Run:**
```bash
docker run -d --name uc-eero --restart unless-stopped -p 9090:9090 -v eero-config:/app/config -e UC_CONFIG_HOME=/app/config -e UC_INTEGRATION_INTERFACE=0.0.0.0 -e UC_INTEGRATION_HTTP_PORT=9090 -e PYTHONPATH=/app ghcr.io/mase1981/uc-intg-eero:latest
```

---

## Configuration

### Important: Amazon-Linked Accounts Not Supported

This integration uses the eero cloud API which **does not support Amazon-linked accounts**. If you log into the eero app using your Amazon account, you must create a separate native eero account to use this integration.

**Workaround:**

1. Create a new eero account using a direct email address (not Amazon login)
2. Open the eero app with your Amazon-linked account
3. Go to **Settings** → **Network Admin Management**
4. Add the new email as a **network admin**
5. Use the new email in this integration's setup flow

For detailed instructions, see [this guide](https://github.com/schmittx/home-assistant-eero/issues/77#issuecomment-1960875926).

### Step 1: Start Setup

1. After installation, go to **Settings** → **Integrations**
2. Find the eero integration and click **Configure**
3. Enter a device name and your eero account email or phone number

### Step 2: Verify

1. eero will send a verification code to your email or phone
2. Enter the verification code in the next screen
3. The integration auto-discovers your eero network

### Step 3: Done

The integration creates sensor, switch, and button entities for your network and each eero node automatically.

> **Note:** eero Secure features (Ad Blocking, Block Malware) require an active eero Secure or eero Secure+ subscription.

---

## Authentication

This integration uses the eero cloud API with cookie-based token authentication:
- Login is initiated with your eero account email or phone number (native eero account only, not Amazon-linked)
- A verification code is sent by eero (SMS or email)
- The token is stored locally and refreshed automatically when expired
- No passwords are stored — only the session token

---

## License

Mozilla Public License 2.0 (MPL-2.0)

## Links

- [GitHub Issues](https://github.com/mase1981/uc-intg-eero/issues)
- [UC Community Forum](https://unfolded.community/)
- [Discord](https://discord.gg/zGVYf58)
- [eero Support](https://support.eero.com/)

---

**Made by [Meir Miyara](https://www.linkedin.com/in/meirmiyara/) for the Unfolded Circle and eero communities**
