#!/usr/bin/env python3
"""
Auto-generate README data overview table
This script scans the chokepoints and generates a markdown table

Usage:
    python scripts/generate_readme_table.py
"""
from pathlib import Path
import json


def generate_data_overview():
    """Generate data overview table for README"""

    # Get all chokepoints with configs
    chokepoints = []
    base_path = Path(__file__).parent.parent

    for config_file in sorted((base_path / 'src/logistics/chokepoints').glob('*/state_variables.json')):
        chokepoint = config_file.parent.name
        with open(config_file) as f:
            config = json.load(f)

        # Count data files
        data_dir = base_path / 'data/logistics/chokepoints' / chokepoint
        total_files = 0
        date_range = None

        if data_dir.exists():
            for var in config.keys():
                var_dir = data_dir / var
                if var_dir.exists():
                    files = sorted(var_dir.glob('*.pckl'))
                    total_files += len(files)

                    # Get date range from filenames
                    if files and not date_range:
                        first_date = files[0].stem
                        last_date = files[-1].stem
                        date_range = f"{first_date} ~ {last_date}"

        chokepoints.append({
            'name': chokepoint,
            'variables': ', '.join(config.keys()),
            'count': total_files,
            'date_range': date_range or 'N/A',
            'status': '✅' if total_files > 0 else '⏳'
        })

    # Generate markdown table
    lines = []
    lines.append("| Chokepoint | Variables | Status | Data Files | Date Range |")
    lines.append("|------------|-----------|--------|------------|------------|")

    for cp in chokepoints:
        lines.append(f"| {cp['name']} | {cp['variables']} | {cp['status']} | {cp['count']:,} | {cp['date_range']} |")

    total_files = sum(cp['count'] for cp in chokepoints)
    lines.append("")
    lines.append(f"**總計:** {len(chokepoints)} 個航道監測點 | {total_files:,} 筆每日數據")

    return '\n'.join(lines)


if __name__ == '__main__':
    print(generate_data_overview())
