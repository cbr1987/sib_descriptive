library(dplyr)
library(tidyr)
library(ggplot2)
library(writexl)

# --- 1. CALCULATE CVR ---

# pivot to long format so we can loop through IDPs cleanly
long_data <- dataset_2201 %>%
  pivot_longer(cols = starts_with("adj_"), 
               names_to = "Region", 
               values_to = "Volume")

# get control stats once
control_stats <- long_data %>%
  filter(post_diag_detailed_nafilled == "No diagnosis made") %>%
  group_by(Region) %>%
  summarise(
    mean_controls = mean(Volume, na.rm = TRUE),
    sd_controls   = sd(Volume, na.rm = TRUE),
    n_controls    = n()
  )

# CVR with FDR correction
cvr_results <- long_data %>%
  filter(post_diag_detailed_nafilled != "No diagnosis made") %>%
  group_by(post_diag_detailed_nafilled, Region) %>%
  summarise(
    mean_dx = mean(Volume, na.rm = TRUE),
    sd_dx   = sd(Volume, na.rm = TRUE),
    n_dx    = n(),
    .groups = "drop"
  ) %>%
  left_join(control_stats, by = "Region") %>%
  mutate(
    CV_dx       = sd_dx / mean_dx,
    CV_controls = sd_controls / mean_controls,
    lnCVR       = log(CV_dx / CV_controls),
    SE_lnCVR    = sqrt((1 / (2 * n_dx)) + (1 / (2 * n_controls))),
    CI_lower    = lnCVR - 1.96 * SE_lnCVR,
    CI_upper    = lnCVR + 1.96 * SE_lnCVR,
    # convert to z and then two-tailed p-value
    z_score     = lnCVR / SE_lnCVR,
    p_value     = 2 * (1 - pnorm(abs(z_score)))
  ) %>%
  # FDR correction across all tests simultaneously
  mutate(p_fdr = p.adjust(p_value, method = "BH")) %>%
  mutate(sig = p_fdr < 0.05)


write_xlsx(cvr_results, "cvr.xlsx")


# --- 2. VISUALISE AS HEATMAP ---

# order diagnoses by number of significant regions (matches your Cohen's d plot)
diag_order <- cvr %>%
  filter(sig == TRUE) %>%
  group_by(post_diag_detailed_nafilled) %>%
  summarise(n_sig = n()) %>%
  arrange(desc(n_sig)) %>%
  pull(post_diag_detailed_nafilled)

# keep all data for plotting but flag significance
cvr_plot_data <- cvr %>%
  mutate(
    Diagnosis = factor(post_diag_detailed_nafilled, levels = diag_order),
    lnCVR_plot = ifelse(sig == TRUE, lnCVR, NA)  # NA cells will plot as white
  )

ggplot(cvr_plot_data, aes(x = Diagnosis, y = Region, fill = lnCVR_plot)) +
  geom_tile(colour = "grey70", linewidth = 0.3) +  # grid lines
  scale_fill_gradient2(
    low      = "#0072B2",
    mid      = "white",
    high     = "red",
    midpoint = 0,
    name     = "ln(CVR)",
    na.value = "white"  # non-significant cells are white
  ) +
  theme_minimal() +
  theme(
    axis.text.x      = element_text(angle = 45, hjust = 1, size = 8),
    axis.text.y      = element_text(size = 8),
    panel.grid       = element_blank(),
    panel.background = element_rect(fill = "white", colour = NA),
    plot.background  = element_rect(fill = "white", colour = NA)
  ) +
  labs(
    x        = "Diagnosis",
    y        = "Brain Region",
    title    = "ln(CVR) by diagnosis and brain region",
    subtitle = "FDR-corrected significant results only. Blue = less variable than No diagnosis, Red = more variable than No diagnosis"
  )