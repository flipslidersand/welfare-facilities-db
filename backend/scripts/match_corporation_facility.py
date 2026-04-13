#!/usr/bin/env python3
"""Match facilities to corporations when corporation_id is missing"""
import os
import sys
from datetime import datetime
from difflib import SequenceMatcher

sys.path.insert(0, os.path.dirname(__file__) + '/..')

from app.database import SessionLocal
from app.models import Facility, Corporation


def fuzzy_match(a: str, b: str, threshold: float = 0.8) -> bool:
    """Simple fuzzy string matching"""
    ratio = SequenceMatcher(None, a.lower(), b.lower()).ratio()
    return ratio >= threshold


def match_facilities_to_corporations(min_similarity: float = 0.8):
    """
    Match unmatched facilities to corporations based on name and location similarity
    """
    db = SessionLocal()

    try:
        # Get all unmatched facilities
        unmatched_facilities = db.query(Facility).filter_by(match_status='unmatched').all()
        print(f"📋 Found {len(unmatched_facilities)} unmatched facilities")

        matched_count = 0

        for facility in unmatched_facilities:
            if not facility.prefecture:
                continue

            # Find corporations in the same prefecture with similar names
            corporations = db.query(Corporation).filter_by(prefecture=facility.prefecture).all()

            best_match = None
            best_score = 0

            for corp in corporations:
                # Extract common parts from facility name and corporation name
                # e.g., "○○社会福祉法人 ☆☆デイサービス" -> "☆☆"
                facility_name_part = facility.name.replace('デイサービス', '').replace('訪問介護', '').replace('施設', '').strip()

                if fuzzy_match(facility_name_part, corp.name, min_similarity):
                    score = SequenceMatcher(None, facility_name_part.lower(), corp.name.lower()).ratio()
                    if score > best_score:
                        best_score = score
                        best_match = corp

            if best_match and best_score >= min_similarity:
                facility.corporation_id = best_match.corporation_id
                facility.match_status = 'matched'
                facility.updated_at = datetime.utcnow()
                matched_count += 1
                print(f"  ✓ {facility.name} -> {best_match.name} (score: {best_score:.2f})")

        db.commit()
        print(f"\n✓ Matched {matched_count} facilities")

    except Exception as e:
        print(f"❌ Error during matching: {e}")
        db.rollback()

    finally:
        db.close()


def show_unmatched_summary():
    """Show summary of still-unmatched facilities"""
    db = SessionLocal()

    try:
        unmatched = db.query(Facility).filter_by(match_status='unmatched').all()
        print(f"\n📊 Unmatched facilities summary:")
        print(f"   Total: {len(unmatched)}")

        if unmatched:
            print(f"\n   First 5 unmatched:")
            for facility in unmatched[:5]:
                print(f"     - {facility.name} ({facility.prefecture}/{facility.city})")

    finally:
        db.close()


if __name__ == "__main__":
    min_sim = float(sys.argv[1]) if len(sys.argv) > 1 else 0.8
    print(f"🔍 Matching facilities to corporations (min similarity: {min_sim})...")
    match_facilities_to_corporations(min_sim)
    show_unmatched_summary()
