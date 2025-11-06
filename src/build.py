"""
Variable construction functions for Molise earthquake analysis.
"""

import pandas as pd
import numpy as np
from scipy.stats import mstats


def construct_worker_type(df, type_col='type'):
    """
    Construct worker_type categorical variable.
    
    Parameters
    ----------
    df : DataFrame
        Input data
    type_col : str
        Column name for raw worker type (1=Private, 2=Public, 3=Self, 4=Non-employed)
    
    Returns
    -------
    Series
        Categorical worker_type: 'private', 'public', 'self', 'non_employed'
    """
    worker_type_map = {
        1: 'private',
        2: 'public',
        3: 'self',
        4: 'non_employed'
    }
    
    worker_type = df[type_col].map(worker_type_map)
    worker_type = pd.Categorical(worker_type, categories=['public', 'private', 'self', 'non_employed'], ordered=False)
    
    return worker_type


def make_outcomes(df, wage_col='wage', contract_col='contract_type', 
                  working_weeks_col='working_weeks', year_col='year'):
    """
    Construct outcome variables.
    
    Parameters
    ----------
    df : DataFrame
        Input data
    wage_col : str
        Column name for wage
    contract_col : str
        Column name for contract type
    working_weeks_col : str
        Column name for working weeks
    year_col : str
        Column name for year
    
    Returns
    -------
    DataFrame
        DataFrame with outcome variables
    """
    outcomes = pd.DataFrame(index=df.index)
    
    # Convert wage to numeric (handle object type)
    if df[wage_col].dtype == 'object':
        wage_numeric = pd.to_numeric(df[wage_col], errors='coerce')
    else:
        wage_numeric = df[wage_col]
    
    # Employment probability: 1 if has wage or working_weeks > 0
    outcomes['emp_prob'] = (
        (wage_numeric.notna() & (wage_numeric > 0)) | 
        (df[working_weeks_col].notna() & (pd.to_numeric(df[working_weeks_col], errors='coerce') > 0))
    ).astype(int)
    
    # Annualized monthly earnings (wage * 12, or wage * working_weeks/52 * 12)
    if working_weeks_col in df.columns:
        weeks = pd.to_numeric(df[working_weeks_col], errors='coerce').fillna(52)
        earnings_annual = wage_numeric * (weeks / 52) * 12
    else:
        earnings_annual = wage_numeric * 12
    
    # Winsorize earnings at p1-p99
    earnings_winsorized = earnings_annual.copy()
    p1 = earnings_annual.quantile(0.01)
    p99 = earnings_annual.quantile(0.99)
    earnings_winsorized = earnings_winsorized.clip(lower=p1, upper=p99)
    
    # Inverse hyperbolic sine transformation
    outcomes['earnings_asinh'] = np.arcsinh(earnings_winsorized)
    
    # Wage (daily equivalent if needed, or monthly)
    outcomes['wage_asinh'] = np.arcsinh(wage_numeric.clip(lower=wage_numeric.quantile(0.01), 
                                                           upper=wage_numeric.quantile(0.99)))
    
    # Permanent contract indicator
    if contract_col in df.columns:
        # 1 = Permanent
        outcomes['contract_perm'] = (pd.to_numeric(df[contract_col], errors='coerce') == 1).astype(int)
    else:
        outcomes['contract_perm'] = 0
    
    # Contract duration (if date_start and date_end available)
    if 'date_start' in df.columns and 'date_end' in df.columns:
        try:
            date_start = pd.to_datetime(df['date_start'], errors='coerce')
            date_end = pd.to_datetime(df['date_end'], errors='coerce')
            outcomes['contract_duration_days'] = (date_end - date_start).dt.days
            outcomes['contract_duration_days'] = outcomes['contract_duration_days'].fillna(0)
        except:
            outcomes['contract_duration_days'] = 0
    else:
        outcomes['contract_duration_days'] = 0
    
    return outcomes


def make_flags(df, person_id_col='id_worker', year_col='year', 
               region_col='region_res', municipality_col=None):
    """
    Create sample flags: balanced panel, stayers, border municipalities.
    
    Parameters
    ----------
    df : DataFrame
        Input data
    person_id_col : str
        Person identifier column
    year_col : str
        Year column
    region_col : str
        Region column
    municipality_col : str, optional
        Municipality column (if available)
    
    Returns
    -------
    DataFrame
        DataFrame with flags
    """
    flags = pd.DataFrame(index=df.index)
    
    # Balanced panel: present in all years 1997-2007 (excluding 2002)
    required_years = set(range(1997, 2002)) | set(range(2003, 2008))
    person_years = df.groupby(person_id_col)[year_col].apply(set)
    flags['is_balanced_97_07'] = person_years.map(lambda x: required_years.issubset(x)).reindex(df[person_id_col]).values
    
    # Stayer: no inter-municipality moves (if municipality data available)
    if municipality_col and municipality_col in df.columns:
        person_municipalities = df.groupby(person_id_col)[municipality_col].nunique()
        flags['is_stayer_residence'] = (person_municipalities == 1).reindex(df[person_id_col]).values
    else:
        flags['is_stayer_residence'] = True  # Assume all stayers if no municipality data
    
    # Border municipality (placeholder - would need actual border data)
    flags['is_border_municipality'] = False
    
    return flags


def assemble_panel(df, meta=None):
    """
    Assemble analysis-ready panel from raw data.
    
    Parameters
    ----------
    df : DataFrame
        Raw data
    meta : dict, optional
        Metadata from Stata file
    
    Returns
    -------
    DataFrame
        Analysis-ready panel
    """
    panel = df.copy()
    
    # Compute age
    if 'year_birth' in panel.columns:
        panel['age'] = panel['year'] - panel['year_birth']
        panel['age_sq'] = panel['age'] ** 2
    else:
        panel['age'] = np.nan
        panel['age_sq'] = np.nan
    
    # Construct worker type
    panel['worker_type'] = construct_worker_type(panel, type_col='type')
    
    # Filter to employed workers only (exclude type 4 = non-employed)
    panel = panel[panel['worker_type'] != 'non_employed'].copy()
    
    # Treatment variables
    # molise_res: 1 if region_res == 12 (Molise), 0 if region_res == 2 (Basilicata)
    panel['molise_res'] = (panel['region_res'] == '12').astype(int)
    
    # post: 1 if year >= 2003
    panel['post'] = (panel['year'] >= 2003).astype(int)
    
    # treat: interaction
    panel['treat'] = panel['molise_res'] * panel['post']
    
    # event_time: year - 2002
    panel['event_time'] = panel['year'] - 2002
    
    # Filter to analysis period: 1997-2001 and 2003-2007 (exclude 2002)
    panel = panel[panel['year'].between(1997, 2007) & (panel['year'] != 2002)].copy()
    
    # Filter to Molise (12) or Basilicata (2) residents
    panel = panel[panel['region_res'].isin(['12', '2'])].copy()
    
    # Make outcomes
    outcomes = make_outcomes(panel)
    for col in outcomes.columns:
        panel[col] = outcomes[col]
    
    # Make flags
    flags = make_flags(panel)
    for col in flags.columns:
        panel[col] = flags[col]
    
    # Fix molise_res based on pre-period (1997-2001) residence
    pre_period = panel[panel['year'] < 2002].copy()
    if len(pre_period) > 0:
        pre_residence = pre_period.groupby('id_worker')['molise_res'].first()
        panel['molise_res'] = pre_residence.reindex(panel['id_worker']).fillna(panel['molise_res']).values
    
    return panel
