import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "super_secret_key_123")

    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Gmail SMTP
    EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.gmail.com")
    EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "true").lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER")
    EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")
    EMAIL_FROM = os.environ.get("EMAIL_FROM", EMAIL_HOST_USER)

    EMAIL_TO = os.environ.get("EMAIL_TO", EMAIL_HOST_USER)
    APP_BASE_URL = os.environ.get("APP_BASE_URL", "")

    OTP_EXPIRATION_SECONDS = int(os.environ.get("OTP_EXPIRATION_SECONDS", "150"))

    UPLOAD_FOLDER = "static/uploads"
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}