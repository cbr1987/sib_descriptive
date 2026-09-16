#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr 27 14:57:49 2026

@author: clarabelessiotis
"""

from scipy import stats
import numpy as np

# Total N for your imaged sample
N = 10238

# --- AGE ---
# Your observed counts (imaged sample proportions x N)
observed_age = np.array([0.040, 0.207, 0.206, 0.373, 0.174]) * N

# Expected proportions from CRIS dataset
expected_age = np.array([0.244, 0.375, 0.251, 0.104, 0.026])

chi2, p = stats.chisquare(f_obs=observed_age, f_exp=expected_age * N)
print(f"Age - Chi2: {chi2:.2f}, p: {p:.4f}")

# --- SEX ---
observed_sex = np.array([0.523, 0.477]) * N
expected_sex = np.array([0.509, 0.491])

chi2, p = stats.chisquare(f_obs=observed_sex, f_exp=expected_sex * N)
print(f"Sex - Chi2: {chi2:.2f}, p: {p:.4f}")

# --- ETHNICITY ---
# Note: 'Not known' excluded from CRIS as not reported
# Redistribute remaining proportions or exclude that category
observed_eth = np.array([0.529, 0.257, 0.086, 0.068]) * N
expected_eth = np.array([0.551, 0.247, 0.108, 0.025])

# Renormalise expected to sum to 1 (since not known is excluded)
expected_eth = expected_eth / expected_eth.sum()

chi2, p = stats.chisquare(f_obs=observed_eth, f_exp=expected_eth * observed_eth.sum())
print(f"Ethnicity - Chi2: {chi2:.2f}, p: {p:.4f}")