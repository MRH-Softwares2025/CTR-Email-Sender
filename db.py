import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "app.db"

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
    created_at TEXT
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


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_default_plans():
    """Initialize default subscription plans if they don't exist"""
    default_plans = [
        {
            "name": "Daily",
            "duration_days": 1,
            "price": 10,
            "description": "24-hour access to email automation features"
        },
        {
            "name": "Weekly",
            "duration_days": 7,
            "price": 50,
            "description": "7-day access to email automation features"
        },
        {
            "name": "Fortnightly",
            "duration_days": 14,
            "price": 80,
            "description": "14-day access to email automation features"
        },
        {
            "name": "Monthly",
            "duration_days": 30,
            "price": 100,
            "description": "30-day access to email automation features"
        }
    ]
    
    with get_connection() as conn:
        # Check if plans already exist
        existing = conn.execute("SELECT COUNT(*) as count FROM subscription_plans").fetchone()
        if existing["count"] > 0:
            return
        
        now = datetime.now(timezone.utc).isoformat()
        for plan in default_plans:
            conn.execute(
                "INSERT INTO subscription_plans (name, duration_days, price, description, active, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (plan["name"], plan["duration_days"], plan["price"], plan["description"], 1, now)
            )
        conn.commit()


def initialize_db():
    with get_connection() as conn:
        conn.execute(CREATE_SUBSCRIPTION_TABLE)
        conn.execute(CREATE_SETTINGS_TABLE)
        conn.execute(CREATE_USERS_TABLE)
        conn.execute(CREATE_SUBSCRIPTION_PLANS_TABLE)
        conn.execute(CREATE_PAYMENTS_TABLE)
        conn.execute(CREATE_LOGS_TABLE)
        conn.commit()
        # Initialize default plans if they don't exist
        initialize_default_plans()


initialize_db()


def get_plans(active_only=True):
    """Get all subscription plans"""
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
                "active": bool(row["active"])
            }
            for row in rows
        ]


def get_plan(plan_id):
    """Get a specific plan by ID"""
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
            "active": bool(row["active"])
        }


def get_subscription(gmail_email=None):
    """Get subscription for a specific user or the most recent subscription if no email provided"""
    with get_connection() as conn:
        if gmail_email:
            row = conn.execute(
                "SELECT expiry, active, plan_id, amount_paid, start_date FROM subscription WHERE gmail_email = ? ORDER BY id DESC LIMIT 1",
                (gmail_email,)
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
            "start_date": row["start_date"]
        }
        
        # If plan_id exists, fetch plan details
        if result["plan_id"]:
            plan = get_plan(result["plan_id"])
            if plan:
                result["plan"] = plan
        
        return result


def get_user_subscription(gmail_email):
    """Get subscription for a specific user by email"""
    return get_subscription(gmail_email)


def set_subscription(expiry, active=True, plan_id=None, amount_paid=None, start_date=None, gmail_email=None):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO subscription (expiry, active, plan_id, amount_paid, start_date, gmail_email) VALUES (?, ?, ?, ?, ?, ?)",
            (expiry, int(active), plan_id, amount_paid, start_date, gmail_email),
        )
        conn.commit()


def get_settings():
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
    with get_connection() as conn:
        conn.execute("DELETE FROM settings")
        conn.commit()


def add_payment_attempt(checkout_request_id, phone_number, status, plan_id=None, amount=None, gmail_email=None):
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO payments (checkout_request_id, gmail_email, phone_number, status, plan_id, amount, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (checkout_request_id, gmail_email, phone_number, status, plan_id, amount, now, now),
        )
        conn.commit()


def update_payment_attempt(checkout_request_id, status, plan_id=None, amount=None):
    now = datetime.now(timezone.utc).isoformat()
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
    """Get payment details by checkout request ID"""
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
            "updated_at": row["updated_at"]
        }


def add_log(message):
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO logs (message, timestamp) VALUES (?, ?)",
            (message, now),
        )
        conn.commit()


def get_recent_logs(limit=50):
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT message, timestamp FROM logs ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [f"{row['timestamp']} - {row['message']}" for row in rows]


def create_user(gmail_email, password_hash):
    """Create a new user with hashed password"""
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        try:
            conn.execute(
                "INSERT INTO users (gmail_email, password_hash, created_at) VALUES (?, ?, ?)",
                (gmail_email, password_hash, now)
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False


def get_user(gmail_email):
    """Get user by email"""
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM users WHERE gmail_email = ?", (gmail_email,)).fetchone()
        if not row:
            return None
        return {
            "id": row["id"],
            "gmail_email": row["gmail_email"],
            "password_hash": row["password_hash"],
            "created_at": row["created_at"]
        }
