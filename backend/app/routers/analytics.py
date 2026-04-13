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
    """Get regional summary statistics (optimized single query)"""
    # Single GROUP BY query instead of N+1
    base_query = db.query(
        Corporation.prefecture,
        func.count(func.distinct(Corporation.corporation_id)).label("corp_count"),
        func.count(func.distinct(Facility.facility_id)).label("facility_count"),
        func.coalesce(func.sum(Facility.capacity), 0).label("total_capacity")
    ).outerjoin(
        Facility,
        Corporation.corporation_id == Facility.corporation_id
    ).filter(
        Corporation.prefecture.isnot(None)
    ).group_by(
        Corporation.prefecture
    )

    results = []
    for pref, corp_count, facility_count, total_capacity in base_query.all():
        avg_capacity = total_capacity / facility_count if facility_count > 0 else 0

        # Revenue (separate query if year specified)
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


@router.get("/service-type-stats")
def get_service_type_stats(
    fiscal_year: Optional[int] = Query(None),
    prefecture: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get statistics by service type"""
    query = db.query(
        Facility.service_type,
        func.count(Facility.facility_id).label("facility_count"),
        func.coalesce(func.sum(Facility.capacity), 0).label("total_capacity"),
        func.count(func.distinct(Facility.corporation_id)).label("corporation_count")
    ).filter(
        Facility.service_type.isnot(None)
    )

    if prefecture:
        query = query.filter(Facility.prefecture == prefecture)

    results = query.group_by(Facility.service_type).all()

    data = [
        {
            "service_type": service_type,
            "facility_count": facility_count,
            "total_capacity": int(total_capacity),
            "corporation_count": corporation_count
        }
        for service_type, facility_count, total_capacity, corporation_count in results
    ]

    return {
        "fiscal_year": fiscal_year,
        "prefecture": prefecture,
        "timestamp": datetime.utcnow(),
        "data": data
    }


@router.get("/year-compare")
def get_year_compare(
    corporation_id: Optional[str] = Query(None),
    prefecture: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get year-over-year comparison"""
    if corporation_id:
        # Corp level comparison
        results = db.query(
            CorporationFinancial.fiscal_year,
            CorporationFinancial.revenue,
            CorporationFinancial.ordinary_profit,
            CorporationFinancial.net_assets
        ).filter(
            CorporationFinancial.corporation_id == corporation_id
        ).order_by(
            CorporationFinancial.fiscal_year.desc()
        ).limit(5).all()

        data = []
        prev_revenue = None
        for year, revenue, profit, assets in results:
            growth = None
            if prev_revenue and revenue:
                growth = round((revenue - prev_revenue) / prev_revenue * 100, 2)
            data.append({
                "fiscal_year": year,
                "revenue": revenue,
                "profit": profit,
                "assets": assets,
                "revenue_growth_pct": growth
            })
            prev_revenue = revenue

        return {
            "type": "corporation",
            "id": corporation_id,
            "timestamp": datetime.utcnow(),
            "data": data
        }

    elif prefecture:
        # Regional comparison
        results = db.query(
            CorporationFinancial.fiscal_year,
            func.sum(CorporationFinancial.revenue).label("total_revenue"),
            func.count(func.distinct(CorporationFinancial.corporation_id)).label("corp_count")
        ).join(
            Corporation,
            Corporation.corporation_id == CorporationFinancial.corporation_id
        ).filter(
            Corporation.prefecture == prefecture
        ).group_by(
            CorporationFinancial.fiscal_year
        ).order_by(
            CorporationFinancial.fiscal_year.desc()
        ).limit(5).all()

        data = []
        prev_revenue = None
        for year, revenue, corp_count in results:
            growth = None
            if prev_revenue and revenue:
                growth = round((revenue - prev_revenue) / prev_revenue * 100, 2)
            data.append({
                "fiscal_year": year,
                "total_revenue": revenue,
                "corp_count": corp_count,
                "revenue_growth_pct": growth
            })
            prev_revenue = revenue

        return {
            "type": "prefecture",
            "prefecture": prefecture,
            "timestamp": datetime.utcnow(),
            "data": data
        }

    return {"error": "Specify either corporation_id or prefecture"}


@router.get("/top-prefectures")
def get_top_prefectures(
    fiscal_year: int = Query(...),
    metric: str = Query("revenue", regex="^(revenue|facility_count|total_capacity)$"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Get top prefectures by metric"""
    if metric == "revenue":
        results = db.query(
            Corporation.prefecture,
            func.sum(CorporationFinancial.revenue).label("value")
        ).join(
            CorporationFinancial,
            Corporation.corporation_id == CorporationFinancial.corporation_id
        ).filter(
            CorporationFinancial.fiscal_year == fiscal_year,
            Corporation.prefecture.isnot(None)
        ).group_by(
            Corporation.prefecture
        ).order_by(
            func.sum(CorporationFinancial.revenue).desc()
        ).limit(limit).all()
    else:
        results = db.query(
            Facility.prefecture,
            func.count(Facility.facility_id).label("value") if metric == "facility_count"
            else func.coalesce(func.sum(Facility.capacity), 0).label("value")
        ).filter(
            Facility.prefecture.isnot(None)
        ).group_by(
            Facility.prefecture
        ).order_by(
            func.count(Facility.facility_id).desc() if metric == "facility_count"
            else func.sum(Facility.capacity).desc()
        ).limit(limit).all()

    data = [
        {"rank": idx + 1, "prefecture": pref, "value": int(value)}
        for idx, (pref, value) in enumerate(results)
    ]

    return {
        "fiscal_year": fiscal_year,
        "metric": metric,
        "timestamp": datetime.utcnow(),
        "data": data
    }
