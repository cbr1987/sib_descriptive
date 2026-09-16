library(cluster)
library(factoextra)
library(tidyverse)
library(ggplot2)

# assuming your residualised volume measures are in a dataframe called df_volumes

df_volumes <- scaled_residuals_for_clustering

# scale the data first
df_scaled <- scale(X0605_residuals_scaled)

df_scaled <- X0605_residuals_scaled

# compute silhouette width for k = 2 to 10
sil_widths <- data.frame(k = 2:10, avg_sil = NA)

for (i in 2:10) {
  # hierarchical clustering
  hc <- hclust(dist(df_scaled), method = "ward.D2")  # change method if needed
  clusters <- cutree(hc, k = i)
  sil <- silhouette(clusters, dist(df_scaled))
  sil_widths$avg_sil[i - 1] <- mean(sil[, 3])
}

# plot average silhouette width by k
ggplot(sil_widths, aes(x = k, y = avg_sil)) +
  geom_line(colour = "#4C72B0", linewidth = 1) +
  geom_point(colour = "#4C72B0", size = 3) +
  geom_hline(yintercept = 0.5, linetype = "dashed", colour = "red") +  # 0.5 = reasonable structure threshold
  scale_x_continuous(breaks = 2:10) +
  labs(
    title = "Average silhouette width by number of clusters",
    x = "Number of clusters (k)",
    y = "Average silhouette width",
    caption = "Dashed line indicates threshold for reasonable cluster structure (0.5)"
  ) +
  theme_minimal() +
  theme(
    plot.title = element_text(size = 13),
    axis.title = element_text(size = 11),
    axis.text = element_text(size = 10)
  )

# save as svg
ggsave(".svg", format = "svg", width = 7, height = 5, dpi = 300)

# also print the values so you can report them
print(sil_widths)