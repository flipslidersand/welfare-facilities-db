from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import Corporation, CorporationFinancial, Facility
from app.schemas import CorporationCreate, CorporationUpdate
from typing import Optional, List


def get_corporation(db: Session, corporation_id: str) -> Optional[Corporation]:
    """Get a single corporation by ID"""
    return db.query(Corporation).filter(Corporation.corporation_id == corporation_id).first()


def get_corporations(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    prefecture: Optional[str] = None,
    corporation_type: Optional[str] = None
) -> List[Corporation]:
    """Get corporations with optional filters"""
    query = db.query(Corporation)

    if prefecture:
        query = query.filter(Corporation.prefecture == prefecture)
    if corporation_type:
        query = query.filter(Corporation.type == corporation_type)

    return query.offset(skip).limit(limit).all()


def create_corporation(db: Session, corporation: CorporationCreate) -> Corporation:
    """Create a new corporation"""
    db_corporation = Corporation(**corporation.model_dump())
    db.add(db_corporation)
    db.commit()
    db.refresh(db_corporation)
    return db_corporation


def update_corporation(
    db: Session,
    corporation_id: str,
    corporation_update: CorporationUpdate
) -> Optional[Corporation]:
    """Update a corporation"""
    db_corporation = get_corporation(db, corporation_id)
    if db_corporation:
        update_data = corporation_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_corporation, key, value)
        db.commit()
        db.refresh(db_corporation)
    return db_corporation


def get_corporation_financials(
    db: Session,
    corporation_id: str,
    years: Optional[List[int]] = None
) -> List[CorporationFinancial]:
    """Get financial records for a corporation"""
    query = db.query(CorporationFinancial).filter(
        CorporationFinancial.corporation_id == corporation_id
    )
    if years:
        query = query.filter(CorporationFinancial.fiscal_year.in_(years))

    return query.order_by(CorporationFinancial.fiscal_year).all()


def get_corporation_facilities(db: Session, corporation_id: str) -> List[Facility]:
    """Get all facilities under a corporation"""
    return db.query(Facility).filter(
        Facility.corporation_id == corporation_id
    ).all()


def get_corporation_rankings(
    db: Session,
    fiscal_year: int,
    limit: int = 20
) -> List[dict]:
    """Get top corporations by revenue for a given year"""
    query = db.query(
        Corporation.corporation_id,
        Corporation.name,
        Corporation.prefecture,
        CorporationFinancial.revenue
    ).join(
        CorporationFinancial,
        Corporation.corporation_id == CorporationFinancial.corporation_id
    ).filter(
        CorporationFinancial.fiscal_year == fiscal_year
    ).order_by(
        CorporationFinancial.revenue.desc()
    ).limit(limit).all()

    results = []
    for rank, (corp_id, name, pref, revenue) in enumerate(query, 1):
        facility_count = db.query(Facility).filter(
            Facility.corporation_id == corp_id
        ).count()
        total_capacity = db.query(Facility).filter(
            Facility.corporation_id == corp_id
        ).with_entities(func.sum(Facility.capacity)).scalar() or 0

        results.append({
            "rank": rank,
            "corporation_id": corp_id,
            "name": name,
            "prefecture": pref,
            "revenue": revenue,
            "facility_count": facility_count,
            "total_capacity": total_capacity
        })

    return results
