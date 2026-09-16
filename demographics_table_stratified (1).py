"""
Stratified Demographics Table (Table 1)
- Continuous variables: mean ± SD, t-test
- Categorical variables: auto-detects all levels, n (%), chi-square
  No need to pre-convert or specify levels manually
"""

import pandas as pd
import numpy as np
from scipy import stats

# ============================================================================
# CONFIGURATION
# ============================================================================

df = pd.read_csv('your_data.csv')

# The binary flag (0/1) to split groups by
GROUP_FLAG = 'any_nph_y'
GROUP_LABELS = {0: 'No NPH', 1: 'NPH'}

# Just list your variables in the appropriate category
CONTINUOUS  = ['age']
CATEGORICAL = ['gender_id', 'falls']

# Combine into a single dict for processing
VARIABLES = {col: 'continuous' for col in CONTINUOUS} | \
            {col: 'categorical' for col in CATEGORICAL}

# ============================================================================
# SPLIT INTO TWO GROUPS
# ============================================================================

group0 = df[df[GROUP_FLAG] == 0]
group1 = df[df[GROUP_FLAG] == 1]

n0      = len(group0)
n1      = len(group1)
n_total = len(df)

col0  = f'{GROUP_LABELS[0]} (n={n0})'
col1  = f'{GROUP_LABELS[1]} (n={n1})'
col_t = f'Total (n={n_total})'

print("="*80)
print("DEMOGRAPHICS TABLE")
print("="*80)
print(f"Total N = {n_total}  |  {GROUP_LABELS[0]}: n={n0}  |  {GROUP_LABELS[1]}: n={n1}\n")

# ============================================================================
# BUILD TABLE
# ============================================================================

rows = []

for col, var_type in VARIABLES.items():

    if var_type == 'continuous':
        mean0    = group0[col].mean()
        sd0      = group0[col].std()
        mean1    = group1[col].mean()
        sd1      = group1[col].std()
        mean_all = df[col].mean()
        sd_all   = df[col].std()

        _, p_val = stats.ttest_ind(group0[col].dropna(), group1[col].dropna())

        rows.append({
            'Variable': f'{col}, mean ± SD',
            col0:       f'{mean0:.1f} ± {sd0:.1f}',
            col1:       f'{mean1:.1f} ± {sd1:.1f}',
            col_t:      f'{mean_all:.1f} ± {sd_all:.1f}',
            'p-value':  f'{p_val:.3f}',
            'Test':     't-test'
        })

    elif var_type == 'categorical':
        # Auto-detect all levels in the data
        levels = sorted(df[col].dropna().unique())

        # Run chi-square across all levels at once
        contingency = pd.crosstab(df[col], df[GROUP_FLAG])
        # Ensure both group columns exist
        for g in [0, 1]:
            if g not in contingency.columns:
                contingency[g] = 0
        contingency = contingency[[0, 1]]

        chi2, p_val, dof, expected = stats.chi2_contingency(contingency)
        test_used = 'Chi-square'
        if expected.min() < 5:
            test_used = "Fisher's exact*"

        # Header row for the variable (p-value shown here)
        rows.append({
            'Variable': f'{col}, n (%)',
            col0:       '',
            col1:       '',
            col_t:      '',
            'p-value':  f'{p_val:.3f}',
            'Test':     test_used
        })

        # One row per level
        for level in levels:
            n_l0    = (group0[col] == level).sum()
            n_l1    = (group1[col] == level).sum()
            n_l_all = (df[col] == level).sum()

            pct0    = n_l0 / n0 * 100
            pct1    = n_l1 / n1 * 100
            pct_all = n_l_all / n_total * 100

            rows.append({
                'Variable': f'  {level}',
                col0:       f'{int(n_l0)} ({pct0:.1f}%)',
                col1:       f'{int(n_l1)} ({pct1:.1f}%)',
                col_t:      f'{int(n_l_all)} ({pct_all:.1f}%)',
                'p-value':  '',
                'Test':     ''
            })

# ============================================================================
# OUTPUT
# ============================================================================

results_df = pd.DataFrame(rows)

# Add significance stars to non-empty p-values
def sig_stars(p):
    try:
        p = float(p)
        if p < 0.001: return '***'
        if p < 0.01:  return '**'
        if p < 0.05:  return '*'
        return ''
    except:
        return ''

results_df['Sig'] = results_df['p-value'].apply(sig_stars)

print(results_df.to_string(index=False))
print()
print("Continuous: mean ± SD, t-test  |  Categorical: n (%), chi-square")
print("* p<0.05  ** p<0.01  *** p<0.001")

results_df.to_csv('demographics_table.csv', index=False)
print("\nSaved to 'demographics_table.csv'")
