"""Unit tests for Phase 5: Resource needs posting, validation, and urgency sorting."""
import pytest
from database.init_db import init_db, seed_sample_data
from logic.disasters import get_all_disasters
from logic.needs import post_resource_need, get_all_needs, get_need_metrics


@pytest.fixture(autouse=True)
def setup_database():
    init_db(drop_all=True)
    seed_sample_data(reset=True)


def test_post_resource_need_valid():
    disasters = get_all_disasters()
    disaster_id = disasters[0]["id"]

    need = post_resource_need(
        disaster_id=disaster_id,
        need_type="Rescue Team",
        quantity_needed=15,
        latitude=37.77,
        longitude=-122.41,
        urgency=5
    )
    assert need["id"] is not None
    assert need["type"] == "Rescue Team"
    assert need["quantity_needed"] == 15
    assert need["urgency"] == 5
    assert need["status"] == "pending"


def test_post_resource_need_validation():
    disasters = get_all_disasters()
    disaster_id = disasters[0]["id"]

    # Zero / negative quantity
    with pytest.raises(ValueError, match="Quantity needed must be greater than 0"):
        post_resource_need(disaster_id, "Rescue Team", 0, 37.7, -122.4, 4)

    # Invalid urgency
    with pytest.raises(ValueError, match="Urgency must be an integer between 1 and 5"):
        post_resource_need(disaster_id, "Rescue Team", 10, 37.7, -122.4, 6)

    # Non-existent disaster
    with pytest.raises(ValueError, match="does not exist"):
        post_resource_need("bad-id", "Rescue Team", 10, 37.7, -122.4, 3)


def test_filter_needs():
    disasters = get_all_disasters()
    disaster_id = disasters[0]["id"]

    all_needs = get_all_needs(disaster_id=disaster_id)
    assert len(all_needs) == 2

    # Filter by urgency
    high_urgency = get_all_needs(urgency_filter=5)
    assert len(high_urgency) == 1
    assert high_urgency[0]["urgency"] == 5
