import random
import string
from datetime import datetime, timedelta, timezone

from flask import current_app
from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db
from app.models import OTPVerification


def generate_otp():
    return "".join(random.choices(string.digits, k=6))


def create_otp_verification(email):
    otp_code = generate_otp()
    expiration_seconds = current_app.config.get("OTP_EXPIRATION_SECONDS", 150)
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=expiration_seconds)

    try:
        OTPVerification.query.filter_by(email=email, is_used=False).delete(
            synchronize_session=False
        )
        db.session.add(
            OTPVerification(email=email, otp_code=otp_code, expires_at=expires_at)
        )
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        raise

    print(f"[OTP DEBUG]: {otp_code}")
    return otp_code


def verify_otp(email, otp_code, commit=True):
    try:
        otp_verification = (
            OTPVerification.query.filter_by(
                email=email,
                otp_code=otp_code,
                is_used=False,
            )
            .with_for_update()
            .first()
        )

        if not otp_verification:
            return False

        expires_at = otp_verification.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if datetime.now(timezone.utc) >= expires_at:
            return False

        otp_verification.is_used = True
        if commit:
            db.session.commit()
        else:
            db.session.flush()
        return True
    except SQLAlchemyError:
        db.session.rollback()
        raise
