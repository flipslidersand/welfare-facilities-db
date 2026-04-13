from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from datetime import datetime

from app.database import get_db
from app.models import Corporation, CorporationFinancial, Facility
from app.crud import corporation_crud

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/ranking")
def get_ranking(
    fiscal_year: int = Query(..., description="Fiscal year to get rankings for"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get top corporations by revenue for a given fiscal year"""
    query = db.query(
        Corporation.corporation_id,
        Corporation.name,
        Corporation.prefecture,
        CorporationFinancial.revenue
    ).join(
        CorporationFinancial,
        Corporation.corporation_id == CorporationFinancial.corporation_id
    ).filter(
        CorporationFinancial.fiscal_year == fiscal_year,
        CorporationFinancial.revenue.isnot(None)
    ).order_by(
        CorporationFinancial.revenue.desc()
    ).limit(limit).all()

    results = []
    for rank, (corp_id, name, pref, revenue) in enumerate(query, 1):
        # Get facility stats for this corporation
        facility_count = db.query(Facility).filter(
            Facility.corporation_id == corp_id
        ).count()

        total_capacity = db.query(func.sum(Facility.capacity)).filter(
            Facility.corporation_id == corp_id
        ).scalar() or 0

        results.append({
            "rank": rank,
            "corporation_id": corp_id,
            "name": name,
            "prefecture": pref,
            "revenue": revenue,
            "facility_count": facility_count,
            "total_capacity": int(total_capacity)
        })

    return {
        "fiscal_year": fiscal_year,
        "timestamp": datetime.utcnow(),
        "data": results
    }


@router.get("/regional")
def get_regional_summary(
    fiscal_year: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """Get regional summary statistics"""
    # Get unique prefectures
    prefectures = db.query(Corporation.prefecture.distinct()).filter(
        Corporation.prefecture.isnot(None)
    ).all()

    results = []

    for (pref,) in prefectures:
        # Corporation count
        corp_count = db.query(Corporation).filter(
            Corporation.prefecture == pref
        ).count()

        # Facility stats
        facility_count = db.query(Facility).filter(
            Facility.prefecture == pref
        ).count()

        total_capacity = db.query(func.sum(Facility.capacity)).filter(
            Facility.prefecture == pref
        ).scalar() or 0

        avg_capacity = total_capacity / facility_count if facility_count > 0 else 0

        # Revenue
        total_revenue = None
        if fiscal_year:
            total_revenue = db.query(func.sum(CorporationFinancial.revenue)).filter(
                CorporationFinancial.fiscal_year == fiscal_year
            ).join(
                Corporation,
                Corporation.corporation_id == CorporationFinancial.corporation_id
            ).filter(
                Corporation.prefecture == pref
            ).scalar()

        results.append({
            "prefecture": pref,
            "corporation_count": corp_count,
            "facility_count": facility_count,
            "total_capacity": int(total_capacity),
            "avg_facility_capacity": round(avg_capacity, 2),
            "total_revenue": total_revenue
        })

    return {
        "fiscal_year": fiscal_year,
        "timestamp": datetime.utcnow(),
        "data": results
    }


@router.get("/summary")
def get_overall_summary(
    db: Session = Depends(get_db)
):
    """Get overall system summary"""
    corporation_count = db.query(Corporation).count()
    facility_count = db.query(Facility).count()
    total_capacity = db.query(func.sum(Facility.capacity)).scalar() or 0

    # Get fiscal years available
    fiscal_years = db.query(CorporationFinancial.fiscal_year.distinct()).order_by(
        CorporationFinancial.fiscal_year.desc()
    ).limit(5).all()

    years = [year[0] for year in fiscal_years]

    return {
        "timestamp": datetime.utcnow(),
        "corporation_count": corporation_count,
        "facility_count": facility_count,
        "total_capacity": int(total_capacity),
        "available_fiscal_years": years
    }
