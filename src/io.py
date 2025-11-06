"""
Data I/O functions for Molise earthquake analysis.
"""

import pandas as pd
import pyreadstat
from pathlib import Path
import numpy as np


def load_raw(data_file=None, base_dir=None):
    """
    Load raw Stata data file.
    
    Parameters
    ----------
    data_file : str or Path, optional
        Path to .dta file. If None, uses Data/Molise.dta relative to base_dir.
    base_dir : str or Path, optional
        Base directory. If None, uses current working directory.
    
    Returns
    -------
    df : DataFrame
        Loaded data
    meta : dict
        Metadata from Stata file (value labels, etc.)
    """
    if base_dir is None:
        base_dir = Path.cwd()
    else:
        base_dir = Path(base_dir)
    
    if data_file is None:
        data_file = base_dir / "Data" / "Molise.dta"
    else:
        data_file = Path(data_file)
    
    try:
        df, meta = pyreadstat.read_dta(data_file)
        print(f"Loaded {len(df):,} rows using pyreadstat")
    except Exception as e:
        print(f"pyreadstat failed: {e}, trying pandas...")
        df = pd.read_stata(data_file)
        meta = None
        print(f"Loaded {len(df):,} rows using pandas")
    
    return df, meta


def write_parquet(df, path, partition_by=None):
    """
    Write DataFrame to Parquet format.
    
    Parameters
    ----------
    df : DataFrame
        Data to write
    path : str or Path
        Output path
    partition_by : str, optional
        Column name to partition by (e.g., 'year')
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    if partition_by and partition_by in df.columns:
        # Partition by specified column
        for val in df[partition_by].unique():
            subset = df[df[partition_by] == val]
            part_path = path.parent / f"{path.stem}_{partition_by}={val}{path.suffix}"
            subset.to_parquet(part_path, index=False)
        print(f"Wrote partitioned parquet files to {path.parent}")
    else:
        df.to_parquet(path, index=False)
        print(f"Wrote parquet file to {path}")


def read_parquet(path):
    """Read Parquet file."""
    return pd.read_parquet(path)
