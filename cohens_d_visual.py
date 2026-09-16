#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 20 09:54:29 2026

@author: clarabelessiotis
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Visualize Cohen's d effect sizes across diagnoses
Shows 2 brain slices per diagnosis with regions colored by effect size
Only visualizes regions that have valid segmentation labels
"""

import pandas as pd
import numpy as np
from nilearn import image, plotting, datasets
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.colorbar import ColorbarBase
from matplotlib.colors import Normalize
import matplotlib.cm as cm

# -----------------------------
# CONFIGURATION
# -----------------------------

# Input files
cohens_d_excel = ""
segmented_nifti = "/"


# -----------------------------
# LOAD COHEN'S D RESULTS
# -----------------------------

# Load the results
df = pd.read_excel(cohens_d_excel, sheet_name="Significant_Adjusted_FDR")

# Correct typo
df.loc[df["Diagnosis"] == "F25: Schizoaffective disrder", "Diagnosis"] = "F25: Schizoaffective disorder"

# Exclude missing diagnoses as difficult to interpret but can include them in appendix
df = df[df['Diagnosis'] != 'Missing']


print(f"Initial rows loaded: {len(df)}")
print(f"Columns: {df.columns.tolist()}")

# Which diagnoses to visualize (leave empty for all)
diagnoses_to_plot = []
# Or use empty list to plot all: diagnoses_to_plot = []

#'F20: Schizophrenia', 'F28_29: Other unspecified psychosis', 'F31: Bipolar affective disorder', 'F25: Schizoaffective disrder'

# Filter to only FDR-significant results
df = df[df["sig_adjusted_fdr"] == True].copy()
print(f"After FDR filter: {len(df)} rows")

# **HANDLE NAs: Remove rows without valid labels aka parcellation data **
initial_count = len(df)
df = df.dropna(subset=['labels'])
removed_count = initial_count - len(df)

print(f"\nRemoved {removed_count} rows with missing labels (non-visualizable regions)")
print(f"Retained {len(df)} rows with valid labels (visualizable regions)")

# Convert labels to integer
df['labels'] = df['labels'].astype(int)

# Check if we have any data left
if len(df) == 0:
    print("\n⚠️ ERROR: No visualizable regions found!")
    print("Check that your 'labels' column has values for segmented regions")
    exit()

# Filter to specific diagnoses if requested
if diagnoses_to_plot:
    df = df[df["Diagnosis"].isin(diagnoses_to_plot)]
    print(f"Filtered to {len(diagnoses_to_plot)} diagnoses: {len(df)} visualizable regions")

# Get unique diagnoses (only those with visualizable regions)
diagnoses = sorted(df["Diagnosis"].unique())
print(f"\nDiagnoses with visualizable regions: {len(diagnoses)}")

# Check that each diagnosis has some visualizable regions
for dx in diagnoses:
    n_regions = len(df[df["Diagnosis"] == dx])
    print(f"  {dx}: {n_regions} visualizable regions")

# -----------------------------
# LOAD SEGMENTATION
# -----------------------------

print("\nLoading segmentation...")
seg_img = image.load_img(segmented_nifti)
seg_data = seg_img.get_fdata()

# Resample to MNI space
print("Resampling to MNI...")
mni = datasets.load_mni152_template()
seg_mni = image.resample_to_img(seg_img, mni, interpolation="nearest")
seg_mni_data = seg_mni.get_fdata()

# **CHECK: Verify labels exist in segmentation**
seg_labels_present = np.unique(seg_mni_data)
df_labels_requested = df['labels'].unique()

# Find labels that are in dataframe but not in segmentation
missing_labels = set(df_labels_requested) - set(seg_labels_present)
if missing_labels:
    print(f"\n⚠️ WARNING: {len(missing_labels)} labels in Excel not found in segmentation:")
    print(f"  Missing labels: {sorted(list(missing_labels))[:10]}...")
    print("  These regions will not be visualized")
    
    # Remove rows with missing labels
    df = df[~df['labels'].isin(missing_labels)]
    print(f"  Retained {len(df)} rows with labels present in segmentation")

print(f"\n✓ Ready to visualize {len(df)} region-diagnosis combinations")

# -----------------------------
# CREATE EFFECT SIZE MAPS FOR EACH DIAGNOSIS
# -----------------------------

def create_effect_map(diagnosis_name, df_subset):
    """Create a brain map colored by Cohen's d effect sizes"""
    
    # Initialize map
    effect_map = np.zeros_like(seg_mni_data)
    
    # Track how many regions we successfully map
    mapped_count = 0
    
    # Fill in effect sizes for each significant region
    for _, row in df_subset.iterrows():
        label = int(row['labels'])
        cohens_d = row['Cohens_d_adjusted']
        
        # Check if this label exists in segmentation
        if label in seg_labels_present:
            effect_map[seg_mni_data == label] = cohens_d
            mapped_count += 1
    
    return effect_map, mapped_count

