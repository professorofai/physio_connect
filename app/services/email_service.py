import smtplib
from email.message import EmailMessage

from flask import current_app, has_request_context, render_template, request


def _send_message(message):
    with smtplib.SMTP(
        current_app.config["EMAIL_HOST"], current_app.config["EMAIL_PORT"]
    ) as smtp:
        if current_app.config["MAIL_USE_TLS"]:
            smtp.starttls()
        smtp.login(
            current_app.config["EMAIL_HOST_USER"],
            current_app.config["EMAIL_HOST_PASSWORD"],
        )
        smtp.send_message(message)


def send_registration_email(to_email, username):
    email_host_user = current_app.config["EMAIL_HOST_USER"]
    email_host_password = current_app.config["EMAIL_HOST_PASSWORD"]
    if not email_host_user or not email_host_password:
        current_app.logger.warning("Email credentials not configured; skipping email send.")
        return False

    msg = EmailMessage()
    msg["Subject"] = "Your Physio Connect Registration is Complete"
    msg["From"] = current_app.config["EMAIL_FROM"]
    msg["To"] = to_email
    base_url = current_app.config.get("APP_BASE_URL", "").rstrip("/")
    if not base_url and has_request_context():
        base_url = request.url_root.rstrip("/")
    dashboard_url = f"{base_url}/dashboard" if base_url else "/dashboard"
    msg.set_content(
        f"Dear {username},\n\nThank you for registering with Physio Connect! "
        f"Your account is now active and you can access your dashboard at {dashboard_url}"
        f"\n\nBest regards,\nPhysio Connect Team"
    )

    try:
        _send_message(msg)
        return True
    except Exception as e:
        current_app.logger.error(f"Failed to send registration email: {e}")
        return False


def send_email_otp(email, otp_code):
    email_host_user = current_app.config["EMAIL_HOST_USER"]
    email_host_password = current_app.config["EMAIL_HOST_PASSWORD"]
    if not email_host_user or not email_host_password:
        current_app.logger.warning("Email credentials not configured; skipping email send.")
        return False

    expiration_seconds = current_app.config.get("OTP_EXPIRATION_SECONDS", 150)
    expiration_minutes, remaining_seconds = divmod(expiration_seconds, 60)
    if expiration_minutes:
        expiration_label = f"{expiration_minutes} minutes"
        if remaining_seconds:
            expiration_label += f" and {remaining_seconds} seconds"
    else:
        expiration_label = f"{remaining_seconds} seconds"
    html_content = render_template(
        "emails/otp_verification.html",
        otp_code=otp_code,
        expiration_label=expiration_label,
    )

    msg = EmailMessage()
    msg["Subject"] = "Your Physio Connect Verification Code"
    msg["From"] = current_app.config["EMAIL_FROM"]
    msg["To"] = email

    msg.set_content(
        f"Your Physio Connect verification code is: {otp_code}. "
        f"This code will expire in {expiration_label}."
    )
    msg.add_alternative(html_content, subtype="html")

    try:
        _send_message(msg)
        return True
    except Exception as e:
        current_app.logger.error(f"Failed to send email: {e}")
        return False
