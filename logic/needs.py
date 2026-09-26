from typing import List, Optional, Dict, Any
from sqlalchemy import func
from database.connection import get_db
from database.models import ResourceNeed, Disaster


def get_all_needs(
    disaster_id: Optional[str] = None,
    status_filter: Optional[str] = None,
    urgency_filter: Optional[int] = None
) -> List[Dict[str, Any]]:
    """Retrieve all resource needs with filtering options."""
    with get_db() as db:
        query = db.query(ResourceNeed, Disaster.name.label("disaster_name")).join(
            Disaster, ResourceNeed.disaster_id == Disaster.id
        )

        if disaster_id and disaster_id.lower() != "all":
            query = query.filter(ResourceNeed.disaster_id == disaster_id)
        if status_filter and status_filter.lower() != "all":
            query = query.filter(ResourceNeed.status == status_filter.lower())
        if urgency_filter and str(urgency_filter).lower() != "all":
            query = query.filter(ResourceNeed.urgency == int(urgency_filter))

        results = query.order_by(ResourceNeed.urgency.desc(), ResourceNeed.created_at.desc()).all()
        return [
            {
                "id": n.id,
                "disaster_id": n.disaster_id,
                "disaster_name": disaster_name,
                "type": n.type,
                "quantity_needed": n.quantity_needed,
                "latitude": n.latitude,
                "longitude": n.longitude,
                "urgency": n.urgency,
                "status": n.status,
                "created_at": n.created_at
            }
            for n, disaster_name in results
        ]


def post_resource_need(
    disaster_id: str,
    need_type: str,
    quantity_needed: int,
    latitude: float,
    longitude: float,
    urgency: int
) -> Dict[str, Any]:
    """Record an emergency resource need for a disaster."""
    if not disaster_id:
        raise ValueError("Disaster selection is required.")
    if not need_type or not need_type.strip():
        raise ValueError("Resource type is required.")
    if quantity_needed <= 0:
        raise ValueError("Quantity needed must be greater than 0.")
    if urgency < 1 or urgency > 5:
        raise ValueError("Urgency must be an integer between 1 and 5.")
    if not (-90.0 <= latitude <= 90.0):
        raise ValueError("Latitude must be between -90 and 90.")
    if not (-180.0 <= longitude <= 180.0):
        raise ValueError("Longitude must be between -180 and 180.")

    with get_db() as db:
        disaster = db.query(Disaster).filter(Disaster.id == disaster_id).first()
        if not disaster:
            raise ValueError(f"Disaster with ID '{disaster_id}' does not exist.")

        need = ResourceNeed(
            disaster_id=disaster_id,
            type=need_type.strip(),
            quantity_needed=int(quantity_needed),
            latitude=float(latitude),
            longitude=float(longitude),
            urgency=int(urgency),
            status="pending"
        )
        db.add(need)
        db.commit()
        return {
            "id": need.id,
            "disaster_id": need.disaster_id,
            "type": need.type,
            "quantity_needed": need.quantity_needed,
            "latitude": need.latitude,
            "longitude": need.longitude,
            "urgency": need.urgency,
            "status": need.status,
            "created_at": need.created_at
        }


def get_need_metrics() -> Dict[str, int]:
    """Calculate aggregate metrics for resource needs."""
    with get_db() as db:
        pending_count = db.query(ResourceNeed).filter(ResourceNeed.status == "pending").count()
        partial_count = db.query(ResourceNeed).filter(ResourceNeed.status == "partial").count()
        fulfilled_count = db.query(ResourceNeed).filter(ResourceNeed.status == "fulfilled").count()
        total_needed_qty = db.query(func.coalesce(func.sum(ResourceNeed.quantity_needed), 0)).scalar()

        return {
            "pending_needs": pending_count,
            "partial_needs": partial_count,
            "fulfilled_needs": fulfilled_count,
            "total_open_needs": pending_count + partial_count,
            "total_needed_qty": int(total_needed_qty)
        }
