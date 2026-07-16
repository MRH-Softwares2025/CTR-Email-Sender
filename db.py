import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "app.db"

DEFAULT_PLANS = [
    {
        "id": 1,
        "name": "Daily",
        "duration_days": 1,
        "price": 10,
        "description": "24-hour access to email automation features",
    },
    {
        "id": 2,
        "name": "Weekly",
        "duration_days": 7,
        "price": 50,
        "description": "7-day access to email automation features",
    },
    {
        "id": 3,
        "name": "Fortnightly",
        "duration_days": 14,
        "price": 80,
        "description": "14-day access to email automation features",
    },
    {
        "id": 4,
        "name": "Monthly",
        "duration_days": 30,
        "price": 100,
        "description": "30-day access to email automation features",
    },
]

CREATE_SUBSCRIPTION_TABLE = """
CREATE TABLE IF NOT EXISTS subscription (
    id INTEGER PRIMARY KEY,
    gmail_email TEXT NOT NULL,
    expiry TEXT NOT NULL,
    active INTEGER NOT NULL,
    plan_id INTEGER,
    amount_paid INTEGER,
    start_date TEXT
)
"""

CREATE_SETTINGS_TABLE = """
CREATE TABLE IF NOT EXISTS settings (
    id INTEGER PRIMARY KEY,
    gmail_email TEXT,
    app_password TEXT,
    email_subject TEXT,
    email_body TEXT,
    start_hour INTEGER,
    end_hour INTEGER,
    emails_per_hour INTEGER,
    time_variation_seconds REAL
)
"""

CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    gmail_email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TEXT,
    oauth_credentials TEXT,
    oauth_connected_at TEXT
)
"""

CREATE_SUBSCRIPTION_PLANS_TABLE = """
CREATE TABLE IF NOT EXISTS subscription_plans (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    duration_days INTEGER NOT NULL,
    price INTEGER NOT NULL,
    description TEXT,
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT
)
"""

CREATE_PAYMENTS_TABLE = """
CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY,
    checkout_request_id TEXT UNIQUE,
    gmail_email TEXT,
    phone_number TEXT,
    status TEXT,
    plan_id INTEGER,
    amount INTEGER,
    created_at TEXT,
    updated_at TEXT
)
"""

CREATE_LOGS_TABLE = """
CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY,
    message TEXT,
    timestamp TEXT
)
"""


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def _get_backend():
    explicit = os.getenv("DB_BACKEND", "").strip().lower()
    if explicit in ("firestore", "firebase"):
        return "firestore"
    if explicit == "sqlite":
        return "sqlite"
    if os.getenv("FIREBASE_PROJECT_ID") or os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON") or os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        return "firestore"
    return "sqlite"


_BACKEND = _get_backend()
_FIRESTORE_CLIENT = None


def _load_firestore_client():
    global _FIRESTORE_CLIENT
    if _FIRESTORE_CLIENT is not None:
        return _FIRESTORE_CLIENT

    try:
        import firebase_admin
        from firebase_admin import credentials
        from firebase_admin import firestore as fb_firestore
    except Exception as exc:
        raise RuntimeError("Firebase dependencies are missing. Install firebase-admin and google-cloud-firestore.") from exc

    if not firebase_admin._apps:
        project_id = os.getenv("FIREBASE_PROJECT_ID")
        sa = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON", "").strip()
        if sa:
            if sa.startswith("{"):
                cred = credentials.Certificate(json.loads(sa))
            else:
                cred = credentials.Certificate(sa)
            firebase_admin.initialize_app(cred, {"projectId": project_id} if project_id else None)
        else:
            firebase_admin.initialize_app(options={"projectId": project_id} if project_id else None)

    _FIRESTORE_CLIENT = fb_firestore.client()
    return _FIRESTORE_CLIENT


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_default_plans():
    if _BACKEND == "firestore":
        db = _load_firestore_client()
        plans = db.collection("subscription_plans").limit(1).get()
        if plans:
            return
        now = _now_iso()
        for plan in DEFAULT_PLANS:
            payload = dict(plan)
            payload["active"] = True
            payload["created_at"] = now
            db.collection("subscription_plans").document(str(plan["id"])) .set(payload)
        return

    with get_connection() as conn:
        existing = conn.execute("SELECT COUNT(*) as count FROM subscription_plans").fetchone()
        if existing["count"] > 0:
            return

        now = _now_iso()
        for plan in DEFAULT_PLANS:
            conn.execute(
                "INSERT INTO subscription_plans (id, name, duration_days, price, description, active, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (plan["id"], plan["name"], plan["duration_days"], plan["price"], plan["description"], 1, now),
            )
        conn.commit()


def initialize_db():
    if _BACKEND == "firestore":
        initialize_default_plans()
        return

    with get_connection() as conn:
        conn.execute(CREATE_SUBSCRIPTION_TABLE)
        conn.execute(CREATE_SETTINGS_TABLE)
        conn.execute(CREATE_USERS_TABLE)
        conn.execute(CREATE_SUBSCRIPTION_PLANS_TABLE)
        conn.execute(CREATE_PAYMENTS_TABLE)
        conn.execute(CREATE_LOGS_TABLE)
        _ensure_sqlite_migrations(conn)
        conn.commit()
        initialize_default_plans()


def _ensure_sqlite_migrations(conn):
    """Apply additive SQLite schema updates for existing installations."""
    cols = conn.execute("PRAGMA table_info(users)").fetchall()
    names = {row[1] for row in cols}

    if "oauth_credentials" not in names:
        conn.execute("ALTER TABLE users ADD COLUMN oauth_credentials TEXT")
    if "oauth_connected_at" not in names:
        conn.execute("ALTER TABLE users ADD COLUMN oauth_connected_at TEXT")


initialize_db()


def get_plans(active_only=True):
    if _BACKEND == "firestore":
        db = _load_firestore_client()
        docs = db.collection("subscription_plans").stream()
        plans = []
        for doc in docs:
            data = doc.to_dict() or {}
            plan = {
                "id": int(data.get("id", doc.id)),
                "name": data.get("name"),
                "duration_days": int(data.get("duration_days", 0)),
                "price": int(data.get("price", 0)),
                "description": data.get("description"),
                "active": bool(data.get("active", True)),
            }
            if not active_only or plan["active"]:
                plans.append(plan)
        return sorted(plans, key=lambda p: p["duration_days"])

    with get_connection() as conn:
        if active_only:
            rows = conn.execute("SELECT * FROM subscription_plans WHERE active = 1 ORDER BY duration_days").fetchall()
        else:
            rows = conn.execute("SELECT * FROM subscription_plans ORDER BY duration_days").fetchall()

        return [
            {
                "id": row["id"],
                "name": row["name"],
                "duration_days": row["duration_days"],
                "price": row["price"],
                "description": row["description"],
                "active": bool(row["active"]),
            }
            for row in rows
        ]


def get_plan(plan_id):
    if _BACKEND == "firestore":
        db = _load_firestore_client()
        doc = db.collection("subscription_plans").document(str(plan_id)).get()
        if not doc.exists:
            return None
        data = doc.to_dict() or {}
        return {
            "id": int(data.get("id", plan_id)),
            "name": data.get("name"),
            "duration_days": int(data.get("duration_days", 0)),
            "price": int(data.get("price", 0)),
            "description": data.get("description"),
            "active": bool(data.get("active", True)),
        }

    with get_connection() as conn:
        row = conn.execute("SELECT * FROM subscription_plans WHERE id = ?", (plan_id,)).fetchone()
        if not row:
            return None

        return {
            "id": row["id"],
            "name": row["name"],
            "duration_days": row["duration_days"],
            "price": row["price"],
            "description": row["description"],
            "active": bool(row["active"]),
        }


def get_subscription(gmail_email=None):
    if _BACKEND == "firestore":
        db = _load_firestore_client()
        if gmail_email:
            doc = db.collection("subscriptions").document(gmail_email).get()
            if not doc.exists:
                return None
            data = doc.to_dict() or {}
        else:
            docs = db.collection("subscriptions").order_by("updated_at", direction="DESCENDING").limit(1).get()
            if not docs:
                return None
            data = docs[0].to_dict() or {}

        result = {
            "expiry": data.get("expiry"),
            "active": bool(data.get("active", False)),
            "plan_id": data.get("plan_id"),
            "amount_paid": data.get("amount_paid"),
            "start_date": data.get("start_date"),
        }
        if result["plan_id"]:
            plan = get_plan(result["plan_id"])
            if plan:
                result["plan"] = plan
        return result

    with get_connection() as conn:
        if gmail_email:
            row = conn.execute(
                "SELECT expiry, active, plan_id, amount_paid, start_date FROM subscription WHERE gmail_email = ? ORDER BY id DESC LIMIT 1",
                (gmail_email,),
            ).fetchone()
        else:
            row = conn.execute("SELECT expiry, active, plan_id, amount_paid, start_date FROM subscription ORDER BY id DESC LIMIT 1").fetchone()

        if not row:
            return None

        result = {
            "expiry": row["expiry"],
            "active": bool(row["active"]),
            "plan_id": row["plan_id"],
            "amount_paid": row["amount_paid"],
            "start_date": row["start_date"],
        }

        if result["plan_id"]:
            plan = get_plan(result["plan_id"])
            if plan:
                result["plan"] = plan

        return result


def get_user_subscription(gmail_email):
    return get_subscription(gmail_email)


def set_subscription(expiry, active=True, plan_id=None, amount_paid=None, start_date=None, gmail_email=None):
    if _BACKEND == "firestore":
        db = _load_firestore_client()
        email_key = gmail_email or "global"
        payload = {
            "gmail_email": gmail_email,
            "expiry": expiry,
            "active": bool(active),
            "plan_id": plan_id,
            "amount_paid": amount_paid,
            "start_date": start_date,
            "updated_at": _now_iso(),
        }
        db.collection("subscriptions").document(email_key).set(payload)
        return

    with get_connection() as conn:
        conn.execute(
            "INSERT INTO subscription (expiry, active, plan_id, amount_paid, start_date, gmail_email) VALUES (?, ?, ?, ?, ?, ?)",
            (expiry, int(active), plan_id, amount_paid, start_date, gmail_email),
        )
        conn.commit()


def get_settings():
    if _BACKEND == "firestore":
        db = _load_firestore_client()
        doc = db.collection("settings").document("global").get()
        if not doc.exists:
            return None
        data = doc.to_dict() or {}
        return {
            "gmail_email": data.get("gmail_email"),
            "app_password": data.get("app_password"),
            "email_subject": data.get("email_subject"),
            "email_body": data.get("email_body"),
            "start_hour": data.get("start_hour"),
            "end_hour": data.get("end_hour"),
            "emails_per_hour": data.get("emails_per_hour"),
            "time_variation_seconds": data.get("time_variation_seconds"),
        }

    with get_connection() as conn:
        row = conn.execute("SELECT * FROM settings ORDER BY id DESC LIMIT 1").fetchone()
        if not row:
            return None
        return {
            "gmail_email": row["gmail_email"],
            "app_password": row["app_password"],
            "email_subject": row["email_subject"],
            "email_body": row["email_body"],
            "start_hour": row["start_hour"],
            "end_hour": row["end_hour"],
            "emails_per_hour": row["emails_per_hour"],
            "time_variation_seconds": row["time_variation_seconds"],
        }


def save_settings(settings):
    if _BACKEND == "firestore":
        db = _load_firestore_client()
        payload = {
            "gmail_email": settings.get("gmail_email"),
            "app_password": settings.get("app_password"),
            "email_subject": settings.get("email_subject"),
            "email_body": settings.get("email_body"),
            "start_hour": settings.get("start_hour"),
            "end_hour": settings.get("end_hour"),
            "emails_per_hour": settings.get("emails_per_hour"),
            "time_variation_seconds": settings.get("time_variation_seconds"),
            "updated_at": _now_iso(),
        }
        db.collection("settings").document("global").set(payload)
        return

    with get_connection() as conn:
        conn.execute(
            "INSERT INTO settings (gmail_email, app_password, email_subject, email_body, start_hour, end_hour, emails_per_hour, time_variation_seconds) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                settings.get("gmail_email"),
                settings.get("app_password"),
                settings.get("email_subject"),
                settings.get("email_body"),
                settings.get("start_hour"),
                settings.get("end_hour"),
                settings.get("emails_per_hour"),
                settings.get("time_variation_seconds"),
            ),
        )
        conn.commit()


def clear_settings():
    if _BACKEND == "firestore":
        db = _load_firestore_client()
        db.collection("settings").document("global").delete()
        return

    with get_connection() as conn:
        conn.execute("DELETE FROM settings")
        conn.commit()


def add_payment_attempt(checkout_request_id, phone_number, status, plan_id=None, amount=None, gmail_email=None):
    now = _now_iso()
    if _BACKEND == "firestore":
        db = _load_firestore_client()
        payload = {
            "checkout_request_id": checkout_request_id,
            "gmail_email": gmail_email,
            "phone_number": phone_number,
            "status": status,
            "plan_id": plan_id,
            "amount": amount,
            "created_at": now,
            "updated_at": now,
        }
        db.collection("payments").document(checkout_request_id).set(payload, merge=True)
        return

    with get_connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO payments (checkout_request_id, gmail_email, phone_number, status, plan_id, amount, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (checkout_request_id, gmail_email, phone_number, status, plan_id, amount, now, now),
        )
        conn.commit()


def update_payment_attempt(checkout_request_id, status, plan_id=None, amount=None):
    now = _now_iso()
    if _BACKEND == "firestore":
        db = _load_firestore_client()
        payload = {"status": status, "updated_at": now}
        if plan_id is not None:
            payload["plan_id"] = plan_id
        if amount is not None:
            payload["amount"] = amount
        db.collection("payments").document(checkout_request_id).set(payload, merge=True)
        return

    with get_connection() as conn:
        if plan_id is not None and amount is not None:
            conn.execute(
                "UPDATE payments SET status = ?, plan_id = ?, amount = ?, updated_at = ? WHERE checkout_request_id = ?",
                (status, plan_id, amount, now, checkout_request_id),
            )
        else:
            conn.execute(
                "UPDATE payments SET status = ?, updated_at = ? WHERE checkout_request_id = ?",
                (status, now, checkout_request_id),
            )
        conn.commit()


def get_payment(checkout_request_id):
    if _BACKEND == "firestore":
        db = _load_firestore_client()
        doc = db.collection("payments").document(checkout_request_id).get()
        if not doc.exists:
            return None
        data = doc.to_dict() or {}
        return {
            "id": None,
            "checkout_request_id": data.get("checkout_request_id", checkout_request_id),
            "gmail_email": data.get("gmail_email"),
            "phone_number": data.get("phone_number"),
            "status": data.get("status"),
            "plan_id": data.get("plan_id"),
            "amount": data.get("amount"),
            "created_at": data.get("created_at"),
            "updated_at": data.get("updated_at"),
        }

    with get_connection() as conn:
        row = conn.execute("SELECT * FROM payments WHERE checkout_request_id = ?", (checkout_request_id,)).fetchone()
        if not row:
            return None

        return {
            "id": row["id"],
            "checkout_request_id": row["checkout_request_id"],
            "gmail_email": row["gmail_email"],
            "phone_number": row["phone_number"],
            "status": row["status"],
            "plan_id": row["plan_id"],
            "amount": row["amount"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }


def add_log(message):
    now = _now_iso()
    if _BACKEND == "firestore":
        db = _load_firestore_client()
        db.collection("logs").document().set({"message": message, "timestamp": now})
        return

    with get_connection() as conn:
        conn.execute("INSERT INTO logs (message, timestamp) VALUES (?, ?)", (message, now))
        conn.commit()


def get_recent_logs(limit=50):
    if _BACKEND == "firestore":
        db = _load_firestore_client()
        docs = db.collection("logs").order_by("timestamp", direction="DESCENDING").limit(limit).stream()
        return [f"{(doc.to_dict() or {}).get('timestamp')} - {(doc.to_dict() or {}).get('message')}" for doc in docs]

    with get_connection() as conn:
        rows = conn.execute("SELECT message, timestamp FROM logs ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [f"{row['timestamp']} - {row['message']}" for row in rows]


def create_user(gmail_email, password_hash):
    now = _now_iso()
    if _BACKEND == "firestore":
        db = _load_firestore_client()
        doc_ref = db.collection("users").document(gmail_email)
        if doc_ref.get().exists:
            return False
        doc_ref.set({"gmail_email": gmail_email, "password_hash": password_hash, "created_at": now})
        return True

    with get_connection() as conn:
        try:
            conn.execute("INSERT INTO users (gmail_email, password_hash, created_at) VALUES (?, ?, ?)", (gmail_email, password_hash, now))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False


def get_user(gmail_email):
    if _BACKEND == "firestore":
        db = _load_firestore_client()
        doc = db.collection("users").document(gmail_email).get()
        if not doc.exists:
            return None
        data = doc.to_dict() or {}
        return {
            "id": data.get("id"),
            "gmail_email": data.get("gmail_email", gmail_email),
            "password_hash": data.get("password_hash"),
            "created_at": data.get("created_at"),
            "oauth_credentials": data.get("oauth_credentials"),
            "oauth_connected_at": data.get("oauth_connected_at"),
        }

    with get_connection() as conn:
        row = conn.execute("SELECT * FROM users WHERE gmail_email = ?", (gmail_email,)).fetchone()
        if not row:
            return None
        return {
            "id": row["id"],
            "gmail_email": row["gmail_email"],
            "password_hash": row["password_hash"],
            "created_at": row["created_at"],
            "oauth_credentials": row["oauth_credentials"],
            "oauth_connected_at": row["oauth_connected_at"],
        }


def update_user_password(gmail_email, new_password_hash):
    if _BACKEND == "firestore":
        db = _load_firestore_client()
        doc_ref = db.collection("users").document(gmail_email)
        if not doc_ref.get().exists:
            return False
        doc_ref.update({"password_hash": new_password_hash})
        return True

    with get_connection() as conn:
        result = conn.execute(
            "UPDATE users SET password_hash = ? WHERE gmail_email = ?",
            (new_password_hash, gmail_email),
        )
        conn.commit()
        return result.rowcount > 0


def save_user_oauth_credentials(gmail_email, credentials_payload):
    now = _now_iso()
    if _BACKEND == "firestore":
        db = _load_firestore_client()
        doc_ref = db.collection("users").document(gmail_email)
        if not doc_ref.get().exists:
            return False
        doc_ref.update({
            "oauth_credentials": credentials_payload,
            "oauth_connected_at": now,
        })
        return True

    with get_connection() as conn:
        result = conn.execute(
            "UPDATE users SET oauth_credentials = ?, oauth_connected_at = ? WHERE gmail_email = ?",
            (json.dumps(credentials_payload), now, gmail_email),
        )
        conn.commit()
        return result.rowcount > 0


def get_user_oauth_credentials(gmail_email):
    if _BACKEND == "firestore":
        db = _load_firestore_client()
        doc = db.collection("users").document(gmail_email).get()
        if not doc.exists:
            return None
        data = doc.to_dict() or {}
        payload = data.get("oauth_credentials")
        return payload if isinstance(payload, dict) else None

    with get_connection() as conn:
        row = conn.execute("SELECT oauth_credentials FROM users WHERE gmail_email = ?", (gmail_email,)).fetchone()
        if not row or not row["oauth_credentials"]:
            return None
        try:
            return json.loads(row["oauth_credentials"])
        except (TypeError, json.JSONDecodeError):
            return None


def clear_user_oauth_credentials(gmail_email):
    if _BACKEND == "firestore":
        db = _load_firestore_client()
        doc_ref = db.collection("users").document(gmail_email)
        if not doc_ref.get().exists:
            return False
        doc_ref.update({"oauth_credentials": None})
        return True

    with get_connection() as conn:
        result = conn.execute(
            "UPDATE users SET oauth_credentials = NULL WHERE gmail_email = ?",
            (gmail_email,),
        )
        conn.commit()
        return result.rowcount > 0
