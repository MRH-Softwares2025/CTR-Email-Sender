import base64
import json
import os
import re
import threading
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request, Depends, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from passlib.context import CryptContext
from starlette.middleware.sessions import SessionMiddleware

from db import (
    add_log,
    add_payment_attempt,
    clear_settings,
    get_recent_logs,
    get_settings,
    get_subscription,
    get_user_subscription,
    set_subscription,
    save_settings,
    update_payment_attempt,
    get_plans,
    get_plan,
    get_payment,
    create_user,
    get_user,
)
from email_automation import EmailAutomationBot, EmailAutomationConfig
from notification_system import get_notification_manager, NotificationPriority

BASE_DIR = Path(__file__).resolve().parent


def load_env_file():
    env_path = BASE_DIR / ".env"
    if not env_path.exists():
        return

    with env_path.open("r", encoding="utf-8") as f:
        lines = f.readlines()

    body_lines = []
    reading_body = False
    body_key_pattern = re.compile(r"^EMAIL_BODY=(.*)$")
    key_pattern = re.compile(r"^[A-Z0-9_]+=.*$")

    for raw_line in lines:
        raw_line = raw_line.rstrip("\n")
        stripped = raw_line.strip()

        if reading_body:
            if key_pattern.match(raw_line):
                reading_body = False
            else:
                body_lines.append(raw_line)
                continue

        if not stripped or stripped.startswith("#"):
            continue

        body_match = body_key_pattern.match(raw_line)
        if body_match:
            reading_body = True
            body_lines.append(body_match.group(1))
            continue

        if "=" in raw_line:
            key, value = raw_line.split("=", 1)
            os.environ[key] = value

    if body_lines:
        os.environ["EMAIL_BODY"] = "\n".join(body_lines)


load_env_file()

app = FastAPI(docs_url=None, redoc_url=None)
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY", "your-secret-key-change-in-production"),
    same_site="lax",
    https_only=False,
)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; connect-src 'self'; font-src 'self' data:; object-src 'none'; "
        "base-uri 'self'; frame-ancestors 'none'"
    )
    return response

# Password hashing
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

bot = None
bot_thread = None
bot_lock = threading.Lock()


class SubscriptionPayRequest(BaseModel):
    phone_number: str
    plan_id: int


class SubscriptionConfirmRequest(BaseModel):
    checkout_request_id: str
    status: str


class ConfigRequest(BaseModel):
    gmail_email: str
    app_password: str = ""
    email_subject: str
    email_body: str
    start_hour: int
    end_hour: int
    emails_per_hour: int
    time_variation_seconds: float


class BatchRequest(BaseModel):
    count: int


def is_subscription_check_disabled():
    return os.getenv("DISABLE_SUBSCRIPTION_CHECK", "false").lower() in ("1", "true", "yes")


def is_subscription_active(gmail_email=None):
    record = get_subscription(gmail_email)
    if not record or not record.get("expiry"):
        return False
    expiry = datetime.fromisoformat(record["expiry"])
    return datetime.now(timezone.utc) < expiry


def get_current_user(request: Request):
    """Get current logged-in user from session"""
    user_email = request.session.get("user_email")
    if not user_email:
        return None
    return user_email


def require_login(request: Request):
    """Check if user is logged in, redirect to login if not"""
    user_email = get_current_user(request)
    if not user_email:
        raise HTTPException(status_code=303, headers={"Location": "/login"})
    return user_email


def get_subscription_response(gmail_email=None):
    subscription = get_subscription(gmail_email)
    subscription_required = not is_subscription_check_disabled()
    if not subscription or not subscription.get("expiry"):
        return {
            "active": False,
            "expiry": None,
            "days_left": 0,
            "subscription_required": subscription_required,
            "plan": None,
            "amount_paid": None,
            "start_date": None,
        }

    expiry = datetime.fromisoformat(subscription["expiry"])
    now = datetime.now(timezone.utc)
    days_left = max((expiry - now).days, 0)
    return {
        "active": now < expiry,
        "expiry": expiry.isoformat(),
        "days_left": days_left,
        "subscription_required": subscription_required,
        "plan": subscription.get("plan"),
        "amount_paid": subscription.get("amount_paid"),
        "start_date": subscription.get("start_date"),
    }


