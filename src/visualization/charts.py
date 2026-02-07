"""
Visualization Charts Module
Provides various chart functions for vessel arrival data
"""
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Optional, Tuple


# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (14, 6)
plt.rcParams['font.size'] = 10


def load_data(csv_path: str) -> pd.DataFrame:
    """
    Load vessel arrival data from CSV

    Args:
        csv_path: Path to CSV file

    Returns:
        DataFrame with date as index
    """
    df = pd.read_csv(csv_path)
    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date')
    df = df.sort_index()
    return df


def plot_total_vessels_timeseries(
    df: pd.DataFrame,
    title: str = "Daily Vessel Arrivals - Bab el-Mandeb Strait",
    figsize: Tuple[int, int] = (14, 6)
) -> plt.Figure:
    """
    Plot total vessel count over time

    Args:
        df: DataFrame with vessel data
        title: Chart title
        figsize: Figure size (width, height)

    Returns:
        matplotlib Figure object
    """
    fig, ax = plt.subplots(figsize=figsize)

    ax.plot(df.index, df['vessel_count'], linewidth=1.5, color='#2E86AB', alpha=0.8)
    ax.fill_between(df.index, df['vessel_count'], alpha=0.3, color='#2E86AB')

    ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel('Number of Vessels', fontsize=12)
    ax.grid(True, alpha=0.3)

    # Add rolling average
    rolling_30 = df['vessel_count'].rolling(window=30, center=True).mean()
    ax.plot(df.index, rolling_30, linewidth=2, color='#A23B72',
            label='30-day Moving Average', linestyle='--')

    ax.legend(loc='upper left')
    plt.tight_layout()

    return fig


def plot_vessel_type_breakdown(
    df: pd.DataFrame,
    title: str = "Vessel Type Distribution Over Time",
    figsize: Tuple[int, int] = (14, 8)
) -> plt.Figure:
    """
    Plot stacked area chart of vessel types

    Args:
        df: DataFrame with vessel data
        title: Chart title
        figsize: Figure size

    Returns:
        matplotlib Figure object
    """
    fig, ax = plt.subplots(figsize=figsize)

    # Vessel types to plot
    vessel_types = ['container', 'tanker', 'dry_bulk', 'general_cargo', 'roro']
    colors = ['#F18F01', '#C73E1D', '#6A994E', '#2E86AB', '#BC4B51']

    ax.stackplot(
        df.index,
        [df[vtype] for vtype in vessel_types],
        labels=[vtype.replace('_', ' ').title() for vtype in vessel_types],
        colors=colors,
        alpha=0.8
    )

    ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel('Number of Vessels', fontsize=12)
    ax.legend(loc='upper left', framealpha=0.9)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    return fig


def plot_vessel_type_percentage(
    df: pd.DataFrame,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    title: str = "Vessel Type Distribution (%)",
    figsize: Tuple[int, int] = (10, 10)
) -> plt.Figure:
    """
    Plot pie chart of vessel type percentages

    Args:
        df: DataFrame with vessel data
        start_date: Optional start date filter (YYYY-MM-DD)
        end_date: Optional end date filter (YYYY-MM-DD)
        title: Chart title
        figsize: Figure size

    Returns:
        matplotlib Figure object
    """
    # Filter by date range if provided
    if start_date:
        df = df[df.index >= start_date]
    if end_date:
        df = df[df.index <= end_date]

    # Calculate totals for each vessel type
    vessel_types = ['container', 'tanker', 'dry_bulk', 'general_cargo', 'roro']
    totals = {vtype: df[vtype].sum() for vtype in vessel_types}

    # Create pie chart
    fig, ax = plt.subplots(figsize=figsize)

    colors = ['#F18F01', '#C73E1D', '#6A994E', '#2E86AB', '#BC4B51']
    labels = [vtype.replace('_', ' ').title() for vtype in vessel_types]
    values = [totals[vtype] for vtype in vessel_types]

    wedges, texts, autotexts = ax.pie(
        values,
        labels=labels,
        colors=colors,
        autopct='%1.1f%%',
        startangle=90,
        textprops={'fontsize': 12}
    )

    # Make percentage text bold
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
        autotext.set_fontsize(11)

    date_range = ""
    if start_date or end_date:
        date_range = f"\n({start_date or 'start'} to {end_date or 'end'})"

    ax.set_title(f"{title}{date_range}", fontsize=16, fontweight='bold', pad=20)

    plt.tight_layout()
    return fig


