def resolve_smtp_credentials(settings=None, env=None):
    settings = settings or {}
    env = env or {}

    smtp_email = str(settings.get("gmail_email") or env.get("GMAIL_EMAIL") or "").strip()
    smtp_password = str(settings.get("app_password") or env.get("GMAIL_APP_PASSWORD") or "").strip()
    return smtp_email, smtp_password
