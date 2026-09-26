"""Unit tests for Phase 4: Resources registration and queries."""
import pytest
from database.init_db import init_db, seed_sample_data
from logic.disasters import get_all_disasters
from logic.resources import register_resource, get_all_resources, get_resource_metrics


@pytest.fixture(autouse=True)
def setup_database():
    init_db(drop_all=True)
    seed_sample_data(reset=True)


def test_register_resource_valid():
    disasters = get_all_disasters()
    disaster_id = disasters[0]["id"]

    res = register_resource(
        disaster_id=disaster_id,
        resource_type="Shelter Kits",
        quantity=30,
        latitude=37.77,
        longitude=-122.41,
        provider="Habitat for Humanity"
    )
    assert res["id"] is not None
    assert res["type"] == "Shelter Kits"
    assert res["quantity"] == 30
    assert res["available"] == 30
    assert res["provider"] == "Habitat for Humanity"


def test_register_resource_validation():
    disasters = get_all_disasters()
    disaster_id = disasters[0]["id"]

    # Zero or negative quantity
    with pytest.raises(ValueError, match="quantity must be greater than 0"):
        register_resource(disaster_id, "Shelter Kits", 0, 37.7, -122.4, "Red Cross")

    with pytest.raises(ValueError, match="quantity must be greater than 0"):
        register_resource(disaster_id, "Shelter Kits", -5, 37.7, -122.4, "Red Cross")

    # Empty provider
    with pytest.raises(ValueError, match="Provider name is required"):
        register_resource(disaster_id, "Shelter Kits", 10, 37.7, -122.4, "")

    # Non-existent disaster
    with pytest.raises(ValueError, match="does not exist"):
        register_resource("non-existent-id", "Shelter Kits", 10, 37.7, -122.4, "Red Cross")


def test_filter_resources():
    disasters = get_all_disasters()
    disaster_id = disasters[0]["id"]

    # Filter by disaster
    res_list = get_all_resources(disaster_id=disaster_id)
    assert len(res_list) >= 3

    # Filter by type
    medical_list = get_all_resources(resource_type="Medical Supplies")
    assert len(medical_list) >= 1
    assert all(r["type"] == "Medical Supplies" for r in medical_list)
