import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

# 1. Prepare data
brain_regions = [col for col in df.columns if col.startswith('adj_') or col == 'wmhadj_WMH_77_']
covariates = ['age_at_scan_date', 'Gender_ID', 'Scanner', 
              'ethnicity_5cat', 'IMD_Score_2019_closest_to_scan', 
              'post_diag_detailed_nafilled']

all_cols = brain_regions + covariates
df_complete = df[all_cols].dropna()

print(f"Original df: {len(df)} rows")
print(f"After removing NAs: {len(df_complete)} rows")

features = df_complete[brain_regions]
confounds = df_complete[['age_at_scan_date', 'Gender_ID', 'Scanner', 
                         'ethnicity_5cat', 'IMD_Score_2019_closest_to_scan']]

print(f"Features shape: {features.shape}")
print(f"Confounds shape: {confounds.shape}")

# 2. Convert categorical confounds to dummy variables
confounds_encoded = pd.get_dummies(confounds, drop_first=True)
print(f"Confounds after encoding: {confounds_encoded.shape}")

# 3. Residualize each brain region
residuals = pd.DataFrame(index=features.index, columns=features.columns, dtype=float)

print("\nResidualizing brain regions...")
for i, col in enumerate(features.columns):
    if i % 20 == 0:
        print(f"  Processing region {i+1}/{len(features.columns)}")
    
    X = confounds_encoded
    y = features[col]
    
    reg = LinearRegression()
    reg.fit(X, y)
    residuals[col] = y - reg.predict(X)

print("✓ Residualization complete")

# 4. Standardize residuals
scaler = StandardScaler()
residuals_scaled = pd.DataFrame(
    scaler.fit_transform(residuals),
    columns=residuals.columns,
    index=residuals.index
)

print(f"Residuals scaled shape: {residuals_scaled.shape}")

# 5. Get diagnosis labels
diagnosis = df_complete['post_diag_detailed_nafilled']

# 6. Define diagnosis colors (YOUR COLOR SCHEME)
color_map = {
    # Grey/Black (No diagnosis/Missing)
    'No diagnosis made': '#2b2b2b',
    'Missing': '#2b2b2b',
    'Examination or procedure code': '#2b2b2b',
    
    # Yellow (Neurological/Medical)
    'Other neurological disease': '#FDB462',
    'Other medical': '#FDB462',
    'Other organic brain disorder': '#FDB462',
    
    # Red (Dementias)
    'F00: Alzheimers disease': '#E31A1C',
    'F01: Vascular dementia': '#E31A1C',
    'F02: Other dementia': '#E31A1C',
    'F06: Mild cognitive disorder': '#E31A1C',
    
    # Green (Substance/Personality)
    'Other mental disorder unspecified': '#33A02C',
    'Psychosocial stressors/Selfharm': '#33A02C',
    'F10-19: Substance disorders': '#33A02C',
    'F50: Behavioural syndromes': '#33A02C',
    'F60-69: Personality disorder': '#33A02C',
    
    # Brown (Depression/Neurotic)
    'F32-33: Depression': '#8B4513',
    'F33: Recurrent depressive disorder': '#8B4513',
    'Other mood disorder': '#8B4513',
    'F40-48: Neurotic disorders': '#8B4513',
    
    # Purple (Developmental)
    'Developmental disorders': '#6A3D9A',
    'F90-98: Disorders of childhood': '#6A3D9A',
    
    # Blue (Psychotic)
    'F31: Bipolar affective disorder': '#1F78B4',
    'F20: Schizophrenia': '#1F78B4',
    'F25: Schizoaffective disrder': '#1F78B4',
    'F28_29: Other unspecified psychosis': '#1F78B4',
}

# Map diagnosis to colors
row_colors = diagnosis.map(color_map)

# Fill any missing colors with grey
row_colors = row_colors.fillna('#CCCCCC')


from matplotlib.patches import Patch