def normalize_phone_number(phone_number: str) -> str:
    cleaned = re.sub(r"[^0-9+]", "", phone_number or "")
    if not cleaned:
        raise ValueError("Phone number is required")

    if cleaned.startswith("+254"):
        return cleaned[1:]
    if cleaned.startswith("254"):
        return cleaned
    if cleaned.startswith("07"):
        return f"254{cleaned[1:]}"
    if cleaned.startswith("7"):
        return f"254{cleaned}"
    raise ValueError("Use a Kenyan number like 07XXXXXXXX or +2547XXXXXXXX")


def get_mpesa_config():
    consumer_key = os.getenv("MPESA_CONSUMER_KEY")
    consumer_secret = os.getenv("MPESA_CONSUMER_SECRET")
    shortcode = os.getenv("MPESA_SHORTCODE")
    passkey = os.getenv("MPESA_PASSKEY")
    callback_url = os.getenv("MPESA_CALLBACK_URL", "http://localhost:8001/api/subscription/callback")
    env_name = os.getenv("MPESA_ENVIRONMENT", "sandbox").lower()
    base_url = os.getenv("MPESA_BASE_URL", "https://sandbox.safaricom.co.ke") if env_name == "sandbox" else os.getenv("MPESA_BASE_URL", "https://api.safaricom.co.ke")
    return {
        "consumer_key": consumer_key,
        "consumer_secret": consumer_secret,
        "shortcode": shortcode,
        "passkey": passkey,
        "callback_url": callback_url,
        "base_url": base_url,
    }


def get_mpesa_access_token():
    mpesa_config = get_mpesa_config()
    consumer_key = mpesa_config["consumer_key"]
    consumer_secret = mpesa_config["consumer_secret"]
    if not consumer_key or not consumer_secret:
        raise RuntimeError("MPESA consumer credentials are not configured. Set MPESA_CONSUMER_KEY and MPESA_CONSUMER_SECRET in your .env file.")

    auth_url = f"{mpesa_config['base_url']}/oauth/v1/generate?grant_type=client_credentials"
    credentials = f"{consumer_key}:{consumer_secret}"
    auth_header = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")

    request = urllib.request.Request(
        auth_url,
        headers={
            "Authorization": f"Basic {auth_header}",
            "Cache-Control": "no-cache",
        },
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        body = response.read().decode("utf-8")
        data = json.loads(body)
        return data.get("access_token")


def initiate_mpesa_stk_push(phone_number: str, amount: str = "100"):
    mpesa_config = get_mpesa_config()
    shortcode = mpesa_config["shortcode"]
    passkey = mpesa_config["passkey"]
    callback_url = mpesa_config["callback_url"]

    if not shortcode or not passkey:
        raise RuntimeError("MPESA shortcode or passkey are not configured. Set MPESA_SHORTCODE and MPESA_PASSKEY in your .env file.")

    normalized_phone = normalize_phone_number(phone_number)
    access_token = get_mpesa_access_token()
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    password = base64.b64encode(f"{shortcode}{passkey}{timestamp}".encode("utf-8")).decode("utf-8")

    payload = {
        "BusinessShortCode": shortcode,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": int(amount),
        "PartyA": normalized_phone,
        "PartyB": shortcode,
        "PhoneNumber": normalized_phone,
        "CallBackURL": callback_url,
        "AccountReference": "EmailSubscription",
        "TransactionDesc": "Email automation subscription payment",
    }

    request = urllib.request.Request(
        f"{mpesa_config['base_url']}/mpesa/stkpush/v1/processrequest",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}",
        },
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        body = response.read().decode("utf-8")
        return json.loads(body)


def activate_subscription_for_payment(checkout_request_id: str, gmail_email: str, plan: dict, amount: int):
    expiry = datetime.now(timezone.utc) + timedelta(days=plan["duration_days"])
    start_date = datetime.now(timezone.utc).isoformat()
    set_subscription(
        expiry.isoformat(),
        True,
        plan_id=plan["id"],
        amount_paid=amount,
        start_date=start_date,
        gmail_email=gmail_email,
    )
    update_payment_attempt(checkout_request_id, "Success", plan_id=plan["id"], amount=amount)
    add_log(f"Subscription activated - Plan: {plan['name']} until {expiry.isoformat()}")
    return {
        "success": True,
        "message": f"Subscription activated with {plan['name']} plan.",
        "expiry": expiry.isoformat(),
        "plan": plan,
    }