def plot_monthly_comparison(
    df: pd.DataFrame,
    years: Optional[list] = None,
    title: str = "Monthly Vessel Arrivals Comparison",
    figsize: Tuple[int, int] = (14, 6)
) -> plt.Figure:
    """
    Plot monthly comparison across different years

    Args:
        df: DataFrame with vessel data
        years: List of years to compare (default: last 3 years)
        title: Chart title
        figsize: Figure size

    Returns:
        matplotlib Figure object
    """
    # Add month column
    df_copy = df.copy()
    df_copy['year'] = df_copy.index.year
    df_copy['month'] = df_copy.index.month

    # Default to last 3 years if not specified
    if years is None:
        available_years = sorted(df_copy['year'].unique())
        years = available_years[-3:] if len(available_years) >= 3 else available_years

    fig, ax = plt.subplots(figsize=figsize)

    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    colors = plt.cm.Set2(range(len(years)))

    for i, year in enumerate(years):
        year_data = df_copy[df_copy['year'] == year]
        monthly_avg = year_data.groupby('month')['vessel_count'].mean()

        ax.plot(
            monthly_avg.index,
            monthly_avg.values,
            marker='o',
            linewidth=2,
            label=str(year),
            color=colors[i],
            markersize=8
        )

    ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Month', fontsize=12)
    ax.set_ylabel('Average Vessels per Day', fontsize=12)
    ax.set_xticks(range(1, 13))
    ax.set_xticklabels(month_names)
    ax.legend(loc='upper left')
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    return fig


def plot_weekly_pattern(
    df: pd.DataFrame,
    title: str = "Average Vessel Arrivals by Day of Week",
    figsize: Tuple[int, int] = (12, 6)
) -> plt.Figure:
    """
    Plot average vessel count by day of week

    Args:
        df: DataFrame with vessel data
        title: Chart title
        figsize: Figure size

    Returns:
        matplotlib Figure object
    """
    df_copy = df.copy()
    df_copy['day_of_week'] = df_copy.index.dayofweek

    # Calculate average by day of week
    weekly_avg = df_copy.groupby('day_of_week')['vessel_count'].agg(['mean', 'std'])

    fig, ax = plt.subplots(figsize=figsize)

    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

    bars = ax.bar(
        range(7),
        weekly_avg['mean'],
        yerr=weekly_avg['std'],
        color='#2E86AB',
        alpha=0.7,
        capsize=5
    )

    ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Day of Week', fontsize=12)
    ax.set_ylabel('Average Vessels', fontsize=12)
    ax.set_xticks(range(7))
    ax.set_xticklabels(days, rotation=45, ha='right')
    ax.grid(True, alpha=0.3, axis='y')

    # Add value labels on bars
    for i, bar in enumerate(bars):
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2.,
            height,
            f'{height:.1f}',
            ha='center',
            va='bottom',
            fontsize=10
        )

    plt.tight_layout()
    return fig


def plot_heatmap_monthly(
    df: pd.DataFrame,
    year: Optional[int] = None,
    title: str = "Daily Vessel Arrivals Heatmap",
    figsize: Tuple[int, int] = (16, 8)
) -> plt.Figure:
    """
    Plot heatmap of daily vessel arrivals by month and day

    Args:
        df: DataFrame with vessel data
        year: Specific year to plot (default: latest year)
        title: Chart title
        figsize: Figure size

    Returns:
        matplotlib Figure object
    """
    df_copy = df.copy()

    # Filter by year
    if year is None:
        year = df_copy.index.year.max()

    df_year = df_copy[df_copy.index.year == year]

    # Create pivot table
    df_year['month'] = df_year.index.month
    df_year['day'] = df_year.index.day

    pivot = df_year.pivot_table(
        values='vessel_count',
        index='day',
        columns='month',
        aggfunc='mean'
    )

    fig, ax = plt.subplots(figsize=figsize)

    sns.heatmap(
        pivot,
        cmap='YlOrRd',
        annot=False,
        fmt='.0f',
        cbar_kws={'label': 'Vessels'},
        ax=ax
    )

    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    ax.set_title(f"{title} ({year})", fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Month', fontsize=12)
    ax.set_ylabel('Day of Month', fontsize=12)
    ax.set_xticklabels(month_names, rotation=0)

    plt.tight_layout()
    return fig


def create_summary_stats(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create summary statistics table

    Args:
        df: DataFrame with vessel data

    Returns:
        DataFrame with summary statistics
    """
    stats = pd.DataFrame({
        'Metric': [
            'Total Days',
            'Date Range',
            'Total Vessels',
            'Average per Day',
            'Maximum in a Day',
            'Minimum in a Day',
            'Std Deviation'
        ],
        'Value': [
            len(df),
            f"{df.index.min().strftime('%Y-%m-%d')} to {df.index.max().strftime('%Y-%m-%d')}",
            f"{df['vessel_count'].sum():,}",
            f"{df['vessel_count'].mean():.2f}",
            f"{df['vessel_count'].max()}",
            f"{df['vessel_count'].min()}",
            f"{df['vessel_count'].std():.2f}"
        ]
    })

    return stats
