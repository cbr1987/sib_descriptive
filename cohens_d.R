library(effsize)
library(dplyr)
library(tidyr)
library(writexl)

df1 <- detailed_diag_2001

# First filter out small groups (<30) or not diagnostic codes:

df1_filter <- df1[df1$post_diag_detailed_nafilled != 'Psychosocial stressors/Selfharm' & 
                  df1$post_diag_detailed_nafilled != 'Other medical' & 
                  df1$post_diag_detailed_nafilled != 'Examination or procedure code', ]

# First filter out small groups (<50) or not diagnostic codes:

df1_filter <- df1[df1$post_diag_detailed_nafilled != 'Psychosocial stressors/Selfharm' & 
                  df1$post_diag_detailed_nafilled != 'Other medical' & 
                  df1$post_diag_detailed_nafilled != 'Other mood disorder' &
                  df1$post_diag_detailed_nafilled != 'F90-98: Disorders of childhood' &
                  df1$post_diag_detailed_nafilled != 'Examination or procedure code', ]

df1_filter$post_diag_copy <- df1_filter$post_diag_detailed_nafilled
df1_filter$post_diag_copy[is.na(df1_filter$post_diag_detailed)] <- NA

# Set the predictors based on names of columns:

# If your brain columns start with "adj_"
brain_regions_t1 <- grep("^adj_", names(df1_filter), value = TRUE)

# If they start with "wmhadj_"
brain_regions_t2 <- grep("^wmhadj_", names(df1_filter), value = TRUE)

# Check what you got
print(paste("Found", length(brain_regions_t1), "brain regions"))
print(head(brain_regions_t1, 10))  # Show first 10

# Define groups
diagnoses_to_test <- setdiff(
  unique(df1_filter$post_diag_copy),
  "No diagnosis made"
) %>% na.omit() 

# Initialize results
cohens_d_raw <- data.frame()

# Calculate raw Cohen's d
for (dx in diagnoses_to_test) {
  for (region in brain_regions_t1) {
    
    # Groups
    group_dx <- df1_filter %>%
      filter(post_diag_copy == dx) %>%
      pull(!!region)
    
    group_no_dx <- df1_filter %>%
      filter(post_diag_copy == "No diagnosis made") %>%
      pull(!!region)
    
    # Cohen's d
    d_result <- cohen.d(group_dx, group_no_dx, na.rm = TRUE)
    
    # t-test
    t_test <- t.test(group_dx, group_no_dx, var.equal = FALSE)
    
    cohens_d_raw <- rbind(cohens_d_raw, data.frame(
      Diagnosis = dx,
      Region = region,
      Cohens_d_raw = d_result$estimate,
      CI_lower_raw = d_result$conf.int[1],
      CI_upper_raw = d_result$conf.int[2],
      p_value_raw = t_test$p.value,
      n_dx = length(na.omit(group_dx)),
      n_no_dx = length(na.omit(group_no_dx))
    ))
  }
}

# Apply FDR correction WITHIN each diagnosis
cohens_d_raw <- cohens_d_raw %>%
  group_by(Diagnosis) %>%
  mutate(p_fdr_raw = p.adjust(p_value_raw, method = "fdr")) %>%
  ungroup() %>%
  mutate(
    sig_raw_uncorrected = p_value_raw < 0.05,
    sig_raw_fdr = p_fdr_raw < 0.05
  )

# ========================================
# 4. GET RESIDUALS (ADJUST FOR CONFOUNDERS)
# ========================================

cat("\nCalculating adjusted residuals...\n")

covariates <- c('age_at_scan_date', 'Gender_ID', 'Scanner', 
                'IMD_Score_2019_closest_to_scan', 'ethnicity_5cat')

# Get complete cases
complete_cols <- c(brain_regions_t1, covariates, 'post_diag_copy')
df1_complete <- df1_filter[complete_cols] %>% drop_na()

cat(paste("Complete cases:", nrow(df1_complete), "\n"))

# Calculate residuals for each region
residuals_df1 <- df1_complete %>% select(post_diag_copy)

for (i in seq_along(brain_regions_t1)) {
  
  region <- brain_regions_t1[i]
  
  if (i %% 20 == 0) {
    cat("  Residualizing region", i, "of", length(brain_regions_t1), "\n")
  }
  
  # Fit linear model
  formula_str <- paste(region, "~", paste(covariates, collapse = " + "))
  model <- lm(as.formula(formula_str), data = df1_complete)
  
  # Store residuals
  residuals_df1[[region]] <- residuals(model)
}

cat("✓ Residuals calculated\n")

# ========================================
# 5. CALCULATE ADJUSTED COHEN'S D USING RESIDUALS 
# ========================================

