library(ggplot2)
library(readxl)
library(ggforce)

# Read your Excel file
diagnosis_stats <- read_excel(".xlsx")

# Convert NA in diagnosis column to "Missing" FIRST
diagnosis_stats <- diagnosis_stats %>%
  mutate(diagnosis = case_when(
    is.na(diagnosis) ~ "Missing",
    diagnosis == "NA" ~ "Missing",
    diagnosis == "" ~ "Missing",
    TRUE ~ as.character(diagnosis)  # <-- Make sure it's character
  ))

# Check what diagnoses you actually have
print("Diagnoses in your data:")
print(unique(diagnosis_stats$diagnosis))

# Define the order - INCLUDE ALL DIAGNOSES FROM YOUR DATA
diagnosis_order <- c(
  # Red (Dementias)
  'F00: Alzheimers disease',
  'F01: Vascular dementia',
  'F02: Other dementia',
  'F06: Mild cognitive disorder',
  
  # Blue (Psychotic)
  'F31: Bipolar affective disorder',
  'F20: Schizophrenia',
  'F25: Schizoaffective disrder',
  'F28_29: Other unspecified psychosis',
  
  # Orange (Depression/Neurotic)
  'F32-33: Depression',
  'F33: Recurrent depressive disorder',
  'Other mood disorder',
  'F40-48: Neurotic disorders',
  
  # Purple (Developmental)
  'Developmental disorders',
  'F90-98: Disorders of childhood',
  
  # Green (Substance/Personality)
  'Other mental disorder unspecified',
  'Psychosocial stressors/Selfharm',
  'F10-19: Substance disorders',
  'F50: Behavioural syndromes',
  'F60-69: Personality disorder',
  
  # Yellow (Neurological/Medical)
  'Other neurological disease',
  'Other medical',
  'Other organic brain disorder',
  
  # Grey/Black (No diagnosis/Missing)
  'No diagnosis made',
  'Missing',
  'Examination or procedure code'
)

# Only convert to factor AFTER checking all diagnoses are in the list
# Check if any diagnoses are missing from the order
missing_from_order <- setdiff(diagnosis_stats$diagnosis, diagnosis_order)
if (length(missing_from_order) > 0) {
  cat("WARNING: These diagnoses are in your data but not in diagnosis_order:\n")
  print(missing_from_order)
  cat("\nAdding them to the end of the order...\n")
  diagnosis_order <- c(diagnosis_order, missing_from_order)
}

# Now convert to factor
diagnosis_stats$diagnosis <- factor(diagnosis_stats$diagnosis, 
                                    levels = diagnosis_order)
# The legend will follow this order

# Define color groups (adjust column names if needed)
diagnosis_stats <- diagnosis_stats %>%
  mutate(
    color_group = case_when(
      diagnosis %in% c('No diagnosis made', 'Missing', 'Examination or procedure code') ~ 'Grey/Black',
      diagnosis %in% c('Other neurological disease', 'Other medical', 'Other organic brain disorder') ~ 'Yellow',
      diagnosis %in% c('F00: Alzheimers disease', 'F01: Vascular dementia', 'F02: Other dementia', 'F06: Mild cognitive disorder') ~ 'Red',
      diagnosis %in% c('Other mental disorder unspecified', 'Psychosocial stressors/Selfharm', 
                       'F10-19: Substance disorders', 'F50: Behavioural syndromes', 
                       'F60-69: Personality disorder') ~ 'Green',
      diagnosis %in% c('F32-33: Depression', 'Other mood disorder', 'F40-48: Neurotic disorders', 
                       'F33: Recurrent depressive disorder') ~ 'Brown',
      diagnosis %in% c('Developmental disorders', 'F90-98: Disorders of childhood') ~ 'Purple',
      diagnosis %in% c('F31: Bipolar affective disorder', 'F20: Schizophrenia', 
                       'F25: Schizoaffective disrder', 'F28_29: Other unspecified psychosis') ~ 'Blue',
      TRUE ~ 'Other'
    ),
    n = as.numeric(n),
        # Use SE instead of SD (much smaller)
    radius_PC1 = 1.96 * (`PC1 std` / sqrt(n)),  # SE = SD / sqrt(n)
    radius_PC2 = 1.96 * (`PC2 std` / sqrt(n))

  )

# Create gradient within groups based on PC1
diagnosis_stats <- diagnosis_stats %>%
  group_by(color_group) %>%
  mutate(
    pc1_normalized = (`PC1 mean` - min(`PC1 mean`)) / (max(`PC1 mean`) - min(`PC1 mean`) + 0.001)
  ) %>%
  ungroup()

# Base colors
base_colors <- c(
  'Grey/Black' = '#2b2b2b',
  'Yellow' = '#FDB462',
  'Red' = '#E31A1C',
  'Green' = '#33A02C',
  'Brown' = '#8B4513',
  'Purple' = '#6A3D9A',
  'Blue' = '#1F78B4'
)