# 7. Create clustermap with your specifications
g = sns.clustermap(
    residuals_scaled.T,  # Transpose: rows = brain regions, cols = individuals
    
    # Clustering
    method='ward',
    metric='euclidean',
    
    # Show clustering
    col_cluster=True,      # Cluster individuals (columns)
    row_cluster=False,     # DON'T cluster brain regions (rows)
    
    # Colors
    col_colors=row_colors,  # Color bar for individuals
    cmap='coolwarm',
    
    # Labels
    xticklabels=False,      # Hide individual IDs
    yticklabels=True,       # Show brain region names
    
    # Colorbar - bottom left, smaller and narrower
    cbar_pos=(0.05, 0.02, 0.10, 0.02),  # Made width smaller: 0.15 -> 0.10
    cbar_kws={'label': 'Standardized Residuals', 'orientation': 'horizontal'},
    
    # Size
    figsize=(20, 12)
)

# Make brain region labels smaller
g.ax_heatmap.set_yticklabels(
    g.ax_heatmap.get_yticklabels(), 
    fontsize=6
)

# Create legend for diagnosis colors
unique_diagnoses = diagnosis.unique()
legend_elements = []

# Order by color groups
diagnosis_order = [
    # Grey/Black
    'No diagnosis made', 'Missing', 'Examination or procedure code',
    # Yellow
    'Other neurological disease', 'Other medical', 'Other organic brain disorder',
    # Red
    'F00: Alzheimers disease', 'F01: Vascular dementia', 'F02: Other dementia', 'F06: Mild cognitive disorder',
    # Green
    'Other mental disorder unspecified', 'Psychosocial stressors/Selfharm', 
    'F10-19: Substance disorders', 'F50: Behavioural syndromes', 'F60-69: Personality disorder',
    # Brown
    'F32-33: Depression', 'F33: Recurrent depressive disorder', 'Other mood disorder', 'F40-48: Neurotic disorders',
    # Purple
    'Developmental disorders', 'F90-98: Disorders of childhood',
    # Blue
    'F31: Bipolar affective disorder', 'F20: Schizophrenia', 
    'F25: Schizoaffective disrder', 'F28_29: Other unspecified psychosis'
]

for dx in diagnosis_order:
    if dx in unique_diagnoses and dx in color_map:
        legend_elements.append(Patch(facecolor=color_map[dx], label=dx))

# Add legend to the left, outside the heatmap, above colorbar
g.ax_heatmap.legend(
    handles=legend_elements,
    bbox_to_anchor=(-0.02, 0.5),  # Left side, middle height
    loc='center right',
    fontsize=7,
    title='Diagnosis',
    title_fontsize=8,
    frameon=True,
    ncol=1  # Single column on the side
)

# Add title
plt.suptitle('Hierarchical Clustering of Brain Structure Residuals', 
             fontsize=14, fontweight='bold', y=0.98)

plt.tight_layout()
plt.show()

print("\n✓ Clustermap displayed")
print("\nTo save, run:")
print("g.savefig('cluster_heatmap.pdf', dpi=300, bbox_inches='tight')")


# NOW PLOT BY DIAGNOSIS MEAN

mean_residuals_by_diagnosis = residuals_scaled.groupby(diagnosis).mean()

# Map diagnosis to colors (for the row colors bar)
row_colors = pd.Series(mean_residuals_by_diagnosis.index).map(color_map)
row_colors = row_colors.fillna('#CCCCCC')

# 8. Create clustermap with mean residuals by diagnosis
g = sns.clustermap(
    mean_residuals_by_diagnosis.T,  # Transpose: rows = brain regions, cols = diagnoses
    
    # Clustering
    method='ward',
    metric='euclidean',
    
    # Show clustering
    col_cluster=True,      # Cluster diagnoses (columns)
    row_cluster=False,     # DON'T cluster brain regions (rows)
    
    # Colors
    col_colors=row_colors,  # Color bar for diagnoses
    cmap='coolwarm',
    
    # Labels
    xticklabels=True,       # SHOW diagnosis names
    yticklabels=True,       # Show brain region names
    
    # Colorbar - bottom left, smaller and narrower
    cbar_pos=(0.05, 0.02, 0.10, 0.02),
    cbar_kws={'label': 'Mean Standardized Residuals', 'orientation': 'horizontal'},
    
    # Size
    figsize=(20, 12)
)

# Make brain region labels smaller
g.ax_heatmap.set_yticklabels(
    g.ax_heatmap.get_yticklabels(), 
    fontsize=6
)

# Make diagnosis labels readable
g.ax_heatmap.set_xticklabels(
    g.ax_heatmap.get_xticklabels(), 
    fontsize=8,
    rotation=90,
    ha='right'
)

