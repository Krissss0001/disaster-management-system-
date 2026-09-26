"""Unit tests for Phase 7: Per-disaster status summary and inventory balance."""
import pytest
from database.init_db import init_db, seed_sample_data
from logic.disasters import get_all_disasters
from logic.resources import get_all_resources
from logic.needs import get_all_needs
from logic.allocations import execute_allocation, get_all_allocations


@pytest.fixture(autouse=True)
def setup_database():
    init_db(drop_all=True)
    seed_sample_data(reset=True)


def test_per_disaster_summary():
    disasters = get_all_disasters()
    d_id = disasters[0]["id"]

    resources = get_all_resources(disaster_id=d_id)
    needs = get_all_needs(disaster_id=d_id)

    assert len(resources) == 3
    assert len(needs) == 2

    # Check balance calculation
    med_res = sum(r["available"] for r in resources if r["type"] == "Medical Supplies")
    med_need = sum(n["quantity_needed"] for n in needs if n["type"] == "Medical Supplies")
    assert med_res == 100
    assert med_need == 40
    assert med_res - med_need == 60  # Surplus


def test_allocation_reflection_in_status():
    disasters = get_all_disasters()
    d_id = disasters[0]["id"]
    needs = get_all_needs(disaster_id=d_id)
    resources = get_all_resources(disaster_id=d_id)

    target_need = next(n for n in needs if n["type"] == "Medical Supplies")
    target_res = next(r for r in resources if r["type"] == "Medical Supplies")

    # Allocate 40
    execute_allocation(target_need["id"], target_res["id"], 40)

    # Check updated status
    allocs = get_all_allocations(disaster_id=d_id)
    assert len(allocs) == 1
    assert allocs[0]["quantity_allocated"] == 40

    updated_resources = get_all_resources(disaster_id=d_id)
    med_res = next(r for r in updated_resources if r["type"] == "Medical Supplies")
    assert med_res["available"] == 60
