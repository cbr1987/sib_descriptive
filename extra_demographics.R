library(dplyr)
library(writexl)
library(tidyr)

# Filter your data first
df_subset <- df %>% filter(primary_diag_post_collapsed_clean == "F01: Vascular dementia")

# Continuous variables - mean and SD
continuous_vars <- c("age_at_scan_date", "IMD_Score_2019_closest_to_scan")  # specify your variables

cont_summary <- df_subset %>%
  summarise(across(all_of(continuous_vars), 
                   list(mean = ~mean(., na.rm = TRUE),
                        sd = ~sd(., na.rm = TRUE)))) %>%
  pivot_longer(everything(), 
               names_to = c("Variable", "Statistic"),
               names_sep = "_(?=[^_]+$)") %>%
  pivot_wider(names_from = Statistic, values_from = value)

# Categorical variables - counts and proportions
categorical_vars <- c("Gender_ID", "ethnicity_5cat", "hypertension", "Cerebrovascular_accident", "Diabetes_mellitus", "Ischemic_heart_disease", "Heart_failure", "Atrial_fibrillation", "Coronary_arteriosclerosis", "Transient_ischemic_attack")  # specify your variables

cat_summary <- df_subset %>%
  select(all_of(categorical_vars)) %>%
  mutate(across(everything(), as.character)) %>% 
  pivot_longer(everything(), names_to = "Variable", values_to = "Category") %>%
  group_by(Variable, Category) %>%
  summarise(n = n(), .groups = "drop") %>%
  group_by(Variable) %>%
  mutate(proportion = n / sum(n),
         percent = proportion * 100)

# Write to Excel with multiple sheets
write_xlsx(list(
  Continuous = cont_summary,
  Categorical = cat_summary
), "demographics_otherdem_post.xlsx")