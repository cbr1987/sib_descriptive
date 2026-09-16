df_pc <- pc_scores_all

# --------------------------
# Define outcome, covariates, and predictors
# --------------------------
outcome <- "diagnosis"
predictors <- grep("^PC", names(df_pc), value = TRUE, perl = TRUE)

# SET REFERENCE GROUP
df_pc$diagnosis <- relevel(
  factor(df_pc$diagnosis),
  ref = "No diagnosis made"
)

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
  
  all_cols <- c(outcome, pred)
  df_sub <- df_pc[complete.cases(df_pc[, all_cols]), ]
  
  if(nrow(df_sub) < 2) next
  
  df_sub[[outcome]] <- droplevels(df_sub[[outcome]])
  
  
  n_per_category <- table(df_sub[[outcome]])
  
  formula_str <- paste(outcome, "~", paste(c(pred), collapse = " + "))
  
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

