# CLEANING

df <- anon_singleid_qual_t1wt2w_cleandiag_1301

df$primary_diag_post_collapsed <- df$primary_diag_post_collapsed_y
df$primary_diag_latest_collapsed <- df$primary_diag_latest_collapsed_y
df$primary_diag_pre_collapsed <- df$primary_diag_pre_collapsed_y

# Fill unspecified or no diagnosis with whatever was in pre and latest:
df$primary_diag_post_collapsed_clean <- df$primary_diag_post_collapsed

# Use which() to avoid NA issues
rows_to_replace <- which(
  df$primary_diag_post_collapsed_clean == "Missing" & 
    !is.na(df$primary_diag_pre_collapsed) & 
    !is.na(df$primary_diag_latest_collapsed) &
    df$primary_diag_pre_collapsed == df$primary_diag_latest_collapsed
)

df$primary_diag_post_collapsed_clean[rows_to_replace] <- df$primary_diag_pre_collapsed[rows_to_replace]

rows_to_replace <- which(
  is.na(df1$post_diag_detailed) & 
    !is.na(df1$primary_diag_pre_collapsed) & 
    !is.na(df1$primary_diag_latest_collapsed) &
    df1$primary_diag_pre_collapsed == df1$primary_diag_latest_collapsed
)

df1$post_diag_detailed_nafilled <- df1$post_diag_detailed

df1$post_diag_detailed_nafilled[rows_to_replace] <- df1$primary_diag_latest_collapsed[rows_to_replace]

#Fill unspecified or no diagnosis with pre if latest is also unspecified:
df$primary_diag_post_collapsed_clean[df$primary_diag_post_collapsed_clean == "Unspecified or no diagnosis" & 
                                       df$primary_diag_latest_collapsed == "Unspecified or no diagnosis"] <- 
  df$primary_diag_pre_collapsed[df$primary_diag_post_collapsed_clean == "Unspecified or no diagnosis" & 
                                  df$primary_diag_latest_collapsed == "Unspecified or no diagnosis"]

#Fill unspecified or no diagnosis with latest if pre is also unspecified:
df$primary_diag_post_collapsed_clean[df$primary_diag_post_collapsed_clean == "Unspecified or no diagnosis" & 
                                       df$primary_diag_pre_collapsed == "Unspecified or no diagnosis"] <- 
  df$primary_diag_latest_collapsed[df$primary_diag_post_collapsed_clean == "Unspecified or no diagnosis" & 
                                  df$primary_diag_pre_collapsed == "Unspecified or no diagnosis"]


# Fill unspecified or no diagnosis with pre if latest is also unspecified:
rows_to_replace1 <- which(
  df$primary_diag_post_collapsed_clean == "Unspecified or no diagnosis" & 
    !is.na(df$primary_diag_latest_collapsed) &
    df$primary_diag_latest_collapsed == "Unspecified or no diagnosis" &
    !is.na(df$primary_diag_pre_collapsed)
)
df$primary_diag_post_collapsed_clean[rows_to_replace1] <- df$primary_diag_pre_collapsed[rows_to_replace1]

# Fill unspecified or no diagnosis with latest if pre is also unspecified:
rows_to_replace2 <- which(
  df$primary_diag_post_collapsed_clean == "Unspecified or no diagnosis" & 
    !is.na(df$primary_diag_pre_collapsed) &
    df$primary_diag_pre_collapsed == "Unspecified or no diagnosis" &
    !is.na(df$primary_diag_latest_collapsed)
)
df$primary_diag_post_collapsed_clean[rows_to_replace2] <- df$primary_diag_latest_collapsed[rows_to_replace2]


rows_to_replace <- which(
  is.na(df$primary_diag_post_collapsed_clean) & 
    !is.na(df$primary_diag_pre_collapsed) | 
    !is.na(df$primary_diag_latest_collapsed) &
    df$primary_diag_pre_collapsed == "F00: Alzheimers disease" | df$primary_diag_latest_collapsed == "F00: Alzheimers disease"
)

df$primary_diag_post_collapsed_clean[rows_to_replace] <- df$primary_diag_pre_collapsed[rows_to_replace]


#Add in a time constraint to replacing unspecified or no diagnosis in the post column:

# Base R version
df$primary_diag_post_collapsed_clean[
  df$primary_diag_post_collapsed_clean == "Missing" & 
    df$primary_diag_pre_collapsed != "Missing" & 
    df$primary_diag_latest_collapsed == "Missing" &
    abs(as.numeric(difftime(df$Scan_Date, df$Diagnosis_Date_Pre, units = "days"))) <= 365.25 * 5
] <- df$primary_diag_pre_collapsed[
  df$primary_diag_post_collapsed_clean == "Missing" & 
    df$primary_diag_pre_collapsed != "Missing" & 
    df$primary_diag_latest_collapsed == "Mssing" &
    abs(as.numeric(difftime(df$Scan_Date, df$Diagnosis_Date_Pre, units = "days"))) <= 365.25 * 5
]