def load_bot_config():
    settings = get_settings() or {}
    config = EmailAutomationConfig(
        gmail_email=settings.get("gmail_email", os.getenv("GMAIL_EMAIL", "")),
        app_password=settings.get("app_password", os.getenv("GMAIL_APP_PASSWORD", "")),
        email_subject=settings.get("email_subject", os.getenv("EMAIL_SUBJECT", "Automated Email")),
        email_body=settings.get("email_body", os.getenv("EMAIL_BODY", "This is an automated email.")),
        start_hour=int(settings.get("start_hour", os.getenv("START_HOUR", "9"))),
        end_hour=int(settings.get("end_hour", os.getenv("END_HOUR", "17"))),
        emails_per_hour=int(settings.get("emails_per_hour", os.getenv("EMAILS_PER_HOUR", "125"))),
        time_variation_seconds=float(settings.get("time_variation_seconds", os.getenv("TIME_VARIATION_SECONDS", "300"))),
    )
    return config


def get_bot_instance():
    global bot
    if bot is None:
        config = load_bot_config()
        bot = EmailAutomationBot(config)
    return bot


def has_saved_settings():
    settings = get_settings() or {}
    return bool(settings.get("gmail_email")) and bool(settings.get("app_password"))


def get_saved_settings():
    return get_settings() or {}


def create_bot_thread(target, *args):
    global bot_thread
    if bot_thread and bot_thread.is_alive():
        raise RuntimeError("A send operation is already running")
    thread = threading.Thread(target=target, args=args, daemon=True)
    bot_thread = thread
    thread.start()
    return thread


@app.post("/api/reset")
async def api_reset():
    global bot
    clear_settings()
    bot = None
    add_log("Configuration reset")
    return {"success": True, "message": "Settings reset. Please log in again."}


@app.get("/", response_class=RedirectResponse)
async def root(request: Request):
    return RedirectResponse(url="/login")


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    # If already logged in, redirect to appropriate page
    user_email = get_current_user(request)
    if user_email:
        settings = get_settings()
        if settings and settings.get("gmail_email") == user_email:
            if is_subscription_active(user_email) or is_subscription_check_disabled():
                return RedirectResponse(url="/send")
            return RedirectResponse(url="/subscription")
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/subscription", response_class=HTMLResponse)
async def subscription_page(request: Request):
    user_email = require_login(request)
    
    # Check if user has active subscription, redirect to send page if they do
    if is_subscription_active(user_email) or is_subscription_check_disabled():
        return RedirectResponse(url="/send")
    
    return templates.TemplateResponse("subscription.html", {"request": request})


@app.get("/send", response_class=HTMLResponse)
async def send_page(request: Request):
    user_email = require_login(request)

    # Check subscription for specific user
    if not (is_subscription_active(user_email) or is_subscription_check_disabled()):
        return RedirectResponse(url="/subscription")

    return templates.TemplateResponse(
        "send.html",
        {
            "request": request,
            "subscription_active": is_subscription_active(user_email),
            "dev_mode": is_subscription_check_disabled(),
        },
    )


@app.get("/api/status")
async def api_status():
    return {
        "running": bot_thread.is_alive() if bot_thread else False,
        **get_subscription_response(),
    }


@app.get("/api/plans")
async def api_plans():
    """Get all available subscription plans"""
    plans = get_plans(active_only=True)
    return {"plans": plans}


@app.get("/api/subscription")
async def api_subscription(gmail_email: str = None):
    # Get gmail_email from settings if not provided
    if not gmail_email:
        settings = get_settings()
        gmail_email = settings.get("gmail_email") if settings else None
    
    # Check subscription expiry and generate notifications
    subscription = get_subscription(gmail_email)
    if subscription and subscription.get("expiry"):
        expiry = datetime.fromisoformat(subscription["expiry"])
        notification_manager = get_notification_manager()
        plan_name = subscription.get("plan", {}).get("name") if subscription.get("plan") else None
        notification_manager.check_subscription_expiry(expiry, plan_name)
    
    return get_subscription_response(gmail_email)