# Create effect maps for each diagnosis
effect_maps = {}
total_mapped = 0

print("\nCreating effect maps for each diagnosis...")
for dx in diagnoses:
    df_dx = df[df["Diagnosis"] == dx]
    effect_map, mapped = create_effect_map(dx, df_dx)
    effect_maps[dx] = effect_map
    total_mapped += mapped
    
    n_regions = len(df_dx)
    mean_d = df_dx["Cohens_d_adjusted"].abs().mean()
    max_d = df_dx["Cohens_d_adjusted"].abs().max()
    
    print(f"{dx}:")
    print(f"  {n_regions} significant regions")
    print(f"  {mapped} successfully mapped to segmentation")
    print(f"  Mean |d| = {mean_d:.2f}, Max |d| = {max_d:.2f}")

if total_mapped == 0:
    print("\n⚠️ ERROR: No regions successfully mapped to segmentation!")
    print("Check that label numbers in Excel match segmentation")
    exit()

print(f"\n✓ Successfully mapped {total_mapped} region-diagnosis pairs")


# -----------------------------
# CALCULATE GLOBAL COLOR SCALE ONCE (USING ALL DIAGNOSES)
# -----------------------------

print("\nDetermining global color scale across ALL diagnoses...")

# Get all non-zero effect sizes across all diagnoses
all_effects = []
for effect_map in effect_maps.values():
    nonzero = effect_map[effect_map != 0]
    if len(nonzero) > 0:
        all_effects.extend(nonzero)

all_effects = np.array(all_effects)

# Determine symmetric color limits (THIS IS FIXED FOR ALL PLOTS)
if len(all_effects) > 0:
    abs_max = np.percentile(np.abs(all_effects), 95)
    vmin_global, vmax_global = -abs_max, abs_max
    print(f"Global color scale: {vmin_global:.2f} to {vmax_global:.2f}")
else:
    vmin_global, vmax_global = -1, 1

# -----------------------------
# DEFINE DIAGNOSTIC GROUPINGS
# -----------------------------

# Define your diagnostic groups
diagnostic_groups = {
    'Neurodegenerative': [
        'F00: Alzheimers disease',
        'F01: Vascular dementia',
        'F02: Other dementia',
        'F06: Mild cognitive disorder'
    ],
    'Psychotic Disorders': [
        'F20: Schizophrenia',
        'F25: Schizoaffective disorder',
        'F28_29: Other unspecified psychosis',
        'F31: Bipolar affective disorder'
    ],
    'Disorders of Early Life': [
        'Developmental disorders',
        'F90-98: Disorders of childhood',
    ],
    'Other Specified Disorders': [
        'F60-69: Personality disorder',
        'F50: Behavioural syndromes',
        'F10-19: Substance disorders'
    ],
    'Other Unspecified Disorders': [
        'Other mental disorder unspecified',
        'Other neurological disease',
        'Other organic brain disorder'
    ]
}

# -----------------------------
# CREATE ONE PLOT PER DIAGNOSTIC GROUP
# -----------------------------

cmap = cm.get_cmap('RdBu_r')

