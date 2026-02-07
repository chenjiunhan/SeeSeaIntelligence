"""
Daily Data Collection Scheduler
Automatically collects data based on state_variables.json configurations
"""
import json
from pathlib import Path
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

import sys
sys.path.insert(0, str(Path(__file__).parent))

from core.collector import DataCollector
from core.backfill import BackfillManager
from core.processor import DataProcessor
from core.logger import setup_logger, setup_apscheduler_logging

# Setup logging
logger = setup_logger(__name__)
setup_apscheduler_logging()


class CollectionScheduler:
    """Scheduler for automated data collection"""

    def __init__(self, base_path: Path = None):
        """
        Initialize scheduler

        Args:
            base_path: Base path for the project
        """
        if base_path is None:
            self.base_path = Path(__file__).parent.parent
        else:
            self.base_path = Path(base_path)

        self.collector = DataCollector(self.base_path)
        self.backfill_manager = BackfillManager(self.base_path)
        self.processor = DataProcessor(self.base_path)
        self.scheduler = BlockingScheduler()

    def load_all_configs(self):
        """
        Load all state_variables.json configs from all chokepoints

        Returns:
            List of (chokepoint, variable, config) tuples
        """
        configs = []
        chokepoints_dir = self.base_path / 'src' / 'logistics' / 'chokepoints'

        if not chokepoints_dir.exists():
            print(f"❌ Chokepoints directory not found: {chokepoints_dir}")
            return configs

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

                for variable_name, variable_config in config.items():
                    configs.append((chokepoint_id, variable_name, variable_config))

            except Exception as e:
                print(f"❌ Error loading config for {chokepoint_id}: {e}")

        return configs

    def collect_data(self, chokepoint: str, variable: str):
        """
        Collect data for a specific variable and process to CSV

        Args:
            chokepoint: Chokepoint ID
            variable: Variable name
        """
        try:
            print(f"\n🔄 [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Collecting {chokepoint}/{variable}...")
            data = self.collector.collect(chokepoint, variable)
            print(f"   ✅ Collection success: {data.get('value')}")

            # Process to CSV
            print(f"   📊 Processing to CSV...")
            csv_path = self.processor.process_to_csv(chokepoint, variable)
            print(f"   ✅ CSV updated: {csv_path}")

        except Exception as e:
            print(f"   ❌ Error: {e}")

    def schedule_all(self):
        """
        Schedule all data collection tasks based on configs
        """
        configs = self.load_all_configs()

        if not configs:
            print("❌ No configurations found!")
            return

        print(f"\n📅 Scheduling {len(configs)} collection tasks...")

        for chokepoint, variable, config in configs:
            update_freq = config.get('update_freq', 'daily')

            # Get custom schedule time (optional)
            schedule_hour = config.get('schedule_hour')
            schedule_minute = config.get('schedule_minute', 0)

            # Map update frequency to cron schedule
            if update_freq == 'test':
                # Run every minute (for testing)
                trigger = CronTrigger(minute='*')
            elif update_freq == 'realtime':
                # Run every minute
                trigger = CronTrigger(minute='*')
            elif update_freq == '15min':
                # Run every 15 minutes
                trigger = CronTrigger(minute='*/15')
            elif update_freq == 'hourly':
                # Run every hour at specified minute
                trigger = CronTrigger(minute=schedule_minute)
            elif update_freq == 'daily':
                # Run daily at specified time (default 00:00 UTC)
                hour = schedule_hour if schedule_hour is not None else 0
                trigger = CronTrigger(hour=hour, minute=schedule_minute)
            elif update_freq == 'weekly':
                # Run weekly on Monday at specified time
                hour = schedule_hour if schedule_hour is not None else 0
                trigger = CronTrigger(day_of_week='mon', hour=hour, minute=schedule_minute)
            elif update_freq == 'monthly':
                # Run monthly on 1st at specified time
                hour = schedule_hour if schedule_hour is not None else 0
                trigger = CronTrigger(day=1, hour=hour, minute=schedule_minute)
            else:
                print(f"   ⚠️  Unknown frequency '{update_freq}' for {chokepoint}/{variable}, defaulting to daily")
                trigger = CronTrigger(hour=0, minute=0)

            # Add job to scheduler
            self.scheduler.add_job(
                self.collect_data,
                trigger=trigger,
                args=[chokepoint, variable],
                id=f"{chokepoint}_{variable}",
                name=f"Collect {chokepoint}/{variable}",
                replace_existing=True
            )

            # Show schedule time for daily/weekly/monthly
            if update_freq in ['daily', 'weekly', 'monthly'] and schedule_hour is not None:
                print(f"   ✓ Scheduled {chokepoint}/{variable} ({update_freq} at {schedule_hour:02d}:{schedule_minute:02d} UTC)")
            else:
                print(f"   ✓ Scheduled {chokepoint}/{variable} ({update_freq})")

    def run_once_now(self):
        """
        Run all collection tasks once immediately (for testing)
        """
        configs = self.load_all_configs()

        print(f"\n🚀 Running {len(configs)} collection tasks now...")

        for chokepoint, variable, config in configs:
            self.collect_data(chokepoint, variable)

    def check_and_backfill(self):
        """
        Check for missing dates and report (but don't backfill automatically)

        Note: Since we can only collect current data, we show what's missing
        but don't attempt to backfill historical data
        """
        print("\n🔍 Checking for missing dates...")

        missing_data = self.backfill_manager.get_all_missing_dates()

        if not missing_data:
            print("   ✅ No missing dates found!")
            return

        print(f"\n📋 Found missing data for {len(missing_data)} variables:")

        for (chokepoint, variable), missing_dates in missing_data.items():
            print(f"\n   {chokepoint}/{variable}:")
            print(f"      Missing {len(missing_dates)} dates")
            if len(missing_dates) <= 5:
                print(f"      Dates: {', '.join(missing_dates)}")
            else:
                print(f"      Range: {missing_dates[0]} to {missing_dates[-1]}")

        print("\n💡 Note: Historical data cannot be backfilled from this source.")
        print("   Data will accumulate as we collect daily going forward.")

    def start(self):
        """
        Start the scheduler
        """
        print("\n" + "="*60)
        print("🕐 Scheduler started")
        print("="*60)
        print("\n📋 Scheduled jobs:")

        for job in self.scheduler.get_jobs():
            print(f"   - {job.name}")

        print("\n⏸️  Press Ctrl+C to stop\n")

        try:
            self.scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            print("\n\n🛑 Scheduler stopped")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='SeeSeaAgent Data Collection Scheduler')
    parser.add_argument('--once', action='store_true', help='Run all collections once and exit')
    parser.add_argument('--start', action='store_true', help='Start the scheduler')
    parser.add_argument('--check', action='store_true', help='Check for missing dates')

    args = parser.parse_args()

    scheduler = CollectionScheduler()

    if args.once:
        # Run once and exit
        scheduler.run_once_now()
    elif args.start:
        # Schedule and keep running
        scheduler.schedule_all()
        scheduler.start()
    elif args.check:
        # Check for missing dates
        scheduler.check_and_backfill()
    else:
        # Default: show help
        parser.print_help()


if __name__ == '__main__':
    main()
