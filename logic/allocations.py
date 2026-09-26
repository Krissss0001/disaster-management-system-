from typing import Tuple, Optional, Dict, Any, List, Union
from sqlalchemy import func
from database.connection import get_db
from database.models import Allocation, Resource, ResourceNeed, Disaster


def validate_allocation(
    need_type: str,
    resource_type: str,
    available_quantity: int,
    quantity_to_allocate: int,
    remaining_needed: Optional[int] = None
) -> Tuple[bool, Optional[str]]:
    """
    Pure validation function for allocating emergency resources to a need.
    Can be unit-tested directly without Streamlit UI code or database dependency.

    Rules enforced:
    1. Quantity to allocate must be strictly greater than 0.
    2. Need type and resource type must match exactly.
    3. Quantity to allocate must not exceed current resource available quantity.
    4. Quantity to allocate must not exceed remaining needed quantity (if provided).
    """
    # Rule: Reject zero or negative quantity
    if quantity_to_allocate is None or quantity_to_allocate <= 0:
        return False, "Allocation quantity must be greater than zero."

    # Rule: Resource and Need types must match
    if not need_type or not resource_type:
        return False, "Both need type and resource type must be specified."
        
    if need_type.strip().lower() != resource_type.strip().lower():
        return False, (
            f"Type mismatch: Cannot allocate '{resource_type.strip()}' "
            f"to a need of type '{need_type.strip()}'."
        )

    # Rule: Never allocate more than available resource quantity
    if quantity_to_allocate > available_quantity:
        return False, (
            f"Over-allocation error: Requested {quantity_to_allocate} units, "
            f"but only {available_quantity} units are currently available."
        )

    # Rule: Check against remaining needed quantity if specified
    if remaining_needed is not None and remaining_needed > 0:
        if quantity_to_allocate > remaining_needed:
            return False, (
                f"Over-allocation error: Requested {quantity_to_allocate} units, "
                f"which exceeds the remaining requirement of {remaining_needed} units."
            )

    return True, None


def get_remaining_need(db_session, need_id: str) -> int:
    """Calculate the remaining unsatisfied units for a specific need."""
    need = db_session.query(ResourceNeed).filter(ResourceNeed.id == need_id).first()
    if not need:
        return 0
    total_allocated = db_session.query(
        func.coalesce(func.sum(Allocation.quantity_allocated), 0)
    ).filter(Allocation.need_id == need_id).scalar()
    return max(0, need.quantity_needed - int(total_allocated))


def execute_allocation(
    need_id: str,
    resource_id: str,
    quantity_to_allocate: int
) -> Dict[str, Any]:
    """
    Execute resource allocation with strict validation and transaction management.
    Decrements resource available, creates Allocation record, and updates need status.
    """
    with get_db() as db:
        need = db.query(ResourceNeed).filter(ResourceNeed.id == need_id).with_for_update().first()
        if not need:
            raise ValueError(f"Resource need with ID '{need_id}' not found.")

        resource = db.query(Resource).filter(Resource.id == resource_id).with_for_update().first()
        if not resource:
            raise ValueError(f"Resource with ID '{resource_id}' not found.")

        # Calculate remaining need
        total_prev_allocated = db.query(
            func.coalesce(func.sum(Allocation.quantity_allocated), 0)
        ).filter(Allocation.need_id == need_id).scalar()
        remaining_needed = max(0, need.quantity_needed - int(total_prev_allocated))

        if remaining_needed <= 0:
            raise ValueError("This need has already been 100% fulfilled.")

        # Pure validation check
        is_valid, error_msg = validate_allocation(
            need_type=need.type,
            resource_type=resource.type,
            available_quantity=resource.available,
            quantity_to_allocate=quantity_to_allocate,
            remaining_needed=remaining_needed
        )
        if not is_valid:
            raise ValueError(error_msg)

        # 1. Decrement resource available
        resource.available -= quantity_to_allocate

        # 2. Create allocation record
        allocation = Allocation(
            need_id=need.id,
            resource_id=resource.id,
            quantity_allocated=quantity_to_allocate
        )
        db.add(allocation)
        db.flush()

        # 3. Update need status
        new_total_allocated = int(total_prev_allocated) + quantity_to_allocate
        if new_total_allocated >= need.quantity_needed:
            need.status = "fulfilled"
        else:
            need.status = "partial"

        db.commit()

        return {
            "allocation_id": allocation.id,
            "need_id": need.id,
            "resource_id": resource.id,
            "quantity_allocated": quantity_to_allocate,
            "remaining_resource_available": resource.available,
            "need_status": need.status,
            "remaining_need": max(0, need.quantity_needed - new_total_allocated),
            "created_at": allocation.created_at
        }


def get_all_allocations(disaster_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Fetch allocation history with associated need, resource, and disaster details."""
    with get_db() as db:
        query = db.query(
            Allocation,
            ResourceNeed.type.label("need_type"),
            ResourceNeed.quantity_needed.label("quantity_needed"),
            ResourceNeed.urgency.label("urgency"),
            Resource.type.label("resource_type"),
            Resource.provider.label("provider"),
            Disaster.name.label("disaster_name")
        ).join(
            ResourceNeed, Allocation.need_id == ResourceNeed.id
        ).join(
            Resource, Allocation.resource_id == Resource.id
        ).join(
            Disaster, ResourceNeed.disaster_id == Disaster.id
        )

        if disaster_id and disaster_id.lower() != "all":
            query = query.filter(ResourceNeed.disaster_id == disaster_id)

        results = query.order_by(Allocation.created_at.desc()).all()
        return [
            {
                "id": a.id,
                "disaster_name": disaster_name,
                "need_id": a.need_id,
                "need_type": need_type,
                "quantity_needed": quantity_needed,
                "urgency": urgency,
                "resource_id": a.resource_id,
                "resource_type": resource_type,
                "provider": provider,
                "quantity_allocated": a.quantity_allocated,
                "created_at": a.created_at
            }
            for a, need_type, quantity_needed, urgency, resource_type, provider, disaster_name in results
        ]
