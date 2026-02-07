"""
Data Processing Script
Process raw pickle data to CSV/JSON format
"""
import argparse
from pathlib import Path
from core.processor import DataProcessor


def main():
    parser = argparse.ArgumentParser(description='Process raw data to CSV/JSON')

    parser.add_argument(
        '--chokepoint',
        type=str,
        default='bab-el-mandeb',
        help='Chokepoint ID (default: bab-el-mandeb)'
    )

    parser.add_argument(
        '--variable',
        type=str,
        default='vessel_arrivals',
        help='Variable name (default: vessel_arrivals)'
    )

    parser.add_argument(
        '--format',
        type=str,
        choices=['csv', 'json', 'both'],
        default='csv',
        help='Output format (default: csv)'
    )

    parser.add_argument(
        '--incremental',
        action='store_true',
        help='Only process new data (default: False)'
    )

    parser.add_argument(
        '--full',
        action='store_true',
        help='Process all data from scratch (default: False)'
    )

    args = parser.parse_args()

    # Initialize processor
    processor = DataProcessor()

    print(f'📊 Processing {args.chokepoint} / {args.variable}')
    print(f'   Format: {args.format}')
    print(f'   Mode: {"Incremental" if args.incremental else "Full"}')
    print()

    try:
        # Process to CSV
        if args.format in ['csv', 'both']:
            incremental = args.incremental and not args.full
            csv_path = processor.process_to_csv(
                args.chokepoint,
                args.variable,
                incremental=incremental
            )
            print(f'\n✅ CSV: {csv_path}')

        # Process to JSON
        if args.format in ['json', 'both']:
            json_path = processor.process_to_json(
                args.chokepoint,
                args.variable,
                format='records'
            )
            print(f'\n✅ JSON: {json_path}')

        print('\n✅ Processing complete!')

    except Exception as e:
        print(f'\n❌ Error: {e}')
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