cohens_d_adjusted <- data.frame()

cat("\nCalculating adjusted Cohen's d on residuals...\n")

# Get diagnoses from residuals df1
diagnoses_in_residuals <- unique(residuals_df1$post_diag_copy)
diagnoses_in_residuals <- diagnoses_in_residuals[diagnoses_in_residuals != "No diagnosis made"]
diagnoses_in_residuals <- na.omit(diagnoses_in_residuals) 

for (i in seq_along(diagnoses_in_residuals)) {
  
  dx <- diagnoses_in_residuals[i]
  
  if (i %% 5 == 0) {
    cat("  Processing diagnosis", i, "of", length(diagnoses_in_residuals), "\n")
  }
  
  for (region in brain_regions_t1) {
    
    # Get residuals
    group_dx <- residuals_df1 %>%
      filter(post_diag_copy == dx) %>%
      pull(!!region)
    
    group_no_dx <- residuals_df1 %>%
      filter(post_diag_copy == "No diagnosis made") %>%
      pull(!!region)
    
    # Remove NAs
    group_dx <- na.omit(group_dx)
    group_no_dx <- na.omit(group_no_dx)
    
    # Skip if insufficient data
    if (length(group_dx) < 10 || length(group_no_dx) < 10) {
      next
    }
    
    # Calculate Cohen's d and t-test on residuals
    tryCatch({
      # Cohen's d on residuals
      d_result <- cohen.d(group_dx, group_no_dx)
      
      # t-test on residuals for p-value
      t_result <- t.test(group_dx, group_no_dx, var.equal = FALSE)
      
      cohens_d_adjusted <- rbind(cohens_d_adjusted, data.frame(
        Diagnosis = dx,
        Region = region,
        Cohens_d_adjusted = d_result$estimate,
        CI_lower_adjusted = d_result$conf.int[1],
        CI_upper_adjusted = d_result$conf.int[2],
        p_value_adjusted = t_result$p.value,
        n_dx = length(group_dx),
        n_no_dx = length(group_no_dx),
        stringsAsFactors = FALSE
      ))
    }, error = function(e) {
      # Skip on error
    })
  }
}

# Apply FDR correction WITHIN each diagnosis
cohens_d_adjusted <- cohens_d_adjusted %>%
  group_by(Diagnosis) %>%
  mutate(p_fdr_adjusted = p.adjust(p_value_adjusted, method = "fdr")) %>%
  ungroup() %>%
  mutate(
    sig_adjusted_uncorrected = p_value_adjusted < 0.05,
    sig_adjusted_fdr = p_fdr_adjusted < 0.05
  )

cat("✓ Adjusted Cohen's d with FDR correction calculated\n")

# ========================================
# 6. COMBINE RAW AND ADJUSTED
# ========================================

cohens_d_all <- cohens_d_raw %>%
  left_join(
    cohens_d_adjusted %>% 
      select(Diagnosis, Region, 
             Cohens_d_adjusted, CI_lower_adjusted, CI_upper_adjusted,
             p_value_adjusted, p_fdr_adjusted,
             sig_adjusted_uncorrected, sig_adjusted_fdr),
    by = c("Diagnosis", "Region")
  )

# Calculate additional metrics
cohens_d_all <- cohens_d_all %>%
  mutate(
    abs_d_raw = abs(Cohens_d_raw),
    abs_d_adjusted = abs(Cohens_d_adjusted),
    attenuation_percent = ((abs_d_raw - abs_d_adjusted) / abs_d_raw) * 100,
    effect_size_category_raw = case_when(
      abs_d_raw < 0.2 ~ "Negligible",
      abs_d_raw < 0.5 ~ "Small",
      abs_d_raw < 0.8 ~ "Medium",
      TRUE ~ "Large"
    ),
    effect_size_category_adjusted = case_when(
      abs_d_adjusted < 0.2 ~ "Negligible",
      abs_d_adjusted < 0.5 ~ "Small",
      abs_d_adjusted < 0.8 ~ "Medium",
      TRUE ~ "Large"
    )
  )

# ========================================
# 7. SUMMARY STATISTICS
# ========================================

cat("\n=== SUMMARY ===\n")
cat("Diagnoses tested:", length(unique(cohens_d_all$Diagnosis)), "\n")
cat("Brain regions tested:", length(unique(cohens_d_all$Region)), "\n")
cat("Total comparisons:", nrow(cohens_d_all), "\n\n")

# Raw results
cat("RAW COHEN'S D:\n")
cat("  Significant (p < 0.05, uncorrected):", 
    sum(cohens_d_all$sig_raw_uncorrected, na.rm = TRUE), "\n")