# Create legend for diagnosis colors
unique_diagnoses = mean_residuals_by_diagnosis.index
legend_elements = []

# Order by color groups
diagnosis_order = [
    # Grey/Black
    'No diagnosis made', 'Missing', 'Examination or procedure code',
    # Yellow
    'Other neurological disease', 'Other medical', 'Other organic brain disorder',
    # Red
    'F00: Alzheimers disease', 'F01: Vascular dementia', 'F02: Other dementia', 'F06: Mild cognitive disorder',
    # Green
    'Other mental disorder unspecified', 'Psychosocial stressors/Selfharm', 
    'F10-19: Substance disorders', 'F50: Behavioural syndromes', 'F60-69: Personality disorder',
    # Brown
    'F32-33: Depression', 'F33: Recurrent depressive disorder', 'Other mood disorder', 'F40-48: Neurotic disorders',
    # Purple
    'Developmental disorders', 'F90-98: Disorders of childhood',
    # Blue
    'F31: Bipolar affective disorder', 'F20: Schizophrenia', 
    'F25: Schizoaffective disrder', 'F28_29: Other unspecified psychosis'
]

for dx in diagnosis_order:
    if dx in unique_diagnoses and dx in color_map:
        legend_elements.append(Patch(facecolor=color_map[dx], label=dx))

# Add legend to the left, outside the heatmap
g.ax_heatmap.legend(
    handles=legend_elements,
    bbox_to_anchor=(-0.02, 0.5),
    loc='center right',
    fontsize=7,
    title='Diagnosis',
    title_fontsize=8,
    frameon=True,
    ncol=1
)

# Add title
plt.suptitle('Hierarchical Clustering of Mean Brain Structure Residuals by Diagnosis', 
             fontsize=14, fontweight='bold', y=0.98)

plt.tight_layout()
plt.show()

# CLUSTER ACCORDING TO MEANS

import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

# 1. Prepare data
brain_regions = [col for col in df.columns if col.startswith('adj_') or col == 'wmhadj_WMH_77_']
covariates = ['age_at_scan_date', 'Gender_ID', 'Scanner', 
              'ethnicity_5cat', 'IMD_Score_2019_closest_to_scan', 
              'post_diag_detailed_nafilled']

all_cols = brain_regions + covariates
df_complete = df[all_cols].dropna()

print(f"Original df: {len(df)} rows")
print(f"After removing NAs: {len(df_complete)} rows")

features = df_complete[brain_regions]
confounds = df_complete[['age_at_scan_date', 'Gender_ID', 'Scanner', 
                         'ethnicity_5cat', 'IMD_Score_2019_closest_to_scan']]

print(f"Features shape: {features.shape}")
print(f"Confounds shape: {confounds.shape}")

# 2. Convert categorical confounds to dummy variables
confounds_encoded = pd.get_dummies(confounds, drop_first=True)
print(f"Confounds after encoding: {confounds_encoded.shape}")

# 3. Residualize each brain region
residuals = pd.DataFrame(index=features.index, columns=features.columns, dtype=float)

print("\nResidualizing brain regions...")
for i, col in enumerate(features.columns):
    if i % 20 == 0:
        print(f"  Processing region {i+1}/{len(features.columns)}")
    
    X = confounds_encoded
    y = features[col]
    
    reg = LinearRegression()
    reg.fit(X, y)
    residuals[col] = y - reg.predict(X)

print("✓ Residualization complete")

# 4. Standardize residuals
scaler = StandardScaler()
residuals_scaled = pd.DataFrame(
    scaler.fit_transform(residuals),
    columns=residuals.columns,
    index=residuals.index
)

print(f"Residuals scaled shape: {residuals_scaled.shape}")

# 5. Get diagnosis labels
diagnosis = df_complete['post_diag_detailed_nafilled']

# 6. Calculate MEAN residuals by diagnosis
residuals_scaled['diagnosis'] = diagnosis.values

# Group by diagnosis and calculate mean
mean_residuals_by_diagnosis = residuals_scaled.groupby('diagnosis').mean()

print(f"\nMean residuals by diagnosis shape: {mean_residuals_by_diagnosis.shape}")
print(f"Number of diagnoses: {len(mean_residuals_by_diagnosis)}")

