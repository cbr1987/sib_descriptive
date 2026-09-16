library(ggplot2)

# Assuming your results dataframes are named:
# results_full - from whole dataset
# results_subset - from subset

results_full <- read_excel("")
results_extra <- read_excel("")

# Merge the two datasets by Category and Predictor
combined <- merge(results_full, results_extra, 
                  by = c("predictor"), 
                  suffixes = c("_full", "_extra"))

#"Category", 
# Convert to numeric
combined$Cohens_d_adjusted_full <- as.numeric(combined$Cohens_d_adjusted_full)
combined$Cohens_d_adjusted_extra <- as.numeric(combined$Cohens_d_adjusted_extra)

# Remove any rows with NA
combined <- combined[!is.na(combined$estimate_full) & !is.na(combined$Cohens_d_adjusted_extra), ]

#Look at a specific predictor
#combined <- combined[combined$Predictor != "wmhadj_optic_chiasm_85_", ]  # Change to your predictor name

# Calculate correlation
cor_result <- cor.test(combined$estimate_full, combined$estimate_extra, method = "spearman")
print(paste("Correlation:", round(cor_result$estimate, 3)))
print(paste("P-value:", cor_result$p.value))
cor_label <- paste0("r = ", round(cor_result$estimate, 3))

# Plot with correlation label
ggplot(combined, aes(x = Estimate_full, y = Estimate_extra, color = Category)) +
  geom_point(size = 3, alpha = 0.7) +
  geom_abline(intercept = 0, slope = 1, linetype = "dashed", color = "black") +
  geom_smooth(method = "lm", se = TRUE, color = "blue") +
  labs(
    title = "Coefficient Comparison for SynthSeg: Total Sample vs Non-AD Sample",
    x = "Coefficients (Total)",
    y = "Coefficients (Non-AD)"
  ) +
  annotate("text", x = Inf, y = -Inf, label = cor_label, 
           hjust = 1.1, vjust = -0.5, size = 5, fontface = "bold") +
  theme_minimal() +
  theme(legend.position = "right")

# Save plot
#ggsave("~/Documents/descriptive_paper/coefficient_comparison.png", 
       #width = 10, height = 8, dpi = 300)


# Loop through all predictors to get correlation measures:

# Get unique predictors
predictors <- unique(combined$Predictor)

# Initialize results dataframe
correlation_results <- data.frame(
  Predictor = character(),
  Correlation = numeric(),
  P_value = numeric(),
  stringsAsFactors = FALSE
)

# Loop through each predictor
for(pred in predictors) {
  
  # Filter for this predictor
  pred_data <- combined[combined$Predictor == pred, ]
  
  # Skip if not enough data
  if(nrow(pred_data) < 3) next
  
  # Calculate correlation
  cor_result <- cor.test(pred_data$Estimate_full, pred_data$Estimate_extra)
  
  # Store results
  correlation_results <- rbind(correlation_results, data.frame(
    Predictor = pred,
    Correlation = cor_result$estimate,
    P_value = cor_result$p.value
  ))
}

# Sort by correlation (lowest to highest)
correlation_results <- correlation_results[order(correlation_results$Correlation), ]

# Print results
print(correlation_results)

# Save to Excel
#library(writexl)
#write_xlsx(correlation_results, "~/Documents/descriptive_paper/predictor_correlations.xlsx")



# Looking at correlation for Cohen's d measures in T1w and T2w:

comparison <- read_excel("")

# Calculate correlation
cor_result <- cor.test(combined$Cohens_d_adjusted_full, combined$Cohens_d_adjusted_extra, method = "spearman")
print(paste("Correlation:", round(cor_result$estimate, 3)))
print(paste("P-value:", cor_result$p.value))
cor_label <- paste0("r = ", round(cor_result$estimate, 3))

# Plot with correlation label
ggplot(combined, aes(x = Cohens_d_adjusted_full, y = Cohens_d_adjusted_extra, color = Diagnosis)) +
  geom_point(size = 3, alpha = 0.7) +
  geom_abline(intercept = 0, slope = 1, linetype = "dashed", color = "black") +
  geom_smooth(method = "lm", se = TRUE, color = "blue") +
  labs(
    title = "Comparison of Adjusted Cohen's d for SynthSeg+ according to magnetic field strength",
    x = "Cohen's d (1.5 T)",
    y = "Cohen's d (1.5 and 3.0 T)"
  ) +
  annotate("text", x = Inf, y = -Inf, label = cor_label, 
           hjust = 1.1, vjust = -0.5, size = 5, fontface = "bold") +
  theme_minimal() +
  theme(legend.position = "right")

# Save plot
#ggsave("~/Documents/descriptive_paper/coefficient_comparison.png", 

# SENSITIVITY ANALYSIS FOR NONLINEAR AGE

# Plot with correlation label
ggplot(combined, aes(x = estimate_full, y = estimate_extra)) +
  geom_point(size = 3, alpha = 0.7) +
  geom_abline(intercept = 0, slope = 1, linetype = "dashed", color = "black") +
  geom_smooth(method = "lm", se = TRUE, color = "blue") +
  labs(
    title = "Volumetric associations with age, by age group",
    x = "> 50 years",
    y = "<= 50 years"
  ) +
  annotate("text", x = Inf, y = -Inf, label = cor_label, 
           hjust = 1.1, vjust = -0.5, size = 5, fontface = "bold") +
  theme_minimal() +
  theme(legend.position = "right")

# Calculate correlation
cor_result <- cor.test(combined$estimate_full, combined$estimate_extra, method = "spearman")
print(paste("Correlation:", round(cor_result$estimate, 3)))
print(paste("P-value:", cor_result$p.value))
cor_label <- paste0("r = ", round(cor_result$estimate, 3))

# Add difference between coefficients
combined$coef_diff <- abs(combined$estimate_full - combined$estimate_extra)

# Top 10 best correlated (smallest difference)
cat("\n=== MOST CONSISTENT ACROSS AGE GROUPS ===\n")
best <- combined[order(combined$coef_diff), ]
print(head(best[, c("predictor", "estimate_full", "estimate_extra", "coef_diff")], 10))

# Top 10 worst correlated (largest difference)
cat("\n=== MOST DISCREPANT ACROSS AGE GROUPS ===\n")
worst <- combined[order(-combined$coef_diff), ]
print(head(worst[, c("predictor", "estimate_full", "estimate_extra", "coef_diff")], 10))

# Optional: flag which direction differs
combined$direction_match <- sign(combined$estimate_full) == sign(combined$estimate_extra)
cat("\n=== VOLUMES WHERE DIRECTION FLIPS BETWEEN AGE GROUPS ===\n")
flipped <- combined[!combined$direction_match, c("predictor", "estimate_full", "estimate_extra")]
print(flipped)

write_xlsx(combined, '/')
