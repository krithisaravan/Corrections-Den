import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from dateutil.relativedelta import relativedelta

# Import clustering, cleaning, and visualization functions
from visualize_topics import load_comments, cluster_comments, get_top_keywords_per_cluster

# Streamlit page config
st.set_page_config(
    page_title="Late Night with Seth Meyers Corrections Comments Analysis",
    layout="wide"
)

st.markdown(
    "<h1 style='text-align: center; margin-bottom: 0.5em;'>"
    "<em>Late Night with Seth Meyers</em> 'Corrections' Comments Analysis"
    "</h1>",
    unsafe_allow_html=True
)

# Load data
path = "data/processed/corrections_comments.csv"
df = load_comments(path)

df["date"] = pd.to_datetime(df["publishedAt"], errors="coerce")
if df["date"].dt.tz is not None:
    df["date"] = df["date"].dt.tz_localize(None)

# Date filter
min_date = df["date"].min().date()
max_date = df["date"].max().date()

st.subheader("Select Date Range")
start_date, end_date = st.slider(
    "Date range:",
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

# Cluster comments
n_clusters = 6
df_filtered, kmeans, embeddings = cluster_comments(df_filtered, n_clusters=n_clusters)
cluster_keywords = get_top_keywords_per_cluster(df_filtered, n_clusters=n_clusters)

cluster_labels = {
    0: "Animal Flubs",
    1: "Pronunciation Corrections",
    2: "Watching Corrections",
    3: "Jackals References",
    4: "Segments & Emmy's Discussion",
    5: "General Seth Comments/Reactions"
}
df_filtered["topic_label"] = df_filtered["cluster"].map(cluster_labels)

# Frequency selector
st.subheader("Select Aggregation Frequency")
freq_option = st.selectbox(
    "Aggregation frequency:",
    options=["Daily", "Weekly", "Monthly"]
)

if freq_option == "Weekly":
    week_end_day = st.selectbox(
        "Week ends on:",
        options=["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"]
    )
    freq = f"W-{week_end_day}"
elif freq_option == "Monthly":
    freq = None
else:
    freq = "D"

# Aggregate by chosen frequency
if freq_option == "Monthly":
    # Align each monthly bin to the same day of month as the start date
    df_filtered = df_filtered.copy()
    df_filtered["date"] = df_filtered["date"].dt.tz_localize(None)
    start_ts = start_ts.tz_localize(None)

    # Build exact month boundaries based on calendar months
    month_starts = []
    current = start_ts
    while current <= end_ts:
        month_starts.append(current)
        current += relativedelta(months=1)
    month_starts.append(end_ts + timedelta(days=1))

    # Assign each comment to its bin start date
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
    df_filtered.groupby([pd.Grouper(key=group_col, freq=freq) if freq else group_col, "topic_label"])
    .size()
    .reset_index(name="comment_count")
)

if freq_option == "Monthly":
    topic_trends = topic_trends.rename(columns={"month_start": "date"})

topic_trends["hover_date"] = pd.to_datetime(topic_trends["date"]).dt.strftime("%Y-%m-%d")

# Plot chart
fig = px.line(
    topic_trends,
    x="date",
    y="comment_count",
    color="topic_label",
    title=f"Comment Topics Over Time ({freq_option})",
    markers=True,
    hover_data={
        "date": False,
        "hover_date": True,
        "comment_count": True,
        "topic_label": False
    }
)

# WGA strike annotation
strike_start = pd.Timestamp("2023-05-02")
strike_end = pd.Timestamp("2023-09-27")

if (end_date >= strike_start.date()) and (start_date <= strike_end.date()):
    fig.add_vrect(
        x0=strike_start,
        x1=strike_end,
        fillcolor="gray",
        opacity=0.25,
        layer="below",
        line_width=0,
        annotation_text="WGA Strike 2023",
        annotation_position="top left"
    )

# Layout & x-axis formatting
fig.update_layout(
    template="plotly_white",
    hovermode="x unified",
    legend_title_text="Topics",
    xaxis_title="Date",
    yaxis_title="Comment Count"
)

tickvals = pd.date_range(
    start=pd.Timestamp(start_date).replace(day=1),
    end=pd.Timestamp(end_date),
    freq="MS"
)

fig.update_xaxes(
    range=[pd.Timestamp(start_date), pd.Timestamp(end_date) + pd.Timedelta(days=1)],
    tickvals=tickvals,
    tickformat="%b %Y",
    tickangle=-45,
    ticklabelmode="period",
    showline=True,
    mirror=True,
    linecolor="black"
)

st.plotly_chart(fig, use_container_width=True)
