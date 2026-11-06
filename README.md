# AstralPool ConnectMyPool Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

A Home Assistant custom integration for AstralPool / Viron Connect pool and spa systems that use the [ConnectMyPool](https://www.connectmypool.com.au) cloud API.

## Features

- **Temperature sensor** — current water temperature
- **Heater control** — on/off switch and set-temperature number entity
- **Solar heater control** — off/auto/on select and set-temperature number entity
- **Channel control** — filter pumps, spa jets, blowers, etc. with mode selection
- **Valve control** — off/auto/on select entities
- **Lighting control** — on/off/auto plus colour selection for colour-enabled zones
- **Pool/Spa mode** — switch between pool and spa for combined systems
- **Heat/Cool mode** — switch between heating and cooling
- **Favourites** — activate configured favourites from a select entity
- **Auto-discovery of devices** — the integration reads your pool's configuration and creates only the entities that apply to your setup

## Prerequisites

You need a **Pool API Code** from AstralPool:

1. Log in to [ConnectMyPool](https://www.connectmypool.com.au) via a desktop browser
2. Go to **Settings → Home Automation**
3. Click **Request Home Automation Access**
4. Wait for the approval email
5. Return to the Home Automation page to retrieve your **Pool API Code**

## Installation

[![Open your Home Assistant instance and open this repository.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=smck83&repository=ha-connectmypool&category=integration)

This button works with the Marketplace (Home Assistant 2026.11 and later) and with HACS (2026.10 and earlier).

1. Click the button above and install **AstralPool ConnectMyPool**
2. Restart Home Assistant
3. Go to **Settings → Devices & Services → Add Integration → ConnectMyPool**
4. Enter your Pool API Code and a friendly name for your pool

## API Rate Limiting

The ConnectMyPool API enforces a **60-second throttle** on status and config requests. This integration polls every **61 seconds** to stay safely outside that window.

When you make a change (toggle a light, adjust a temperature, switch a mode, etc.) the integration waits for the pool to confirm it, then requests a status refresh. Sending an action lifts the API throttle for 5 minutes, so this follow-up poll succeeds straight away and the UI updates soon after the pool responds, rather than at the next scheduled poll. If the pool fails or times out, Home Assistant shows an error.

## How Some Controls Behave

- **Set temperatures on combined pool and spa systems** — the API can only change the set temperature of the active mode, so the Heater Set Temperature slider works in Pool mode and the Heater Spa Set Temperature slider works in Spa mode. Using the other slider shows an error and changes nothing.
- **Channel modes** — the API can only step a channel to its next mode, so the integration steps it until it reaches the mode you picked. This can take several seconds, and the device passes through the modes in between. The list shows every possible mode, but the modes available depend on the device. If you pick one the device does not have, it steps through its modes, returns to where it started and shows an error.

## Entities Created

| Platform | Entity | Description |
|----------|--------|-------------|
| `sensor` | Water Temperature | Current pool/spa water temperature |
| `switch` | Heater (per heater) | Turn heater on/off |
| `number` | Heater Set Temp (per heater) | Adjust heater target temperature |
| `number` | Heater Spa Set Temp (per heater) | Adjust spa heater target temperature |
| `select` | Solar Mode (per solar) | Off / Auto / On |
| `number` | Solar Set Temp (per solar) | Adjust solar target temperature |
| `select` | Channel Mode (per channel) | Off / Auto / On / Low / Medium / High |
| `select` | Valve Mode (per valve) | Off / Auto / On |
| `switch` | Light (per zone) | Turn light on/off |
| `select` | Light Mode (per zone) | Off / Auto / On |
| `select` | Light Colour (per zone) | Colour selection for colour-enabled zones |
| `select` | Pool/Spa Mode | Switch between Pool and Spa |
| `select` | Heat/Cool Mode | Switch between Heating and Cooling |
| `select` | Active Favourite | Activate a favourite |

## Troubleshooting

- **"Time Throttle Exceeded"** — the API only answers once every 60 seconds. The integration polls every 61 seconds and retries by itself, so if you see this while adding your pool, wait a minute and try again.
- **"Pool Not Connected"** — your pool hardware is offline or not communicating with ConnectMyPool.
- **"Invalid API Code"** — double-check your Pool API Code in the integration configuration.

## Credits

Inspired by the community work in the [Home Assistant Community thread](https://community.home-assistant.io/t/rest-sensor-receiving-json-astralpool-connectmypool-com-au/306727) by @smck83, @zagnuts, and others.

## License

[MIT](LICENSE)
