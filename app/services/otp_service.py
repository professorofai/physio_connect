import random
import string
from datetime import datetime, timedelta

from flask import current_app

from app.extensions import db
from app.models import OTPVerification


def generate_otp():
    return "".join(random.choices(string.digits, k=6))


def create_otp_verification(email):
    otp_code = generate_otp()
    expires_at = datetime.utcnow() + timedelta(minutes=10)

    OTPVerification.query.filter_by(email=email, is_used=False).delete()
    db.session.commit()

    otp_verification = OTPVerification(email=email, otp_code=otp_code, expires_at=expires_at)
    db.session.add(otp_verification)
    db.session.commit()

    print(f"[OTP DEBUG]: {otp_code}")
    return otp_code


def verify_otp(email, otp_code):
    otp_verification = OTPVerification.query.filter_by(email=email, otp_code=otp_code, is_used=False).first()

    if not otp_verification:
        return False

    if datetime.utcnow() > otp_verification.expires_at:
        return False

    otp_verification.is_used = True
    db.session.commit()
    return True
