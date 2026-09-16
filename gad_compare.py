#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 23 19:08:32 2026

@author: clarabelessiotis
"""
# Comparing gadolinium with no gadolinium scans - individual volume measures code

import seaborn as sns
import matplotlib.pyplot as plt
from scipy import stats
from IPython.display import SVG, display

df = pd.read_excel('gad_test_deduped_forchecking.xlsx', engine='openpyxl')

# --- PREP ---
df['gad'] = df['gad'].fillna(0).astype(int)
df_deduped = df[df['flair'] != 1].copy()

# deduplicate within each group separately
group0 = df_deduped[df_deduped['gad'] == 0].drop_duplicates(subset=['Scanner', 'ScanID'], keep='first')
group1 = df_deduped[df_deduped['gad'] == 1].drop_duplicates(subset=['Scanner', 'ScanID'], keep='first')

# rejoin for plotting
df_deduped = pd.concat([group0, group1])

print(f"GAD=0: {len(group0)} subjects")
print(f"GAD=1: {len(group1)} subjects")
print(f"Total: {len(df_deduped)}")

icv_col = 'right lateral ventricle'  # change to your exact column name
palette = {0: "#4C72B0", 1: "#DD8452"}

group0 = df_deduped[df_deduped['gad'] == 0][icv_col].dropna()
group1 = df_deduped[df_deduped['gad'] == 1][icv_col].dropna()


# --- STATS ---
stat, p = stats.mannwhitneyu(group0, group1, alternative='two-sided')
spearman_r, spearman_p = stats.spearmanr(df_deduped['gad'], df_deduped[icv_col].fillna(df_deduped[icv_col].median()))

print(f"Group 0: n={len(group0)}, median={group0.median():.2f}")
print(f"Group 1: n={len(group1)}, median={group1.median():.2f}")
print(f"Mann-Whitney U={stat:.2f}, p={p:.4f}")
print(f"Spearman r={spearman_r:.3f}, p={spearman_p:.4f}")

# --- PLOT ---
fig, ax = plt.subplots(figsize=(6, 6))

sns.stripplot(data=df_deduped, x='gad', y=icv_col, hue='gad',
              palette=palette, alpha=0.6, size=6, jitter=True, ax=ax, legend=False)
sns.boxplot(data=df_deduped, x='gad', y=icv_col, hue='gad',
            palette=palette, width=0.4, fliersize=0,
            boxprops=dict(alpha=0.3), ax=ax, legend=False)

ax.set_title(f'Right lateral ventricle by GAD Group\nMann-Whitney p={p:.4f}')
ax.set_xlabel('GAD Group')
ax.set_ylabel('Right lateral ventricle')
ax.set_xticks([0, 1])
ax.set_xticklabels(['GAD=0', 'GAD=1'])

plt.tight_layout()

# To save as SVG

fig.savefig('/rlatvent_by_gad_group.svg', format='svg', bbox_inches='tight')
plt.close(fig)  # close without showing

# reopen saved file to display
from IPython.display import SVG, display
display(SVG('icv_by_gad_group.svg'))

df_deduped.to_excel('gad_test_deduped_forchecking.xlsx', index=False, engine='openpyxl')

# Comparing gadolinium with no gadolinium scans - multiple volume columns looped over

import seaborn as sns
import matplotlib.pyplot as plt
from scipy import stats
import pandas as pd
from IPython.display import SVG, display


# --- DEFINE VOLUMES TO TEST ---
volume_cols = ['general white matter', 'general grey matter', 'general csf', 
               'cerebellum', 'brainstem', 'thalamus', 'putamenpallidum', 'hippocampusamygdala', 
               'total intracranial', 'left cerebral white matter', 'left cerebral cortex', 'left lateral ventricle', 
               'left inferior lateral ventricle', 'left cerebellum white matter', 'left cerebellum cortex', 'left thalamus', 
               'left caudate', 'left putamen', 'left pallidum', '3rd ventricle', '4th ventricle', 'brain-stem', 'left hippocampus', 
               'left amygdala', 'csf', 'left accumbens area', 'left ventral DC', 'right cerebral white matter', 'right cerebral cortex', 
               'right lateral ventricle', 'right inferior lateral ventricle', 'right cerebellum white matter', 'right cerebellum cortex',
               'right thalamus', 'right caudate', 'right putamen', 'right pallidum', 'right hippocampus', 'right amygdala', 
               'right accumbens area', 'right ventral DC' 
]

palette = {0: "#4C72B0", 1: "#DD8452"}
save_dir = ''

# --- LOOP ---
results = []

for icv_col in volume_cols:
    if icv_col not in df_deduped.columns:
        print(f"Skipping '{icv_col}' — not found in dataframe")
        continue

    group0 = df_deduped[df_deduped['gad'] == 0][icv_col].dropna()
    group1 = df_deduped[df_deduped['gad'] == 1][icv_col].dropna()

    if len(group0) < 3 or len(group1) < 3:
        print(f"Skipping '{icv_col}' — not enough data")
        continue

    # --- STATS ---
    stat, p = stats.mannwhitneyu(group0, group1, alternative='two-sided')
    spearman_r, spearman_p = stats.spearmanr(
        df_deduped['gad'],
        df_deduped[icv_col].fillna(df_deduped[icv_col].median())
    )

    print(f"\n=== {icv_col} ===")
    print(f"Group 0: n={len(group0)}, median={group0.median():.2f}")
    print(f"Group 1: n={len(group1)}, median={group1.median():.2f}")
    print(f"Mann-Whitney U={stat:.2f}, p={p:.4f}")
    print(f"Spearman r={spearman_r:.3f}, p={spearman_p:.4f}")

    results.append({
        'Column': icv_col,
        'GAD=0 median': round(group0.median(), 2),
        'GAD=0 n': len(group0),
        'GAD=1 median': round(group1.median(), 2),
        'GAD=1 n': len(group1),
        'Mann-Whitney U': round(stat, 2),
        'MW p-value': round(p, 4),
        'Spearman r': round(spearman_r, 3),
        'Spearman p': round(spearman_p, 4),
        'Significant (p<0.05)': p < 0.05
    })

    # --- PLOT ---
    fig, ax = plt.subplots(figsize=(6, 6))

    sns.stripplot(data=df_deduped, x='gad', y=icv_col, hue='gad',
                  palette=palette, alpha=0.6, size=6, jitter=True, ax=ax, legend=False)
    sns.boxplot(data=df_deduped, x='gad', y=icv_col, hue='gad',
                palette=palette, width=0.4, fliersize=0,
                boxprops=dict(alpha=0.3), ax=ax, legend=False)

    sig = " *" if p < 0.05 else ""
    ax.set_title(f'{icv_col} by GAD Group\nMann-Whitney p={p:.4f}{sig}')
    ax.set_xlabel('GAD Group')
    ax.set_ylabel(icv_col)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(['GAD=0', 'GAD=1'])

    plt.tight_layout()

    # save and display
    safe_name = icv_col.replace(' ', '_').replace('(', '').replace(')', '')
    save_path = f'{save_dir}{safe_name}_by_gad_group.svg'
    fig.savefig(save_path, format='svg', bbox_inches='tight')
    plt.close(fig)
    display(SVG(save_path))

# --- SUMMARY TABLE ---
results_df = pd.DataFrame(results)
print("\n=== SUMMARY TABLE ===")
print(results_df.to_string(index=False))

results_df.to_excel('gad_test_results.xlsx', index=False, engine='openpyxl')
