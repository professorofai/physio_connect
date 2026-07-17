import os

class Config:
    SECRET_KEY = "super_secret_key_123"   # 🔥 ADD THIS LINE

    SQLALCHEMY_DATABASE_URI = "sqlite:///database.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    EMAIL_HOST = "smtp.gmail.com"
    EMAIL_PORT = 587
    EMAIL_HOST_USER = "your_email@gmail.com"
    EMAIL_HOST_PASSWORD = "your_app_password"
    EMAIL_FROM = "your_email@gmail.com"

    UPLOAD_FOLDER = "static/uploads"
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}