# Create df subset with only the remaining unspecified

df_subset <- df[df$primary_diag_post_collapsed_clean == 'Unspecified or no diagnosis', ]

# Replace values that are still unspecified 

# Create a helper column to determine which value to use
df$replacement_value <- ifelse(
  df$primary_diag_latest_collapsed != "Missing" & 
    abs(as.numeric(difftime(df$Scan_Date, df$Diagnosis_Date_latest, units = "days"))) <= 365.25 * 5,
  df$primary_diag_latest_collapsed,  # Use Latest if available and within 5 years
  ifelse(
    df$primary_diag_pre_collapsed != "Missing" & 
      abs(as.numeric(difftime(df$Scan_Date, df$Diagnosis_Date_Pre, units = "days"))) <= 365.25 * 5,
    df$primary_diag_pre_collapsed,  # Otherwise use Pre if available and within 5 years
    NA  # Neither is available
  )
)

# Now fill the post diagnosis
df$primary_diag_post_collapsed_clean[
  df$primary_diag_post_collapsed_clean == "Missing" & 
    !is.na(df$replacement_value)
] <- df$replacement_value[
  df$primary_diag_post_collapsed_clean == "Missing" & 
    !is.na(df$replacement_value)
]

# Clean up helper column
df$replacement_value <- NULL


# MAKE A 'TRUER' NO DIAGNOSIS GROUP:

df$primary_diag_post_collapsed_clean[df$primary_diag_post_collapsed_clean == "Unspecified or no diagnosis" & 
                                       df$primary_diag_pre_collapsed == "Unspecified or no diagnosis" & df$primary_diag_latest_collapsed == "Unspecified or no diagnosis"] <- "Nil diagnosis recorded"

#Including NA:
rows_to_replace <- which(
  (is.na(df$primary_diag_post_collapsed_clean) | 
     df$primary_diag_post_collapsed_clean == "Unspecified or no diagnosis") & 
    (is.na(df$primary_diag_pre_collapsed) | 
       df$primary_diag_pre_collapsed == "Unspecified or no diagnosis") &
    (is.na(df$primary_diag_latest_collapsed) | 
       df$primary_diag_latest_collapsed == "Unspecified or no diagnosis")
)

df$primary_diag_post_collapsed_clean[rows_to_replace] <- "Nil diagnosis recorded"

# Cleaner dplyr version
library(dplyr)

df <- df %>%
  mutate(
    days_pre_to_scan = as.numeric(difftime(scan_date, primary_diag_pre_date, units = "days")),
    days_latest_to_scan = as.numeric(difftime(scan_date, primary_diag_latest_date, units = "days")),
    primary_diag_post_collapsed_clean = if_else(
      primary_diag_post_collapsed_clean == "Unspecified or no diagnosis" & 
        primary_diag_pre_collapsed == primary_diag_latest_collapsed &
        abs(days_pre_to_scan) <= 365.25 * 5 &
        abs(days_latest_to_scan) <= 365.25 * 5,
      primary_diag_pre_collapsed,
      primary_diag_post_collapsed_clean
    )
  ) %>%
  select(-days_pre_to_scan, -days_latest_to_scan)  # Remove temporary columns


#CONVERT DATES TO CORRECT NUMBERS:

# If your date column is called 'scan_date'
df$Scan_Date <- as.Date(as.numeric(df$Scan_Date), origin = "1899-12-30")

# Do this for all your date columns:
df$Diagnosis_Date_latest <- as.Date(as.numeric(df$Diagnosis_Date_latest), origin = "1899-12-30")
df$Diagnosis_Date_Pre <- as.Date(as.numeric(df$Diagnosis_Date_Pre), origin = "1899-12-30")
df$Diagnosis_Date_Post <- as.Date(as.numeric(df$Diagnosis_Date_Post), origin = "1899-12-30")

# RENAME dementia categories:
df_post$primary_diag_post_collapsed_clean[df_post$primary_diag_post_collapsed_clean == "F03: Unspecified dementia"] <- "F02: Other dementia"


# DETERMINE DURATION BETWEEN DIAGNOSIS AND SCAN DATE:

df$weeks_diff_latest <- as.numeric(difftime(df$Diagnosis_Date_latest, df$Scan_Date, units = "weeks"))
df$weeks_diff_post <- as.numeric(difftime(df$Diagnosis_Date_Post, df$Scan_Date, units = "weeks"))
df$weeks_diff_pre <- as.numeric(difftime(df$Diagnosis_Date_Pre, df$Scan_Date, units = "weeks"))

# Convert character to numeric

df <- df %>%
  mutate(
    age_at_scan_date = as.numeric(age_at_scan_date),
    IMD_Score_2019_closest_to_scan = as.numeric(IMD_Score_2019_closest_to_scan)
  )



