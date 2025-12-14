import os
from dotenv import load_dotenv
import pandas as pd
import re
import streamlit as st
from googleapiclient.discovery import build
from tqdm import tqdm
from sklearn.cluster import KMeans
from sentence_transformers import SentenceTransformer



# Load environment
load_dotenv()
API_KEY = os.getenv("YOUTUBE_API_KEY")
CHANNEL_ID = os.getenv("YOUTUBE_CHANNEL_ID")
#API_KEY = st.secrets["YOUTUBE_API_KEY"]
#CHANNEL_ID = st.secrets["YOUTUBE_CHANNEL_ID"]

if not API_KEY or not CHANNEL_ID:
    raise ValueError("Missing API key or channel ID.")

youtube = build("youtube", "v3", developerKey=API_KEY)

# Clean and preprocess comments
def clean_comment(text):
    if pd.isna(text):
        return ""
    text = text.lower()
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"[^a-z\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

# Get the ID of the "uploads" playlist for the Late Night YouTube channel.
def get_upload_playlist_id(channel_id: str) -> str:
    res = youtube.channels().list(
        part="contentDetails",
        id=channel_id
    ).execute()
    return res["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

# Retrieve videos whose titles contain "corrections".
def get_corrections_videos(playlist_id: str, max_videos=200) -> pd.DataFrame:
    videos = []
    next_page_token = None
    while len(videos) < max_videos:
        res = youtube.playlistItems().list(
            part="snippet",
            playlistId=playlist_id,
            maxResults=50,
            pageToken=next_page_token
        ).execute()
        
        for item in res["items"]:
            title = item["snippet"]["title"]
            video_id = item["snippet"]["resourceId"]["videoId"]
            if "corrections" in title.lower():
                videos.append({
                    "video_id": video_id,
                    "title": title,
                    "publishedAt": item["snippet"]["publishedAt"]
                })
        next_page_token = res.get("nextPageToken")
        if not next_page_token:
            break

    return pd.DataFrame(videos)

# Retrieve top-level comments for a video
def get_video_comments(video_id: str, max_comments=500) -> pd.DataFrame:
    comments = []
    next_page_token = None
    while len(comments) < max_comments:
        res = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=100,
            textFormat="plainText",
            pageToken=next_page_token
        ).execute()
        
        for item in res.get("items", []):
            snippet = item["snippet"]["topLevelComment"]["snippet"]
            comments.append({
                "video_id": video_id,
                "comment": snippet["textDisplay"],
                "like_count": snippet["likeCount"],
                "publishedAt": snippet["publishedAt"],
                "reply_count": item["snippet"]["totalReplyCount"]
            })
        next_page_token = res.get("nextPageToken")
        if not next_page_token:
            break
    return pd.DataFrame(comments)

# Cluster comments using sentence embeddings and KMeans
def cluster_comments(comments: pd.Series, n_clusters=5):
    print(f"Generating sentence embeddings for {len(comments)} comments...")
    model = SentenceTransformer("all-MiniLM-L6-v2")
    embeddings = model.encode(comments.tolist(), show_progress_bar=True)

    print(f"Clustering into {n_clusters} topics...")
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(embeddings)
    return labels


# Main pipeline
def generate_comment_analysis():
    print("Collecting 'Corrections' videos...")
    upload_playlist = get_upload_playlist_id(CHANNEL_ID)
    video_df = get_corrections_videos(upload_playlist)

    if video_df.empty:
        print("No 'Corrections' videos found.")
        return

    print(f"Found {len(video_df)} videos.")

    # Fetch comments
    all_comments = []
    for idx, row in tqdm(video_df.iterrows(), total=len(video_df), desc="Fetching comments"):
        video_comments = get_video_comments(row["video_id"])
        all_comments.append(video_comments)
    comments_df = pd.concat(all_comments, ignore_index=True)
    print(f"Fetched {len(comments_df)} comments.")

    # Clean comments
    print("Cleaning comments...")
    comments_df["clean_comment"] = comments_df["comment"].astype(str).apply(clean_comment)
    comments_df = comments_df[comments_df["clean_comment"].str.len() > 5]
    print(f"Retained {len(comments_df)} comments after cleaning.")

    # Cluster comments into topics using sentence embeddings
    comments_df["cluster"] = cluster_comments(comments_df["clean_comment"], n_clusters=6)
    print("Clustered comments into 6 topics.")

    # Save to CSV with cluster assignments
    os.makedirs("data/processed", exist_ok=True)
    out_path = "data/processed/corrections_comments.csv"
    comments_df.to_csv(out_path, index=False)
    print(f"Saved processed comments with cluster assignments to {out_path}")

if __name__ == "__main__":
    generate_comment_analysis()
