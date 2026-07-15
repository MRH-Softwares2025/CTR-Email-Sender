import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore as fb_firestore

DB_PATH = Path(__file__).resolve().parent / "app.db"


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def init_firestore():
    project_id = os.getenv("FIREBASE_PROJECT_ID")
    service_account = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON", "").strip()

    if not firebase_admin._apps:
        if not service_account:
            raise RuntimeError("Set FIREBASE_SERVICE_ACCOUNT_JSON to your service account file path before migration.")
        cred = credentials.Certificate(service_account)
        firebase_admin.initialize_app(cred, {"projectId": project_id} if project_id else None)

    return fb_firestore.client()


def migrate_plans(conn, db):
    rows = conn.execute("SELECT id, name, duration_days, price, description, active, created_at FROM subscription_plans").fetchall()
    for row in rows:
        db.collection("subscription_plans").document(str(row["id"])).set(
            {
                "id": row["id"],
                "name": row["name"],
                "duration_days": row["duration_days"],
                "price": row["price"],
                "description": row["description"],
                "active": bool(row["active"]),
                "created_at": row["created_at"] or now_iso(),
            }
        )


def migrate_users(conn, db):
    rows = conn.execute("SELECT gmail_email, password_hash, created_at FROM users").fetchall()
    for row in rows:
        db.collection("users").document(row["gmail_email"]).set(
            {
                "gmail_email": row["gmail_email"],
                "password_hash": row["password_hash"],
                "created_at": row["created_at"] or now_iso(),
            }
        )


def migrate_settings(conn, db):
    row = conn.execute(
        "SELECT gmail_email, app_password, email_subject, email_body, start_hour, end_hour, emails_per_hour, time_variation_seconds FROM settings ORDER BY id DESC LIMIT 1"
    ).fetchone()
    if not row:
        return

    db.collection("settings").document("global").set(
        {
            "gmail_email": row["gmail_email"],
            "app_password": row["app_password"],
            "email_subject": row["email_subject"],
            "email_body": row["email_body"],
            "start_hour": row["start_hour"],
            "end_hour": row["end_hour"],
            "emails_per_hour": row["emails_per_hour"],
            "time_variation_seconds": row["time_variation_seconds"],
            "updated_at": now_iso(),
        }
    )


def migrate_subscriptions(conn, db):
    rows = conn.execute(
        "SELECT gmail_email, expiry, active, plan_id, amount_paid, start_date FROM subscription ORDER BY id ASC"
    ).fetchall()

    latest_by_email = {}
    for row in rows:
        latest_by_email[row["gmail_email"]] = row

    for gmail_email, row in latest_by_email.items():
        db.collection("subscriptions").document(gmail_email).set(
            {
                "gmail_email": gmail_email,
                "expiry": row["expiry"],
                "active": bool(row["active"]),
                "plan_id": row["plan_id"],
                "amount_paid": row["amount_paid"],
                "start_date": row["start_date"],
                "updated_at": now_iso(),
            }
        )


def migrate_payments(conn, db):
    rows = conn.execute(
        "SELECT checkout_request_id, gmail_email, phone_number, status, plan_id, amount, created_at, updated_at FROM payments"
    ).fetchall()
    for row in rows:
        if not row["checkout_request_id"]:
            continue
        db.collection("payments").document(row["checkout_request_id"]).set(
            {
                "checkout_request_id": row["checkout_request_id"],
                "gmail_email": row["gmail_email"],
                "phone_number": row["phone_number"],
                "status": row["status"],
                "plan_id": row["plan_id"],
                "amount": row["amount"],
                "created_at": row["created_at"] or now_iso(),
                "updated_at": row["updated_at"] or now_iso(),
            }
        )


def migrate_logs(conn, db):
    rows = conn.execute("SELECT message, timestamp FROM logs ORDER BY id ASC").fetchall()
    for row in rows:
        db.collection("logs").document().set(
            {
                "message": row["message"],
                "timestamp": row["timestamp"] or now_iso(),
            }
        )


def main():
    if not DB_PATH.exists():
        raise RuntimeError(f"SQLite file not found: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    db = init_firestore()

    migrate_plans(conn, db)
    migrate_users(conn, db)
    migrate_settings(conn, db)
    migrate_subscriptions(conn, db)
    migrate_payments(conn, db)
    migrate_logs(conn, db)

    conn.close()
    print("Migration complete: SQLite -> Firestore")


if __name__ == "__main__":
    main()
