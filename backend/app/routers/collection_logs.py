from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.models import DataCollectionLog
from app.scheduler import run_facility_import, run_financial_import, log_collection

router = APIRouter(prefix="/api/collection-logs", tags=["collection"])


@router.get("/")
def list_logs(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    script_name: Optional[str] = None,
    status: Optional[str] = None
):
    """Get data collection execution logs"""
    query = db.query(DataCollectionLog)

    if script_name:
        query = query.filter(DataCollectionLog.script_name == script_name)
    if status:
        query = query.filter(DataCollectionLog.status == status)

    results = query.order_by(
        DataCollectionLog.started_at.desc()
    ).offset(skip).limit(limit).all()

    return {
        "total": db.query(DataCollectionLog).count(),
        "data": [
            {
                "id": log.id,
                "script_name": log.script_name,
                "status": log.status,
                "records_processed": log.records_processed,
                "error_message": log.error_message,
                "started_at": log.started_at,
                "completed_at": log.completed_at,
                "created_at": log.created_at
            }
            for log in results
        ]
    }


@router.get("/{log_id}")
def get_log(log_id: int, db: Session = Depends(get_db)):
    """Get a specific log entry"""
    log = db.query(DataCollectionLog).filter(DataCollectionLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")

    return {
        "id": log.id,
        "script_name": log.script_name,
        "status": log.status,
        "records_processed": log.records_processed,
        "error_message": log.error_message,
        "started_at": log.started_at,
        "completed_at": log.completed_at,
        "created_at": log.created_at
    }


@router.post("/trigger/{script_name}")
def trigger_collection(script_name: str, db: Session = Depends(get_db)):
    """Manually trigger a data collection script"""
    if script_name == "facility":
        try:
            log_collection("import_facility_csv", "running")
            run_facility_import()
            return {
                "status": "triggered",
                "script": script_name,
                "message": "Facility import triggered"
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    elif script_name == "financial":
        try:
            log_collection("import_corporation_csv", "running")
            run_financial_import()
            return {
                "status": "triggered",
                "script": script_name,
                "message": "Financial import triggered"
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    else:
        raise HTTPException(status_code=400, detail="Unknown script name")


@router.get("/stats/summary")
def get_stats_summary(db: Session = Depends(get_db)):
    """Get summary statistics of data collection"""
    total_runs = db.query(DataCollectionLog).count()
    success_runs = db.query(DataCollectionLog).filter(
        DataCollectionLog.status == "success"
    ).count()
    failed_runs = db.query(DataCollectionLog).filter(
        DataCollectionLog.status == "failed"
    ).count()

    total_records = db.query(func.sum(DataCollectionLog.records_processed)).scalar() or 0

    latest_log = db.query(DataCollectionLog).order_by(
        DataCollectionLog.started_at.desc()
    ).first()

    return {
        "total_runs": total_runs,
        "success_runs": success_runs,
        "failed_runs": failed_runs,
        "success_rate": round(success_runs / total_runs * 100, 2) if total_runs > 0 else 0,
        "total_records_processed": total_records,
        "latest_run": {
            "script": latest_log.script_name,
            "status": latest_log.status,
            "started_at": latest_log.started_at
        } if latest_log else None
    }


# Import for func
from sqlalchemy import func
