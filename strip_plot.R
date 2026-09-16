library(readxl)
library(dplyr)
library(tidyr)
library(ggplot2)
library(patchwork)
library(stringr)

# Read Excel file
df <- read_excel(".xlsx")

# Prepare data
df_prepared <- df %>%
  filter(!is.na(p_fdr_adjusted)) %>%
  mutate(
    # Categorize regions
    region_type = case_when(
      str_starts(Region, "wmhadj_") ~ "WMH",           # WMH
      str_starts(Region, "adj_ctx") ~ "Cortical",      # Cortical
      str_starts(Region, "adj_") & !str_starts(Region, "adj_ctx") ~ "Segmentation",     # Segmentation
      TRUE ~ "other"
    ),
    # Handle zero p-values
    min_nonzero = min(p_fdr_adjusted[p_fdr_adjusted > 0], na.rm = TRUE),
    p_value_clean = ifelse(p_fdr_adjusted == 0, min_nonzero, p_fdr_adjusted),
    # Calculate -log10(p)
    neg_log_p = -log10(p_value_clean),
    # Significance
    significant = p_fdr_adjusted < 0.05,
    # Color grouping
    color_group = ifelse(significant, region_type, "non-significant"),
    color_group = factor(color_group, 
                         levels = c("WMH", "Cortical", "Segmentation", "non-significant"))
  )

# Get unique diagnoses
diagnoses <- unique(df_prepared$Diagnosis)

# Store all plots
all_plots <- list()

# Create plots for each diagnosis
for (dx in diagnoses) {
  
  cat(paste0("\nCreating plot for: ", dx, "\n"))
  
  # Filter data for this diagnosis
  df_dx <- df_prepared %>% filter(Diagnosis == dx)
  
  if (nrow(df_dx) == 0) {
    cat("  No data, skipping...\n")
    next
  }
  
  # Calculate y-limits for THIS diagnosis only
  y_max_dx <- max(df_dx$neg_log_p, na.rm = TRUE)
  y_limits_dx <- c(0, y_max_dx * 1.1)
  
  cat("  Y-axis range: 0 to", round(y_limits_dx[2], 1), "\n")
  
  # Split into two datasets
  df_wmh <- df_dx %>% filter(region_type == "WMH")
  df_synthseg <- df_dx %>% filter(region_type %in% c("Cortical", "Segmentation"))
  
  # ==========================================
  # Strip 1: WMH only
  # ==========================================
  p1 <- ggplot(df_wmh, aes(x = 1, y = neg_log_p)) +
    geom_hline(yintercept = -log10(0.05), linetype = "dashed", 
               color = "black", linewidth = 0.8) +
    geom_jitter(aes(color = color_group), width = 0.2, height = 0.3, 
                size = 2.5, alpha = 0.7) +
    scale_color_manual(
      values = c(
        "WMH" = "#1F78B4",           # blue
        "non-significant" = "grey70"
      ),
      drop = FALSE
    ) +
    scale_x_continuous(breaks = NULL, limits = c(0.5, 1.5)) +
    scale_y_continuous(
      limits = y_limits_dx,  # SAME LIMITS AS STRIP 2
      expand = expansion(mult = c(0, 0.02))
    ) +
    coord_cartesian(clip = "off") +
    labs(
      x = "WMH-SynthSeg",
      y = "-log10(p-value)"
    ) +
    theme_minimal() +
    theme(
      legend.position = "none",
      text = element_text(size = 12),
      axis.title.x = element_text(face = "bold", size = 11),
      panel.grid.major.x = element_blank(),
      panel.grid.minor.x = element_blank()
    )
  
  # ==========================================
  # Strip 2: Synthseg (Segmentation + Cortical)
  # ==========================================
  p2 <- ggplot(df_synthseg, aes(x = 1, y = neg_log_p)) +
    geom_hline(yintercept = -log10(0.05), linetype = "dashed", 
               color = "black", linewidth = 0.8) +
    geom_jitter(aes(color = color_group), width = 0.2, height = 0.3, 
                size = 2.5, alpha = 0.7) +
    scale_color_manual(
      values = c(
        "Cortical" = "#E31A1C",      # red
        "Segmentation" = "#33A02C",  # green
        "non-significant" = "grey70"
      ),
      labels = c(
        "Cortical" = "Parcellation",
        "Segmentation" = "Segmentation",
        "non-significant" = "Non-sig",
        "WMH" = "Segmentation"
      ),
      drop = FALSE
    ) +
    scale_x_continuous(breaks = NULL, limits = c(0.5, 1.5)) +
    scale_y_continuous(
      limits = y_limits_dx,  # SAME LIMITS AS STRIP 1
      expand = expansion(mult = c(0, 0.02))
    ) +
    coord_cartesian(clip = "off") +
    labs(
      x = "SynthSeg+",
      y = ""  # No y-label for second strip
    ) +
    theme_minimal() +
    theme(
      legend.position = "bottom",
      legend.title = element_blank(),
      text = element_text(size = 12),
      axis.title.x = element_text(face = "bold", size = 11),
      axis.text.y = element_blank(),  # No y-axis numbers on right plot
      axis.ticks.y = element_blank(),
      panel.grid.major.x = element_blank(),
      panel.grid.minor.x = element_blank()
    )
  
  # ==========================================
  # Combine side by side
  # ==========================================
  combined_plot <- p1 + p2 +
    plot_layout(widths = c(1, 1)) +
    plot_annotation(
      title = dx,
      theme = theme(plot.title = element_text(size = 16, face = "bold", hjust = 0.5))
    )
  
  all_plots[[dx]] <- combined_plot
}

cat("\n=== Plots created! Displaying... ===\n")

# Display all plots
for (dx in names(all_plots)) {
  print(all_plots[[dx]])
}

# ==========================================
# To save
# ==========================================
cat("\n=== To save, run: ===\n\n")

cat(for (dx in names(all_plots)) {
  dx_clean <- gsub('[:/]', '', dx)
  dx_clean <- gsub(' ', '_', dx_clean)
  
  ggsave(
    filename = paste0('pvalue_stripplot_', dx_clean, '.png'),
    plot = all_plots[[dx]],
    width = 10,
    height = 6,
    dpi = 300
  )
  
}
