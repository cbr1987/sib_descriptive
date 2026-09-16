library(pwr)
library(dplyr)

group_sizes <- read_excel(
  ".xlsx"
)

# your control n - set this to your actual number
n_controls <- 904

# calculate minimum detectable effect size for each diagnostic group
power_results <- group_sizes %>%
  rowwise() %>%
  mutate(
    min_detectable_d = pwr.t2n.test(
      n1 = n_diag,
      n2 = n_controls,
      sig.level = 0.05,
      power = 0.80,
      alternative = "two.sided"
    )$d
  ) %>%
  ungroup() %>%
  arrange(desc(n_diag))  # order by group size for readability

# view results
print(power_results)

write_xlsx(power_results, ".xlsx")
