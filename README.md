# Molise 2002 Earthquake Labor-Market Analysis

A reproducible pipeline to estimate short- and medium-run labor-market effects of the 2002 Molise earthquake using Difference-in-Differences (DiD), Triple-Difference (DDD), and event-study designs on INPS LoSaI microdata.

## Overview

This project analyzes the impact of the 2002 Molise earthquake on labor market outcomes, including:
- Employment probability
- Earnings/wages
- Contract stability

The analysis examines heterogeneity by worker type (public, private, self-employed), gender, age, sector, and firm size.

## Project Structure

```
ERMDA-30464_GP/
├── Data/
│   └── Molise.dta              # Raw INPS LoSaI data
├── data/
│   └── derived/                 # Processed datasets
├── src/                         # Reusable Python modules
│   ├── __init__.py
│   ├── io.py                    # Data I/O functions
│   ├── build.py                 # Variable construction
│   ├── models.py                # Estimation functions (DiD, DDD, event-study)
│   ├── plots.py                 # Visualization functions
│   ├── export.py                # Table export utilities
│   ├── robustness.py            # Robustness checks
│   └── diagnostics.py           # Diagnostic functions
├── out/
│   ├── tables/                  # Estimation tables (CSV, LaTeX)
│   ├── figures/                 # All plots
│   ├── report/                  # Compiled report
│   │   ├── _figures/
│   │   ├── _tables/
│   │   ├── README.md
│   │   └── session_info.txt
│   └── diagnostics/            # Diagnostic outputs
├── 01_analyze_data.ipynb        # Phase 1: Data exploration
├── 02_structure_code.ipynb      # Phase 2: Code structuring
├── 03_main_analysis.ipynb       # Phase 3: Full analysis pipeline
└── README.md                    # This file
```

## Requirements

### Python Environment

The project uses Python 3.11+ with the following packages:

- `pandas` - Data manipulation
- `numpy` - Numerical computing
- `pyreadstat` - Stata file reading
- `linearmodels` - Panel data estimation
- `statsmodels` - Statistical models
- `matplotlib` - Plotting
- `seaborn` - Statistical visualization
- `pyarrow` - Parquet file support
- `scipy` - Scientific computing

### Installation

1. Activate your conda environment (e.g., `data_analysis`):
```bash
conda activate data_analysis
```

2. Install required packages:
```bash
pip install pandas numpy pyreadstat linearmodels statsmodels matplotlib seaborn pyarrow scipy
```

## Data

### Input Data

The analysis uses two Stata files containing INPS LoSaI microdata:
- `Data/Molise.dta` - Treatment region (Molise, region code 12)
- `Data/Basilicata.dta` - Control region (Basilicata, region code 2)

The `load_raw()` function automatically loads and combines both datasets. Key variables include:

- **Identifiers**: `id_worker`, `year`, `id_firm`
- **Demographics**: `gender` (0=Male, 1=Female), `year_birth`, `age`
- **Geography**: `region_res` (12=Molise, 2=Basilicata)
- **Worker Type**: `type` (1=Private, 2=Public, 3=Self-employed, 4=Non-employed)
- **Employment**: `wage`, `working_weeks`, `contract_type`, `sector_12cat`
- **Dates**: `date_start`, `date_end`

### Analysis Period

- **Pre-period**: 1997-2001
- **Post-period**: 2003-2007
- **Excluded**: 2002 (earthquake year)

## Usage

### Step 1: Data Analysis

Run the first notebook to explore the data structure:

```bash
jupyter notebook 01_analyze_data.ipynb
```

This notebook:
- Loads and inspects the raw data
- Identifies variable types and distributions
- Checks data quality (missingness, outliers)
- Creates a codebook
- Documents temporal and geographic coverage

### Step 2: Code Structuring

Run the second notebook to set up the analysis modules:

```bash
jupyter notebook 02_structure_code.ipynb
```

This notebook:
- Maps actual variable names to analysis variables
- Creates reusable Python modules in `/src/`
- Tests data loading and variable construction

**Note**: The modules are already created, but you can re-run this to verify or modify them.

### Step 3: Main Analysis

Run the main analysis notebook:

```bash
jupyter notebook 03_main_analysis.ipynb
```

This notebook executes the full analysis pipeline:

1. **Data Preparation**
   - Loads raw data
   - Constructs analysis variables
   - Creates treatment indicators
   - Assembles analysis-ready panel

2. **Baseline DiD Estimation**
   - Estimates DiD models for all outcomes
   - Exports tables with coefficients and standard errors

3. **DDD by Worker Type**
   - Triple-difference models comparing private/self vs public workers
   - Reports θ (private) and φ (self) coefficients

4. **Event-Study Analysis**
   - Dynamic DiD with event-time dummies
   - Pooled and worker-type-specific estimates
   - Parallel trends tests
   - Generates event-study plots

5. **Three Environments Analysis**
   - Panel A: Within Molise (private vs public)
   - Panel B: Within Basilicata (placebo)
   - Panel C: Cross-region DDD

6. **Robustness Checks**
   - Alternative specifications
   - Different post windows
   - Balanced panel only
   - Including 2002 with shock indicator

7. **Heterogeneity Analysis**
   - By gender × worker type
   - By age groups
   - By sector (construction vs other)

