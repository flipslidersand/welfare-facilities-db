"""Background scheduler for data collection tasks"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import asyncio
import subprocess
import sys
import os
import httpx
from app.database import SessionLocal
from app.models import DataCollectionLog

scheduler = BackgroundScheduler()


def notify_slack(message: str):
    """Send notification to Slack webhook"""
    slack_webhook = os.getenv("SLACK_WEBHOOK_URL", "")
    if not slack_webhook:
        return

    try:
        httpx.post(
            slack_webhook,
            json={"text": message},
            timeout=5
        )
    except Exception as e:
        print(f"⚠️  Slack notification failed: {e}")


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
    script_name = "import_facility_csv"
    csv_path = os.getenv("FACILITY_CSV_PATH", "")

    # Log start
    log_collection(script_name, "running")

    # Validate CSV path
    if not csv_path or not os.path.exists(csv_path):
        error_msg = f"FACILITY_CSV_PATH not set or file not found: {csv_path}"
        log_collection(script_name, "skipped", error_msg=error_msg)
        print(f"⏭️  {error_msg}")
        return

    # Execute with retry logic
    max_retries = 2
    for attempt in range(max_retries):
        try:
            result = subprocess.run(
                [sys.executable, "scripts/import_facility_csv.py", csv_path, "介護"],
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode == 0:
                # Extract record count from output
                records = 0
                for line in result.stdout.split('\n'):
                    if "Imported" in line:
                        try:
                            records = int(line.split()[1])
                        except:
                            pass

                log_collection(script_name, "success", records=records)
                notify_slack(f"✅ Facility import succeeded: {records} records processed")
                print(f"✓ Facility import completed: {records} records")
                return
            else:
                raise Exception(f"Script failed: {result.stderr}")

        except Exception as e:
            error_msg = str(e)
            if attempt < max_retries - 1:
                print(f"⚠️  Facility import attempt {attempt + 1} failed, retrying: {error_msg}")
                continue
            else:
                log_collection(script_name, "failed", error_msg=error_msg)
                notify_slack(f"❌ Facility import failed after {max_retries} retries:\n{error_msg}")
                print(f"❌ Facility import failed: {error_msg}")
                return


def run_financial_import():
    """Annual financial data import (April 1 at 2:00)"""
    script_name = "import_corporation_csv"
    csv_path = os.getenv("FINANCIAL_CSV_PATH", "")

    # Log start
    log_collection(script_name, "running")

    # Validate CSV path
    if not csv_path or not os.path.exists(csv_path):
        error_msg = f"FINANCIAL_CSV_PATH not set or file not found: {csv_path}"
        log_collection(script_name, "skipped", error_msg=error_msg)
        print(f"⏭️  {error_msg}")
        return

    # Execute with retry logic
    max_retries = 2
    for attempt in range(max_retries):
        try:
            result = subprocess.run(
                [sys.executable, "scripts/import_corporation_csv.py", csv_path],
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode == 0:
                # Extract record count from output
                records = 0
                for line in result.stdout.split('\n'):
                    if "Imported" in line or "processed" in line:
                        try:
                            records = int(line.split()[1])
                        except:
                            pass

                log_collection(script_name, "success", records=records)
                notify_slack(f"✅ Financial import succeeded: {records} records processed")
                print(f"✓ Financial import completed: {records} records")
                return
            else:
                raise Exception(f"Script failed: {result.stderr}")

        except Exception as e:
            error_msg = str(e)
            if attempt < max_retries - 1:
                print(f"⚠️  Financial import attempt {attempt + 1} failed, retrying: {error_msg}")
                continue
            else:
                log_collection(script_name, "failed", error_msg=error_msg)
                notify_slack(f"❌ Financial import failed after {max_retries} retries:\n{error_msg}")
                print(f"❌ Financial import failed: {error_msg}")
                return


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
