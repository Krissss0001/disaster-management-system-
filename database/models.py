import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database.connection import Base


def generate_uuid() -> str:
    """Generate a standard UUID4 hex string."""
    return str(uuid.uuid4())


def get_utc_now() -> datetime:
    """Return current UTC timestamp."""
    return datetime.now(timezone.utc)


class Disaster(Base):
    __tablename__ = "disasters"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(120), nullable=False)
    type = Column(String(50), nullable=False)  # e.g., Earthquake, Wildfire, Flood, Hurricane
    severity = Column(Integer, nullable=False)  # 1 to 5
    status = Column(String(20), nullable=False, default="ongoing")  # ongoing, contained, resolved
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=get_utc_now, nullable=False)

    # Relationships
    resources = relationship("Resource", back_populates="disaster", cascade="all, delete-orphan")
    needs = relationship("ResourceNeed", back_populates="disaster", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Disaster {self.name} ({self.type}, Severity: {self.severity}, Status: {self.status})>"


class Resource(Base):
    __tablename__ = "resources"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    disaster_id = Column(String(36), ForeignKey("disasters.id"), nullable=False)
    type = Column(String(50), nullable=False)  # e.g., Medical Supplies, Food & Water, Rescue Team
    quantity = Column(Integer, nullable=False)
    available = Column(Integer, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    provider = Column(String(100), nullable=False)  # e.g., Red Cross, Local Fire Dept, FEMA
    created_at = Column(DateTime, default=get_utc_now, nullable=False)

    # Relationships
    disaster = relationship("Disaster", back_populates="resources")
    allocations = relationship("Allocation", back_populates="resource", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Resource {self.type} - Available: {self.available}/{self.quantity} by {self.provider}>"


class ResourceNeed(Base):
    __tablename__ = "resource_needs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    disaster_id = Column(String(36), ForeignKey("disasters.id"), nullable=False)
    type = Column(String(50), nullable=False)  # e.g., Medical Supplies, Food & Water, Rescue Team
    quantity_needed = Column(Integer, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    urgency = Column(Integer, nullable=False)  # 1 to 5
    status = Column(String(20), nullable=False, default="pending")  # pending, partial, fulfilled
    created_at = Column(DateTime, default=get_utc_now, nullable=False)

    # Relationships
    disaster = relationship("Disaster", back_populates="needs")
    allocations = relationship("Allocation", back_populates="need", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ResourceNeed {self.type} - Needed: {self.quantity_needed}, Urgency: {self.urgency}, Status: {self.status}>"


class Allocation(Base):
    __tablename__ = "allocations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    need_id = Column(String(36), ForeignKey("resource_needs.id"), nullable=False)
    resource_id = Column(String(36), ForeignKey("resources.id"), nullable=False)
    quantity_allocated = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=get_utc_now, nullable=False)

    # Relationships
    need = relationship("ResourceNeed", back_populates="allocations")
    resource = relationship("Resource", back_populates="allocations")

    def __repr__(self):
        return f"<Allocation Need={self.need_id} -> Resource={self.resource_id} (Qty: {self.quantity_allocated})>"
