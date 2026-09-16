#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 30 11:12:37 2026

@author: clarabelessiotis
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import AgglomerativeClustering
from IPython.display import SVG, display

save_dir = ''

# ── Load your files ───────────────────────────────────────────────────────────
residuals_scaled = pd.read_excel('scaled_residuals_for_clustering.xlsx'
                                  )

pc_scores = pd.read_excel('pc_scores_all.xlsx' 
                          )  # adjust filename as needed

pc1 = pc_scores['PC1'].values
pc2 = pc_scores['PC2'].values

print(f"Residuals: {residuals_scaled.shape}")
print(f"PC scores: {pc_scores.shape}")

# ── Plot scatter for k = 2, 3, 4 ─────────────────────────────────────────────
palettes = {
    2: ['#4C72B0', '#DD8452'],
    3: ['#4C72B0', '#DD8452', '#55A868'],
    4: ['#4C72B0', '#DD8452', '#55A868', '#C44E52'],
}

from sklearn.metrics import silhouette_score

for k in [2, 3, 4]:

    clustering = AgglomerativeClustering(n_clusters=k, linkage='ward', metric='euclidean')
    labels = clustering.fit_predict(residuals_scaled)
    
    sil_score = silhouette_score(residuals_scaled, labels)

    fig, ax = plt.subplots(figsize=(7, 6))

    for cluster_id in range(k):
        mask = labels == cluster_id
        ax.scatter(
            pc1[mask], pc2[mask],
            c=palettes[k][cluster_id],
            alpha=0.4, s=15,
            label=f'Cluster {cluster_id + 1}'
        )

    ax.set_xlabel(f'PC1 (22.4% variance)', fontsize=11)
    ax.set_ylabel(f'PC2 (8.9% variance)', fontsize=11)
    ax.set_title(f'{k}-cluster solution (Ward linkage) — silhouette = {sil_score:.3f}', fontsize=11)
    ax.legend(title='Cluster', bbox_to_anchor=(1.05, 1), loc='upper left')
    ax.axhline(0, color='grey', linewidth=0.5, linestyle='--')
    ax.axvline(0, color='grey', linewidth=0.5, linestyle='--')

    plt.tight_layout()
    save_path = save_dir + f'pc_scatter_{k}_clusters.svg'
    fig.savefig(save_path, format='svg', bbox_inches='tight')
    plt.close(fig)
    display(SVG(save_path))
    print(f'k={k}: silhouette = {sil_score:.3f} — Saved: {save_path}')

from IPython.display import SVG, display

for k in [2, 3, 4]:

    clustering = AgglomerativeClustering(n_clusters=k, linkage='ward', metric='euclidean')
    labels = clustering.fit_predict(residuals_scaled)

    fig, ax = plt.subplots(figsize=(7, 6))

    for cluster_id in range(k):
        mask = labels == cluster_id
        ax.scatter(
            pc1[mask], pc2[mask],
            c=palettes[k][cluster_id],
            alpha=0.4, s=15,
            label=f'Cluster {cluster_id + 1}'
        )

    ax.set_xlabel('PC1', fontsize=11)
    ax.set_ylabel('PC2', fontsize=11)
    ax.set_title(f'{k}-cluster solution (hierarchical, Ward linkage)', fontsize=11)
    ax.legend(title='Cluster', bbox_to_anchor=(1.05, 1), loc='upper left')
    ax.axhline(0, color='grey', linewidth=0.5, linestyle='--')
    ax.axvline(0, color='grey', linewidth=0.5, linestyle='--')

    plt.tight_layout()
    save_path = save_dir + f'pc_scatter_{k}_clusters.svg'
    fig.savefig(save_path, format='svg', bbox_inches='tight')
    plt.close(fig)
    display(SVG(save_path))
    print(f'Saved: {save_path}')
    