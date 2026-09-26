from typing import List, Optional, Dict, Any
from sqlalchemy import func
from database.connection import get_db
from database.models import Resource, Disaster


def get_all_resources(
    disaster_id: Optional[str] = None,
    resource_type: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Get all resources with optional filtering by disaster or resource type."""
    with get_db() as db:
        query = db.query(Resource, Disaster.name.label("disaster_name")).join(
            Disaster, Resource.disaster_id == Disaster.id
        )
        if disaster_id and disaster_id.lower() != "all":
            query = query.filter(Resource.disaster_id == disaster_id)
        if resource_type and resource_type.lower() != "all":
            query = query.filter(Resource.type == resource_type)

        results = query.order_by(Resource.created_at.desc()).all()
        return [
            {
                "id": r.id,
                "disaster_id": r.disaster_id,
                "disaster_name": disaster_name,
                "type": r.type,
                "quantity": r.quantity,
                "available": r.available,
                "allocated": r.quantity - r.available,
                "latitude": r.latitude,
                "longitude": r.longitude,
                "provider": r.provider,
                "created_at": r.created_at
            }
            for r, disaster_name in results
        ]


def register_resource(
    disaster_id: str,
    resource_type: str,
    quantity: int,
    latitude: float,
    longitude: float,
    provider: str
) -> Dict[str, Any]:
    """Register a new resource linked to a disaster."""
    if not disaster_id:
        raise ValueError("Disaster selection is required.")
    if not resource_type or not resource_type.strip():
        raise ValueError("Resource type is required.")
    if quantity <= 0:
        raise ValueError("Resource quantity must be greater than 0.")
    if not provider or not provider.strip():
        raise ValueError("Provider name is required.")
    if not (-90.0 <= latitude <= 90.0):
        raise ValueError("Latitude must be between -90 and 90.")
    if not (-180.0 <= longitude <= 180.0):
        raise ValueError("Longitude must be between -180 and 180.")

    with get_db() as db:
        # Check disaster exists
        disaster = db.query(Disaster).filter(Disaster.id == disaster_id).first()
        if not disaster:
            raise ValueError(f"Disaster with ID '{disaster_id}' does not exist.")

        resource = Resource(
            disaster_id=disaster_id,
            type=resource_type.strip(),
            quantity=int(quantity),
            available=int(quantity),
            latitude=float(latitude),
            longitude=float(longitude),
            provider=provider.strip()
        )
        db.add(resource)
        db.commit()
        return {
            "id": resource.id,
            "disaster_id": resource.disaster_id,
            "type": resource.type,
            "quantity": resource.quantity,
            "available": resource.available,
            "latitude": resource.latitude,
            "longitude": resource.longitude,
            "provider": resource.provider,
            "created_at": resource.created_at
        }


def get_resource_metrics() -> Dict[str, int]:
    """Calculate aggregated metrics for resources."""
    with get_db() as db:
        total_qty = db.query(func.coalesce(func.sum(Resource.quantity), 0)).scalar()
        total_avail = db.query(func.coalesce(func.sum(Resource.available), 0)).scalar()
        total_types = db.query(Resource.type).distinct().count()
        return {
            "total_resources": int(total_qty),
            "available_resources": int(total_avail),
            "allocated_resources": int(total_qty - total_avail),
            "resource_types_count": int(total_types)
        }
