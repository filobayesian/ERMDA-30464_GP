"""
Plotting functions for Molise earthquake analysis.
"""

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from pathlib import Path


def plot_event(results_df, title, outfile, by_type=False):
    """
    Plot event-study coefficients with confidence intervals.
    
    Parameters
    ----------
    results_df : DataFrame
        Results from event_study()
    title : str
        Plot title
    outfile : str or Path
        Output file path
    by_type : bool
        If True, plot separate lines for each worker type
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    
    if by_type and 'worker_type' in results_df.columns:
        for worker_type in results_df['worker_type'].unique():
            data = results_df[results_df['worker_type'] == worker_type].sort_values('event_time')
            ax.plot(data['event_time'], data['beta'], marker='o', label=worker_type)
            ax.fill_between(data['event_time'], data['ci_low'], data['ci_high'], alpha=0.2)
    else:
        data = results_df.sort_values('event_time')
        ax.plot(data['event_time'], data['beta'], marker='o', color='blue')
        ax.fill_between(data['event_time'], data['ci_low'], data['ci_high'], alpha=0.2)
    
    ax.axhline(y=0, color='black', linestyle='--', linewidth=0.5)
    ax.axvline(x=0, color='red', linestyle='--', linewidth=0.5, label='Earthquake')
    ax.set_xlabel('Event Time (Years from 2002)')
    ax.set_ylabel('Coefficient')
    ax.set_title(title)
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    outfile = Path(outfile)
    outfile.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(outfile, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved plot to {outfile}")


def plot_three_env(tables, outfile):
    """Plot three environments analysis."""
    # Placeholder - will implement in Phase 3
    pass


def plot_heatmap(grid, outfile):
    """Plot coefficient heatmap for heterogeneity analysis."""
    # Placeholder - will implement in Phase 3
    pass
