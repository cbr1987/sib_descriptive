#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb 16 14:37:57 2026

@author: clarabelessiotis
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Load your Excel file
df = pd.read_excel('', sheet_name='')

print("Loaded DataFrame:")
print(df)
print("\n")

# Extract data
categories = df.iloc[:, 0].tolist()
mean1 = df.iloc[:, 1].tolist()  # Or use df['mean1'] if named
sd1 = df.iloc[:, 2].tolist()
mean2 = df.iloc[:, 3].tolist()
sd2 = df.iloc[:, 4].tolist()

# Create figure
fig, ax = plt.subplots(figsize=(10, 8))

y = np.arange(len(categories))

# Plot points with error bars horizontally
ax.errorbar(mean1, y - 0.15, xerr=sd1, fmt='o', 
            color='#3498db', capsize=5, label='No Falls (n = 1,138)',
            markersize=10, linewidth=2, elinewidth=2)

ax.errorbar(mean2, y + 0.15, xerr=sd2, fmt='s',
            color='#e74c3c', capsize=5, label='Falls (n = 2,705)',
            markersize=10, linewidth=2, elinewidth=2)

# Customize
ax.set_yticks(y)
ax.set_yticklabels(categories, fontsize=11)
ax.set_xlabel('Mean Value', fontsize=12, fontweight='bold')
ax.set_ylabel('Imaging Measure', fontsize=12, fontweight='bold')
ax.set_title('Mean Imaging Values According to Falls History', 
             fontsize=14, fontweight='bold')
ax.legend(fontsize=11, loc='best')
ax.grid(axis='x', alpha=0.3, linestyle='--')
ax.axvline(x=0, color='black', linestyle='-', linewidth=0.8)  # Reference line at 0

# Add some padding to x-axis
ax.margins(x=0.1)

plt.tight_layout()


plt.savefig('/coefficient_plot.png', dpi=300, bbox_inches='tight')
plt.show()

print("✓ Coefficient plot saved!")