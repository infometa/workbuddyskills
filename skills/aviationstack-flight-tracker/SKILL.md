---
name: aviationstack-flight-tracker
version: 1.0.0
description: Track flights in real-time with detailed status, gate info, delays, and live position. Use when user asks to track a flight, check flight status, look up flight information by flight number (e.g., "track AA100", "what's the status of United 2402", "check my flight BA123"), or wants to display flight data in a formatted view similar to Flighty app. Requires AVIATIONSTACK_API_KEY.
description_zh: "实时航班追踪：登机口、延误、飞行位置，类 Flighty 体验（需 API Key）"
description_en: "Real-time flight tracking with gate info, delays and live position via Aviationstack"
allowed-tools: Bash,Read
---

# Flight Tracker

Track any flight worldwide using AviationStack API and display in a clean, Flighty-style format.

## Quick Start

Track a flight by its IATA code:

```bash
scripts/track_flight.py AA100
scripts/track_flight.py UA2402
scripts/track_flight.py BA123
```

## First-Time Setup

Before using this skill, you need an API key (one-time setup):

1. **Get a free API key** at https://aviationstack.com/signup/free (100 requests/month)
2. **Set environment variable:**
   ```bash
   export AVIATIONSTACK_API_KEY='your-key-here'
   ```
3. **Install dependencies:**
   ```bash
   pip3 install requests
   ```

For detailed setup instructions, see [api-setup.md](references/api-setup.md).

## Output Format

The skill displays flight information in a clean, readable format with:

- ✈️ Airline and flight number
- 🛩️ Aircraft type and registration
- 🛫 Departure airport, terminal, gate, times
- 🛬 Arrival airport, terminal, gate, times
- 📊 Flight status with visual indicators
- ⏱️ Delay calculations (if applicable)
- 🌐 Live position, altitude, speed (when airborne)

Status indicators:
- 🟢 Active/Airborne/En-route
- ✅ Landed/Arrived
- 🟡 Scheduled
- 🟠 Delayed
- 🔴 Cancelled

## Advanced Usage

**Get raw JSON data:**
```bash
scripts/track_flight.py AA100 --json
```

**Check help:**
```bash
scripts/track_flight.py --help
```

## Workflow

When a user asks to track a flight:

1. Extract the flight number from the request
2. Run the tracking script with the flight number
3. Present the formatted output to the user
4. If data is needed for further processing, use `--json` flag

## Flight Number Formats

Accept IATA flight codes:
- AA100 (American Airlines)
- UA2402 (United)
- BA123 (British Airways)
- DL456 (Delta)

The script automatically converts to uppercase and handles the lookup.

## Error Handling

The script handles common errors:
- Missing API key → Shows setup instructions
- Flight not found → Suggests verification
- API errors → Displays error message
- Rate limit exceeded → Indicates limit reached

## API Limits

Free tier: 100 requests/month. Track usage to stay within limits. For heavy usage, consider upgrading or alternative APIs (see references/api-setup.md).

## Notes

- Uses AviationStack free tier (no HTTPS on free plan)
- Real-time data updated frequently
- Historical flight data available
- Worldwide coverage (250+ countries, 13,000+ airlines)
