"""
IMF PortWatch Collector
Fetches chokepoint vessel arrival data from IMF PortWatch
"""
from datetime import datetime
from typing import Dict, Any, List
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
import requests


class IMFPortWatchCollector:
    """Collector for IMF PortWatch data"""

    BASE_URL = "https://portwatch.imf.org"
    CHOKEPOINT_MAP = {
        'bab-el-mandeb': 'chokepoint4',
        'strait-of-hormuz': 'chokepoint6',
        'strait-of-malacca': 'chokepoint5',
        'suez-canal': 'chokepoint1',
        'panama-canal': 'chokepoint2',
        'bosporus-strait': 'chokepoint3'
    }

    def __init__(self):
        pass

    def collect(self, source_url: str, chokepoint: str, variable: str, start_date: str = None) -> Dict[str, Any]:
        """
        Collect vessel arrival historical data from IMF PortWatch

        This method extracts the ArcGIS API URL from the page and fetches
        daily vessel data for the chokepoint. Can optionally fetch only data
        from a specific start date onwards (incremental collection).

        Args:
            source_url: The source URL from state_variables.json
            chokepoint: Chokepoint ID (e.g., 'bab-el-mandeb')
            variable: Variable name (e.g., 'vessel_arrivals')
            start_date: Optional start date in YYYY-MM-DD format (fetch from this date onwards)

        Returns:
            Dictionary with time series data, timestamp, and metadata
        """
        try:
            # Map chokepoint name to ArcGIS portid
            portid = self.CHOKEPOINT_MAP.get(chokepoint)
            if not portid:
                raise Exception(f"Unknown chokepoint: {chokepoint}")

            if start_date:
                print(f"   📡 Fetching data from {start_date} onwards...")
            else:
                print(f"   📡 Extracting API URL from {source_url}...")

            # Use Playwright to load the page and capture the query URL
            query_url = self._extract_api_url(source_url, portid)

            if not query_url:
                raise Exception("Could not extract API URL from page")

            print(f"   🎯 Found API URL")

            # Convert protobuf URL to JSON and add ordering
            json_url = query_url.replace('f=pbf', 'f=json')

            # Add orderByFields to get newest data first
            if 'orderByFields' not in json_url:
                json_url += '&orderByFields=date%20DESC'

            # If start_date is provided, we'll fetch recent data and filter in Python
            # (ArcGIS API doesn't support date comparison in where clause)
            if start_date:
                from datetime import datetime as dt
                start_dt = dt.strptime(start_date, '%Y-%m-%d')
                start_epoch = int(start_dt.timestamp() * 1000)

                # Fetch last 100 days to ensure we get all new data
                json_url += '&resultRecordCount=100'
                print(f"   📥 Fetching recent data (will filter >= {start_date})...")
            else:
                print(f"   📥 Fetching all historical data...")

            # Fetch the data
            response = requests.get(json_url, timeout=30)
            response.raise_for_status()
            data = response.json()

            # Check if we got any features
            if 'features' not in data or not data['features']:
                # This is normal when doing incremental collection and there's no new data
                print(f"   ℹ️ No new data available from API")
                return {
                    "time_series": [],
                    "total_records": 0,
                    "date_range": {
                        "start": None,
                        "end": None
                    },
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "source": source_url,
                    "chokepoint": chokepoint,
                    "variable": variable,
                    "status": "success",
                    "note": "No new data available"
                }

            # Process the features into time series
            time_series = []
            for feature in data['features']:
                attrs = feature['attributes']
                date_ms = attrs.get('date')

                if date_ms:
                    # Filter by start_date if provided
                    if start_date and date_ms < start_epoch:
                        continue

                    dt = datetime.fromtimestamp(date_ms / 1000)
                    time_series.append({
                        'date': dt.strftime('%Y-%m-%d'),
                        'year': attrs.get('year'),
                        'month': attrs.get('month'),
                        'day': attrs.get('day'),
                        'vessel_count': attrs.get('n_total', 0),
                        'container': attrs.get('n_container', 0),
                        'dry_bulk': attrs.get('n_dry_bulk', 0),
                        'general_cargo': attrs.get('n_general_cargo', 0),
                        'roro': attrs.get('n_roro', 0),
                        'tanker': attrs.get('n_tanker', 0)
                    })

            # Sort by date
            time_series.sort(key=lambda x: x['date'])

            if time_series:
                print(f"   ✅ Collected {len(time_series)} daily records")
                print(f"   📅 Date range: {time_series[0]['date']} to {time_series[-1]['date']}")
            else:
                print(f"   ℹ️ No new data available")

            return {
                "time_series": time_series,
                "total_records": len(time_series),
                "date_range": {
                    "start": time_series[0]['date'] if time_series else None,
                    "end": time_series[-1]['date'] if time_series else None
                },
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "source": source_url,
                "chokepoint": chokepoint,
                "variable": variable,
                "status": "success"
            }

        except Exception as e:
            return {
                "time_series": [],
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "source": source_url,
                "chokepoint": chokepoint,
                "variable": variable,
                "status": "error",
                "error": str(e)
            }

    def _extract_api_url(self, source_url: str, portid: str) -> str:
        """
        Extract the ArcGIS API query URL from the page by intercepting network requests

        Args:
            source_url: The page URL to load
            portid: The chokepoint ID (e.g., 'chokepoint4')

        Returns:
            The captured API query URL
        """
        captured_url = None

        def handle_request(request):
            nonlocal captured_url
            url = request.url
            # Look for Daily_Chokepoints_Data query with the specific portid
            if 'Daily_Chokepoints_Data' in url and '/query' in url and f"portid%3D%27{portid}%27" in url:
                captured_url = url

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()

                # Listen for requests
                page.on("request", handle_request)

                # Load page
                page.goto(source_url, wait_until="load", timeout=30000)

                # Wait for initial load
                page.wait_for_timeout(10000)

                # Scroll to trigger data loading
                for i in range(20):
                    page.keyboard.press("PageDown")
                    page.wait_for_timeout(500)

                    # Break early if we got the URL
                    if captured_url:
                        break

                # Extra wait
                page.wait_for_timeout(3000)

                browser.close()

                return captured_url

        except Exception as e:
            print(f"   ⚠️ Error extracting API URL: {e}")
            return None
