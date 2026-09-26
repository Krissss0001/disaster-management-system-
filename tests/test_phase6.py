"""Unit tests for Phase 6: Core allocation validation and execution business rules."""
import pytest
from database.init_db import init_db, seed_sample_data
from logic.allocations import validate_allocation, execute_allocation, get_all_allocations
from logic.needs import get_all_needs
from logic.resources import get_all_resources


@pytest.fixture(autouse=True)
def setup_database():
    init_db(drop_all=True)
    seed_sample_data(reset=True)


# ==============================================================================
# 1. PURE FUNCTION TESTS: validate_allocation()
# ==============================================================================

def test_validate_allocation_success():
    is_valid, err = validate_allocation(
        need_type="Medical Supplies",
        resource_type="Medical Supplies",
        available_quantity=100,
        quantity_to_allocate=40,
        remaining_needed=40
    )
    assert is_valid is True
    assert err is None


def test_validate_allocation_type_mismatch():
    is_valid, err = validate_allocation(
        need_type="Medical Supplies",
        resource_type="Food & Water",
        available_quantity=100,
        quantity_to_allocate=10
    )
    assert is_valid is False
    assert "Type mismatch" in err


def test_validate_allocation_zero_or_negative_quantity():
    # Zero quantity
    is_valid, err = validate_allocation(
        need_type="Rescue Team",
        resource_type="Rescue Team",
        available_quantity=20,
        quantity_to_allocate=0
    )
    assert is_valid is False
    assert "greater than zero" in err

    # Negative quantity
    is_valid, err = validate_allocation(
        need_type="Rescue Team",
        resource_type="Rescue Team",
        available_quantity=20,
        quantity_to_allocate=-5
    )
    assert is_valid is False
    assert "greater than zero" in err


def test_validate_allocation_over_allocation_resource():
    # Quantity exceeds available resource
    is_valid, err = validate_allocation(
        need_type="Medical Supplies",
        resource_type="Medical Supplies",
        available_quantity=30,
        quantity_to_allocate=35
    )
    assert is_valid is False
    assert "Over-allocation" in err


def test_validate_allocation_over_allocation_need():
    # Quantity exceeds remaining need
    is_valid, err = validate_allocation(
        need_type="Medical Supplies",
        resource_type="Medical Supplies",
        available_quantity=100,
        quantity_to_allocate=50,
        remaining_needed=40
    )
    assert is_valid is False
    assert "exceeds the remaining requirement" in err


# ==============================================================================
# 2. EXECUTION TESTS: execute_allocation()
# ==============================================================================

def test_execute_partial_allocation():
    # In seeded data: Medical Supplies need = 40, resource = 100
    needs = get_all_needs()
    med_need = next(n for n in needs if n["type"] == "Medical Supplies")
    resources = get_all_resources()
    med_res = next(r for r in resources if r["type"] == "Medical Supplies")

    # Allocate 15 units (Partial)
    res = execute_allocation(
        need_id=med_need["id"],
        resource_id=med_res["id"],
        quantity_to_allocate=15
    )

    assert res["allocation_id"] is not None
    assert res["quantity_allocated"] == 15
    assert res["need_status"] == "partial"
    assert res["remaining_need"] == 25
    assert res["remaining_resource_available"] == 85


def test_execute_full_allocation_fulfillment():
    needs = get_all_needs()
    med_need = next(n for n in needs if n["type"] == "Medical Supplies")
    resources = get_all_resources()
    med_res = next(r for r in resources if r["type"] == "Medical Supplies")

    # Allocate all 40 units (Fulfilled)
    res = execute_allocation(
        need_id=med_need["id"],
        resource_id=med_res["id"],
        quantity_to_allocate=40
    )

    assert res["need_status"] == "fulfilled"
    assert res["remaining_need"] == 0
    assert res["remaining_resource_available"] == 60

    allocations = get_all_allocations()
    assert len(allocations) >= 1
    assert allocations[0]["quantity_allocated"] == 40
