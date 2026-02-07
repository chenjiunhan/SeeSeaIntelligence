"""
Data Processor
Converts raw pickle data to CSV/JSON format with incremental processing
"""
import json
import csv
import pickle
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime


class DataProcessor:
    """Process raw data into structured formats (CSV/JSON)"""

    def __init__(self, base_path: Path = None):
        """
        Initialize processor

        Args:
            base_path: Base path for the project (defaults to project root)
        """
        if base_path is None:
            # Assume we're in src/core, go up two levels
            self.base_path = Path(__file__).parent.parent.parent
        else:
            self.base_path = Path(base_path)

    def process_to_csv(self, chokepoint: str, variable: str, incremental: bool = True) -> str:
        """
        Process pickle files to CSV format

        Args:
            chokepoint: Chokepoint ID (e.g., 'bab-el-mandeb')
            variable: Variable name (e.g., 'vessel_arrivals')
            incremental: If True, only process new files since last run

        Returns:
            Path to the generated CSV file
        """
        # Get raw data directory
        raw_dir = self.base_path / 'data' / 'logistics' / 'chokepoints' / chokepoint / variable

        if not raw_dir.exists():
            raise FileNotFoundError(f"Raw data directory not found: {raw_dir}")

        # Create processed data directory
        processed_dir = self.base_path / 'processed' / 'logistics' / 'chokepoints' / chokepoint / variable
        processed_dir.mkdir(parents=True, exist_ok=True)

        # CSV file path
        csv_path = processed_dir / f'{variable}.csv'

        # Get list of pickle files to process
        pickle_files = sorted(raw_dir.glob('*.pckl'))

        if not pickle_files:
            raise FileNotFoundError(f"No pickle files found in: {raw_dir}")

        # If incremental, check which files have already been processed
        processed_dates = set()
        if incremental and csv_path.exists():
            processed_dates = self._get_processed_dates_from_csv(csv_path)
            print(f"   📊 Found {len(processed_dates)} existing records in CSV")

        # Collect all data
        all_data = []
        new_count = 0

        for pickle_file in pickle_files:
            # Skip metadata file
            if pickle_file.name.startswith('_'):
                continue

            date_str = pickle_file.stem  # e.g., '2026-01-25'

            # Skip if already processed
            if date_str in processed_dates:
                continue

            # Load pickle file
            with open(pickle_file, 'rb') as f:
                data = pickle.load(f)

            # Skip if data doesn't have the expected structure
            if not isinstance(data, dict) or 'date' not in data:
                print(f"   ⚠️  Skipping {pickle_file.name}: invalid structure")
                continue

            # Convert to flat structure for CSV
            row = {
                'date': data.get('date', date_str),
                'vessel_count': data.get('vessel_count', 0),
                'container': data.get('breakdown', {}).get('container', 0),
                'dry_bulk': data.get('breakdown', {}).get('dry_bulk', 0),
                'general_cargo': data.get('breakdown', {}).get('general_cargo', 0),
                'roro': data.get('breakdown', {}).get('roro', 0),
                'tanker': data.get('breakdown', {}).get('tanker', 0),
                'collected_at': data.get('collected_at', ''),
                'chokepoint': data.get('chokepoint', chokepoint),
                'variable': data.get('variable', variable)
            }

            all_data.append(row)
            new_count += 1

        # If incremental and we have new data, append to existing CSV
        if incremental and csv_path.exists() and new_count > 0:
            print(f"   💾 Appending {new_count} new records to CSV...")

            # Check if file ends with newline, add one if not
            with open(csv_path, 'rb') as f:
                f.seek(-1, 2)  # Go to last byte
                last_char = f.read(1)
                needs_newline = last_char != b'\n'

            with open(csv_path, 'a', newline='', encoding='utf-8') as f:
                # Add newline if the last line doesn't have one
                if needs_newline:
                    f.write('\n')

                if all_data:
                    writer = csv.DictWriter(f, fieldnames=all_data[0].keys())
                    writer.writerows(all_data)

        # Otherwise, write full CSV (including existing data)
        elif all_data:
            # If we're not in incremental mode or file doesn't exist, reload all data
            if not incremental or not csv_path.exists():
                print(f"   💾 Writing full CSV with {len(pickle_files)} records...")
                all_data = []

                for pickle_file in pickle_files:
                    if pickle_file.name.startswith('_'):
                        continue

                    with open(pickle_file, 'rb') as f:
                        data = pickle.load(f)

                    row = {
                        'date': data['date'],
                        'vessel_count': data['vessel_count'],
                        'container': data['breakdown']['container'],
                        'dry_bulk': data['breakdown']['dry_bulk'],
                        'general_cargo': data['breakdown']['general_cargo'],
                        'roro': data['breakdown']['roro'],
                        'tanker': data['breakdown']['tanker'],
                        'collected_at': data['collected_at'],
                        'chokepoint': data['chokepoint'],
                        'variable': data['variable']
                    }
                    all_data.append(row)

            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                if all_data:
                    writer = csv.DictWriter(f, fieldnames=all_data[0].keys())
                    writer.writeheader()
                    writer.writerows(all_data)

            print(f"   ✅ CSV written: {csv_path}")
        else:
            print(f"   ℹ️ No new data to process")

        # Update processing metadata
        self._update_processing_metadata(chokepoint, variable, 'csv', len(all_data))

        return str(csv_path)

    def process_to_json(self, chokepoint: str, variable: str, format: str = 'records') -> str:
        """
        Process pickle files to JSON format

        Args:
            chokepoint: Chokepoint ID
            variable: Variable name
            format: JSON format - 'records' (array of objects) or 'timeseries' (date->data mapping)

        Returns:
            Path to the generated JSON file
        """
        # Get raw data directory
        raw_dir = self.base_path / 'data' / 'logistics' / 'chokepoints' / chokepoint / variable

        if not raw_dir.exists():
            raise FileNotFoundError(f"Raw data directory not found: {raw_dir}")

        # Create processed data directory
        processed_dir = self.base_path / 'processed' / 'logistics' / 'chokepoints' / chokepoint / variable
        processed_dir.mkdir(parents=True, exist_ok=True)

        # JSON file path
        json_path = processed_dir / f'{variable}.json'

        # Get list of pickle files
        pickle_files = sorted(raw_dir.glob('*.pckl'))

        if not pickle_files:
            raise FileNotFoundError(f"No pickle files found in: {raw_dir}")

        print(f"   💾 Processing {len(pickle_files)} files to JSON...")

        # Collect all data
        if format == 'records':
            # Array of objects format
            all_data = []

            for pickle_file in pickle_files:
                if pickle_file.name.startswith('_'):
                    continue

                with open(pickle_file, 'rb') as f:
                    data = pickle.load(f)

                all_data.append({
                    'date': data['date'],
                    'vessel_count': data['vessel_count'],
                    'breakdown': data['breakdown'],
                    'collected_at': data['collected_at']
                })

            output = {
                'chokepoint': chokepoint,
                'variable': variable,
                'total_records': len(all_data),
                'date_range': {
                    'start': all_data[0]['date'] if all_data else None,
                    'end': all_data[-1]['date'] if all_data else None
                },
                'processed_at': datetime.utcnow().isoformat() + 'Z',
                'data': all_data
            }

        else:  # timeseries format
            # Date -> data mapping
            timeseries = {}

            for pickle_file in pickle_files:
                if pickle_file.name.startswith('_'):
                    continue

                with open(pickle_file, 'rb') as f:
                    data = pickle.load(f)

                timeseries[data['date']] = {
                    'vessel_count': data['vessel_count'],
                    'breakdown': data['breakdown'],
                    'collected_at': data['collected_at']
                }

            output = {
                'chokepoint': chokepoint,
                'variable': variable,
                'total_records': len(timeseries),
                'processed_at': datetime.utcnow().isoformat() + 'Z',
                'timeseries': timeseries
            }

        # Write JSON
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        print(f"   ✅ JSON written: {json_path}")

        # Update processing metadata
        self._update_processing_metadata(chokepoint, variable, 'json', len(pickle_files))

        return str(json_path)

    def _get_processed_dates_from_csv(self, csv_path: Path) -> set:
        """
        Read existing CSV and extract all dates that have been processed

        Args:
            csv_path: Path to CSV file

        Returns:
            Set of date strings
        """
        dates = set()

        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                dates.add(row['date'])

        return dates

    def _update_processing_metadata(self, chokepoint: str, variable: str, format: str, record_count: int):
        """
        Update metadata about processing

        Args:
            chokepoint: Chokepoint ID
            variable: Variable name
            format: Output format (csv/json)
            record_count: Number of records processed
        """
        processed_dir = self.base_path / 'processed' / 'logistics' / 'chokepoints' / chokepoint / variable
        metadata_path = processed_dir / f'_processing_metadata.json'

        # Load existing metadata if it exists
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
        else:
            metadata = {}

        # Update metadata for this format
        metadata[format] = {
            'last_processed': datetime.utcnow().isoformat() + 'Z',
            'record_count': record_count
        }

        # Save metadata
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
