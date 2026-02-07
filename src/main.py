"""
Main entry point for data collection
"""
import argparse
import json
from pathlib import Path

from core.collector import DataCollector


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='SeeSeaAgent Data Collector')
    parser.add_argument('--chokepoint', required=True, help='Chokepoint ID (e.g., bab-el-mandeb)')
    parser.add_argument('--variable', required=True, help='Variable name (e.g., transit_status)')
    parser.add_argument('--show', action='store_true', help='Show collected data')

    args = parser.parse_args()

    collector = DataCollector()

    print(f"🔍 Collecting data for {args.chokepoint}/{args.variable}...")

    try:
        data = collector.collect(args.chokepoint, args.variable)

        print(f"\n📊 Collection Result:")
        print(f"   Status: {data.get('status')}")
        print(f"   Value: {data.get('value')}")
        print(f"   Timestamp: {data.get('timestamp')}")

        if data.get('note'):
            print(f"   Note: {data.get('note')}")

        if data.get('error'):
            print(f"   ❌ Error: {data.get('error')}")

        if args.show:
            print(f"\n📄 Full Data:")
            print(json.dumps(data, indent=2, ensure_ascii=False))

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
