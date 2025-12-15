import os
from dotenv import load_dotenv
import pandas as pd
from googleapiclient.discovery import build
from tqdm import tqdm
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import numpy as np
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

# Load environment
load_dotenv()
API_KEY = os.getenv("YOUTUBE_API_KEY")
CHANNEL_ID = os.getenv("YOUTUBE_CHANNEL_ID")

if not API_KEY or not CHANNEL_ID:
    raise ValueError("Missing API key or channel ID.")

youtube = build("youtube", "v3", developerKey=API_KEY)

RAW_CACHE_PATH = "data/raw/corrections_comments_raw.csv"
PROCESSED_PATH = "data/processed/corrections_comments.csv"

# YouTube helper functions
def get_upload_playlist_id(channel_id: str) -> str:
    res = youtube.channels().list(
        part="contentDetails",
        id=channel_id
    ).execute()
    return res["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]


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
            if "corrections" in title.lower():
                videos.append({
                    "video_id": item["snippet"]["resourceId"]["videoId"],
                    "title": title,
                    "publishedAt": item["snippet"]["publishedAt"]
                })

        next_page_token = res.get("nextPageToken")
        if not next_page_token:
            break

    return pd.DataFrame(videos)


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

# Clustering
def cluster_comments(comments: pd.Series, n_clusters=5):

    custom_stopwords = {"like", "just", "love", "don", "know", "did", "say", "seth", "corrections", "correction", "ve", "really", "best"}
    all_stopwords = list(ENGLISH_STOP_WORDS.union(custom_stopwords))
    
    vectorizer = TfidfVectorizer(stop_words=all_stopwords, max_df=0.9, min_df=10)
    X = vectorizer.fit_transform(comments)

    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    labels = kmeans.fit_predict(X)

    return labels, vectorizer, kmeans, X


def summarize_clusters(df, vectorizer, kmeans, X, n_terms=10, n_examples=5):
    feature_names = np.array(vectorizer.get_feature_names_out())
    print("\n=== CLUSTER SUMMARIES ===\n")

    for cluster_id in sorted(df["cluster"].unique()):
        print(f"\n--- Cluster {cluster_id} ---")
        center = kmeans.cluster_centers_[cluster_id]
        top_indices = center.argsort()[::-1][:n_terms]
        top_terms = feature_names[top_indices]
        print("Top terms:")
        print(", ".join(top_terms))

        examples = df[df["cluster"] == cluster_id]["comment"].head(n_examples)
        print("\nExample comments:")
        for c in examples:
            print(f"  - {c[:200]}")

# Main pipeline
def generate_comment_analysis():
    os.makedirs("data/raw", exist_ok=True)
    os.makedirs("data/processed", exist_ok=True)

    # ---- LOAD OR FETCH COMMENTS ----
    if os.path.exists(RAW_CACHE_PATH):
        print(f"Loaded cached comments from {RAW_CACHE_PATH}")
        comments_df = pd.read_csv(RAW_CACHE_PATH)
    else:
        print("Collecting 'Corrections' videos...")
        upload_playlist = get_upload_playlist_id(CHANNEL_ID)
        video_df = get_corrections_videos(upload_playlist)

        if video_df.empty:
            print("No 'Corrections' videos found.")
            return

        print(f"Found {len(video_df)} videos.")

        all_comments = []
        for _, row in tqdm(video_df.iterrows(), total=len(video_df), desc="Fetching comments"):
            video_comments = get_video_comments(row["video_id"])
            all_comments.append(video_comments)

        comments_df = pd.concat(all_comments, ignore_index=True)
        comments_df.to_csv(RAW_CACHE_PATH, index=False)
        print(f"Fetched {len(comments_df)} comments.")
        print(f"Saved raw comments to {RAW_CACHE_PATH}")

    # Clean
    comments_df = comments_df.dropna(subset=["comment"])
    comments_df = comments_df[comments_df["comment"].str.strip() != ""]

    # Cluster
    labels, vectorizer, kmeans, X = cluster_comments(
        comments_df["comment"],
        n_clusters=5
    )
    comments_df["cluster"] = labels
    print("Clustered comments into topics.")

    # Summarize
    summarize_clusters(comments_df, vectorizer, kmeans, X)

    # Save processed comments
    comments_df.to_csv(PROCESSED_PATH, index=False)
    print(f"\nSaved processed comments to {PROCESSED_PATH}")


if __name__ == "__main__":
    generate_comment_analysis()