@app.post("/api/subscription/pay")
async def api_subscription_pay(request: Request, payload: SubscriptionPayRequest):
    plan = get_plan(payload.plan_id)
    if not plan:
        return {"success": False, "message": "Invalid plan selected"}

    settings = get_settings() or {}
    gmail_email = get_current_user(request) or settings.get("gmail_email")
    try:
        normalized_phone = normalize_phone_number(payload.phone_number)
    except ValueError as exc:
        return {"success": False, "message": str(exc)}

    checkout_request_id = f"checkout_{int(datetime.now(timezone.utc).timestamp())}"
    add_payment_attempt(
        checkout_request_id=checkout_request_id,
        phone_number=normalized_phone,
        status="Pending",
        plan_id=payload.plan_id,
        amount=plan["price"],
        gmail_email=gmail_email,
    )
    add_log(f"Payment initiated for {normalized_phone} - Plan: {plan['name']} (KES {plan['price']})")

    try:
        mpesa_response = initiate_mpesa_stk_push(normalized_phone, amount=plan["price"])
        add_log(f"MPESA STK Push sent for {normalized_phone} - KES {plan['price']}")
        return {
            "success": True,
            "message": "MPESA STK Push initiated. Complete the prompt on your phone to activate the subscription.",
            "checkout_request_id": checkout_request_id,
            "mpesa_response": mpesa_response,
            "plan": plan,
        }
    except Exception as exc:
        add_log(f"MPESA initiation failed: {exc}")
        return {
            "success": False,
            "message": f"MPESA payment could not be started: {exc}",
            "checkout_request_id": checkout_request_id,
            "plan": plan,
        }


@app.post("/api/subscription/confirm")
async def api_subscription_confirm(request: Request):
    payload = await request.json()
    notification_manager = get_notification_manager()

    callback = payload.get("Body", {}).get("stkCallback") if isinstance(payload, dict) else None
    if callback:
        checkout_request_id = callback.get("CheckoutRequestID") or callback.get("MerchantRequestID")
        result_code = callback.get("ResultCode")
        result_desc = callback.get("ResultDesc", "No description provided")
        status = "success" if result_code == 0 else "failed"
    else:
        checkout_request_id = payload.get("checkout_request_id")
        status = str(payload.get("status", "")).lower()
        result_desc = payload.get("message", "No description provided")

    if status != "success":
        if checkout_request_id:
            update_payment_attempt(checkout_request_id, "Failed")
            add_log(f"Payment confirmation failed for {checkout_request_id}: {result_desc}")
        notification_manager.add_payment_notification(success=False)
        return {"success": False, "message": "Payment did not succeed."}

    payment = get_payment(checkout_request_id) if checkout_request_id else None
    if not payment or not payment.get("plan_id"):
        if checkout_request_id:
            update_payment_attempt(checkout_request_id, "Failed")
            add_log(f"Payment confirmation failed: No plan found for {checkout_request_id}")
        return {"success": False, "message": "Invalid payment: No plan associated."}

    plan = get_plan(payment["plan_id"])
    if not plan:
        update_payment_attempt(checkout_request_id, "Failed")
        add_log(f"Payment confirmation failed: Invalid plan ID {payment['plan_id']}")
        return {"success": False, "message": "Invalid plan."}

    result = activate_subscription_for_payment(
        checkout_request_id=checkout_request_id,
        gmail_email=payment.get("gmail_email"),
        plan=plan,
        amount=payment.get("amount") or plan["price"],
    )
    notification_manager.add_payment_notification(success=True, amount=plan["price"], plan_name=plan["name"])
    return result


