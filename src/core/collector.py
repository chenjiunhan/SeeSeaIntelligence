"""
Core Collector
Reads JSON config and routes to appropriate collector
"""
import json
import pickle
from pathlib import Path
from typing import Dict, Any
from urllib.parse import urlparse

import sys
from pathlib import Path
# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from collectors.imf_portwatch import IMFPortWatchCollector


class DataCollector:
    """Main data collector that routes to specific collectors"""

    def __init__(self, base_path: Path = None):
        """
        Initialize collector

        Args:
            base_path: Base path for the project (defaults to project root)
        """
        if base_path is None:
            # Assume we're in src/core, go up two levels
            self.base_path = Path(__file__).parent.parent.parent
        else:
            self.base_path = Path(base_path)

        # Initialize collectors
        self.collectors = {
            'portwatch.imf.org': IMFPortWatchCollector(),
        }

    def load_config(self, chokepoint: str) -> Dict[str, Any]:
        """
        Load state_variables.json for a chokepoint

        Args:
            chokepoint: Chokepoint ID (e.g., 'bab-el-mandeb')

        Returns:
            Dictionary from state_variables.json
        """
        config_path = self.base_path / 'src' / 'logistics' / 'chokepoints' / chokepoint / 'state_variables.json'

        if not config_path.exists():
            raise FileNotFoundError(f"Config not found: {config_path}")

        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_collector(self, source_url: str):
        """
        Get appropriate collector based on source URL

        Args:
            source_url: Source URL from config

        Returns:
            Collector instance
        """
        parsed = urlparse(source_url)
        domain = parsed.netloc

        # Match domain to collector
        for collector_domain, collector in self.collectors.items():
            if collector_domain in domain:
                return collector

        raise ValueError(f"No collector found for domain: {domain}")

    def collect(self, chokepoint: str, variable: str, incremental: bool = True) -> Dict[str, Any]:
        """
        Collect data for a specific variable

        Args:
            chokepoint: Chokepoint ID
            variable: Variable name
            incremental: If True, only fetch data from the last collected date onwards

        Returns:
            Collected data
        """
        # Load config
        config = self.load_config(chokepoint)

        if variable not in config:
            raise ValueError(f"Variable '{variable}' not found in config for {chokepoint}")

        variable_config = config[variable]
        source_url = variable_config['source']

        # Get appropriate collector
        collector = self.get_collector(source_url)

        # Check if we should do incremental collection
        start_date = None
        if incremental:
            latest_date = self._get_latest_date(chokepoint, variable)
            if latest_date:
                # Fetch from the day after the latest date
                from datetime import datetime, timedelta
                latest_dt = datetime.strptime(latest_date, '%Y-%m-%d')
                next_day = latest_dt + timedelta(days=1)
                start_date = next_day.strftime('%Y-%m-%d')
                print(f"   📊 Incremental mode: fetching from {start_date} onwards")
            else:
                print(f"   📊 First time collection: fetching all historical data")

        # Collect data (pass start_date if collector supports it)
        try:
            data = collector.collect(source_url, chokepoint, variable, start_date=start_date)
        except TypeError:
            # Fallback for collectors that don't support start_date parameter
            data = collector.collect(source_url, chokepoint, variable)

        # Save to file
        self.save_data(chokepoint, variable, data)

        return data

    def save_data(self, chokepoint: str, variable: str, data: Dict[str, Any]):
        """
        Save collected data to pickle files with date-based naming

        If data contains a time_series, saves each day's data to a separate file.
        Skips files that already exist (incremental save).
        Updates metadata to track the latest collected date.

        Args:
            chokepoint: Chokepoint ID (e.g., 'bab-el-mandeb')
            variable: Variable name
            data: Data to save (may contain time_series field)
        """
        from datetime import datetime

        # Create directory structure: data/logistics/chokepoints/{chokepoint}/{variable}/
        data_dir = self.base_path / 'data' / 'logistics' / 'chokepoints' / chokepoint / variable
        data_dir.mkdir(parents=True, exist_ok=True)

        # Check if data contains time series with actual data
        if 'time_series' in data and data['time_series'] and len(data['time_series']) > 0:
            # Save each day's data separately (skip existing files)
            time_series = data['time_series']
            print(f"   💾 Processing {len(time_series)} daily records...")

            saved_count = 0
            skipped_count = 0

            for daily_record in time_series:
                date_str = daily_record['date']  # Already in YYYY-MM-DD format
                file_path = data_dir / f'{date_str}.pckl'

                # Skip if file already exists
                if file_path.exists():
                    skipped_count += 1
                    continue

                # Create a daily data package
                daily_data = {
                    'date': date_str,
                    'vessel_count': daily_record['vessel_count'],
                    'breakdown': {
                        'container': daily_record.get('container', 0),
                        'dry_bulk': daily_record.get('dry_bulk', 0),
                        'general_cargo': daily_record.get('general_cargo', 0),
                        'roro': daily_record.get('roro', 0),
                        'tanker': daily_record.get('tanker', 0)
                    },
                    'collected_at': data['timestamp'],
                    'source': data['source'],
                    'chokepoint': chokepoint,
                    'variable': variable,
                    'status': data['status']
                }

                with open(file_path, 'wb') as f:
                    pickle.dump(daily_data, f)

                saved_count += 1

            # Update metadata
            if time_series:
                latest_date = time_series[-1]['date']  # Already sorted by date
                self._update_metadata(chokepoint, variable, latest_date)

            print(f"   ✅ Saved {saved_count} new files, skipped {skipped_count} existing files")

        else:
            # No time series data
            # Check if total_records is 0 (no new data)
            if data.get('total_records', 0) == 0:
                # This is expected when doing incremental collection with no new data
                print(f"   ℹ️  No new data to save")
            else:
                # Unexpected case - save as-is for debugging
                date_str = datetime.utcnow().strftime('%Y-%m-%d')
                file_path = data_dir / f'{date_str}.pckl'

                with open(file_path, 'wb') as f:
                    pickle.dump(data, f)

                print(f"   ⚠️  Saved non-timeseries data to: {file_path}")

    def _update_metadata(self, chokepoint: str, variable: str, latest_date: str):
        """
        Update metadata file with the latest collected date

        Args:
            chokepoint: Chokepoint ID
            variable: Variable name
            latest_date: Latest date in YYYY-MM-DD format
        """
        from datetime import datetime

        data_dir = self.base_path / 'data' / 'logistics' / 'chokepoints' / chokepoint / variable
        metadata_path = data_dir / '_metadata.json'

        metadata = {
            'chokepoint': chokepoint,
            'variable': variable,
            'latest_date': latest_date,
            'last_updated': datetime.utcnow().isoformat() + 'Z'
        }

        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

    def _get_latest_date(self, chokepoint: str, variable: str) -> str:
        """
        Get the latest collected date from metadata

        Args:
            chokepoint: Chokepoint ID
            variable: Variable name

        Returns:
            Latest date in YYYY-MM-DD format, or None if no metadata
        """
        data_dir = self.base_path / 'data' / 'logistics' / 'chokepoints' / chokepoint / variable
        metadata_path = data_dir / '_metadata.json'

        if not metadata_path.exists():
            return None

        with open(metadata_path, 'r') as f:
            metadata = json.load(f)

        return metadata.get('latest_date')

    def load_data(self, chokepoint: str, variable: str, date: str = None) -> Dict[str, Any]:
        """
        Load saved data from pickle file

        Args:
            chokepoint: Chokepoint ID
            variable: Variable name
            date: Date string (YYYY-MM-DD). If None, loads latest

        Returns:
            Loaded data
        """
        from datetime import datetime

        data_dir = self.base_path / 'data' / 'logistics' / 'chokepoints' / chokepoint / variable

        if not data_dir.exists():
            raise FileNotFoundError(f"Data directory not found: {data_dir}")

        if date is None:
            # Load latest file
            files = sorted(data_dir.glob('*.pckl'), reverse=True)
            if not files:
                raise FileNotFoundError(f"No data files found in: {data_dir}")
            file_path = files[0]
        else:
            file_path = data_dir / f'{date}.pckl'
            if not file_path.exists():
                raise FileNotFoundError(f"Data file not found: {file_path}")

        with open(file_path, 'rb') as f:
            return pickle.load(f)
