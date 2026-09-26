"""Unit tests for Phase 1: Database models, relationships, and seeding."""
import pytest
from database.connection import get_db
from database.models import Disaster, Resource, ResourceNeed, Allocation
from database.init_db import init_db, seed_sample_data


def test_database_initialization_and_seeding():
    init_db(drop_all=True)
    disaster = seed_sample_data(reset=True)
    assert disaster is not None

    with get_db() as db:
        disasters = db.query(Disaster).all()
        assert len(disasters) == 1
        d = disasters[0]
        assert d.name == "Cascade Ridge Wildfire"
        assert d.severity == 4
        assert d.status == "ongoing"
        assert len(d.id) == 36  # UUID length

        # Check resources seeded
        resources = db.query(Resource).filter_by(disaster_id=d.id).all()
        assert len(resources) == 3
        res_types = {r.type for r in resources}
        assert "Medical Supplies" in res_types
        assert "Food & Water" in res_types
        assert "Rescue Team" in res_types

        # Check needs seeded
        needs = db.query(ResourceNeed).filter_by(disaster_id=d.id).all()
        assert len(needs) == 2
        need_types = {n.type for n in needs}
        assert "Medical Supplies" in need_types
        assert "Food & Water" in need_types

        # Check cascade relationship access
        assert len(d.resources) == 3
        assert len(d.needs) == 2
