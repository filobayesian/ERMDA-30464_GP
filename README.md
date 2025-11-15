# Dataset Documentation

This document describes the structure and values of variables in the filtered datasets located in `data/derived/`.

## Dataset Files

The project contains three filtered datasets:
- `basilicata_filtered.dta` - Basilicata region data
- `molise_filtered.dta` - Molise region data  
- `puglia_filtered.dta` - Puglia region data

## Data Processing

All datasets have been processed as follows:
1. **Region filtering**: Restricted to Basilicata (region code "2"), Molise (region code "12"), and Puglia (region code "16")
2. **Worker cohort**: Retained only workers who were employed at least once in 1999, 2000, or 2001
3. **Year window**: Restricted observations to the period 1998-2007
4. **Variable selection**: Kept only selected columns from the original dataset
5. **Derived variables**: Added `employed` and `income_category` variables

## Variable Descriptions

### `id_worker`
- **Type**: Integer (int64)
- **Description**: Unique identifier for each worker
- **Values**: Positive integers
- **Missing values**: None
- **Example**: 3052, 2806

### `year`
- **Type**: Integer (int64)
- **Description**: Year of the observation
- **Values**: Integers in the range 1998-2007
- **Missing values**: None
- **Example**: 1999, 2000, 2001, ..., 2007

### `type`
- **Type**: Integer (int64)
- **Description**: Employment type classification
- **Values**: 
  - `1` = Private employees
  - `2` = Public employees
  - `3` = Self-employed
  - `4` = Non employed
- **Missing values**: None
- **Notes**: Used to identify employment status

### `wage`
- **Type**: Numeric (object in source, converted to numeric)
- **Description**: Annual wage or salary amount
- **Values**: Non-negative floating point numbers
- **Range**: 0.00 to 179,100.00 (observed range across all regions)
- **Missing values**: May contain NaN for non-employed observations
- **Units**: Monetary units (likely Euros)
- **Example**: 300, 7000, 18700, 19100, 18100

### `contract_type`
- **Type**: Object/String (stored as object in Stata)
- **Description**: Type of employment contract
- **Values**: Numeric codes stored as strings (e.g., "1", "2")
- **Missing values**: NaN for non-employed or missing contract information
- **Notes**: Specific code meanings depend on the original data source classification
- **Example**: "1", "2" (when present)

### `sector_2d`
- **Type**: Object/String (stored as object in Stata)
- **Description**: 2-digit sector classification code
- **Values**: Numeric codes stored as strings (e.g., "45", "49", "78", "29")
- **Missing values**: NaN for non-employed or missing sector information
- **Notes**: Industry sector classification using 2-digit codes
- **Example**: "45", "49", "78", "29"

### `region_res`
- **Type**: Object/String
- **Description**: Region of residence code
- **Values**: 
  - `"2"` = Basilicata (control group)
  - `"12"` = Molise (treated group)
  - `"16"` = Puglia (control group)
- **Missing values**: None
- **Notes**: All datasets are filtered to contain only one region each

### `employed`
- **Type**: Integer (Int8)
- **Description**: Binary indicator for employment status (derived variable)
- **Values**: 
  - `1` = Employed (wage > 0 OR type ≠ 4)
  - `0` = Not employed (wage = 0 AND type = 4)
- **Missing values**: None
- **Notes**: Created based on wage values and employment type (type = 4 indicates non-employed)

### `income_category`
- **Type**: Integer (Int8)
- **Description**: Income classification based on annual wage (derived variable)
- **Values**: 
  - `1` = Low income (wage < 28,000)
  - `2` = Medium income (28,000 ≤ wage ≤ 50,000)
  - `3` = High income (wage > 50,000)
- **Missing values**: None (or NaN for missing wage values)
- **Notes**: Created from the `wage` variable using the following thresholds:
  - Low: below €28,000
  - Medium: between €28,000 and €50,000 (inclusive)
  - High: above €50,000

## Dataset Structure

Each filtered dataset is structured as a panel (long format) where:
- **Unit of observation**: Worker-year (each row represents one worker in one year)
- **Time period**: 1998-2007
- **Worker cohort**: Workers who were employed at least once in 1999, 2000, or 2001

## Sample Sizes

After filtering:
- **Basilicata**: 94,448 rows for 9,875 unique workers
- **Molise**: 51,781 rows for 5,431 unique workers
- **Puglia**: 607,473 rows for 63,923 unique workers

## Notes

1. **Wage values**: Wage is stored as object/string in the original data but should be converted to numeric for analysis using `pd.to_numeric(wage, errors="coerce")`

2. **Missing values**: Missing values are represented as `NaN` (Not a Number) in pandas, which translate to missing values in Stata format

3. **Variable types**: Some variables are stored as object/string type to preserve codes that may have leading zeros or special characters

4. **Employment indicator**: The `employed` variable combines information from both `wage` (positive wages indicate employment) and `type` (type 4 indicates non-employment)

5. **Income categorization**: The `income_category` variable is based on annual wage amounts. Workers with missing or zero wages are classified according to their actual wage value (if available)