cat("  Significant (p < 0.05, FDR-corrected):", 
    sum(cohens_d_all$sig_raw_fdr, na.rm = TRUE), "\n")
cat("  Large effects (|d| > 0.8):", 
    sum(cohens_d_all$abs_d_raw > 0.8, na.rm = TRUE), "\n\n")

# Adjusted results
cat("ADJUSTED COHEN'S D (residuals):\n")
cat("  Significant (p < 0.05, uncorrected):", 
    sum(cohens_d_all$sig_adjusted_uncorrected, na.rm = TRUE), "\n")
cat("  Significant (p < 0.05, FDR-corrected):", 
    sum(cohens_d_all$sig_adjusted_fdr, na.rm = TRUE), "\n")
cat("  Large effects (|d| > 0.8):", 
    sum(cohens_d_all$abs_d_adjusted > 0.8, na.rm = TRUE), "\n")

# Summary by diagnosis
summary_by_dx <- cohens_d_all %>%
  group_by(Diagnosis) %>%
  summarise(
    n_regions_tested = n(),
    n_sig_raw_fdr = sum(sig_raw_fdr, na.rm = TRUE),
    n_sig_adjusted_fdr = sum(sig_adjusted_fdr, na.rm = TRUE),
    mean_abs_d_raw = mean(abs_d_raw, na.rm = TRUE),
    mean_abs_d_adjusted = mean(abs_d_adjusted, na.rm = TRUE),
    max_abs_d_raw = max(abs_d_raw, na.rm = TRUE),
    max_abs_d_adjusted = max(abs_d_adjusted, na.rm = TRUE),
    .groups = "drop"
  ) %>%
  arrange(desc(n_sig_adjusted_fdr))

cat("\n=== SIGNIFICANT REGIONS BY DIAGNOSIS (FDR < 0.05) ===\n")
print(summary_by_dx)

# ========================================
# 8. SAVE RESULTS
# ========================================

write_xlsx(list(
  All_Results = cohens_d_all,
  Summary_by_Diagnosis = summary_by_dx,
  Significant_Raw_FDR = cohens_d_all %>% 
    filter(sig_raw_fdr) %>% 
    arrange(Diagnosis, desc(abs_d_raw)),
  Significant_Adjusted_FDR = cohens_d_all %>% 
    filter(sig_adjusted_fdr) %>% 
    arrange(Diagnosis, desc(abs_d_adjusted)),
  Top_50_Raw = cohens_d_all %>% 
    arrange(desc(abs_d_raw)) %>% 
    head(50),
  Top_50_Adjusted = cohens_d_all %>% 
    arrange(desc(abs_d_adjusted)) %>% 
    head(50)
), "~/Documents/descriptive_paper/cohens_combined_t1w_above30n_completecase.xlsx")

cat("\n✓ Results saved to cohens_d_raw_and_adjusted_with_fdr.xlsx\n")

# ========================================
# 9. CREATE FORMATTED TABLE (AFTER EXISTING SAVE)
# ========================================

# Function to format Cohen's d with CI
format_d_ci <- function(d, ci_lower, ci_upper) {
  paste0(sprintf("%.2f", d), " (", sprintf("%.2f", ci_lower), ", ", sprintf("%.2f", ci_upper), ")")
}

# Function to format p-values
format_pval <- function(p) {
  case_when(
    is.na(p) ~ "NA",
    p < 0.001 ~ "<0.001",
    p < 0.01 ~ sprintf("%.3f", p),
    TRUE ~ sprintf("%.2f", p)
  )
}

# Create formatted table
table_formatted <- cohens_d_all %>%
  mutate(
    # Format Cohen's d with CI
    `Cohen's d (Raw) [95% CI]` = format_d_ci(Cohens_d_raw, CI_lower_raw, CI_upper_raw),
    `Cohen's d (Adjusted) [95% CI]` = format_d_ci(Cohens_d_adjusted, CI_lower_adjusted, CI_upper_adjusted),
    # Format p-values
    `FDR p (Raw)` = format_pval(p_fdr_raw),
    `FDR p (Adjusted)` = format_pval(p_fdr_adjusted)
  ) %>%
  select(
    Diagnosis,
    Region,
    `Cohen's d (Raw) [95% CI]`,
    `FDR p (Raw)`,
    `Cohen's d (Adjusted) [95% CI]`,
    `FDR p (Adjusted)`
  )

# Save formatted table
write_xlsx(table_formatted, 
           "")

cat("\n✓ Formatted table saved: cohens_combined_t1w_above30n_detailediag_FORMATTED.xlsx\n")