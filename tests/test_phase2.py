"""Unit tests for Phase 2: Dashboard metrics, queries, and filters."""
import pytest
from database.init_db import init_db, seed_sample_data
from logic.disasters import get_all_disasters, get_active_disasters_count
from logic.resources import get_all_resources, get_resource_metrics
from logic.needs import get_all_needs, get_need_metrics


@pytest.fixture(autouse=True)
def setup_database():
    init_db(drop_all=True)
    seed_sample_data(reset=True)


def test_dashboard_disaster_queries():
    active_count = get_active_disasters_count()
    assert active_count == 1

    all_disasters = get_all_disasters()
    assert len(all_disasters) == 1
    d = all_disasters[0]
    assert d["name"] == "Cascade Ridge Wildfire"
    assert d["status"] == "ongoing"
    assert d["resource_count"] == 3
    assert d["needs_count"] == 2

    # Filter by status
    filtered = get_all_disasters(status_filter="ongoing")
    assert len(filtered) == 1
    resolved = get_all_disasters(status_filter="resolved")
    assert len(resolved) == 0


def test_dashboard_resource_metrics():
    metrics = get_resource_metrics()
    assert metrics["total_resources"] == 620  # 100 + 500 + 20
    assert metrics["available_resources"] == 620
    assert metrics["allocated_resources"] == 0
    assert metrics["resource_types_count"] == 3

    resources = get_all_resources()
    assert len(resources) == 3


def test_dashboard_need_metrics():
    metrics = get_need_metrics()
    assert metrics["pending_needs"] == 2
    assert metrics["partial_needs"] == 0
    assert metrics["fulfilled_needs"] == 0
    assert metrics["total_open_needs"] == 2
    assert metrics["total_needed_qty"] == 240  # 40 + 200

    needs = get_all_needs()
    assert len(needs) == 2
