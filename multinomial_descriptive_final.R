# multinomial regression - final analysis code for sib descriptive study

library(nnet)      
library(dplyr)
library(lmtest)
library(writexl)

df <- anon_t1wt2w_qual_cleaneddiag

df_core <- df[df$acquisition == 'MPRAGE' | df$t2wacquisition == 'FLAIR', ]
df_core_t1w <- df[df$acquisition == 'MPRAGE' & !is.na(df$adj_left_cerebral_cortex), ]
df_core_t2w <- df[df$t2wacquisition == 'FLAIR' & !is.na(df$wmhadj_WMH_77_), ]

df_extra <- df[df$acquisition != 'MPRAGE' & df$t2wacquisition != 'FLAIR', ]
df_extra_t1w <- df[df$acquisition != 'MPRAGE' & !is.na(df$adj_left_cerebral_cortex), ]
df_extra_t2w <- df[df$t2wacquisition != 'FLAIR' & !is.na(df$wmhadj_WMH_77_), ]

# DROPPING SMALL VARIABLES BEFORE ANALYSIS:
df$Gender_ID <- factor(df$Gender_ID, levels = c("Male", "Female"))
df$Scanner <- factor(df$Scanner, levels = c("CNSA", "CNSB", "CNSD", "CNSE"))

# DROPPING SMALL DIAGNOSIS GROUPS FOR MODEL STABILITY:

df_filter <- df[df$primary_diag_post_collapsed_clean != 'Psychosocial stressors/Selfharm' & 
                  df$primary_diag_post_collapsed_clean != 'Other medical' & 
                  df$primary_diag_post_collapsed_clean != 'Other mood disorder' & 
                  df$primary_diag_post_collapsed_clean != 'Other medical' & 
                  df$primary_diag_post_collapsed_clean != 'F90-98: Disorders of childhood' & 
                  df$primary_diag_post_collapsed_clean != 'Examination or procedure code', ]


#RUNNING ANALYSIS WITH WHOLE DATASET:

df_filter$Scanner <- as.factor(df_filter$Scanner)
df_filter$Gender_ID <- as.factor(df_filter$Gender_ID)
df_filter$ethnicity_5cat <- as.factor(df_filter$ethnicity_5cat)
df_filter$primary_diag_post_collapsed_clean <- as.factor(df_filter$primary_diag_post_collapsed_clean)

# Convert continuous variables to numeric
df_filter$age_at_scan_date <- as.numeric(df_filter$age_at_scan_date)
df_filter$IMD_Score_2019_closest_to_scan <- as.numeric(df_filter$IMD_Score_2019_closest_to_scan)

# SET REFERENCE GROUP
df_filter$primary_diag_post_collapsed_clean <- relevel(
  df_filter$primary_diag_post_collapsed_clean, 
  ref = "No diagnosis made"
)

# --------------------------
# Define outcome, covariates, and predictors
# --------------------------
outcome <- "primary_diag_post_collapsed_clean"
covariates <- c("age_at_scan_date", "Gender_ID", "Scanner", "IMD_Score_2019_closest_to_scan", "ethnicity_5cat")
predictors <- grep("^adj_", names(df_filter), value = TRUE, perl = TRUE)

# --------------------------
# Initialize results container
# --------------------------
results_df <- data.frame(
  Outcome = character(),
  Predictor = character(),
  Category = character(),
  N = numeric(), 
  Estimate = numeric(),
  StdError = numeric(),
  z_value = numeric(),
  p_value = numeric(),
  p_fdr = numeric(),
  OR = numeric(),
  stringsAsFactors = FALSE
)

# --------------------------
# Loop through predictors
# --------------------------
for(pred in predictors){
  
  all_cols <- c(outcome, covariates, pred)
  df_sub <- df_filter[complete.cases(df_filter[, all_cols]), ]
  
  if(nrow(df_sub) < 2) next
  
  df_sub[[outcome]] <- droplevels(df_sub[[outcome]])
  
  
  n_per_category <- table(df_sub[[outcome]])
  
  formula_str <- paste(outcome, "~", paste(c(covariates, pred), collapse = " + "))
  
  # Fit multinomial logistic regression (removed duplicate line)
  fit <- multinom(as.formula(formula_str), data = df_sub, trace = FALSE)
  
  s <- summary(fit)
  coefs <- s$coefficients
  ses   <- s$standard.errors
  zvals <- coefs / ses
  pvals <- 2 * (1 - pnorm(abs(zvals)))
  
  tmp <- data.frame(
    Category = rownames(coefs),
    N = as.numeric(n_per_category[rownames(coefs)]), 
    Predictor = pred,
    Estimate = coefs[, pred],
    StdError = ses[, pred],
    z_value = zvals[, pred],
    p_value = pvals[, pred],
    OR = exp(coefs[, pred]),
    stringsAsFactors = FALSE
  )
  
  tmp$p_fdr <- p.adjust(tmp$p_value, method = "fdr")
  
  results_df <- rbind(results_df, tmp)
}

# --------------------------
# Save results to Excel
# --------------------------
write_xlsx(results_df, ".xlsx")

