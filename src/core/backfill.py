"""
Backfill missing dates for data collection
"""
from pathlib import Path
from datetime import datetime, timedelta
from typing import List
import json


class BackfillManager:
    """Manages backfilling of missing data"""

    def __init__(self, base_path: Path = None):
        """
        Initialize backfill manager

        Args:
            base_path: Base path for the project
        """
        if base_path is None:
            self.base_path = Path(__file__).parent.parent.parent
        else:
            self.base_path = Path(base_path)

    def get_missing_dates(self, chokepoint: str, variable: str, start_date: str = None) -> List[str]:
        """
        Get list of missing dates for a variable

        Args:
            chokepoint: Chokepoint ID
            variable: Variable name
            start_date: Start date (YYYY-MM-DD). If None, uses 30 days ago

        Returns:
            List of missing date strings (YYYY-MM-DD)
        """
        data_dir = self.base_path / 'data' / 'logistics' / 'chokepoints' / chokepoint / variable

        # Determine start date
        if start_date is None:
            # Default: check last 30 days
            start = datetime.utcnow() - timedelta(days=30)
        else:
            start = datetime.strptime(start_date, '%Y-%m-%d')

        end = datetime.utcnow()

        # Generate all dates in range
        all_dates = []
        current = start
        while current <= end:
            all_dates.append(current.strftime('%Y-%m-%d'))
            current += timedelta(days=1)

        # Check which dates are missing
        missing_dates = []

        if not data_dir.exists():
            # No data at all - all dates are missing
            return all_dates

        existing_files = set(f.stem for f in data_dir.glob('*.pckl'))

        for date_str in all_dates:
            if date_str not in existing_files:
                missing_dates.append(date_str)

        return missing_dates

    def get_all_missing_dates(self) -> dict:
        """
        Get all missing dates for all chokepoints and variables

        Returns:
            Dictionary of {(chokepoint, variable): [missing_dates]}
        """
        missing_data = {}
        chokepoints_dir = self.base_path / 'src' / 'logistics' / 'chokepoints'

        if not chokepoints_dir.exists():
            return missing_data

        # Scan all chokepoint directories
        for chokepoint_dir in chokepoints_dir.iterdir():
            if not chokepoint_dir.is_dir():
                continue

            config_file = chokepoint_dir / 'state_variables.json'
            if not config_file.exists():
                continue

            chokepoint_id = chokepoint_dir.name

            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)

                for variable_name in config.keys():
                    missing = self.get_missing_dates(chokepoint_id, variable_name)
                    if missing:
                        missing_data[(chokepoint_id, variable_name)] = missing

            except Exception as e:
                print(f"❌ Error loading config for {chokepoint_id}: {e}")

        return missing_data

    def needs_backfill(self, chokepoint: str, variable: str) -> bool:
        """
        Check if a variable needs backfilling

        Args:
            chokepoint: Chokepoint ID
            variable: Variable name

        Returns:
            True if missing dates exist
        """
        missing = self.get_missing_dates(chokepoint, variable)
        return len(missing) > 0
