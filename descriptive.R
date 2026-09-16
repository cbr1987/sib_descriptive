#DESCRIPTIVE PLOTS FOR DATA

#BOXPLOT
library(ggplot2)

ggplot(df_filter, aes(x = ethnicity_5cat, y = adj_wmh, fill = ethnicity_5cat)) +
  geom_boxplot() +  # or geom_violin() for a smoother distribution
  labs(
    x = "Ethnicity",
    y = "Adjusted WMH",
    title = "Distribution of WMH by Ethnicity"
  ) +
  theme_minimal() +
  scale_fill_brewer(palette = "Set2") +
  theme(legend.position = "none")  # optional: hide legend since x-axis labels already show ethnicity

plot()


#PAIRWISE T TESTS TO LOOK FOR DIFFERENCE IN MEANS
# Pairwise t-tests
t_diagnosis <- pairwise.t.test(
  df_filter$adj_wmh,
  df_filter$primary_diag_latest_collapsed,
  p.adjust.method = "bonferroni",
  pool.sd = FALSE
)

t_diagnosis

write_xlsx(as.data.frame(t_diagnosis$p.value), "p_values_diag.xlsx")

library(dplyr)
library(tidyr)
library(tibble)

pvals_eth_long <- as.data.frame(t_diagnosis$p.value) %>%
  rownames_to_column(var = "Group1") %>%
  pivot_longer(-Group1, names_to = "Group2", values_to = "p_value") %>%
  filter(!is.na(p_value)) %>%
  arrange(p_value)

# Write to Excel
library(writexl)
write_xlsx(pvals_eth_long, "p_values_diag.xlsx")



#PLOTTING MEAN VASC RISK SCORE BY DIAGNOSIS
# Summarize mean and SE for each DIAGNOSIS
score_eth <- df_post %>%
  group_by(primary_diag_post_collapsed_clean) %>%
  summarize(
    mean_vasc = mean(vasc_risk_score, na.rm = TRUE),
    se_vasc = sd(vasc_risk_score, na.rm = TRUE)/sqrt(n())
  )

score_eth <- score_eth %>%
  mutate(
    primary_diag_post_collapsed_clean = factor(
      primary_diag_post_collapsed_clean,
      levels = c("Nil diagnosis recorded", "F06: Mild cognitive disorder", "F00: Alzheimers disease", "F01: Vascular dementia", "F02: Other dementia"))
  )


# Plot
ggplot(score_eth, aes(x = primary_diag_post_collapsed_clean, y = mean_vasc, color = primary_diag_post_collapsed_clean)) +
  geom_point(size = 3) +
  geom_errorbar(aes(ymin = mean_vasc - se_vasc, ymax = mean_vasc + se_vasc), width = 0.2) +
  labs(
    x = "Diagnosis",
    y = "Mean CVD score ± SE",
    title = "Mean CVD score by Diagnosis"
  ) +
  theme_minimal() +
  scale_color_brewer(palette = "Set2") +
  theme(legend.position = "none")


#PAIRWISE T TESTS TO LOOK FOR DIFFERENCE IN MEANS
# Pairwise t-tests
t_vascular <- pairwise.t.test(
  df_filter$vasc_risk_score,
  df_filter$primary_diag_latest_collapsed,
  p.adjust.method = "bonferroni",
  pool.sd = FALSE
)

t_vascular

#PLOTTING MEAN WMH BY DIAGNOSIS
# Summarize mean and SE for each DIAGNOSIS
score_wmh <- df_post %>%
  group_by(primary_diag_post_collapsed_clean) %>%
  summarize(
    mean_wmh = mean(adj_wmh, na.rm = TRUE),
    se_wmh = sd(adj_wmh, na.rm = TRUE)/sqrt(n())
  )

score_wmh <- score_wmh %>%
  mutate(
    primary_diag_post_collapsed_clean = factor(
      primary_diag_post_collapsed_clean,
      levels = c("Nil diagnosis recorded", "F06: Mild cognitive disorder", "F00: Alzheimers disease", "F01: Vascular dementia", "F02: Other dementia"))
  )

