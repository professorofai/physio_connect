import smtplib
from email.message import EmailMessage

from flask import current_app, render_template


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
    msg.set_content(
        f"Dear {username},\n\nThank you for registering with Physio Connect! Your account is now active and you can access your dashboard at http://localhost:5000/dashboard\n\nBest regards,\nPhysio Connect Team"
    )

    try:
        with smtplib.SMTP(current_app.config["EMAIL_HOST"], current_app.config["EMAIL_PORT"]) as smtp:
            smtp.starttls()
            smtp.login(email_host_user, email_host_password)
            smtp.send_message(msg)
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

    html_content = render_template("emails/otp_verification.html", otp_code=otp_code)

    msg = EmailMessage()
    msg["Subject"] = "Your Physio Connect Verification Code"
    msg["From"] = current_app.config["EMAIL_FROM"]
    msg["To"] = email

    msg.set_content(f"Your Physio Connect verification code is: {otp_code}. This code will expire in 10 minutes.")
    msg.add_alternative(html_content, subtype="html")

    try:
        with smtplib.SMTP(current_app.config["EMAIL_HOST"], current_app.config["EMAIL_PORT"]) as smtp:
            smtp.starttls()
            smtp.login(email_host_user, email_host_password)
            smtp.send_message(msg)
        return True
    except Exception as e:
        current_app.logger.error(f"Failed to send email: {e}")
        return False