@app.post("/api/subscription/callback")
async def api_subscription_callback(request: Request):
    payload = await request.json()
    callback = payload.get("Body", {}).get("stkCallback")
    if not callback:
        raise HTTPException(status_code=400, detail="Invalid MPESA callback payload")

    checkout_request_id = callback.get("CheckoutRequestID") or callback.get("MerchantRequestID")
    result_code = callback.get("ResultCode")
    result_desc = callback.get("ResultDesc", "No description provided")

    notification_manager = get_notification_manager()

    if result_code != 0:
        update_payment_attempt(checkout_request_id, "Failed")
        add_log(f"MPESA callback failed: {checkout_request_id} ({result_desc})")
        notification_manager.add_payment_notification(success=False)
        return {"success": False, "message": f"Payment failed: {result_desc}"}

    payment = get_payment(checkout_request_id)
    if not payment or not payment.get("plan_id"):
        update_payment_attempt(checkout_request_id, "Failed")
        add_log(f"MPESA callback failed: No plan found for {checkout_request_id}")
        return {"success": False, "message": "Invalid payment: No plan associated."}

    plan = get_plan(payment["plan_id"])
    if not plan:
        update_payment_attempt(checkout_request_id, "Failed")
        add_log(f"MPESA callback failed: Invalid plan ID {payment['plan_id']}")
        return {"success": False, "message": "Invalid plan."}

    result = activate_subscription_for_payment(
        checkout_request_id=checkout_request_id,
        gmail_email=payment.get("gmail_email"),
        plan=plan,
        amount=payment.get("amount") or plan["price"],
    )
    notification_manager.add_payment_notification(success=True, amount=plan["price"], plan_name=plan["name"])
    return result


def get_env_defaults():
    return {
        "email_subject": os.getenv("EMAIL_SUBJECT", "Automated Email"),
        "email_body": os.getenv("EMAIL_BODY", "This is an automated email."),
        "start_hour": int(os.getenv("START_HOUR", "9")),
        "end_hour": int(os.getenv("END_HOUR", "17")),
        "emails_per_hour": int(os.getenv("EMAILS_PER_HOUR", "125")),
        "time_variation_seconds": float(os.getenv("TIME_VARIATION_SECONDS", "300")),
    }


def resolve_config_payload(payload: ConfigRequest) -> dict:
    data = payload.dict()
    saved = get_settings() or {}

    if not data.get("app_password"):
        data["app_password"] = saved.get("app_password") or os.getenv("GMAIL_APP_PASSWORD", "")

    if not data.get("app_password"):
        raise HTTPException(
            status_code=400,
            detail="App password is required. Enter it on the login page or when changing credentials.",
        )

    return data


@app.get("/api/defaults")
async def api_defaults():
    return get_env_defaults()


@app.get("/api/config")
async def api_get_config():
    settings = get_settings() or {}
    defaults = get_env_defaults()
    return {
        "gmail_email": settings.get("gmail_email", os.getenv("GMAIL_EMAIL", "")),
        "email_subject": settings.get("email_subject", defaults["email_subject"]),
        "email_body": settings.get("email_body", defaults["email_body"]),
        "start_hour": int(settings.get("start_hour", defaults["start_hour"])),
        "end_hour": int(settings.get("end_hour", defaults["end_hour"])),
        "emails_per_hour": int(settings.get("emails_per_hour", defaults["emails_per_hour"])),
        "time_variation_seconds": float(
            settings.get("time_variation_seconds", defaults["time_variation_seconds"])
        ),
    }


@app.post("/api/config")
async def api_post_config(payload: ConfigRequest):
    try:
        config_data = resolve_config_payload(payload)
        new_bot = EmailAutomationBot(EmailAutomationConfig(**config_data))
    except HTTPException:
        raise
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"success": False, "message": str(exc)})

    verification = new_bot.verify_credentials()
    if not verification.get("success"):
        return JSONResponse(status_code=400, content=verification)

    save_settings(config_data)
    global bot
    bot = new_bot
    add_log("Configuration saved and SMTP credentials verified")
    
    # Check if user has active subscription
    gmail_email = payload.gmail_email
    has_active_subscription = is_subscription_active(gmail_email) or is_subscription_check_disabled()
    
    return {
        "success": True, 
        "message": "Configuration saved and SMTP credentials verified.",
        "redirect": "/send" if has_active_subscription else "/subscription"
    }


@app.post("/api/login")
async def api_login(request: Request, gmail_email: str = Form(...), password: str = Form(...)):
    """Handle user login"""
    # Truncate password to 72 bytes (bcrypt limit)
    password = password[:72]
    
    # Check if user exists
    user = get_user(gmail_email)
    
    if not user:
        # Create new user if doesn't exist (first-time login)
        password_hash = pwd_context.hash(password)
        if not create_user(gmail_email, password_hash):
            return JSONResponse(status_code=400, content={"success": False, "message": "Failed to create user"})
        user = get_user(gmail_email)
    
    # Verify password
    if not pwd_context.verify(password, user["password_hash"]):
        return JSONResponse(status_code=401, content={"success": False, "message": "Invalid credentials"})
    
    # Set session
    request.session["user_email"] = gmail_email
    add_log(f"User logged in: {gmail_email}")
    
    # Check subscription status
    has_active_subscription = is_subscription_active(gmail_email) or is_subscription_check_disabled()
    
    return {
        "success": True,
        "message": "Login successful",
        "redirect": "/send" if has_active_subscription else "/subscription"
    }


