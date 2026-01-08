#!/usr/bin/env python3
"""
Flight Search Tool - Query flight prices programmatically

This script provides multiple methods for flight price research:
1. Amadeus API (requires free API key registration)
2. Google Flights URL generator (for manual lookup)
3. Direct airline booking URL generator

Usage:
    python3 flight_search.py --origin PHL --dest DEN --depart 2026-01-24 --return 2026-01-26 --passengers 2
    python3 flight_search.py --config colorado_trip  # Use preset configuration

API Setup (optional, enables price fetching):
    1. Register at https://developers.amadeus.com/
    2. Create an app to get API Key and Secret
    3. Set environment variables:
       export AMADEUS_API_KEY="your_key"
       export AMADEUS_API_SECRET="your_secret"
"""

import argparse
import json
import os
import sys
import urllib.parse
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import urllib.request
import ssl

# ============================================================================
# Configuration Presets
# ============================================================================

PRESETS = {
    "colorado_trip": {
        "origin": "PHL",
        "destination": "DEN",
        "outbound_dates": ["2026-01-23", "2026-01-24"],  # Fri or Sat
        "return_dates": ["2026-01-26", "2026-01-27", "2026-01-28", "2026-01-29"],  # Mon-Thu
        "passengers": 2,
        "description": "Colorado snowboarding trip - Jan 2026"
    }
}

# Airlines commonly flying PHL-DEN route
AIRLINES = {
    "AA": {"name": "American Airlines", "code": "AA", "url": "https://www.aa.com"},
    "UA": {"name": "United Airlines", "code": "UA", "url": "https://www.united.com"},
    "F9": {"name": "Frontier Airlines", "code": "F9", "url": "https://www.flyfrontier.com"},
    "WN": {"name": "Southwest Airlines", "code": "WN", "url": "https://www.southwest.com"},
    "DL": {"name": "Delta Air Lines", "code": "DL", "url": "https://www.delta.com"},
    "NK": {"name": "Spirit Airlines", "code": "NK", "url": "https://www.spirit.com"},
}

# ============================================================================
# URL Generators
# ============================================================================

def generate_google_flights_url(
    origin: str,
    destination: str,
    depart_date: str,
    return_date: str,
    passengers: int = 1
) -> str:
    """Generate a Google Flights search URL."""
    # Google Flights URL format
    # https://www.google.com/travel/flights?q=Flights%20to%20DEN%20from%20PHL%20on%202026-01-24%20through%202026-01-26
    
    base_url = "https://www.google.com/travel/flights"
    # Simpler parameterized approach
    params = {
        "hl": "en",
        "curr": "USD",
    }
    
    # Build the flight search query
    # Format: /flights/PHL/DEN/2026-01-24/2026-01-26
    path = f"/flights/{origin}/{destination}/{depart_date}/{return_date}"
    
    # Alternative: use the q parameter
    query = f"Flights from {origin} to {destination} on {depart_date} through {return_date}"
    if passengers > 1:
        query += f" {passengers} passengers"
    
    params["q"] = query
    
    return f"{base_url}?{urllib.parse.urlencode(params)}"


def generate_google_flights_direct_url(
    origin: str,
    destination: str,
    depart_date: str,
    return_date: str,
    passengers: int = 1
) -> str:
    """Generate a direct Google Flights URL with proper encoding."""
    # Direct URL format that works more reliably
    # Example: https://www.google.com/travel/flights/search?tfs=...
    
    base = "https://www.google.com/travel/flights/search"
    
    # Build readable URL
    params = []
    params.append(f"f={origin}")
    params.append(f"t={destination}")
    params.append(f"d={depart_date}")
    params.append(f"r={return_date}")
    if passengers > 1:
        params.append(f"px={passengers}")
    
    # Actually use the simpler search format
    simple_url = f"https://www.google.com/travel/flights?q=Flights+to+{destination}+from+{origin}+on+{depart_date}+through+{return_date}"
    
    return simple_url


def generate_kayak_url(
    origin: str,
    destination: str,
    depart_date: str,
    return_date: str,
    passengers: int = 1
) -> str:
    """Generate a Kayak search URL."""
    # Format: https://www.kayak.com/flights/PHL-DEN/2026-01-24/2026-01-26/2adults
    passengers_str = f"{passengers}adults" if passengers > 1 else ""
    return f"https://www.kayak.com/flights/{origin}-{destination}/{depart_date}/{return_date}/{passengers_str}"


