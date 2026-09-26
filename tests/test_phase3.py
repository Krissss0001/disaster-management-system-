"""Unit tests for Phase 3: Manage Disasters logic, validation, and status transitions."""
import pytest
from database.init_db import init_db, seed_sample_data
from logic.disasters import create_disaster, update_disaster_status, get_disaster_by_id
from logic.alerts import dispatch_emergency_alert, get_recent_alerts


@pytest.fixture(autouse=True)
def setup_database():
    init_db(drop_all=True)
    seed_sample_data(reset=True)


def test_create_disaster_valid():
    d = create_disaster(
        name="Santa Barbara Flood",
        disaster_type="Flood",
        severity=3,
        latitude=34.4208,
        longitude=-119.6982,
        description="Flash flooding near canyon roads."
    )
    assert d["id"] is not None
    assert d["name"] == "Santa Barbara Flood"
    assert d["severity"] == 3
    assert d["status"] == "ongoing"


def test_create_disaster_validation_errors():
    # Empty name
    with pytest.raises(ValueError, match="name is required"):
        create_disaster("", "Wildfire", 3, 34.0, -118.0)

    # Invalid severity
    with pytest.raises(ValueError, match="Severity must be an integer between 1 and 5"):
        create_disaster("Test", "Wildfire", 6, 34.0, -118.0)

    # Invalid latitude
    with pytest.raises(ValueError, match="Latitude must be between -90 and 90"):
        create_disaster("Test", "Wildfire", 3, 95.0, -118.0)


def test_update_disaster_status():
    d = create_disaster("Bay Earthquake", "Earthquake", 4, 37.7, -122.4)
    disaster_id = d["id"]

    # Update to contained
    success = update_disaster_status(disaster_id, "contained")
    assert success is True
    updated = get_disaster_by_id(disaster_id)
    assert updated["status"] == "contained"

    # Update to resolved
    success = update_disaster_status(disaster_id, "resolved")
    assert success is True
    updated = get_disaster_by_id(disaster_id)
    assert updated["status"] == "resolved"

    # Invalid status
    with pytest.raises(ValueError, match="Invalid status"):
        update_disaster_status(disaster_id, "unknown_status")


def test_emergency_alert_dispatch():
    alert = dispatch_emergency_alert(
        event_type="HIGH_SEVERITY_DISASTER",
        title="Test Catastrophic Wildfire",
        urgency_or_severity=5,
        details="Immediate mass evacuation ordered.",
        location_str="37.7749, -122.4194"
    )
    assert alert["status"] in ["simulated_call_dispatched", "live_sms_dispatched"]
    alerts = get_recent_alerts(limit=5)
    assert len(alerts) >= 1
    assert alerts[0]["urgency_or_severity"] == 5
