# cronk-personal-life-tools

Scripts and tools for the cronk-personal-life agent and its subagents.

## Scripts

### `scripts/dateutil.sh`

Date utility script for reliable date/time handling with EST timezone awareness.

**Usage:**
```bash
dateutil.sh now                        # Current date/time with day of week
dateutil.sh day YYYY-MM-DD             # Day of week for a date
dateutil.sh diff YYYY-MM-DD YYYY-MM-DD # Days between two dates
dateutil.sh range YYYY-MM-DD YYYY-MM-DD # List dates in range with days
dateutil.sh until YYYY-MM-DD           # Days from today until date
```

**Example:**
```bash
$ ./scripts/dateutil.sh now
Current Date/Time (EST): Wednesday, January 08, 2026 at 01:09 PM EST
ISO Format: 2026-01-08

$ ./scripts/dateutil.sh day 2026-01-24
2026-01-24 is Saturday, January 24, 2026

$ ./scripts/dateutil.sh range 2026-01-24 2026-01-26
Date Range: 2026-01-24 to 2026-01-26
---
2026-01-24 (Saturday)
2026-01-25 (Sunday)
2026-01-26 (Monday)
```

**Technical Details:**
- Timezone: Hardcoded to `America/New_York` (EST/EDT) for Philadelphia
- Platform: macOS-specific date command syntax
- Date Format: Always expects/outputs ISO format `YYYY-MM-DD`

### `scripts/flight_search.py`

Flight search tool for researching flight prices programmatically.

**Features:**
- Generates search URLs for Google Flights, Kayak, Skyscanner, Southwest
- Supports Amadeus API for automated price lookup (free tier available)
- Preset configurations for recurring trips
- Points portal links (Chase UR, Citi ThankYou)

**Usage:**
```bash
# Use a preset configuration (searches all date combinations)
python3 scripts/flight_search.py --config colorado_trip

# Custom search
python3 scripts/flight_search.py --origin PHL --dest DEN --depart 2026-01-24 --return 2026-01-26 --passengers 2

# List available presets
python3 scripts/flight_search.py --list-presets

# Output as JSON
python3 scripts/flight_search.py --config colorado_trip --json

# Save results
python3 scripts/flight_search.py --config colorado_trip --save data/results.json
```

**API Setup (optional):**
For automated price lookup, register for free Amadeus API credentials:
1. Sign up at https://developers.amadeus.com/
2. Create an app to get API Key and Secret
3. Set environment variables:
   ```bash
   export AMADEUS_API_KEY="your_key"
   export AMADEUS_API_SECRET="your_secret"
   ```

**Adding New Presets:**
Edit the `PRESETS` dictionary in the script to add new trip configurations.

## Data

- `data/colorado-trip-flights.json` - Saved flight search results for Colorado trip

## Related Knowledge Graph

See the [cronk-agents-knowledge-graph](https://github.com/cronk-magic/cronk-agents-knowledge-graph) for documentation:
- `nodes/date-time-utilities.md` - Date/time handling procedures
- `nodes/date-time-utilities/date-script.md` - Script usage documentation
- `nodes/flight-search-tools.md` - Flight search automation
