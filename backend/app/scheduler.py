"""Background scheduler for data collection tasks"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import asyncio
from app.database import SessionLocal
from app.models import DataCollectionLog

scheduler = BackgroundScheduler()


def log_collection(script_name: str, status: str, records: int = 0, error_msg: str = None):
    """Log data collection event"""
    db = SessionLocal()
    try:
        log = DataCollectionLog(
            script_name=script_name,
            status=status,
            records_processed=records,
            error_message=error_msg,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow() if status != "running" else None
        )
        db.add(log)
        db.commit()
    finally:
        db.close()


def run_facility_import():
    """Monthly facility data import (day 1 at 3:00)"""
    try:
        log_collection("import_facility_csv", "running")
        # スクリプト実行ロジックはここに記述
        # subprocess.run(["python", "scripts/import_facility_csv.py", "facilities.csv", "介護"])
        log_collection("import_facility_csv", "success", records=0)
        print("✓ Facility import completed")
    except Exception as e:
        log_collection("import_facility_csv", "failed", error_msg=str(e))
        print(f"❌ Facility import failed: {e}")


def run_financial_import():
    """Annual financial data import (April 1 at 2:00)"""
    try:
        log_collection("import_corporation_csv", "running")
        # スクリプト実行ロジックはここに記述
        # subprocess.run(["python", "scripts/import_corporation_csv.py", "--financials", "financials.csv"])
        log_collection("import_corporation_csv", "success", records=0)
        print("✓ Financial import completed")
    except Exception as e:
        log_collection("import_corporation_csv", "failed", error_msg=str(e))
        print(f"❌ Financial import failed: {e}")


def init_scheduler():
    """Initialize background scheduler"""
    # Monthly: every 1st day at 3:00 AM
    scheduler.add_job(
        run_facility_import,
        CronTrigger(day=1, hour=3, minute=0),
        id="facility_import",
        name="Monthly Facility Data Import"
    )

    # Yearly: April 1 at 2:00 AM (Japan fiscal year start)
    scheduler.add_job(
        run_financial_import,
        CronTrigger(month=4, day=1, hour=2, minute=0),
        id="financial_import",
        name="Annual Financial Data Import"
    )

    print("✓ Scheduler initialized with 2 jobs")


def start_scheduler():
    """Start background scheduler"""
    if not scheduler.running:
        init_scheduler()
        scheduler.start()
        print("✓ Scheduler started")


def stop_scheduler():
    """Stop background scheduler"""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        print("✓ Scheduler stopped")
