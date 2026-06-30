"""
data_analysis.py
----------------
Loads the MovieLens `u.user` dataset and performs the three required analyses:
  1. Total number of users
  2. Age distribution analysis
  3. User grouping based on occupation

Data source priority:
  * If the environment variable S3_BUCKET is set, the dataset is fetched from
    AWS S3 using boto3. On EC2 this uses the instance's IAM ROLE for auth, so
    NO access keys are ever stored in code or config  (secure-by-design).
  * Otherwise it falls back to a bundled local copy (app/data/u.user), which
    is what local development and the Jenkins test stage use.
"""

import io
import os
from functools import lru_cache

import pandas as pd

# Column names: the DAT8 copy of u.user ships WITH a header row, but we declare
# the schema explicitly so parsing is identical no matter the source.
COLUMNS = ["user_id", "age", "gender", "occupation", "zip_code"]

# Local fallback path (bundled with the app).
LOCAL_DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "u.user")

# AWS config, read from the environment so nothing is hard-coded.
S3_BUCKET = os.environ.get("S3_BUCKET")
S3_KEY = os.environ.get("S3_KEY", "u.user")
AWS_REGION = os.environ.get("AWS_REGION", "ap-south-1")


def _read_csv(buffer_or_path):
    """Parse the pipe-delimited dataset into a clean DataFrame."""
    df = pd.read_csv(
        buffer_or_path,
        sep="|",
        header=None,         # we supply the schema via names=
        names=COLUMNS,       # enforce our schema regardless of source
        skiprows=1,          # skip the dataset's own header line
        dtype={"zip_code": str},
    )
    df["age"] = pd.to_numeric(df["age"], errors="coerce")
    df = df.dropna(subset=["age"])
    df["age"] = df["age"].astype(int)
    return df


def load_data(path=None):
    """
    Return the dataset as a DataFrame.

    If `path` is given, read that file (used by tests).
    Else if S3_BUCKET is configured, read from S3 via the EC2 IAM role.
    Else read the bundled local file.
    """
    if path:
        return _read_csv(path)

    if S3_BUCKET:
        # Imported lazily so local dev / tests don't require boto3 or AWS.
        import boto3

        s3 = boto3.client("s3", region_name=AWS_REGION)
        obj = s3.get_object(Bucket=S3_BUCKET, Key=S3_KEY)
        body = obj["Body"].read().decode("utf-8")
        return _read_csv(io.StringIO(body))

    return _read_csv(LOCAL_DATA_PATH)


def data_source_label():
    """Human-readable description of where the data is coming from."""
    if S3_BUCKET:
        return f"AWS S3  (s3://{S3_BUCKET}/{S3_KEY})"
    return "Local file  (app/data/u.user)"


# ---- The three mandated analyses -------------------------------------------

def total_users(df):
    """1. Total number of users."""
    return int(len(df))


def age_distribution(df):
    """
    2. Age distribution analysis.
    Returns both summary statistics and counts bucketed into age groups.
    """
    bins = [0, 17, 25, 35, 45, 55, 200]
    labels = ["<18", "18-25", "26-35", "36-45", "46-55", "56+"]
    groups = pd.cut(df["age"], bins=bins, labels=labels, right=True)
    buckets = groups.value_counts().reindex(labels).fillna(0).astype(int)
    return {
        "min": int(df["age"].min()),
        "max": int(df["age"].max()),
        "mean": round(float(df["age"].mean()), 1),
        "median": int(df["age"].median()),
        "buckets": buckets.to_dict(),  # {"<18": n, "18-25": n, ...}
    }


def users_by_occupation(df):
    """3. User grouping based on occupation (sorted, most common first)."""
    counts = df.groupby("occupation").size().sort_values(ascending=False)
    return counts.astype(int).to_dict()


def gender_split(df):
    """Bonus: gender breakdown, used for an extra chart on the dashboard."""
    return df.groupby("gender").size().astype(int).to_dict()


def build_summary(path=None):
    """Single entry point: load data and return everything the UI/API needs."""
    df = load_data(path)
    return {
        "source": data_source_label(),
        "total_users": total_users(df),
        "age": age_distribution(df),
        "occupations": users_by_occupation(df),
        "gender": gender_split(df),
    }
