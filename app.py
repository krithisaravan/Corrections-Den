import os
import streamlit as st
import pandas as pd
from datetime import timedelta
from dateutil.relativedelta import relativedelta
import plotly.express as px

from comment_analysis import generate_comment_analysis
from visualize_topics import load_comments 

st.set_page_config(
    page_title="Corrections Den",
    layout="wide"
)

st.markdown(
    """
    <style>
    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI",
                     Roboto, Helvetica, Arial, sans-serif;
    }
    .kpi-container {
        display: flex;
        justify-content: center;
        gap: 4rem;
        margin-top: 1.5rem;
        margin-bottom: 2rem;
    }
    .kpi-box {
        text-align: center;
    }
    .kpi-value {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1f4fd8;
    }
    .kpi-label {
        font-size: 0.9rem;
        color: #555;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <h1 style="text-align: center; margin-bottom: 0.75rem;">
        Welcome to the Corrections Den.
    </h1>

    <p style="
        text-align: center;
        max-width: 900px;
        margin: 0 auto 2.5rem auto;
        font-size: 1.05rem;
        line-height: 1.6;
        color: rgba(255, 255, 255, 0.85);
    ">
        <em> Corrections Den </em> analyzes YouTube comments from Seth Meyer's YouTube-only segment “Corrections," 
        grouping thousands of viewer remarks into the most frequently-recurring themes (identified using TF-IDF and K-means clustering) 
        and tracking how those topics evolve over time. Explore daily, weekly, or monthly trends to see what audiences fixate on and how 
        conversation has shifted across episodes.
    </p>
    """,
    unsafe_allow_html=True
)

# Sidebar controls
with st.sidebar:
    st.header("Data Controls")

    if st.button("Refresh data (uses YouTube quota)"):
        with st.spinner("Fetching new comments from YouTube…"):
            generate_comment_analysis()
        st.cache_data.clear()
        st.success("Data refreshed. Reload the page.")

# Load cached data (already clustered)
@st.cache_data(ttl=86400)
def load_cached_comments():
    path = "data/processed/corrections_comments.csv"
    if not os.path.exists(path):
        st.error(
            "Data file not found.\n\n"
            "Click **Refresh data** in the sidebar to initialize."
        )
        st.stop()
    df = pd.read_csv(path)
    return df

df = load_cached_comments()

# Metadata
df["date"] = pd.to_datetime(df["publishedAt"], errors="coerce")
if df["date"].dt.tz is not None:
    df["date"] = df["date"].dt.tz_localize(None)

min_date = df["date"].min().date()
max_date = df["date"].max().date()

# KPIs
total_comments = len(df)
total_videos = df["video_id"].nunique()

st.markdown(
    f"""
    <div class="kpi-container">
        <div class="kpi-box">
            <div class="kpi-value">{total_comments:,}</div>
            <div class="kpi-label">Total Comments</div>
        </div>
        <div class="kpi-box">
            <div class="kpi-value">{total_videos}</div>
            <div class="kpi-label">Corrections Videos</div>
        </div>
        <div class="kpi-box">
            <div class="kpi-value">{min_date.year}–{max_date.year}</div>
            <div class="kpi-label">Date Range</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# Date range selector
st.subheader("Select Date Range")

start_date, end_date = st.slider(
    "Date range",
    min_value=min_date,
    max_value=max_date,
    value=(min_date, max_date),
    format="YYYY-MM-DD"
)

df_filtered = df[
    (df["date"].dt.date >= start_date) &
    (df["date"].dt.date <= end_date)
].copy()

# Assign cluster labels in accordance with comment_analysis.py output
cluster_labels = {
    0: "Joke Reactions",
    1: "Animal Flubs & Recurring Bits",
    2: "Commentary or Corrections on Corrections",
    3: "Jackals References and Merchandise",
    4: "LNSM Crew Reactions"
}

df_filtered["topic_label"] = df_filtered["cluster"].map(cluster_labels)

# Aggregation selector
st.subheader("Aggregation Frequency")
freq_option = st.selectbox("Frequency", ["Daily", "Weekly", "Monthly"])

if freq_option == "Weekly":
    week_end_day = st.selectbox("Week ends on", ["SUN","MON","TUE","WED","THU","FRI","SAT"])
    freq = f"W-{week_end_day}"
elif freq_option == "Monthly":
    freq = None
else:
    freq = "D"

# Aggregation
if freq_option == "Monthly":
    start_ts = pd.Timestamp(start_date)
    end_ts = pd.Timestamp(end_date)

    month_starts = []
    current = start_ts
    while current <= end_ts:
        month_starts.append(current)
        current += relativedelta(months=1)
    month_starts.append(end_ts + timedelta(days=1))

    df_filtered["month_start"] = pd.cut(
        df_filtered["date"],
        bins=month_starts,
        labels=month_starts[:-1],
        right=False
    )
    df_filtered["month_start"] = pd.to_datetime(df_filtered["month_start"])
    group_col = "month_start"
else:
    group_col = "date"

topic_trends = (
    df_filtered
    .groupby(
        [pd.Grouper(key=group_col, freq=freq) if freq else group_col,
         "topic_label"]
    )
    .size()
    .reset_index(name="comment_count")
)

if freq_option == "Monthly":
    topic_trends = topic_trends.rename(columns={"month_start": "date"})

# Plot
lnsm_palette = [
    "#1f4fd8", "#e63946", "#457b9d", "#2a9d8f", "#f4a261", "#6d597a"
]

fig = px.line(
    topic_trends,
    x="date",
    y="comment_count",
    color="topic_label",
    markers=True,
    color_discrete_sequence=lnsm_palette,
    title=f"Comment Topics Over Time ({freq_option})",
    labels={"date": "Date", "comment_count": "Comment Count", "topic_label": "Topic"}
)

fig.update_layout(template="plotly_white", hovermode="x unified",
                  legend_title_text="Topics", width=1600)

fig.update_xaxes(tickangle=-45, showline=True, mirror=True, linecolor="black")
fig.update_yaxes(showline=True, mirror=True, linecolor="black")

# WGA strike annotation
strike_start = pd.Timestamp("2023-05-02")
strike_end = pd.Timestamp("2023-09-27")
if (end_date >= strike_start.date()) and (start_date <= strike_end.date()):
    fig.add_vrect(
        x0=strike_start, x1=strike_end,
        fillcolor="#FF6F61", opacity=0.25, layer="below", line_width=0,
        annotation_text="WGA Strike 2023", annotation_position="top left",
        annotation_font=dict(color="white", size=12)
    )

st.plotly_chart(fig, use_container_width=True)
