import os
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import plotly.express as px

from visualize_topics import (
    load_comments,
    cluster_comments,
    get_top_keywords_per_cluster
)
from comment_analysis import generate_comment_analysis

# --------------------------------------
# Page config
# --------------------------------------
st.set_page_config(
    page_title="Corrections Den",
    layout="wide"
)

# --------------------------------------
# Header
# --------------------------------------
st.markdown(
    """
    <div style="text-align:center">
        <h1 style="margin-bottom:0.2em;">
            Corrections Den
        </h1>
        <h3 style="font-weight:400; margin-top:0;">
            <em>Late Night with Seth Meyers</em> "Corrections" Comment Analysis
        </h3>
    </div>
    """,
    unsafe_allow_html=True
)

# --------------------------------------
# Sidebar — data controls
# --------------------------------------
with st.sidebar:
    st.header("Data Controls")

    if st.button("🔄 Refresh data (uses YouTube quota)"):
        with st.spinner("Fetching new comments from YouTube…"):
            generate_comment_analysis()
        st.cache_data.clear()
        st.success("Data refreshed. Reload the page.")

# --------------------------------------
# Load data (NO API CALLS HERE)
# --------------------------------------
@st.cache_data(ttl=86400)  # 24 hours
def load_cached_comments():
    path = "data/processed/corrections_comments.csv"

    if not os.path.exists(path):
        st.error(
            "Data file not found.\n\n"
            "Please click **Refresh data** in the sidebar to initialize the dataset."
        )
        st.stop()

    return load_comments(path)

df = load_cached_comments()

# --------------------------------------
# Last updated timestamp
# --------------------------------------
last_updated = datetime.fromtimestamp(
    os.path.getmtime("data/processed/corrections_comments.csv")
)

st.caption(
    f"📅 Data last updated: **{last_updated.strftime('%Y-%m-%d %H:%M')}**"
)

# --------------------------------------
# Date parsing
# --------------------------------------
df["date"] = pd.to_datetime(df["publishedAt"], errors="coerce")
if df["date"].dt.tz is not None:
    df["date"] = df["date"].dt.tz_localize(None)

# --------------------------------------
# Date range selector
# --------------------------------------
min_date = df["date"].min().date()
max_date = df["date"].max().date()

st.subheader("Select Date Range")

start_date, end_date = st.slider(
    "Date range",
    min_value=min_date,
    max_value=max_date,
    value=(min_date, max_date),
    format="YYYY-MM-DD"
)

start_ts = pd.Timestamp(start_date)
end_ts = pd.Timestamp(end_date)

df_filtered = df[
    (df["date"].dt.date >= start_date) &
    (df["date"].dt.date <= end_date)
].copy()

# --------------------------------------
# Topic clustering (cheap, local)
# --------------------------------------
n_clusters = 6
df_filtered, _, _ = cluster_comments(df_filtered, n_clusters=n_clusters)

cluster_labels = {
    0: "Animal Flubs",
    1: "Pronunciation Corrections",
    2: "Watching Corrections",
    3: "Jackals References",
    4: "Segments & Emmy's Discussion",
    5: "General Seth Comments / Reactions"
}

df_filtered["topic_label"] = df_filtered["cluster"].map(cluster_labels)

# --------------------------------------
# Aggregation selector
# --------------------------------------
st.subheader("Aggregation Frequency")

freq_option = st.selectbox(
    "Frequency",
    ["Daily", "Weekly", "Monthly"]
)

if freq_option == "Weekly":
    week_end_day = st.selectbox(
        "Week ends on",
        ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"]
    )
    freq = f"W-{week_end_day}"

elif freq_option == "Monthly":
    freq = None  # handled manually

else:
    freq = "D"

# --------------------------------------
# Aggregation logic
# --------------------------------------
if freq_option == "Monthly":
    df_filtered["date"] = df_filtered["date"].dt.tz_localize(None)
    start_ts = start_ts.tz_localize(None)

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
        [
            pd.Grouper(key=group_col, freq=freq) if freq else group_col,
            "topic_label"
        ]
    )
    .size()
    .reset_index(name="comment_count")
)

if freq_option == "Monthly":
    topic_trends = topic_trends.rename(columns={"month_start": "date"})

# --------------------------------------
# Plot (original behavior preserved)
# --------------------------------------
seth_palette = [
    "#1f4fd8",  # NBC blue
    "#e63946",
    "#457b9d",
    "#2a9d8f",
    "#f4a261",
    "#6d597a"
]

fig = px.line(
    topic_trends,
    x="date",
    y="comment_count",
    color="topic_label",
    title=f"Comment Topics Over Time ({freq_option})",
    markers=True,
    color_discrete_sequence=seth_palette,
    labels={
        "date": "Date",
        "comment_count": "Comment Count",
        "topic_label": "Topic"
    }
)

# WGA strike annotation
strike_start = pd.Timestamp("2023-05-02")
strike_end = pd.Timestamp("2023-09-27")

if start_date <= strike_end.date() and end_date >= strike_start.date():
    fig.add_vrect(
        x0=strike_start,
        x1=strike_end,
        fillcolor="gray",
        opacity=0.2,
        layer="below",
        line_width=0,
        annotation_text="WGA Strike (2023)",
        annotation_position="top left"
    )

fig.update_layout(
    template="plotly_white",
    hovermode="x unified",
    legend_title_text="Topics",
    width=1400
)

fig.update_xaxes(
    tickangle=-45,
    showline=True,
    mirror=True,
    linecolor="black"
)

fig.update_yaxes(
    showline=True,
    mirror=True,
    linecolor="black"
)

st.plotly_chart(fig, use_container_width=True)

