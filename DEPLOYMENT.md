# Deployment Guide

## Overview

This application has been optimized for lightweight deployment on cloud platforms (AWS, Heroku, Streamlit Cloud, etc.) by **pre-computing all machine learning operations** during data collection, rather than at runtime.

## Architecture

### Data Collection Phase (Run Locally)
Heavy ML dependencies are used ONLY during data collection:
- `sentence-transformers` (~500MB with PyTorch)
- YouTube API calls
- Embedding generation
- Clustering computation

**Output**: CSV file with pre-computed cluster assignments

### Runtime Phase (Deployed to Cloud)
Lightweight dependencies for fast startup and low resource usage:
- `streamlit`, `pandas`, `plotly` (visualization only)
- **No ML libraries loaded**
- **No model downloads**
- Just reads CSV and generates interactive plots

## Setup Instructions

### 1. Local Data Collection (One-time or periodic updates)

Install the full dependencies:
```bash
pip install -r requirements-data-collection.txt
```

Set up your environment variables (create a `.env` file):
```
YOUTUBE_API_KEY=your_api_key_here
YOUTUBE_CHANNEL_ID=your_channel_id_here
```

Run the data collection script:
```bash
python comment_analysis.py
```

This will:
- Fetch YouTube comments
- Clean and preprocess them
- Generate sentence embeddings using `all-MiniLM-L6-v2` model
- Cluster comments into 6 topics
- Save results to `data/processed/corrections_comments.csv`

### 2. Deploy to Cloud

**Only install runtime requirements:**
```bash
pip install -r requirements.txt
```

**Deploy files:**
- `app.py` (main Streamlit app)
- `requirements.txt` (lightweight runtime dependencies)
- `data/processed/corrections_comments.csv` (pre-computed data)

**Platform-specific notes:**

#### Streamlit Cloud
- Upload the CSV file in your repository
- Use `requirements.txt` (NOT requirements-data-collection.txt)
- Set secrets in Streamlit Cloud dashboard if needed

#### Heroku
```bash
git push heroku main
```
Procfile (if needed):
```
web: streamlit run app.py --server.port=$PORT
```

#### AWS (EC2, Elastic Beanstalk, etc.)
- Use lightweight instance types (t2.micro, t3.small)
- Only `requirements.txt` dependencies needed
- App should start in seconds, not minutes

## Resource Comparison

### Before Optimization (Real-time clustering)
- **Startup time**: 2-5 minutes (downloading model)
- **Memory**: 1-2 GB (PyTorch + model in memory)
- **CPU**: Heavy during clustering
- **Disk**: 1+ GB
- **Result**: Timeouts on basic instances ❌

### After Optimization (Pre-computed clusters)
- **Startup time**: 5-15 seconds
- **Memory**: 100-300 MB
- **CPU**: Minimal (just pandas/plotly)
- **Disk**: <100 MB
- **Result**: Works on basic instances ✅

## Updating Data

To refresh the data with new YouTube comments:

1. Run locally:
   ```bash
   pip install -r requirements-data-collection.txt
   python comment_analysis.py
   ```

2. Commit the updated CSV:
   ```bash
   git add data/processed/corrections_comments.csv
   git commit -m "Update comment data"
   git push
   ```

3. Cloud deployment auto-updates (or redeploy manually)

## Optional: Offline Analysis

The `visualize_topics.py` module is available for deeper offline analysis but is NOT used by the deployed app.

To use it:
```bash
pip install -r requirements-data-collection.txt
python visualize_topics.py
```

## Troubleshooting

### App still slow on deployment
- Verify you're using `requirements.txt` (not requirements-data-collection.txt)
- Check that `data/processed/corrections_comments.csv` exists and contains a `cluster` column
- Ensure no imports of `sentence_transformers` in `app.py`

### Missing cluster column error
- Re-run `comment_analysis.py` locally to regenerate the CSV with cluster assignments
- Ensure you're using the updated version that saves clusters

### First-time setup triggers data collection on cloud
- The app will call `generate_comment_analysis()` if CSV is missing
- **Best practice**: Always upload pre-computed CSV to avoid this
- If triggered, it will fail due to missing heavy dependencies (as intended)