# Apply gradient
library(colorspace)
diagnosis_stats <- diagnosis_stats %>%
  rowwise() %>%
  mutate(
    point_color = lighten(base_colors[color_group], amount = 0.6 - (pc1_normalized * 0.6))
  ) %>%
  ungroup()


# Start the plot
p <- ggplot(diagnosis_stats, aes(x = `PC1 mean`, y = `PC2 mean`))

# Add ellipses one by one
for (i in 1:nrow(diagnosis_stats)) {
  p <- p + geom_ellipse(
    data = diagnosis_stats[i, ],
    aes(x0 = `PC1 mean`, y0 = `PC2 mean`, 
        a = radius_PC1, b = radius_PC2, 
        angle = 0),
    fill = diagnosis_stats$point_color[i],
    alpha = 0.2, 
    color = NA
  )
}

# Add the rest of the plot
p <- p +
  # Mean points
  geom_point(aes(fill = diagnosis), 
             size = 5, shape = 21, 
             color = 'black', stroke = 0.8) +
  # Manual fill scale
  scale_fill_manual(
    values = setNames(diagnosis_stats$point_color, diagnosis_stats$diagnosis),
    name = "Diagnosis"
  ) +
  # Axes and labels
  labs(
    x = "PC1 (22.7% variance)",
    y = "PC2 (8.6% variance)",
    title = "Mean PC Scores by Diagnosis",
    subtitle = "Points = means; ellipses = 95% CI; color intensity = PC1 strength"
  ) +
  # Reference lines
  geom_hline(yintercept = 0, linetype = "dashed", color = "gray50", alpha = 0.5) +
  geom_vline(xintercept = 0, linetype = "dashed", color = "gray50", alpha = 0.5) +
  # Theme
  theme_minimal(base_size = 12) +
  theme(
    legend.position = "right",
    legend.text = element_text(size = 8),
    legend.title = element_text(size = 10, face = "bold"),
    plot.title = element_text(size = 14, face = "bold"),
    panel.grid.major = element_line(color = "gray90"),
    panel.grid.minor = element_blank(),
    axis.title = element_text(size = 12, face = "bold")
  ) +
  guides(fill = guide_legend(override.aes = list(alpha = 1, size = 4)))

print(p)

# Save
ggsave("pc_means_by_diagnosis.pdf", p, width = 14, height = 10, dpi = 300)

# WITH ERROR BARS INSTEAD
p <- ggplot(diagnosis_stats, aes(x = `PC1 mean`, y = `PC2 mean`)) +
  # Error bars (95% CI) - colored to match points
  geom_errorbar(aes(ymin = `PC2 mean` - 1.96*`PC2 std`/sqrt(n),
                    ymax = `PC2 mean` + 1.96*`PC2 std`/sqrt(n),
                    color = diagnosis),  # <-- Added color
                width = 0, alpha = 0.3) +
  geom_errorbarh(aes(xmin = `PC1 mean` - 1.96*`PC1 std`/sqrt(n),
                     xmax = `PC1 mean` + 1.96*`PC1 std`/sqrt(n),
                     color = diagnosis),  # <-- Added color
                 height = 0, alpha = 0.3) +
  # Points
  geom_point(aes(fill = diagnosis), 
             size = 5, shape = 21, color = 'black', stroke = 0.8) +
  # Color scale for error bars
  scale_color_manual(
    values = setNames(diagnosis_stats$point_color, diagnosis_stats$diagnosis),
    guide = "none"  # Don't show in legend
  ) +
  # Fill scale for points
  scale_fill_manual(
    values = setNames(diagnosis_stats$point_color, diagnosis_stats$diagnosis),
    name = "Diagnosis"
  ) +
  geom_hline(yintercept = 0, linetype = "dashed", alpha = 0.5) +
  geom_vline(xintercept = 0, linetype = "dashed", alpha = 0.5) +
  labs(x = "PC1 (22.7%)", y = "PC2 (8.6%)",
       title = "Mean PC Scores by Diagnosis",
       subtitle = "Error bars = 95% CI") +
  theme_minimal(base_size = 12) +
  theme(
    legend.position = "right",
    legend.text = element_text(size = 8),
    legend.title = element_text(size = 10, face = "bold")
  ) +
  guides(fill = guide_legend(override.aes = list(alpha = 1, size = 4)))

print(p)

ggsave("pc_means_errorbars.pdf", p, width = 14, height = 10, dpi = 300)


# PC scores within and between diagnosis variance in PC1

library(ggplot2)
library(dplyr)
library(readxl)

# Read your Excel file
diagnosis_stats <- read_excel(".xlsx")

# Calculate within-variance from std
diagnosis_stats <- diagnosis_stats %>%
  mutate(
    within_var = (`PC1 std`)^2 + (`PC2 std`)^2
  )

# Calculate between-diagnosis variance from means
between_var <- var(diagnosis_stats$`PC1 mean`) + var(diagnosis_stats$`PC2 mean`)

