library(writexl)

df_filter <- df_extra[df_extra$primary_diag_post_collapsed_clean != 'Other neurological disease' & 
                  df_extra$primary_diag_post_collapsed_clean != 'Other mood disorder' & 
                  df_extra$primary_diag_post_collapsed_clean != 'Other organic brain disorder' & 
                  df_extra$primary_diag_post_collapsed_clean != 'Other medical' & 
                  df_extra$primary_diag_post_collapsed_clean != 'Other mental disorder unspecified' & 
                  df_extra$primary_diag_post_collapsed_clean != 'Psychosocial stressors/Selfharm' & 
                  df_extra$primary_diag_post_collapsed_clean != 'Missing' & 
                  df_extra$primary_diag_post_collapsed_clean != 'Examination or procedure code', ]  

df_filter <- df_extra_t1w
df_filter$Scanner <- as.factor(df_filter$Scanner)
df_filter$Gender_ID <- as.factor(df_filter$Gender_ID)
df_filter$ethnicity_5cat <- as.factor(df_filter$ethnicity_5cat)
df_filter$primary_diag_post_collapsed_clean <- as.factor(df_filter$primary_diag_post_collapsed_clean)
# Convert continuous variables to numeric
df_filter$age_at_scan_date <- as.numeric(df_filter$age_at_scan_date)
df_filter$IMD_Score_2019_closest_to_scan <- as.numeric(df_filter$IMD_Score_2019_closest_to_scan)

# Define variables
y_var <- "age_at_scan_date"
covariates <- c("Gender_ID", "Scanner", "IMD_Score_2019_closest_to_scan", "ethnicity_5cat", "primary_diag_post_collapsed")  # your covariates
predictors <- grep("^adj_(?!ctx)", names(df_filter), value = TRUE, perl = TRUE) # your predictors

#"^adj_(?!ctx)"

# Initialize results containers
results_predictors <- data.frame()
results_covariates <- NULL
covariates_stored <- FALSE

# Loop through predictors
for(pred in predictors) {
  
  # Build formula
  formula_str <- paste(y_var, "~", pred, "+", paste(covariates, collapse = " + "))
  
  # Fit model
  tryCatch({
    model <- lm(as.formula(formula_str), data = df_filter)
  }, error = function(e) {
    cat("Skipping", pred, "due to error:", conditionMessage(e), "\n")
    next
  })
  
  # Extract coefficients
  coefs <- summary(model)$coefficients
  
  # Extract ONLY the predictor coefficient
  pred_tmp <- data.frame(
    outcome = y_var,
    predictor = pred,
    estimate = coefs[pred, "Estimate"],
    se = coefs[pred, "Std. Error"],
    t_value = coefs[pred, "t value"],
    p_value = coefs[pred, "Pr(>|t|)"],
    stringsAsFactors = FALSE
  )
  
  results_predictors <- rbind(results_predictors, pred_tmp)
  
  # Store covariates only ONCE
  if (!covariates_stored) {
    covariate_names <- rownames(coefs)[rownames(coefs) != pred]
    
    results_covariates <- data.frame(
      outcome = y_var,
      predictor = covariate_names,
      estimate = coefs[covariate_names, "Estimate"],
      se = coefs[covariate_names, "Std. Error"],
      t_value = coefs[covariate_names, "t value"],
      p_value = coefs[covariate_names, "Pr(>|t|)"],
      stringsAsFactors = FALSE
    )
    covariates_stored <- TRUE
  }
}

# Combine results
results_df <- rbind(results_predictors, results_covariates)

# Apply FDR correction
results_df$p_fdr <- p.adjust(results_df$p_value, method = "fdr")

# View and save
print(results_df)
write_xlsx(results_df, "linreg_extra_t1w_cleanedpostdiag.xlsx")