def generate_skyscanner_url(
    origin: str,
    destination: str,
    depart_date: str,
    return_date: str,
    passengers: int = 1
) -> str:
    """Generate a Skyscanner search URL."""
    # Format: https://www.skyscanner.com/transport/flights/phl/denv/260124/260126/
    depart_fmt = datetime.strptime(depart_date, "%Y-%m-%d").strftime("%y%m%d")
    return_fmt = datetime.strptime(return_date, "%Y-%m-%d").strftime("%y%m%d")
    return f"https://www.skyscanner.com/transport/flights/{origin.lower()}/{destination.lower()}e/{depart_fmt}/{return_fmt}/"


def generate_southwest_url(
    origin: str,
    destination: str,
    depart_date: str,
    return_date: str,
    passengers: int = 1
) -> str:
    """Generate Southwest Airlines search URL."""
    # Southwest has a specific URL format
    base = "https://www.southwest.com/air/booking/select.html"
    params = {
        "originationAirportCode": origin,
        "destinationAirportCode": destination,
        "returnAirportCode": "",
        "departureDate": depart_date,
        "departureTimeOfDay": "ALL_DAY",
        "returnDate": return_date,
        "returnTimeOfDay": "ALL_DAY",
        "adultPassengersCount": str(passengers),
        "seniorPassengersCount": "0",
        "tripType": "roundtrip",
        "fareType": "USD",
        "passengerType": "ADULT",
        "reset": "true",
        "int": "HOMEQBOMAIR"
    }
    return f"{base}?{urllib.parse.urlencode(params)}"


# ============================================================================
# Points Portal URLs
# ============================================================================

def generate_chase_ur_url() -> str:
    """Generate Chase Ultimate Rewards travel portal URL."""
    return "https://ultimaterewardspoints.chase.com/travel"


def generate_citi_ty_url() -> str:
    """Generate Citi ThankYou travel portal URL."""
    return "https://www.thankyou.com/cms/thankyou/travel.page"


# ============================================================================
# Amadeus API Integration
# ============================================================================

class AmadeusAPI:
    """Amadeus Flight Offers API client."""
    
    def __init__(self):
        self.api_key = os.environ.get("AMADEUS_API_KEY")
        self.api_secret = os.environ.get("AMADEUS_API_SECRET")
        self.token = None
        self.base_url = "https://test.api.amadeus.com"  # Use test for free tier
        
    def is_configured(self) -> bool:
        """Check if API credentials are available."""
        return bool(self.api_key and self.api_secret)
    
    def authenticate(self) -> bool:
        """Get OAuth token from Amadeus."""
        if not self.is_configured():
            return False
            
        url = f"{self.base_url}/v1/security/oauth2/token"
        data = urllib.parse.urlencode({
            "grant_type": "client_credentials",
            "client_id": self.api_key,
            "client_secret": self.api_secret
        }).encode()
        
        try:
            req = urllib.request.Request(url, data=data, method="POST")
            req.add_header("Content-Type", "application/x-www-form-urlencoded")
            
            # Handle SSL
            context = ssl.create_default_context()
            
            with urllib.request.urlopen(req, context=context) as response:
                result = json.loads(response.read())
                self.token = result.get("access_token")
                return bool(self.token)
        except Exception as e:
            print(f"Amadeus auth error: {e}", file=sys.stderr)
            return False
    
    def search_flights(
        self,
        origin: str,
        destination: str,
        depart_date: str,
        return_date: str,
        passengers: int = 1,
        max_results: int = 10
    ) -> Optional[List[Dict]]:
        """Search for flight offers."""
        if not self.token:
            if not self.authenticate():
                return None
        
        url = f"{self.base_url}/v2/shopping/flight-offers"
        params = {
            "originLocationCode": origin,
            "destinationLocationCode": destination,
            "departureDate": depart_date,
            "returnDate": return_date,
            "adults": passengers,
            "nonStop": "false",
            "currencyCode": "USD",
            "max": max_results
        }
        
        full_url = f"{url}?{urllib.parse.urlencode(params)}"
        
        try:
            req = urllib.request.Request(full_url)
            req.add_header("Authorization", f"Bearer {self.token}")
            
            context = ssl.create_default_context()
            
            with urllib.request.urlopen(req, context=context) as response:
                result = json.loads(response.read())
                return self._parse_offers(result)
        except Exception as e:
            print(f"Amadeus search error: {e}", file=sys.stderr)
            return None
    
    def _parse_offers(self, response: Dict) -> List[Dict]:
        """Parse Amadeus response into simplified format."""
        offers = []
        for offer in response.get("data", []):
            parsed = {
                "price": float(offer.get("price", {}).get("total", 0)),
                "currency": offer.get("price", {}).get("currency", "USD"),
                "segments": [],
                "airlines": set()
            }
            
            for itinerary in offer.get("itineraries", []):
                for segment in itinerary.get("segments", []):
                    seg_info = {
                        "departure": segment.get("departure", {}).get("iataCode"),
                        "arrival": segment.get("arrival", {}).get("iataCode"),
                        "departure_time": segment.get("departure", {}).get("at"),
                        "arrival_time": segment.get("arrival", {}).get("at"),
                        "carrier": segment.get("carrierCode"),
                        "flight_number": segment.get("number"),
                        "duration": segment.get("duration")
                    }
                    parsed["segments"].append(seg_info)
                    parsed["airlines"].add(segment.get("carrierCode"))
            
            parsed["airlines"] = list(parsed["airlines"])
            offers.append(parsed)
        
        return offers


