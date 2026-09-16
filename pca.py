#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 19 12:36:42 2026

@author: clarabelessiotis
"""

from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import seaborn as sns
from scipy.stats import pearsonr, ttest_ind
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler



df = pd.read_excel('')

# First need to make sure have same number of rows in both datasets:

brain_regions = [col for col in df.columns if col.startswith('adj_') or col == 'wmhadj_WMH_77_']
covariates = ['age_at_scan_date', 'Gender_ID', 'Scanner', 
              'ethnicity_5cat', 'IMD_Score_2019_closest_to_scan', 
              'post_diag_detailed_nafilled', 'count_F', 'any_F']

all_cols = brain_regions + covariates
df_complete = df[all_cols].dropna()

print(f"Original df_clean: {len(df)} rows")
print(f"After removing NAs: {len(df_complete)} rows")

features = df_complete[brain_regions]

# Confounds (what we want to regress out)
confounds = df_complete[['age_at_scan_date', 'Gender_ID', 'Scanner', 
                         'ethnicity_5cat', 'IMD_Score_2019_closest_to_scan']]

print(f"Features shape: {features.shape}")
print(f"Confounds shape: {confounds.shape}")

# ========================================
# 3. ENCODE CATEGORICAL CONFOUNDS
# ========================================

# Convert categorical variables to dummy variables
confounds_encoded = pd.get_dummies(confounds, drop_first=True)

print(f"Confounds after encoding: {confounds_encoded.shape}")
print(f"Confound columns: {confounds_encoded.columns.tolist()}")

# ========================================
# 4. RESIDUALIZE EACH BRAIN REGION
# ========================================

print("\nResidualizing brain regions...")

# Initialize residuals dataframe
residuals = pd.DataFrame(index=features.index, columns=features.columns, dtype=float)

# Regress out confounds from each brain region
for i, col in enumerate(features.columns):
    
    if i % 20 == 0:
        print(f"  Processing region {i+1}/{len(features.columns)}")
    
    # Get data for this region (should have no NAs since we used dropna)
    X = confounds_encoded
    y = features[col]
    
    # Fit linear regression
    reg = LinearRegression()
    reg.fit(X, y)
    
    # Calculate residuals (observed - predicted)
    predicted = reg.predict(X)
    residuals[col] = y.values - predicted

print("✓ Residualization complete")

# Check for any remaining NAs
print(f"NAs in residuals: {residuals.isna().sum().sum()}")

# ========================================
# 5. STANDARDIZE RESIDUALS
# ========================================

print("\nStandardizing residuals...")

scaler = StandardScaler()
residuals_scaled = scaler.fit_transform(residuals)

print(f"Residuals scaled shape: {residuals_scaled.shape}")
print("✓ Standardization complete")


# ========================================
# 6. FIT PCA
# ========================================
pca_full = PCA()
pca_full.fit(residuals_scaled)

# Plot scree plot
plt.figure(figsize=(10, 6))
plt.plot(range(1, len(pca_full.explained_variance_ratio_) + 1), 
         np.cumsum(pca_full.explained_variance_ratio_), 'bo-')
plt.xlabel('Number of Components')
plt.ylabel('Cumulative Explained Variance')
plt.title('Scree Plot')
plt.grid(True)
plt.axhline(y=0.8, color='r', linestyle='--', label='80% variance')
plt.axhline(y=0.9, color='g', linestyle='--', label='90% variance')
plt.legend()
plt.savefig('scree_plot.pdf', dpi=300, bbox_inches='tight')
plt.show()

# Check components needed
n_components_80 = np.argmax(np.cumsum(pca_full.explained_variance_ratio_) >= 0.80) + 1
n_components_90 = np.argmax(np.cumsum(pca_full.explained_variance_ratio_) >= 0.90) + 1
print(f"Components for 80% variance: {n_components_80}")
print(f"Components for 90% variance: {n_components_90}")
print(f"First 10 components explain: {np.cumsum(pca_full.explained_variance_ratio_)[:10]}")

print(f"\nPC1 explains: {pca_full.explained_variance_ratio_[0]:.1%}")
print(f"PC2 explains: {pca_full.explained_variance_ratio_[1]:.1%}")
print(f"PC1+PC2 total: {pca_full.explained_variance_ratio_[:2].sum():.1%}")

# ========================================
# 7. EXTRACT LOADINGS FOR PC1 AND PC2
# ========================================


# Create loadings dataframe
loadings = pd.DataFrame(
    pca_full.components_[:2, :].T,  # First 2 PCs, transposed
    columns=['PC1', 'PC2'],
    index=brain_regions  # Your list of brain region names
)

# ===== ANALYZE PC1 =====
print("\n" + "="*70)
print("PC1 LOADINGS ANALYSIS (22.7% variance)")
print("="*70)

print(f"\nPC1 Statistics:")
print(f"  Mean: {loadings['PC1'].mean():.4f}")
print(f"  Std:  {loadings['PC1'].std():.4f}")
print(f"  Min:  {loadings['PC1'].min():.4f}")
print(f"  Max:  {loadings['PC1'].max():.4f}")

# Check if all same sign
all_positive = (loadings['PC1'] > 0).all()
all_negative = (loadings['PC1'] < 0).all()

if all_positive or all_negative:
    print("\n*** ALL LOADINGS SAME SIGN → PC1 = GLOBAL BRAIN PATTERN ***")
else:
    print("\n*** MIXED SIGNS → PC1 = REGIONAL CONTRAST ***")
    n_positive = (loadings['PC1'] > 0).sum()
    n_negative = (loadings['PC1'] < 0).sum()
    print(f"    Positive loadings: {n_positive}")
    print(f"    Negative loadings: {n_negative}")

print("\n=== TOP 15 POSITIVE LOADINGS (PC1) ===")
print(loadings.nlargest(15, 'PC1')['PC1'])

print("\n=== TOP 15 NEGATIVE LOADINGS (PC1) ===")
print(loadings.nsmallest(15, 'PC1')['PC1'])

# ===== ANALYZE PC2 =====
print("\n" + "="*70)
print("PC2 LOADINGS ANALYSIS (8.6% variance)")
print("="*70)

print(f"\nPC2 Statistics:")
print(f"  Mean: {loadings['PC2'].mean():.4f}")
print(f"  Std:  {loadings['PC2'].std():.4f}")
print(f"  Min:  {loadings['PC2'].min():.4f}")
print(f"  Max:  {loadings['PC2'].max():.4f}")

print("\n=== TOP 15 POSITIVE LOADINGS (PC2) ===")
print(loadings.nlargest(15, 'PC2')['PC2'])

print("\n=== TOP 15 NEGATIVE LOADINGS (PC2) ===")
print(loadings.nsmallest(15, 'PC2')['PC2'])

# ========================================
# 8. VISUALIZE LOADINGS
# ========================================

# Bar plots of top loadings
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# PC1 - Top positive
top_pc1_pos = loadings.nlargest(15, 'PC1')
axes[0, 0].barh(range(len(top_pc1_pos)), top_pc1_pos['PC1'].values, color='red', alpha=0.7)
axes[0, 0].set_yticks(range(len(top_pc1_pos)))
axes[0, 0].set_yticklabels(top_pc1_pos.index, fontsize=9)
axes[0, 0].set_xlabel('Loading', fontsize=10)
axes[0, 0].set_title('PC1: Top 15 Positive Loadings', fontsize=11)
axes[0, 0].axvline(x=0, color='black', linestyle='--', linewidth=0.5)
axes[0, 0].grid(True, alpha=0.3, axis='x')

# PC1 - Top negative
top_pc1_neg = loadings.nsmallest(15, 'PC1')
axes[0, 1].barh(range(len(top_pc1_neg)), top_pc1_neg['PC1'].values, color='blue', alpha=0.7)
axes[0, 1].set_yticks(range(len(top_pc1_neg)))
axes[0, 1].set_yticklabels(top_pc1_neg.index, fontsize=9)
axes[0, 1].set_xlabel('Loading', fontsize=10)
axes[0, 1].set_title('PC1: Top 15 Negative Loadings', fontsize=11)
axes[0, 1].axvline(x=0, color='black', linestyle='--', linewidth=0.5)
axes[0, 1].grid(True, alpha=0.3, axis='x')

# PC2 - Top positive
top_pc2_pos = loadings.nlargest(15, 'PC2')
axes[1, 0].barh(range(len(top_pc2_pos)), top_pc2_pos['PC2'].values, color='red', alpha=0.7)
axes[1, 0].set_yticks(range(len(top_pc2_pos)))
axes[1, 0].set_yticklabels(top_pc2_pos.index, fontsize=9)
axes[1, 0].set_xlabel('Loading', fontsize=10)
axes[1, 0].set_title('PC2: Top 15 Positive Loadings', fontsize=11)
axes[1, 0].axvline(x=0, color='black', linestyle='--', linewidth=0.5)
axes[1, 0].grid(True, alpha=0.3, axis='x')

# PC2 - Top negative
top_pc2_neg = loadings.nsmallest(15, 'PC2')
axes[1, 1].barh(range(len(top_pc2_neg)), top_pc2_neg['PC2'].values, color='blue', alpha=0.7)
axes[1, 1].set_yticks(range(len(top_pc2_neg)))
axes[1, 1].set_yticklabels(top_pc2_neg.index, fontsize=9)
axes[1, 1].set_xlabel('Loading', fontsize=10)
axes[1, 1].set_title('PC2: Top 15 Negative Loadings', fontsize=11)
axes[1, 1].axvline(x=0, color='black', linestyle='--', linewidth=0.5)
axes[1, 1].grid(True, alpha=0.3, axis='x')

plt.tight_layout()
plt.savefig('pca_top_loadings.pdf', dpi=300, bbox_inches='tight')
plt.show()

# Heatmap of all loadings
plt.figure(figsize=(6, 20))
sns.heatmap(loadings[['PC1', 'PC2']], 
            cmap='RdBu_r', 
            center=0,
            vmin=-0.3, vmax=0.3,
            cbar_kws={'label': 'Loading'},
            yticklabels=True)
plt.title('PCA Loadings: All Brain Regions')
plt.tight_layout()
plt.savefig('pca_loadings_heatmap.pdf', dpi=300, bbox_inches='tight')
plt.show()

# ========================================
# 9. GET PC SCORES FOR EACH PERSON
# ========================================



print(f"Rows in residuals_scaled: {residuals_scaled.shape[0]}")


pc_scores = pd.DataFrame(
    pca_full.transform(residuals_scaled)[:, :2],
    columns=['PC1', 'PC2']
)

pc_array = pca_full.transform(residuals_scaled)

pc_scores2 = pd.DataFrame(
    pc_array,
    columns=[f'PC{i+1}' for i in range(pc_array.shape[1])]
)


# Add diagnosis from the filtered dataframe
pc_scores2['diagnosis'] = df_complete['post_diag_detailed_nafilled'].values

pc_scores2.to_excel('.xlsx')

# Add other variables you might need
pc_scores['age'] = df_complete['age_at_scan_date'].values
if 'died' in df_complete.columns:
    pc_scores['died'] = df_complete['died'].values
# Transform data to get PC scores
pc_scores_array = pca_full.transform(residuals_scaled)

# Create dataframe with scores
pc_scores = pd.DataFrame(
    pc_scores_array[:, :2],
    columns=['PC1', 'PC2']
)

# Add diagnosis (make sure this matches your data)
pc_scores['diagnosis'] = df_complete['post_diag_detailed_nafilled'].values

# Calculate mean scores by diagnosis
pc_means = pc_scores.groupby('diagnosis').agg({
    'PC1': ['mean', 'std', 'count'],
    'PC2': ['mean', 'std']
}).round(3)

print("\n" + "="*70)
print("MEAN PC SCORES BY DIAGNOSIS (sorted by PC1)")
print("="*70)
print(pc_means.sort_values(('PC1', 'mean')))

# ========================================
# 10. VISUALIZE PC SCORES BY DIAGNOSIS
# ========================================

# Boxplots
fig, axes = plt.subplots(2, 1, figsize=(14, 12))

# Get diagnosis order by mean PC1
diagnosis_order = pc_scores.groupby('diagnosis')['PC1'].mean().sort_values().index

# PC1 boxplot
pc1_data = [pc_scores[pc_scores['diagnosis']==dx]['PC1'].values 
            for dx in diagnosis_order]
bp1 = axes[0].boxplot(pc1_data, labels=diagnosis_order, vert=False, 
                       patch_artist=True)
for patch in bp1['boxes']:
    patch.set_facecolor('lightblue')
axes[0].set_xlabel('PC1 Score (22.7% variance)', fontsize=11)
axes[0].set_ylabel('Diagnosis', fontsize=11)
axes[0].set_title('PC1 Scores by Diagnosis (ordered by mean)', fontsize=12, fontweight='bold')
axes[0].axvline(x=0, color='red', linestyle='--', linewidth=1.5, alpha=0.7)
axes[0].grid(True, alpha=0.3, axis='x')
axes[0].tick_params(axis='y', labelsize=9)

# PC2 boxplot
diagnosis_order_pc2 = pc_scores.groupby('diagnosis')['PC2'].mean().sort_values().index
pc2_data = [pc_scores[pc_scores['diagnosis']==dx]['PC2'].values 
            for dx in diagnosis_order_pc2]
bp2 = axes[1].boxplot(pc2_data, labels=diagnosis_order_pc2, vert=False,
                       patch_artist=True)
for patch in bp2['boxes']:
    patch.set_facecolor('lightcoral')
axes[1].set_xlabel('PC2 Score (8.6% variance)', fontsize=11)
axes[1].set_ylabel('Diagnosis', fontsize=11)
axes[1].set_title('PC2 Scores by Diagnosis (ordered by mean)', fontsize=12, fontweight='bold')
axes[1].axvline(x=0, color='red', linestyle='--', linewidth=1.5, alpha=0.7)
axes[1].grid(True, alpha=0.3, axis='x')
axes[1].tick_params(axis='y', labelsize=9)

plt.tight_layout()
plt.savefig('pc_scores_boxplots.pdf', dpi=300, bbox_inches='tight')
plt.show()

# ========================================
# 11. SCATTER PLOT: PC1 vs PC2 BY DIAGNOSIS
# ========================================

plt.figure(figsize=(14, 10))

# Get unique diagnoses
diagnoses = pc_scores['diagnosis'].unique()
colors = plt.cm.tab20(np.linspace(0, 1, len(diagnoses)))

for dx, color in zip(diagnoses, colors):
    subset = pc_scores[pc_scores['diagnosis'] == dx]
    plt.scatter(subset['PC1'], subset['PC2'], 
               label=dx, alpha=0.4, s=25, c=[color])

plt.axhline(y=0, color='black', linestyle='--', linewidth=1, alpha=0.5)
plt.axvline(x=0, color='black', linestyle='--', linewidth=1, alpha=0.5)
plt.xlabel('PC1 (22.7% variance)', fontsize=12)
plt.ylabel('PC2 (8.6% variance)', fontsize=12)
plt.title('Diagnoses in PC1-PC2 Space', fontsize=14, fontweight='bold')
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=9)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('pc_scatter_all_diagnoses.pdf', dpi=300, bbox_inches='tight')
plt.show()

# ========================================
# 12. CORRELATIONS WITH CLINICAL VARIABLES
# ========================================

print("\n" + "="*70)
print("PC CORRELATIONS WITH CLINICAL VARIABLES")
print("="*70)

# Age correlation (should be ~0 since adjusted)
r_age_pc1, p_age_pc1 = pearsonr(pc_scores['PC1'], 
                                 df_complete['age_at_scan_date'])
print(f"\nPC1 vs Age: r={r_age_pc1:.3f}, p={p_age_pc1:.4f}")
if abs(r_age_pc1) < 0.1:
    print("  ✓ Good - age adjustment worked")
else:
    print("  ⚠ Warning - some age correlation remains")

r_age_pc2, p_age_pc2 = pearsonr(pc_scores['PC2'], 
                                 df_complete['age_at_scan_date'])
print(f"PC2 vs Age: r={r_age_pc2:.3f}, p={p_age_pc2:.4f}")

# Mortality (if available)
if 'died' in df_analysis.columns:
    pc1_died = pc_scores[df_analysis['died']==1]['PC1']
    pc1_alive = pc_scores[df_analysis['died']==0]['PC1']
    t_pc1, p_pc1 = ttest_ind(pc1_died, pc1_alive)
    
    print(f"\n=== PC1 AND MORTALITY ===")
    print(f"  Died: mean={pc1_died.mean():.3f}, std={pc1_died.std():.3f}, n={len(pc1_died)}")
    print(f"  Alive: mean={pc1_alive.mean():.3f}, std={pc1_alive.std():.3f}, n={len(pc1_alive)}")
    print(f"  t-test: t={t_pc1:.2f}, p={p_pc1:.4f}")
    if p_pc1 < 0.05:
        print("  ✓ PC1 significantly associated with mortality")
    
    pc2_died = pc_scores[df_analysis['died']==1]['PC2']
    pc2_alive = pc_scores[df_analysis['died']==0]['PC2']
    t_pc2, p_pc2 = ttest_ind(pc2_died, pc2_alive)
    
    print(f"\n=== PC2 AND MORTALITY ===")
    print(f"  Died: mean={pc2_died.mean():.3f}, std={pc2_died.std():.3f}")
    print(f"  Alive: mean={pc2_alive.mean():.3f}, std={pc2_alive.std():.3f}")
    print(f"  t-test: t={t_pc2:.2f}, p={p_pc2:.4f}")
    if p_pc2 < 0.05:
        print("  ✓ PC2 significantly associated with mortality")

# ========================================
# 13. SUMMARY TABLE FOR PAPER
# ========================================

# Create summary of PCA results
pca_summary = pd.DataFrame({
    'Component': ['PC1', 'PC2', 'PC3', 'PC4', 'PC5'],
    'Variance_Explained_%': [f"{x:.1f}" for x in pca_full.explained_variance_ratio_[:5] * 100],
    'Cumulative_%': [f"{x:.1f}" for x in np.cumsum(pca_full.explained_variance_ratio_[:5]) * 100]
})

print("\n" + "="*70)
print("PCA SUMMARY TABLE")
print("="*70)
print(pca_summary.to_string(index=False))

# Save to Excel
pca_summary.to_excel('/', index=False)
loadings.to_excel('')
pc_means.to_excel('')

print("\n✓ All results saved!")
print("  - pca_variance_summary.xlsx")
print("  - pca_loadings.xlsx")
print("  - pc_scores_by_diagnosis.xlsx")

# CALCULATING VARIANCE

# 1. Calculate mean distance between diagnoses vs within diagnoses

from scipy.spatial.distance import pdist, squareform

# Between-diagnosis variance
diagnosis_means = pc_scores.groupby('diagnosis')[['PC1', 'PC2']].mean()
between_var = diagnosis_means.var().sum()

# Within-diagnosis variance
within_var = pc_scores.groupby('diagnosis')[['PC1', 'PC2']].var().mean().sum()

ratio = within_var / between_var
print(f"Within/Between variance ratio: {ratio:.2f}")
# If ratio > 1 → more variance within than between diagnoses


import matplotlib.pyplot as plt
import numpy as np

# Calculate variances for each diagnosis
within_vars = []
diagnosis_names = []

for dx in pc_scores['diagnosis'].unique():
    dx_data = pc_scores[pc_scores['diagnosis'] == dx][['PC1', 'PC2']]
    within_var = dx_data.var().sum()
    within_vars.append(within_var)
    diagnosis_names.append(dx)

# Calculate between-diagnosis variance
diagnosis_means = pc_scores.groupby('diagnosis')[['PC1', 'PC2']].mean()
between_var = diagnosis_means.var().sum()

# Plot
fig, ax = plt.subplots(figsize=(12, 6))

x_pos = np.arange(len(diagnosis_names))
bars = ax.bar(x_pos, within_vars, alpha=0.7, color='steelblue', 
               label='Within-diagnosis variance')
ax.axhline(y=between_var, color='red', linestyle='--', linewidth=2,
           label=f'Between-diagnosis variance = {between_var:.2f}')

# Add ratio annotation
ax.text(len(diagnosis_names)/2, max(within_vars)*0.9,
        f'Mean ratio = {np.mean(within_vars)/between_var:.1f}:1',
        ha='center', fontsize=14, fontweight='bold',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

ax.set_xticks(x_pos)
ax.set_xticklabels(diagnosis_names, rotation=45, ha='right', fontsize=9)
ax.set_ylabel('Variance in PC Space', fontsize=12)
ax.set_title('Within-Diagnosis vs Between-Diagnosis Variance', 
             fontsize=14, fontweight='bold')
ax.legend(fontsize=11)
ax.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('within_between_variance.pdf', dpi=300, bbox_inches='tight')
plt.show()

print(f"\nMean within-diagnosis variance: {np.mean(within_vars):.2f}")
print(f"Between-diagnosis variance: {between_var:.2f}")
print(f"Ratio: {np.mean(within_vars)/between_var:.2f}:1")


import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Calculate within-diagnosis variance for each diagnosis
within_variance_by_dx = []

for dx in pc_scores['diagnosis'].unique():
    dx_data = pc_scores[pc_scores['diagnosis'] == dx][['PC1', 'PC2']]
    within_var = dx_data.var().sum()
    n = len(dx_data)
    within_variance_by_dx.append({
        'Diagnosis': dx,
        'Within_Variance': within_var,
        'N': n
    })

variance_df = pd.DataFrame(within_variance_by_dx)

# Sort by variance
variance_df = variance_df.sort_values('Within_Variance')

# Categorize diagnoses
def categorize_diagnosis(dx):
    """Categorize as specific vs broad/unspecified"""
    if any(term in dx.lower() for term in ['other', 'unspecified', 'missing', 'nos']):
        return 'Broad/Unspecified'
    elif any(term in dx.lower() for term in ['schizophrenia', 'bipolar', 'alzheimer', 'vascular']):
        return 'Specific/Well-Defined'
    else:
        return 'Other'

variance_df['Category'] = variance_df['Diagnosis'].apply(categorize_diagnosis)

# Plot
fig, ax = plt.subplots(figsize=(12, 10))

# Color by category
colors = []
for cat in variance_df['Category']:
    if cat == 'Specific/Well-Defined':
        colors.append('steelblue')
    elif cat == 'Broad/Unspecified':
        colors.append('coral')
    else:
        colors.append('lightgray')

bars = ax.barh(range(len(variance_df)), variance_df['Within_Variance'], 
                color=colors, alpha=0.7, edgecolor='black')

ax.set_yticks(range(len(variance_df)))
ax.set_yticklabels(variance_df['Diagnosis'], fontsize=9)
ax.set_xlabel('Within-Diagnosis Variance', fontsize=12, fontweight='bold')
ax.set_title('Within-Diagnosis Variance by Diagnostic Category', 
             fontsize=14, fontweight='bold')

# Add legend
from matplotlib.patches import Patch
legend_elements = [
    Patch(facecolor='steelblue', alpha=0.7, label='Specific/Well-Defined'),
    Patch(facecolor='coral', alpha=0.7, label='Broad/Unspecified'),
    Patch(facecolor='lightgray', alpha=0.7, label='Other')
]
ax.legend(handles=legend_elements, loc='lower right', fontsize=10)

# Add sample sizes as text
for i, (idx, row) in enumerate(variance_df.iterrows()):
    ax.text(row['Within_Variance'] + 0.1, i, f"n={row['N']}", 
            va='center', fontsize=8, color='black')

ax.grid(True, alpha=0.3, axis='x')
plt.tight_layout()
plt.savefig('within_variance_by_diagnosis.pdf', dpi=300, bbox_inches='tight')
plt.show()

# Print statistics
print("\n=== WITHIN-VARIANCE BY DIAGNOSTIC SPECIFICITY ===")
print("\nSpecific/Well-Defined Diagnoses:")
print(variance_df[variance_df['Category'] == 'Specific/Well-Defined'][['Diagnosis', 'Within_Variance', 'N']])

print("\nBroad/Unspecified Diagnoses:")
print(variance_df[variance_df['Category'] == 'Broad/Unspecified'][['Diagnosis', 'Within_Variance', 'N']])

# Statistical comparison
specific_vars = variance_df[variance_df['Category'] == 'Specific/Well-Defined']['Within_Variance']
broad_vars = variance_df[variance_df['Category'] == 'Broad/Unspecified']['Within_Variance']

print(f"\nMean variance - Specific: {specific_vars.mean():.2f}")
print(f"Mean variance - Broad: {broad_vars.mean():.2f}")
print(f"Ratio: {broad_vars.mean() / specific_vars.mean():.2f}x")


from scipy.stats import mannwhitneyu

# Test if specific diagnoses have lower variance than broad categories
specific_vars = variance_df[variance_df['Category'] == 'Specific/Well-Defined']['Within_Variance']
broad_vars = variance_df[variance_df['Category'] == 'Broad/Unspecified']['Within_Variance']

U, p = mannwhitneyu(specific_vars, broad_vars, alternative='less')

print(f"\nMann-Whitney U test:")
print(f"U = {U}, p = {p:.4f}")

if p < 0.05:
    print("✓ Specific diagnoses have significantly lower within-group variance")
else:
    print("No significant difference")
    
    

# Merge PC scores with comorbidity counts
pc_scores_with_comorbidity = pc_scores.merge(
    df_complete[['count_F']], 
    left_index=True, 
    right_index=True
)

# Test: Does comorbidity predict PC1 (atrophy)?
from scipy.stats import spearmanr
r, p = spearmanr(pc_scores_with_comorbidity['count_F'], 
                 pc_scores_with_comorbidity['PC1'])

print(f"Correlation between number of diagnoses and PC1: r={r:.3f}, p={p:.4f}")


# For each primary diagnosis, compare variance between:
# - People with that diagnosis alone
# - People with that diagnosis + comorbidities

for dx in unique_diagnoses:
    dx_subset = pc_scores[pc_scores['diagnosis'] == dx]
    
    pure_dx = dx_subset[dx_subset['num_secondary_dx'] == 0]
    comorbid_dx = dx_subset[dx_subset['num_secondary_dx'] > 0]
    
    if len(pure_dx) > 10 and len(comorbid_dx) > 10:
        var_pure = pure_dx['PC1'].var()
        var_comorbid = comorbid_dx['PC1'].var()
        
        print(f"{dx}:")
        print(f"  Pure (n={len(pure_dx)}): variance = {var_pure:.3f}")
        print(f"  Comorbid (n={len(comorbid_dx)}): variance = {var_comorbid:.3f}")


