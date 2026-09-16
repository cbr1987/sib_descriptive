library(dplyr)
library(writexl)
library(tidyr)

# DON'T filter out NAs - keep everyone
df_demographics <- df1

# Create grouped variable that handles NA separately from "No diagnosis"
df_demographics <- df_demographics %>%
  mutate(post_diag_detailed_grouped = case_when(
    is.na(post_diag_detailed) ~ "Missing",  # NA → "Missing"
    TRUE ~ post_diag_detailed               # Everything else stays as is (including "No diagnosis")
  ))

# Get unique diagnosis levels (now includes "Missing" AND "No diagnosis")
diagnosis_levels <- sort(unique(df_demographics$post_diag_detailed_grouped))

# Verify the levels
cat("\n=== DIAGNOSIS LEVELS ===\n")
print(diagnosis_levels)
cat("\nSample sizes:\n")
print(table(df_demographics$post_diag_detailed_grouped, useNA = "ifany"))

# Get the levels from the OVERALL data
get_levels_from_overall <- function() {
  levels_list <- list()
  
  for (var in categorical_vars) {
    tbl <- table(df_demographics[[var]], useNA = "no")
    levels_list[[var]] <- names(tbl)
  }
  
  return(levels_list)
}

overall_levels <- get_levels_from_overall()

# Function to create Table 1 style output for one diagnosis
create_table1_group <- function(data_subset, dx_name, use_levels) {
  
  n_total <- nrow(data_subset)
  
  results <- data.frame(
    Variable = character(),
    Level = character(),
    Diagnosis = character(),
    Value = character(),
    row_order = integer(),
    stringsAsFactors = FALSE
  )
  
  current_row <- 1
  
  # Continuous variables
  for (var in continuous_vars) {
    mean_val <- mean(data_subset[[var]], na.rm = TRUE)
    sd_val <- sd(data_subset[[var]], na.rm = TRUE)
    
    results <- rbind(results, data.frame(
      Variable = var,
      Level = "Mean (SD)",
      Diagnosis = dx_name,
      Value = paste0(round(mean_val, 1), " (", round(sd_val, 1), ")"),
      row_order = current_row,
      stringsAsFactors = FALSE
    ))
    current_row <- current_row + 1
  }
  
  # Categorical variables
  for (var in categorical_vars) {
    tbl <- table(data_subset[[var]], useNA = "no")
    pct <- prop.table(tbl) * 100
    
    # Add header row
    results <- rbind(results, data.frame(
      Variable = var,
      Level = "",
      Diagnosis = dx_name,
      Value = "",
      row_order = current_row,
      stringsAsFactors = FALSE
    ))
    current_row <- current_row + 1
    
    # Add rows for levels that exist in overall
    for (level_name in use_levels[[var]]) {
      if (level_name %in% names(tbl)) {
        value_text <- paste0(tbl[level_name], " (", round(pct[level_name], 1), "%)")
      } else {
        value_text <- "0 (0%)"
      }
      
      results <- rbind(results, data.frame(
        Variable = "",
        Level = paste0("  ", level_name),
        Diagnosis = dx_name,
        Value = value_text,
        row_order = current_row,
        stringsAsFactors = FALSE
      ))
      current_row <- current_row + 1
    }
  }
  
  return(results)
}

# Create overall summary (now includes everyone)
all_data <- create_table1_group(df_demographics, "Overall", overall_levels)

# Add diagnosis-specific summaries (including both "Missing" AND "No diagnosis")
for (dx in diagnosis_levels) {
  df_subset <- df_demographics %>% 
    filter(post_diag_detailed_grouped == dx)
  
  dx_summary <- create_table1_group(df_subset, dx, overall_levels)
  all_data <- rbind(all_data, dx_summary)
}

# Pivot
demographics_wide <- all_data %>%
  select(Variable, Level, Diagnosis, Value, row_order) %>%
  pivot_wider(
    id_cols = c(Variable, Level, row_order),
    names_from = Diagnosis,
    values_from = Value
  ) %>%
  arrange(row_order) %>%
  select(-row_order)

# Get N for each diagnosis (including "Missing" AND "No diagnosis" as separate groups)
n_by_diagnosis <- df_demographics %>%
  group_by(post_diag_detailed_grouped) %>%
  summarise(N = n(), .groups = "drop") %>%
  arrange(post_diag_detailed_grouped) %>%
  add_row(post_diag_detailed_grouped = "Overall", N = nrow(df_demographics), .before = 1)

# Create column names with N
new_colnames <- c("Variable", "")
for (i in 1:nrow(n_by_diagnosis)) {
  dx <- n_by_diagnosis$post_diag_detailed_grouped[i]
  n_val <- n_by_diagnosis$N[i]
  new_colnames <- c(new_colnames, paste0(dx, " (N=", format(n_val, big.mark = ","), ")"))
}

colnames(demographics_wide) <- new_colnames

# Write to Excel
write_xlsx(demographics_wide, "demographics_by_diagnosis_with_missing_separate.xlsx")

# Print to console
print(demographics_wide)

# Print summary
cat("\n", rep("=", 70), "\n", sep = "")
cat("SUMMARY\n")
cat(rep("=", 70), "\n", sep = "")
cat(sprintf("Total N: %d\n", nrow(df_demographics)))
cat(sprintf("Missing (NA): %d (%.1f%%)\n", 
            sum(df_demographics$post_diag_detailed_grouped == "Missing"),
            100 * mean(df_demographics$post_diag_detailed_grouped == "Missing")))
cat(sprintf("No diagnosis: %d (%.1f%%)\n", 
            sum(df_demographics$post_diag_detailed_grouped == "No diagnosis", na.rm = TRUE),
            100 * mean(df_demographics$post_diag_detailed_grouped == "No diagnosis", na.rm = TRUE)))
cat(sprintf("Other diagnoses: %d (%.1f%%)\n",
            sum(!df_demographics$post_diag_detailed_grouped %in% c("Missing", "No diagnosis")),
            100 * mean(!df_demographics$post_diag_detailed_grouped %in% c("Missing", "No diagnosis"))))
cat(rep("=", 70), "\n", sep = "")