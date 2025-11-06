"""
Estimation functions for DiD, DDD, and event-study models.
"""

import pandas as pd
import numpy as np
from linearmodels import PanelOLS
from linearmodels.panel import compare
import statsmodels.api as sm


def did(df, outcome, cluster='id_worker', entity_effects=True, time_effects=True):
    """
    Estimate difference-in-differences model.
    
    Model: Y = α + β(molise_res × post) + γ_i + λ_t + ε
    
    Parameters
    ----------
    df : DataFrame
        Panel data with entity_id and time_id
    outcome : str
        Outcome variable name
    cluster : str
        Variable to cluster standard errors by
    entity_effects : bool
        Include entity fixed effects
    time_effects : bool
        Include time fixed effects
    
    Returns
    -------
    result : PanelOLSResults
        Estimation results
    """
    # Prepare data
    data = df.copy()
    data = data.dropna(subset=[outcome, 'molise_res', 'post', 'treat'])
    
    # Create entity and time indices
    data = data.set_index(['id_worker', 'year'])
    
    # Dependent variable
    y = data[outcome]
    
    # Treatment variable
    X = data[['treat']].copy()
    
    # Add constant
    X = sm.add_constant(X)
    
    # Estimate
    mod = PanelOLS(y, X, entity_effects=entity_effects, time_effects=time_effects)
    result = mod.fit(cov_type='clustered', cluster_entity=True)
    
    return result


def ddd_worker_type(df, outcome, cluster='id_worker', entity_effects=True, time_effects=True):
    """
    Estimate triple-difference model by worker type.
    
    Model: Y = α + θ(molise_res × post × private) + φ(molise_res × post × self) + 
           all two-way interactions + γ_i + λ_t + μ_s + ε
    
    Parameters
    ----------
    df : DataFrame
        Panel data
    outcome : str
        Outcome variable name
    cluster : str
        Variable to cluster standard errors by
    entity_effects : bool
        Include entity fixed effects
    time_effects : bool
        Include time fixed effects
    
    Returns
    -------
    result : PanelOLSResults
        Estimation results
    """
    # Prepare data
    data = df.copy()
    data = data[data['worker_type'].isin(['public', 'private', 'self'])].copy()
    data = data.dropna(subset=[outcome, 'molise_res', 'post', 'worker_type'])
    
    # Create worker type dummies
    data['private'] = (data['worker_type'] == 'private').astype(int)
    data['self'] = (data['worker_type'] == 'self').astype(int)
    # public is baseline
    
    # Create triple interactions
    data['treat_private'] = data['treat'] * data['private']
    data['treat_self'] = data['treat'] * data['self']
    
    # Two-way interactions
    data['molise_private'] = data['molise_res'] * data['private']
    data['molise_self'] = data['molise_res'] * data['self']
    data['post_private'] = data['post'] * data['private']
    data['post_self'] = data['post'] * data['self']
    
    # Set index
    data = data.set_index(['id_worker', 'year'])
    
    # Dependent variable
    y = data[outcome]
    
    # Regressors: triple interactions and all two-way interactions
    X = data[['treat_private', 'treat_self', 
              'molise_res', 'post', 'private', 'self',
              'molise_private', 'molise_self', 'post_private', 'post_self']].copy()
    
    # Add constant
    X = sm.add_constant(X)
    
    # Estimate with entity, time, and worker type FE
    # Note: worker type FE via dummy variables in X
    mod = PanelOLS(y, X, entity_effects=entity_effects, time_effects=time_effects)
    result = mod.fit(cov_type='clustered', cluster_entity=True)
    
    return result


def event_study(df, outcome, by_type=False, entity_effects=True, time_effects=True):
    """
    Estimate event-study (dynamic DiD) model.
    
    Model: Y = α + Σ_{k≠-1} β_k[1{event_time=k} × molise_res] + γ_i + λ_t + ε
    
    Parameters
    ----------
    df : DataFrame
        Panel data
    outcome : str
        Outcome variable name
    by_type : bool
        If True, estimate separate dynamics by worker type
    entity_effects : bool
        Include entity fixed effects
    time_effects : bool
        Include time fixed effects
    
    Returns
    -------
    results_df : DataFrame
        DataFrame with columns: event_time, beta, se, ci_low, ci_high
    """
    data = df.copy()
    data = data.dropna(subset=[outcome, 'molise_res', 'event_time'])
    
    # Filter to event_time in [-5, 5] (excluding 0 which is 2002)
    data = data[data['event_time'].between(-5, 5) & (data['event_time'] != 0)].copy()
    
    # Create event time dummies (excluding -1 as reference)
    event_times = sorted([k for k in data['event_time'].unique() if k != -1])
    
    results_list = []
    
    if by_type:
        # Estimate separately by worker type
        for worker_type in ['public', 'private', 'self']:
            data_type = data[data['worker_type'] == worker_type].copy()
            if len(data_type) == 0:
                continue
            
            # Create interaction terms
            for k in event_times:
                data_type[f'event_{k}'] = ((data_type['event_time'] == k) * data_type['molise_res']).astype(int)
            
            # Set index
            data_type = data_type.set_index(['id_worker', 'year'])
            y = data_type[outcome]
            
            # Regressors: event time interactions
            X_cols = [f'event_{k}' for k in event_times]
            X = data_type[X_cols].copy()
            X = sm.add_constant(X)
            
            # Estimate
            mod = PanelOLS(y, X, entity_effects=entity_effects, time_effects=time_effects)
            result = mod.fit(cov_type='clustered', cluster_entity=True)
            
            # Extract coefficients
            for k in event_times:
                coef_name = f'event_{k}'
                if coef_name in result.params.index:
                    beta = result.params[coef_name]
                    se = result.std_errors[coef_name]
                    ci_low = beta - 1.96 * se
                    ci_high = beta + 1.96 * se
                    results_list.append({
                        'event_time': k,
                        'worker_type': worker_type,
                        'beta': beta,
                        'se': se,
                        'ci_low': ci_low,
                        'ci_high': ci_high
                    })
            
            # Add reference period (-1)
            results_list.append({
                'event_time': -1,
                'worker_type': worker_type,
                'beta': 0.0,
                'se': 0.0,
                'ci_low': 0.0,
                'ci_high': 0.0
            })
    else:
        # Pooled estimation
        # Create interaction terms
        for k in event_times:
            data[f'event_{k}'] = ((data['event_time'] == k) * data['molise_res']).astype(int)
        
        # Set index
        data = data.set_index(['id_worker', 'year'])
        y = data[outcome]
        
        # Regressors
        X_cols = [f'event_{k}' for k in event_times]
        X = data[X_cols].copy()
        X = sm.add_constant(X)
        
        # Estimate
        mod = PanelOLS(y, X, entity_effects=entity_effects, time_effects=time_effects)
        result = mod.fit(cov_type='clustered', cluster_entity=True)
        
        # Extract coefficients
        for k in event_times:
            coef_name = f'event_{k}'
            if coef_name in result.params.index:
                beta = result.params[coef_name]
                se = result.std_errors[coef_name]
                ci_low = beta - 1.96 * se
                ci_high = beta + 1.96 * se
                results_list.append({
                    'event_time': k,
                    'beta': beta,
                    'se': se,
                    'ci_low': ci_low,
                    'ci_high': ci_high
                })
        
        # Add reference period
        results_list.append({
            'event_time': -1,
            'beta': 0.0,
            'se': 0.0,
            'ci_low': 0.0,
            'ci_high': 0.0
        })
    
    results_df = pd.DataFrame(results_list)
    return results_df
