#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct 27 09:36:18 2025

@author: clarabelessiotis
"""

#MRIQC

import pandas as pd
import numpy as np
file_path = '/.xlsx' 
df = pd.read_excel(file_path)

print(df.head)

df.columns = df.columns.str.strip().str.lower().str.replace(r'\s+', '_', regex=True)

df[['general white matter', 'general grey matter', 'general csf',
    'cerebellum', 'brainstem', 'thalamus', 'putamenpallidum',
    'hippocampusamygdala']].dtypes

cols = ['general_white_matter','general_grey_matter','general_csf','cerebellum',
        'brainstem','thalamus','putamenpallidum','hippocampusamygdala']


df = df.dropna(subset=cols)

df = df1.dropna(subset=['WMH(77)'])
df2 = df[df['t2wvisualqcsynthseg'].isna()]

print(df.columns.tolist())


for col in cols:
    print(col, df[col].map(type).value_counts())
    
for col in cols:
    df[col] = df[col].astype(str)           # ensure everything is string first
    df[col] = df[col].str.strip()           # remove leading/trailing spaces
    df[col] = df[col].str.replace(r'[^\d\.\-]', '', regex=True) 
    df[col] = pd.to_numeric(df[col], errors='coerce')  

mask = (df[cols] > 0.645).all(axis=1)  # True if all column > 0.645
mask = (df[cols] > 0.645).any(axis=1)  # True if any column < 0.645

df_filtered = df[mask]
print(len(df_filtered))

#Sample random number from the selection that have high quality
sampled = df_filtered.sample(n=1083, random_state=42)  # random_state optional
sampled = df_filtered.sample(frac=0.1)  # random_state optional
print(sampled)

df_restflair = df2.drop(sampled.index)

df_restflair = df_restflair[df_restflair['t2wvisualqcsynthseg'].isna()]

df_restflair.to_excel('.xlsx')


sampled.to_excel('.xlsx')

for col in cols:
    print(f"\nColumn: {col}")
    print(df[col].head(20).apply(repr))  
    

row = df.loc[(df['ScanID'] == 21653) & (df['cerebellum'] == 0.126)]
type(df.loc[df['ScanID'] == 21653, 'cerebellum'].iloc[0])

row = df.loc[df['scanid'] == 21653, cols]  # select only the columns of interest

df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')

mask_df = df[cols] < 0.645
# create a column that lists which columns caused the row to be kept
df['filtered_columns'] = mask_df.apply(lambda x: ', '.join(x.index[x].tolist()), axis=1)

# create a column for whether the row is kept (any column < 0.645)
df['kept'] = mask_df.any(axis=1)

# export to Excel
df.to_excel(".xlsx", index=False)


							
count = (df['visualqcraw'] == 0).sum()
print(count)


missing_rows = df[~mask]  # these were dropped

# Look at the exact float values
print(missing_rows[cols].head(20))  # inspect first 20 rs


df_filtered.to_excel('.xlsx', index=False)
outliers.to_excel('.xlsx', index=False)

def get_bounds(series):
    Q1 = series.dropna().quantile(0.25)
    Q3 = series.dropna().quantile(0.75)
    IQR = Q3 - Q1
    lower = Q1 - 1.5 * IQR
    upper = Q3 + 1.5 * IQR
    return lower, upper

# Define your columns
cols_to_check = [
    'periventricular_wmh_voxels_x',
    'deep_wmh_voxels_x', 
    'total_wmh_voxels_x',
    'total_pvs_voxels_x',
    'basal_ganglia_pvs_voxels_x',
    'centrum_semiovale_pvs_voxels_x',
    'white_matter_pvs_voxels_x'
]

# Get bounds for each column
bounds = {col: get_bounds(df[col]) for col in cols_to_check}

# Create a boolean mask for outliers across any column
outlier_mask = pd.Series(False, index=df.index)

for col, (lower, upper) in bounds.items():
    outlier_mask |= (df[col] < lower) | (df[col] > upper)

# Extract outlier rows
outliers = df[outlier_mask]



df.columns[df.columns.str.contains(r'pvs_')]

# Compute all bounds
lower_bound_efc, upper_bound_efc = get_bounds(df['efc'])
lower_bound_inu_med, upper_bound_inu_med = get_bounds(df['inu_med'])
lower_bound_inu_range, upper_bound_inu_range = get_bounds(df['inu_range'])
lower_bound_snr_gm, upper_bound_snr_gm = get_bounds(df['snr_gm'])
lower_bound_fber, upper_bound_fber = get_bounds(df['fber'])
lower_bound_wm2max, upper_bound_wm2max = get_bounds(df['wm2max'])
lower_bound_tpm_overlap_csf, upper_bound_tpm_overlap_csf = get_bounds(df['tpm_overlap_csf'])
lower_bound_cnr, upper_bound_cnr = get_bounds(df['cnr'])
lower_bound_snr_csf, upper_bound_snr_csf = get_bounds(df['snr_csf'])
lower_bound_summary_bg_stdv, upper_bound_summary_bg_stdv = get_bounds(df['summary_bg_stdv'])
lower_bound_snr_wm, upper_bound_snr_wm = get_bounds(df['snr_wm'])
lower_bound_cjv, upper_bound_cjv = get_bounds(df['cjv'])
lower_bound_qi_2, upper_bound_qi_2 = get_bounds(df['qi_2'])

outliers = df[
    (df['efc'] > upper_bound_efc) |                     # high efc = bad
    (df['inu_med'] < lower_bound_inu_med) |             # low inu_med = bad
    (df['inu_med'] > upper_bound_inu_med) |             # also high inu_med = bad
    (df['inu_range'] < lower_bound_inu_range) |         # low inu_range = bad
    (df['inu_range'] > upper_bound_inu_range) |         # high inu_range = bad
    (df['snr_gm'] < lower_bound_snr_gm) |               # low snr_gm = bad
    (df['fber'] < lower_bound_fber) |                   # low fber = bad
    (df['wm2max'] < lower_bound_wm2max) |               # low wm2max = bad
    (df['wm2max'] > upper_bound_wm2max) |               # high wm2max = bad
    (df['cnr'] < lower_bound_cnr) |                     # low cnr = bad
    (df['snr_csf'] < lower_bound_snr_csf) |             # low snr_csf = bad
    (df['snr_wm'] < lower_bound_snr_wm) |               # low snr_wm = bad
    (df['cjv'] > upper_bound_cjv)                       # high cjv = bad
]

combined_count = len(outliers)
total_count = len(df)
print(f"Number of outliers: {len(outliers)}")
print("Outlier rows:\n", outliers)
print(f"\nNumber of combined outliers: {combined_count} / {total_count} ({combined_count/total_count:.2%})")
print(outliers)


conditions = pd.DataFrame({
    'efc_high': df['efc'] > upper_bound_efc,                      # high efc = bad
    'inu_med_low': df['inu_med'] < lower_bound_inu_med,           # low inu_med = bad
    'inu_med_high': df['inu_med'] > upper_bound_inu_med,          # high inu_med = bad
    'inu_range_low': df['inu_range'] < lower_bound_inu_range,     # low inu_range = bad
    'inu_range_high': df['inu_range'] > upper_bound_inu_range,    # high inu_range = bad
    'snr_gm_low': df['snr_gm'] < lower_bound_snr_gm,              # low snr_gm = bad
    'fber_low': df['fber'] < lower_bound_fber,                    # low fber = bad
    'wm2max_low': df['wm2max'] < lower_bound_wm2max,              # low wm2max = bad
    'wm2max_high': df['wm2max'] > upper_bound_wm2max,             # high wm2max = bad
    'cnr_low': df['cnr'] < lower_bound_cnr,                       # low cnr = bad
    'snr_csf_low': df['snr_csf'] < lower_bound_snr_csf,           # low snr_csf = bad
    'snr_wm_low': df['snr_wm'] < lower_bound_snr_wm,              # low snr_wm = bad
    'cjv_high': df['cjv'] > upper_bound_cjv                       # high cjv = bad
}, index=df.index)

# --- Count how many IQMs each image is an outlier in ---
df['n_outlier_iqms'] = conditions.sum(axis=1)

outlier_images = df[df['n_outlier_iqms'] > 0]

# --- Get overall counts ---
total_images = len(df)
n_outlier_images = len(outlier_images)
prop_outliers = (n_outlier_images / total_images) * 100


print(f"Total images: {total_images}")
print(f"Images with ≥1 outlier IQM: {n_outlier_images} ({prop_outliers:.2f}%)\n")
multiple_outliers = df[df['n_outlier_iqms'] > 1]
print(f"Images with >1 outlier IQM: {len(multiple_outliers)}")

outlier_summary = []

for col in conditions.columns:
    count = conditions[col].sum()  # number of images that are outliers in this direction
    proportion = (count / total_images) * 100  # as percentage
    outlier_summary.append({
        'metric': col,
        'outlier_count': count,
        'proportion (%)': round(proportion, 2)
    })

# --- Convert to DataFrame ---
outlier_summary_df = pd.DataFrame(outlier_summary)

# --- Print results ---
print(outlier_summary_df)

outlier_summary_df.to_excel('.xlsx', index=False)



#simpler usage if doesn't matter which direction the outliers are in (eg for FLAIR images):
    

# ---- Specify the columns you want to check ----
columns_to_check = ["WMH(77)", "Intracranial-volume"]

# ---- Collect all outlier rows across all specified columns ----
all_outliers = pd.DataFrame()  # empty DataFrame to store all outlier rows

for col in columns_to_check:
    if col not in df.columns:
        print(f"⚠️ Column '{col}' not found — skipping.")
        continue

    lower, upper = get_bounds(df[col])
    mask = (df[col] < lower) | (df[col] > upper)
    outliers = df.loc[mask].copy()

    if not outliers.empty:
        # Add info about which column caused the outlier and the bounds
        outliers["Outlier_Column"] = col
        outliers["Lower_Bound"] = lower
        outliers["Upper_Bound"] = upper
        all_outliers = pd.concat([all_outliers, outliers], ignore_index=True)

# ---- Save all outlier rows to a new Excel file ----
output_file = ".xlsx"
all_outliers.to_excel(output_file, index=False)

print(f"✅ Saved all outlier rows to: {output_file}")
print(f"Total outlier rows: {len(all_outliers)}")

#CODE FOR SYNTHSEG QC CHECK