# Plot
ggplot(score_wmh, aes(x = primary_diag_post_collapsed_clean, y = mean_wmh, color = primary_diag_post_collapsed_clean)) +
  geom_point(size = 3) +
  geom_errorbar(aes(ymin = mean_wmh - se_wmh, ymax = mean_wmh + se_wmh), width = 0.2) +
  labs(
    x = "Diagnosis",
    y = "Mean Adjusted WMH volume ± SE",
    title = "Mean WMH Volume by Diagnosis"
  ) +
  theme_minimal() +
  scale_color_brewer(palette = "Set2") +
  theme(legend.position = "none")


#PLOTTING MEAN WMH BY ETHNICITY
# Summarize mean and SE for each ethnicity
wmh_eth <- df_post %>%
  group_by(ethnicity_5cat) %>%
  summarize(
    mean_wmh = mean(adj_wmh, na.rm = TRUE),
    se_wmh = sd(adj_wmh, na.rm = TRUE)/sqrt(n())
  )

wmh_eth <- wmh_eth %>%
  mutate(
    ethnicity_5cat = factor(
      ethnicity_5cat,
      levels = c("White", "Asian", "Black", "Other", "Not known"))
  )

# Plot
ggplot(wmh_eth, aes(x = ethnicity_5cat, y = mean_wmh, color = ethnicity_5cat)) +
  geom_point(size = 3) +
  geom_errorbar(aes(ymin = mean_wmh - se_wmh, ymax = mean_wmh + se_wmh), width = 0.2) +
  labs(
    x = "Ethnicity",
    y = "Mean Adjusted WMH volume ± SE",
    title = "Mean WMH Volume by Ethnicity"
  ) +
  theme_minimal() +
  scale_color_brewer(palette = "Set2") +
  theme(legend.position = "none")

# Pairwise t-tests
t_ethnicity <- pairwise.t.test(
  df_filter$adj_wmh,
  df_filter$ethnicity_5cat,
  p.adjust.method = "bonferroni",
  pool.sd = FALSE
)

t_ethnicity


#PLOTTING MEAN CVD BY ETHNICITY
# Summarize mean and SE for each ethnicity
cvd_eth <- df_post %>%
  group_by(ethnicity_5cat) %>%
  summarize(
    mean_cvd = mean(vasc_risk_score, na.rm = TRUE),
    se_cvd = sd(vasc_risk_score, na.rm = TRUE)/sqrt(n())
  )

cvd_eth <- cvd_eth %>%
  mutate(
    ethnicity_5cat = factor(
      ethnicity_5cat,
      levels = c("White", "Asian", "Black", "Other", "Not known"))
  )

# Plot
ggplot(cvd_eth, aes(x = ethnicity_5cat, y = mean_cvd, color = ethnicity_5cat)) +
  geom_point(size = 3) +
  geom_errorbar(aes(ymin = mean_cvd - se_cvd, ymax = mean_cvd + se_cvd), width = 0.2) +
  labs(
    x = "Ethnicity",
    y = "Mean CVD score ± SE",
    title = "Mean CVD score by Ethnicity"
  ) +
  theme_minimal() +
  scale_color_brewer(palette = "Set2") +
  theme(legend.position = "none")

# Pairwise t-tests
t_ethnicity <- pairwise.t.test(
  df_filter$adj_wmh,
  df_filter$ethnicity_5cat,
  p.adjust.method = "bonferroni",
  pool.sd = FALSE
)

t_ethnicity

# VISUALISING DATE OF SCAN COMPARED TO DATE OF DIAGNOSIS:

hist(df$weeks_diff_pre, main = "Distribution of Weeks Between Scan and Pre-scan Diagnosis", 
     xlab = "Weeks")
boxplot(df$weeks_diff_pre, main = "Weeks Between Scan and Diagnosis")

# Count how many are within certain ranges
table(cut(df$years_diff, breaks = c(-Inf, -5, 0, 5, Inf), 
          labels = c(">5 years before", "0-5 years before", 
                     "0-5 years after", ">5 years after")))

