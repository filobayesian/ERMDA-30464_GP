"""
Export functions for tables and summaries.
"""

import pandas as pd
from pathlib import Path


def write_table(result, outfile, format='both'):
    """
    Write estimation results to CSV and/or LaTeX.
    
    Parameters
    ----------
    result : PanelOLSResults or similar
        Estimation results
    outfile : str or Path
        Output file path (without extension)
    format : str
        'csv', 'tex', or 'both'
    """
    outfile = Path(outfile)
    outfile.parent.mkdir(parents=True, exist_ok=True)
    
    # Extract coefficients and standard errors
    summary = pd.DataFrame({
        'Coefficient': result.params,
        'Std_Error': result.std_errors,
        'P_Value': result.pvalues
    })
    
    if 'csv' in format or format == 'both':
        summary.to_csv(f"{outfile}.csv")
        print(f"Saved table to {outfile}.csv")
    
    if 'tex' in format or format == 'both':
        summary.to_latex(f"{outfile}.tex", float_format="%.4f")
        print(f"Saved table to {outfile}.tex")


def write_summary(results, outfile):
    """Write summary of multiple results."""
    # Placeholder - will implement in Phase 3
    pass

