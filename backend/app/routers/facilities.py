from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.schemas import Facility, FacilityCreate
from app.crud import facility_crud

router = APIRouter(prefix="/api/facilities", tags=["facilities"])


@router.get("/", response_model=List[Facility])
def list_facilities(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    prefecture: Optional[str] = None,
    service_type: Optional[str] = None,
    corporation_id: Optional[str] = None
):
    """Get list of facilities"""
    return facility_crud.get_facilities(
        db,
        skip=skip,
        limit=limit,
        prefecture=prefecture,
        service_type=service_type,
        corporation_id=corporation_id
    )


@router.get("/{facility_id}", response_model=Facility)
def get_facility(facility_id: str, db: Session = Depends(get_db)):
    """Get facility details"""
    facility = facility_crud.get_facility(db, facility_id)
    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found")
    return facility


@router.get("/prefecture/{prefecture}/summary")
def get_prefecture_summary(
    prefecture: str,
    db: Session = Depends(get_db)
):
    """Get summary statistics for a prefecture"""
    facilities = facility_crud.get_facilities_by_prefecture(db, prefecture)
    service_counts = facility_crud.get_facility_count_by_service(db, prefecture)

    total_capacity = sum(f.capacity for f in facilities if f.capacity)
    avg_capacity = total_capacity / len(facilities) if facilities else 0

    return {
        "prefecture": prefecture,
        "facility_count": len(facilities),
        "total_capacity": total_capacity,
        "avg_capacity": round(avg_capacity, 2),
        "service_breakdown": service_counts
    }
