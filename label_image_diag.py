#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 12 14:51:31 2026

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
cohens_d_excel = "cohensd_t1w_final_revision.xlsx"
segmented_nifti = ""

# Which diagnoses to visualize (leave empty for all)
diagnoses_to_plot = []
# Or use empty list to plot all: diagnoses_to_plot = []

# -----------------------------
# LOAD COHEN'S D RESULTS
# -----------------------------

# Load the results
df = pd.read_excel(cohens_d_excel, sheet_name="for_label_image")

print(f"Initial rows loaded: {len(df)}")
print(f"Columns: {df.columns.tolist()}")

# Filter to only FDR-significant results
df = df[df["sig_adjusted_fdr"] == True].copy()
print(f"After FDR filter: {len(df)} rows")

# **HANDLE NAs: Remove rows without valid labels**
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
# DETERMINE GLOBAL COLOR SCALE
# -----------------------------

print("\nDetermining color scale...")

# Get all non-zero effect sizes across all diagnoses
all_effects = []
for effect_map in effect_maps.values():
    nonzero = effect_map[effect_map != 0]
    if len(nonzero) > 0:
        all_effects.extend(nonzero)

all_effects = np.array(all_effects)

# Determine symmetric color limits
if len(all_effects) > 0:
    # Use 95th percentile to avoid extreme outliers dominating color scale
    abs_max = np.percentile(np.abs(all_effects), 95)
    vmin, vmax = -abs_max, abs_max
    
    print(f"Effect size range: {all_effects.min():.2f} to {all_effects.max():.2f}")
    print(f"Color scale (95th percentile): {vmin:.2f} to {vmax:.2f}")
else:
    vmin, vmax = -1, 1
    print("WARNING: No non-zero effects found")

# -----------------------------
# PLOTTING: TWO SLICES PER DIAGNOSIS WITH CLEAN LAYOUT
# -----------------------------

print("\nCreating visualizations...")

# Number of rows = number of diagnoses
n_diagnoses = len(diagnoses)

# Create figure with proper spacing
fig = plt.figure(figsize=(12, 3.5 * n_diagnoses + 1.5))

# Create grid with space for titles and colorbar
# Each diagnosis gets: title row + brain row
gs = GridSpec(n_diagnoses * 2 + 1, 2,  # 2 rows per diagnosis + 1 for colorbar
              figure=fig, 
              wspace=0.1,   # horizontal space between slices
              hspace=0.3,   # vertical space between elements
              height_ratios=([0.15, 1] * n_diagnoses) + [0.15],  # title + brain rows + colorbar
              left=0.05, right=0.95, top=0.96, bottom=0.05)

# Get colormap
cmap = cm.get_cmap('RdBu_r')

# Plot each diagnosis
for idx, dx in enumerate(diagnoses):
    
    print(f"  Plotting {dx}...")
    
    # Get effect map
    effect_map = effect_maps[dx]
    
    # **CHECK: Does this diagnosis have any non-zero effects?**
    nonzero_count = np.sum(effect_map != 0)
    if nonzero_count == 0:
        print(f"    WARNING: No visualizable effects for {dx}")
        continue
    
    # Create NIfTI image
    effect_img = image.new_img_like(seg_mni, effect_map)
    
    # Clean diagnosis name (remove F code if present)
    if ':' in dx:
        dx_clean = dx.split(':', 1)[1].strip()
    else:
        dx_clean = dx
    
    # Calculate row indices (each diagnosis uses 2 rows)
    title_row = idx * 2
    brain_row = idx * 2 + 1
    
    # Add diagnosis name spanning both columns in the title row
    ax_title = fig.add_subplot(gs[title_row, :])
    ax_title.text(0.5, 0.5, dx_clean, 
                 ha='center', va='center',
                 fontsize=14, fontweight='bold',
                 transform=ax_title.transAxes)
    ax_title.axis('off')  # Hide axis
    
    # First slice: Sagittal (left-right view)
    ax1 = fig.add_subplot(gs[brain_row, 0])
    try:
        display1 = plotting.plot_stat_map(
            effect_img,
            bg_img=mni,
            display_mode='x',      # sagittal plane
            cut_coords=[-10],      # left hemisphere
            cmap='RdBu_r',
            vmin=vmin,
            vmax=vmax,
            threshold=0.01,        # hide zeros
            colorbar=False,        # No individual colorbars
            axes=ax1,
            title=None,            # No title
            annotate=False         # Remove annotations
        )
        # Remove any automatic titles/labels
        ax1.set_title('')
    except Exception as e:
        print(f"    ERROR plotting sagittal for {dx}: {e}")
    
    # Second slice: Coronal (front-back view)
    ax2 = fig.add_subplot(gs[brain_row, 1])
    try:
        display2 = plotting.plot_stat_map(
            effect_img,
            bg_img=mni,
            display_mode='y',      # coronal plane
            cut_coords=[0],        # center
            cmap='RdBu_r',
            vmin=vmin,
            vmax=vmax,
            threshold=0.01,
            colorbar=False,        # No individual colorbars
            axes=ax2,
            title=None,            # No title
            annotate=False         # Remove annotations
        )
        # Remove any automatic titles/labels
        ax2.set_title('')
    except Exception as e:
        print(f"    ERROR plotting coronal for {dx}: {e}")

# -----------------------------
# ADD SHARED COLORBAR AT BOTTOM
# -----------------------------

# Create axis for colorbar spanning both columns in the last row
cbar_ax = fig.add_subplot(gs[n_diagnoses * 2, :])

# Create colorbar
norm = Normalize(vmin=vmin, vmax=vmax)
cb = ColorbarBase(cbar_ax, cmap=cmap, norm=norm, orientation='horizontal')

# Colorbar label
cb.set_label("Cohen's d (Adjusted for age, sex, scanner, deprivation, ethnicity)", 
            fontsize=11, fontweight='bold')

# Add annotations to colorbar
cb.ax.text(vmin * 0.9, -2.8, 'Smaller volumes\nin diagnosis group', 
          ha='left', va='top', fontsize=9, color='navy', style='italic')
cb.ax.text(vmax * 0.9, -2.8, 'Larger volumes\nin diagnosis group', 
          ha='right', va='top', fontsize=9, color='darkred', style='italic')

# Add overall title at very top
fig.suptitle('Brain Structural Differences: Diagnosis vs No Diagnosis (FDR p < 0.05)', 
            fontsize=15, fontweight='bold')

# Save figure
output_file = 'cohens_d_brain_maps_clean_revision.svg'
plt.savefig(output_file, format='svg', bbox_inches='tight', facecolor='white')
print(f"\n✓ Saved figure: {output_file}")

plt.show()

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