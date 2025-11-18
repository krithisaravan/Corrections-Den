# Corrections Den: An Analysis of *Late Night with Seth Meyers* “Corrections” Comments

This project analyzes viewer comments from the *Late Night with Seth Meyers* YouTube series “Corrections” to uncover recurring themes, audience reactions, and trends in comments over time. Using NLP techniques like TF-IDF, sentence embeddings, and KMeans clustering, the app visualizes how comment topics evolve across episodes.

---

## Features 

- **Automated YouTube Data Collection**
  - Fetches video metadata and comments using the YouTube Data API.
  - Filters for “Corrections” videos specifically.

- **Text Cleaning & Preprocessing**
  - Removes noise (links, punctuation, emojis).
  - Normalizes and tokenizes viewer comments.

- **Topic Clustering**
  - Groups comments into topics using sentence embeddings and KMeans.
  - Identifies representative keywords and sample comments per cluster.

- **Interactive Visualization (App)**
  - Explore trends and frequencies by topic, date range, and frequency (daily, weekly, monthly).
  - Built with Plotly for dynamic, interactive visualizations.

## App Preview

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

