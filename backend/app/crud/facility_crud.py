from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import Facility
from app.schemas import FacilityCreate, FacilityUpdate
from typing import Optional, List


def get_facility(db: Session, facility_id: str) -> Optional[Facility]:
    """Get a single facility by ID"""
    return db.query(Facility).filter(Facility.facility_id == facility_id).first()


def get_facilities(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    prefecture: Optional[str] = None,
    service_type: Optional[str] = None,
    corporation_id: Optional[str] = None
) -> List[Facility]:
    """Get facilities with optional filters"""
    query = db.query(Facility)

    if prefecture:
        query = query.filter(Facility.prefecture == prefecture)
    if service_type:
        query = query.filter(Facility.service_type == service_type)
    if corporation_id:
        query = query.filter(Facility.corporation_id == corporation_id)

    return query.offset(skip).limit(limit).all()


def create_facility(db: Session, facility: FacilityCreate) -> Facility:
    """Create a new facility"""
    db_facility = Facility(**facility.model_dump())
    db.add(db_facility)
    db.commit()
    db.refresh(db_facility)
    return db_facility


def update_facility(
    db: Session,
    facility_id: str,
    facility_update: FacilityUpdate
) -> Optional[Facility]:
    """Update a facility"""
    db_facility = get_facility(db, facility_id)
    if db_facility:
        update_data = facility_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_facility, key, value)
        db.commit()
        db.refresh(db_facility)
    return db_facility


def get_facilities_by_prefecture(
    db: Session,
    prefecture: str
) -> List[Facility]:
    """Get all facilities in a prefecture"""
    return db.query(Facility).filter(Facility.prefecture == prefecture).all()


def get_facility_count_by_service(
    db: Session,
    prefecture: Optional[str] = None
) -> dict:
    """Get count of facilities by service type"""
    query = db.query(
        Facility.service_type,
        func.count(Facility.facility_id).label('count')
    )

    if prefecture:
        query = query.filter(Facility.prefecture == prefecture)

    results = query.group_by(Facility.service_type).all()
    return {service_type: count for service_type, count in results}