@app.post("/api/logout")
async def api_logout(request: Request):
    """Handle user logout"""
    user_email = request.session.get("user_email")
    if user_email:
        add_log(f"User logged out: {user_email}")
    request.session.clear()
    return {"success": True, "message": "Logged out successfully", "redirect": "/login"}


def ensure_subscription_or_dev_mode():
    if is_subscription_check_disabled():
        return
    if not is_subscription_active():
        raise HTTPException(
            status_code=403,
            detail="Subscription inactive. Please activate via MPESA or set DISABLE_SUBSCRIPTION_CHECK=true for development.",
        )


@app.post("/api/send/single")
async def api_send_single():
    ensure_subscription_or_dev_mode()
    bot = get_bot_instance()
    result = bot.send_email()
    add_log(result.get("message", "Single send executed"))
    return result


@app.post("/api/send/batch")
async def api_send_batch(payload: BatchRequest):
    ensure_subscription_or_dev_mode()
    if payload.count > 20:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": "Batch size is capped at 20 emails per send."},
        )

    bot = get_bot_instance()

    def batch_target():
        bot.send_batch(payload.count)
        add_log(f"Batch send completed ({payload.count})")

    create_bot_thread(batch_target)
    return {"success": True, "message": "Batch send started.", "requested": payload.count}


@app.post("/api/send/continuous")
async def api_send_continuous():
    ensure_subscription_or_dev_mode()
    bot = get_bot_instance()

    def continuous_target():
        bot.run_continuous()
        add_log("Continuous send completed")

    create_bot_thread(continuous_target)
    return {"success": True, "message": "Continuous mode started."}


@app.post("/api/send/stop")
async def api_send_stop():
    ensure_subscription_or_dev_mode()
    bot = get_bot_instance()
    bot.request_stop()
    add_log("Stop requested")
    return {"success": True, "message": "Send process stopped."}


@app.get("/api/stats")
async def api_stats():
    bot = get_bot_instance()
    return bot.get_statistics()


@app.get("/api/logs")
async def api_logs():
    logs = get_recent_logs()
    return {"logs": logs}


# Notification endpoints
@app.get("/api/notifications")
async def api_notifications():
    """Get all active notifications"""
    notification_manager = get_notification_manager()
    return {
        "notifications": notification_manager.get_all_notifications_dict(),
        "summary": notification_manager.get_notification_summary()
    }


@app.post("/api/notifications/{notification_id}/read")
async def api_mark_notification_read(notification_id: int):
    """Mark a notification as read"""
    notification_manager = get_notification_manager()
    try:
        notification_manager.get_active_notifications()[notification_id].mark_as_read()
        return {"success": True, "message": "Notification marked as read"}
    except (IndexError, AttributeError):
        return {"success": False, "message": "Notification not found"}


@app.post("/api/notifications/{notification_id}/dismiss")
async def api_dismiss_notification(notification_id: int):
    """Dismiss a notification"""
    notification_manager = get_notification_manager()
    try:
        notification_manager.dismiss_notification(notification_id)
        return {"success": True, "message": "Notification dismissed"}
    except IndexError:
        return {"success": False, "message": "Notification not found"}


@app.post("/api/notifications/dismiss-all")
async def api_dismiss_all_notifications():
    """Dismiss all notifications"""
    notification_manager = get_notification_manager()
    notification_manager.dismiss_all()
    return {"success": True, "message": "All notifications dismissed"}


@app.post("/api/notifications/mark-all-read")
async def api_mark_all_notifications_read():
    """Mark all notifications as read"""
    notification_manager = get_notification_manager()
    notification_manager.mark_all_as_read()
    return {"success": True, "message": "All notifications marked as read"}


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8001"))
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=False)