# 7. Define diagnosis colors (YOUR COLOR SCHEME)
color_map = {
    # Grey/Black (No diagnosis/Missing)
    'No diagnosis made': '#2b2b2b',
    'Missing': '#2b2b2b',
    'Examination or procedure code': '#2b2b2b',
    
    # Yellow (Neurological/Medical)
    'Other neurological disease': '#FDB462',
    'Other medical': '#FDB462',
    'Other organic brain disorder': '#FDB462',
    
    # Red (Dementias)
    'F00: Alzheimers disease': '#E31A1C',
    'F01: Vascular dementia': '#E31A1C',
    'F02: Other dementia': '#E31A1C',
    'F06: Mild cognitive disorder': '#E31A1C',
    
    # Green (Substance/Personality)
    'Other mental disorder unspecified': '#33A02C',
    'Psychosocial stressors/Selfharm': '#33A02C',
    'F10-19: Substance disorders': '#33A02C',
    'F50: Behavioural syndromes': '#33A02C',
    'F60-69: Personality disorder': '#33A02C',
    
    # Brown (Depression/Neurotic)
    'F32-33: Depression': '#8B4513',
    'F33: Recurrent depressive disorder': '#8B4513',
    'Other mood disorder': '#8B4513',
    'F40-48: Neurotic disorders': '#8B4513',
    
    # Purple (Developmental)
    'Developmental disorders': '#6A3D9A',
    'F90-98: Disorders of childhood': '#6A3D9A',
    
    # Blue (Psychotic)
    'F31: Bipolar affective disorder': '#1F78B4',
    'F20: Schizophrenia': '#1F78B4',
    'F25: Schizoaffective disrder': '#1F78B4',
    'F28_29: Other unspecified psychosis': '#1F78B4',
}

# Map diagnosis to colors (for the row colors bar)
row_colors = pd.Series(mean_residuals_by_diagnosis.index).map(color_map)
row_colors = row_colors.fillna('#CCCCCC')

# Create row_colors as a list in the correct order
row_colors_list = [color_map.get(dx, '#CCCCCC') for dx in mean_residuals_by_diagnosis.index]

# 8. Create clustermap with mean residuals by diagnosis
g = sns.clustermap(
    mean_residuals_by_diagnosis.T,  # Transpose: rows = brain regions, cols = diagnoses
    
    # Clustering
    method='ward',
    metric='euclidean',
    
    # Show clustering
    col_cluster=True,      # Cluster diagnoses (columns)
    row_cluster=False,     # DON'T cluster brain regions (rows)
    
    # Colors
    col_colors=row_colors_list,  # List of colors
    cmap='coolwarm',
    
    # Labels
    xticklabels=True,       # SHOW diagnosis names
    yticklabels=True,       # Show brain region names
    
    # Colorbar - bottom left, smaller and narrower
    cbar_pos=(0.05, 0.02, 0.10, 0.02),
    cbar_kws={'label': 'Mean Standardized Residuals', 'orientation': 'horizontal'},
    
    # Size
    figsize=(20, 12)
)

# Make brain region labels smaller
g.ax_heatmap.set_yticklabels(
    g.ax_heatmap.get_yticklabels(), 
    fontsize=6
)

# Make diagnosis labels with proper alignment
labels = g.ax_heatmap.get_xticklabels()

g.ax_heatmap.set_xticklabels(
    labels,
    fontsize=7,
    rotation=45,
    ha='right',
    rotation_mode='anchor'  # This fixes the offset issue
)

# Create legend for diagnosis colors
legend_elements = []  # Reset legend elements
for dx in diagnosis_order:
    if dx in unique_diagnoses and dx in color_map:
        legend_elements.append(Patch(facecolor=color_map[dx], label=dx))

# Add legend to the left, outside the heatmap
g.ax_heatmap.legend(
    handles=legend_elements,
    bbox_to_anchor=(-0.02, 0.5),
    loc='center right',
    fontsize=7,
    title='Diagnosis',
    title_fontsize=8,
    frameon=True,
    ncol=1
)

# Add title
plt.suptitle('Hierarchical Clustering of Mean Brain Structure Residuals by Diagnosis', 
             fontsize=14, fontweight='bold', y=0.98)

plt.tight_layout()
plt.show()

print("\n✓ Clustermap displayed")
print("\nTo save, run:")
print("g.savefig('cluster_heatmap_means.pdf', dpi=300, bbox_inches='tight')")