8. **Diagnostics**
   - Parallel trends tests
   - Cell counts
   - Missingness audit

9. **Report Generation**
   - Compiles all outputs
   - Creates README with model formulas
   - Generates session info

## Model Specifications

### Baseline DiD

```
Y_{i r t} = α + β(molise_res × post) + γ_i + λ_t + ε_{i r t}
```

- **Fixed Effects**: Individual (γ_i) and year (λ_t)
- **Clustering**: Standard errors clustered by `person_id`
- **Outcomes**: `emp_prob`, `earnings_asinh`, `wage_asinh`, `contract_perm`

### DDD by Worker Type

```
Y_{i s r t} = α + θ(molise_res × post × private) + φ(molise_res × post × self) + 
              all two-way interactions + γ_i + λ_t + μ_s + ε_{i s r t}
```

- **Fixed Effects**: Individual, year, worker_type
- **Coefficients**: 
  - θ: Private vs Public
  - φ: Self vs Public

### Event Study

```
Y_{i r t} = α + Σ_{k≠-1} β_k [1{event_time = k} × molise_res] + γ_i + λ_t + ε_{i r t}
```

- **Reference period**: k = -1 (year 2001)
- **Event time range**: k ∈ [-5, +5], excluding 0 (2002)

## Variable Construction

### Treatment Variables

- **`molise_res`**: 1 if `region_res == 12` (Molise), 0 if `region_res == 2` (Basilicata), fixed by pre-period residence
- **`post`**: 1 if `year >= 2003`
- **`treat`**: `molise_res × post`
- **`event_time`**: `year - 2002`

### Worker Type

Constructed from `type` field:
- 1 → `private`
- 2 → `public` (baseline)
- 3 → `self`
- 4 → `non_employed` (excluded from analysis)

### Outcomes

- **`emp_prob`**: 1 if employed (has wage or working_weeks > 0)
- **`earnings_asinh`**: `asinh(earnings_annualized)`, winsorized at p1-p99
- **`wage_asinh`**: `asinh(wage)`, winsorized at p1-p99
- **`contract_perm`**: 1 if `contract_type == 1` (Permanent)

### Sample Flags

- **`is_balanced_97_07`**: Present in all years 1997-2007 (excluding 2002)
- **`is_stayer_residence`**: No inter-municipality moves
- **`is_border_municipality`**: On region border (requires additional data)

## Outputs

All outputs are saved to the `/out/` directory:

### Tables (`/out/tables/`)
- `baseline_did_{outcome}.csv` / `.tex` - Baseline DiD results
- `ddd_{outcome}.csv` / `.tex` - DDD results
- `event_study_{outcome}.csv` - Event-study coefficients
- `table_three_env.csv` - Three environments summary
- `robustness_index.csv` - Robustness check summary
- `heterogeneity_grids/all_dimensions.csv` - Heterogeneity results

### Figures (`/out/figures/`)
- `fig_event_{outcome}.png` - Event-study plots (pooled)
- `fig_event_{outcome}_bytype.png` - Event-study plots by worker type
- `fig_three_env_{outcome}.png` - Three environments figure

### Report (`/out/report/`)
- `README.md` - Detailed model documentation
- `session_info.txt` - Package versions and system info
- `_figures/` - All plots
- `_tables/` - All tables

### Diagnostics (`/out/diagnostics/`)
- `cell_counts.csv` - Observation counts by cell
- `missingness_audit.csv` - Missing data summary

## Reproducibility

The analysis is fully reproducible:

- **Random seed**: Set to 42 for all random operations
- **Deterministic processing**: All data transformations are deterministic
- **Version tracking**: Session info records package versions
- **Clear lineage**: Data processing steps are documented

To rebuild all outputs from scratch:

```bash
# Clean previous outputs (optional)
rm -rf out/* data/derived/*

# Run notebooks in order
jupyter notebook 01_analyze_data.ipynb
jupyter notebook 02_structure_code.ipynb
jupyter notebook 03_main_analysis.ipynb
```

## Notes

### Data Loading

The `load_raw()` function automatically:
1. Loads both `Data/Molise.dta` and `Data/Basilicata.dta`
2. Sets `region_res` to '12' for Molise and '2' for Basilicata
3. Combines the datasets into a single DataFrame
4. Prints summary statistics for each region

If you want to load only a single file, use:
```python
df, meta = load_raw(load_both_regions=False)
```

### Data Requirements

- Minimum cell size: Each cell (region × type × year) should have N ≥ 50 observations
- The code will warn if cells have insufficient observations

### Estimation Details

- **Clustering**: Standard errors clustered by `person_id` (entity-level)
- **Fixed Effects**: Individual and year fixed effects included in all models
- **LPM**: Linear probability models used for binary outcomes (logit/probit available in robustness)
- **Confidence Intervals**: 95% CIs computed with small-sample adjustments if supported

## Citation

If you use this code, please cite:

```
Molise 2002 Earthquake Labor-Market Analysis
ERMDA-30464_GP
```

## License

[Specify your license here]

## Contact

[Your contact information]

---

**Last Updated**: 2024
**Python Version**: 3.11+
**Analysis Period**: 1997-2007 (excluding 2002)