for group_name, group_diagnoses in diagnostic_groups.items():
    
    print(f"\n{'='*60}")
    print(f"Creating plot for: {group_name}")
    print(f"{'='*60}")
    
    # Filter to diagnoses in this group that actually exist in data
    group_dx_present = [dx for dx in group_diagnoses if dx in diagnoses]
    
    if len(group_dx_present) == 0:
        print(f"  No diagnoses from {group_name} found in data, skipping...")
        continue
    
    print(f"  Plotting {len(group_dx_present)} diagnoses: {group_dx_present}")
    
    n_diagnoses_group = len(group_dx_present)
    diagnoses_per_row = 1
    n_cols = diagnoses_per_row * 2
    n_rows_needed = int(np.ceil(n_diagnoses_group / diagnoses_per_row))
    
    # Create figure
    fig = plt.figure(figsize=(12, 3.5 * n_rows_needed + 1.5))
    
    # Create grid - INCREASED title row height for more space
    total_grid_rows = n_rows_needed * 2 + 1
    gs = GridSpec(total_grid_rows, n_cols,
                  figure=fig,
                  wspace=0.1,
                  hspace=0.2,  # INCREASED from 0.3 to 0.4 for more vertical space
                  height_ratios=([0.15, 1] * n_rows_needed) + [0.15],  # INCREASED title row from 0.15 to 0.25
                  left=0.05, right=0.95, top=0.94, bottom=0.05)  # REDUCED top margin slightly
    
    # Plot each diagnosis in this group
    for idx, dx in enumerate(group_dx_present):
        
        print(f"  Plotting {dx}...")
        
        # Get effect map (from the global effect_maps dictionary)
        effect_map = effect_maps[dx]
        
        nonzero_count = np.sum(effect_map != 0)
        if nonzero_count == 0:
            print(f"    WARNING: No visualizable effects for {dx}")
            continue
        
        # Create NIfTI image
        effect_img = image.new_img_like(seg_mni, effect_map)
        
        # Clean diagnosis name
        if ':' in dx:
            dx_clean = dx.split(':', 1)[1].strip()
        else:
            dx_clean = dx
        
        # Calculate position in grid
        row_idx = idx // diagnoses_per_row
        col_idx = idx % diagnoses_per_row
        
        title_row = row_idx * 2
        brain_row = row_idx * 2 + 1
        col_start = col_idx * 2
        col_end = col_start + 2
        
        # Add diagnosis name - NOT BOLD, different font
        ax_title = fig.add_subplot(gs[title_row, col_start:col_end])
        ax_title.text(0.4, 0.4, dx_clean,
                     ha='right', va='center',
                     fontsize=15,  # Slightly smaller
                     fontweight='bold',  # NOT BOLD
                     fontfamily='Arial',  # Clean font
                     style='italic',  # Optional: makes it distinct
                     transform=ax_title.transAxes)
        ax_title.axis('off')
        
        # Sagittal slice
        ax1 = fig.add_subplot(gs[brain_row, col_start])
        try:
            display1 = plotting.plot_stat_map(
                effect_img,
                bg_img=mni,
                display_mode='x',
                cut_coords=[-10],
                cmap='RdBu_r',
                vmin=vmin_global,
                vmax=vmax_global,
                threshold=0.01,
                colorbar=False,
                axes=ax1,
                title=None,
                annotate=False
            )
            ax1.set_title('')
        except Exception as e:
            print(f"    ERROR plotting sagittal: {e}")
        
        # Coronal slice
        ax2 = fig.add_subplot(gs[brain_row, col_start + 1])
        try:
            display2 = plotting.plot_stat_map(
                effect_img,
                bg_img=mni,
                display_mode='y',
                cut_coords=[0],
                cmap='RdBu_r',
                vmin=vmin_global,
                vmax=vmax_global,
                threshold=0.01,
                colorbar=False,
                axes=ax2,
                title=None,
                annotate=False
            )
            ax2.set_title('')
        except Exception as e:
            print(f"    ERROR plotting coronal: {e}")
    
    # Add shared colorbar at bottom
    cbar_ax = fig.add_subplot(gs[n_rows_needed * 2, :])
    norm = Normalize(vmin=vmin_global, vmax=vmax_global)
    cb = ColorbarBase(cbar_ax, cmap=cmap, norm=norm, orientation='horizontal')
    
    cb.set_label("Cohen's d (Adjusted for Age, Sex, Scanner, Deprivation, Ethnicity)",
                fontsize=11, fontweight='bold')
    
    cb.ax.text(vmin_global * 0.9, -2.8, 'Smaller volumes\nin diagnosis group',
              ha='left', va='top', fontsize=9, color='navy', style='italic')
    cb.ax.text(vmax_global * 0.9, -2.8, 'Larger volumes\nin diagnosis group',
              ha='right', va='top', fontsize=9, color='darkred', style='italic')
    
    # Add title for this group - at the top
    fig.suptitle(f'{group_name}: Brain Volume Differences vs No Diagnosis (FDR p < 0.05)',
                fontsize=20, fontweight='bold', fontfamily='Arial', y=0.98)  # Adjusted y position
    
    # Save this group's plot
    output_file = f'cohens_d_brains_{group_name.replace(" ", "_").replace("&", "and")}.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"  ✓ Saved: {output_file}")
    
    plt.show()


print("\n" + "="*60)
print("All diagnostic group plots created!")
print("="*60)


print("\n" + "="*60)
print("All diagnostic group plots created!")
print("="*60)
# -----------------------------
# SUMMARY STATISTICS
# -----------------------------

print("\n" + "="*60)
print("SUMMARY")
print("="*60)
print(f"Total significant results (FDR < 0.05): {initial_count}")
print(f"Non-visualizable regions (NA labels): {removed_count}")
print(f"Visualizable regions: {len(df)}")
print(f"Diagnoses with visualizable effects: {len(diagnoses)}")
print(f"Total region-diagnosis pairs mapped: {total_mapped}")
print("="*60)

# Save figure
output_file = 'cohens_d_brain_maps_clean.png'
plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
print(f"\n✓ Saved figure: {output_file}")


# If you want mosaic images instead:
    
