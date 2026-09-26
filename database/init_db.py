import sys
from pathlib import Path

# Add project root to sys.path so script can be run directly
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from database.connection import engine, Base, get_db
from database.models import Disaster, Resource, ResourceNeed, Allocation


def init_db(drop_all: bool = False):
    """Create all database tables."""
    if drop_all:
        Base.metadata.drop_all(bind=engine)
        print("Dropped all existing tables.")
    Base.metadata.create_all(bind=engine)
    print("Database tables initialized successfully.")


def seed_sample_data(reset: bool = False):
    """Seed 1 sample disaster with 3 resources and 2 needs."""
    with get_db() as db:
        if reset:
            db.query(Allocation).delete()
            db.query(ResourceNeed).delete()
            db.query(Resource).delete()
            db.query(Disaster).delete()
            db.commit()
            print("Cleared existing records.")

        # Check if any disaster exists
        existing_disaster = db.query(Disaster).first()
        if existing_disaster and not reset:
            print(f"Database already contains data (Disaster: '{existing_disaster.name}'). Use --reset to re-seed.")
            return existing_disaster

        sample_disaster = Disaster(
            name="Cascade Ridge Wildfire",
            type="Wildfire",
            severity=4,
            status="ongoing",
            latitude=37.7749,
            longitude=-122.4194,
            description="Rapidly spreading brush fire threatening suburban ridges. Evacuation zones active across Sector 4."
        )
        db.add(sample_disaster)
        db.flush()  # Populates sample_disaster.id

        # 3 Sample Resources for this disaster
        res1 = Resource(
            disaster_id=sample_disaster.id,
            type="Medical Supplies",
            quantity=100,
            available=100,
            latitude=37.7800,
            longitude=-122.4100,
            provider="Red Cross Pacific"
        )
        res2 = Resource(
            disaster_id=sample_disaster.id,
            type="Food & Water",
            quantity=500,
            available=500,
            latitude=37.7700,
            longitude=-122.4250,
            provider="World Central Kitchen"
        )
        res3 = Resource(
            disaster_id=sample_disaster.id,
            type="Rescue Team",
            quantity=20,
            available=20,
            latitude=37.7650,
            longitude=-122.4050,
            provider="Bay Area Search & Rescue"
        )
        db.add_all([res1, res2, res3])

        # 2 Sample Resource Needs for this disaster
        need1 = ResourceNeed(
            disaster_id=sample_disaster.id,
            type="Medical Supplies",
            quantity_needed=40,
            latitude=37.7780,
            longitude=-122.4150,
            urgency=5,
            status="pending"
        )
        need2 = ResourceNeed(
            disaster_id=sample_disaster.id,
            type="Food & Water",
            quantity_needed=200,
            latitude=37.7720,
            longitude=-122.4200,
            urgency=4,
            status="pending"
        )
        db.add_all([need1, need2])
        db.commit()

        print(f"Successfully seeded sample disaster: '{sample_disaster.name}' (ID: {sample_disaster.id})")
        print("  - 3 Resources seeded: Medical Supplies (100), Food & Water (500), Rescue Team (20)")
        print("  - 2 Needs seeded: Medical Supplies (40, Urgency 5), Food & Water (200, Urgency 4)")
        return sample_disaster


if __name__ == "__main__":
    reset_flag = "--reset" in sys.argv
    init_db(drop_all=reset_flag)
    seed_sample_data(reset=reset_flag)