# ============================================================================
# Main Search Function
# ============================================================================

def search_flights(
    origin: str,
    destination: str,
    depart_date: str,
    return_date: str,
    passengers: int = 1,
    use_api: bool = True
) -> Dict:
    """
    Search for flights and return results with URLs.
    
    Returns dict with:
        - api_results: List of flight offers (if API configured)
        - urls: Dict of search URLs for manual checking
        - points_urls: Dict of points portal URLs
    """
    result = {
        "search_params": {
            "origin": origin,
            "destination": destination,
            "depart_date": depart_date,
            "return_date": return_date,
            "passengers": passengers
        },
        "api_results": None,
        "urls": {},
        "points_urls": {},
        "timestamp": datetime.now().isoformat()
    }
    
    # Try API if requested
    if use_api:
        api = AmadeusAPI()
        if api.is_configured():
            print(f"Searching Amadeus API for {origin} → {destination}...", file=sys.stderr)
            result["api_results"] = api.search_flights(
                origin, destination, depart_date, return_date, passengers
            )
            if result["api_results"]:
                print(f"Found {len(result['api_results'])} offers", file=sys.stderr)
        else:
            print("Amadeus API not configured (set AMADEUS_API_KEY and AMADEUS_API_SECRET)", file=sys.stderr)
    
    # Generate comparison shopping URLs
    result["urls"] = {
        "google_flights": generate_google_flights_direct_url(
            origin, destination, depart_date, return_date, passengers
        ),
        "kayak": generate_kayak_url(
            origin, destination, depart_date, return_date, passengers
        ),
        "skyscanner": generate_skyscanner_url(
            origin, destination, depart_date, return_date, passengers
        ),
        "southwest": generate_southwest_url(
            origin, destination, depart_date, return_date, passengers
        )
    }
    
    # Points portal URLs
    result["points_urls"] = {
        "chase_ultimate_rewards": generate_chase_ur_url(),
        "citi_thankyou": generate_citi_ty_url()
    }
    
    return result


def search_date_combinations(preset_name: str) -> List[Dict]:
    """Search all date combinations for a preset configuration."""
    if preset_name not in PRESETS:
        raise ValueError(f"Unknown preset: {preset_name}")
    
    preset = PRESETS[preset_name]
    results = []
    
    for depart in preset["outbound_dates"]:
        for return_date in preset["return_dates"]:
            print(f"\n{'='*60}", file=sys.stderr)
            print(f"Searching: {depart} → {return_date}", file=sys.stderr)
            print(f"{'='*60}", file=sys.stderr)
            
            result = search_flights(
                origin=preset["origin"],
                destination=preset["destination"],
                depart_date=depart,
                return_date=return_date,
                passengers=preset["passengers"]
            )
            result["trip_name"] = preset_name
            results.append(result)
    
    return results


