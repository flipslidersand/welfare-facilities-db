from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.schemas import Corporation, CorporationCreate, CorporationDetail
from app.crud import corporation_crud

router = APIRouter(prefix="/api/corporations", tags=["corporations"])


@router.get("/", response_model=List[Corporation])
def list_corporations(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    prefecture: Optional[str] = None,
    corporation_type: Optional[str] = None
):
    """Get list of corporations"""
    return corporation_crud.get_corporations(
        db,
        skip=skip,
        limit=limit,
        prefecture=prefecture,
        corporation_type=corporation_type
    )


@router.get("/{corporation_id}", response_model=CorporationDetail)
def get_corporation(corporation_id: str, db: Session = Depends(get_db)):
    """Get corporation details including financials and facilities"""
    corporation = corporation_crud.get_corporation(db, corporation_id)
    if not corporation:
        raise HTTPException(status_code=404, detail="Corporation not found")
    return corporation


@router.get("/{corporation_id}/financials")
def get_corporation_financials(
    corporation_id: str,
    db: Session = Depends(get_db),
    years: Optional[str] = Query(None)
):
    """Get financial records for a corporation"""
    corporation = corporation_crud.get_corporation(db, corporation_id)
    if not corporation:
        raise HTTPException(status_code=404, detail="Corporation not found")

    # Parse years parameter if provided
    year_list = None
    if years:
        try:
            year_list = [int(y.strip()) for y in years.split(',')]
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid years parameter")

    financials = corporation_crud.get_corporation_financials(
        db,
        corporation_id,
        years=year_list
    )
    return {"corporation_id": corporation_id, "financials": financials}


@router.get("/{corporation_id}/facilities")
def get_corporation_facilities(
    corporation_id: str,
    db: Session = Depends(get_db)
):
    """Get all facilities under a corporation"""
    corporation = corporation_crud.get_corporation(db, corporation_id)
    if not corporation:
        raise HTTPException(status_code=404, detail="Corporation not found")

    facilities = corporation_crud.get_corporation_facilities(db, corporation_id)
    return {"corporation_id": corporation_id, "facility_count": len(facilities), "facilities": facilities}
