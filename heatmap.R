library(ggplot2)
library(readxl)

# Edits to see how this changes things in github



my_data <- read_excel(
  "cohens_combined_t1w_above30n_detailediag.xlsx",
  sheet = "Significant_Adjusted_FDR"  # replace with your actual sheet name
)

# count significant regions per diagnosis and order factor
diagnosis_order <- my_data %>%
  group_by(Diagnosis) %>%
  summarise(n_sig = n()) %>%  # since you've already filtered to significant only, just count rows
  arrange(desc(n_sig)) %>%
  pull(Diagnosis)

# apply the order as a factor
my_data <- my_data %>%
  mutate(Diagnosis = factor(Diagnosis, levels = diagnosis_order))

ggplot(my_data, aes(x = Diagnosis, y = Region, fill = Cohens_d_adjusted)) +
  geom_tile(colour = "grey90") +  # grey borders keep the grid visible for blank cells
  scale_fill_gradient2(
    low = "#0072B2", 
    mid = "white", 
    high = "red", 
    midpoint = 0,
    name = "Cohen's d adjusted"
  ) +
  theme_minimal() +
  theme(
    axis.text.x = element_text(angle = 45, hjust = 1, size = 8),
    axis.text.y = element_text(size = 8),
    panel.grid = element_blank(),
    panel.background = element_rect(fill = "white", colour = NA)
  ) +
  labs(x = "Diagnosis", y = "Brain Region")

# Some other changes to test out github