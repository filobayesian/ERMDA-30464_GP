"""
Data I/O functions for Molise earthquake analysis.
"""

import pandas as pd
import pyreadstat
from pathlib import Path
import numpy as np


def load_raw(data_file=None, base_dir=None, load_both_regions=True):
    """
    Load raw Stata data file(s).
    
    Parameters
    ----------
    data_file : str or Path, optional
        Path to .dta file. If None and load_both_regions=True, loads both
        Data/Molise.dta and Data/Basilicata.dta. If None and load_both_regions=False,
        uses Data/Molise.dta relative to base_dir.
    base_dir : str or Path, optional
        Base directory. If None, uses current working directory.
    load_both_regions : bool, default True
        If True, loads both Molise and Basilicata datasets and combines them.
    
    Returns
    -------
    df : DataFrame
        Loaded data (combined if load_both_regions=True)
    meta : dict
        Metadata from Stata file (value labels, etc.) - from first file loaded
    """
    if base_dir is None:
        base_dir = Path.cwd()
    else:
        base_dir = Path(base_dir)
    
    if load_both_regions and data_file is None:
        # Load both Molise and Basilicata datasets
        molise_file = base_dir / "Data" / "Molise.dta"
        basilicata_file = base_dir / "Data" / "Basilicata.dta"
        
        dfs = []
        meta = None
        
        # Load Molise
        if molise_file.exists():
            try:
                df_molise, meta = pyreadstat.read_dta(molise_file)
                print(f"Loaded Molise: {len(df_molise):,} rows using pyreadstat")
            except Exception as e:
                print(f"pyreadstat failed for Molise: {e}, trying pandas...")
                df_molise = pd.read_stata(molise_file)
                meta = None
                print(f"Loaded Molise: {len(df_molise):,} rows using pandas")
            
            # Ensure region_res is set to 12 for Molise
            if 'region_res' in df_molise.columns:
                df_molise['region_res'] = '12'
            else:
                df_molise['region_res'] = '12'
            
            dfs.append(df_molise)
        else:
            print(f"Warning: {molise_file} not found")
        
        # Load Basilicata
        if basilicata_file.exists():
            try:
                df_basilicata, meta_bas = pyreadstat.read_dta(basilicata_file)
                print(f"Loaded Basilicata: {len(df_basilicata):,} rows using pyreadstat")
            except Exception as e:
                print(f"pyreadstat failed for Basilicata: {e}, trying pandas...")
                df_basilicata = pd.read_stata(basilicata_file)
                print(f"Loaded Basilicata: {len(df_basilicata):,} rows using pandas")
            
            # Ensure region_res is set to 2 for Basilicata
            if 'region_res' in df_basilicata.columns:
                df_basilicata['region_res'] = '2'
            else:
                df_basilicata['region_res'] = '2'
            
            dfs.append(df_basilicata)
        else:
            print(f"Warning: {basilicata_file} not found")
        
        if len(dfs) == 0:
            raise FileNotFoundError("No data files found")
        
        # Combine datasets
        df = pd.concat(dfs, ignore_index=True)
        print(f"\nCombined dataset: {len(df):,} rows")
        print(f"Region distribution:")
        print(df['region_res'].value_counts())
        
        return df, meta
    
    else:
        # Load single file (original behavior)
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