def format_results(results: List[Dict], output_format: str = "text") -> str:
    """Format search results for display."""
    if output_format == "json":
        return json.dumps(results, indent=2)
    
    lines = []
    lines.append("=" * 70)
    lines.append("FLIGHT SEARCH RESULTS")
    lines.append("=" * 70)
    
    for r in results:
        params = r["search_params"]
        lines.append("")
        lines.append(f"Route: {params['origin']} → {params['destination']}")
        lines.append(f"Dates: {params['depart_date']} to {params['return_date']}")
        lines.append(f"Passengers: {params['passengers']}")
        lines.append("-" * 50)
        
        # API results
        if r["api_results"]:
            lines.append("API RESULTS (prices in USD):")
            for i, offer in enumerate(r["api_results"][:5], 1):
                airlines = ", ".join(offer["airlines"])
                lines.append(f"  {i}. ${offer['price']:.2f} - {airlines}")
        else:
            lines.append("API: Not available (check URLs below)")
        
        lines.append("")
        lines.append("SEARCH URLS (click to compare prices):")
        for name, url in r["urls"].items():
            lines.append(f"  • {name.replace('_', ' ').title()}: {url}")
        
        lines.append("")
    
    # Points info (just once)
    lines.append("=" * 70)
    lines.append("POINTS PORTALS:")
    for name, url in results[0]["points_urls"].items():
        lines.append(f"  • {name.replace('_', ' ').title()}: {url}")
    
    lines.append("")
    lines.append("NOTE: Points redemption values vary. Check portals for current rates:")
    lines.append("  - Chase UR: Often 1.25-1.5 cents/point via portal")
    lines.append("  - Citi TY: Often 1-1.25 cents/point via portal")
    lines.append("  - Transfer partners may offer better value")
    
    return "\n".join(lines)


# ============================================================================
# CLI Interface
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Search for flight prices",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    # Preset config
    parser.add_argument(
        "--config", "-c",
        choices=list(PRESETS.keys()),
        help="Use a preset configuration"
    )
    
    # Manual parameters
    parser.add_argument("--origin", "-o", help="Origin airport code (e.g., PHL)")
    parser.add_argument("--dest", "-d", help="Destination airport code (e.g., DEN)")
    parser.add_argument("--depart", help="Departure date (YYYY-MM-DD)")
    parser.add_argument("--return", dest="return_date", help="Return date (YYYY-MM-DD)")
    parser.add_argument("--passengers", "-p", type=int, default=1, help="Number of passengers")
    
    # Output options
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--no-api", action="store_true", help="Skip API lookup")
    parser.add_argument(
        "--save", "-s",
        help="Save results to file"
    )
    
    # Info
    parser.add_argument("--list-presets", action="store_true", help="List available presets")
    
    args = parser.parse_args()
    
    if args.list_presets:
        print("Available presets:")
        for name, config in PRESETS.items():
            print(f"  {name}: {config['description']}")
            print(f"    Route: {config['origin']} → {config['destination']}")
            print(f"    Outbound: {', '.join(config['outbound_dates'])}")
            print(f"    Return: {', '.join(config['return_dates'])}")
        return
    
    # Use preset or manual params
    if args.config:
        results = search_date_combinations(args.config)
    elif args.origin and args.dest and args.depart and args.return_date:
        result = search_flights(
            origin=args.origin,
            destination=args.dest,
            depart_date=args.depart,
            return_date=args.return_date,
            passengers=args.passengers,
            use_api=not args.no_api
        )
        results = [result]
    else:
        parser.print_help()
        print("\nError: Either --config or all of --origin, --dest, --depart, --return are required")
        sys.exit(1)
    
    # Format output
    output_format = "json" if args.json else "text"
    output = format_results(results, output_format)
    print(output)
    
    # Save if requested
    if args.save:
        with open(args.save, "w") as f:
            # Always save as JSON for machine readability
            json.dump(results, f, indent=2)
        print(f"\nResults saved to: {args.save}", file=sys.stderr)


if __name__ == "__main__":
    main()