# Sort by within_var (highest to lowest)
diagnosis_stats <- diagnosis_stats %>%
  arrange(desc(within_var)) %>%
  mutate(diagnosis = factor(diagnosis, levels = diagnosis))

# Calculate mean ratio
mean_ratio <- mean(diagnosis_stats$within_var) / between_var

# Base colors
base_colors <- c(
  'Grey/Black' = '#2b2b2b',
  'Yellow' = '#FDB462',
  'Red' = '#E31A1C',
  'Green' = '#33A02C',
  'Brown' = '#8B4513',
  'Purple' = '#6A3D9A',
  'Blue' = '#1F78B4',
  'Other' = '#CCCCCC'
)

library(ggplot2)
library(dplyr)
library(readxl)

# Read your Excel file
diagnosis_stats <- read_excel(".xlsx")

# Calculate within-variance from std
diagnosis_stats <- diagnosis_stats %>%
  mutate(
    within_var = (`PC1 std`)^2 + (`PC2 std`)^2
  )

# Calculate between-diagnosis variance from means
between_var <- var(diagnosis_stats$`PC1 mean`) + var(diagnosis_stats$`PC2 mean`)

# Sort by within_var (highest to lowest)
diagnosis_stats <- diagnosis_stats %>%
  arrange(desc(within_var)) %>%
  mutate(diagnosis = factor(diagnosis, levels = diagnosis))

# Calculate mean ratio
mean_ratio <- mean(diagnosis_stats$within_var) / between_var

# Store number of diagnoses
n_diagnoses <- nrow(diagnosis_stats)

# Base colors
base_colors <- c(
  'Grey/Black' = '#2b2b2b',
  'Yellow' = '#FDB462',
  'Red' = '#E31A1C',
  'Green' = '#33A02C',
  'Brown' = '#8B4513',
  'Purple' = '#6A3D9A',
  'Blue' = '#1F78B4',
  'Other' = '#CCCCCC'
)

# Create plot
p <- ggplot(diagnosis_stats, aes(x = diagnosis, y = within_var, fill = color_group)) +
  # Bars - transparent, no outline
  geom_col(alpha = 0.5) +
  # Between-diagnosis variance line - FULL WIDTH like meta-analysis line of no effect
  annotate('segment', x = -Inf, xend = Inf, y = between_var, yend = between_var,
           color = 'black', linetype = 'dashed', linewidth = 1.2) +
  # Add ratio annotation at top
  annotate('text', x = n_diagnoses / 2, 
           y = max(diagnosis_stats$within_var) * 0.95,
           label = sprintf('Mean ratio = %.1f:1', mean_ratio),
           size = 5.5, fontface = 'bold',
           color = 'black') +
  # Between-variance label overlaid on line - BLACK
  annotate('text', x = 2, y = between_var * 1.08,
           label = sprintf('Between-diagnosis variance = %.2f', between_var),
           size = 3.5, color = 'black', fontface = 'bold', hjust = 0) +
  # Color scale
  scale_fill_manual(
    values = base_colors,
    name = 'Diagnostic Category',
    labels = c('Grey/Black' = 'No diagnosis/Missing',
               'Yellow' = 'Neurological/Medical',
               'Red' = 'Neurodegenerative/Memory',
               'Green' = 'Substance/Personality',
               'Brown' = 'Depression/Neurotic',
               'Purple' = 'Developmental',
               'Blue' = 'Psychotic')
  ) +
  # Labels
  labs(
    x = '',
    y = 'Within-Diagnosis Variance (PC1 + PC2)',
    title = 'Within-Diagnosis Compared to Between-Diagnosis Variance',
    subtitle = sprintf('Mean within: %.2f | Between: %.2f | Ratio: %.1f:1',
                       mean(diagnosis_stats$within_var), between_var, mean_ratio)
  ) +
  # Flip coordinates
  coord_flip() +
  # Theme
  theme_minimal(base_size = 12) +
  theme(
    plot.title = element_text(size = 15, face = 'bold', hjust = 0.5),
    plot.subtitle = element_text(size = 11, hjust = 0.5, color = 'gray30'),
    axis.text.y = element_text(size = 9, color = 'black'),
    axis.text.x = element_text(size = 11, color = 'black'),
    axis.title.x = element_text(size = 12, face = 'bold'),
    legend.position = 'bottom',
    legend.title = element_text(size = 11, face = 'bold'),
    legend.text = element_text(size = 10),
    panel.grid.major.x = element_line(color = 'gray90'),
    panel.grid.minor = element_blank(),
    panel.grid.major.y = element_blank()
  ) +
  guides(fill = guide_legend(nrow = 1))

# Print
print(p)

# Save
ggsave('within_between_variance.pdf', p, width = 14, height = 10, dpi = 300)


# Print statistics
cat("\n=== VARIANCE STATISTICS ===\n")
cat(sprintf("Mean within-diagnosis variance: %.2f\n", mean(diagnosis_stats$within_var)))
cat(sprintf("Between-diagnosis variance: %.2f\n", between_var))
cat(sprintf("Ratio: %.1f:1\n", mean_ratio))