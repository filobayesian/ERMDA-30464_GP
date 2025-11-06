"""
Diagnostic functions.
"""

import pandas as pd
import numpy as np
from scipy import stats


def pretrend_test(event_df):
    """
    Test for parallel trends in pre-period.
    
    Parameters
    ----------
    event_df : DataFrame
        Event-study results
    
    Returns
    -------
    dict
        Test statistics and p-values
    """
    # Filter to pre-period (event_time < 0)
    pre = event_df[event_df['event_time'] < 0].copy()
    
    if len(pre) == 0:
        return {'test_stat': np.nan, 'p_value': np.nan}
    
    # Test if sum of pre-period coefficients is zero
    # This is a simplified version - full implementation would use F-test
    coefs = pre['beta'].values
    ses = pre['se'].values
    
    # Wald test
    test_stat = (coefs.sum() ** 2) / (ses ** 2).sum()
    p_value = 1 - stats.chi2.cdf(test_stat, df=len(coefs))
    
    return {'test_stat': test_stat, 'p_value': p_value, 'n_pre_periods': len(pre)}


def cell_counts(df, keys):
    """
    Count observations by cell (e.g., region × type × year).
    
    Parameters
    ----------
    df : DataFrame
        Data
    keys : list of str
        Column names to group by
    
    Returns
    -------
    DataFrame
        Cell counts
    """
    counts = df.groupby(keys).size().reset_index(name='count')
    return counts

