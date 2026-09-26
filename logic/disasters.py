from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from database.connection import get_db
from database.models import Disaster, Resource, ResourceNeed


def get_all_disasters(status_filter: Optional[str] = None, type_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve all disasters with optional filtering by status and type."""
    with get_db() as db:
        query = db.query(Disaster)
        if status_filter and status_filter.lower() != "all":
            query = query.filter(Disaster.status == status_filter.lower())
        if type_filter and type_filter.lower() != "all":
            query = query.filter(Disaster.type == type_filter)
        
        disasters = query.order_by(Disaster.severity.desc(), Disaster.created_at.desc()).all()
        return [
            {
                "id": d.id,
                "name": d.name,
                "type": d.type,
                "severity": d.severity,
                "status": d.status,
                "latitude": d.latitude,
                "longitude": d.longitude,
                "description": d.description,
                "created_at": d.created_at,
                "resource_count": len(d.resources),
                "needs_count": len(d.needs)
            }
            for d in disasters
        ]


def get_disaster_by_id(disaster_id: str) -> Optional[Dict[str, Any]]:
    """Fetch details of a single disaster by its UUID."""
    with get_db() as db:
        d = db.query(Disaster).filter(Disaster.id == disaster_id).first()
        if not d:
            return None
        return {
            "id": d.id,
            "name": d.name,
            "type": d.type,
            "severity": d.severity,
            "status": d.status,
            "latitude": d.latitude,
            "longitude": d.longitude,
            "description": d.description,
            "created_at": d.created_at
        }


def create_disaster(
    name: str,
    disaster_type: str,
    severity: int,
    latitude: float,
    longitude: float,
    description: Optional[str] = None,
    status: str = "ongoing"
) -> Dict[str, Any]:
    """Create a new disaster record with validation."""
    if not name or not name.strip():
        raise ValueError("Disaster name is required.")
    if severity < 1 or severity > 5:
        raise ValueError("Severity must be an integer between 1 and 5.")
    if not (-90.0 <= latitude <= 90.0):
        raise ValueError("Latitude must be between -90 and 90.")
    if not (-180.0 <= longitude <= 180.0):
        raise ValueError("Longitude must be between -180 and 180.")
    
    valid_statuses = {"ongoing", "contained", "resolved"}
    if status.lower() not in valid_statuses:
        raise ValueError(f"Invalid status '{status}'. Must be one of {valid_statuses}.")

    with get_db() as db:
        disaster = Disaster(
            name=name.strip(),
            type=disaster_type.strip(),
            severity=int(severity),
            status=status.lower(),
            latitude=float(latitude),
            longitude=float(longitude),
            description=description.strip() if description else None
        )
        db.add(disaster)
        db.commit()
        return {
            "id": disaster.id,
            "name": disaster.name,
            "type": disaster.type,
            "severity": disaster.severity,
            "status": disaster.status,
            "latitude": disaster.latitude,
            "longitude": disaster.longitude,
            "description": disaster.description,
            "created_at": disaster.created_at
        }


def update_disaster_status(disaster_id: str, new_status: str) -> bool:
    """Update status of a disaster."""
    valid_statuses = {"ongoing", "contained", "resolved"}
    if new_status.lower() not in valid_statuses:
        raise ValueError(f"Invalid status '{new_status}'. Must be one of {valid_statuses}.")

    with get_db() as db:
        disaster = db.query(Disaster).filter(Disaster.id == disaster_id).first()
        if not disaster:
            return False
        disaster.status = new_status.lower()
        db.commit()
        return True


def get_active_disasters_count() -> int:
    """Count disasters that are active (ongoing or contained)."""
    with get_db() as db:
        return db.query(Disaster).filter(Disaster.status.in_(["ongoing", "contained"])).count()
