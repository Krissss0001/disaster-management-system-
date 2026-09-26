"""Convenience script to initialize and seed the disaster database."""
import sys
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from database.init_db import init_db, seed_sample_data

if __name__ == "__main__":
    reset = "--reset" in sys.argv
    print("Setting up Disaster Response Coordination Database...")
    init_db(drop_all=reset)
    seed_sample_data(reset=reset)
    print("Done! You can verify the database contents.")
