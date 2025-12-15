# Corrections Den: An Analysis of *Late Night with Seth Meyers* “Corrections” Comments

The Corrections Den offers an analysis of viewer comments from the *Late Night with Seth Meyers* YouTube series “Corrections,” using TF-IDF and KMeans clustering to determine the most dominant topics in comments left throughout the series. Topic trends are visualized in Plotly to illustrate how how comment topics have evolved over the years.

---

## Overview 

- **Automated YouTube Data Collection**
  - YouTube API fetches video metadata and comments using the YouTube Data API. Only comments left on “Corrections” videos are analyzed.

- **Text Cleaning & Preprocessing**
  - Comments undergo tokenization and normalization, followed by TF-IDF vectorization.
  - Text is filtered using a custom stopword list tailored to the "Corrections" comment domain to suppress generic filler language while preserving recurring in-jokes and references.

- **Topic Clustering**
  - Comments are grouped into topics using TF-IDF and KMeans. This approach was selected after experimentation with embedding-based models, which tended to over-smooth highly referential, joke-heavy comments. TF-IDF was better suited for extracting frequently-recurring terms within a large dataset comprising many short, noisy documents.
  - Clusters are computed once on the full corpus to ensure stability. Representative keywords are extracted from each cluster centroid, and a sample of comments aid in the qualitative interpretation of topics.

- **Interactive Visualization**
  - A dynamic visualization on Plotly allows users to explore trends and frequencies by topic, date range, and frequency (daily, weekly, monthly).

## [App](https://corrections-den.streamlit.app) Preview

<!--
<p align="center">
  <img width="1619" height="874" alt="cd_daily" src="https://github.com/user-attachments/assets/d9562919-49db-4414-9002-90a6d8790aef"><br>
  <em>Daily aggregation view for October 2025</em>
</p>

<p align="center">
  <img width="1646" height="762" alt="cd_weekly_2025" src="https://github.com/user-attachments/assets/0833a0fc-68c7-4644-9c5a-7a72304fac6a"><br>
  <em>Weekly trends for 2025</em>
</p>

<p align="center">
  <img width="1622" height="879" alt="cd_monthly" src="https://github.com/user-attachments/assets/0beb014d-8a66-459d-9efa-df3c98d7c5bc"><br>
  <em>Monthly overview</em>
</p>

<p align="center">
  <img width="1622" height="879" alt="cd_monthly_2025" src="https://github.com/user-attachments/assets/743e51a9-ece9-4510-8088-005c3ac1d2a7"><br>
  <em>Monthly aggregation focused on 2025</em>
</p>
-->
<p align="center">
  <img width="1609" height="898" alt="Screenshot 2025-12-14 at 7 34 58 PM" src="https://github.com/user-attachments/assets/91d8bce6-e3fc-45c3-a54c-5183d850204e" />
  <em>Monthly view of "Corrections" topic trends from 2021 to 2025</em>
</p>



