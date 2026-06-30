"""
Tests for the data-analysis layer and the Flask app.

These run in the Jenkins **Test stage** and use the bundled local dataset /
fixture, so they need NO AWS access — the pipeline stays fast and self-contained.
"""

import os
import sys

import pytest

# Make the app package importable (app/ is added to the path).
APP_DIR = os.path.join(os.path.dirname(__file__), "..", "app")
sys.path.insert(0, os.path.abspath(APP_DIR))

import data_analysis as da  # noqa: E402
from app import app as flask_app  # noqa: E402

FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "sample_users.user")
FULL_DATA = os.path.join(APP_DIR, "data", "u.user")


# ---- Fixture-based tests (deterministic, 8 known users) --------------------

def test_fixture_loads_eight_users():
    df = da.load_data(FIXTURE)
    assert da.total_users(df) == 8


def test_columns_parsed_correctly():
    df = da.load_data(FIXTURE)
    assert list(df.columns) == ["user_id", "age", "gender", "occupation", "zip_code"]
    # zip codes must stay strings (leading zeros preserved, e.g. 05201).
    assert df["zip_code"].dtype == object


def test_occupation_grouping():
    df = da.load_data(FIXTURE)
    occ = da.users_by_occupation(df)
    assert occ["technician"] == 2       # users 1 and 4
    assert occ["administrator"] == 2    # users 7 and 8


def test_age_distribution_buckets_sum_to_total():
    df = da.load_data(FIXTURE)
    dist = da.age_distribution(df)
    assert sum(dist["buckets"].values()) == da.total_users(df)
    assert dist["min"] == 23 and dist["max"] == 57


# ---- Full-dataset sanity tests (the real 943-user file) --------------------

def test_full_dataset_has_943_users():
    df = da.load_data(FULL_DATA)
    assert da.total_users(df) == 943


def test_full_dataset_occupation_count():
    df = da.load_data(FULL_DATA)
    # MovieLens 100k has 21 distinct occupations.
    assert len(da.users_by_occupation(df)) == 21


# ---- Flask route / API tests ----------------------------------------------

@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c


def test_health_endpoint(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ok"


def test_stats_api_shape(client):
    resp = client.get("/api/stats")
    assert resp.status_code == 200
    data = resp.get_json()
    for key in ("total_users", "age", "occupations", "gender", "source"):
        assert key in data


def test_dashboard_renders(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"User Analytics" in resp.data
